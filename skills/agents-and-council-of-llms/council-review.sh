#!/usr/bin/env bash
# Anonymize council outputs and solicit bounded peer review.
set -euo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
DELEGATE=${COUNCIL_DELEGATE:-"$DIR/../bounded-llm-delegation/scripts/delegate"}
DEBUG=${COUNCIL_DEBUG:-0}
debug() { [[ "$DEBUG" == 1 ]] && echo "[DEBUG] $*" >&2 || true; }

usage() {
    cat <<'EOF'
Usage: council-review.sh --session PATH [OPTIONS]

  --session PATH          Council session from council-convene.sh
  --reviewers LIST        Comma-separated reviewer lenses
  --model MODEL           Reviewer model (default: configured first model)
  --harness NAME          Harness (default: original session, then pi)
  --timeout SECONDS       Per-review deadline (default: 300)
  --kill-after SECONDS    TERM-to-KILL grace (default: 20)
  --max-concurrency N     Simultaneous reviewers (default: 4, max: 8)
  --dry-run               Build anonymization key and show plan only
  -h, --help              Show help

The parent shell/tool deadline must exceed --timeout + --kill-after + aggregation
grace. Review child sessions and run artifacts are persistent.
EOF
}

load_model() {
    local config=${COUNCIL_MODELS_FILE:-"$HOME/.config/council/models.conf"}
    if [[ -n ${COUNCIL_REVIEW_MODEL:-} ]]; then
        printf '%s\n' "$COUNCIL_REVIEW_MODEL"
    elif [[ -f "$config" ]]; then
        grep -vE '^[[:space:]]*(#|$)' "$config" | head -1
    elif [[ -n ${PI_MODEL:-} ]]; then
        [[ -n ${PI_PROVIDER:-} ]] && printf '%s/' "$PI_PROVIDER"
        printf '%s\n' "$PI_MODEL"
    else
        printf 'default\n'
    fi
}

SESSION_DIR=""
REVIEWERS=""
MODEL=""
HARNESS=${COUNCIL_HARNESS:-}
TIMEOUT_SECS=${COUNCIL_TIMEOUT:-300}
KILL_AFTER=${COUNCIL_KILL_AFTER:-20}
MAX_CONCURRENCY=${COUNCIL_MAX_CONCURRENCY:-4}
DRY_RUN=0

while (($#)); do
    case "$1" in
        --session) SESSION_DIR=${2:?}; shift 2 ;;
        --reviewers) REVIEWERS=${2:?}; shift 2 ;;
        --model) MODEL=${2:?}; shift 2 ;;
        --harness) HARNESS=${2:?}; shift 2 ;;
        --timeout) TIMEOUT_SECS=${2:?}; shift 2 ;;
        --kill-after) KILL_AFTER=${2:?}; shift 2 ;;
        --max-concurrency) MAX_CONCURRENCY=${2:?}; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "council-review: unknown argument: $1" >&2; exit 2 ;;
    esac
done

[[ -n "$SESSION_DIR" && -d "$SESSION_DIR" ]] || { echo "council-review: valid --session is required" >&2; exit 2; }
SESSION_DIR=$(cd "$SESSION_DIR" && pwd -P)
[[ -x "$DELEGATE" ]] || { echo "council-review: bounded delegate not executable: $DELEGATE" >&2; exit 2; }
for value in "$TIMEOUT_SECS" "$KILL_AFTER" "$MAX_CONCURRENCY"; do
    [[ "$value" =~ ^[1-9][0-9]*$ ]] || { echo "council-review: deadlines/concurrency must be positive integers" >&2; exit 2; }
done
((MAX_CONCURRENCY <= 8)) || { echo "council-review: max concurrency is 8" >&2; exit 2; }

METADATA_JSON="$SESSION_DIR/metadata.json"
if [[ -z "$HARNESS" && -r "$METADATA_JSON" ]]; then
    HARNESS=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("harness", "pi"))' "$METADATA_JSON")
fi
[[ -n "$HARNESS" ]] || HARNESS=pi
[[ -n "$MODEL" ]] || MODEL=$(load_model)

