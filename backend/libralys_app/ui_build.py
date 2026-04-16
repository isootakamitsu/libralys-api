import * as R from "./router.js";

const DEFAULT_TIMEOUT_MS = 18000;


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
  const m = sec.meta || {};
  return sec.layout || m.layout || UI_LAYOUT.DEFAULT;
}


function uiT(deps, s) {
  if (deps && typeof deps.T === "function") return deps.T(String(s ?? ""));
  return String(s ?? "");
}

let _topnavCssOnce = false;

function encAssetRel(rel) {
  return String(rel || "")
    .split("/")
    .map((s) => encodeURIComponent(s))
    .join("/");
}

function topnavStreamlitKey(cardId) {
  return `topnav_${String(cardId).replace(/"/g, "")}`;
}

function injectTopNavCardCss(apiUrl, payload) {
  if (!document.head || !Array.isArray(payload) || !payload.length) return;
  if (_topnavCssOnce) return;
  _topnavCssOnce = true;
  const rules = [];
  for (const spec of payload) {
    const mh = "118px";
    const fs = "clamp(0.95rem, 2.3vw, 1.08rem)";
    const wk = topnavStreamlitKey(spec.cardId);
    const sel = `#page-host.page-top div.st-key-${wk} [data-testid="stButton"] button`;
    const selOn = `#page-host.page-top div.lib-ai-nav-onpage[data-lib-topnav-id="${String(spec.cardId).replace(/"/g, "")}"]`;
    let bgImg;
    let bgExtra;
    if (spec.image) {
      const u = apiUrl("/api/system-asset/" + encAssetRel(spec.image));
      bgImg =
        "linear-gradient(155deg, rgba(15,28,46,0) 0%, rgba(7,11,18,0) 52%, rgba(15,28,46,0) 100%), " + `url("${u}")`;
      bgExtra =
        "background-size: auto, cover !important;\n  background-position: center, center !important;\n  background-repeat: no-repeat, no-repeat !important;";
    } else {
      const p = ((Number(spec.preset) % 8) + 8) % 8;
      const palettes = [
        [195, 245, 38, 220],
        [265, 290, 48, 200],
        [175, 205, 42, 210],
        [210, 240, 45, 230],
        [155, 185, 40, 195],
        [230, 260, 50, 215],
        [200, 225, 44, 235],
        [185, 215, 36, 205],
      ];
      const [a, b, sat, glow] = palettes[p];
      const core = `linear-gradient(155deg, hsl(${a},${sat}%,16%) 0%, hsl(${b},${sat + 8}%,10%) 48%, #070b12 100%)`;
      const grid =
        "repeating-linear-gradient(0deg, transparent, transparent 18px, rgba(148,200,255,0.04) 18px, rgba(148,200,255,0.04) 19px), " +
        "repeating-linear-gradient(90deg, transparent, transparent 18px, rgba(148,200,255,0.04) 18px, rgba(148,200,255,0.04) 19px)";
      const glowR =
        `radial-gradient(ellipse 90% 60% at 20% 30%, hsla(${glow},55%,45%,0.22) 0%, transparent 55%), ` +
        `radial-gradient(ellipse 70% 50% at 85% 75%, hsla(${a},70%,50%,0.12) 0%, transparent 50%)`;
      const scan = "linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.04) 50%, transparent 60%)";
      bgImg = `${core}, ${glowR}, ${grid}, ${scan}`;
      bgExtra = "background-blend-mode: normal, normal, normal, normal !important;";
    }
    rules.push(`
${sel},
${selOn} {
  background-color: transparent !important;
  background-image: ${bgImg} !important;
  ${bgExtra}
  min-height: ${mh} !important;
  height: auto !important;
  white-space: normal !important;
  text-align: left !important;
  align-items: flex-start !important;
  justify-content: flex-end !important;
  padding: 1.05rem 1.1rem 1.15rem 1.1rem !important;
  color: #ffffff !important;
  font-weight: 800 !important;
  font-size: ${fs} !important;
  line-height: 1.4 !important;
  letter-spacing: 0.04em !important;
  border: 1px solid rgba(201, 169, 98, 0.55) !important;
  border-radius: 16px !important;
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.06),
    0 16px 48px rgba(15, 28, 46, 0.35),
    0 0 40px rgba(56, 189, 248, 0.06) !important;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease !important;
}
${selOn} {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  box-sizing: border-box !important;
}
${sel}:hover {
  background-color: transparent !important;
  cursor: pointer !important;
  transform: translateY(-2px);
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.1),
    0 22px 56px rgba(15, 28, 46, 0.42),
    0 0 48px rgba(201, 169, 98, 0.12) !important;
  border-color: rgba(201, 169, 98, 0.85) !important;
}
${sel}:focus-visible {
  outline: 2px solid rgba(201, 169, 98, 0.95) !important;
  outline-offset: 2px !important;
}
@media (max-width: 640px) {
  ${sel} {
    min-height: calc(${mh} + 12px) !important;
    padding: 1.05rem 1rem 1.15rem 1rem !important;
  }
}
${sel} p,
${selOn} p,
${sel} span,
${selOn} span {
  color: #ffffff !important;
  font-size: inherit !important;
  font-weight: 800 !important;
  letter-spacing: inherit !important;
  line-height: inherit !important;
  text-shadow:
    0 1px 0 rgba(15, 28, 46, 0.65),
    0 2px 4px rgba(0, 0, 0, 0.55),
    0 3px 22px rgba(0, 0, 0, 0.95),
    0 0 10px rgba(0, 0, 0, 0.88) !important;
}
`);
  }
  const st = document.createElement("style");
  st.id = "lib-topnav-ai-bg";
  st.textContent = rules.join("\n");
  const prev = document.getElementById("lib-topnav-ai-bg");
  if (prev) prev.replaceWith(st);
  else document.head.appendChild(st);
}

