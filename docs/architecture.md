# Architecture

## Static-first flow

```text
Provider APIs
    ↓
Scheduled ingestion and validation
    ↓
Canonical observations and coverage indexes
    ↓
Immutable static release assets
    ↓
Browser explorer
    ├── compatibility engine
    ├── query worker
    ├── visualizations
    └── optional edge fallback
```

## Layers

### Raw

Immutable provider responses with retrieval metadata and checksums.

### Normalized

Provider-independent geography IDs, normalized periods, units, observation status, and quality flags.

### Semantic

Canonical concepts, provider-specific indicator variants, approved equivalences, conversions, and operation rules.

### Serving

Small JSON catalogs, compact coverage indexes, and partitioned analytical assets.

## Main boundaries

- Provider adapters parse provider formats but cannot publish serving assets directly.
- The normalization pipeline owns canonical identity and validation.
- The compatibility engine never scans full observations to answer availability questions.
- The query planner emits only registered deterministic operations.
- The UI owns presentation state but not data semantics.

## Cost model

The MVP must work using GitHub Actions and a static host. Object storage and edge queries are escalation paths triggered by measured asset or browser-query limits.

Exact hosting quotas and prices are launch-time checks because provider policies change. Architecture must not depend on a fragile free-tier assumption.
