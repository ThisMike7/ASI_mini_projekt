const API_BASE_URL = "http://127.0.0.1:8000";

const map = L.map("map").setView([20.0, 0.0], 2);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {

  maxZoom: 18,

  attribution: "© OpenStreetMap contributors",

}).addTo(map);

let markersLayer = L.layerGroup().addTo(map);

let rankingData = [];

let citiesData = [];

let currentSortColumn = "score";

let currentSortDirection = "desc";

let currentContinent = "All";

let currentHistoryContinent = "All";

let currentSearchTerm = "";

let historyChart = null;

let currentHistoryData = [];

let currentHistoryMetric = "score";
function getContinentLabel(continent) {

  return continent === "All" ? "all continents" : continent;

}

function getMarkerColor(score) {

  if (score >= 90) return "green";

  if (score >= 75) return "blue";

  if (score >= 60) return "orange";

  if (score >= 40) return "red";

  return "darkred";

}

function createMarkerIcon(score) {

  const color = getMarkerColor(score);

  return L.divIcon({

    className: "custom-marker",

    html: `<div style="

      background:${color};

      width:18px;

      height:18px;

      border-radius:50%;

      border:3px solid white;

      box-shadow:0 0 8px rgba(0,0,0,0.4);

    "></div>`,

    iconSize: [24, 24],

    iconAnchor: [12, 12],

  });

}

function buildQueryUrl(baseUrl, paramsObject) {

  const params = new URLSearchParams();

  Object.entries(paramsObject).forEach(([key, value]) => {

    if (value !== undefined && value !== null && value !== "" && value !== "All") {

      params.append(key, value);

    }

  });

  return params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;

}

async function loadRanking() {

  const url = buildQueryUrl(`${API_BASE_URL}/ranking`, {

    continent: currentContinent,

  });

  const response = await fetch(url);

  rankingData = await response.json();

  updateLastUpdateText(rankingData);

  renderDashboard();

}

async function loadCities() {

  const response = await fetch(`${API_BASE_URL}/cities`);

  citiesData = await response.json();

  renderCitySelect();

}

function renderCitySelect() {

  const citySelect = document.getElementById("citySelect");

  citySelect.innerHTML = `<option value="">-- select --</option>`;

  const filteredCities =

    currentHistoryContinent === "All"

      ? citiesData

      : citiesData.filter((city) => city.continent === currentHistoryContinent);

  filteredCities.forEach((city) => {

    const option = document.createElement("option");

    option.value = city.id;

    option.textContent = `${city.name} (${city.country})`;

    citySelect.appendChild(option);

  });

}

function updateLastUpdateText(ranking) {

  const lastUpdateText = document.getElementById("lastUpdateText");

  if (!ranking || ranking.length === 0) {

    lastUpdateText.textContent = "Last data update: no data";

    return;

  }

  const validDates = ranking

    .map((item) => item.measured_at)

    .filter((date) => date)

    .map((date) => new Date(date))

    .filter((date) => !Number.isNaN(date.getTime()));

  if (validDates.length === 0) {

    lastUpdateText.textContent = "Last data update: no date available";

    return;

  }

  const latestDate = validDates.sort((a, b) => b - a)[0];

  lastUpdateText.textContent =

    `Last data update: ${latestDate.toLocaleString("en-US")}`;

}

function getVisibleRanking() {

  let visibleRanking = rankingData;

  if (currentSearchTerm.trim() !== "") {

    const search = currentSearchTerm.toLowerCase().trim();

    visibleRanking = visibleRanking.filter((item) => {

      return (

        item.city.toLowerCase().includes(search) ||

        item.country.toLowerCase().includes(search) ||

        item.continent.toLowerCase().includes(search) ||

        getContinentLabel(item.continent).toLowerCase().includes(search)

      );

    });

  }

  return visibleRanking;

}

function sortRanking(data) {

  return [...data].sort((a, b) => {

    const valueA = a[currentSortColumn];

    const valueB = b[currentSortColumn];

    if (typeof valueA === "number" && typeof valueB === "number") {

      return currentSortDirection === "asc"

        ? valueA - valueB

        : valueB - valueA;

    }

    return currentSortDirection === "asc"

      ? String(valueA).localeCompare(String(valueB), "en")

      : String(valueB).localeCompare(String(valueA), "en");

  });

}

function renderDashboard() {

  const visibleRanking = getVisibleRanking();

  const sortedRanking = sortRanking(visibleRanking);

  renderTable(sortedRanking);

  renderMap(sortedRanking);

  updateSortIndicators();

}

