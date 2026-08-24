# Durable Commit Examples

These real messages illustrate judgment, not a mandatory house style. Inspect the
target repository before borrowing their subject syntax or body structure.

## Contents

- gptel: compact causal explanation
- gptel: honest limitation and implementation map
- gptel: proportional brevity
- org-fc: a deliberately separated contribution series
- A useful synthesis
- Lessons to carry forward

## gptel: compact causal explanation

From gptel commit `54197735aa2557eb9dd9554aab06afbd13e6b4a4`:

```text
gptel-request: Fix FSM hang when model calls unknown tool

* gptel-request.el (gptel--handle-tool-use): When the model calls
a tool name that doesn't match any registered tool-spec, the FSM
silently drops the call without calling process-tool-result,
leaving the state machine stuck in the TOOL state indefinitely.

Return an error result to the model listing available tools,
allowing the FSM to transition normally and the model to
self-correct.
```

Why it endures:

- The subject names the component, symptom, and event that triggers it.
- The first paragraph connects invalid input to the exact state-machine failure.
- The second explains both the remedy and the recovered behavior.
- The file and symbol anchor makes the rationale easy to locate in an Emacs tree.

## gptel: honest limitation and implementation map

From gptel commit `c91454c7b955f3ca8285375e937aa9b50c91c206`:

```text
gptel-anthropic: Support tools and JSON output together

Because the Anthropic backend provides JSON output as tool call
arguments, it was not possible in gptel to mix user-supplied tools
and JSON output when using it.  This is now mostly fixed, by
- not requiring that the JSON output tool be called, allowing the
model to call other tools first if required,
- and orchestrating streaming callback calls to present the JSON
tool call arguments as the response.

Note: Streaming request processing will still miss some output if
the model calls both user-supplied and the JSON tool in the same
turn, but this is very unlikely.  To be sure, you can turn off
streaming when using Anthropic + structed outputs.

* NEWS (New features and UI changes): Mention changes
* gptel-anthropic.el (gptel--request-data): Don't force the use of
the JSON tool.
* gptel-request.el (gptel--handle-tool-use): Call the streaming
callback with t (to indicate end of stream) when processing the
JSON tool call arguments.
```

Why it endures:

- It explains the provider-specific representation that caused the limitation.
- “Mostly fixed” is substantiated by a precise remaining edge case and workaround.
- The final inventory maps behavior to documentation and two implementation sites.
- It does not hide design debt to make the change sound more complete than it is.

The original contains the spelling `structed`; retain historical messages when
quoting them, but proofread new messages independently.

## gptel: proportional brevity

From gptel commit `ebf0f3d8e9932e0ac6de82542220864cc17f6784`:

```text
gptel-openai-oauth: Require cl-lib at runtime

* gptel-openai-oauth.el: Byte compiler warning.
```

This tiny correction does not pretend to need an essay. The scoped subject and
single diagnostic are enough. Durable does not mean long.

## org-fc: a deliberately separated contribution series

The org-fc history separates a single review enhancement into implementation,
tests, and user documentation. Each commit is still a coherent contribution and
the subjects make the series legible in a short log.

### 1. Implementation

From commit `35f72d8b75598bb28a43bc97ffd390bd19399f65`:

```text
feat(review): track session progress counts

Capture the number of positions loaded into each scheduler after review
filtering and preserve it as the session's initial workload.

Count each successfully saved rating independently from the mutable scheduler
queue. This keeps completed work visible when "again" ratings requeue positions
or suspension removes pending siblings.
```

The message distinguishes immutable initial workload, mutable queue state, and
successful rating attempts. It also records the two edge cases that make separate
counters necessary. The diff changes only `org-fc-review.el`.

### 2. Tests

From commit `868f637853ed3311d464d72ef70d75798e778f56`:

```text
test(review): cover session progress accounting

Verify that sessions retain their initial workload while successful rating
attempts advance the rated count.

Exercise the again path to confirm that it increments progress and returns
the position to the queue without changing the initial count.

Ensure a failed rating update does not advance session progress.
```

Each paragraph states an invariant, not merely the name of a test. The test-only
diff becomes a readable behavioral specification.

### 3. User documentation

From commit `f3abdae37a6ae14e5786b90a3fd853dfc7ea8433`:

```text
docs(review): show progress in custom header lines

Explain the built-in review header, the distinction between initial, rated,
and remaining position counts, and the effects of requeueing and suspension.

Provide a working org-fc-after-setup-hook example which displays phase and
session progress while retaining file-title and ancestor context.

Record the new session metadata in the changelog and identify the internal
interfaces on which advanced header customization currently depends.
```

The documentation commit has a distinct reader-facing purpose. Its three files
form one unit: customization guidance, review semantics, and changelog notice.

This split is excellent for a project that values independently reviewable source,
tests, and documentation contributions. It is not a universal commandment. In a
repository that requires tests in the implementation commit, the same behavioral
work could reasonably be grouped differently.

## A useful synthesis

Conventional Commits and gptel's component prefixes express different dimensions:

- `feat`, `fix`, `docs`, and `test` classify the reason for a change;
- `gptel-request` identifies the component that owns the behavior; and
- the summary states the outcome.

When establishing or refining a repository convention, the two can be combined:

```text
fix(gptel-request): recover when models call unknown tools
feat(org-fc-review): track session progress counts
docs(org-fc-review): explain custom header progress
```

These are illustrative rewrites, not the historical subjects. They preserve the
machine-readable change kind while making the scope concrete and searchable.

The component need not be the only changed file. `gptel-request` can remain the
owner when NEWS, tests, or a backend adapter also changes. Conversely, a genuinely
cross-cutting change may be better served by a stable subsystem such as `review`
than by an arbitrary file name. The goal is a truthful semantic locator, not the
smallest or most mechanically precise label.

## Lessons to carry forward

The two histories use different subject dialects:

```text
gptel-request: Fix FSM hang when model calls unknown tool
feat(review): track session progress counts
```

Both succeed because they are consistent with their repositories, specific about
outcome, and short enough to scan. Do not normalize one into the other.

Across the examples, the strongest bodies do four things:

1. name the prior behavior or invariant;
2. connect cause to consequence;
3. state the new behavior and its boundaries; and
4. remain honest about limitations.

The diff supplies syntax. The message should preserve reasoning.
