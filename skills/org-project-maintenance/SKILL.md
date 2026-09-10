---
name: org-project-maintenance
description: Maintain software-project planning artifacts written in Org mode. Use when working in repos that treat README.org, PLANNING.org, TASKS.org, Agents.md, changelogs, or adjacent notes as durable project memory. Helps Claude decide what belongs in chat versus in project docs; record dated decisions; update backlog items and task states coherently; preserve experimental/deferred status; and keep Org-based project management clean, minimal, and historically useful.
license: Complete terms in LICENSE.txt
---

# Org Project Maintenance

Maintain project memory, not just project prose.

This skill is for repositories where Org files are part of the engineering surface: planning, backlog, decision log, session archaeology, release notes, and feature phasing all matter. Use it to keep project-management artifacts accurate, lightweight, and durable.

## Core mission

When a repo uses Org files for planning/tracking, do all of the following:
- Put information in the *right file*, not merely in the chat.
- Convert ephemeral reasoning into durable notes only when it will help future sessions.
- Record design decisions with dates and enough rationale to explain *why*.
- Keep backlog/task state coherent and low-noise.
- Preserve the distinction between *implemented*, *experimental*, *deferred*, and *abandoned*.
- Avoid turning planning files into rambling transcripts.

## Default operating stance

Assume the project has three layers of memory:
1. **Chat** = ephemeral coordination
2. **Code/tests** = executable truth
3. **Org docs** = durable intent, decisions, task tracking, and archaeology

Bias toward:
- brief chat summaries
- precise code changes
- durable Org updates for rationale, planning, and task state

Do **not** leave important architecture/UX rationale trapped only in the chat if it will matter later.

## Canonical file roles

Use the repo's own conventions first. If the repo has similar files, these are the default meanings.

### `README.org`
User-facing reality.

Put here:
- current features and behavior
- user-visible shortcuts
- workflow changes a solver/operator will notice
- major configuration notes
- concise troubleshooting guidance

Do not put here:
- speculative roadmap detail
- long decision rationale
- backlog mechanics
- internal debates unless users must know them

### `PLANNING.org`
Intent, architecture, phased plans, decisions.

Put here:
- dated design decisions
- architectural guardrails
- phased rollout plans
- explicit UX tradeoffs and rationale
- stable project direction
- distinctions like implemented vs experimental vs deferred

Do not put here:
- minute-by-minute implementation log
- every bug fix unless it changed design understanding
- noisy task checkbox churn

### `TASKS.org`
Execution surface.

Put here:
- active work items
- backlog entries
- validation checklists
- DONE/DEFERRED/EXPERIMENTAL markers
- concise notes about implementation status

Do not put here:
- long architectural essays
- duplicated README behavior descriptions
- speculative brainstorming with no likely follow-through

### `Agents.md` / `AGENTS.md`
Behavioral operating instructions for agents.

Put here only when changing agent workflow expectations:
- mandatory startup reads
- tool discipline
- commit-message conventions
- repo workflow rules

Do not edit casually during a feature unless the human asks or the workflow itself has changed.

### Feature notes / ad hoc `.org` docs
Use when a topic deserves focused requirements or cross-team handoff.

Examples:
- backend feature requirements
- migration notes
- release planning
- API asks
- deep design notes too specific for PLANNING.org

## Chat vs document rules

### Put it in chat only when:
- it is a short coordination note
- it is a question for the human
- it is a transient implementation thought
- it would clutter the durable docs more than help

### Put it in Org docs when:
- future-you or future-agents will need the rationale
- a behavior changed in a way users will feel
- a feature is being phased experimentally
- a task changed state
- a design choice was made between plausible alternatives
- a workaround was rejected for UX/architecture reasons and that rejection matters

### Strong default
If the reasoning changes future implementation choices, it probably belongs in `PLANNING.org` or `TASKS.org`, not only in chat.

## Decision-log rules

Use dated decision entries for choices that affect future work.

### Good candidates
- feature phasing decisions
- UX interaction semantics
- persistence strategy
- state-model changes
- API-contract assumptions
- known intentional compromises
- implementation approach chosen over alternatives

### Entry shape
Use concise dated headings:

```org
** 2026-04-23 — Keyboard Navigation Phasing
Short paragraph explaining the decision and the why.

- Optional bullet for phase breakdown
- Optional bullet for explicit guardrail
```

