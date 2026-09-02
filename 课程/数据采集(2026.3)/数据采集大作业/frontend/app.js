const DATA_PATHS = ["../data/weather_clean.json", "./data/weather_clean.json"];
const META_PATHS = ["../data/weather_metadata.json", "./data/weather_metadata.json"];

const state = {
  rows: [],
  meta: {},
  filtered: [],
  page: 1,
  pageSize: 18,
  filters: {
    year: "",
    season: "",
    weather: "",
    keyword: "",
    tempMin: -30,
  },
  charts: {},
};

const el = {
  sourceNote: document.querySelector("#sourceNote"),
  totalDays: document.querySelector("#totalDays"),
  avgTemp: document.querySelector("#avgTemp"),
  totalRain: document.querySelector("#totalRain"),
  extremeDays: document.querySelector("#extremeDays"),
  yearSelect: document.querySelector("#yearSelect"),
  seasonSelect: document.querySelector("#seasonSelect"),
  weatherSelect: document.querySelector("#weatherSelect"),
  keywordInput: document.querySelector("#keywordInput"),
  tempRange: document.querySelector("#tempRange"),
  tempValue: document.querySelector("#tempValue"),
  resetBtn: document.querySelector("#resetBtn"),
  tableCount: document.querySelector("#tableCount"),
  weatherTable: document.querySelector("#weatherTable"),
  prevPage: document.querySelector("#prevPage"),
  nextPage: document.querySelector("#nextPage"),
  pageInfo: document.querySelector("#pageInfo"),
  insightList: document.querySelector("#insightList"),
  weatherList: document.querySelector("#weatherList"),
  sourceStats: document.querySelector("#sourceStats"),
};

async function loadFirst(paths) {
  let lastError;
  for (const path of paths) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (response.ok) return response.json();
      lastError = new Error(`${path}: ${response.status}`);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("数据加载失败");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatNumber(value, digits = 0) {
  return new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value || 0));
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length : 0;
}

function sum(values) {
  return values.reduce((total, value) => total + Number(value || 0), 0);
}

function uniqueValues(field) {
  return [...new Set(state.rows.map((row) => row[field]).filter((value) => value !== undefined && value !== ""))].sort(
    (a, b) => String(a).localeCompare(String(b), "zh-CN")
  );
}

function fillSelect(select, values, label) {
  if (!select) return;
  select.innerHTML = `<option value="">全部${label}</option>${values
    .map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)
    .join("")}`;
}

function countBy(rows, field, limit = 0) {
  const map = new Map();
  for (const row of rows) {
    const key = row[field] || "未知";
    map.set(key, (map.get(key) || 0) + 1);
  }
  const data = [...map.entries()].map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);
  return limit ? data.slice(0, limit) : data;
}

function yearlySeries(rows) {
  const map = new Map();
  for (const row of rows) {
    if (!map.has(row.year)) map.set(row.year, { temps: [], rain: 0, hot: 0, cold: 0, windy: 0 });
    const item = map.get(row.year);
    item.temps.push(Number(row.temp_mean || 0));
    item.rain += Number(row.precipitation || 0);
    item.hot += row.is_hot ? 1 : 0;
    item.cold += row.is_cold ? 1 : 0;
    item.windy += row.is_windy ? 1 : 0;
  }
  return [...map.entries()]
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([year, item]) => ({
      name: String(year),
      avgTemp: Number(average(item.temps).toFixed(2)),
      rain: Number(item.rain.toFixed(2)),
      hot: item.hot,
      cold: item.cold,
      windy: item.windy,
    }));
}

function monthlySeries(rows) {
  const map = new Map();
  for (const row of rows) {
    const key = `${row.year}-${String(row.month).padStart(2, "0")}`;
    if (!map.has(key)) map.set(key, { temps: [], rain: 0 });
    const item = map.get(key);
    item.temps.push(Number(row.temp_mean || 0));
    item.rain += Number(row.precipitation || 0);
  }
  return [...map.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([month, item]) => ({ name: month, avgTemp: Number(average(item.temps).toFixed(2)), rain: Number(item.rain.toFixed(2)) }));
}

function seasonSeries(rows) {
  const order = ["春季", "夏季", "秋季", "冬季"];
  return order.map((season) => {
    const list = rows.filter((row) => row.season === season);
    return {
      name: season,
      avgTemp: Number(average(list.map((row) => row.temp_mean)).toFixed(2)),
      rain: Number(sum(list.map((row) => row.precipitation)).toFixed(2)),
      days: list.length,
    };
  });
}

