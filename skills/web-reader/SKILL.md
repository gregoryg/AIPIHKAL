---
name: web-reader
description: Read public HTTP(S) webpages with the local web-reader CLI using bounded GET-only static extraction and explicit Playwright rendering. Use when the harness has no adequate first-class URL reader, its native reader fails or returns unusable content without a comparable fallback, or the user explicitly asks to exercise web-reader; do not replace a working read_web or read_webpage tool with this skill.
---

# Web reader

Use `web-reader` as a fallback capability, not as a parallel path around a good
harness-native webpage reader.

## Choose the interface

1. Prefer an available `read_web`, `read_webpage`, or equivalent tool when it
   already provides bounded static extraction and explicit browser rendering.
2. Otherwise verify that `web-reader` is installed:

   ```bash
   command -v web-reader
   web-reader --version
   ```

3. If it is absent, report that dependency clearly. Do not install software or
   improvise a less safe network stack without user authorization.

## Read static content first

Invoke the command through an argv-style subprocess API when the harness offers
one. When only a shell command is available, quote the URL as untrusted input;
never concatenate URL text into shell syntax.

```bash
web-reader read --url 'https://example.com/page' --mode static --output json
```

Inspect the structured response rather than treating process success alone as
proof of useful extraction:

- `ok` distinguishes success from a structured failure.
- `content` contains bounded Markdown.
- `finalUrl` records the post-redirect source.
- `extractor`, `redirects`, `timingMs`, and `truncation` explain the result.
- a nonzero exit status accompanies failures.

Answer from static output when it contains the material needed for the task.
Do not escalate merely because the page is visually complex or the answer
requires careful reading.

## Escalate deliberately

Retry with browser mode only when there is concrete evidence that useful content
requires JavaScript, such as an empty application shell, a script-required
placeholder, or requested material demonstrably absent from the static result.
If an equivalent native tool exposes browser mode, retry through that tool
rather than dropping to the CLI.

```bash
web-reader read --url 'https://example.com/app' --mode browser --output json
```

Browser mode executes untrusted page code, starts Chrome/Chromium, and has a
larger and weaker network boundary than static mode. It uses a fresh context,
not the user's authenticated browser profile. A login wall, paywall, CAPTCHA,
or authorization failure is not by itself justification to evade the site with
browser mode.

The command never escalates automatically. Record which mode supplied the final
answer when that distinction matters.

## Respect refusal boundaries

The executable permits public HTTP(S) GET requests only. It rejects embedded URL
credentials and non-public destinations, including loopback, private,
link-local, multicast, and reserved addresses. It also validates redirects.

- Treat `PRIVATE_ADDRESS`, `URL_CREDENTIALS`, and `UNSUPPORTED_PROTOCOL` as stop
  conditions; do not attempt alternate spellings, redirects, or encodings to
  bypass them.
- Use an explicitly authorized local-system tool for private or internal URLs.
- Use a format-specific tool for PDFs and other unsupported binary content.
- Do not use this reader for form submission, authenticated browser workflows,
  downloads, or other non-GET interactions.
- Keep default limits unless the task provides a concrete reason for a modest
  increase. Never turn a webpage read into an unbounded context dump.

On failure, report the error code and useful diagnostic. Do not present an empty
or policy-blocked result as evidence about the page's contents.