function renderTable(ranking) {

  const tableBody = document.getElementById("rankingTableBody");

  tableBody.innerHTML = "";

  if (!ranking || ranking.length === 0) {

    tableBody.innerHTML = `

      <tr>

        <td colspan="8">No data for the selected filter.</td>

      </tr>

    `;

    return;

  }

  ranking.forEach((item) => {

    const row = document.createElement("tr");

    row.innerHTML = `

      <td>${item.city}</td>

      <td>${item.country}</td>

      <td>${getContinentLabel(item.continent)}</td>

      <td>${item.temperature} °C</td>

      <td>${item.pm10}</td>

      <td>${item.pm25}</td>

      <td class="score">${item.score}</td>

      <td class="category">${item.category}</td>

    `;

    tableBody.appendChild(row);

  });

}

function renderMap(ranking) {

  markersLayer.clearLayers();

  if (!ranking || ranking.length === 0) {

    map.setView([20.0, 0.0], 2);

    return;

  }

  ranking.forEach((item) => {

    const marker = L.marker([item.latitude, item.longitude], {

      icon: createMarkerIcon(item.score),

    });

    marker.bindPopup(`

      <strong>${item.city}</strong><br>

      ${item.country}, ${item.continent}<br>

      Score: ${item.score} (${item.category})<br>

      Temperature: ${item.temperature} °C<br>

      Wind: ${item.wind_speed} km/h<br>

      Precipitation: ${item.precipitation} mm<br>

      PM10: ${item.pm10}<br>

      PM2.5: ${item.pm25}

    `);

    marker.addTo(markersLayer);

  });

  const bounds = L.latLngBounds(

    ranking.map((item) => [item.latitude, item.longitude])

  );

  map.fitBounds(bounds, {

    padding: [40, 40],

    maxZoom: currentContinent === "All" ? 2 : 5,

  });

}

function handleSort(column) {

  if (currentSortColumn === column) {

    currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";

  } else {

    currentSortColumn = column;

    currentSortDirection = "asc";

  }

  renderDashboard();

}

function updateSortIndicators() {

  document.querySelectorAll("th[data-sort]").forEach((header) => {

    header.classList.remove("sorted-asc", "sorted-desc");

    if (header.dataset.sort === currentSortColumn) {

      header.classList.add(

        currentSortDirection === "asc" ? "sorted-asc" : "sorted-desc"

      );

    }

  });

}

async function refreshData() {

  const statusText = document.getElementById("statusText");

  const button = document.getElementById("refreshBtn");

  try {

    statusText.textContent =

      `Fetching data from API: ${getContinentLabel(currentContinent)}...`;

    button.disabled = true;

    const url = buildQueryUrl(`${API_BASE_URL}/refresh`, {

      continent: currentContinent,

    });

    const response = await fetch(url, {

      method: "POST",

    });

    if (!response.ok) {

      throw new Error("Refresh failed");

    }

    await loadRanking();

    statusText.textContent =

      `Data refreshed: ${getContinentLabel(currentContinent)}`;

  } catch (error) {

    console.error(error);

    statusText.textContent = "Error refreshing data";

  } finally {

    button.disabled = false;

  }

}

async function loadHistory() {

  const citySelect = document.getElementById("citySelect");

  const cityId = citySelect.value;

  if (!cityId) {

    document.getElementById("historyTitle").textContent =

      "Select a capital to view measurement history.";

    document.getElementById("historyTableBody").innerHTML = "";

    clearHistoryChart();

    return;

  }

  const response = await fetch(`${API_BASE_URL}/cities/${cityId}/history?limit=20`);

  const data = await response.json();

  renderHistory(data);

}

function renderHistory(data) {

  const historyTitle = document.getElementById("historyTitle");

  const tableBody = document.getElementById("historyTableBody");

  historyTitle.textContent = `Measurement history: ${data.city}, ${data.country}`;

  tableBody.innerHTML = "";

  if (!data.history || data.history.length === 0) {

    tableBody.innerHTML = `

      <tr>

        <td colspan=”8”>No historical data. Click “Refresh data from API”.</td>

      </tr>

    `;

    clearHistoryChart();

    return;

  }

  data.history.forEach((item) => {

    const date = new Date(item.measured_at).toLocaleString("pl-PL");

    const row = document.createElement("tr");

    row.innerHTML = `

      <td>${date}</td>

      <td class="score">${item.score}</td>

      <td>${item.category}</td>

      <td>${item.temperature} °C</td>

      <td>${item.wind_speed} km/h</td>

      <td>${item.precipitation} mm</td>

      <td>${item.pm10}</td>

      <td>${item.pm25}</td>

    `;

    tableBody.appendChild(row);

  });
  currentHistoryData = data.history;
  renderHistoryChart(data.history);

}