function chart(id) {
  const node = document.querySelector(`#${id}`);
  if (!node) return null;
  if (!state.charts[id]) {
    state.charts[id] = window.echarts ? echarts.init(node) : createFallbackChart(node);
  }
  return state.charts[id];
}

function createFallbackChart(node) {
  return {
    setOption(option) {
      const series = option.series?.[0] || {};
      const isPie = series.type === "pie";
      const data = isPie
        ? series.data || []
        : (option.xAxis?.data || []).map((name, index) => ({ name, value: series.data?.[index] || 0 }));
      const max = Math.max(...data.map((item) => Number(item.value) || 0), 1);
      node.innerHTML = `<div class="fallback-chart">
        ${data
          .map((item) => {
            const percent = Math.max(3, Math.round(((Number(item.value) || 0) / max) * 100));
            return `<div class="fallback-row"><span>${escapeHtml(item.name)}</span><div><i style="width:${percent}%"></i></div><strong>${formatNumber(item.value, 1)}</strong></div>`;
          })
          .join("")}
      </div>`;
    },
    resize() {},
  };
}

function baseAxisOption() {
  return {
    animationDuration: 650,
    animationEasing: "cubicOut",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(76, 106, 132, 0.92)",
      borderColor: "rgba(255, 255, 255, 0.34)",
      textStyle: { color: "#ffffff" },
      extraCssText: "border-radius:14px;box-shadow:0 16px 36px rgba(43,68,90,.24);backdrop-filter:blur(12px);",
    },
    grid: { left: 48, right: 26, top: 34, bottom: 68 },
    xAxis: {
      type: "category",
      axisLabel: { color: "rgba(255,255,255,0.72)" },
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.2)" } },
      axisTick: { lineStyle: { color: "rgba(255,255,255,0.16)" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "rgba(255,255,255,0.72)" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.14)" } },
    },
  };
}

function renderLineChart(id, data, seriesDefs) {
  const instance = chart(id);
  if (!instance) return;
  instance.setOption({
    ...baseAxisOption(),
    color: ["#ffffff", "#45a7ff", "#ffd25c", "#f64f5f"],
    legend: { top: 0, textStyle: { color: "rgba(255,255,255,0.76)", fontWeight: 700 } },
    xAxis: { ...baseAxisOption().xAxis, data: data.map((item) => item.name), axisLabel: { color: "rgba(255,255,255,0.72)", rotate: data.length > 16 ? 35 : 0 } },
    series: seriesDefs.map((def) => ({
      name: def.name,
      type: def.type || "line",
      smooth: true,
      data: data.map((item) => item[def.key]),
      areaStyle: def.area ? { color: "rgba(255, 255, 255, 0.16)" } : undefined,
      lineStyle: { width: 3 },
      itemStyle: { shadowBlur: 14, shadowColor: "rgba(255, 255, 255, 0.34)" },
      barMaxWidth: 34,
      emphasis: { focus: "series" },
    })),
  });
}

