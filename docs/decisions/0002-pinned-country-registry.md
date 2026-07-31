# 0002: Pin the global ISO country registry

## Status

Accepted.

## Decision

WorldInsights derives its global ISO-3166 country and territory registry from the exact dependency `pycountry==24.6.1`.

The registry assigns dense, one-based internal geography IDs so browser coverage bitsets remain compact. The original MVP IDs remain permanently reserved:

- Germany (`DEU`) = 1
- Nepal (`NPL`) = 2
- United States (`USA`) = 3

All remaining ISO entries are assigned deterministically by alpha-3 code. Alpha-3 codes remain the canonical external identity, while three-digit M49 codes provide the join key for pinned world-atlas geometry.

## Consequences

- The same dependency version always produces the same 249-entry registry.
- Upgrading the source package requires an explicit reviewed dependency change.
- Internal IDs are implementation identifiers and must not be inferred from alphabetical position outside the registry.
- Sovereign-country versus territory classification remains a separate curated step before entries are emitted as canonical WorldInsights geographies.
