#!/usr/bin/env bash
set -euo pipefail

DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/transcripts"

cat > "$TMP/fake-delegate" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
run_dir=""
prompt_file=""
model=default
while (($#)); do
    case "$1" in
        --run-dir) run_dir=$2; shift 2 ;;
        --prompt-file) prompt_file=$2; shift 2 ;;
        --model) model=$2; shift 2 ;;
        *) shift ;;
    esac
done
mkdir -p "$run_dir"
printf 'fake response model=%s prompt=%s\n' "$model" "$(sha256sum "$prompt_file" | cut -d' ' -f1)" > "$run_dir/final.md"
printf '0\n' > "$run_dir/status"
if [[ "$model" == fail ]]; then
    printf 'partial failed response\n' > "$run_dir/final.md"
    printf '124\n' > "$run_dir/status"
    exit 124
fi
EOF
chmod +x "$TMP/fake-delegate"
printf '%s\n' 'Evaluate A&B; preserve literal {{LENS}} and backslash \path.' > "$TMP/problem.md"

COUNCIL_DELEGATE="$TMP/fake-delegate" \
COUNCIL_TRANSCRIPTS_DIR="$TMP/transcripts" \
"$DIR/council-convene.sh" \
    --prompt-file "$TMP/problem.md" \
    --lenses 'Architecture,Performance,Migration' \
    --models 'model-a,model-b' \
    --context 'Context C&D preserves literal {{PROBLEM}}.' \
    --harness pi \
    --timeout 5 \
    --kill-after 1 \
    --max-concurrency 2 >/dev/null

session=$(find "$TMP/transcripts" -mindepth 1 -maxdepth 1 -type d | head -1)
[[ -n "$session" ]]
[[ $(find "$session" -maxdepth 1 -type f -name '[0-9][0-9]_*.md' | wc -l) == 3 ]]
grep -q '3/3 succeeded' <(printf 'Council complete: 3/3 succeeded\n')
grep -q 'Perspective: 01_Architecture' "$session/FULL_TRANSCRIPT.md"
grep -Fq 'Evaluate A&B; preserve literal {{LENS}} and backslash \path.' "$session/01_Architecture_PROMPT.txt"
grep -Fq 'Context C&D preserves literal {{PROBLEM}}.' "$session/01_Architecture_PROMPT.txt"
python3 -m json.tool "$session/metadata.json" >/dev/null

COUNCIL_DELEGATE="$TMP/fake-delegate" \
"$DIR/council-review.sh" \
    --session "$session" \
    --reviewers 'Adversary & Ops,Implementer' \
    --model reviewer-model \
    --harness pi \
    --timeout 5 \
    --kill-after 1 \
    --max-concurrency 2 >/dev/null
[[ $(find "$session" -maxdepth 1 -type f -name 'REVIEW_[0-9][0-9]_*.md' | wc -l) == 2 ]]
grep -q 'REVIEW_01_Adversary_Ops' "$session/PEER_REVIEW.md"
grep -q '^A:' "$session/review_key.txt"

set +e
sleep 1
COUNCIL_DELEGATE="$TMP/fake-delegate" \
COUNCIL_TRANSCRIPTS_DIR="$TMP/transcripts" \
"$DIR/council-convene.sh" \
    --problem 'Exercise partial failure.' \
    --count 2 \
    --models 'model-a,fail' \
    --harness pi \
    --timeout 5 \
    --kill-after 1 >/dev/null
status=$?
set -e
[[ "$status" != 0 ]]
failed_session=$(find "$TMP/transcripts" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)
grep -q '^COUNCIL_ERROR:' "$failed_session/02_Objective_Analysis.md"
grep -q 'partial failed response' "$failed_session/02_Objective_Analysis.md"
[[ $(<"$failed_session/failure-count.txt") == 1 ]]

echo 'council tests: OK'
