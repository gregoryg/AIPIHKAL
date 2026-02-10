#!/bin/bash

# council-convene.sh: The Council of LLMs Solicitation Tool
# Usage: ./council-convene.sh --problem "..." --lenses "..." --context "..."
#        ./council-convene.sh --prompt-file /path/to/prompt.txt --count 3
#        ./council-convene.sh --prompt-b64 "base64string" --lenses "..."

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
# Priority: 1) --models arg, 2) COUNCIL_MODELS env, 3) config file, 4) defaults

load_default_models() {
    local config_file="${COUNCIL_MODELS_FILE:-$HOME/.config/council/models.conf}"
    
    if [[ -n "${COUNCIL_MODELS:-}" ]]; then
        debug "Loading models from COUNCIL_MODELS env var"
        echo "$COUNCIL_MODELS"
    elif [[ -f "$config_file" ]]; then
        debug "Loading models from config file: $config_file"
        grep -v '^#' "$config_file" | grep -v '^$' | tr '\n' ',' | sed 's/,$//'
    else
        debug "Using hardcoded default models"
        echo "openrouter/openai/gpt-4o-mini,openrouter/anthropic/claude-3.5-haiku,openrouter/google/gemini-2.0-flash-001"
    fi
}

# === Argument Parsing ===
PROMPT_FILE="$DIR/prompts/council.md"
PROBLEM=""
LENSES=""
MODELS_ARG=""
COUNT=""
CONTEXT=""
INPUT_PROMPT_FILE=""
INPUT_PROMPT_B64=""
TIMEOUT_SECS="${COUNCIL_TIMEOUT:-120}"

show_help() {
    cat << 'EOF'
council-convene.sh - Convene a Council of LLMs

USAGE:
    council-convene.sh --problem "..." [OPTIONS]
    council-convene.sh --prompt-file FILE [OPTIONS]
    council-convene.sh --prompt-b64 BASE64 [OPTIONS]

INPUT OPTIONS (one required):
    --problem TEXT      Problem statement (inline)
    --prompt-file FILE  Read problem from file (avoids shell escaping)
    --prompt-b64 STR    Problem as base64-encoded string

COUNCIL OPTIONS:
    --lenses LIST       Comma-separated expert lenses (e.g., "Legal, Technical, Ethics")
    --models LIST       Comma-separated model identifiers (overrides config)
    --count N           Number of council members (for consensus/voting mode)
    --context TEXT      Additional context for the problem

OTHER OPTIONS:
    --timeout SECS      Timeout per model call (default: 120)
    --dry-run           Show what would be called without executing
    --help              Show this help

ENVIRONMENT:
    COUNCIL_MODELS      Comma-separated default models
    COUNCIL_MODELS_FILE Path to models config (default: ~/.config/council/models.conf)
    COUNCIL_DEBUG       Set to 1 for verbose output
    COUNCIL_TIMEOUT     Default timeout in seconds (default: 120)

EXAMPLES:
    # Simple consensus vote
    ./council-convene.sh --problem "Should we use microservices?" --count 3

    # Role-based analysis
    ./council-convene.sh --problem "Evaluate this contract" \
        --lenses "Legal, Financial, Risk Management"

    # Complex prompt from file
    echo "Long complex prompt..." > /tmp/prompt.txt
    ./council-convene.sh --prompt-file /tmp/prompt.txt --count 5

    # Override models for this session
    ./council-convene.sh --problem "..." \
        --models "openrouter/openai/gpt-4o,openrouter/anthropic/claude-3.5-sonnet"
EOF
}

DRY_RUN=0

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --problem) PROBLEM="$2"; shift ;;
        --prompt-file) INPUT_PROMPT_FILE="$2"; shift ;;
        --prompt-b64) INPUT_PROMPT_B64="$2"; shift ;;
        --lenses) LENSES="$2"; shift ;;
        --models) MODELS_ARG="$2"; shift ;;
        --count) COUNT="$2"; shift ;;
        --context) CONTEXT="$2"; shift ;;
        --timeout) TIMEOUT_SECS="$2"; shift ;;
        --dry-run) DRY_RUN=1 ;;
        --help|-h) show_help; exit 0 ;;
        *) echo "Unknown parameter: $1" >&2; echo "Use --help for usage." >&2; exit 1 ;;
    esac
    shift
done

