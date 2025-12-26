/**
 * Plot Explorer JavaScript Module
 *
 * Handles fetching data from the plot API and rendering Plotly charts.
 */

// Global state
let indicators = [];
let countries = [];

// Load indicators and countries on page load
document.addEventListener("DOMContentLoaded", function () {
  loadIndicators();
  loadCountries();
});

/**
 * Fetch available indicators from API
 */
async function loadIndicators() {
  try {
    const response = await fetch("/api/plot/indicators");
    const data = await response.json();

    if (data.indicators) {
      indicators = data.indicators;
      populateIndicatorDropdown(data.indicators);
    }
  } catch (error) {
    console.error("Error loading indicators:", error);
    showError("Failed to load indicators. Please refresh the page.");
  }
}

/**
 * Fetch available countries from API
 */
async function loadCountries() {
  try {
    const response = await fetch("/api/plot/countries");
    const data = await response.json();

    if (data.countries) {
      countries = data.countries;
      populateCountryDropdown(data.countries);
    }
  } catch (error) {
    console.error("Error loading countries:", error);
    showError("Failed to load countries. Please refresh the page.");
  }
}

/**
 * Populate indicator dropdown
 */
function populateIndicatorDropdown(indicators) {
  const select = document.getElementById("indicators");
  select.innerHTML = "";

  // Group by source
  const grouped = {};
  indicators.forEach((ind) => {
    const source = ind.source || "other";
    if (!grouped[source]) grouped[source] = [];
    grouped[source].push(ind);
  });

  // Create optgroups
  Object.keys(grouped)
    .sort()
    .forEach((source) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = source.toUpperCase();

      grouped[source].forEach((ind) => {
        const option = document.createElement("option");
        option.value = ind.code;
        option.textContent = `${ind.name} (${ind.code})`;
        option.title = ind.description || ind.name;
        optgroup.appendChild(option);
      });

      select.appendChild(optgroup);
    });
}

/**
 * Populate country dropdown
 */
function populateCountryDropdown(countries) {
  const select = document.getElementById("countries");
  select.innerHTML = "";

  countries.forEach((country) => {
    const option = document.createElement("option");
    option.value = country.code;
    option.textContent = `${country.name} (${country.code})`;
    select.appendChild(option);
  });
}

/**
 * Generate plot based on user selections
 */
async function generatePlot() {
  // Get selections
  const indicatorSelect = document.getElementById("indicators");
  const countrySelect = document.getElementById("countries");
  const startYear = document.getElementById("start-year").value;
  const endYear = document.getElementById("end-year").value;
  const chartType = document.getElementById("chart-type").value;

  const selectedIndicators = Array.from(indicatorSelect.selectedOptions).map(
    (opt) => opt.value
  );
  const selectedCountries = Array.from(countrySelect.selectedOptions).map(
    (opt) => opt.value
  );

  // Validate
  if (selectedIndicators.length === 0) {
    showError("Please select at least one indicator");
    return;
  }

  if (selectedCountries.length === 0) {
    showError("Please select at least one country");
    return;
  }

  // Show loading
  showLoading();
  hideError();
  hideWarning();

  try {
    // Build API URL
    const params = new URLSearchParams({
      indicators: selectedIndicators.join(","),
      countries: selectedCountries.join(","),
      chart_type: chartType,
    });

    if (startYear) params.append("start_year", startYear);
    if (endYear) params.append("end_year", endYear);

    const url = `/api/plot/data?${params.toString()}`;

    // Fetch data
    const response = await fetch(url);
    const data = await response.json();

    if (data.error) {
      showError(data.error);
      hideLoading();
      return;
    }

    // Show warning if partial results
    if (data.warning) {
      showWarning(data.warning);
    }

    // Render chart
    if (data.transformed) {
      renderChart(
        data.transformed,
        chartType,
        selectedIndicators,
        selectedCountries
      );
    } else {
      renderChart(data.data, chartType, selectedIndicators, selectedCountries);
    }

    hideLoading();
  } catch (error) {
    console.error("Error generating plot:", error);
    showError("Failed to generate plot. Please try again.");
    hideLoading();
  }
}

/**
 * Render Plotly chart based on type
 */
function renderChart(data, chartType, indicators, countries) {
  const chartDiv = document.getElementById("plotly-chart");

  if (chartType === "line") {
    renderLineChart(data, chartDiv, indicators, countries);
  } else if (chartType === "bar") {
    renderBarChart(data, chartDiv, indicators, countries);
  } else if (chartType === "scatter") {
    renderScatterChart(data, chartDiv, indicators, countries);
  } else if (chartType === "choropleth") {
    renderChoroplethMap(data, chartDiv, indicators);
  }
}

