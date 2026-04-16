import * as R from "./router.js";

const DEFAULT_TIMEOUT_MS = 18000;

/* =========================
   安全ユーティリティ
========================= */
function safeStr(v) {
  return v == null ? "" : String(v);
}

/* =========================
   UI設定
========================= */
const UI_LAYOUT = {
  STREAMLIT: "streamlit",
  STREAMLIT_NAV: "streamlit-nav",
  STREAMLIT_NAV_MULTI: "streamlit-nav-multi",
  STREAMLIT_SERVICE: "streamlit-service",
  STREAMLIT_MARKET: "streamlit-market",
  TOP_NEWS: "top-news",
  NAV: "nav",
  DEFAULT: "default",
};

function sectionLayout(sec) {
  const m = (sec && sec.meta) || {};
  return sec?.layout || m.layout || UI_LAYOUT.DEFAULT;
}

function uiT(deps, s) {
  if (deps && typeof deps.T === "function") return deps.T(String(s ?? ""));
  return String(s ?? "");
}

/* =========================
   トレンド関連
========================= */

function tierBadgeClass(tier) {
  const t = safeStr(tier);
  if (t === "公的") return "lib-trend-badge lib-trend-badge--tier-ko";
  if (t === "業界") return "lib-trend-badge lib-trend-badge--tier-gy";
  return "lib-trend-badge lib-trend-badge--tier-oth";
}

function fmtTrendScore(template, score) {
  const n = Number(score) || 0;
  return safeStr(template)
    .replace("{score:.2f}", n.toFixed(2))
    .replace("{score}", String(n));
}

function passTrendFilters(row, catFilter, srcFilter, lbl) {
  if (catFilter !== lbl.trend_cat_all && safeStr(row.category) !== catFilter) return false;
  if (srcFilter === lbl.trend_src_all) return true;

  const sk = safeStr(row.source_key).toLowerCase();

  if (srcFilter === lbl.trend_src_kokudo) return sk === "kokudo";
  if (srcFilter === lbl.trend_src_sanki) return sk === "sanki";
  if (srcFilter === lbl.trend_src_reit) return sk === "reit";
  if (srcFilter === lbl.trend_src_other)
    return sk !== "kokudo" && sk !== "sanki" && sk !== "reit";

  return true;
}

/* =========================
   HTMLエスケープ
========================= */
function escapeHtmlStatic(s) {
  return safeStr(s).replace(/[&<>"']/g, function (c) {
    return {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c];
  });
}

/* =========================
   API通信
========================= */
async function fetchWithTimeout(url, options, timeoutMs) {
  const ctrl = new AbortController();
  const id = setTimeout(function () {
    ctrl.abort();
  }, timeoutMs);

  try {
    const r = await fetch(url, Object.assign({}, options, { signal: ctrl.signal }));
    return r;
  } finally {
    clearTimeout(id);
  }
}

export async function fetchUiJson(apiUrl, segment, lang, timeoutMs) {
  const ms = timeoutMs || DEFAULT_TIMEOUT_MS;
  const q = "?lang=" + encodeURIComponent(lang);
  const url = apiUrl("/api/ui/" + segment + q);

  const r = await fetchWithTimeout(
    url,
    { method: "GET", headers: { Accept: "application/json" } },
    ms
  );

  if (!r.ok) throw new Error(url + " → " + r.status);

  return JSON.parse(await r.text());
}

/* =========================
   表示
========================= */
export function showLoading(host) {
  host.innerHTML = '<div class="ui-loading"><p>Loading…</p></div>';
}

export function showFetchError(host, title, err) {
  const msg = safeStr((err && err.message) || err);
  host.innerHTML =
    '<div class="ui-error">' +
    "<h1>" + escapeHtmlStatic(title) + "</h1>" +
    "<pre>" + escapeHtmlStatic(msg) + "</pre>" +
    "</div>";
}

/* =========================
   ページ描画（最小安定版）
========================= */
export function renderUIPage(host, data, deps) {
  const escapeHtml = (deps && deps.escapeHtml) || escapeHtmlStatic;

  const title = safeStr(data && data.title);
  const sections = (data && data.sections) || [];

  if (!sections.length) {
    host.innerHTML = '<div class="ui-empty">No content (sections empty)</div>';
    return;
  }

  let html = "";

  for (let i = 0; i < sections.length; i++) {
    const sec = sections[i];
    html += "<section><h2>" + escapeHtml(sec.title || "") + "</h2></section>";
  }

  host.innerHTML = html;
}

/* =========================
   ナビ操作
========================= */
function wireUiInteractions(host) {
  const els = host.querySelectorAll("[data-hash-target]");
  for (let i = 0; i < els.length; i++) {
    const el = els[i];
    el.addEventListener("click", function () {
      const h = el.getAttribute("data-hash-target");
      if (h) location.hash = h;
    });
  }
}