# === Input Resolution ===
# Handle --prompt-file
if [[ -n "$INPUT_PROMPT_FILE" ]]; then
    if [[ ! -f "$INPUT_PROMPT_FILE" ]]; then
        echo "Error: Prompt file not found: $INPUT_PROMPT_FILE" >&2
        exit 1
    fi
    PROBLEM=$(cat "$INPUT_PROMPT_FILE")
    debug "Loaded problem from file: $INPUT_PROMPT_FILE (${#PROBLEM} chars)"
fi

# Handle --prompt-b64
if [[ -n "$INPUT_PROMPT_B64" ]]; then
    PROBLEM=$(echo "$INPUT_PROMPT_B64" | base64 -d)
    debug "Decoded problem from base64 (${#PROBLEM} chars)"
fi

# Validate we have a problem
if [[ -z "$PROBLEM" ]]; then
    echo "Error: Must specify --problem, --prompt-file, or --prompt-b64" >&2
    echo "Use --help for usage." >&2
    exit 1
fi

# === Model Resolution ===
if [[ -z "$MODELS_ARG" ]]; then
    MODELS_ARG=$(load_default_models)
    debug "Using default models: $MODELS_ARG"
fi

# === Setup Session ===
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="$DIR/transcripts/$TIMESTAMP"
mkdir -p "$SESSION_DIR"

echo "Starting Council Session: $TIMESTAMP"
debug "Session directory: $SESSION_DIR"

# Save metadata
cat > "$SESSION_DIR/metadata.txt" << EOF
Problem: $PROBLEM
Lenses: $LENSES
Models: $MODELS_ARG
Context: $CONTEXT
Timestamp: $TIMESTAMP
EOF

# === Parse Arrays ===
IFS=',' read -ra LENS_ARR <<< "$LENSES"
IFS=',' read -ra MODEL_ARR <<< "$MODELS_ARG"

# Trim whitespace
for i in "${!LENS_ARR[@]}"; do LENS_ARR[$i]=$(echo "${LENS_ARR[$i]}" | xargs); done
for i in "${!MODEL_ARR[@]}"; do MODEL_ARR[$i]=$(echo "${MODEL_ARR[$i]}" | xargs); done

debug "Lenses: ${LENS_ARR[*]:-none}"
debug "Models: ${MODEL_ARR[*]}"

# === Determine Iteration Count ===
if [[ -n "$COUNT" ]]; then
    MAX_ITER=$COUNT
