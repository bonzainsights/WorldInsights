# Development process

## Rule

**One capability, one tested commit.**

For every change:

1. Define the capability and acceptance criteria.
2. Add or update the smallest relevant tests.
3. Implement the capability.
4. Run focused tests.
5. Run repository-wide validation available at that point.
6. Inspect the staged diff.
7. Commit only the intended files.

## Commit sequence

The planned order is:

1. product and architecture contract;
2. workspace and validation tooling;
3. canonical data contracts;
4. geography and period normalization;
5. first provider adapter;
6. static release builder;
7. compatibility engine;
8. explorer UI;
9. visualizations and provenance;
10. CI and static deployment.

## Commit messages

Use concise conventional prefixes such as `docs:`, `chore:`, `feat:`, `test:`, and `fix:`.