/**
 * Render line chart (time series)
 */
function renderLineChart(data, chartDiv, indicators, countries) {
  const traces = [];

  // Data format: {indicator: {country: {year: value}}}
  Object.keys(data).forEach((indicator) => {
    Object.keys(data[indicator]).forEach((country) => {
      const years = Object.keys(data[indicator][country]).sort();
      const values = years.map((year) => data[indicator][country][year]);

      traces.push({
        x: years,
        y: values,
        mode: "lines+markers",
        name: `${country} - ${indicator}`,
        line: { width: 2 },
        marker: { size: 6 },
      });
    });
  });

  const layout = {
    title: "Time Series Analysis",
    xaxis: { title: "Year" },
    yaxis: { title: "Value" },
    hovermode: "closest",
    showlegend: true,
  };

  Plotly.newPlot(chartDiv, traces, layout, { responsive: true });
}

/**
 * Render bar chart (comparison)
 */
function renderBarChart(data, chartDiv, indicators, countries) {
  const traces = [];

  // Data format: {country: {indicator: {year, value}}}
  indicators.forEach((indicator) => {
    const x = [];
    const y = [];

    Object.keys(data).forEach((country) => {
      if (data[country][indicator]) {
        x.push(country);
        y.push(data[country][indicator].value);
      }
    });

    traces.push({
      x: x,
      y: y,
      type: "bar",
      name: indicator,
    });
  });

  const layout = {
    title: "Country Comparison",
    xaxis: { title: "Country" },
    yaxis: { title: "Value" },
    barmode: "group",
  };

  Plotly.newPlot(chartDiv, traces, layout, { responsive: true });
}

/**
 * Render scatter plot (correlation)
 */
function renderScatterChart(data, chartDiv, indicators, countries) {
  const x = [];
  const y = [];
  const text = [];

  // Data format: {country: {indicator1: value, indicator2: value}}
  const ind1 = indicators[0];
  const ind2 = indicators[1] || indicators[0];

  Object.keys(data).forEach((country) => {
    if (
      data[country][ind1] !== undefined &&
      data[country][ind2] !== undefined
    ) {
      x.push(data[country][ind1]);
      y.push(data[country][ind2]);
      text.push(country);
    }
  });

  const trace = {
    x: x,
    y: y,
    mode: "markers",
    type: "scatter",
    text: text,
    marker: { size: 12, color: "#667eea" },
  };

  const layout = {
    title: `Correlation: ${ind1} vs ${ind2}`,
    xaxis: { title: ind1 },
    yaxis: { title: ind2 },
    hovermode: "closest",
  };

  Plotly.newPlot(chartDiv, [trace], layout, { responsive: true });
}

/**
 * Render choropleth map
 */
function renderChoroplethMap(data, chartDiv, indicators) {
  const locations = [];
  const z = [];
  const text = [];

  // Data format: {country: {year, value}}
  Object.keys(data).forEach((country) => {
    locations.push(country);
    z.push(data[country].value);
    text.push(`${country}: ${data[country].value}`);
  });

  const trace = {
    type: "choropleth",
    locations: locations,
    z: z,
    text: text,
    colorscale: "Viridis",
    autocolorscale: false,
    reversescale: false,
    marker: {
      line: {
        color: "rgb(180,180,180)",
        width: 0.5,
      },
    },
    colorbar: {
      title: indicators[0],
    },
  };

  const layout = {
    title: `Global Distribution: ${indicators[0]}`,
    geo: {
      projection: {
        type: "natural earth",
      },
    },
  };

  Plotly.newPlot(chartDiv, [trace], layout, { responsive: true });
}

/**
 * Show loading indicator
 */
function showLoading() {
  document.getElementById("loading").style.display = "block";
  document.getElementById("plotly-chart").style.display = "none";
  document.getElementById("generate-btn").disabled = true;
}

/**
 * Hide loading indicator
 */
function hideLoading() {
  document.getElementById("loading").style.display = "none";
  document.getElementById("plotly-chart").style.display = "block";
  document.getElementById("generate-btn").disabled = false;
}

/**
 * Show error message
 */
function showError(message) {
  const errorDiv = document.getElementById("error");
  errorDiv.textContent = message;
  errorDiv.style.display = "block";
}

/**
 * Hide error message
 */
function hideError() {
  document.getElementById("error").style.display = "none";
}
