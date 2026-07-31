# Pinned World Bank fixtures

These files are offline provider-contract fixtures. They preserve the World Bank Indicators API response shape so unit tests never depend on network access.

- `population_page.json`: frozen legacy `SP.POP.TOTL` fixture for the V1 contract.
- `gdp_per_capita_2023_page.json`: frozen 2023 `NY.GDP.PCAP.CD` provider-contract fixture.
- `population_2019_2023_page.json`: `SP.POP.TOTL` for Germany, Nepal, and the United States, 2019–2023.
- `gdp_per_capita_2019_2023_page.json`: `NY.GDP.PCAP.CD` for the same countries and years.

The 2019–2023 values were verified against World Development Indicators on 2026-07-30. World Bank series are revision-prone, so these pinned files are reproducible release evidence, not a promise that future API vintages will preserve the same historical values.
