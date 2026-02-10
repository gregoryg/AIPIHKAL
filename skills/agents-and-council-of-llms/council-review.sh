#!/bin/bash

# council-review.sh: Democratic Peer Review Tool for the Council
# Usage: ./council-review.sh --session "path/to/session" [--reviewers "..."] [--model "..."]

set -euo pipefail

# Robust Directory Resolution
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Debug mode
DEBUG="${COUNCIL_DEBUG:-0}"
debug() { [[ "$DEBUG" == "1" ]] && echo "[DEBUG] $*" >&2 || true; }

# Load Secrets
if [ -f "skills/common/secrets.sh" ]; then
    source "skills/common/secrets.sh"
fi

# === Configuration Loading ===
load_default_model() {
    local config_file="${COUNCIL_MODELS_FILE:-$HOME/.config/council/models.conf}"
    
    if [[ -n "${COUNCIL_REVIEW_MODEL:-}" ]]; then
        debug "Loading review model from COUNCIL_REVIEW_MODEL env var"
        echo "$COUNCIL_REVIEW_MODEL"
    elif [[ -f "$config_file" ]]; then
        debug "Loading first model from config file as reviewer: $config_file"
        grep -v '^#' "$config_file" | grep -v '^$' | head -n1
    else
        debug "Using hardcoded default review model"
        echo "openrouter/openai/gpt-4o-mini"
    fi
}

# === Argument Parsing ===
MODEL=""
PROMPT_FILE="$DIR/prompts/peer-review.md"
REVIEWERS=""
SESSION_DIR=""
TIMEOUT_SECS="${COUNCIL_TIMEOUT:-120}"

show_help() {
    cat << 'EOF'
council-review.sh - Democratic Peer Review for Council Sessions

USAGE:
    council-review.sh --session PATH [OPTIONS]

REQUIRED:
    --session PATH      Path to a council session directory (from council-convene.sh)

OPTIONS:
    --reviewers LIST    Comma-separated reviewer lenses (default: auto-detect from session)
    --model MODEL       Model for all reviewers (default: from config or first council model)
    --timeout SECS      Timeout per review call (default: 120)
    --dry-run           Show what would be reviewed without executing
    --help              Show this help

ENVIRONMENT:
    COUNCIL_REVIEW_MODEL  Default model for reviews
    COUNCIL_MODELS_FILE   Path to models config
    COUNCIL_DEBUG         Set to 1 for verbose output
    COUNCIL_TIMEOUT       Default timeout in seconds

EXAMPLES:
    # Auto-detect reviewers from original session
    ./council-review.sh --session ./transcripts/20260210_141523

    # Specific reviewers with custom model
    ./council-review.sh --session ./transcripts/20260210_141523 \
        --reviewers "Devil's Advocate, Optimist" \
        --model "openrouter/anthropic/claude-3.5-sonnet"

    # Single "supreme court" reviewer
    ./council-review.sh --session ./transcripts/20260210_141523 \
        --reviewers "Supreme Court" \
        --model "openrouter/openai/gpt-4o"
EOF
}

DRY_RUN=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --session) SESSION_DIR="$2"; shift ;;
        --model) MODEL="$2"; shift ;;
        --reviewers) REVIEWERS="$2"; shift ;;
        --timeout) TIMEOUT_SECS="$2"; shift ;;
        --dry-run) DRY_RUN=1 ;;
        --help|-h) show_help; exit 0 ;;
        *) echo "Unknown parameter: $1" >&2; echo "Use --help for usage." >&2; exit 1 ;;
    esac
    shift
done

# Validate session
if [[ -z "$SESSION_DIR" ]]; then
    echo "Error: Must specify --session" >&2
    echo "Use --help for usage." >&2
    exit 1
fi

if [[ ! -d "$SESSION_DIR" ]]; then
    echo "Error: Session directory not found: $SESSION_DIR" >&2
    exit 1
fi

# === Load Model ===
if [[ -z "$MODEL" ]]; then
    MODEL=$(load_default_model)
    debug "Using default review model: $MODEL"
