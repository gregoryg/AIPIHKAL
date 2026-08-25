#!/usr/bin/env bash
# Convene independent model perspectives through bounded delegation.
set -euo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
DELEGATE=${COUNCIL_DELEGATE:-"$DIR/../bounded-llm-delegation/scripts/delegate"}
STATE_ROOT=${XDG_STATE_HOME:-"$HOME/.local/state"}
TRANSCRIPTS_ROOT=${COUNCIL_TRANSCRIPTS_DIR:-"$STATE_ROOT/bounded-llm-delegation/councils"}
DEBUG=${COUNCIL_DEBUG:-0}
debug() { [[ "$DEBUG" == 1 ]] && echo "[DEBUG] $*" >&2 || true; }

usage() {
    cat <<'EOF'
Usage:
  council-convene.sh --problem TEXT [OPTIONS]
  council-convene.sh --prompt-file FILE [OPTIONS]
  council-convene.sh --prompt-b64 BASE64 [OPTIONS]

Input (choose one):
  --problem TEXT          Inline problem; prompt-file is safer for complex text
  --prompt-file FILE      Read the problem from a file
  --prompt-b64 BASE64     Decode the problem from base64

Council:
  --lenses LIST           Comma-separated expert lenses
  --models LIST           Comma-separated model IDs for the selected harness
  --count N               Member count; models cycle as needed
  --context TEXT          Additional shared context
  --harness NAME          Delegation harness (default: pi)
  --cwd DIR               Child working directory (default: current directory)
  --context-policy MODE   none or project (default: none)
  --timeout SECONDS       Per-member child deadline (default: 300)
  --kill-after SECONDS    TERM-to-KILL grace (default: 20)
  --max-concurrency N     Maximum simultaneous members (default: 4, max: 8)
  --dry-run               Validate and show the plan without model calls
  -h, --help              Show help

Environment:
  COUNCIL_HARNESS, COUNCIL_MODELS, COUNCIL_MODELS_FILE,
  COUNCIL_TIMEOUT, COUNCIL_KILL_AFTER, COUNCIL_MAX_CONCURRENCY,
  COUNCIL_TRANSCRIPTS_DIR, COUNCIL_DELEGATE, COUNCIL_DEBUG

The parent shell/tool deadline must exceed --timeout + --kill-after + transcript
grace. Sessions and per-member run artifacts are persistent by default.
EOF
}

load_models() {
    local config=${COUNCIL_MODELS_FILE:-"$HOME/.config/council/models.conf"}
    if [[ -n ${COUNCIL_MODELS:-} ]]; then
        printf '%s\n' "$COUNCIL_MODELS"
    elif [[ -f "$config" ]]; then
        grep -vE '^[[:space:]]*(#|$)' "$config" | paste -sd, -
    elif [[ ${HARNESS:-pi} == pi && -n ${PI_MODEL:-} ]]; then
        if [[ -n ${PI_PROVIDER:-} ]]; then
            printf '%s/%s\n' "$PI_PROVIDER" "$PI_MODEL"
        else
            printf '%s\n' "$PI_MODEL"
        fi
    else
        printf 'default\n'
    fi
}

PROBLEM=""
INPUT_FILE=""
INPUT_B64=""
LENSES=""
MODELS=""
COUNT=""
CONTEXT=""
HARNESS=${COUNCIL_HARNESS:-pi}
CWD=$PWD
CONTEXT_POLICY=none
TIMEOUT_SECS=${COUNCIL_TIMEOUT:-300}
KILL_AFTER=${COUNCIL_KILL_AFTER:-20}
MAX_CONCURRENCY=${COUNCIL_MAX_CONCURRENCY:-4}
DRY_RUN=0

while (($#)); do
    case "$1" in
        --problem) PROBLEM=${2:?}; shift 2 ;;
        --prompt-file) INPUT_FILE=${2:?}; shift 2 ;;
        --prompt-b64) INPUT_B64=${2:?}; shift 2 ;;
        --lenses) LENSES=${2:?}; shift 2 ;;
        --models) MODELS=${2:?}; shift 2 ;;
        --count) COUNT=${2:?}; shift 2 ;;
        --context) CONTEXT=${2:?}; shift 2 ;;
        --harness) HARNESS=${2:?}; shift 2 ;;
        --cwd) CWD=${2:?}; shift 2 ;;
        --context-policy) CONTEXT_POLICY=${2:?}; shift 2 ;;
        --timeout) TIMEOUT_SECS=${2:?}; shift 2 ;;
        --kill-after) KILL_AFTER=${2:?}; shift 2 ;;
        --max-concurrency) MAX_CONCURRENCY=${2:?}; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "council-convene: unknown argument: $1" >&2; exit 2 ;;
    esac
done