PROBLEM_FILE="$SESSION_DIR/problem.txt"
CONTEXT_FILE="$SESSION_DIR/context.txt"
PROBLEM='[Problem statement not found]'
CONTEXT=''
if [[ -r "$PROBLEM_FILE" ]]; then
    PROBLEM=$(cat "$PROBLEM_FILE")
elif [[ -r "$SESSION_DIR/metadata.txt" ]]; then
    legacy_problem=$(sed -n 's/^Problem: //p' "$SESSION_DIR/metadata.txt" | head -1)
    [[ -n "$legacy_problem" ]] && PROBLEM=$legacy_problem
fi
if [[ -r "$CONTEXT_FILE" ]]; then
    CONTEXT=$(cat "$CONTEXT_FILE")
elif [[ -r "$SESSION_DIR/metadata.txt" ]]; then
    CONTEXT=$(sed -n 's/^Context: //p' "$SESSION_DIR/metadata.txt" | head -1)
fi

if [[ -z "$REVIEWERS" && -r "$SESSION_DIR/lenses.txt" ]]; then
    REVIEWERS=$(cat "$SESSION_DIR/lenses.txt")
elif [[ -z "$REVIEWERS" && -r "$SESSION_DIR/metadata.txt" ]]; then
    REVIEWERS=$(sed -n 's/^Lenses: //p' "$SESSION_DIR/metadata.txt" | head -1)
fi
[[ -n "$REVIEWERS" ]] || REVIEWERS=Peer_Reviewer
IFS=',' read -r -a REVIEWER_ARR <<< "$REVIEWERS"
for i in "${!REVIEWER_ARR[@]}"; do REVIEWER_ARR[$i]=$(echo "${REVIEWER_ARR[$i]}" | xargs); done

response_files=()
while IFS= read -r -d '' file; do
    name=$(basename "$file")
    case "$name" in
        FULL_TRANSCRIPT.md|PEER_REVIEW.md|anonymized-responses.md|REVIEW_*.md|*_REVIEW.md) continue ;;
    esac
    response_files+=("$file")