function tierBadgeClass(tier) {
  const t = String(tier);
  if (t === "公的") return "lib-trend-badge lib-trend-badge--tier-ko";
  if (t === "業界") return "lib-trend-badge lib-trend-badge--tier-gy";
  return "lib-trend-badge lib-trend-badge--tier-oth";
}

function fmtTrendScore(template, score) {
  const n = Number(score) || 0;
  return String(template).replace("{score:.2f}", n.toFixed(2)).replace("{score}", String(n));
}

function passTrendFilters(row, catFilter, srcFilter, lbl) {
  if (catFilter !== lbl.trend_cat_all && String(row.category) !== catFilter) return false;
  if (srcFilter === lbl.trend_src_all) return true;
  const sk = String(row.source_key || "other").toLowerCase();
  if (srcFilter === lbl.trend_src_kokudo) return sk === "kokudo";
  if (srcFilter === lbl.trend_src_sanki) return sk === "sanki";
  if (srcFilter === lbl.trend_src_reit) return sk === "reit";
  if (srcFilter === lbl.trend_src_other) return sk !== "kokudo" && sk !== "sanki" && sk !== "reit";
  return true;
}

function trendSpotlightCardHtml(row, escapeHtml, today, langFn, lbl) {
  const title = langFn() === "en" ? row.title_en || row.title_ja : row.title_ja;
  const summary = row.summary || "";
  const pub = String(row.pub_date_iso || "").slice(0, 10);
  const pubDate = new Date(pub + "T00:00:00");
  const ageDays = !isNaN(pubDate.getTime()) ? Math.floor((today - pubDate) / 86400000) : 999;
  const newBadge = ageDays <= 14;
  const newHtml = newBadge ? '<span class="lib-trend-badge lib-trend-badge--new">NEW</span>' : "";
  const tier = String(row.reliability_tier || "");
  const tierHtml = `<span class="${tierBadgeClass(tier)}">${escapeHtml(tier)}</span>`;
  const catHtml = `<span class="lib-trend-badge lib-trend-badge--tier-oth">${escapeHtml(row.category)}</span>`;
  const fixedScore = fmtTrendScore(lbl.trend_score_caption, row.display_score);
  const url = String(row.source_url || "");
  let link = "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    link = `<p class="lib-trend-wrap" style="margin:0.35rem 0 0 0"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(lbl.trend_open_official)}</a></p>`;
  }
  return (
    `<div class="lib-trend-wrap lib-trend-card lib-trend-card--spotlight">` +
    `<div class="lib-trend-badges">${newHtml}${tierHtml}${catHtml}</div>` +
    `<p class="lib-trend-card-title">${escapeHtml(title)}</p>` +
    `<p class="lib-trend-card-sum">${escapeHtml(summary)}</p>` +
    `<p class="lib-trend-meta">${escapeHtml(row.source_label != null ? row.source_label : "")} · ${escapeHtml(pub)}</p>` +
    `<p class="lib-trend-score">${escapeHtml(fixedScore)}</p></div>${link}`
  );
}

function trendRowHtml(row, escapeHtml, today, compact, langFn, lbl) {
  const title = langFn() === "en" ? row.title_en || row.title_ja : row.title_ja;
  const summary = row.summary || "";
  const pub = String(row.pub_date_iso || "").slice(0, 10);
  const pubDate = new Date(pub + "T00:00:00");
  const ageDays = !isNaN(pubDate.getTime()) ? Math.floor((today - pubDate) / 86400000) : 999;
  const newHtml = ageDays <= 14 ? '<span class="lib-trend-badge lib-trend-badge--new">NEW</span> ' : "";
  const tier = String(row.reliability_tier || "");
  const tierBadge = `<span class="${tierBadgeClass(tier)}">${escapeHtml(tier)}</span> `;
  let scoreHtml = "";
  if (!compact) {
    const sc = fmtTrendScore(lbl.trend_score_caption, row.display_score);
    scoreHtml = `<p class="lib-trend-score">${escapeHtml(sc)}</p>`;
  }
  const left =
    `<div class="lib-trend-wrap">` +
    `<p class="lib-trend-row-title">${newHtml}${escapeHtml(title)}</p>` +
    `<p class="lib-trend-meta">${tierBadge}${escapeHtml(row.source_label != null ? row.source_label : "")} · ${escapeHtml(pub)} · ${escapeHtml(row.category)}</p>` +
    `${scoreHtml}</div>`;
  const mid = `<div class="lib-trend-wrap"><p class="lib-trend-card-sum" style="margin:0">${escapeHtml(summary)}</p></div>`;
  const url = String(row.source_url || "");
  let link = "";
  if (url.startsWith("http://") || url.startsWith("https://")) {
    link = `<p class="lib-trend-wrap" style="margin:0.35rem 0 0 0"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(lbl.trend_open_official)}</a></p>`;
  }
  return `<div class="lib-trend-row">${left}<div>${mid}</div><div></div></div>${link}`;
}