fi

# === Load Metadata ===
METADATA_FILE="$SESSION_DIR/metadata.txt"
PROBLEM="[Problem statement not found]"
CONTEXT=""

if [[ -f "$METADATA_FILE" ]]; then
    FOUND_PROBLEM=$(grep "^Problem:" "$METADATA_FILE" | head -n 1 | sed 's/^Problem: //')
    if [[ -n "$FOUND_PROBLEM" ]]; then 
        PROBLEM="$FOUND_PROBLEM"
    fi
    
    FOUND_CONTEXT=$(grep "^Context:" "$METADATA_FILE" | head -n 1 | sed 's/^Context: //')
    if [[ -n "$FOUND_CONTEXT" ]]; then 
        CONTEXT="$FOUND_CONTEXT"
    fi

    # Auto-detect reviewers if not specified
    if [[ -z "$REVIEWERS" ]]; then
        FOUND_LENSES=$(grep "^Lenses:" "$METADATA_FILE" | head -n 1 | sed 's/^Lenses: //')
        if [[ -n "$FOUND_LENSES" ]]; then
            REVIEWERS="$FOUND_LENSES"
            echo "Auto-detected original council members for review: $REVIEWERS"
        fi
    fi
fi

# Default reviewer if still empty
if [[ -z "$REVIEWERS" ]]; then
    REVIEWERS="Peer_Reviewer"
    debug "No reviewers specified or detected, using default: $REVIEWERS"
fi

# === Anonymize Responses ===
echo "Anonymizing responses..."

ANON_TEXT=""
KEY_FILE="$SESSION_DIR/review_key.txt"
> "$KEY_FILE"

LETTER_INDEX=0
LETTERS=("A" "B" "C" "D" "E" "F" "G" "H" "I" "J" "K" "L" "M" "N" "O" "P")

# Find response files (exclude system files)
response_files=()
while IFS= read -r -d '' f; do
    filename=$(basename "$f")
    # Skip system files
    [[ "$filename" == "FULL_TRANSCRIPT.md" ]] && continue
    [[ "$filename" == "PEER_REVIEW.md" ]] && continue
    [[ "$filename" == *"_REVIEW.md" ]] && continue
    [[ "$filename" == *"_PROMPT.txt" ]] && continue
    [[ "$filename" == "metadata.txt" ]] && continue
    [[ "$filename" == "review_key.txt" ]] && continue
    response_files+=("$f")
done < <(find "$SESSION_DIR" -maxdepth 1 -name "*.md" -print0 | sort -z)

