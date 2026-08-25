# Harness adapters

Use this reference when selecting or debugging a launcher adapter. CLI surfaces
were checked on 2026-08-25 against Pi 0.84.3, Codex CLI 0.149.1, OpenCode 1.4.3,
Claude Code 2.1.92, Hermes 0.14.0, and Gemini CLI 0.37.1. Recheck `--help` after
upgrades; wrappers which document imaginary flags are worse than no wrapper.

## Contents

- [Pi](#pi)
- [Codex](#codex)
- [OpenCode](#opencode)
- [Claude](#claude)
- [Hermes](#hermes)
- [Gemini](#gemini)
- [Policy comparison](#policy-comparison)

## Pi

Preferred generic child harness.

```bash
pi --session-id UUID --name NAME \
  --model PROVIDER/MODEL --thinking high \
  --tools read,grep,find,ls --print < prompt.md
```

Relevant controls:

- persistence is default; `--no-session` disables it;
- resume with `--session PATH_OR_ID` or `--continue`;
- choose exact provider/model with `--provider` and `--model`;
- use `--tools`, `--no-tools`, and `--exclude-tools` for least privilege;
- use `--no-context-files`, `--no-extensions`, `--no-skills`, and
  `--no-prompt-templates` for an isolated pure-model call;
- use `--mode json` when the event stream matters.

Pi accepts piped prompt text in print mode, keeping prompts out of argv. Child
processes inherit `PI_*` metadata from the parent shell, but do not inherit the
parent conversation. An explicit child session ID prevents accidental reuse.

## Codex

```bash
codex exec --sandbox read-only --cd "$PWD" \
  --json --output-last-message final.md - < prompt.md
```

Relevant controls:

- persistence is default; never add `--ephemeral` casually;
- initial runs emit a thread/session ID in JSON events;
- resume with `codex exec resume SESSION_ID - < follow-up.md`;
- use `--sandbox read-only` for review work;
- use `--ignore-rules` when project instructions must be excluded deliberately;
- `--output-last-message` is written only after a completed final response.

Capture JSON events separately from `final.md`. If the outer shell kills Codex
before the final turn, the event log and persisted session remain the recovery
path. Resume options are narrower than initial `exec` options; the session
retains important initial policy.

## OpenCode

```bash
opencode run --model PROVIDER/MODEL --format json \
  --title NAME --dir "$PWD" "PROMPT"
```

Relevant controls:

- sessions persist by default;
- resume with `--session ID` or `--continue`;
- use `--pure` to exclude external plugins;
- choose model variant/reasoning with `--variant`;
- there is no documented strict no-tool/read-only flag comparable to Pi or
  Codex in `opencode run`.

The current CLI takes prompt text as positional argv. Do not include secrets or
very large prompts. Treat read-only instructions as best-effort unless an
external sandbox enforces them.

## Claude

```bash
claude --print --output-format stream-json \
  --session-id UUID --name NAME --model MODEL \
  --permission-mode plan --tools Read,Grep,Glob < prompt.md
```

Relevant controls:

- persistence is default; `--no-session-persistence` disables it;
- resume with `--resume SESSION_ID` or `--continue`;
- use `--permission-mode plan` and `--tools` for review-only work;
- use `--max-budget-usd` for a hard model-spend boundary;
- use `--include-partial-messages` with stream JSON for recoverable progress;
- print mode skips the workspace trust dialog, so use only a trusted cwd.

`--bare` reduces prompt/runtime machinery but also disables OAuth/keychain auth
for Anthropic. Do not select it merely to save tokens when subscription auth is
required.

## Hermes

```bash
hermes --oneshot "PROMPT" --model PROVIDER/MODEL --pass-session-id
```

Relevant controls:

- resume with `--resume ID` or `--continue [NAME]`;
- choose provider/model with `--provider` and `--model`;
- select toolsets with `--toolsets`;
- exclude project rules with `--ignore-rules`;
- one-shot mode intentionally auto-bypasses approvals;
- one-shot prompt text is an argv value and final stdout omits session metadata.

Because approval bypass is intrinsic to one-shot mode, use an external sandbox
or a narrowly configured toolset and require explicit acceptance. The generic
launcher refuses Hermes without `--allow-auto-approve`.

## Gemini

```bash
gemini --approval-mode plan --output-format stream-json \
  --model MODEL --prompt "" < prompt.md
```

Relevant controls:

- sessions persist by default;
- list with `--list-sessions` and resume with `--resume ID_OR_INDEX`;
- `--approval-mode plan` is the read-only review mode;
- use `--include-directories` only when additional roots are intended;
- prefer policy files over deprecated `--allowed-tools`;
- avoid `--raw-output` for untrusted model text.

The headless prompt flag can consume stdin in addition to its argument. The
launcher supplies an empty argument and sends the real prompt through stdin.

## Policy comparison

| Harness | Persistent default | Chosen session ID | Enforced read-only | Prompt via stdin | Structured output |
|---------|--------------------|-------------------|--------------------|------------------|-------------------|
| Pi | yes | yes | strong tool allowlist | yes | JSON |
| Codex | yes | no | sandbox | yes | JSONL |
| OpenCode | yes | no | not directly documented | no | JSON events |
| Claude | yes | yes | plan mode/tool list | yes | JSON/stream JSON |
| Hermes | yes | not for one-shot | no; auto-approves | no | final text |
| Gemini | yes | no | plan mode | yes | JSON/stream JSON |

When policy cannot be enforced by the harness, use an OS sandbox or choose a
different harness. A prompt saying “do not edit” is not a permission boundary.
