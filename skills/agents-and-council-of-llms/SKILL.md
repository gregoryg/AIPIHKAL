---
name: agents-and-council-of-llms
description: Convene multiple independent LLM perspectives, optionally anonymize and peer-review them, then adjudicate a single evidence-checked verdict. Use for consequential architecture decisions, red-team review, subjective tradeoffs, consistency checks, or role-based analysis where model/lens diversity adds value; use bounded-llm-delegation instead for a single child task.
---

# Council of LLMs

Act as Council Chair, not a vote counter. Solicit bounded independent views,
verify disputed claims, and synthesize the best answer.

Read `../bounded-llm-delegation/SKILL.md` before launching members. Its session,
deadline, process, artifact, least-privilege, and failure rules govern every
council call.

## Triage

Use a council only when independent perspectives can change the result:

- role-based analysis of a complex design;
- consequential red-team or migration review;
- genuine ambiguity or subjective tradeoffs;
- consistency/hallucination checks across repeated calls;
- explicit user request for multiple models.

Use one bounded delegate for isolated reconnaissance or summarization. Answer
directly for simple facts and unambiguous work.

## Protocol

1. **Research first when needed.** Build a compact fact brief from primary
   sources. Do not ask every member to rediscover the same repository.
2. **Choose council shape.** Use distinct lenses for complementary expertise or
   repeated identical prompts for consistency. Repeated calls to one model are
   not model diversity.
3. **Write one complete prompt file.** Include the user's request verbatim,
   verified facts, scope, mutation/tool limits, expected output, and stopping
   condition.
4. **Select current models.** Prefer Pi as the common harness and choose diverse
   provider/model IDs available through Pi. Verify stale identifiers before a
   large fan-out.
5. **Set bounded execution.** Choose per-member deadline, forced-kill grace, and
   concurrency. Make the parent shell-tool deadline longer than member deadline
   plus aggregation grace.
6. **Convene.** Preserve each prompt, child session, stdout/stderr, final output,
   status, and compiled transcript.
7. **Inspect failures.** Distinguish timeout, auth, stale model, quota, and model
   errors. Preserve successful seats; do not silently replace a failed model.
8. **Review only when useful.** Skip peer review when outputs substantially
   agree. Otherwise anonymize responses and request targeted critique/ranking.
9. **Adjudicate.** Verify consequential factual disputes with primary sources or
   local tools. Explain where the Chair rejects council claims.
10. **Log durable sessions.** Read `council_logs.org` when it exists (create it
    when needed), prepend a compact entry, and link the transcript/review
    artifacts. Do not paste full model output into the log.

## Convene

Role-based council:

```bash
skills/agents-and-council-of-llms/council-convene.sh \
  --prompt-file /path/to/council-prompt.md \
  --lenses 'Emacs Architecture,Performance and Persistence,Migration UX' \
  --models 'openai-codex/MODEL,anthropic/MODEL,google/MODEL' \
  --harness pi \
  --timeout 600 \
  --kill-after 20 \
  --max-concurrency 3
```

Consistency council:

```bash
skills/agents-and-council-of-llms/council-convene.sh \
  --prompt-file /path/to/problem.md \
  --count 3 \
  --models 'openai-codex/MODEL' \
  --harness pi
```

Always run `--dry-run` before expensive or wide fan-out. The default child policy
is no tools and no project context; the complete fact brief must therefore be
in the prompt. Pass `--context-policy project` only when members genuinely need
repository instructions/context. Councils never grant mutation authority.

Important options:

| Option | Meaning |
|--------|---------|
| `--harness` | Common authenticated harness; default Pi |
| `--models` | Comma-separated IDs understood by that harness |
| `--lenses` | Comma-separated expert roles |
| `--count` | Number of consistency members |
| `--timeout` | Per-member child deadline |
| `--kill-after` | Grace from TERM to forced KILL |
| `--max-concurrency` | Provider/local fan-out bound; default 4 |
| `--cwd` | Explicit child working directory |
| `--context-policy` | `none` or `project` |

Read [references/configuration.md](references/configuration.md) for model and
environment configuration.

## Peer review

Run only after inspecting the initial transcript:

```bash
skills/agents-and-council-of-llms/council-review.sh \
  --session ~/.local/state/bounded-llm-delegation/councils/SESSION \
  --reviewers "Devil's Advocate,Implementability Reviewer" \
  --model PROVIDER/MODEL \
  --harness pi \
  --timeout 600
```

The review script reads `problem.txt` and `context.txt`, anonymizes successful and
failed member outputs, launches persistent bounded reviewer sessions, and writes
`PEER_REVIEW.md`. Anonymity reduces authority/model anchoring; it does not make
responses independent after reviewers see all answers.

## Artifact contract

Each council session contains:

| Artifact | Purpose |
|----------|---------|
| `metadata.json` | Harness, models, lenses, cwd, deadlines, concurrency |
| `problem.txt`, `context.txt` | Exact shared task inputs |
| `*_PROMPT.txt` | Exact member/reviewer prompts |
| numbered `*.md` | Member responses, including explicit errors/partial output |
| `runs/` | Bounded-delegation metadata, session IDs, stdout/stderr, status |
| `FULL_TRANSCRIPT.md` | Initial compiled transcript |
| `review_key.txt` | Response anonymization map |
| `PEER_REVIEW.md` | Aggregated critiques |

New transcripts default to
`${XDG_STATE_HOME:-~/.local/state}/bounded-llm-delegation/councils/`, outside the
skill source tree. Historical in-tree ignored transcripts remain readable. Do
not use `/tmp` for the only copy of a consequential council.

## Synthesis rules

- Weight evidence and task fit, not majority.
- Separate verified facts, observations, and recommendations.
- Flag failed or timed-out seats; do not imply a full council succeeded.
- Verify surprising API, security, compatibility, and performance claims.
- Prefer concrete corrections over generic “add tests” advice.
- Keep full responses out of the parent context unless a dispute requires them.
- State the final decision and unresolved uncertainty plainly.
