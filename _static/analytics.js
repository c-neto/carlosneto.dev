// Renders the public /analytics page from _static/analytics.json
// (generated daily in CI by scripts/goatcounter_export.py).
// Labels such as referrer names and page titles come from visitors, so they are
// always inserted with textContent, never innerHTML.
(function () {
  "use strict";

  const root = document.getElementById("gc-analytics");
  if (!root) return;

  const $ = (sel) => root.querySelector(sel);
  const fmt = new Intl.NumberFormat("en-US");
  const SVG = "http://www.w3.org/2000/svg";
  const RANGE_KEY = "gc-analytics-range";

  let data = null;
  let rangeKey = "30d";
  try { rangeKey = localStorage.getItem(RANGE_KEY) || "30d"; } catch (e) { /* storage blocked */ }

  // ---------- helpers ----------

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function svgEl(tag, attrs) {
    const node = document.createElementNS(SVG, tag);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  }

  function parseDay(day) {
    return new Date(day + "T00:00:00Z");
  }

  function fmtDay(day, withYear) {
    const opts = { month: "short", day: "numeric", timeZone: "UTC" };
    if (withYear) opts.year = "numeric";
    return parseDay(day).toLocaleDateString("en-US", opts);
  }

  function flag(code) {
    if (!/^[A-Za-z]{2}$/.test(code || "")) return "";
    return String.fromCodePoint(...[...code.toUpperCase()].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65));
  }

  function cleanTitle(title, path) {
    const t = (title || "").replace(/\s*[—–|-]\s*Carlos Neto.*$/i, "").trim();
    return t || path || "(unknown page)";
  }

  // Only same-site links: page paths are recorded by the counter script.
  function safeHref(path) {
    try {
      const url = new URL(path, window.location.origin);
      return url.origin === window.location.origin ? url.pathname : null;
    } catch (e) {
      return null;
    }
  }

  function niceStep(max, ticks) {
    const raw = Math.max(max, 1) / ticks;
    const pow = Math.pow(10, Math.floor(Math.log10(raw)));
    const n = raw / pow;
    const step = (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * pow;
    return Math.max(1, Math.round(step));
  }

  // ---------- label builders per list ----------

  const labels = {
    pages(it) {
      const text = cleanTitle(it.title, it.path);
      const href = safeHref(it.path);
      if (!href) return text;
      const a = el("a", null, text);
      a.href = href;
      return a;
    },
    countries(it) {
      const f = flag(it.id);
      return (f ? f + " " : "") + (it.name || it.id || "Unknown");
    },
    referrers(it) {
      return it.name || "Direct / unknown";
    },
    default(it) {
      return it.name || it.id || "Unknown";
    },
  };

  // ---------- renderers ----------

  function renderList(key, items, total) {
    const list = $(`[data-list="${key}"]`);
    list.replaceChildren();
    if (!items || !items.length) {
      list.append(el("li", "gc-empty", "No data in this range."));
      return;
    }
    const max = Math.max(...items.map((i) => i.count), 1);
    const label = labels[key] || labels.default;
    for (const it of items) {
      const row = el("li", "gc-row");
      const name = el("span", "gc-label");
      name.append(label(it));
      const share = total ? ` (${Math.round((it.count / total) * 100)}%)` : "";
      const value = el("span", "gc-val", fmt.format(it.count));
      value.title = `${fmt.format(it.count)} visitors${share}`;
      const track = el("span", "gc-track");
      const bar = el("span", "gc-bar");
      bar.style.width = `${Math.max((it.count / max) * 100, 1.5)}%`;
      track.append(bar);
      row.append(name, value, track);
      list.append(row);
    }
  }

  function renderTiles(r) {
    const days = r.daily.length || 1;
    const peak = r.daily.reduce((best, d) => (d.count > (best ? best.count : -1) ? d : best), null);
    $('[data-tile="total"]').textContent = fmt.format(r.total);
    $('[data-tile="avg"]').textContent = fmt.format(Math.round(r.total / days));
    $('[data-tile="peak"]').textContent = peak ? fmt.format(peak.count) : "–";
    $('[data-tile="peak-day"]').textContent = peak && peak.count ? fmtDay(peak.day, true) : "";
  }

  function renderChart(series) {
    const wrap = $('[data-chart="daily"]');
    wrap.replaceChildren();
    if (!series.length) {
      wrap.append(el("p", "gc-empty", "No data in this range."));
      return;
    }

    const W = Math.max(wrap.clientWidth, 280);
    const H = 220;
    const m = { t: 12, r: 12, b: 26, l: 36 };
    const iw = W - m.l - m.r;
    const ih = H - m.t - m.b;
    const maxVal = Math.max(...series.map((d) => d.count), 1);
    const step = niceStep(maxVal, 3);
    const yMax = Math.ceil(maxVal / step) * step;
    const x = (i) => m.l + (series.length === 1 ? iw / 2 : (i / (series.length - 1)) * iw);
    const y = (v) => m.t + ih - (v / yMax) * ih;

    const svg = svgEl("svg", {
      viewBox: `0 0 ${W} ${H}`,
      width: W,
      height: H,
      role: "img",
      "aria-label": `Visitors per day, ${series.length} days, peak ${fmt.format(maxVal)}`,
    });

    // Recessive grid + y labels
    for (let v = 0; v <= yMax; v += step) {
      svg.append(svgEl("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0 ? "gc-axis" : "gc-grid-line" }));
      const t = svgEl("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end", class: "gc-tick" });
      t.textContent = fmt.format(v);
      svg.append(t);
    }

    // X labels: first, middle, last
    const idx = [...new Set([0, Math.floor((series.length - 1) / 2), series.length - 1])];
    idx.forEach((i, n) => {
      const anchor = n === 0 ? "start" : i === series.length - 1 ? "end" : "middle";
      const t = svgEl("text", { x: x(i), y: H - 6, "text-anchor": anchor, class: "gc-tick" });
      t.textContent = fmtDay(series[i].day);
      svg.append(t);
    });

    const pts = series.map((d, i) => `${x(i).toFixed(1)},${y(d.count).toFixed(1)}`);
    svg.append(svgEl("path", {
      d: `M${x(0)},${y(0)} L${pts.join(" L")} L${x(series.length - 1)},${y(0)} Z`,
      class: "gc-area",
    }));
    svg.append(svgEl("path", { d: `M${pts.join(" L")}`, class: "gc-line" }));

    // Hover layer: crosshair + dot + tooltip
    const cross = svgEl("line", { y1: m.t, y2: m.t + ih, class: "gc-cross", visibility: "hidden" });
    const dot = svgEl("circle", { r: 4.5, class: "gc-dot", visibility: "hidden" });
    const hit = svgEl("rect", { x: m.l, y: m.t, width: iw, height: ih, fill: "transparent" });
    svg.append(cross, dot, hit);

    const tip = el("div", "gc-tip");
    tip.hidden = true;
    wrap.append(svg, tip);

    function show(evt) {
      const rect = svg.getBoundingClientRect();
      const px = ((evt.clientX - rect.left) / rect.width) * W;
      const i = Math.min(series.length - 1, Math.max(0, Math.round(((px - m.l) / iw) * (series.length - 1))));
      const d = series[i];
      cross.setAttribute("x1", x(i));
      cross.setAttribute("x2", x(i));
      dot.setAttribute("cx", x(i));
      dot.setAttribute("cy", y(d.count));
      cross.setAttribute("visibility", "visible");
      dot.setAttribute("visibility", "visible");
      tip.replaceChildren(el("strong", null, fmt.format(d.count)), document.createTextNode(` visitors · ${fmtDay(d.day, true)}`));
      tip.hidden = false;
      const left = (x(i) / W) * rect.width;
      tip.style.left = `${Math.min(Math.max(left, 70), rect.width - 70)}px`;
    }
    function hide() {
      cross.setAttribute("visibility", "hidden");
      dot.setAttribute("visibility", "hidden");
      tip.hidden = true;
    }
    hit.addEventListener("pointermove", show);
    hit.addEventListener("pointerdown", show);
    hit.addEventListener("pointerleave", hide);
  }

  function render() {
    const r = data.ranges[rangeKey] || data.ranges["30d"];
    root.querySelectorAll(".gc-range").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.range === rangeKey)));
    renderTiles(r);
    renderChart(r.daily || []);
    for (const key of ["pages", "countries", "referrers", "browsers", "systems", "sizes"]) {
      renderList(key, r[key], r.total);
    }
    const updated = new Date(data.generated_at);
    const updatedEl = $(".gc-updated");
    const goatCounter = document.createElement("a");
    goatCounter.href = "https://www.goatcounter.com/";
    goatCounter.textContent = "GoatCounter";
    updatedEl.replaceChildren(
      document.createTextNode(`Updated ${updated.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })}. Powered by `),
      goatCounter,
      document.createTextNode(", an open-source alternative to Google Analytics and Matomo. No cookies are stored, and no personal data is required."),
    );
  }

  // ---------- wiring ----------

  root.querySelectorAll(".gc-range").forEach((btn) => {
    btn.addEventListener("click", () => {
      rangeKey = btn.dataset.range;
      try { localStorage.setItem(RANGE_KEY, rangeKey); } catch (e) { /* storage blocked */ }
      if (data) render();
    });
  });

  let lastWidth = 0;
  new ResizeObserver(() => {
    const w = $('[data-chart="daily"]').clientWidth;
    if (data && Math.abs(w - lastWidth) > 4) {
      lastWidth = w;
      const r = data.ranges[rangeKey] || data.ranges["30d"];
      renderChart(r.daily || []);
    }
  }).observe(root);

  fetch(root.dataset.src, { cache: "no-cache" })
    .then((resp) => {
      if (!resp.ok) throw new Error(String(resp.status));
      return resp.json();
    })
    .then((json) => {
      if (!json || !json.ranges) throw new Error("bad payload");
      data = json;
      $(".gc-status").hidden = true;
      $(".gc-body").hidden = false;
      render();
    })
    .catch(() => {
      $(".gc-status").textContent = "No data yet. Stats are collected from day one and published daily, so check back soon.";
    });
})();