function renderBarChart(id, data, color) {
  const instance = chart(id);
  if (!instance) return;
  const values = data.map((item) => Number(item.value) || 0);
  const hasNegative = values.some((value) => value < 0);
  const hasPositive = values.some((value) => value > 0);
  const maxAbs = Math.max(...values.map((value) => Math.abs(value)), 1);
  const axisPadding = Math.max(1, maxAbs * 0.14);
  const positiveColor = color || "#ffffff";
  const negativeColor = "#9fd8ff";
  instance.setOption({
    ...baseAxisOption(),
    color: [positiveColor, negativeColor],
    grid: { left: 48, right: 28, top: 30, bottom: 62 },
    xAxis: {
      ...baseAxisOption().xAxis,
      data: data.map((item) => item.name),
      axisLabel: { color: "rgba(255,255,255,0.78)", rotate: data.length > 8 ? 30 : 0, fontWeight: 700 },
      axisLine: {
        onZero: true,
        lineStyle: { color: hasNegative ? "rgba(255,255,255,0.62)" : "rgba(255,255,255,0.2)", width: hasNegative ? 2 : 1 },
      },
    },
    yAxis: {
      ...baseAxisOption().yAxis,
      min: hasNegative ? Math.floor(Math.min(...values) - axisPadding) : undefined,
      max: hasPositive ? Math.ceil(Math.max(...values) + axisPadding) : undefined,
      splitNumber: 5,
      axisLabel: { color: "rgba(255,255,255,0.72)", fontWeight: 700 },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.13)" } },
      axisLine: { show: hasNegative, lineStyle: { color: "rgba(255,255,255,0.22)" } },
    },
    tooltip: {
      ...baseAxisOption().tooltip,
      valueFormatter: (value) => formatNumber(value, 1),
    },
    series: [
      {
        type: "bar",
        data: data.map((item) => {
          const value = Number(item.value) || 0;
          return {
            value,
            label: {
              position: value < 0 ? "bottom" : "top",
            },
            itemStyle: {
              color: value < 0 ? negativeColor : positiveColor,
              borderRadius: value < 0 ? [4, 4, 14, 14] : [14, 14, 4, 4],
              shadowBlur: value === 0 ? 0 : 14,
              shadowColor: value < 0 ? "rgba(159, 216, 255, 0.28)" : "rgba(255, 255, 255, 0.26)",
            },
          };
        }),
        barMaxWidth: 32,
        barMinHeight: 3,
        label: {
          show: hasNegative,
          color: "rgba(255,255,255,0.86)",
          fontSize: 11,
          fontWeight: 800,
          formatter: ({ value }) => (Math.abs(Number(value)) < 1 ? "" : formatNumber(value, 1)),
        },
        markLine: hasNegative
          ? {
              symbol: "none",
              silent: true,
              label: { show: false },
              lineStyle: { color: "rgba(255,255,255,0.5)", width: 1.5, type: "solid" },
              data: [{ yAxis: 0 }],
            }
          : undefined,
        emphasis: { focus: "series" },
      },
    ],
  });
}

function renderPieChart(id, data) {
  const instance = chart(id);
  if (!instance) return;
  const total = data.reduce((value, item) => value + Number(item.value || 0), 0);
  const shortName = (name) => (String(name).length > 3 ? `${String(name).slice(0, 3)}…` : String(name));
  const sortedByValue = [...data].sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0));
  const top5Names = new Set(sortedByValue.slice(0, 5).map((item) => item.name));
  const pieData = data.map((item) => ({
    ...item,
    label: {
      show: total > 0 && top5Names.has(item.name),
    },
    labelLine: {
      show: total > 0 && top5Names.has(item.name),
    },
  }));
  instance.setOption({
    animationDuration: 650,
    animationEasing: "cubicOut",
    color: ["#ffffff", "#72d5e6", "#65d15d", "#ffd25c", "#ff9c3f", "#f64f5f", "#8a64d6"],
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(76, 106, 132, 0.92)",
      borderColor: "rgba(255, 255, 255, 0.34)",
      textStyle: { color: "#ffffff" },
      extraCssText: "border-radius:14px;box-shadow:0 16px 36px rgba(43,68,90,.24);backdrop-filter:blur(12px);",
    },
    legend: {
      bottom: 0,
      left: "center",
      type: "scroll",
      itemWidth: 9,
      itemHeight: 9,
      itemGap: 8,
      textStyle: { color: "rgba(255,255,255,0.78)", fontSize: 11, fontWeight: 800 },
      pageIconColor: "#ffffff",
      pageIconInactiveColor: "rgba(255,255,255,0.38)",
      pageTextStyle: { color: "rgba(255,255,255,0.72)" },
      formatter: (name) => {
        const item = data.find((entry) => entry.name === name);
        const percent = total ? (Number(item?.value || 0) / total) * 100 : 0;
        return `${shortName(name)} ${formatNumber(percent, 0)}%`;
      },
    },
    graphic: [
      {
        type: "group",
        left: "50%",
        top: "43%",
        bounding: "raw",
        children: [
          {
            type: "text",
            x: 0,
            y: -18,
            style: {
              text: "天气",
              fill: "#ffffff",
              fontSize: 20,
              fontWeight: 850,
              textAlign: "center",
              textVerticalAlign: "middle",
            },
          },
          {
            type: "text",
            x: 0,
            y: 12,
            style: {
              text: `${formatNumber(total)} 天`,
              fill: "rgba(255,255,255,0.68)",
              fontSize: 13,
              fontWeight: 800,
              textAlign: "center",
              textVerticalAlign: "middle",
            },
          },
        ],
      },
    ],
    series: [
      {
        type: "pie",
        radius: ["42%", "58%"],
        center: ["50%", "43%"],
        avoidLabelOverlap: true,
        minShowLabelAngle: 18,
        data: pieData,
        label: {
          position: "outside",
          alignTo: "edge",
          edgeDistance: 36,
          formatter: ({ name, percent }) => `${shortName(name)}\n${formatNumber(percent, 0)}%`,
          color: "#ffffff",
          fontSize: 12,
          fontWeight: 850,
          lineHeight: 16,
          textShadowColor: "rgba(45, 68, 88, 0.34)",
          textShadowBlur: 8,
        },
        labelLine: {
          length: 7,
          length2: 6,
          maxSurfaceAngle: 80,
          lineStyle: { color: "rgba(255,255,255,0.42)" },
        },
        emphasis: {
          scale: true,
          scaleSize: 6,
          label: {
            show: true,
            formatter: "{b}\n{d}%",
            color: "#ffffff",
            fontSize: 13,
            fontWeight: 800,
            lineHeight: 17,
          },
        },
        itemStyle: { borderColor: "rgba(111, 143, 171, 0.42)", borderWidth: 2 },
      },
    ],
  });
}