function renderTrendDynamic(host, box, items, lbl, escapeHtml, langFn) {
  if (!box) return;
  const catSel = host.querySelector("#lib_trend_filter_category");
  const srcSel = host.querySelector("#lib_trend_filter_source");
  const catFilter = catSel ? catSel.value : lbl.trend_cat_all;
  const srcFilter = srcSel ? srcSel.value : lbl.trend_src_all;
  const activeAll = items.filter((r) => !r.archived);
  const archived = items.filter((r) => r.archived);
  const active = activeAll.filter((r) => passTrendFilters(r, catFilter, srcFilter, lbl));
  const archivedF = archived.filter((r) => passTrendFilters(r, catFilter, srcFilter, lbl));

  if (!active.length && !archivedF.length) {
    box.innerHTML = `<div class="lib-trend-wrap lib-trend-st-info">${escapeHtml(lbl.trend_empty)}</div>`;
    return;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const spotlight = active.slice(0, 3);
  const rest = active.slice(3);

  let html = "";
  html += `<div class="lib-trend-wrap"><p class="lib-trend-note"><b>${escapeHtml(lbl.trend_spotlight_heading)}</b></p></div>`;
  if (spotlight.length) {
    const n = Math.min(3, spotlight.length);
    let spotCls = "lib-trend-spotlight-cols";
    if (n === 1) spotCls += " lib-trend-spotlight-cols--1";
    else if (n === 2) spotCls += " lib-trend-spotlight-cols--2";
    html += `<div class="${spotCls}">`;
    for (let i = 0; i < n; i++) {
      html += `<div class="lib-sl-column">${trendSpotlightCardHtml(spotlight[i], escapeHtml, today, langFn, lbl)}</div>`;
    }
    html += "</div>";
  } else {
    html += `<p class="lib-trend-caption">${escapeHtml(lbl.trend_spotlight_empty)}</p>`;
  }

  if (rest.length) {
    html += `<details class="lib-st-expander"><summary>${escapeHtml(lbl.trend_by_use_heading)}</summary><div class="lib-trend-expander-body">`;
    for (const row of rest) {
      html += trendRowHtml(row, escapeHtml, today, false, langFn, lbl);
    }
    html += "</div></details>";
  } else {
    html += `<p class="lib-trend-caption">${escapeHtml(lbl.trend_list_empty)}</p>`;
  }

  if (archivedF.length) {
    html += '<hr class="lib-trend-sep" />';
    html += `<details class="lib-st-expander"><summary>${escapeHtml(lbl.trend_archive_expander)}</summary><div class="lib-trend-expander-body">`;
    const byMonth = new Map();
    for (const row of archivedF.slice().sort((a, b) => {
      const pa = String(a.pub_date_iso || "");
      const pb = String(b.pub_date_iso || "");
      if (pa !== pb) return pb.localeCompare(pa);
      return String(b.id || "").localeCompare(String(a.id || ""));
    })) {
      const ym = String(row.pub_date_iso || "").slice(0, 7) || "—";
      if (!byMonth.has(ym)) byMonth.set(ym, []);
      byMonth.get(ym).push(row);
    }
    const yms = Array.from(byMonth.keys()).sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
    for (const ym of yms) {
      html += `<div class="lib-trend-wrap"><p class="lib-trend-archive-month">${escapeHtml(lbl.trend_archive_month_prefix)} ${escapeHtml(ym)}</p></div>`;
      for (const row of byMonth.get(ym)) {
        html += trendRowHtml(row, escapeHtml, today, true, langFn, lbl);
      }
    }
    html += "</div></details>";
  }

  box.innerHTML = html;
}

function wireTrendSection(host, deps, trendJson) {
  const box = host.querySelector("#lib-trend-dynamic");
  if (!box || !trendJson) return;
  const items = trendJson.items || [];
  const lbl = trendJson.labels || {};
  const escapeHtml = deps.escapeHtml;
  const langFn = deps.lang || (() => "ja");
  const rerender = () => {
    try {
      renderTrendDynamic(host, box, items, lbl, escapeHtml, langFn);
    } catch (e) {
      console.error(e);
    }
  };
  const catSel = host.querySelector("#lib_trend_filter_category");
  const srcSel = host.querySelector("#lib_trend_filter_source");
  if (catSel) catSel.addEventListener("change", rerender);
  if (srcSel) srcSel.addEventListener("change", rerender);
  rerender();
}

function renderHeroStreamlit(sec, escapeHtml, deps) {
  const m = sec.meta || {};
  const apiUrl = deps.apiUrl;
  const bgRel = m.background || "image/ai_realestate_bg.jpg";
  const photoUrl = escapeHtml(apiUrl("/api/system-asset/" + encAssetRel(bgRel)));
  const hl = escapeHtml(m.lang || "ja");
  const subLines = (m.subcopy_lines || [])
    .map((x) => escapeHtml(uiT(deps, String(x))))
    .join("<br><br>");
  const ctas = (m.ctas || [])
    .map((c) => {
      const kind = c.variant === "secondary" ? "baseButton-secondary" : "baseButton-primary";
      const kv = c.variant === "secondary" ? "secondary" : "primary";
      return (
        `<div class="lib-sl-column" data-testid="column">` +
        `<div data-testid="stButton"><button type="button" data-testid="${kind}" kind="${kv}" data-hash-target="${escapeHtml(c.target || "")}">${escapeHtml(uiT(deps, c.label || ""))}</button></div></div>`
      );
    })
    .join("");
  return (
    `<div class="streamlit-hero hero-visual hero-visual--fullvp" lang="${hl}" style="--lib-hero-photo:url('${photoUrl}');">` +
    `<div class="hero-visual__bg streamlit-hero__bg" aria-hidden="true"></div>` +
    `<div class="hero-inner streamlit-hero-inner">` +
    `<div class="hero-copy hero-copy-panel">` +
    `<p class="hero-tagline-jp">${escapeHtml(uiT(deps, m.kicker || ""))}</p>` +
    `<p class="hero-micro-en" lang="en">${escapeHtml(uiT(deps, m.micro_en || ""))}</p>` +
    `<div class="headline">${escapeHtml(uiT(deps, m.headline || ""))}</div>` +
    `<div class="gold-line" aria-hidden="true"></div>` +
    `<div class="subcopy">${subLines}<br><br></div>` +
    `<p class="hero-footnote">${escapeHtml(uiT(deps, m.footnote || ""))}</p>` +
    `</div></div></div>` +
    `<div class="lib-sl-columns lib-sl-columns-2 lib-sl-gap-small lib-top-hero-cta-row">` +
    ctas +
    `</div>` +
    `<div class="hr" role="separator" aria-hidden="true"></div>`
  );
}

function renderMarkup(sec, escapeHtml) {
  const html = (sec.meta && sec.meta.html) || "";
  if (!html) return '<section class="ui-sec ui-sec--markup"></section>';
  return `<section class="ui-sec ui-sec--markup" data-markup-trusted="1">${html}</section>`;
}

function renderTrends(sec, escapeHtml, liteBoldHtml, _deps) {
  const m = sec.meta || {};
  const lbl = m.labels || {};
  const trendSectionTitle =
    `<div class="lib-corp-sec">` +
    `<h3 class="lib-corp-sec-jp">${escapeHtml(lbl.trend_section_title || "")}</h3>` +
    `<div class="lib-corp-sec-line" aria-hidden="true"></div></div>`;
  const trendFilters =
    `<div class="lib-trend-filters-row lib-sl-columns-2 lib-sl-gap-default">` +
    `<div class="lib-sl-column">` +
    `<label class="lib-st-widget-label" for="lib_trend_filter_category">${escapeHtml(lbl.trend_filter_category || "")}</label>` +
    `<select id="lib_trend_filter_category" class="lib-st-select">` +
    `<option>${escapeHtml(lbl.trend_cat_all || "")}</option>` +
    `<option>住宅</option><option>オフィス</option><option>商業</option><option>J-REIT</option>` +
    `</select></div>` +
    `<div class="lib-sl-column">` +
    `<label class="lib-st-widget-label" for="lib_trend_filter_source">${escapeHtml(lbl.trend_filter_source || "")}</label>` +
    `<select id="lib_trend_filter_source" class="lib-st-select">` +
    `<option>${escapeHtml(lbl.trend_src_all || "")}</option>` +
    `<option>${escapeHtml(lbl.trend_src_kokudo || "")}</option>` +
    `<option>${escapeHtml(lbl.trend_src_sanki || "")}</option>` +
    `<option>${escapeHtml(lbl.trend_src_reit || "")}</option>` +
    `<option>${escapeHtml(lbl.trend_src_other || "")}</option>` +
    `</select></div></div>`;
  return (
    `<section class="lib-top-trends">` +
    trendSectionTitle +
    `<details class="lib-st-expander"><summary>${escapeHtml(lbl.trend_notes_expander || "")}</summary>` +
    `<div class="lib-trend-notes-md">${liteBoldHtml(lbl.trend_section_sub || "")}</div>` +
    `<div class="lib-trend-notes-md">${liteBoldHtml(lbl.trend_legal_note || "")}</div></details>` +
    trendFilters +
    `<div id="lib-trend-dynamic" class="lib-trend-dynamic"></div>` +
    `</section><div class="hr" role="separator" aria-hidden="true"></div>`
  );
}

function renderStreamlitNavMulti(sec, escapeHtml, deps) {
  const m = sec.meta || {};
  const groups = m.groups || [];
  const cur = deps.getHashPage ? deps.getHashPage() : "";
  const onPagePrefix = deps.lang && deps.lang() === "en" ? "Viewing: " : "表示中：";
  let navHtml = "";
  for (let gi = 0; gi < groups.length; gi++) {
    const pages = groups[gi];
    const n = pages.length;
    const colsPer = Math.min(5, Math.max(1, n));
    navHtml += `<div class="lib-topnav-group-rows" data-group-idx="${gi}">`;
    navHtml += `<div class="lib-sl-columns lib-sl-columns-${colsPer} lib-sl-gap-medium">`;
    for (let j = 0; j < colsPer; j++) {
      navHtml += '<div class="lib-sl-column">';
      if (j < n) {
        const it = pages[j];
        const page = it.page;
        const onPage = page === cur;
        const cid = escapeHtml(it.cardId || "");
        const wk = escapeHtml(topnavStreamlitKey(it.cardId || ""));
        if (onPage) {
          navHtml += `<div class="lib-ai-nav-onpage" data-lib-topnav-id="${cid}"><p>${escapeHtml(onPagePrefix)}${escapeHtml(uiT(deps, it.title || ""))}</p></div>`;
        } else {
          navHtml += `<div class="st-key-${wk}" data-testid="stButton"><button type="button" data-testid="baseButton-primary" kind="primary" data-hash-target="${escapeHtml(it.target || "")}">${escapeHtml(uiT(deps, it.title || ""))}</button></div>`;
        }
      }
      navHtml += "</div>";
    }
    navHtml += "</div></div>";
    if (gi < groups.length - 1) {
      navHtml += '<div class="lib-topnav-after-group-spacer" aria-hidden="true"></div>';
    }
  }
  return `<section class="lib-top-nav-groups">${navHtml}</section><div class="hr" role="separator" aria-hidden="true"></div>`;
}

export function showLoading(host) {
  host.innerHTML =
    '<div class="ui-loading" role="status"><div class="ui-loading__spinner" aria-hidden="true"></div><p class="ui-loading__text">Loading…</p></div>';
}

export function showFetchError(host, title, err, timeoutMs) {
  const msg = String(err && err.message ? err.message : err);
  const hint = timeoutMs ? `<p class="ui-error__hint">Timeout: ${timeoutMs}ms</p>` : "";
  host.innerHTML =
    '<div class="ui-error">' +
    "<h1>" +
    escapeHtmlStatic(title) +
    "</h1><pre>" +
    escapeHtmlStatic(msg) +
    "</pre>" +
    hint +
    "</div>";
}

function escapeHtmlStatic(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function fetchWithTimeout(url, options, timeoutMs) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(url, { ...options, signal: ctrl.signal });
    return r;
  } finally {
    clearTimeout(id);
  }
}