input_count=0
[[ -n "$PROBLEM" ]] && input_count=$((input_count + 1))
[[ -n "$INPUT_FILE" ]] && input_count=$((input_count + 1))
[[ -n "$INPUT_B64" ]] && input_count=$((input_count + 1))
[[ "$input_count" -eq 1 ]] || { echo "council-convene: provide exactly one input mode" >&2; exit 2; }
if [[ -n "$INPUT_FILE" ]]; then
    [[ -r "$INPUT_FILE" ]] || { echo "council-convene: unreadable prompt file: $INPUT_FILE" >&2; exit 2; }
    PROBLEM=$(cat "$INPUT_FILE")
elif [[ -n "$INPUT_B64" ]]; then
    PROBLEM=$(printf '%s' "$INPUT_B64" | base64 --decode)
fi
[[ -n "$PROBLEM" ]] || { echo "council-convene: empty problem" >&2; exit 2; }
[[ -d "$CWD" ]] || { echo "council-convene: invalid cwd: $CWD" >&2; exit 2; }
[[ "$CONTEXT_POLICY" =~ ^(none|project)$ ]] || { echo "council-convene: invalid context policy" >&2; exit 2; }
for value in "$TIMEOUT_SECS" "$KILL_AFTER" "$MAX_CONCURRENCY"; do
    [[ "$value" =~ ^[1-9][0-9]*$ ]] || { echo "council-convene: deadlines/concurrency must be positive integers" >&2; exit 2; }
done
((MAX_CONCURRENCY <= 8)) || { echo "council-convene: max concurrency is 8" >&2; exit 2; }
[[ -x "$DELEGATE" ]] || { echo "council-convene: bounded delegate not executable: $DELEGATE" >&2; exit 2; }

[[ -n "$MODELS" ]] || MODELS=$(load_models)
IFS=',' read -r -a MODEL_ARR <<< "$MODELS"
IFS=',' read -r -a LENS_ARR <<< "$LENSES"
for i in "${!MODEL_ARR[@]}"; do MODEL_ARR[$i]=$(echo "${MODEL_ARR[$i]}" | xargs); done
for i in "${!LENS_ARR[@]}"; do LENS_ARR[$i]=$(echo "${LENS_ARR[$i]}" | xargs); done

if [[ -n "$COUNT" ]]; then
    [[ "$COUNT" =~ ^[1-9][0-9]*$ ]] || { echo "council-convene: count must be positive" >&2; exit 2; }
    MEMBER_COUNT=$COUNT