function applyFilters() {
  const keyword = state.filters.keyword.trim().toLowerCase();
  state.filtered = state.rows.filter((row) => {
    if (state.filters.year && String(row.year) !== String(state.filters.year)) return false;
    if (state.filters.season && row.season !== state.filters.season) return false;
    if (state.filters.weather && row.weather_text !== state.filters.weather) return false;
    if (Number(row.temp_max || 0) < state.filters.tempMin) return false;
    if (keyword) {
      const haystack = [row.date, row.year, row.month, row.season, row.weather_text, row.source].join(" ").toLowerCase();
      if (!haystack.includes(keyword)) return false;
    }
    return true;
  });
  state.page = 1;
  renderAll();
}

function renderSourceNote() {
  if (!el.sourceNote) return;
  el.sourceNote.textContent = `${state.meta.topic || "大连市近10年天气数据分析"}；样本 ${formatNumber(
    state.meta.total_days || state.rows.length
  )} 天；范围 ${state.meta.date_start || "-"} 至 ${state.meta.date_end || "-"}；来源 ${state.meta.source || "本地数据"}。`;
}

function renderMetrics() {
  if (!el.totalDays) return;
  const rows = state.filtered;
  const avgTempValue = average(rows.map((row) => row.temp_mean));
  el.totalDays.textContent = formatNumber(rows.length);
  el.avgTemp.textContent = `${formatNumber(avgTempValue, 1)}°C`;
  el.totalRain.textContent = `${formatNumber(sum(rows.map((row) => row.precipitation)), 1)}mm`;
  const extremes = rows.filter((row) => row.is_hot || row.is_cold || row.is_heavy_rain || row.is_windy).length;
  el.extremeDays.textContent = formatNumber(extremes);
  const extremeCard = el.extremeDays.closest("article");
  if (extremeCard) {
    const extremePercent = rows.length ? (extremes / rows.length) * 100 : 0;
    extremeCard.style.setProperty("--extreme-percent", `${Math.min(100, Math.max(0, extremePercent))}%`);
    let label = extremeCard.querySelector(".metric-percent-label");
    if (!label) {
      label = document.createElement("em");
      label.className = "metric-percent-label";
      extremeCard.append(label);
    }
    label.textContent = `${formatNumber(extremePercent, 1)}%`;
  }
  const tempCard = el.avgTemp.closest("article");
  if (tempCard) {
    const tempPercent = Math.min(92, Math.max(8, ((avgTempValue + 20) / 55) * 100));
    tempCard.classList.add("temp-card");
    tempCard.style.setProperty("--temp-left", `${tempPercent}%`);
    let pin = tempCard.querySelector(".metric-temp-pin");
    if (!pin) {
      pin = document.createElement("i");
      pin.className = "metric-temp-pin";
      pin.setAttribute("aria-hidden", "true");
      tempCard.append(pin);
    }
    pin.innerHTML = `<span>${formatNumber(avgTempValue, 1)}°C</span>`;
  }
}