export async function fetchUiJson(apiUrl, segment, lang, timeoutMs) {
  const ms = timeoutMs || DEFAULT_TIMEOUT_MS;
  const q = "?lang=" + encodeURIComponent(lang);
  const url = apiUrl("/api/ui/" + segment + q);
  const r = await fetchWithTimeout(url, { method: "GET", headers: { Accept: "application/json" } }, ms);
  if (!r.ok) throw new Error(url + " → " + r.status);
  return JSON.parse(await r.text());
}

function renderHero(sec, escapeHtml, liteBoldHtml, deps) {
  if (sectionLayout(sec) === UI_LAYOUT.STREAMLIT) {
    return renderHeroStreamlit(sec, escapeHtml, deps);
  }
  const m = sec.meta || {};
  const logo = m.logo;
  let logoHtml = "";
  if (logo && logo.src) {
    logoHtml =
      '<div class="ui-hero__logo"><img src="' +
      escapeHtml(logo.src) +
      '" alt="' +
      escapeHtml(uiT(deps, logo.alt || "")) +
      '" /></div>';
  }
  const ctas = (m.ctas || [])
    .map((c) => {
      const v = c.variant === "secondary" ? "ui-cta ui-cta--secondary" : "ui-cta ui-cta--primary";
      const tgt = c.target || "";
      const nav = c.navTarget || "";
      const dataAttr = tgt ? ' data-hash-target="' + escapeHtml(tgt) + '"' : ' data-nav-target="' + escapeHtml(nav) + '"';
      return (
        '<button type="button" class="' +
        v +
        '"' +
        dataAttr +
        ">" +
        escapeHtml(uiT(deps, c.label || "")) +
        "</button>"
      );
    })
    .join("");
  return (
    '<section class="ui-hero">' +
    logoHtml +
    '<div class="ui-hero__copy">' +
    '<p class="ui-hero__kicker">' +
    escapeHtml(uiT(deps, m.kicker || "")) +
    "</p>" +
    '<p class="ui-hero__micro" lang="en">' +
    escapeHtml(uiT(deps, m.micro_en || "")) +
    "</p>" +
    '<h1 class="ui-hero__headline">' +
    escapeHtml(uiT(deps, m.headline || "")) +
    "</h1>" +
    '<div class="ui-hero__sub">' +
    liteBoldHtml(uiT(deps, m.subcopy || "")) +
    "</div>" +
    '<p class="ui-hero__foot">' +
    escapeHtml(uiT(deps, m.footnote || "")) +
    "</p>" +
    '<div class="ui-hero__ctas">' +
    ctas +
    "</div></div></section>"
  );
}