if [[ ${#response_files[@]} -eq 0 ]]; then
    echo "Error: No response files found in session directory" >&2
    exit 1
fi

debug "Found ${#response_files[@]} response files to anonymize"

for f in "${response_files[@]}"; do
    filename=$(basename "$f")
    
    # Assign Letter
    if [[ $LETTER_INDEX -ge ${#LETTERS[@]} ]]; then
        echo "Warning: More than ${#LETTERS[@]} responses, some may not be labeled correctly" >&2
    fi
    LABEL="${LETTERS[$LETTER_INDEX]:-X$LETTER_INDEX}"
    echo "$LABEL: $filename" >> "$KEY_FILE"
    
    CONTENT=$(cat "$f")
    
    # Check for error responses
    if grep -q "^COUNCIL_ERROR:" <<< "$CONTENT"; then
        ANON_TEXT+="
---
### RESPONSE $LABEL
**(This council member encountered an error)**
$CONTENT
"
    else
        ANON_TEXT+="
---
### RESPONSE $LABEL
$CONTENT
"
    fi
    ((LETTER_INDEX++))
done

debug "Anonymization key saved to: $KEY_FILE"

# === Dry Run Check ===
if [[ "$DRY_RUN" == "1" ]]; then
    echo ""
    echo "=== DRY RUN ==="
    echo "Session: $SESSION_DIR"
    echo "Problem: ${PROBLEM:0:100}..."
    echo "Reviewers: $REVIEWERS"
    echo "Model: $MODEL"
    echo ""
    echo "Anonymized ${#response_files[@]} responses:"
    cat "$KEY_FILE"
    echo ""
    echo "Would create reviews in: $SESSION_DIR/"
    exit 0
fi

# === Load Prompt Template ===
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: Prompt template not found at $PROMPT_FILE" >&2
    exit 1
fi
TEMPLATE=$(cat "$PROMPT_FILE")

# === Solicit Reviews (Parallel) ===
IFS=',' read -ra REVIEWER_ARR <<< "$REVIEWERS"
for i in "${!REVIEWER_ARR[@]}"; do 
    REVIEWER_ARR[$i]=$(echo "${REVIEWER_ARR[$i]}" | xargs)
done

echo "Starting Democratic Peer Review with ${#REVIEWER_ARR[@]} reviewer(s)..."
debug "Using model: $MODEL"

pids=()

for reviewer in "${REVIEWER_ARR[@]}"; do
    echo "[Reviewer: $reviewer] Evaluating..."
    
    # Build prompt
    PROMPT="${TEMPLATE//\{\{REVIEWER_LENS\}\}/$reviewer}"
    PROMPT="${PROMPT//\{\{PROBLEM\}\}/$PROBLEM}"
    PROMPT="${PROMPT//\{\{CONTEXT\}\}/$CONTEXT}"
    PROMPT="${PROMPT//\{\{RESPONSES\}\}/$ANON_TEXT}"
    
    OUTPUT_FILE="$SESSION_DIR/${reviewer// /_}_REVIEW.md"
    
    # Execute with timeout
    (
        if timeout "$TIMEOUT_SECS" opencode run "$PROMPT" --model "$MODEL" > "$OUTPUT_FILE" 2>&1; then
            debug "Reviewer $reviewer completed successfully"
        else
            exit_code=$?
            if [[ $exit_code -eq 124 ]]; then
                echo "COUNCIL_ERROR: Review by $reviewer timed out after ${TIMEOUT_SECS}s" > "$OUTPUT_FILE"
            else
                echo "COUNCIL_ERROR: Review by $reviewer failed with exit code $exit_code" >> "$OUTPUT_FILE"
            fi
        fi
    ) &
    pids+=($!)
done

# === Wait for Completion ===
echo "Waiting for reviews to complete..."
failed=0
for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
        ((failed++))
    fi
done

if [[ $failed -gt 0 ]]; then
    echo "Warning: $failed review(s) may have failed. Check individual outputs." >&2
fi

# === Aggregate Reviews ===
AGGREGATE_FILE="$SESSION_DIR/PEER_REVIEW.md"

cat > "$AGGREGATE_FILE" << EOF
# Council Peer Review: Democratic Process

## Problem
$PROBLEM

## Context
$CONTEXT

## Anonymization Key
$(cat "$KEY_FILE")

---

EOF

for reviewer in "${REVIEWER_ARR[@]}"; do
    OUTPUT_FILE="$SESSION_DIR/${reviewer// /_}_REVIEW.md"
    
    echo "## Review by: $reviewer" >> "$AGGREGATE_FILE"
    
    if [[ -f "$OUTPUT_FILE" ]]; then
        if grep -q "^COUNCIL_ERROR:" "$OUTPUT_FILE"; then
            echo "**(Error during review)**" >> "$AGGREGATE_FILE"
        fi
        cat "$OUTPUT_FILE" >> "$AGGREGATE_FILE"
    else
        echo "(Review failed or timed out)" >> "$AGGREGATE_FILE"
    fi
    
    echo "" >> "$AGGREGATE_FILE"
    echo "---" >> "$AGGREGATE_FILE"
    echo "" >> "$AGGREGATE_FILE"
done

echo ""
echo "Democratic Review Complete."
echo "Key saved to: $KEY_FILE"
echo "Aggregate Review saved to: $AGGREGATE_FILE"
echo ""
cat "$AGGREGATE_FILE"