function renderCharts() {
  const yearly = yearlySeries(state.filtered);
  const monthly = monthlySeries(state.filtered);
  const seasons = seasonSeries(state.filtered);
  renderLineChart("yearTempChart", yearly, [{ name: "年均温", key: "avgTemp", area: true }]);
  renderLineChart("yearRainChart", yearly, [{ name: "年降水", key: "rain", type: "bar" }]);
  renderLineChart("monthlyTrendChart", monthly, [
    { name: "月均温", key: "avgTemp", area: true },
    { name: "月降水", key: "rain", type: "bar" },
  ]);
  renderBarChart("seasonTempChart", seasons.map((item) => ({ name: item.name, value: item.avgTemp })), "#ffffff");
  renderBarChart("seasonRainChart", seasons.map((item) => ({ name: item.name, value: item.rain })), "#72d5e6");
  renderPieChart("weatherChart", countBy(state.filtered, "weather_text", 10));
  renderBarChart(
    "extremeChart",
    [
      { name: "高温日", value: state.filtered.filter((row) => row.is_hot).length },
      { name: "低温日", value: state.filtered.filter((row) => row.is_cold).length },
      { name: "降水日", value: state.filtered.filter((row) => row.is_rainy).length },
      { name: "大雨日", value: state.filtered.filter((row) => row.is_heavy_rain).length },
      { name: "大风日", value: state.filtered.filter((row) => row.is_windy).length },
      { name: "降雪日", value: state.filtered.filter((row) => row.is_snowy).length },
    ],
    "#ffd25c"
  );
}

function renderTable() {
  if (!el.weatherTable) return;
  const totalPages = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
  state.page = Math.min(state.page, totalPages);
  const start = (state.page - 1) * state.pageSize;
  const pageRows = state.filtered.slice(start, start + state.pageSize);
  el.tableCount.textContent = `${formatNumber(state.filtered.length)} 天`;
  el.pageInfo.textContent = `第 ${state.page} / ${totalPages} 页`;
  el.prevPage.disabled = state.page <= 1;
  el.nextPage.disabled = state.page >= totalPages;
  el.weatherTable.innerHTML = pageRows
    .map(
      (row) => `<tr>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.weather_text)}</td>
        <td>${formatNumber(row.temp_max, 1)} / ${formatNumber(row.temp_min, 1)}°C</td>
        <td>${formatNumber(row.temp_mean, 1)}°C</td>
        <td>${formatNumber(row.precipitation, 1)}mm</td>
        <td>${formatNumber(row.wind_max, 1)}km/h</td>
        <td><div class="skill-list">
          ${row.is_hot ? '<span class="skill">高温</span>' : ""}
          ${row.is_cold ? '<span class="skill">低温</span>' : ""}
          ${row.is_heavy_rain ? '<span class="skill">大雨</span>' : ""}
          ${row.is_windy ? '<span class="skill">大风</span>' : ""}
          ${row.is_snowy ? '<span class="skill">降雪</span>' : ""}
        </div></td>
      </tr>`
    )
    .join("");
}

function renderInsights() {
  if (!el.insightList) return;
  const rows = state.filtered;
  const hottest = rows.reduce((best, row) => (Number(row.temp_max) > Number(best?.temp_max ?? -999) ? row : best), null);
  const coldest = rows.reduce((best, row) => (Number(row.temp_min) < Number(best?.temp_min ?? 999) ? row : best), null);
  const wettest = rows.reduce((best, row) => (Number(row.precipitation) > Number(best?.precipitation ?? -1) ? row : best), null);
  const windy = rows.reduce((best, row) => (Number(row.wind_max) > Number(best?.wind_max ?? -1) ? row : best), null);
  const items = [
    ["最高温日期", hottest ? `${hottest.date} · ${formatNumber(hottest.temp_max, 1)}°C` : "暂无"],
    ["最低温日期", coldest ? `${coldest.date} · ${formatNumber(coldest.temp_min, 1)}°C` : "暂无"],
    ["最大降水", wettest ? `${wettest.date} · ${formatNumber(wettest.precipitation, 1)}mm` : "暂无"],
    ["最大风速", windy ? `${windy.date} · ${formatNumber(windy.wind_max, 1)}km/h` : "暂无"],
  ];
  el.insightList.innerHTML = items
    .map(([label, value]) => `<article class="insight-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`)
    .join("");
}

function renderWeatherList() {
  if (!el.weatherList) return;
  const total = Math.max(state.filtered.length, 1);
  el.weatherList.innerHTML = countBy(state.filtered, "weather_text", 30)
    .map(
      (item, index) => `<article class="keyword-item">
        <span>${String(index + 1).padStart(2, "0")}</span>
        <strong>${escapeHtml(item.name)}</strong>
        <em>${formatNumber(item.value)} 天 · ${formatNumber((item.value / total) * 100, 1)}%</em>
      </article>`
    )
    .join("");
}

