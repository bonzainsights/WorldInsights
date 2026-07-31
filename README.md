# WorldInsights

WorldInsights is a compatibility-first global data explorer. It lets users combine indicators from one or more public-data providers, then validates geography, time, semantics, units, and operation rules before rendering a result.

The project is designed as a static-first analytical application:

- provider data is ingested and validated during scheduled builds;
- normalized releases are published as immutable static assets;
- compatibility checks run from compact indexes in the browser;
- bounded analytical work runs in a Web Worker;
- an edge service is optional, not required for the MVP.

## First public slice

The first vertical slice targets annual country-level World Bank indicators and supports:

- indicator discovery;
- dynamic country and period availability;
- map, trend, comparison, scatter, and table views;
- explicit missingness, unit, quality, and provenance information;
- versioned, shareable exploration recipes.

## Repository layout

```text
apps/web/                 Browser application
packages/contracts/       Shared TypeScript contracts
packages/compatibility/   Browser compatibility engine
pipeline/                 Python ingestion and release builder
data/                     Schemas, curated mappings, and fixtures
docs/                     Product, architecture, and decisions
.github/workflows/        Validation, release, and deployment workflows
```

## Development rule

Every commit introduces one coherent capability and must pass its relevant tests before publication. See [docs/development-process.md](docs/development-process.md).