done < <(find "$SESSION_DIR" -maxdepth 1 -type f -name '*.md' -print0 | sort -z)
((${#response_files[@]} > 0)) || { echo "council-review: no council response files found" >&2; exit 2; }

KEY_FILE="$SESSION_DIR/review_key.txt"
ANON_FILE="$SESSION_DIR/anonymized-responses.md"
: > "$KEY_FILE"
: > "$ANON_FILE"
letters=(A B C D E F G H I J K L M N O P)
for i in "${!response_files[@]}"; do
    label=${letters[$i]:-X$i}
    name=$(basename "${response_files[$i]}")
    printf '%s: %s\n' "$label" "$name" >> "$KEY_FILE"
    {
        echo
        echo '---'
        echo "### RESPONSE $label"
        if grep -q '^COUNCIL_ERROR:' "${response_files[$i]}"; then
            echo '**(This council member encountered an error.)**'
        fi
        cat "${response_files[$i]}"
    } >> "$ANON_FILE"
done
REVIEW_PROBLEM_FILE="$SESSION_DIR/review-problem.txt"
REVIEW_CONTEXT_FILE="$SESSION_DIR/review-context.txt"
printf '%s\n' "$PROBLEM" > "$REVIEW_PROBLEM_FILE"
printf '%s\n' "$CONTEXT" > "$REVIEW_CONTEXT_FILE"

CWD=$PWD
if [[ -r "$METADATA_JSON" ]]; then
    recorded_cwd=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("cwd", ""))' "$METADATA_JSON")
    [[ -d "$recorded_cwd" ]] && CWD=$recorded_cwd
fi

echo "Reviewing ${#response_files[@]} responses with ${#REVIEWER_ARR[@]} reviewer(s)"
echo "Harness: $HARNESS; model: $MODEL"
if [[ "$DRY_RUN" -eq 1 ]]; then
    echo '=== DRY RUN ==='
    cat "$KEY_FILE"
    exit 0
fi

TEMPLATE_FILE="$DIR/prompts/peer-review.md"
[[ -r "$TEMPLATE_FILE" ]] || { echo "council-review: missing template: $TEMPLATE_FILE" >&2; exit 2; }
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$SESSION_DIR/runs/reviews"
safe_name() { printf '%s' "$1" | tr -cs '[:alnum:]_.-' '_' | sed 's/^_*//; s/_*$//'; }

run_reviewer() {
    local index=$1 reviewer=$2 review_id=$3
    local prompt_file="$SESSION_DIR/${review_id}_PROMPT.txt"
    local output_file="$SESSION_DIR/${review_id}.md"
    local run_dir="$SESSION_DIR/runs/reviews/$review_id"
    mkdir -p "$run_dir"
    python3 - "$TEMPLATE_FILE" "$prompt_file" "$reviewer" \
        "$REVIEW_PROBLEM_FILE" "$REVIEW_CONTEXT_FILE" "$ANON_FILE" <<'PY'
import pathlib
import re
import sys

template_path, output_path, reviewer, problem_path, context_path, responses_path = sys.argv[1:]
values = {
    "REVIEWER_LENS": reviewer,
    "PROBLEM": pathlib.Path(problem_path).read_text().rstrip("\n"),
    "CONTEXT": pathlib.Path(context_path).read_text().rstrip("\n"),
    "RESPONSES": pathlib.Path(responses_path).read_text().rstrip("\n"),
}
template = pathlib.Path(template_path).read_text()
rendered = re.sub(r"\{\{(REVIEWER_LENS|PROBLEM|CONTEXT|RESPONSES)\}\}",
                  lambda match: values[match.group(1)], template)
pathlib.Path(output_path).write_text(rendered)
PY

    local args=(
        --harness "$HARNESS"
        --prompt-file "$prompt_file"
        --cwd "$CWD"
        --policy none
        --context none
        --deadline "$TIMEOUT_SECS"
        --kill-after "$KILL_AFTER"
        --name "council-review-${STAMP}-${review_id}"
        --run-dir "$run_dir"
    )
    [[ "$MODEL" != default ]] && args+=(--model "$MODEL")
    [[ "$HARNESS" == hermes ]] && args+=(--allow-auto-approve)

    set +e
    "$DELEGATE" "${args[@]}" > "$run_dir.launcher.log" 2>&1
    local status=$?
    set -e
    {
        if [[ "$status" -ne 0 ]]; then
            printf 'COUNCIL_ERROR: reviewer %s (%s via %s) exited %s\n\n' "$reviewer" "$MODEL" "$HARNESS" "$status"
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
review_ids=()
next_wait=0
active=0
failed=0
for i in "${!REVIEWER_ARR[@]}"; do
    reviewer=${REVIEWER_ARR[$i]}
    slug=$(safe_name "$reviewer")
    [[ -n "$slug" ]] || slug=Reviewer
    review_id=$(printf 'REVIEW_%02d_%s' "$((i+1))" "$slug")
    review_ids+=("$review_id")
    echo "[$review_id] $reviewer"
    run_reviewer "$i" "$reviewer" "$review_id" &
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

AGGREGATE="$SESSION_DIR/PEER_REVIEW.md"
{
    echo '# Council Peer Review'
    echo
    echo '## Problem'
    printf '%s\n' "$PROBLEM"
    echo
    echo '## Context'
    printf '%s\n' "$CONTEXT"
    echo
    echo '## Anonymization key'
    cat "$KEY_FILE"
    for review_id in "${review_ids[@]}"; do
        echo
        echo '---'
        echo
        echo "## $review_id"
        cat "$SESSION_DIR/${review_id}.md"
    done
} > "$AGGREGATE"

printf '%s\n' "$failed" > "$SESSION_DIR/review-failure-count.txt"
echo "Peer review complete: $((${#REVIEWER_ARR[@]}-failed))/${#REVIEWER_ARR[@]} succeeded"
echo "Aggregate: $AGGREGATE"
[[ "$failed" -eq 0 ]]
