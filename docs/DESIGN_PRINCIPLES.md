# Design principles

Hey, revise as the project matures. Defaults below are minimal—expand with rules for **your** codebase.

1. **Explicit contracts** — Document supported replayt (and third-party framework) versions; test integration boundaries. The concrete public surface and version notes for this package live in [PUBLIC_API_SPEC.md](PUBLIC_API_SPEC.md).
2. **Small public surfaces** — Prefer narrow APIs and documented extension points.
3. **Observable automation** — Local scripts and CI produce clear logs and exit codes.
4. **Consumer-side maintenance** — Compatibility shims and pins live **here**; upstream changes are tracked with tests
   and changelog notes.
5. **Not a lever on core** — This repo does not exist to steer replayt core; propose upstream changes through normal
   channels.

## LLM / demos (if applicable)

Document models, secrets handling, cost and redaction expectations here or in MISSION.

**Telemetry:** Span and resource attributes are shipped to third-party observability systems. Apply the same redaction and
secret-handling rules you use for logs and traces elsewhere (no credentials in attributes; minimize PII). See
[SECURITY_REDACTION.md](SECURITY_REDACTION.md) for the complete redaction policy, which defines categories for
attributes that must never be emitted, should be hashed/truncated, or are safe to emit, with specific guidance for
LLM-related fields and references to OpenTelemetry semantic conventions.

## Audience (extend)

| Audience | Needs |
| -------- | ----- |
| **Maintainers** | Mission, scripts, pinned versions, release notes |
| **Integrators** | Stable adapter surface, compatibility matrix |
| **Contributors** | README, tests, coding expectations |
