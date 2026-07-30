# ADR 0001: Static-first analytical architecture

- Status: Accepted
- Date: 2026-07-30

## Context

WorldInsights needs cross-provider exploration, but the first release must remain inexpensive to host and simple to operate. Most source datasets update periodically rather than per user request.

## Decision

Build immutable normalized releases during scheduled jobs and execute ordinary compatibility and analytical work in the browser. Keep an edge query service optional.

## Consequences

### Positive

- No always-on application server is required.
- Releases are reproducible and easy to roll back.
- Static assets can be cached aggressively.
- Provider rate limits do not affect interactive users.

### Negative

- Release size and browser memory require explicit budgets.
- Some large joins may eventually need an edge execution path.
- Provider freshness is bounded by the release schedule.

## Guardrail

Do not add backend infrastructure until measured common queries exceed browser or static-host budgets after partitioning and caching improvements.
