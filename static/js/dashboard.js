"use strict";

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  ticker: "",
  period: "1y",
  data: null,
  priceChart: null,
  rsiChart: null,
  macdChart: null,
};

// ── DOM refs ───────────────────────────────────────────────────────────────
const el = {
  tickerInput:  document.getElementById("ticker-input"),
  periodSelect: document.getElementById("period-select"),
  searchBtn:    document.getElementById("search-btn"),
  addInput:     document.getElementById("add-input"),
  addBtn:       document.getElementById("add-btn"),
  watchlistUl:  document.getElementById("watchlist-ul"),
  loading:      document.getElementById("loading"),
  errorMsg:     document.getElementById("error-msg"),
  infoBar:      document.getElementById("info-bar"),
  infoTicker:   document.getElementById("info-ticker"),
  infoPrice:    document.getElementById("info-price"),
  infoDate:     document.getElementById("info-date"),
  chartsArea:   document.getElementById("charts-area"),
  signalsArea:  document.getElementById("signals-area"),
  signalsBody:  document.getElementById("signals-body"),
  signalsTable: document.getElementById("signals-table"),
  noSignals:    document.getElementById("no-signals"),
};

// ── API helpers ────────────────────────────────────────────────────────────

async function apiGet(path) {
  const resp = await fetch(path);
  const json = await resp.json();
  if (!resp.ok) throw new Error(json.error || "Request failed");
  return json;
}

async function apiPost(path, body) {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const json = await resp.json();
  if (!resp.ok) throw new Error(json.error || "Request failed");
  return json;
}

async function apiDelete(path) {
  const resp = await fetch(path, { method: "DELETE" });
  const json = await resp.json();
  if (!resp.ok) throw new Error(json.error || "Request failed");
  return json;
}

// ── UI state helpers ───────────────────────────────────────────────────────

function showLoading(on) {
  el.loading.classList.toggle("hidden", !on);
  el.searchBtn.disabled = on;
}

function showError(msg) {
  el.errorMsg.textContent = msg;
  el.errorMsg.classList.remove("hidden");
}

function clearError() {
  el.errorMsg.classList.add("hidden");
  el.errorMsg.textContent = "";
}

function setChartsVisible(on) {
  el.chartsArea.classList.toggle("hidden", !on);
  el.infoBar.classList.toggle("hidden", !on);
  el.signalsArea.classList.toggle("hidden", !on);
}

// ── Watchlist UI ───────────────────────────────────────────────────────────

async function loadWatchlist() {
  try {
    const data = await apiGet("/api/watchlist");
    renderWatchlist(data.tickers);
  } catch (e) {
    console.error("watchlist load failed:", e.message);
  }
}

function renderWatchlist(tickers) {
  el.watchlistUl.innerHTML = "";
  for (const ticker of tickers) {
    const li = document.createElement("li");
    li.dataset.ticker = ticker;
    if (ticker === state.ticker) li.classList.add("active");

    const nameSpan = document.createElement("span");
    nameSpan.className = "ticker-name";
    nameSpan.textContent = ticker;

    const delBtn = document.createElement("button");
    delBtn.className = "del-btn";
    delBtn.title = "삭제";
    delBtn.textContent = "✕";
    delBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await removeTicker(ticker);
    });

    li.appendChild(nameSpan);
    li.appendChild(delBtn);
    li.addEventListener("click", () => {
      el.tickerInput.value = ticker;
      runAnalysis(ticker, state.period);
    });

    el.watchlistUl.appendChild(li);
  }
}

async function addTicker() {
  const ticker = el.addInput.value.trim().toUpperCase();
  if (!ticker) return;
  try {
    const data = await apiPost("/api/watchlist", { ticker });
    el.addInput.value = "";
    renderWatchlist(data.tickers);
  } catch (e) {
    alert(e.message);
  }
}

async function removeTicker(ticker) {
  try {
    const data = await apiDelete(`/api/watchlist/${ticker}`);
    renderWatchlist(data.tickers);
  } catch (e) {
    alert(e.message);
  }
}

// ── Analysis ───────────────────────────────────────────────────────────────