elif [[ ${#LENS_ARR[@]} -gt 0 && -n "${LENS_ARR[0]}" ]]; then
    MAX_ITER=${#LENS_ARR[@]}
elif [[ ${#MODEL_ARR[@]} -gt 0 ]]; then
    MAX_ITER=${#MODEL_ARR[@]}
else
    echo "Error: Must specify --lenses, --models, or --count." >&2
    exit 1
fi

echo "Count: $MAX_ITER" >> "$SESSION_DIR/metadata.txt"
debug "Council size: $MAX_ITER members"

# === Dry Run Check ===
if [[ "$DRY_RUN" == "1" ]]; then
    echo ""
    echo "=== DRY RUN ==="
    echo "Would convene $MAX_ITER council members:"
    for (( i=0; i<MAX_ITER; i++ )); do
        if [[ $i -lt ${#LENS_ARR[@]} && -n "${LENS_ARR[$i]}" ]]; then
            lens="${LENS_ARR[$i]}"
        else
            lens="Objective Analysis"
        fi
        if [[ $i -lt ${#MODEL_ARR[@]} ]]; then
            model="${MODEL_ARR[$i]}"
        else
            model="${MODEL_ARR[-1]:-openrouter/openai/gpt-4o-mini}"
        fi
        echo "  Member $((i+1)): $lens (model: $model)"
    done
    echo ""
    echo "Problem (first 200 chars):"
    echo "${PROBLEM:0:200}..."
    echo ""
    echo "Session would be saved to: $SESSION_DIR"
    exit 0
fi

# === Load Prompt Template ===
if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Error: Prompt template not found at $PROMPT_FILE" >&2
    exit 1
fi
TEMPLATE=$(cat "$PROMPT_FILE")

# === Run Council Members (Parallel) ===
echo "Convening Council with $MAX_ITER members..."

pids=()
member_info=()

for (( i=0; i<MAX_ITER; i++ )); do
    # Determine Lens
    if [[ $i -lt ${#LENS_ARR[@]} && -n "${LENS_ARR[$i]}" ]]; then
        CUR_LENS="${LENS_ARR[$i]}"
        LENS_PROMPT="$CUR_LENS"
        FILE_NAME="$CUR_LENS"
    else
        LENS_PROMPT="Objective Analysis"
        FILE_NAME="Member_$((i+1))"
    fi

    # Determine Model (cycle through available models)
    if [[ ${#MODEL_ARR[@]} -gt 0 ]]; then
        model_idx=$((i % ${#MODEL_ARR[@]}))
        CUR_MODEL="${MODEL_ARR[$model_idx]}"
    else
        CUR_MODEL="openrouter/openai/gpt-4o-mini"
    fi

    echo "[Member: $FILE_NAME] Deliberating using $CUR_MODEL..."
    member_info+=("$FILE_NAME:$CUR_MODEL")

    # Build prompt from template
    PROMPT="${TEMPLATE//\{\{LENS\}\}/$LENS_PROMPT}"
    PROMPT="${PROMPT//\{\{PROBLEM\}\}/$PROBLEM}"
    PROMPT="${PROMPT//\{\{CONTEXT\}\}/$CONTEXT}"

    # Save prompt for audit
    echo "$PROMPT" > "$SESSION_DIR/${FILE_NAME// /_}_PROMPT.txt"

    OUTPUT_FILE="$SESSION_DIR/${FILE_NAME// /_}.md"

    # Execute with timeout, capture errors
    (
        if timeout "$TIMEOUT_SECS" opencode run "$PROMPT" --model "$CUR_MODEL" > "$OUTPUT_FILE" 2>&1; then
            debug "Member $FILE_NAME completed successfully"
        else
            exit_code=$?
            if [[ $exit_code -eq 124 ]]; then
                echo "COUNCIL_ERROR: $CUR_MODEL timed out after ${TIMEOUT_SECS}s" > "$OUTPUT_FILE"
            else
                echo "COUNCIL_ERROR: $CUR_MODEL failed with exit code $exit_code" >> "$OUTPUT_FILE"
            fi
        fi
    ) &
    pids+=($!)
done

# === Wait for Completion ===
echo "Waiting for council members to complete..."
failed=0
for idx in "${!pids[@]}"; do
    pid="${pids[$idx]}"
    if ! wait "$pid"; then
        echo "Warning: Member process $pid exited with error" >&2
        ((failed++))
    fi
done

if [[ $failed -gt 0 ]]; then
    echo "Warning: $failed member(s) may have failed. Check individual outputs." >&2
fi

# === Compile Transcript ===
TRANSCRIPT_FILE="$SESSION_DIR/FULL_TRANSCRIPT.md"

cat > "$TRANSCRIPT_FILE" << EOF
# Council Session Transcript: $TIMESTAMP

## Problem
$PROBLEM

## Context
$CONTEXT

---

EOF

for (( i=0; i<MAX_ITER; i++ )); do
    if [[ $i -lt ${#LENS_ARR[@]} && -n "${LENS_ARR[$i]}" ]]; then
        FILE_NAME="${LENS_ARR[$i]}"
    else
        FILE_NAME="Member_$((i+1))"
    fi

    OUTPUT_FILE="$SESSION_DIR/${FILE_NAME// /_}.md"
    
    echo "## Perspective: $FILE_NAME" >> "$TRANSCRIPT_FILE"
    
    if [[ -f "$OUTPUT_FILE" ]]; then
        # Check for error marker
        if grep -q "^COUNCIL_ERROR:" "$OUTPUT_FILE"; then
            echo "**(Error during deliberation)**" >> "$TRANSCRIPT_FILE"
        fi
        cat "$OUTPUT_FILE" >> "$TRANSCRIPT_FILE"
    else
        echo "(Output missing)" >> "$TRANSCRIPT_FILE"
    fi
    
    echo "" >> "$TRANSCRIPT_FILE"
    echo "---" >> "$TRANSCRIPT_FILE"
    echo "" >> "$TRANSCRIPT_FILE"
done

echo ""
echo "Council Session Complete."
echo "Transcript saved to: $TRANSCRIPT_FILE"
echo ""
cat "$TRANSCRIPT_FILE"