function renderCards(sec, escapeHtml, liteBoldHtml, deps) {
  const layout = sectionLayout(sec);
  if (layout === UI_LAYOUT.STREAMLIT_NAV_MULTI) {
    return renderStreamlitNavMulti(sec, escapeHtml, deps);
  }
  const title = sec.title ? "<h2 class=\"ui-sec-title\">" + escapeHtml(uiT(deps, sec.title)) + "</h2>" : "";
  const lead = sec.text ? "<p class=\"ui-sec-lead\">" + liteBoldHtml(uiT(deps, sec.text)) + "</p>" : "";
  const kicker = sec.meta && sec.meta.kicker ? "<p class=\"ui-sec-kicker\">" + escapeHtml(uiT(deps, sec.meta.kicker)) + "</p>" : "";
  const items = sec.items || [];
  let body = "";
  if (layout === UI_LAYOUT.STREAMLIT_NAV) {
    const cols = Math.max(1, Math.min(5, Number((sec.meta && sec.meta.columns) || items.length || 1)));
    const rowClass = (sec.meta && sec.meta.rowClass) || "";
    body =
      '<div class="streamlit-card-grid streamlit-card-grid--' +
      cols +
      " " +
      escapeHtml(rowClass) +
      '">' +
      items
        .map(
          (it) =>
            '<article class="streamlit-card streamlit-nav-card" role="button" tabindex="0" data-hash-target="' +
            escapeHtml(it.target || "") +
            '"><h3 class="streamlit-card__title">' +
            escapeHtml(uiT(deps, it.title || "")) +
            "</h3>" +
            (it.text ? '<p class="streamlit-card__text">' + escapeHtml(uiT(deps, it.text)) + "</p>" : "") +
            "</article>",
        )
        .join("") +
      "</div>";
    return (
      '<section class="ui-sec ui-sec--cards streamlit-cards-sec">' +
      kicker +
      title +
      lead +
      body +
      '<div class="hr" role="separator" aria-hidden="true"></div></section>'
    );
  }
  if (layout === UI_LAYOUT.STREAMLIT_SERVICE) {
    body =
      '<div class="streamlit-card-grid streamlit-card-grid--service">' +
      items
        .map((it) => {
          const sub = it.subtitle ? '<span class="streamlit-card__badge">' + escapeHtml(uiT(deps, it.subtitle)) + "</span>" : "";
          return (
            '<article class="streamlit-card streamlit-service-card" role="button" tabindex="0" data-hash-target="' +
            escapeHtml(it.target || "") +
            '"><h3 class="streamlit-card__title">' +
            escapeHtml(uiT(deps, it.title || "")) +
            "</h3>" +
            sub +
            '<p class="streamlit-card__text">' +
            liteBoldHtml(uiT(deps, it.text || "")) +
            "</p></article>"
          );
        })
        .join("") +
      "</div>";
    return '<section class="ui-sec ui-sec--cards streamlit-service-sec">' + kicker + title + lead + body + "</section>";
  }
  if (layout === UI_LAYOUT.NAV) {
    body =
      '<div class="ui-card-grid ui-card-grid--nav">' +
      items
        .map(
          (it) =>
            '<article class="ui-card ui-card--nav" data-nav-target="' +
            escapeHtml(it.navTarget || "") +
            '"><h3>' +
            escapeHtml(uiT(deps, it.title || "")) +
            "</h3><p>" +
            escapeHtml(uiT(deps, it.text || "")) +
            "</p></article>",
        )
        .join("") +
      "</div>";
  } else {
    body =
      '<div class="ui-card-grid">' +
      items
        .map((it) => {
          const mh = it.meta && it.meta.body_html ? '<div class="ui-card__bodymd">' + it.meta.body_html + "</div>" : "";
          const sub = it.subtitle ? '<p class="ui-card__sub">' + escapeHtml(uiT(deps, it.subtitle)) + "</p>" : "";
          return (
            '<article class="ui-card"><h3>' +
            escapeHtml(uiT(deps, it.title || "")) +
            "</h3>" +
            sub +
            "<p>" +
            liteBoldHtml(uiT(deps, it.text || "")) +
            "</p>" +
            mh +
            "</article>"
          );
        })
        .join("") +
      "</div>";
  }
  return '<section class="ui-sec ui-sec--cards">' + kicker + title + lead + body + "</section>";
}