async function runAnalysis(ticker, period) {
  if (!ticker) return;
  clearError();
  showLoading(true);
  setChartsVisible(false);

  state.ticker = ticker;
  state.period = period;

  // 활성 아이템 표시
  document.querySelectorAll("#watchlist-ul li").forEach((li) => {
    li.classList.toggle("active", li.dataset.ticker === ticker);
  });

  try {
    const data = await apiGet(`/api/analyze?ticker=${encodeURIComponent(ticker)}&period=${period}`);
    state.data = data;
    renderAll(data);
    setChartsVisible(true);
  } catch (e) {
    showError(`분석 실패: ${e.message}`);
  } finally {
    showLoading(false);
  }
}

// ── Render all ─────────────────────────────────────────────────────────────

function renderAll(data) {
  const labels = data.ohlcv.map((d) => d.date);

  // Info bar
  const last = data.ohlcv[data.ohlcv.length - 1];
  el.infoTicker.textContent = data.ticker;
  el.infoPrice.textContent = last ? `$${last.close?.toLocaleString()}` : "";
  el.infoDate.textContent = `최신: ${data.last_updated}`;

  renderPriceChart(labels, data);
  renderRsiChart(labels, data);
  renderMacdChart(labels, data);
  renderSignals(data.signals);
}

// ── Chart: Price + MA + BB + Signals ──────────────────────────────────────

function renderPriceChart(labels, data) {
  if (state.priceChart) state.priceChart.destroy();

  const closeData   = data.ohlcv.map((d) => d.close);
  const ma5Data     = data.indicators.ma.map((d) => d.ma5);
  const ma20Data    = data.indicators.ma.map((d) => d.ma20);
  const ma60Data    = data.indicators.ma.map((d) => d.ma60);
  const bbUpperData = data.indicators.bollinger.map((d) => d.upper);
  const bbLowerData = data.indicators.bollinger.map((d) => d.lower);

  // Build signal marker arrays (null = no point)
  const buyPrices  = new Array(labels.length).fill(null);
  const sellPrices = new Array(labels.length).fill(null);
  const labelIndex = new Map(labels.map((l, i) => [l, i]));

  for (const sig of data.signals) {
    const idx = labelIndex.get(sig.date);
    if (idx === undefined) continue;
    if (sig.type === "BUY")  buyPrices[idx]  = sig.price;
    if (sig.type === "SELL") sellPrices[idx] = sig.price;
  }

  const buyRadius  = buyPrices.map((v)  => (v !== null ? 9 : 0));
  const sellRadius = sellPrices.map((v) => (v !== null ? 9 : 0));

  const ctx = document.getElementById("price-chart").getContext("2d");
  state.priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Close",
          data: closeData,
          borderColor: "#2196F3",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: "MA5",
          data: ma5Data,
          borderColor: "#FF9800",
          borderWidth: 1,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: "MA20",
          data: ma20Data,
          borderColor: "#9C27B0",
          borderWidth: 1,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: "MA60",
          data: ma60Data,
          borderColor: "#F44336",
          borderWidth: 1,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: "BB Upper",
          data: bbUpperData,
          borderColor: "#78909C",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0,
          fill: false,
        },
        {
          label: "BB Lower",
          data: bbLowerData,
          borderColor: "#78909C",
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0,
          fill: { target: 4, above: "rgba(120,144,156,0.08)", below: "rgba(120,144,156,0.08)" },
          backgroundColor: "rgba(120,144,156,0.08)",
        },
        {
          label: "Buy ▲",
          data: buyPrices,
          showLine: false,
          pointStyle: "triangle",
          pointRadius: buyRadius,
          pointBackgroundColor: "#3fb950",
          pointBorderColor: "#3fb950",
          borderColor: "transparent",
          backgroundColor: "transparent",
        },
        {
          label: "Sell ▽",
          data: sellPrices,
          showLine: false,
          pointStyle: "triangle",
          rotation: 180,
          pointRadius: sellRadius,
          pointBackgroundColor: "#f85149",
          pointBorderColor: "#f85149",
          borderColor: "transparent",
          backgroundColor: "transparent",
        },
      ],
    },
    options: chartOptions(`${data.ticker} 가격 차트`),
  });
}

// ── Chart: RSI ─────────────────────────────────────────────────────────────

