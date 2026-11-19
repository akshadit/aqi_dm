/**
 * AirInsight Ultra-Premium Frontend Controller
 * Features:
 * - Living Cloud Drift & Atmospheric Stage Control (Inspired by Alto Volcán de Agua)
 * - Dynamic Vertical Atmospheric Ruler Scale with Real-Time Needle Positioning
 * - Ambient Sky Tone Transitions Based on Measured Air Quality
 * - Frosted Glassmorphism Micro-Interactions & Dual-Mode Architecture
 */

const API_BASE = "";

// Global App State
let currentCities = [];
let activeCityId = null;
let currentAppMode = "consumer"; // "consumer" or "dev"
let currentChartInstances = {};
let latestOverviewData = [];

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  await loadCities();
  await loadStats();
  await loadOverview();
  renderConsumerTrajectory();
  onConsumerSimulatorChange();
}

// -------------------------------------------------------------
// TOAST NOTIFICATIONS
// -------------------------------------------------------------
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const bgClass = type === "success" ? "bg-emerald-600/90" : type === "error" ? "bg-rose-600/90" : "bg-slate-900/90";
  toast.className = `${bgClass} backdrop-blur-md text-white px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold flex items-center space-x-2.5 transition-all duration-300 transform translate-y-4 opacity-0 pointer-events-auto border border-white/20`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle-2' : type === 'error' ? 'alert-triangle' : 'sparkles'}" class="w-4 h-4"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  // Animate in
  setTimeout(() => {
    toast.classList.remove("translate-y-4", "opacity-0");
  }, 20);

  // Auto remove
  setTimeout(() => {
    toast.classList.add("translate-y-4", "opacity-0");
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}

// -------------------------------------------------------------
// APP MODE SWITCHER (ATMOSPHERE VIEW vs DEV VIVA STUDIO)
// -------------------------------------------------------------
function setAppMode(mode) {
  currentAppMode = mode;
  const consumerContainer = document.getElementById("mode-consumer-container");
  const devContainer = document.getElementById("mode-dev-container");
  const btnConsumer = document.getElementById("btn-mode-consumer");
  const btnDev = document.getElementById("btn-mode-dev");

  if (mode === "consumer") {
    consumerContainer.classList.remove("hidden");
    devContainer.classList.add("hidden");

    btnConsumer.className = "flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white text-slate-900 shadow-2xs transition-all";
    btnDev.className = "flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 transition-all";

    loadOverview();
    renderConsumerTrajectory();
  } else {
    consumerContainer.classList.add("hidden");
    devContainer.classList.remove("hidden");

    btnDev.className = "flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-white text-purple-900 shadow-2xs transition-all";
    btnConsumer.className = "flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-900 transition-all";

    switchDevTab("dev-overview");
    showToast("Opened Academic Viva Data Mining Studio", "info");
  }

  if (window.lucide) lucide.createIcons();
}

// -------------------------------------------------------------
// 1. DATA INITIALIZATION & TELEMETRY
// -------------------------------------------------------------
async function loadCities() {
  try {
    const res = await fetch(`${API_BASE}/api/cities`);
    const cities = await res.json();
    currentCities = cities;

    const selector = document.getElementById("city-selector");
    selector.innerHTML = "";
    cities.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.innerText = c.city_name;
      selector.appendChild(opt);
    });

    if (cities.length > 0 && !activeCityId) {
      activeCityId = cities[0].id;
      selector.value = activeCityId;
    }
  } catch (err) {
    console.error("Failed to load cities:", err);
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const stats = await res.json();
    
    // Dev Mode Telemetry KPI updates
    const cEl = document.getElementById("dev-cities-count");
    if (cEl) {
      document.getElementById("dev-cities-count").innerText = stats.cities_count;
      document.getElementById("dev-total-records").innerText = stats.total_records.toLocaleString();
      document.getElementById("dev-obs-records").innerText = stats.observed_records.toLocaleString();
      document.getElementById("dev-fc-records").innerText = stats.forecast_records.toLocaleString();
    }
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

function onCityChange() {
  const selector = document.getElementById("city-selector");
  activeCityId = parseInt(selector.value);
  loadOverview();
  renderConsumerTrajectory();
}

// Quick City Pills Handler
function selectQuickCity(cityName) {
  const match = currentCities.find(c => c.city_name.toLowerCase() === cityName.toLowerCase());
  if (match) {
    activeCityId = match.id;
    document.getElementById("city-selector").value = match.id;
    onCityChange();
    showToast(`Switched view to ${match.city_name}`, "info");
  } else {
    document.getElementById("quick-city-search").value = cityName;
    handleSearchEnter();
  }
}

// Enter on quick search input
async function handleSearchEnter() {
  const input = document.getElementById("quick-city-search");
  const query = input.value.trim();
  if (!query) return;

  const existing = currentCities.find(c => c.city_name.toLowerCase() === query.toLowerCase());
  if (existing) {
    activeCityId = existing.id;
    document.getElementById("city-selector").value = existing.id;
    onCityChange();
    input.value = "";
    showToast(`Displaying ${existing.city_name}`, "success");
    return;
  }

  // Query Geocoding
  input.disabled = true;
  input.placeholder = "Resolving coordinates via Geocoding...";
  try {
    const res = await fetch(`${API_BASE}/api/geocoding/search?q=${encodeURIComponent(query)}`);
    const candidates = await res.json();
    if (candidates && candidates.length > 0) {
      const cand = candidates[0];
      const addRes = await fetch(`${API_BASE}/api/cities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: cand.name, latitude: cand.latitude, longitude: cand.longitude, country: cand.country })
      });
      const added = await addRes.json();
      await loadCities();
      activeCityId = added.city_id;
      document.getElementById("city-selector").value = added.city_id;
      onCityChange();
      showToast(`Discovered "${cand.name}, ${cand.country}"! Fetching live telemetry...`, "success");
      triggerIngestCurrentCity();
    } else {
      showToast(`Could not resolve coordinates for "${query}".`, "error");
    }
  } catch (e) {
    showToast("Geocoding search failed: " + e, "error");
  } finally {
    input.disabled = false;
    input.placeholder = "Search city e.g. Delhi, London, Tokyo...";
    input.value = "";
  }
}

// -------------------------------------------------------------
// 2. ATMOSPHERIC SCENIC HERO & VERTICAL RULER SCALE
// -------------------------------------------------------------

async function loadOverview() {
  try {
    const res = await fetch(`${API_BASE}/api/overview`);
    const data = await res.json();
    latestOverviewData = data.cities_summary || [];

    if (latestOverviewData.length === 0) return;

    const active = latestOverviewData.find(c => c.city_id === activeCityId) || latestOverviewData[0];
    const cityInfo = currentCities.find(c => c.id === active.city_id) || {};

    // 1. Update Atmospheric Stage & Cloud Backdrop Colors based on AQI
    updateAtmosphericSkyColor(active.us_aqi);

    // 2. Update Editorial Hero Typography
    const titleEl = document.getElementById("hero-city-name-display");
    if (titleEl) {
      titleEl.innerText = active.city_name;
    }
    const countryEl = document.getElementById("hero-state-country");
    if (countryEl) {
      countryEl.innerText = `${cityInfo.country || "INDIA"} • MONITORED ATMOSPHERE`;
    }

    // 3. Update Vertical Atmospheric Scale (Alto Style)
    updateVerticalScale(active, cityInfo);

    // 4. Update Radial SVG Gauge & Hero Numbers
    document.getElementById("hero-timestamp").innerText = `Live Satellite UTC: ${active.timestamp.replace("T", " ")}`;
    document.getElementById("hero-aqi-val").innerText = Math.round(active.us_aqi);
    updateRadialGauge(active.us_aqi, active.color);

    // 5. Tier Pill & Headline
    const tierBadge = document.getElementById("hero-tier-badge");
    document.getElementById("hero-tier-text").innerText = active.tier;
    tierBadge.style.color = active.color;
    tierBadge.style.borderColor = `${active.color}40`;

    const adv = getConsumerAdvisory(active.tier);
    document.getElementById("hero-headline").innerText = adv.headline;
    document.getElementById("hero-short-summary").innerText = adv.summary;
    document.getElementById("hero-advisory-text").innerText = adv.text;
    updateActivityBadges(adv);

    // 6. Primary Pollutant Callout
    updatePrimaryPollutantCallout(active);

    // 7. Chemical Pollutants Strip
    document.getElementById("pill-pm25").innerText = active.pm2_5;
    document.getElementById("pill-pm10").innerText = active.pm10;
    document.getElementById("pill-no2").innerText = active.no2;
    document.getElementById("pill-so2").innerText = active.so2;
    document.getElementById("pill-co").innerText = active.co;
    document.getElementById("pill-o3").innerText = active.o3;

    // 8. Leaderboard & Dev Chart
    renderConsumerLeaderboard(latestOverviewData);
    if (document.getElementById("chart-dev-comparison")) {
      renderDevComparisonChart(latestOverviewData);
    }
  } catch (err) {
    console.error("Overview load failed:", err);
  }
}

// Dynamic Sky Backdrop Adaptation
function updateAtmosphericSkyColor(aqi) {
  const root = document.documentElement;
  if (aqi <= 50) {
    // Crisp clean mountain sky (Like Alto Volcán morning)
    root.style.setProperty("--sky-top", "#8fb9d4");
    root.style.setProperty("--sky-mid", "#c4dbe8");
    root.style.setProperty("--sky-bottom", "#e8edf2");
  } else if (aqi <= 100) {
    // Warm morning golden sky
    root.style.setProperty("--sky-top", "#9bbcc9");
    root.style.setProperty("--sky-mid", "#d6cbbe");
    root.style.setProperty("--sky-bottom", "#edeae4");
  } else if (aqi <= 150) {
    // Hazy amber / warm dusk
    root.style.setProperty("--sky-top", "#a89689");
    root.style.setProperty("--sky-mid", "#d4af94");
    root.style.setProperty("--sky-bottom", "#ede0d4");
  } else if (aqi <= 200) {
    // Smoggy dusky terracotta
    root.style.setProperty("--sky-top", "#8f6e69");
    root.style.setProperty("--sky-mid", "#be8d84");
    root.style.setProperty("--sky-bottom", "#dbc3be");
  } else {
    // Twilight smog emergency
    root.style.setProperty("--sky-top", "#504b5e");
    root.style.setProperty("--sky-mid", "#826b7c");
    root.style.setProperty("--sky-bottom", "#ad97a6");
  }
}

// Updates Vertical Atmospheric Scale Ruler (Alto Style)
function updateVerticalScale(active, cityInfo) {
  const scaleAqiEl = document.getElementById("scale-current-aqi");
  const scaleCityEl = document.getElementById("scale-city-name");
  const scaleCoordsEl = document.getElementById("scale-coords");
  const needleEl = document.getElementById("scale-needle");

  if (scaleAqiEl) scaleAqiEl.innerText = `${Math.round(active.us_aqi)} AQI`;
  if (scaleCityEl) scaleCityEl.innerText = active.city_name.toUpperCase();
  if (scaleCoordsEl && cityInfo.latitude) {
    scaleCoordsEl.innerText = `${Math.abs(cityInfo.latitude).toFixed(2)}° ${cityInfo.latitude >= 0 ? "N" : "S"}  ${Math.abs(cityInfo.longitude).toFixed(2)}° ${cityInfo.longitude >= 0 ? "E" : "W"}`;
  }

  if (needleEl) {
    // Calculate needle vertical position (0 to 100%)
    // Top is 500 (0%), Bottom is 0 (100%)
    const clampedAQI = Math.min(Math.max(active.us_aqi, 0), 500);
    const topPct = (1.0 - (clampedAQI / 500.0)) * 100.0;
    needleEl.style.top = `${topPct}%`;
    needleEl.style.backgroundColor = active.color;
    needleEl.style.boxShadow = `0 0 0 4px ${active.color}35`;
  }
}

// Radial SVG Gauge Meter
function updateRadialGauge(aqi, color) {
  const circle = document.getElementById("gauge-circle-progress");
  if (!circle) return;

  const circumference = 251.2; // 2 * pi * 40
  const maxAQI = 400.0;
  const fraction = Math.min(Math.max(aqi, 0), maxAQI) / maxAQI;
  const offset = circumference * (1 - fraction);

  circle.style.strokeDashoffset = offset;
  circle.style.stroke = color;
}

function updatePrimaryPollutantCallout(cityData) {
  const titleEl = document.getElementById("primary-pollutant-title");
  const descEl = document.getElementById("primary-pollutant-desc");
  if (!titleEl || !descEl) return;

  if (cityData.pm2_5 > 35) {
    titleEl.innerText = `Primary Pollutant: PM2.5 (${cityData.pm2_5} µg/m³ — Fine Combustion Soot)`;
    descEl.innerText = "Fine inhalable particles that penetrate deep into pulmonary pathways and cardiovascular systems.";
  } else if (cityData.pm10 > 75) {
    titleEl.innerText = `Primary Pollutant: PM10 (${cityData.pm10} µg/m³ — Coarse Roadway Dust)`;
    descEl.innerText = "Coarse dust and mechanical grinding particles causing respiratory and throat irritation.";
  } else if (cityData.no2 > 40) {
    titleEl.innerText = `Primary Pollutant: NO₂ (${cityData.no2} µg/m³ — Vehicular Combustion)`;
    descEl.innerText = "Combustion byproduct from diesel and petrol engines causing acute airway inflammation.";
  } else {
    titleEl.innerText = "Pollutant Species Within Standard WHO Benchmark Limits";
    descEl.innerText = "All measured particulate and gaseous concentrations are currently in favorable ranges.";
  }
}

function getConsumerAdvisory(tier) {
  switch (tier) {
    case "Good":
      return {
        headline: "Crisp & Clean Ambient Air",
        summary: "Pollution levels pose zero health concern for all population groups.",
        text: "Air quality is ideal. Enjoy outdoor sports, jogging, cycling, and keep windows open for natural ventilation.",
        outdoor: true, windows: true, mask: false, purifier: false
      };
    case "Moderate":
      return {
        headline: "Acceptable Breathing Conditions",
        summary: "Air quality is satisfactory, though sensitive people may experience minor throat dryness.",
        text: "Generally safe for everyone. Unusually sensitive individuals may consider slightly reducing prolonged outdoor exertion.",
        outdoor: true, windows: true, mask: false, purifier: false
      };
    case "Unhealthy for Sensitive Groups":
      return {
        headline: "Hazy & Stagnant Atmosphere",
        summary: "Children, elderly, and people with asthma or lung conditions should take precautions.",
        text: "Sensitive groups should limit prolonged outdoor exertion. Consider keeping residential windows mostly closed.",
        outdoor: false, windows: false, mask: true, purifier: true
      };
    case "Unhealthy":
      return {
        headline: "Heavy Urban Pollution Alert",
        summary: "Everyone may begin to experience respiratory irritation and eye fatigue.",
        text: "Wear an N95 mask outdoors, avoid strenuous physical activities, seal windows, and run indoor air purifiers.",
        outdoor: false, windows: false, mask: true, purifier: true
      };
    case "Very Unhealthy":
    case "Hazardous":
      return {
        headline: "Severe Emergency Smog Warning",
        summary: "Severe atmospheric health hazard. Serious risk for the entire population.",
        text: "Avoid all outdoor physical activity. Keep indoor air sealed with HEPA filtration and seek medical advice if breathless.",
        outdoor: false, windows: false, mask: true, purifier: true
      };
    default:
      return {
        headline: "Stable Ambient Environment",
        summary: "Standard regional conditions.",
        text: "Normal ambient conditions. Exercise standard care.",
        outdoor: true, windows: true, mask: false, purifier: false
      };
  }
}

function updateActivityBadges(adv) {
  const setBadge = (id, textId, allowed, allowedText, blockedText) => {
    const el = document.getElementById(id);
    const textEl = document.getElementById(textId);
    if (!el || !textEl) return;
    if (allowed) {
      el.className = "p-3.5 rounded-2xl bg-white/80 border border-slate-200/80 flex items-center space-x-3 shadow-2xs";
      textEl.innerText = allowedText;
      textEl.className = "text-[10px] text-emerald-600 font-bold";
    } else {
      el.className = "p-3.5 rounded-2xl bg-rose-50/90 border border-rose-200/80 flex items-center space-x-3 shadow-2xs";
      textEl.innerText = blockedText;
      textEl.className = "text-[10px] text-rose-600 font-bold";
    }
  };

  setBadge("badge-outdoor", "badge-outdoor-text", adv.outdoor, "Safe & Great", "Avoid Jogging");
  setBadge("badge-windows", "badge-windows-text", adv.windows, "Open Windows", "Keep Windows Closed");
  setBadge("badge-mask", "badge-mask-text", !adv.mask, "Not Required", "N95 Mask Advised");
  setBadge("badge-purifier", "badge-purifier-text", !adv.purifier, "Idle / Off", "Run HEPA Purifier");
}

function renderConsumerLeaderboard(cities) {
  const container = document.getElementById("consumer-city-leaderboard");
  if (!container) return;
  container.innerHTML = "";

  cities.forEach((c, idx) => {
    const isSelected = c.city_id === activeCityId;
    const item = document.createElement("div");
    item.className = `p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
      isSelected ? "bg-white/95 border-sky-400 shadow-md transform scale-[1.02]" : "bg-white/70 border-slate-200/70 hover:bg-white hover:border-slate-300"
    }`;
    item.onclick = () => {
      activeCityId = c.city_id;
      document.getElementById("city-selector").value = c.city_id;
      onCityChange();
      showToast(`Selected ${c.city_name}`, "info");
    };

    item.innerHTML = `
      <div class="flex items-center space-x-3">
        <span class="w-5 text-center text-xs font-black text-slate-400 font-mono">#${idx + 1}</span>
        <span class="w-3 h-3 rounded-full shadow-2xs" style="background-color: ${c.color}"></span>
        <div>
          <h4 class="font-extrabold text-slate-900 text-xs">${c.city_name}</h4>
          <span class="text-[10px] text-slate-400 font-medium font-mono">PM2.5: ${c.pm2_5} µg/m³</span>
        </div>
      </div>
      <div class="text-right">
        <span class="font-black text-sm" style="color: ${c.color}">${Math.round(c.us_aqi)}</span>
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${c.tier}</p>
      </div>
    `;
    container.appendChild(item);
  });
}

// 24-Hour Past + 48-Hour Forecast Trajectory Chart
async function renderConsumerTrajectory() {
  if (!activeCityId) return;
  try {
    const res = await fetch(`${API_BASE}/api/hourly/${activeCityId}?pollutant=us_aqi`);
    const data = await res.json();

    const canvas = document.getElementById("chart-consumer-trajectory");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (currentChartInstances["consumerTrajectory"]) {
      currentChartInstances["consumerTrajectory"].destroy();
    }

    const obs = data.observed.slice(-24);
    const fc = data.forecast.slice(0, 48);

    const labels = [
      ...obs.map(d => d.time.slice(5, 16).replace("T", " ")),
      ...fc.map(d => d.time.slice(5, 16).replace("T", " "))
    ];
    const obsVals = [...obs.map(d => d.value), ...Array(fc.length).fill(null)];
    const fcVals = [...Array(obs.length).fill(null), ...fc.map(d => d.value)];

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, "rgba(2, 132, 199, 0.25)");
    gradient.addColorStop(1, "rgba(2, 132, 199, 0.0)");

    currentChartInstances["consumerTrajectory"] = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Past 24h (Observed)",
            data: obsVals,
            borderColor: "#0284c7",
            backgroundColor: gradient,
            fill: true,
            borderWidth: 3,
            tension: 0.35,
            pointRadius: 0
          },
          {
            label: "Forecast Horizon",
            data: fcVals,
            borderColor: "#f59e0b",
            borderDash: [5, 5],
            borderWidth: 2.5,
            tension: 0.35,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { ticks: { maxTicksLimit: 10, font: { size: 10, family: "JetBrains Mono" } }, grid: { display: false } },
          y: { grid: { color: "rgba(241, 245, 249, 0.8)" }, ticks: { font: { size: 10, family: "JetBrains Mono" } } }
        }
      }
    });
  } catch (e) {
    console.error("Failed to render trajectory:", e);
  }
}

// Interactive What-If Simulator
async function onConsumerSimulatorChange() {
  const pm25 = parseFloat(document.getElementById("c-sim-pm25").value);
  const pm10 = parseFloat(document.getElementById("c-sim-pm10").value);
  const no2 = parseFloat(document.getElementById("c-sim-no2").value);

  document.getElementById("c-sim-pm25-val").innerText = `${pm25}`;
  document.getElementById("c-sim-pm10-val").innerText = `${pm10}`;
  document.getElementById("c-sim-no2-val").innerText = `${no2}`;

  try {
    const res = await fetch(`${API_BASE}/api/mining/predict-sample`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pm2_5: pm25, pm10: pm10, no2: no2, so2: 12.0, co: 800.0, o3: 35.0 })
    });
    const pred = await res.json();

    const tierEl = document.getElementById("c-sim-result-tier");
    tierEl.innerText = pred.predicted_category;
    tierEl.style.color = pred.color;

    const descEl = document.getElementById("c-sim-result-desc");
    descEl.innerText = getConsumerAdvisory(pred.predicted_category).summary;

    const box = document.getElementById("c-sim-result-box");
    box.style.borderColor = `${pred.color}50`;
    box.style.backgroundColor = `${pred.color}15`;

    const probs = Object.entries(pred.probabilities).filter(([_, v]) => v > 0).map(([k, v]) => `${k}: ${v}%`).join(" | ");
    document.getElementById("c-sim-result-probs").innerText = probs ? `Confidence: ${probs}` : "";
  } catch (err) {
    console.error("Consumer simulator error:", err);
  }
}

async function triggerIngestCurrentCity() {
  if (!activeCityId) return;
  const btn = document.getElementById("btn-fetch-live");
  btn.classList.add("animate-spin");
  try {
    const res = await fetch(`${API_BASE}/api/ingest/city/${activeCityId}`, { method: "POST" });
    const data = await res.json();
    showToast(`Updated live satellite telemetry for ${data.city_name}!`, "success");
    await loadOverview();
    await renderConsumerTrajectory();
    await loadStats();
  } catch (e) {
    showToast("API fetch error: " + e, "error");
  } finally {
    btn.classList.remove("animate-spin");
  }
}

// -------------------------------------------------------------
// 3. DEV / VIVA MODE (ACADEMIC DATA MINING LAB)
// -------------------------------------------------------------

function switchDevTab(tabId) {
  const tabs = [
    "dev-overview", "dev-preprocessing", "dev-clustering",
    "dev-classification", "dev-association", "dev-trends", "dev-reports"
  ];
  tabs.forEach(t => {
    const el = document.getElementById(`dev-view-${t}`);
    const btn = document.getElementById(`dev-tab-btn-${t}`);
    if (el) el.classList.add("hidden");
    if (btn) {
      btn.classList.remove("bg-slate-800", "text-white");
      btn.classList.add("text-slate-400");
    }
  });

  const targetEl = document.getElementById(`dev-view-${tabId}`);
  const targetBtn = document.getElementById(`dev-tab-btn-${tabId}`);
  if (targetEl) targetEl.classList.remove("hidden");
  if (targetBtn) {
    targetBtn.classList.add("bg-slate-800", "text-white");
    targetBtn.classList.remove("text-slate-400");
  }

  // Trigger Dev-Specific Algorithms
  if (tabId === "dev-overview") loadStats();
  else if (tabId === "dev-preprocessing") runPreprocessingAudit();
  else if (tabId === "dev-clustering") runKMeans();
  else if (tabId === "dev-classification") runDecisionTree();
  else if (tabId === "dev-association") runApriori();
  else if (tabId === "dev-trends") runRegression();

  if (window.lucide) lucide.createIcons();
}

function renderDevComparisonChart(cities) {
  const canvas = document.getElementById("chart-dev-comparison");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (currentChartInstances["devComparison"]) currentChartInstances["devComparison"].destroy();

  currentChartInstances["devComparison"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: cities.map(c => c.city_name),
      datasets: [{
        label: "US AQI Ground Truth",
        data: cities.map(c => c.us_aqi),
        backgroundColor: cities.map(c => c.color),
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
        x: { grid: { display: false } }
      }
    }
  });
}

async function runPreprocessingAudit() {
  try {
    const res = await fetch(`${API_BASE}/api/preprocessing`);
    const data = await res.json();
    const tbody = document.getElementById("dev-prep-tbody");
    tbody.innerHTML = "";
    for (const [feat, info] of Object.entries(data.report.outliers_detected)) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="p-3 font-semibold uppercase text-slate-800">${feat}</td>
        <td class="p-3 text-amber-600 font-bold">${info.count}</td>
        <td class="p-3">${info.lower_bound}</td>
        <td class="p-3 font-medium">${info.upper_bound}</td>
      `;
      tbody.appendChild(tr);
    }
    showToast("Loaded Preprocessing Audit metrics", "info");
  } catch (e) {
    console.error("Prep audit error:", e);
  }
}

async function runKMeans() {
  const k = parseInt(document.getElementById("dev-input-k")?.value || 4);
  try {
    const res = await fetch(`${API_BASE}/api/mining/kmeans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ k: k })
    });
    const data = await res.json();

    const pcaTrace = {
      x: data.pca_points.map(p => p.x),
      y: data.pca_points.map(p => p.y),
      mode: "markers",
      type: "scatter",
      text: data.pca_points.map(p => `${p.city}<br>Cluster: ${p.cluster}<br>AQI: ${p.us_aqi}`),
      marker: { color: data.pca_points.map(p => p.cluster), colorscale: "Viridis", size: 6 }
    };
    Plotly.newPlot("chart-dev-pca", [pcaTrace], {
      margin: { l: 40, r: 20, t: 20, b: 40 },
      xaxis: { title: "Principal Component 1" },
      yaxis: { title: "Principal Component 2" },
      plot_bgcolor: "#ffffff"
    }, { responsive: true });

    const container = document.getElementById("dev-km-archetypes");
    container.innerHTML = "";
    data.cluster_summaries.forEach(c => {
      const d = document.createElement("div");
      d.className = "p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex justify-between";
      d.innerHTML = `<strong>Cluster ${c.cluster}: ${c.archetype}</strong> <span class="text-slate-500 font-semibold font-mono">${c.count} samples (${c.percentage}%)</span>`;
      container.appendChild(d);
    });
    showToast(`K-Means computed with k=${k}`, "success");
  } catch (e) {
    console.error("K-Means error:", e);
  }
}

async function runDecisionTree() {
  try {
    const res = await fetch(`${API_BASE}/api/mining/decision-tree`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ max_depth: 4, criterion: "gini" })
    });
    const data = await res.json();

    document.getElementById("dev-dt-acc").innerText = `${data.accuracy}%`;
    document.getElementById("dev-dt-prec").innerText = `${data.precision}%`;
    document.getElementById("dev-dt-rec").innerText = `${data.recall}%`;
    document.getElementById("dev-dt-f1").innerText = `${data.f1_score}%`;

    const cmTrace = {
      z: data.confusion_matrix,
      x: data.confusion_matrix_labels,
      y: data.confusion_matrix_labels,
      type: "heatmap",
      colorscale: "Blues"
    };
    Plotly.newPlot("chart-dev-cm", [cmTrace], { margin: { l: 60, r: 20, t: 20, b: 60 } }, { responsive: true });

    const canvas = document.getElementById("chart-dev-importance");
    if (canvas) {
      const ctx = canvas.getContext("2d");
      if (currentChartInstances["devImportance"]) currentChartInstances["devImportance"].destroy();
      currentChartInstances["devImportance"] = new Chart(ctx, {
        type: "bar",
        data: {
          labels: Object.keys(data.feature_importances).map(f => f.toUpperCase()),
          datasets: [{ data: Object.values(data.feature_importances), backgroundColor: "#0284c7", borderRadius: 6 }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true }, y: { grid: { display: false } } }
        }
      });
    }
    showToast("Trained Decision Tree model", "success");
  } catch (e) {
    console.error("DT error:", e);
  }
}

async function runApriori() {
  try {
    const res = await fetch(`${API_BASE}/api/mining/apriori`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ min_support: 0.10, min_confidence: 0.50, min_lift: 1.0 })
    });
    const data = await res.json();

    const tbody = document.getElementById("dev-apriori-tbody");
    tbody.innerHTML = "";
    data.rules.slice(0, 15).forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="p-2.5 font-semibold text-slate-800">${r.antecedents}</td>
        <td class="p-2.5 text-sky-700 font-semibold">${r.consequents}</td>
        <td class="p-2.5">${r.support}%</td>
        <td class="p-2.5">${r.confidence}%</td>
        <td class="p-2.5 font-bold text-emerald-600">${r.lift}x</td>
      `;
      tbody.appendChild(tr);
    });
    showToast(`Discovered ${data.rules.length} association rules`, "success");
  } catch (e) {
    console.error("Apriori error:", e);
  }
}