function renderTable(sec, escapeHtml, liteBoldHtml, deps) {
  const cols = (sec.meta && sec.meta.columns) || [
    { key: "title", label: "Title" },
    { key: "text", label: "Detail" },
  ];
  const items = sec.items || [];
  const head = "<tr>" + cols.map((c) => "<th>" + escapeHtml(uiT(deps, c.label)) + "</th>").join("") + "</tr>";
  const rows = items
    .map((it) => {
      return (
        "<tr>" +
        cols
          .map((c) => {
            const v = it[c.key] != null ? String(it[c.key]) : "";
            const tv = uiT(deps, v);
            return "<td>" + (c.key === "text" ? liteBoldHtml(tv) : escapeHtml(tv)) + "</td>";
          })
          .join("") +
        "</tr>"
      );
    })
    .join("");
  const title = sec.title ? "<h2 class=\"ui-sec-title\">" + escapeHtml(uiT(deps, sec.title)) + "</h2>" : "";
  const note = sec.text ? "<p class=\"ui-sec-lead\">" + liteBoldHtml(uiT(deps, sec.text)) + "</p>" : "";
  const wrapClass =
    sectionLayout(sec) === UI_LAYOUT.STREAMLIT_MARKET
      ? "ui-sec ui-sec--table streamlit-market-table"
      : "ui-sec ui-sec--table";
  return (
    '<section class="' +
    wrapClass +
    '">' +
    title +
    note +
    '<div class="ui-table-wrap"><table class="ui-table"><thead>' +
    head +
    "</thead><tbody>" +
    rows +
    "</tbody></table></div></section>"
  );
}

function renderChart(sec, escapeHtml, deps) {
  const m = sec.meta || {};
  const items = sec.items || [];
  const yk = m.yKey || "pv_million";
  const xk = m.xKey || "year";
  const maxY = Math.max(1, ...items.map((r) => Number(r[yk]) || 0));
  const bars = items
    .map((r) => {
      const h = Math.round(((Number(r[yk]) || 0) / maxY) * 100);
      return (
        '<div class="ui-chart__barwrap"><div class="ui-chart__bar" style="height:' +
        h +
        '%"></div><span class="ui-chart__x">' +
        escapeHtml(String(r[xk] ?? "")) +
        "</span></div>"
      );
    })
    .join("");
  const title = sec.title ? "<h2 class=\"ui-sec-title\">" + escapeHtml(uiT(deps, sec.title)) + "</h2>" : "";
  const cap = sec.text ? "<p class=\"ui-sec-lead\">" + escapeHtml(uiT(deps, sec.text)) + "</p>" : "";
  return '<section class="ui-sec ui-sec--chart">' + title + cap + '<div class="ui-chart">' + bars + "</div></section>";
}

function renderText(sec, escapeHtml, liteBoldHtml, deps) {
  const m = sec.meta || {};
  const id = m.id ? ' id="' + escapeHtml(m.id) + '"' : "";
  const title = sec.title ? "<h2 class=\"ui-sec-title\">" + escapeHtml(uiT(deps, sec.title)) + "</h2>" : "";
  const body = sec.text ? "<div class=\"ui-sec-md\"" + id + ">" + liteBoldHtml(uiT(deps, sec.text)) + "</div>" : "<div" + id + "></div>";
  return '<section class="ui-sec ui-sec--text">' + title + body + "</section>";
}

function fieldHtml(f, escapeHtml) {
  const nm = escapeHtml(f.name || "");
  const lab = escapeHtml(f.label || "");
  const ph = escapeHtml(f.placeholder || "");
  const typ = f.input || "text";
  if (typ === "hidden") {
    return '<input type="hidden" name="' + nm + '" value="' + escapeHtml(String(f.value ?? "")) + '" />';
  }
  if (typ === "textarea") {
    return (
      '<label class="ui-field"><span class="ui-field__l">' +
      lab +
      '</span><textarea name="' +
      nm +
      '" placeholder="' +
      ph +
      '">' +
      escapeHtml(String(f.value ?? "")) +
      "</textarea></label>"
    );
  }
  if (typ === "checkbox") {
    const ch = f.value ? " checked" : "";
    return (
      '<label class="ui-field ui-field--inline"><input type="checkbox" name="' +
      nm +
      '"' +
      ch +
      ' /><span>' +
      lab +
      "</span></label>"
    );
  }
  if (typ === "select") {
    const opts = (f.options || [])
      .map((o) => {
        const sel = String(o) === String(f.value) ? " selected" : "";
        return "<option" + sel + ">" + escapeHtml(String(o)) + "</option>";
      })
      .join("");
    return '<label class="ui-field"><span class="ui-field__l">' + lab + '</span><select name="' + nm + '">' + opts + "</select></label>";
  }
  const step = f.step ? ' step="' + escapeHtml(f.step) + '"' : "";
  return (
    '<label class="ui-field"><span class="ui-field__l">' +
    lab +
    '</span><input type="' +
    escapeHtml(typ) +
    '" name="' +
    nm +
    '" value="' +
    escapeHtml(String(f.value ?? "")) +
    '"' +
    step +
    ' placeholder="' +
    ph +
    '" /></label>'
  );
}

