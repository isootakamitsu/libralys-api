export const LANG_KEY = "lang";
export const NAV_PAGE_ROUTER_KEY = "_lib_nav_route";
export const NAV_PENDING_KEY = "_lib_nav_pending";
export const PAGE_HISTORY_STACK_KEY = "_lib_page_stack";
export const PAGE_HISTORY_LAST_KEY = "_lib_last_committed_page";
export const MAX_PAGE_HISTORY = 24;

export const PAGES = [
  "TOP",
  "はじめての方へ",
  "業務内容",
  "業務の流れ",
  "AI分析ツール",
  "AI評価研究グループ",
  "価格の目利き",
  "市場分析",
  "DCFシミュレータ",
  "不動産鑑定士マッチング",
  "実績・ケーススタディ",
  "会社概要",
  "代表プロフィール",
  "AI思想（Methodology）",
  "企業統治（Governance）",
  "情報セキュリティ（ISMS相当）",
  "倫理規程・不動産鑑定士職業倫理",
  "プライバシー",
  "お問い合わせ",
];

const _PAGE_SET = new Set(PAGES);

/** 英語スラッグ → 内部ページ */
const HASH_SLUG_TO_PAGE = {
  top: "TOP",
  services: "業務内容",
  mekiki: "価格の目利き",
  market: "市場分析",
  dcf: "DCFシミュレータ",
};

/** ページ → スラッグ */
const PAGE_TO_HASH_SLUG = {
  "TOP": "top",
  "業務内容": "services",
  "価格の目利き": "mekiki",
  "市場分析": "market",
  "DCFシミュレータ": "dcf",
};

export function isValidPage(page) {
  return _PAGE_SET.has(page);
}

export function getHashHref(page) {
  if (!isValidPage(page)) return "#/top";
  const seg = PAGE_TO_HASH_SLUG[page] ?? encodeURIComponent(page);
  return "#/" + seg;
}

export function getHashPage() {
  const raw = (location.hash || "").replace(/^#\/?/, "").trim();
  if (!raw) return "TOP";

  let decoded;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    decoded = raw;
  }

  const bySlug = HASH_SLUG_TO_PAGE[String(decoded).toLowerCase()];
  if (bySlug) return bySlug;

  return isValidPage(decoded) ? decoded : "TOP";
}

export function setHashPage(page) {
  if (!isValidPage(page)) return;
  const seg = PAGE_TO_HASH_SLUG[page] ?? encodeURIComponent(page);
  const h = "#/" + seg;
  if (location.hash !== h) location.hash = h;
}

export function readSession(key, fallback = null) {
  try {
    const v = sessionStorage.getItem(key);
    return v === null || v === "" ? fallback : v;
  } catch {
    return fallback;
  }
}

export function writeSession(key, value) {
  try {
    if (value === null || value === undefined) sessionStorage.removeItem(key);
    else sessionStorage.setItem(key, String(value));
  } catch {}
}

export function readJsonSession(key, fallback) {
  try {
    const v = sessionStorage.getItem(key);
    if (!v) return fallback;
    return JSON.parse(v);
  } catch {
    return fallback;
  }
}

export function writeJsonSession(key, obj) {
  try {
    sessionStorage.setItem(key, JSON.stringify(obj));
  } catch {}
}

export function pushPageHistory(currentPage) {
  if (!isValidPage(currentPage)) return;

  const last = readSession(PAGE_HISTORY_LAST_KEY, null);

  if (last === null) {
    writeSession(PAGE_HISTORY_LAST_KEY, currentPage);
    return;
  }

  if (last === currentPage) return;

  const stack = readJsonSession(PAGE_HISTORY_STACK_KEY, []);
  stack.push(last);

  while (stack.length > MAX_PAGE_HISTORY) stack.shift();

  writeJsonSession(PAGE_HISTORY_STACK_KEY, stack);
  writeSession(PAGE_HISTORY_LAST_KEY, currentPage);
}

export function popPageHistory() {
  const stack = readJsonSession(PAGE_HISTORY_STACK_KEY, []);
  return stack.length ? stack.pop() : "TOP";
}

export function applyPendingNav() {
  const pending = readSession(NAV_PENDING_KEY, null);

  if (pending && isValidPage(pending)) {
    writeSession(NAV_PENDING_KEY, "");
    setHashPage(pending);
    return pending;
  }

  return null;
}