elif [[ ${#LENS_ARR[@]} -gt 0 && -n ${LENS_ARR[0]:-} ]]; then
    MEMBER_COUNT=${#LENS_ARR[@]}
else
    MEMBER_COUNT=${#MODEL_ARR[@]}
fi
((MEMBER_COUNT <= 16)) || { echo "council-convene: maximum council size is 16" >&2; exit 2; }

umask 077
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SESSION_DIR="$TRANSCRIPTS_ROOT/${STAMP}-$$"
mkdir -p "$SESSION_DIR/runs"
printf '%s\n' "$PROBLEM" > "$SESSION_DIR/problem.txt"
printf '%s\n' "$CONTEXT" > "$SESSION_DIR/context.txt"
printf '%s\n' "$LENSES" > "$SESSION_DIR/lenses.txt"
printf '%s\n' "$MODELS" > "$SESSION_DIR/models.txt"
python3 - "$SESSION_DIR/metadata.json" <<PY
import json, sys
json.dump({
  "timestamp": ${STAMP@Q},
  "harness": ${HARNESS@Q},
  "models": ${MODELS@Q}.split(","),
  "lenses": ${LENSES@Q}.split(",") if ${LENSES@Q} else [],
  "member_count": int(${MEMBER_COUNT@Q}),
  "cwd": ${CWD@Q},
  "context_policy": ${CONTEXT_POLICY@Q},
  "timeout_seconds": int(${TIMEOUT_SECS@Q}),
  "kill_after_seconds": int(${KILL_AFTER@Q}),
  "max_concurrency": int(${MAX_CONCURRENCY@Q})
}, open(sys.argv[1], "w"), indent=2)
PY
cat > "$SESSION_DIR/metadata.txt" <<EOF
Session: $SESSION_DIR
Harness: $HARNESS
Models: $MODELS
Lenses: $LENSES
Count: $MEMBER_COUNT
Cwd: $CWD
Timeout: $TIMEOUT_SECS
Kill-after: $KILL_AFTER
Max-concurrency: $MAX_CONCURRENCY
Problem-File: problem.txt
Context-File: context.txt
EOF

echo "Starting Council Session: $SESSION_DIR"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "=== DRY RUN ==="
    for ((i=0; i<MEMBER_COUNT; i++)); do
        lens=${LENS_ARR[$i]:-Objective Analysis}
        model=${MODEL_ARR[$((i % ${#MODEL_ARR[@]}))]:-default}
        printf '  %02d: %s [%s via %s]\n' "$((i+1))" "$lens" "$model" "$HARNESS"
    done
    exit 0
fi

TEMPLATE_FILE="$DIR/prompts/council.md"
[[ -r "$TEMPLATE_FILE" ]] || { echo "council-convene: missing template: $TEMPLATE_FILE" >&2; exit 2; }

safe_name() { printf '%s' "$1" | tr -cs '[:alnum:]_.-' '_' | sed 's/^_*//; s/_*$//'; }
run_member() {
    local index=$1 lens=$2 model=$3 member_id=$4
    local prompt_file="$SESSION_DIR/${member_id}_PROMPT.txt"
    local output_file="$SESSION_DIR/${member_id}.md"
    local run_dir="$SESSION_DIR/runs/$member_id"
    mkdir -p "$run_dir"
    python3 - "$TEMPLATE_FILE" "$prompt_file" "$lens" \
        "$SESSION_DIR/problem.txt" "$SESSION_DIR/context.txt" <<'PY'
import pathlib
import re
import sys

template_path, output_path, lens, problem_path, context_path = sys.argv[1:]
values = {
    "LENS": lens,
    "PROBLEM": pathlib.Path(problem_path).read_text().rstrip("\n"),
    "CONTEXT": pathlib.Path(context_path).read_text().rstrip("\n"),
}
template = pathlib.Path(template_path).read_text()
rendered = re.sub(r"\{\{(LENS|PROBLEM|CONTEXT)\}\}",
                  lambda match: values[match.group(1)], template)
pathlib.Path(output_path).write_text(rendered)
PY

    local args=(
        --harness "$HARNESS"
        --prompt-file "$prompt_file"
        --cwd "$CWD"
        --policy none
        --context "$CONTEXT_POLICY"
        --deadline "$TIMEOUT_SECS"
        --kill-after "$KILL_AFTER"
        --name "council-${STAMP}-${member_id}"
        --run-dir "$run_dir"
    )
    [[ "$model" != default ]] && args+=(--model "$model")
    [[ "$HARNESS" == hermes ]] && args+=(--allow-auto-approve)

    set +e
    "$DELEGATE" "${args[@]}" > "$run_dir.launcher.log" 2>&1
    local status=$?
    set -e
    {
        if [[ "$status" -ne 0 ]]; then
            printf 'COUNCIL_ERROR: member %s (%s via %s) exited %s\n\n' "$member_id" "$model" "$HARNESS" "$status"
        fi
        if [[ -s "$run_dir/final.md" ]]; then
            cat "$run_dir/final.md"
        elif [[ -s "$run_dir/stdout.log" ]]; then
            cat "$run_dir/stdout.log"
        else
            echo '(no model output)'
        fi
    } > "$output_file"
    return "$status"
}

pids=()
member_ids=()
next_wait=0
active=0
failed=0
for ((i=0; i<MEMBER_COUNT; i++)); do
    lens=${LENS_ARR[$i]:-Objective Analysis}
    model=${MODEL_ARR[$((i % ${#MODEL_ARR[@]}))]:-default}
    slug=$(safe_name "$lens")
    [[ -n "$slug" ]] || slug=Member
    member_id=$(printf '%02d_%s' "$((i+1))" "$slug")
    member_ids+=("$member_id")
    echo "[$member_id] $lens using $model via $HARNESS"
    run_member "$i" "$lens" "$model" "$member_id" &
    pids+=("$!")
    active=$((active + 1))
    if ((active >= MAX_CONCURRENCY)); then
        set +e
        wait "${pids[$next_wait]}"
        status=$?
        set -e
        [[ "$status" -eq 0 ]] || failed=$((failed + 1))
        next_wait=$((next_wait + 1))
        active=$((active - 1))
    fi
done
while ((next_wait < ${#pids[@]})); do
    set +e
    wait "${pids[$next_wait]}"
    status=$?
    set -e
    [[ "$status" -eq 0 ]] || failed=$((failed + 1))
    next_wait=$((next_wait + 1))
done

TRANSCRIPT="$SESSION_DIR/FULL_TRANSCRIPT.md"
{
    echo "# Council Session Transcript: $STAMP"
    echo
    echo "## Problem"
    cat "$SESSION_DIR/problem.txt"
    echo
    echo "## Context"
    cat "$SESSION_DIR/context.txt"
    for member_id in "${member_ids[@]}"; do
        echo
        echo '---'
        echo
        echo "## Perspective: $member_id"
        cat "$SESSION_DIR/${member_id}.md"
    done
} > "$TRANSCRIPT"

printf '%s\n' "$failed" > "$SESSION_DIR/failure-count.txt"
echo "Council complete: $((MEMBER_COUNT-failed))/$MEMBER_COUNT succeeded"
echo "Transcript: $TRANSCRIPT"
[[ "$failed" -eq 0 ]]