function renderForm(sec, escapeHtml, deps) {
  const m = sec.meta || {};
  const fields = (sec.items || []).map((f) => fieldHtml(f, escapeHtml)).join("");
  const title = sec.title ? "<h2 class=\"ui-sec-title\">" + escapeHtml(uiT(deps, sec.title)) + "</h2>" : "";
  const intro = sec.text ? "<p class=\"ui-sec-lead\">" + deps.liteBoldHtml(uiT(deps, sec.text)) + "</p>" : "";
  let buttons = "";
  if (m.renderer === "mekiki" && Array.isArray(m.buttons)) {
    buttons = m.buttons
      .map((b) => {
        const primary = b.id === "run" ? " ui-cta--primary" : " ui-cta--secondary";
        return (
          '<button type="button" class="ui-cta' +
          primary +
          '" data-mekiki-act="' +
          escapeHtml(b.id) +
          '">' +
          escapeHtml(uiT(deps, b.label)) +
          "</button>"
        );
      })
      .join("");
  } else if (m.action === "dcf-recalc") {
    buttons =
      '<button type="button" class="ui-cta ui-cta--primary" data-dcf-recalc="1">' + escapeHtml(uiT(deps, m.submitLabel || "OK")) + "</button>";
  } else if (m.action === "mailto") {
    buttons =
      '<button type="button" class="ui-cta ui-cta--primary" data-mailto-send="1">' + escapeHtml(uiT(deps, m.submitLabel || "OK")) + "</button>";
  }
  return (
    '<section class="ui-sec ui-sec--form" data-ui-form="' +
    escapeHtml(m.renderer || m.action || "generic") +
    '">' +
    title +
    intro +
    '<form class="ui-form" onsubmit="return false">' +
    fields +
    '<div class="ui-form__actions">' +
    buttons +
    "</div></form></section>"
  );
}

export function renderUIPage(host, data, deps) {
  const { escapeHtml, liteBoldHtml } = deps;
  const title = uiT(deps, data.title || "");
  const sections = data.sections || [];
  const meta = data.meta || {};
  const streamlitTop = !!meta.streamlitTop;
  const hidePageTitle = !!meta.hidePageTitle;
  const sectionParts = [];
  const trendMetas = [];
  let navCssPayload = null;
  for (const sec of sections) {
    const t = sec.type;
    if (t === "hero") sectionParts.push(renderHero(sec, escapeHtml, liteBoldHtml, deps));
    else if (t === "cards") {
      if (sectionLayout(sec) === UI_LAYOUT.STREAMLIT_NAV_MULTI && sec.meta && sec.meta.navCssPayload) {
        navCssPayload = sec.meta.navCssPayload;
      }
      sectionParts.push(renderCards(sec, escapeHtml, liteBoldHtml, deps));
    } else if (t === "table") sectionParts.push(renderTable(sec, escapeHtml, liteBoldHtml, deps));
    else if (t === "chart") sectionParts.push(renderChart(sec, escapeHtml, deps));
    else if (t === "text") sectionParts.push(renderText(sec, escapeHtml, liteBoldHtml, deps));
    else if (t === "form") sectionParts.push(renderForm(sec, escapeHtml, deps));
    else if (t === "markup") sectionParts.push(renderMarkup(sec, escapeHtml));
    else if (t === "trends") {
      sectionParts.push(renderTrends(sec, escapeHtml, liteBoldHtml, deps));
      trendMetas.push(sec.meta || {});
    } else sectionParts.push("<section class=\"ui-sec\"><p>" + escapeHtml("Unknown section: " + t) + "</p></section>");
  }
  if (streamlitTop) {
    host.innerHTML = '<div class="lib-top-page-inner">' + sectionParts.join("") + "</div>";
  } else {
    const head =
      hidePageTitle || !title
        ? ""
        : '<header class="ui-page__head"><h1 class="page-title">' + escapeHtml(title) + "</h1></header>";
    host.innerHTML = '<div class="ui-page">' + head + sectionParts.join("") + "</div>";
  }
  if (streamlitTop && navCssPayload && deps.apiUrl) {
    try {
      injectTopNavCardCss(deps.apiUrl, navCssPayload);
    } catch (e) {
      console.error(e);
    }
  }
  for (const tm of trendMetas) {
    wireTrendSection(host, deps, tm);
  }
  wireUiInteractions(host, deps);
}

function wireUiInteractions(host, deps) {
  const { apiUrl, lang, escapeHtml } = deps;
  host.querySelectorAll("[data-hash-target]").forEach((el) => {
    el.addEventListener("click", () => {
      const h = el.getAttribute("data-hash-target");
      if (h) {
        const norm = h.startsWith("#") ? h : "#" + h;
        if (location.hash !== norm) location.hash = norm;
      }
    });
    el.addEventListener("keydown", (ev) => {
      const tag = (el.tagName || "").toUpperCase();
      if (tag === "BUTTON" || tag === "A") return;
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        el.click();
      }
    });
  });
  host.querySelectorAll("[data-nav-target]").forEach((el) => {
    el.addEventListener("click", () => {
      const p = el.getAttribute("data-nav-target");
      if (p) R.setHashPage(p);
    });
  });
  host.querySelectorAll(".ui-card--nav").forEach((card) => {
    card.addEventListener("click", () => {
      const p = card.getAttribute("data-nav-target");
      if (p) R.setHashPage(p);
    });
  });
  host.querySelectorAll("[data-mekiki-act]").forEach((btn) => {
    btn.addEventListener("click", () => void handleMekikiAct(btn.getAttribute("data-mekiki-act"), host, deps));
  });
  host.querySelectorAll("[data-dcf-recalc]").forEach((btn) => {
    btn.addEventListener("click", () => void handleDcfRecalc(host, deps));
  });
  host.querySelectorAll("[data-mailto-send]").forEach((btn) => {
    btn.addEventListener("click", () => handleMailto(host, deps));
  });
}