### Style rules
- Lead with the decision, not the full historical story.
- Include *why* in one short paragraph.
- Use bullets only for structured subpoints, not as a substitute for prose.
- If a feature is provisional, say so explicitly.
- If later phases depend on a state-model distinction, name it directly.

### Do not log:
- trivial implementation details
- noisy refactor steps
- obvious corrections unless they changed project understanding

## Task lifecycle semantics

Prefer the repo's own states. If the repo uses custom status prose, mirror that. Otherwise use these working meanings.

### `TODO`
Not started; intended work.

### `STARTED`
Actively in progress in this session or currently owned.

### `IN-TEST`
Implemented but still awaiting validation, especially on device/browser or with user acceptance test confirmation.

### `DONE`
Implemented and validated enough for the repo's standard.

### `DEFERRED`
Good idea, intentionally postponed. Use only when the postponement itself matters.

### `EXPERIMENTAL`
Implemented for evaluation, not yet accepted as stable product behavior.

### `BLOCKED`
Cannot proceed without external dependency, API change, asset, or human decision.

To use the above lifecycle, insert the following after the frontmatter:
```
#+todo: TODO STARTED IN-TEST BLOCKED | DONE DEFERRED
```

## Backlog hygiene rules

### Add a new backlog item when:
- the work is meaningfully distinct
- it could be completed or deferred independently
- it needs to be remembered across sessions

### Add notes under an existing item when:
- you are refining the same work item
- validation details belong with that task
- the design changed but the task identity did not

### Mark `DEFERRED` rather than leaving a vague TODO when:
- the idea is intentionally parked
- doing it now would confuse evaluation of another feature
- it is a power-user enhancement for later

### Mark `EXPERIMENTAL` when:
- the behavior is live but under evaluation
- a toggle exists to compare workflows
- the human has signaled likely iteration after hands-on use

### Move to recently completed / done when:
- the feature landed and basic validation passed
- the task would otherwise continue cluttering active work

## Minimalism rules for project docs

Project docs should be information-dense, not exhaustive.

Prefer:
- small, precise edits
- appending to the right section
- refining existing bullets instead of duplicating them
- short prose paragraphs over sprawling bullet dumps

Avoid:
- repeating the same rationale in README + PLANNING + TASKS unless each audience needs it
- copying long chat explanations verbatim into Org files
- adding TODOs for every passing idea
- turning `TASKS.org` into a diary

## Experimental feature rules

When a feature is under evaluation:
- mark it clearly as experimental in `PLANNING.org` and/or `TASKS.org`
- explain what behavior is being tested
- record the current decision separately from the fact that it may change
- if exposed in UI, note why it is temporary or lightweight

Example uses:
- temporary toggle instead of full preferences system
- provisional navigation semantics
- workaround being tried before a fuller solution exists

## Reverted or rejected changes

When a change is implemented and then reverted, document it *only if* the rejection teaches something durable.

Good reasons to note a rejection:
- UX mismatch
- architecture conflict
- browser/platform limitation
- deliberate preference for a lighter pattern

Bad reasons to note a rejection:
- momentary false start with no lasting consequences

## Session-end checklist for Org-managed repos

Before wrapping up, consider whether the repo now needs updates to:
- `README.org` for user-visible changes
- `PLANNING.org` for durable reasoning or phase decisions
- `TASKS.org` for state transitions, deferred ideas, validation items
- a focused `.org` note for cross-team/API requirements

If the answer is yes, make the edits before declaring the work done.

## Preferred writing style

- Use clear, plain language.
- Favor short explanatory paragraphs over bullet spam.
- Use bullets for lists, phases, acceptance points, or checklists.
- Keep headings informative and date-stamped when recording decisions.
- Match the repo's existing tone.

## Practical examples

Read these only as needed:
- `references/file-role-playbook.md` for where information belongs
- `references/decision-log-patterns.md` for dated entry patterns
- `references/task-state-semantics.md` for status guidance
- `references/chat-to-org-translation.md` for converting chat reasoning into durable notes

## Final rule

Do not be a tourist in the planning files.

Treat Org project artifacts as living engineering tools. Update them when the work changes project memory; leave them alone when the chat or code already carries the full truth.
