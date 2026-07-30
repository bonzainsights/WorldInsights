# Product contract

## Purpose

WorldInsights is a constrained analytical playground for global public data. Users may select features, providers, countries, periods, transformations, and visualizations in different orders. After every selection, the system computes what remains valid.

The system must either:

1. produce a reproducible visualization from compatible data; or
2. explain precisely why the requested combination cannot be safely constructed and propose the smallest valid alternative.

## Core workflows

### Explore one indicator

Select an indicator, inspect valid geographies and periods, render a map or trend, and inspect provenance.

### Compare indicators

Select an operation and multiple indicators. The system computes shared geography and time coverage, validates semantics and units, then renders only valid aligned observations.

### Compare providers

Select provider variants of the same canonical concept. The system displays disagreement and methodological differences rather than silently averaging them.

### Start from a geography

Select a country or aggregate and discover indicators and periods available for it.

## First-release scope

- one provider: World Bank;
- 5–10 annual country-level indicators;
- one immutable release at a time plus historical release metadata;
- 2D map, line chart, scatter plot, ranked comparison, and table;
- URL-serializable exploration recipe;
- static hosting without an always-on backend.

## Non-goals

- arbitrary SQL or arbitrary code execution;
- causal inference;
- user accounts;
- private datasets;
- real-time streaming data;
- a mandatory 3D globe;
- automatic semantic matching without review.

## Product invariants

- Zero and missing are never conflated.
- Provider aggregates and countries are never silently joined.
- Derived values require registered transformation rules.
- Every displayed result exposes source, release, unit, quality, and transformation metadata.
- A shared recipe pins a data release and reconstructs the same analysis.
