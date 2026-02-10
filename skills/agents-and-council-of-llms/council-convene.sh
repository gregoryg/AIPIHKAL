#!/bin/bash

# council-convene.sh: The Council of LLMs Solicitation Tool
# Usage: ./council-convene.sh --problem "..." --lenses "..." --context "..."

# Robust Directory Resolution
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Load Secrets
if [ -f "skills/common/secrets.sh" ]; then
    source "skills/common/secrets.sh"
fi

# 1. Parse Arguments
DEFAULT_MODEL="opencode/glm-4.7-free"
PROMPT_FILE="$DIR/prompts/council.md"

PROBLEM=""
LENSES=""
MODELS_ARG=""
COUNT=""
CONTEXT=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --problem) PROBLEM="$2"; shift ;;
        --lenses) LENSES="$2"; shift ;;
        --models) MODELS_ARG="$2"; shift ;;
        --count) COUNT="$2"; shift ;;
        --context) CONTEXT="$2"; shift ;;
        --model) DEFAULT_MODEL="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROBLEM" ]; then
    echo "Usage: $0 --problem \"<problem>\" [--lenses \"<l1,l2>\"] [--models \"<m1,m2>\"] [--count <N>]"
    exit 1
fi

# 2. Setup Session
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Save to transcripts dir relative to this script
SESSION_DIR="$DIR/transcripts/$TIMESTAMP"
mkdir -p "$SESSION_DIR"
echo "Starting Council Session: $TIMESTAMP"
echo "Problem: $PROBLEM" > "$SESSION_DIR/metadata.txt"

# 3. logic to determine iterations
# Split CSVs into arrays
IFS=',' read -ra LENS_ARR <<< "$LENSES"
IFS=',' read -ra MODEL_ARR <<< "$MODELS_ARG"

# Trim whitespace
for i in "${!LENS_ARR[@]}"; do LENS_ARR[$i]=$(echo "${LENS_ARR[$i]}" | xargs); done
for i in "${!MODEL_ARR[@]}"; do MODEL_ARR[$i]=$(echo "${MODEL_ARR[$i]}" | xargs); done

# Determine Loop Count
if [ ! -z "$COUNT" ]; then
    MAX_ITER=$COUNT
elif [ ${#LENS_ARR[@]} -gt 0 ]; then
    MAX_ITER=${#LENS_ARR[@]}
elif [ ${#MODEL_ARR[@]} -gt 0 ]; then
    MAX_ITER=${#MODEL_ARR[@]}
else
    echo "Error: Must specify --lenses, --models, or --count."
    exit 1
fi

# Save metadata
echo "Lenses: $LENSES" >> "$SESSION_DIR/metadata.txt"
echo "Models: $MODELS_ARG" >> "$SESSION_DIR/metadata.txt"
echo "Count: $MAX_ITER" >> "$SESSION_DIR/metadata.txt"

# 4. Solicit Responses (Parallel Execution)
pids=()

# Check Prompt File
if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found at $PROMPT_FILE"
    exit 1
fi
TEMPLATE=$(cat "$PROMPT_FILE")

echo "Convening Council with $MAX_ITER members..."

for (( i=0; i<MAX_ITER; i++ )); do
    # Determine Lens Name/Perspective
    if [ $i -lt ${#LENS_ARR[@]} ]; then
        CUR_LENS="${LENS_ARR[$i]}"
        # If lens is explicit, we use it for both filename and prompt
        LENS_PROMPT="$CUR_LENS"
        FILE_NAME="$CUR_LENS"
    else
        # If no lens specified for this slot (Consensus/Voting Mode)
        # We use a generic prompt but unique filename
        LENS_PROMPT="Objective Analysis"
        FILE_NAME="Member_$((i+1))"
    fi

    # Determine Model
    if [ $i -lt ${#MODEL_ARR[@]} ]; then
        CUR_MODEL="${MODEL_ARR[$i]}"
    else
        # Fallback to last specified model or default
        if [ ${#MODEL_ARR[@]} -gt 0 ]; then
             # If we have models but ran out, recycle the last one?
             # Or maybe standard logic is to use Default if explicit list exhausted?
             # Let's use DEFAULT_MODEL if index out of bounds.
             CUR_MODEL="$DEFAULT_MODEL"
        else
             CUR_MODEL="$DEFAULT_MODEL"
        fi
    fi

    echo "[Member: $FILE_NAME] Deliberating using $CUR_MODEL..."

    # Replace placeholders
    PROMPT="${TEMPLATE//\{\{LENS\}\}/$LENS_PROMPT}"
    PROMPT="${PROMPT//\{\{PROBLEM\}\}/$PROBLEM}"
    PROMPT="${PROMPT//\{\{CONTEXT\}\}/$CONTEXT}"

    # Save the prompt for audit
    echo "$PROMPT" > "$SESSION_DIR/${FILE_NAME// /_}_PROMPT.txt"

    # Run opencode
    OUTPUT_FILE="$SESSION_DIR/${FILE_NAME// /_}.md"

    # Execute in background
    opencode run "$PROMPT" --model "$CUR_MODEL" > "$OUTPUT_FILE" 2>&1 &
    pids+=($!)
done

# 5. Wait for Completion
for pid in "${pids[@]}"; do
    wait "$pid"
done

# 6. Compile Transcript
TRANSCRIPT_FILE="$SESSION_DIR/FULL_TRANSCRIPT.md"
echo "# Council Session Transcript: $TIMESTAMP" > "$TRANSCRIPT_FILE"
echo "## Problem" >> "$TRANSCRIPT_FILE"
echo "$PROBLEM" >> "$TRANSCRIPT_FILE"
echo "" >> "$TRANSCRIPT_FILE"

# Re-iterate to grab files (files might be unordered if we just ls, so we reconstruct names)
for (( i=0; i<MAX_ITER; i++ )); do
    if [ $i -lt ${#LENS_ARR[@]} ]; then
        FILE_NAME="${LENS_ARR[$i]}"
    else
        FILE_NAME="Member_$((i+1))"
    fi

    OUTPUT_FILE="$SESSION_DIR/${FILE_NAME// /_}.md"
    echo "## Perspective: $FILE_NAME" >> "$TRANSCRIPT_FILE"

    if [ -f "$OUTPUT_FILE" ]; then
        cat "$OUTPUT_FILE" >> "$TRANSCRIPT_FILE"
    else
        echo "(Output missing)" >> "$TRANSCRIPT_FILE"
    fi
    echo "" >> "$TRANSCRIPT_FILE"
    echo "---" >> "$TRANSCRIPT_FILE"
done

echo "Council Session Complete."
echo "Transcript saved to: $TRANSCRIPT_FILE"
cat "$TRANSCRIPT_FILE"
