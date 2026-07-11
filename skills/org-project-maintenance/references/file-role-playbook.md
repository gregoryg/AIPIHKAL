# File Role Playbook

Use this reference when deciding *where* a piece of information belongs.

## Quick matrix

| Information type | Best file | Why |
|---|---|---|
| User-visible behavior | `README.org` | Users and future agents need current reality |
| Architecture / rationale / phase decisions | `PLANNING.org` | Durable intent and design memory |
| Active backlog / validation / deferred ideas | `TASKS.org` | Execution and state tracking |
| Agent workflow rules | `Agents.md` | Session behavior and tool discipline |
| Cross-team asks / focused requirements | dedicated `.org` note | Keeps planning files from swelling |

## Use README.org for
- newly available shortcuts
- interaction behavior users should know
- feature toggles users can operate
- troubleshooting notes tied to real user friction

## Use PLANNING.org for
- dated decisions
- explicit tradeoffs
- phased rollout plans
- architecture guardrails
- distinctions like active tile vs selected letter
- statements like "experimental now; may change after testing"

## Use TASKS.org for
- current work item status
- backlog entries
- validation checklists
- done/deferred/experimental markers
- concise implementation notes that matter for follow-up

## Use a dedicated requirements note for
- backend API asks
- release planning packets
- migration plans
- concentrated design requirements too specific for the main planning file

## Anti-patterns
- Putting roadmap debate into README
- Putting long architecture essays into TASKS
- Duplicating the same long rationale in all docs
- Leaving important UX rationale only in chat