async function runRegression() {
  if (!activeCityId) return;
  try {
    const res = await fetch(`${API_BASE}/api/mining/regression`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city_id: activeCityId, pollutant: "pm2_5", forecast_hours: 24 })
    });
    const data = await res.json();

    document.getElementById("dev-reg-status").innerText = data.trend_status;
    document.getElementById("dev-reg-drift").innerText = `${data.change_per_day > 0 ? "+" : ""}${data.change_per_day}/day`;
    document.getElementById("dev-reg-mae").innerText = data.mae;
    document.getElementById("dev-reg-rmse").innerText = data.rmse;

    const canvas = document.getElementById("chart-dev-regression");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (currentChartInstances["devRegression"]) currentChartInstances["devRegression"].destroy();

    const labels = [
      ...data.history.map(d => d.time.slice(5, 16).replace("T", " ")),
      ...data.extrapolation.map(d => d.time.slice(5, 16).replace("T", " "))
    ];
    const actuals = [...data.history.map(d => d.actual), ...Array(data.extrapolation.length).fill(null)];
    const fitted = [...data.history.map(d => d.fitted), ...Array(data.extrapolation.length).fill(null)];
    const fut = [...Array(data.history.length).fill(null), ...data.extrapolation.map(d => d.predicted)];

    currentChartInstances["devRegression"] = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "Actual", data: actuals, borderColor: "#0f172a", pointRadius: 1.5, showLine: false },
          { label: "OLS Linear Fit", data: fitted, borderColor: "#0284c7", borderWidth: 2, pointRadius: 0 },
          { label: "Extrapolated Trend", data: fut, borderColor: "#ef4444", borderDash: [4, 4], borderWidth: 2, pointRadius: 0 }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: { x: { ticks: { maxTicksLimit: 10 } } }
      }
    });
    showToast("OLS Regression line fitted", "info");
  } catch (e) {
    console.error("Regression error:", e);
  }
}

async function generateReport() {
  try {
    const res = await fetch(`${API_BASE}/api/report`);
    const data = await res.json();
    document.getElementById("dev-report-output").value = data.report;
    showToast("Compiled academic defense report", "success");
  } catch (e) {
    showToast("Report error: " + e, "error");
  }
}
