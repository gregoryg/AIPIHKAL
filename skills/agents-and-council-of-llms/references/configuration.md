# Council configuration

Use Pi as the default harness. Configure current Pi model IDs rather than
copying example identifiers which will rot.

## Contents

- [Model sources](#model-sources)
- [Environment](#environment)
- [Choosing a council](#choosing-a-council)
- [Harness alternatives](#harness-alternatives)
- [Deadline sizing](#deadline-sizing)

## Model sources

Resolution order:

1. `--models`;
2. `COUNCIL_MODELS`;
3. `COUNCIL_MODELS_FILE` (default `~/.config/council/models.conf`);
4. active `PI_PROVIDER`/`PI_MODEL` when invoked inside Pi;
5. selected harness default model.

Use one model per line in the config file:

```text
# Verify these with `pi --list-models` on the current installation.
openai-codex/CURRENT_MODEL
anthropic/CURRENT_MODEL
google/CURRENT_MODEL
```

List current models with the selected harness before relying on identifiers:

```bash
pi --list-models
opencode models
claude --help
```

Model names and authentication surfaces change. A failed seat should remain a
failed seat until the Chair explicitly chooses a replacement.

## Environment

| Variable | Purpose | Default |
|----------|---------|---------|
| `COUNCIL_HARNESS` | Child harness | `pi` |
| `COUNCIL_MODELS` | Comma-separated models | active Pi model/harness default |
| `COUNCIL_MODELS_FILE` | One-model-per-line config | `~/.config/council/models.conf` |
| `COUNCIL_REVIEW_MODEL` | Peer-review model | first configured/active model |
| `COUNCIL_TIMEOUT` | Per-child deadline seconds | `300` |
| `COUNCIL_KILL_AFTER` | TERM-to-KILL grace seconds | `20` |
| `COUNCIL_MAX_CONCURRENCY` | Concurrent children | `4` |
| `COUNCIL_TRANSCRIPTS_DIR` | Session root | XDG state `bounded-llm-delegation/councils/` |
| `COUNCIL_DELEGATE` | Launcher override for tests | sibling delegate script |
| `COUNCIL_DEBUG` | Verbose diagnostics | `0` |

Harnesses use their existing authenticated configuration. Council scripts do not
load or pass API keys.

## Choosing a council

Use 3--5 genuinely different models/lenses for broad deliberation. Use 2--3
repeated calls for consistency checks. More seats are not automatically better:
they consume quota, enlarge synthesis, and can repeat correlated training
biases.

Prefer explicit lenses which produce different evidence:

- product workflow/UX;
- native platform architecture;
- performance and persistence;
- migration and operations;
- adversarial security/recovery.

Avoid vague roles such as “smart expert” and “another smart expert.”

## Harness alternatives

`--harness` selects one adapter for all seats. Pi is preferred because one
harness can reach many providers while preserving a small common orchestration
surface.

Other adapters are available through `bounded-llm-delegation`, but policy and
model identifiers differ. Read its harness reference first. In particular,
OpenCode has weaker read-only enforcement and Hermes one-shot auto-approves
tools.

## Deadline sizing

For a parallel council:

```text
parent deadline >= member deadline + kill-after + transcript/synthesis grace
```

For peer review, apply the same rule separately. Do not give the initial council
and peer review one shared opaque deadline.

Start around:

- 120--300 seconds for short no-tool opinions;
- 600--900 seconds for high-reasoning reviews;
- longer work only under an observable supervisor such as tmux.

A deadline should bound work, not force every model to rush. Preserve the child
session and resume with a narrower “stop researching and return findings” prompt
when inspection consumed the first run.
