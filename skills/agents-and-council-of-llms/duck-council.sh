#!/bin/bash

# duck-council.sh: The Council of LLMs Solicitation Tool
# Usage: ./duck-council.sh --problem "..." --lenses "..." --context "..."

# Load Secrets
if [ -f "skills/common/secrets.sh" ]; then
    source "skills/common/secrets.sh"
fi

# 1. Parse Arguments
MODEL="opencode/glm-4.7-free" # Default model
PROMPT_FILE="skills/agents-and-council-of-llms/prompts/council.md"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --problem) PROBLEM="$2"; shift ;;
        --lenses) LENSES="$2"; shift ;;
        --context) CONTEXT="$2"; shift ;;
        --model) MODEL="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$PROBLEM" ] || [ -z "$LENSES" ]; then
    echo "Usage: $0 --problem \"<problem>\" --lenses \"<lens1,lens2,...>\" [--context \"<context>\"]"
    exit 1
fi

# 2. Setup Session
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="skills/agents-and-council-of-llms/transcripts/$TIMESTAMP"
mkdir -p "$SESSION_DIR"
echo "Starting Council Session: $TIMESTAMP"
echo "Problem: $PROBLEM" > "$SESSION_DIR/metadata.txt"
echo "Lenses: $LENSES" >> "$SESSION_DIR/metadata.txt"

IFS=',' read -ra ADDR <<< "$LENSES"

# 3. Solicit Responses (Parallel Execution)
pids=()
for lens in "${ADDR[@]}"; do
    lens=$(echo "$lens" | xargs) # trim whitespace
    echo "[Council Member: $lens] Deliberating..."
    
    # Read prompt template
    if [ -f "$PROMPT_FILE" ]; then
        TEMPLATE=$(cat "$PROMPT_FILE")
    else
        echo "Error: Prompt file not found at $PROMPT_FILE"
        exit 1
    fi

    # Replace placeholders
    PROMPT="${TEMPLATE//\{\{LENS\}\}/$lens}"
    PROMPT="${PROMPT//\{\{PROBLEM\}\}/$PROBLEM}"
    PROMPT="${PROMPT//\{\{CONTEXT\}\}/$CONTEXT}"
    
    # Save the prompt for audit
    echo "$PROMPT" > "$SESSION_DIR/${lens// /_}_PROMPT.txt"
    
    # Run opencode
    OUTPUT_FILE="$SESSION_DIR/${lens// /_}.md"
    
    opencode run "$PROMPT" --model "$MODEL" > "$OUTPUT_FILE" 2>&1 &
    pids+=($!)
done

# 4. Wait for Completion
for pid in "${pids[@]}"; do
    wait "$pid"
done

# 5. Compile Transcript
TRANSCRIPT_FILE="$SESSION_DIR/FULL_TRANSCRIPT.md"
echo "# Council Session Transcript: $TIMESTAMP" > "$TRANSCRIPT_FILE"
echo "## Problem" >> "$TRANSCRIPT_FILE"
echo "$PROBLEM" >> "$TRANSCRIPT_FILE"
echo "" >> "$TRANSCRIPT_FILE"

for lens in "${ADDR[@]}"; do
    lens=$(echo "$lens" | xargs)
    OUTPUT_FILE="$SESSION_DIR/${lens// /_}.md"
    echo "## Perspective: $lens" >> "$TRANSCRIPT_FILE"
    # Basic cleanup of opencode output if needed (e.g., removing logs if mixed in)
    cat "$OUTPUT_FILE" >> "$TRANSCRIPT_FILE"
    echo "" >> "$TRANSCRIPT_FILE"
    echo "---" >> "$TRANSCRIPT_FILE"
done

echo "Council Session Complete."
echo "Transcript saved to: $TRANSCRIPT_FILE"
cat "$TRANSCRIPT_FILE"
