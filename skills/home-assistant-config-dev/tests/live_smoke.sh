#!/usr/bin/env bash
# Opt-in live smoke checks. Reports metadata only; does not dump event contents.
set -euo pipefail

if [[ ${HA_DEV_LIVE_SMOKE:-} != 1 ]]; then
    printf '%s\n' \
        'Refused: set HA_DEV_LIVE_SMOKE=1 to run live Home Assistant checks.' >&2
    exit 2
fi

: "${HA_DEV_SMOKE_CALENDAR:?Set an exact calendar entity ID}"
: "${HA_DEV_SMOKE_TRACE_DOMAIN:?Set automation or script}"
: "${HA_DEV_SMOKE_TRACE_ITEM_ID:?Set the trace item ID}"

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../scripts" && pwd -P)
start=$(date --iso-8601=seconds --date='-1 hour')
end=$(date --iso-8601=seconds --date='+4 hours')

calendar_output=$(
    "$script_dir/ha-calendar-events" \
        "$HA_DEV_SMOKE_CALENDAR" "$start" "$end" --limit 10
)
jq -e '{check:"calendar",status,entity_id,count,total_count,truncated} |
    select(.status == "ok")' <<<"$calendar_output"

trace_list=$(
    "$script_dir/ha-trace" list \
        "$HA_DEV_SMOKE_TRACE_DOMAIN" "$HA_DEV_SMOKE_TRACE_ITEM_ID" --limit 1
)
run_id=$(jq -er '.traces[0].run_id' <<<"$trace_list")
jq -e '{check:"trace-list",status,domain,item_id,count} |
    select(.status == "ok" and .count == 1)' <<<"$trace_list"

trace_get=$(
    "$script_dir/ha-trace" get \
        "$HA_DEV_SMOKE_TRACE_DOMAIN" "$HA_DEV_SMOKE_TRACE_ITEM_ID" "$run_id"
)
jq -e '{check:"trace-get",status,domain,item_id,
    run_id:.trace.run_id,state:.trace.state,
    execution:.trace.script_execution,path_count:.trace.path_count,
    paths_truncated:.trace.paths_truncated,has_error:(.trace.error != null)} |
    select(.status == "ok")' <<<"$trace_get"

if [[ ${HA_DEV_SMOKE_ASSIST:-} == 1 ]]; then
    assist_phrase=${HA_DEV_SMOKE_ASSIST_PHRASE:-What time is it?}
    assist_output=$("$script_dir/ha-assist-run" --execute "$assist_phrase")
    jq -e '{check:"assist",status,pipeline,engine,processed_locally,
        response_type,has_error:(.error != null),progress_event_count,
        event_count,events_truncated} | select(.status == "ok")' \
        <<<"$assist_output"
else
    jq -n '{check:"assist",status:"skipped",
        reason:"Set HA_DEV_SMOKE_ASSIST=1 for the production pipeline query"}'
fi
