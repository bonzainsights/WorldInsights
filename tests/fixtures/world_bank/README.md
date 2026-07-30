# Pinned World Bank fixtures

These files are offline provider-contract fixtures. They preserve the World Bank Indicators API response shape so unit tests never depend on network access.

- `population_page.json`: `SP.POP.TOTL`, year 2023.
- `gdp_per_capita_2023_page.json`: `NY.GDP.PCAP.CD`, year 2023, for Germany, Nepal, and the United States.

The GDP-per-capita values were verified against World Development Indicators on 2026-07-30. World Bank series are revision-prone, so these pinned values are test evidence, not a promise that the live API will never revise historical observations.
