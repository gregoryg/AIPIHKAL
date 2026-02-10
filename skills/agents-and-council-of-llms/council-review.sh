#!/bin/bash

# council-review.sh: Democratic Peer Review Tool for the Council
# Usage: ./council-review.sh --session "skills/agents-and-council-of-llms/transcripts/..." [--reviewers "Lens1,Lens2"] [--model "..."]

# Robust Directory Resolution
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Load Secrets
if [ -f "skills/common/secrets.sh" ]; then
    source "skills/common/secrets.sh"
fi

# 1. Parse Arguments
MODEL="opencode/glm-4.7-free" # Default underlying model
PROMPT_FILE="$DIR/prompts/peer-review.md"
REVIEWERS=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --session) SESSION_DIR="$2"; shift ;;
        --model) MODEL="$2"; shift ;;
        --reviewers) REVIEWERS="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$SESSION_DIR" ]; then
    echo "Usage: $0 --session \"<session_dir>\" [--reviewers \"<lenses>\"] [--model \"<model>\"]"
    exit 1
fi

if [ ! -d "$SESSION_DIR" ]; then
    echo "Error: Session directory not found: $SESSION_DIR"
    exit 1
fi

# 2. Load Metadata
METADATA_FILE="$SESSION_DIR/metadata.txt"
PROBLEM="[Problem statement not found]"
CONTEXT="(See Problem)"

if [ -f "$METADATA_FILE" ]; then
    # Simple extraction (assumes single line or structured enough)
    # We use grep to find the line starting with "Problem:", then cut everything after the first space
    # NOTE: This is brittle for multi-line problems, but sufficient for now.
    FOUND_PROBLEM=$(grep "^Problem:" "$METADATA_FILE" | head -n 1 | cut -d' ' -f2-)
    if [ ! -z "$FOUND_PROBLEM" ]; then PROBLEM="$FOUND_PROBLEM"; fi

    # Try to find original lenses if REVIEWERS not set
    if [ -z "$REVIEWERS" ]; then
        FOUND_LENSES=$(grep "^Lenses:" "$METADATA_FILE" | head -n 1 | cut -d' ' -f2-)
        if [ ! -z "$FOUND_LENSES" ]; then
            REVIEWERS="$FOUND_LENSES"
            echo "Auto-detected original council members for review: $REVIEWERS"
        fi
    fi
fi

# Default Reviewer if still empty
if [ -z "$REVIEWERS" ]; then
    REVIEWERS="Peer_Reviewer"
fi

# 3. Anonymize Responses
ANON_TEXT=""
KEY_FILE="$SESSION_DIR/review_key.txt"
> "$KEY_FILE"

LETTER_INDEX=0
LETTERS=("A" "B" "C" "D" "E" "F" "G" "H" "I" "J")

echo "Anonymizing responses..."

# Loop through lens outputs (excluding transcripts/prompts/metadata/reviews)
# We sort to ensure deterministic assignment of letters if re-run
for f in $(ls "$SESSION_DIR"/*.md | sort); do
    filename=$(basename "$f")
    # Skip system files
    if [[ "$filename" == "FULL_TRANSCRIPT.md" ]]; then continue; fi
    if [[ "$filename" == "PEER_REVIEW.md" ]]; then continue; fi
    if [[ "$filename" == *"_REVIEW.md" ]]; then continue; fi

    # Assign Letter
    LABEL="${LETTERS[$LETTER_INDEX]}"
    echo "$LABEL: $filename" >> "$KEY_FILE"

    CONTENT=$(cat "$f")

    ANON_TEXT+="
---
### RESPONSE $LABEL
$CONTENT
"
    ((LETTER_INDEX++))
done

# 4. Solicit Reviews (Parallel Execution)
IFS=',' read -ra ADDR <<< "$REVIEWERS"
pids=()

echo "Starting Democratic Peer Review with model: $MODEL"

# Read template once
if [ -f "$PROMPT_FILE" ]; then
    TEMPLATE=$(cat "$PROMPT_FILE")
else
    echo "Error: Prompt file not found at $PROMPT_FILE"
    exit 1
fi

for reviewer in "${ADDR[@]}"; do
    reviewer=$(echo "$reviewer" | xargs) # trim whitespace
    echo "[Reviewer: $reviewer] Evaluating..."

    # Prepare Prompt
    PROMPT="${TEMPLATE//\{\{REVIEWER_LENS\}\}/$reviewer}"
    PROMPT="${PROMPT//\{\{PROBLEM\}\}/$PROBLEM}"
    PROMPT="${PROMPT//\{\{CONTEXT\}\}/$CONTEXT}"
    PROMPT="${PROMPT//\{\{RESPONSES\}\}/$ANON_TEXT}"

    # Output file for this specific review
    OUTPUT_FILE="$SESSION_DIR/${reviewer// /_}_REVIEW.md"

    # Execute
    opencode run "$PROMPT" --model "$MODEL" > "$OUTPUT_FILE" 2>&1 &
    pids+=($!)
done

# 5. Wait for Completion
for pid in "${pids[@]}"; do
    wait "$pid"
done

# 6. Aggregate Reviews
AGGREGATE_FILE="$SESSION_DIR/PEER_REVIEW.md"
echo "# Council Peer Review: Democratic Process" > "$AGGREGATE_FILE"
echo "## Problem" >> "$AGGREGATE_FILE"
echo "$PROBLEM" >> "$AGGREGATE_FILE"
echo "" >> "$AGGREGATE_FILE"

for reviewer in "${ADDR[@]}"; do
    reviewer=$(echo "$reviewer" | xargs)
    OUTPUT_FILE="$SESSION_DIR/${reviewer// /_}_REVIEW.md"

    echo "## Review by: $reviewer" >> "$AGGREGATE_FILE"
    if [ -f "$OUTPUT_FILE" ]; then
        cat "$OUTPUT_FILE" >> "$AGGREGATE_FILE"
    else
        echo "(Review failed or timed out)" >> "$AGGREGATE_FILE"
    fi
    echo "" >> "$AGGREGATE_FILE"
    echo "---" >> "$AGGREGATE_FILE"
done

echo "Democratic Review Complete."
echo "Key saved to: $KEY_FILE"
echo "Aggregate Review saved to: $AGGREGATE_FILE"
cat "$AGGREGATE_FILE"
