# Direct HTTP model calls

Use direct HTTP only when a stateless model completion is preferable to a
resumable harness. A provider endpoint is not automatically an agent loop.

## Contents

- [Use cases](#use-cases)
- [Required boundaries](#required-boundaries)
- [Safe request construction](#safe-request-construction)
- [Retries and streaming](#retries-and-streaming)
- [Artifacts and secrets](#artifacts-and-secrets)

## Use cases

Good fits:

- classify or transform bounded text;
- request structured output from a known schema;
- compare a small prompt across providers;
- call a model not exposed by an installed harness.

Prefer a harness when repository tools, provider-specific auth refresh,
conversation resumption, compaction, or multi-turn tool use matters.

## Required boundaries

Every call needs:

- explicit endpoint and API version;
- connect timeout and total timeout;
- maximum response size;
- HTTP status validation with body preservation;
- bounded retry policy;
- model and request ID logging;
- schema validation before consuming output;
- redaction of credentials and sensitive content.

A sensible curl baseline is:

```bash
curl --silent --show-error --fail-with-body \
  --connect-timeout 10 \
  --max-time 180 \
  --retry 2 \
  --retry-delay 1 \
  --retry-max-time 240 \
  --output response.json \
  --data-binary @request.json \
  "$ENDPOINT"
```

Provider rate-limit semantics differ. Honor `Retry-After` where available and
avoid retrying invalid credentials, invalid model IDs, or schema errors.

## Safe request construction

Build JSON with `jq` or a language JSON library, never string interpolation:

```bash
jq -n \
  --arg model "$MODEL" \
  --rawfile prompt prompt.txt \
  '{model: $model, input: $prompt}' > request.json
```

Do not put prompt text or API keys directly in argv. Prefer a provider SDK or a
curl config/header file supplied through a private file descriptor when header
secrets would otherwise appear in the process list. Set private artifact
permissions with `umask 077`.

## Retries and streaming

Separate connect, request, and outer process deadlines. A stalled stream must
still hit a total deadline. Preserve partial stream bytes for diagnosis, but do
not treat an unterminated stream as a valid final response.

Bound retries by both attempt count and total elapsed time. Add jitter in custom
retry loops to avoid synchronized fan-out retries. Record the final attempt and
HTTP/request IDs.

Validate streamed event framing and the provider's explicit completion marker.
Do not parse arbitrary newline-delimited chunks as complete JSON objects unless
the protocol guarantees that framing.

## Artifacts and secrets

Retain, as policy permits:

- redacted request or prompt hash;
- endpoint host and API version;
- model;
- start/end timestamps;
- HTTP status and response headers needed for diagnosis;
- request ID;
- raw bounded response;
- normalized result and validation status.

Never retain bearer tokens, cookies, signed URLs, raw authorization headers, or
unredacted sensitive prompts in shared logs. A direct call has no native
resumable session; durable request/response artifacts are its only recovery
record.