function renderSourceStats() {
  if (!el.sourceStats) return;
  const items = [
    ["主题", state.meta.topic || "大连市近10年天气数据分析"],
    ["数据来源", state.meta.source || "本地数据"],
    ["日期范围", `${state.meta.date_start || "-"} 至 ${state.meta.date_end || "-"}`],
    ["记录数量", `${formatNumber(state.meta.total_days || state.rows.length)} 天`],
    ["平均气温", `${formatNumber(state.meta.avg_temp, 1)}°C`],
    ["累计降水", `${formatNumber(state.meta.total_precipitation, 1)}mm`],
  ];
  el.sourceStats.innerHTML = items
    .map(([label, value]) => `<article class="source-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`)
    .join("");
}

function renderActiveNav() {
  const page = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".floating-nav a").forEach((link) => {
    const target = (link.getAttribute("href") || "").split("/").pop() || "index.html";
    link.classList.toggle("active", target === page || (page === "" && target === "index.html"));
  });
}

function bindNavEvents() {
  const nav = document.querySelector(".floating-nav");
  if (!nav) return;
  nav.addEventListener("pointerdown", (event) => {
    const link = event.target.closest("a");
    if (!link || !nav.contains(link)) return;
    nav.querySelectorAll("a.active").forEach((item) => item.classList.remove("active"));
    link.classList.add("active");
  });
}

function renderAll() {
  renderMetrics();
  renderCharts();
  renderTable();
  renderInsights();
  renderWeatherList();
  renderSourceStats();
}

function bindEvents() {
  const bindings = [
    [el.yearSelect, "year", "change"],
    [el.seasonSelect, "season", "change"],
    [el.weatherSelect, "weather", "change"],
    [el.keywordInput, "keyword", "input"],
  ];
  for (const [node, key, eventName] of bindings) {
    if (!node) continue;
    node.addEventListener(eventName, () => {
      state.filters[key] = node.value;
      applyFilters();
    });
  }
  if (el.tempRange) {
    el.tempRange.addEventListener("input", () => {
      state.filters.tempMin = Number(el.tempRange.value);
      el.tempValue.textContent = `${state.filters.tempMin}°C+`;
      applyFilters();
    });
  }
  if (el.resetBtn) {
    el.resetBtn.addEventListener("click", () => {
      state.filters = { year: "", season: "", weather: "", keyword: "", tempMin: -30 };
      if (el.yearSelect) el.yearSelect.value = "";
      if (el.seasonSelect) el.seasonSelect.value = "";
      if (el.weatherSelect) el.weatherSelect.value = "";
      if (el.keywordInput) el.keywordInput.value = "";
      if (el.tempRange) el.tempRange.value = "-30";
      if (el.tempValue) el.tempValue.textContent = "-30°C+";
      applyFilters();
    });
  }
  if (el.prevPage) {
    el.prevPage.addEventListener("click", () => {
      state.page -= 1;
      renderTable();
    });
  }
  if (el.nextPage) {
    el.nextPage.addEventListener("click", () => {
      state.page += 1;
      renderTable();
    });
  }
  let resizeFrame = 0;
  window.addEventListener("resize", () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      for (const instance of Object.values(state.charts)) instance.resize();
    });
  });
}

async function init() {
  renderActiveNav();
  bindNavEvents();
  try {
    const embeddedRows = window.WEATHER_DATA;
    const embeddedMeta = window.WEATHER_META;
    const [rows, meta] = embeddedRows
      ? [embeddedRows, embeddedMeta || {}]
      : await Promise.all([loadFirst(DATA_PATHS), loadFirst(META_PATHS).catch(() => ({}))]);
    state.rows = rows;
    state.meta = meta;
    state.filtered = [...rows];
    fillSelect(el.yearSelect, uniqueValues("year"), "年份");
    fillSelect(el.seasonSelect, ["春季", "夏季", "秋季", "冬季"], "季节");
    fillSelect(el.weatherSelect, uniqueValues("weather_text"), "天气");
    bindEvents();
    renderSourceNote();
    renderAll();
  } catch (error) {
    if (el.sourceNote) {
      el.sourceNote.textContent = `数据加载失败：${error.message}`;
    }
  }
}

init();