function clearHistoryChart() {

  if (historyChart) {

    historyChart.destroy();

    historyChart = null;

  }

}

function getMetricConfig(metric) {
  const configs = {
    score: {
      label: "Score",
      unit: "pts",
      colorLabel: "Score",
    },
    temperature: {
      label: "Temperature",
      unit: "°C",
      colorLabel: "Temperature",
    },
    pm10: {
      label: "PM10",
      unit: "µg/m³",
      colorLabel: "PM10",
    },
    pm25: {
      label: "PM2.5",
      unit: "µg/m³",
      colorLabel: "PM2.5",
    },
    wind_speed: {
      label: "Wind",
      unit: "km/h",
      colorLabel: "Wind",
    },
    precipitation: {
      label: "Precipitation",
      unit: "mm",
      colorLabel: "Precipitation",
    },
  };

  return configs[metric] || configs.score;
}

function renderHistoryChart(history) {
  const ctx = document.getElementById("historyChart");
  const metricConfig = getMetricConfig(currentHistoryMetric);

  const chronologicalHistory = [...history].reverse();

  const labels = chronologicalHistory.map((item) =>
    new Date(item.measured_at).toLocaleString("en-US")
  );

  const values = chronologicalHistory.map((item) => item[currentHistoryMetric]);

  clearHistoryChart();

  historyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `${metricConfig.label} [${metricConfig.unit}]`,
          data: values,
          tension: 0.25,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "bottom",
        },
        title: {
          display: true,
          text: `${metricConfig.label} over time`,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return `${metricConfig.label}: ${context.parsed.y} ${metricConfig.unit}`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            maxRotation: 45,
            minRotation: 0,
          },
        },
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: `${metricConfig.label} [${metricConfig.unit}]`,
          },
        },
      },
    },
  });
}

function switchTab(tabName) {

  document.querySelectorAll(".tab-button").forEach((button) => {

    button.classList.toggle("active", button.dataset.tab === tabName);

  });

  document.querySelectorAll(".tab-content").forEach((content) => {

    content.classList.remove("active");

  });

  if (tabName === "dashboard") {

    document.getElementById("dashboardTab").classList.add("active");

    setTimeout(() => {

      map.invalidateSize();

      renderDashboard();

    }, 100);

  }

  if (tabName === "history") {

    document.getElementById("historyTab").classList.add("active");

  }

}

document.getElementById("refreshBtn").addEventListener("click", refreshData);

document.getElementById("loadHistoryBtn").addEventListener("click", loadHistory);

document.getElementById("citySelect").addEventListener("change", loadHistory);

document.getElementById("searchInput").addEventListener("input", (event) => {

  currentSearchTerm = event.target.value;

  renderDashboard();

});

document.getElementById("continentFilter").addEventListener("change", async (event) => {

  currentContinent = event.target.value;

  const statusText = document.getElementById("statusText");

  statusText.textContent =

    `Loading saved data: ${getContinentLabel(currentContinent)}...`;

  await loadRanking();

  statusText.textContent =

    `Showing last saved data for: ${getContinentLabel(currentContinent)}`;

});

document

  .getElementById("historyContinentFilter")

  .addEventListener("change", (event) => {

    currentHistoryContinent = event.target.value;

    renderCitySelect();

    document.getElementById("historyTitle").textContent =

      "Select a capital to view measurement history.";

    document.getElementById("historyTableBody").innerHTML = "";
currentHistoryData = [];
    clearHistoryChart();

  });
document.getElementById("historyMetricSelect").addEventListener("change", (event) => {

  currentHistoryMetric = event.target.value;

  if (currentHistoryData && currentHistoryData.length > 0) {

    renderHistoryChart(currentHistoryData);

  }

});
document.querySelectorAll("th[data-sort]").forEach((header) => {

  header.addEventListener("click", () => {

    handleSort(header.dataset.sort);

  });

});

document.querySelectorAll(".tab-button").forEach((button) => {

  button.addEventListener("click", () => {

    switchTab(button.dataset.tab);

  });

});

async function initializePage() {
  const statusText = document.getElementById("statusText");

  statusText.textContent = "Loading last saved data...";

  await loadCities();
  await loadRanking();

  statusText.textContent =
    "Showing last saved data. Worker automatically updates measurements every hour.";
}

initializePage();