async function handleMekikiAct(act, host, deps) {
  const form = host.querySelector('section[data-ui-form="mekiki"] form') || host.querySelector(".ui-form");
  if (!form) return;
  const raw = (form.querySelector('[name="raw_listing"]') || {}).value || "";
  const L = deps.lang();
  if (act === "parse") {
    try {
      const r = await fetchWithTimeout(
        deps.apiUrl("/parse_listing"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ raw_listing: raw, lang: L }),
        },
        DEFAULT_TIMEOUT_MS,
      );
      const data = await r.json();
      const p = data.parsed || {};
      const set = (n, v) => {
        const el = form.querySelector('[name="' + n + '"]');
        if (el && v != null && v !== "") el.value = v;
      };
      set("price_myen", p.price_myen);
      set("area_sqm", p.area_sqm);
      set("walk_min", p.walk_min);
      const bc = form.querySelector('[name="building_condition"]');
      if (bc) bc.checked = !!p.building_condition;
      set("address", p.address);
    } catch (e) {
      console.error(e);
      alert(String(e.message || e));
    }
    return;
  }
  if (act !== "run") return;

  const body = {
    lang: ((form.querySelector('[name="lang"]') || {}).value || L),
    raw_listing: raw,
    price_myen: Number((form.querySelector('[name="price_myen"]') || {}).value || 0),
    area_sqm: Number((form.querySelector('[name="area_sqm"]') || {}).value || 0),
    walk_min: Number((form.querySelector('[name="walk_min"]') || {}).value || 0),
    building_condition: !!(form.querySelector('[name="building_condition"]') || {}).checked,
    address: (form.querySelector('[name="address"]') || {}).value || "",
    region: (form.querySelector('[name="region"]') || {}).value || "全国（暫定）",
    road_width_m: Number((form.querySelector('[name="road_width_m"]') || {}).value || 0),
    shape_risk: (form.querySelector('[name="shape_risk"]') || {}).value || "不明",
    comps_raw: (form.querySelector('[name="comps_raw"]') || {}).value || "",
  };
  const out = host.querySelector("#mekiki-result-host");
  if (out) out.innerHTML = "<p>…</p>";
  try {
    const r = await fetchWithTimeout(
      deps.apiUrl("/api/price"),
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) },
      DEFAULT_TIMEOUT_MS,
    );
    const res = await r.json();
    if (res.error) {
      if (out) out.innerHTML = "<pre class=\"ui-mekiki-err\">" + escapeHtml(res.error) + "</pre>";
      return;
    }
    let html = "";
    if (res.summary_text) html += "<div class=\"lib-page-md\">" + deps.liteBoldHtml(res.summary_text) + "</div>";
    if (res.detail_lines && res.detail_lines.length) {
      html += "<h3>Detail</h3><ul>";
      for (const line of res.detail_lines) html += "<li>" + deps.liteBoldHtml(line) + "</li>";
      html += "</ul>";
    }
    if (res.table_text) html += "<pre class=\"ui-mekiki-table\">" + escapeHtml(res.table_text) + "</pre>";
    if (res.disclaimer_markdown) html += "<div class=\"lib-page-md\">" + deps.liteBoldHtml(res.disclaimer_markdown) + "</div>";
    if (out) out.innerHTML = html || "<p>(no output)</p>";
  } catch (e) {
    console.error(e);
    if (out) out.innerHTML = "<pre class=\"ui-mekiki-err\">" + escapeHtml(String(e.message || e)) + "</pre>";
  }
}

async function handleDcfRecalc(host, deps) {
  const form = host.querySelector('section[data-ui-form="dcf-recalc"] form') || host.querySelector(".ui-sec--form .ui-form");
  if (!form) return;
  const q = new URLSearchParams();
  q.set("lang", deps.lang());
  q.set("noi_million", String((form.querySelector('[name="noi_million"]') || {}).value || "10"));
  q.set("growth_pct", String((form.querySelector('[name="growth_pct"]') || {}).value || "1"));
  q.set("discount_pct", String((form.querySelector('[name="discount_pct"]') || {}).value || "6"));
  q.set("horizon_years", String((form.querySelector('[name="horizon_years"]') || {}).value || "10"));
  try {
    const u = deps.apiUrl("/api/ui/dcf?" + q.toString());
    const r = await fetchWithTimeout(u, { method: "GET" }, DEFAULT_TIMEOUT_MS);
    const page = await r.json();
    renderUIPage(host, page, deps);
  } catch (e) {
    console.error(e);
    alert(String(e.message || e));
  }
}

function handleMailto(host, deps) {
  const form = host.querySelector(".ui-sec--form .ui-form");
  if (!form) return;
  const purpose = (form.querySelector('[name="purpose"]') || {}).value || "";
  const body = (form.querySelector('[name="body"]') || {}).value || "";
  const root = host.querySelector(".ui-page");
  const em = (root && root.getAttribute("data-office-email")) || "";
  if (!em) {
    alert(deps.T("contact_info_secrets_setup"));
    return;
  }
  const subj = encodeURIComponent("[Contact] " + purpose);
  const b = encodeURIComponent(body);
  window.location.href = "mailto:" + em + "?subject=" + subj + "&body=" + b;
}


export function patchOfficeEmail(host, email) {
  const r = host.querySelector(".ui-page");
  if (r && email) r.setAttribute("data-office-email", email);
}

