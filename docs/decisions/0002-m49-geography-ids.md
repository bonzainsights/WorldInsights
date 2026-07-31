# ADR 0002: Use UN M49 codes as canonical country geography IDs

## Status

Accepted for new V2 country releases.

## Decision

WorldInsights uses the numeric UN M49 country or area code as `geography_id` for country-level V2 releases.

Examples:

- Germany: `276`
- Nepal: `524`
- United States: `840`

The frozen V1 compatibility fixture keeps its historical internal IDs (`1`, `2`, `3`) and is rebuilt through an explicit legacy-only remapping step.

## Rationale

M49 IDs are stable, numeric, compact enough for the current coverage bitset representation, and directly match the IDs in the version-pinned world-atlas geometry. This avoids maintaining a second browser-only ISO3-to-geometry lookup when global country coverage is introduced.

## Consequences

- Existing V2 exploration recipes are release-bound and will not silently cross the ID migration.
- New V2 observations, geography catalogs, and coverage files use M49 IDs.
- Aggregates remain outside the country M49 namespace.
- The browser map can migrate to joining geometry by `geography_id` directly.