function renderRsiChart(labels, data) {
  if (state.rsiChart) state.rsiChart.destroy();

  const rsiData   = data.indicators.rsi.map((d) => d.value);
  const lineSize   = labels.length;
  const obLine    = new Array(lineSize).fill(70);
  const osLine    = new Array(lineSize).fill(30);

  const ctx = document.getElementById("rsi-chart").getContext("2d");
  state.rsiChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "RSI",
          data: rsiData,
          borderColor: "#00BCD4",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0,
          fill: false,
        },
        {
          label: "과매수(70)",
          data: obLine,
          borderColor: "#f85149",
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
        },
        {
          label: "과매도(30)",
          data: osLine,
          borderColor: "#3fb950",
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      ...chartOptions("RSI"),
      scales: {
        x: xScaleOpts(),
        y: { ...yScaleOpts(), min: 0, max: 100 },
      },
    },
  });
}

// ── Chart: MACD ────────────────────────────────────────────────────────────

function renderMacdChart(labels, data) {
  if (state.macdChart) state.macdChart.destroy();

  const macdData   = data.indicators.macd.map((d) => d.macd);
  const signalData = data.indicators.macd.map((d) => d.signal);
  const histData   = data.indicators.macd.map((d) => d.histogram);
  const histColors = histData.map((v) =>
    v === null ? "transparent" : v >= 0 ? "#3fb950" : "#f85149"
  );

  const ctx = document.getElementById("macd-chart").getContext("2d");
  state.macdChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          type: "bar",
          label: "Histogram",
          data: histData,
          backgroundColor: histColors,
          borderWidth: 0,
          barPercentage: 1.0,
          categoryPercentage: 1.0,
        },
        {
          type: "line",
          label: "MACD",
          data: macdData,
          borderColor: "#2196F3",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0,
        },
        {
          type: "line",
          label: "Signal",
          data: signalData,
          borderColor: "#FF9800",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0,
        },
      ],
    },
    options: chartOptions("MACD"),
  });
}

// ── Signals table ──────────────────────────────────────────────────────────

function renderSignals(signals) {
  el.signalsBody.innerHTML = "";

  const recent = [...signals].reverse().slice(0, 15);

  if (recent.length === 0) {
    el.noSignals.classList.remove("hidden");
    el.signalsTable.classList.add("hidden");
    return;
  }

  el.noSignals.classList.add("hidden");
  el.signalsTable.classList.remove("hidden");

  for (const sig of recent) {
    const tr = document.createElement("tr");
    const isBuy = sig.type === "BUY";
    tr.innerHTML = `
      <td>${sig.date}</td>
      <td class="${isBuy ? "signal-buy" : "signal-sell"}">${isBuy ? "▲ BUY" : "▽ SELL"}</td>
      <td>${sig.price?.toLocaleString()}</td>
      <td>${sig.stop_loss != null ? sig.stop_loss.toLocaleString() : "-"}</td>
      <td>${sig.target   != null ? sig.target.toLocaleString()   : "-"}</td>
      <td>${sig.reason}</td>
    `;
    el.signalsBody.appendChild(tr);
  }
}

// ── Chart option helpers ───────────────────────────────────────────────────

function xScaleOpts() {
  return {
    ticks: {
      maxTicksLimit: 8,
      maxRotation: 0,
      color: "#8b949e",
      font: { size: 11 },
    },
    grid: { color: "#21262d" },
  };
}

function yScaleOpts() {
  return {
    position: "right",
    ticks: { color: "#8b949e", font: { size: 11 } },
    grid: { color: "#21262d" },
  };
}

function chartOptions(title) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "top",
        labels: { color: "#8b949e", font: { size: 11 }, boxWidth: 12 },
      },
      title: {
        display: true,
        text: title,
        color: "#8b949e",
        font: { size: 12 },
        padding: { bottom: 6 },
      },
      tooltip: {
        backgroundColor: "#161b22",
        borderColor: "#30363d",
        borderWidth: 1,
        titleColor: "#c9d1d9",
        bodyColor: "#8b949e",
      },
    },
    scales: {
      x: xScaleOpts(),
      y: yScaleOpts(),
    },
  };
}

// ── Event listeners ────────────────────────────────────────────────────────

el.searchBtn.addEventListener("click", () => {
  const ticker = el.tickerInput.value.trim().toUpperCase();
  const period = el.periodSelect.value;
  if (ticker) runAnalysis(ticker, period);
});

el.tickerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") el.searchBtn.click();
});

el.addBtn.addEventListener("click", addTicker);

el.addInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") addTicker();
});

// ── Init ───────────────────────────────────────────────────────────────────

loadWatchlist();
