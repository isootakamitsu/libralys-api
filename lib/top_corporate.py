# -*- coding: utf-8 -*-
"""
TOP をコーポレートサイト型に近づけるブロック（お知らせ・フッター導線）。
谷澤総合鑑定所トップの「NEWS 帯＋階層的導線＋フッター近接リンク」イメージを Streamlit で再現。

【統合】
- NAV_PENDING_KEY / PAGES / BASE_DIR は app.py から渡す。
- ニュースは data/top_news.json（無ければプレースホルダ1件）。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import streamlit as st

# 谷澤総合鑑定所型：企業情報 / 事業案内 / ツール・実績 / お問い合わせ の横並び導線（ボタン＋ session、フルリロードなし）
TOP_GLOBAL_NAV_SPEC: Tuple[Tuple[str, str, str], ...] = (
    ("会社概要", "ABOUT", "会社概要"),
    ("業務内容", "SERVICES", "業務内容"),
    ("実績・ケーススタディ", "WORKS", "実績・ケーススタディ"),
    ("AI分析ツール", "TOOLS", "AI分析ツール"),
    ("お問い合わせ", "CONTACT", "お問い合わせ"),
)


def _html(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def inject_top_corporate_home_css() -> None:
    if st.session_state.get("_lib_inject_corp_css"):
        return
    st.session_state["_lib_inject_corp_css"] = True
    st.markdown(
        """
<style>
/* 谷澤型：全幅の薄いグローバル帯（横ナビの代替・サイドバーと二重にならず補完） */
.lib-corp-topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  justify-content: center;
  gap: 0;
  margin: 0 0 0.85rem 0;
  padding: 0;
  background: #ffffff;
  border: 1px solid rgba(15, 28, 46, 0.12);
  border-radius: 12px;
  box-shadow: 0 8px 28px rgba(15, 28, 46, 0.05);
  overflow: hidden;
}
.lib-corp-topbar-item {
  flex: 1 1 0;
  min-width: 118px;
  max-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  padding: 0.65rem 0.5rem;
  text-decoration: none !important;
  color: #0f1c2e !important;
  border-right: 1px solid rgba(15, 28, 46, 0.08);
  transition: background 0.15s ease, color 0.15s ease;
}
.lib-corp-topbar-item:last-child { border-right: none; }
.lib-corp-topbar-item:hover {
  background: rgba(201, 162, 77, 0.1);
  color: #0f1c2e !important;
}
.lib-corp-topbar-item:focus-visible {
  outline: 2px solid #c9a24d;
  outline-offset: -2px;
  z-index: 1;
}
.lib-corp-topbar-current {
  flex: 1 1 0;
  min-width: 118px;
  max-width: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.15rem;
  padding: 0.65rem 0.5rem;
  background: linear-gradient(180deg, rgba(201, 162, 77, 0.16) 0%, rgba(201, 162, 77, 0.06) 100%);
  border-right: 1px solid rgba(15, 28, 46, 0.08);
  cursor: default;
}
.lib-corp-topbar-current:last-child { border-right: none; }
.lib-corp-topbar-en {
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.22em;
  color: #64748b;
  text-transform: uppercase;
}
.lib-corp-topbar-jp {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #0f1c2e;
}
.lib-corp-topbar-current .lib-corp-topbar-en { color: #0f1c2e; }
@media (max-width: 720px) {
  .lib-corp-topbar-item, .lib-corp-topbar-current {
    flex: 1 1 45%;
    max-width: none;
    border-right: 1px solid rgba(15, 28, 46, 0.08);
    border-bottom: 1px solid rgba(15, 28, 46, 0.06);
  }
}
/* コーポレート本文見出し（英字キッカー＋金線） */
.lib-corp-sec {
  margin: 0.5rem 0 1rem 0;
  padding: 0 0 0.25rem 0;
}
.lib-corp-sec-en {
  margin: 0 0 0.2rem 0;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.24em;
  color: #94a3b8;
  text-transform: uppercase;
}
.lib-corp-sec-jp {
  margin: 0 0 0.45rem 0;
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: #0f1c2e !important;
  line-height: 1.25;
}
.lib-corp-sec-line {
  width: 56px;
  height: 3px;
  background: #c9a24d;
  border-radius: 2px;
  margin-bottom: 0.35rem;
}
.lib-corp-sec-sub {
  margin: 0;
  font-size: 0.92rem;
  color: #64748b;
  line-height: 1.55;
}
/* 3カラム「事業の柱」カード */
.lib-corp-pillar-card {
  border-left: 4px solid #c9a24d !important;
  border-radius: 12px !important;
}
.lib-corp-news-wrap {
  border: 1px solid rgba(15, 28, 46, 0.12);
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 12px 36px rgba(15, 28, 46, 0.06);
  padding: 1.1rem 1.25rem 1rem 1.25rem;
  margin: 0 0 0.25rem 0;
}
.lib-corp-news-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.65rem 1rem;
  margin-bottom: 0.65rem;
  border-bottom: 1px solid rgba(15, 28, 46, 0.1);
  padding-bottom: 0.55rem;
}
.lib-corp-news-head-main { flex: 1 1 200px; min-width: 0; }
.lib-corp-news-h {
  margin: 0 0 0.2rem 0;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.2em;
  color: #64748b;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
.lib-corp-news-h-bar {
  display: inline-block;
  width: 4px;
  height: 1.05em;
  background: #c9a24d;
  border-radius: 1px;
  flex-shrink: 0;
}
.lib-corp-news-sub {
  margin: 0;
  font-size: 0.8rem;
  color: #94a3b8;
}
.lib-corp-news-rail {
  margin: 0;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: #cbd5e1;
  text-transform: uppercase;
  text-align: right;
  align-self: center;
}
.lib-corp-news-row {
  display: grid;
  grid-template-columns: 92px 88px 1fr;
  gap: 0.65rem 0.85rem;
  align-items: baseline;
  padding: 0.45rem 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  font-size: 0.92rem;
  line-height: 1.5;
}
.lib-corp-news-row:last-child { border-bottom: none; }
.lib-corp-news-date { color: #0f1c2e; font-weight: 700; font-variant-numeric: tabular-nums; }
.lib-corp-news-cat {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #0f1c2e;
  background: rgba(201, 162, 77, 0.18);
  border: 1px solid rgba(201, 162, 77, 0.35);
  border-radius: 999px;
  padding: 0.12rem 0.45rem;
  text-align: center;
}
.lib-corp-news-title { color: #1e293b; margin: 0; }
@media (max-width: 640px) {
  .lib-corp-news-row {
    grid-template-columns: 1fr;
    gap: 0.2rem;
  }
}
.lib-corp-footer-h {
  margin: 1.5rem 0 0.55rem 0;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  color: #64748b;
  text-transform: uppercase;
}
.lib-corp-footer-note {
  margin: 0.5rem 0 0 0;
  font-size: 0.78rem;
  color: #94a3b8;
  text-align: center;
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_top_global_nav_strip(
    *,
    valid_pages: Sequence[str],
    current_page: str,
    pending_nav_key: str,
) -> None:
    """谷澤型の横並び主要導線（Streamlit ボタンで遷移。?nav= リンクは使わない）。"""
    items: List[Tuple[str, str, str]] = [
        (jp, en, tgt)
        for jp, en, tgt in TOP_GLOBAL_NAV_SPEC
        if tgt in valid_pages
    ]
    if not items:
        return
    cols = st.columns(len(items), gap="small")
    for i, (jp, en, tgt) in enumerate(items):
        with cols[i]:
            here = current_page == tgt
            if st.button(
                jp,
                key=f"corp_topnav_{i}",
                width="stretch",
                disabled=here,
                type="secondary",
                help=en,
            ):
                st.session_state[pending_nav_key] = tgt
                st.rerun()


def render_corporate_section_title(
    *,
    title_jp: str,
    title_en: str,
    subtitle: Optional[str] = None,
) -> None:
    """本文ブロック用：英字ラベル＋和文見出し＋金線（コーポレートサイトのセクションリズム）。"""
    sub_html = (
        f'<p class="lib-corp-sec-sub">{_html(subtitle)}</p>' if subtitle else ""
    )
    en_html = (
        f'<p class="lib-corp-sec-en">{_html(title_en)}</p>'
        if (title_en or "").strip()
        else ""
    )
    st.markdown(
        f"""
<div class="lib-corp-sec">
  {en_html}
  <h3 class="lib-corp-sec-jp">{_html(title_jp)}</h3>
  <div class="lib-corp-sec-line" aria-hidden="true"></div>
  {sub_html}
</div>
""",
        unsafe_allow_html=True,
    )


_NEWS_FALLBACK: List[Dict[str, Any]] = [
    {
        "date": "—",
        "category": "お知らせ",
        "title": "data/top_news.json に記事を追加すると、ここに最新情報が表示されます。",
        "body": "",
    }
]

_NEWS_FALLBACK_EN: List[Dict[str, Any]] = [
    {
        "date": "—",
        "category": "Notice",
        "title": "Add items to `data/top_news.json` to display updates here.",
        "body": "",
    }
]


def _news_fallback_for_lang(lang: str, max_items: int) -> List[Dict[str, Any]]:
    fb = _NEWS_FALLBACK_EN if lang == "en" else _NEWS_FALLBACK
    return list(fb[:max_items])


def _normalize_news_item(item: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """`title_en` / `body_en` / `category_en` があれば英語 UI で優先する。"""
    body_val = item.get("body", "")
    if body_val is None:
        body_s = ""
    elif isinstance(body_val, str):
        body_s = body_val.strip()
    else:
        body_s = str(body_val).strip()
    body_en_val = item.get("body_en", "")
    if body_en_val is None:
        body_en_s = ""
    elif isinstance(body_en_val, str):
        body_en_s = body_en_val.strip()
    else:
        body_en_s = str(body_en_val).strip()
    try:
        importance = int(item.get("importance", 0) or 0)
    except (TypeError, ValueError):
        importance = 0
    link_raw = item.get("url") or item.get("link")
    link_s = str(link_raw).strip() if link_raw is not None else ""
    if lang == "en":
        return {
            "date": str(item.get("date", "—")),
            "category": str(item.get("category_en") or item.get("category", "Notice")),
            "title": str(item.get("title_en") or item.get("title", "")),
            "body": body_en_s or body_s,
            "importance": importance,
            "link": link_s,
        }
    return {
        "date": str(item.get("date", "—")),
        "category": str(item.get("category", "お知らせ")),
        "title": str(item.get("title", "")),
        "body": body_s,
        "importance": importance,
        "link": link_s,
    }


@st.cache_data(show_spinner=False)
def _load_top_news_from_disk(
    path_resolved: str, mtime_ns: int, max_items: int, lang: str
) -> List[Dict[str, Any]]:
    path = Path(path_resolved)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return _news_fallback_for_lang(lang, max_items)
    if not isinstance(data, list) or not data:
        return _news_fallback_for_lang(lang, max_items)
    out: List[Dict[str, Any]] = []
    for item in data[:max_items]:
        if not isinstance(item, dict):
            continue
        out.append(_normalize_news_item(item, lang))
    return out if out else _news_fallback_for_lang(lang, max_items)


def _load_top_news_entries(
    base_dir: Path, max_items: int = 5, lang: str = "ja"
) -> List[Dict[str, Any]]:
    path = base_dir / "data" / "top_news.json"
    if not path.is_file():
        return _news_fallback_for_lang(lang, max_items)
    try:
        mt = path.stat().st_mtime_ns
    except OSError:
        return _news_fallback_for_lang(lang, max_items)
    return _load_top_news_from_disk(str(path.resolve()), mt, max_items, lang)


@st.cache_data(show_spinner=False)
def _load_top_news_from_disk_full(
    path_resolved: str, mtime_ns: int, lang: str, load_cap: int
) -> List[Dict[str, Any]]:
    """JSON から最大 load_cap 件まで読み、正規化のみ（ソートは呼び出し側）。"""
    path = Path(path_resolved)
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return _news_fallback_for_lang(lang, min(load_cap, 5))
    if not isinstance(data, list) or not data:
        return _news_fallback_for_lang(lang, min(load_cap, 5))
    out: List[Dict[str, Any]] = []
    cap = max(1, int(load_cap))
    for item in data[:cap]:
        if not isinstance(item, dict):
            continue
        out.append(_normalize_news_item(item, lang))
    return out if out else _news_fallback_for_lang(lang, min(cap, 5))


def load_top_news_sorted(
    base_dir: Path,
    *,
    lang: str = "ja",
    load_cap: int = 80,
) -> List[Dict[str, Any]]:
    """
    `data/top_news.json` を日付（新しい順）＋任意の importance で安定ソートして返す。
    注目枠・通常・アーカイブ分割は UI 側で行う。
    """
    path = base_dir / "data" / "top_news.json"
    if not path.is_file():
        return _news_fallback_for_lang(lang, 5)
    try:
        mt = path.stat().st_mtime_ns
    except OSError:
        return _news_fallback_for_lang(lang, 5)
    items = _load_top_news_from_disk_full(str(path.resolve()), mt, lang, load_cap)

    def _parse_d(s: str) -> date:
        t = (s or "").strip().replace("/", ".").replace("-", ".")
        parts = [p for p in t.split(".") if p]
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                return date(y, m, d)
            except ValueError:
                return date.min
        return date.min

    def _sort_key(e: Dict[str, Any]) -> tuple:
        imp = int(e.get("importance", 0) or 0)
        d_ord = _parse_d(str(e.get("date", ""))).toordinal()
        title = str(e.get("title", ""))
        return (imp, d_ord, title)

    return sorted(items, key=_sort_key, reverse=True)


def render_top_news_section(
    *,
    base_dir: Path,
    max_items: int = 5,
    section_title: str = "最新のお知らせ",
    hint: str = "",
) -> None:
    entries = _load_top_news_entries(base_dir, max_items=max_items)
    rows_html = []
    for e in entries:
        d = (
            str(e.get("date", "—"))
            .replace("&", "&amp;")
            .replace("<", "&lt;")
        )
        c = (
            str(e.get("category", ""))
            .replace("&", "&amp;")
            .replace("<", "&lt;")
        )
        t = (
            str(e.get("title", ""))
            .replace("&", "&amp;")
            .replace("<", "&lt;")
        )
        rows_html.append(
            f'<div class="lib-corp-news-row">'
            f'<span class="lib-corp-news-date">{d}</span>'
            f'<span><span class="lib-corp-news-cat">{c}</span></span>'
            f'<p class="lib-corp-news-title">{t}</p></div>'
        )

    st.markdown(
        f"""
<div class="lib-corp-news-wrap" id="lib-corp-news">
  <div class="lib-corp-news-head">
    <div class="lib-corp-news-head-main">
      <p class="lib-corp-news-h"><span class="lib-corp-news-h-bar" aria-hidden="true"></span>NEWS</p>
      <p class="lib-corp-news-sub">{_html(section_title)}</p>
    </div>
    <p class="lib-corp-news-rail">Updates</p>
  </div>
  {''.join(rows_html)}
</div>
{f'<p style="margin:0.35rem 0 0 0;font-size:0.78rem;color:#94a3b8;">{_html(hint)}</p>' if hint.strip() else ''}
""",
        unsafe_allow_html=True,
    )


def render_top_footer_strip(
    *,
    pending_nav_key: str,
    valid_pages: Sequence[str],
    current_page: str,
) -> None:
    """フッター風の短い導線（コーポレートサイトの必須リンク帯に相当）。"""
    links: List[tuple[str, str, str]] = [
        ("corp_ft_top", "TOP", "TOP"),
        ("corp_ft_company", "会社概要", "会社概要"),
        ("corp_ft_privacy", "プライバシー", "プライバシー"),
        ("corp_ft_contact", "お問い合わせ", "お問い合わせ"),
    ]
    st.markdown(
        '<p class="lib-corp-footer-h">QUICK LINKS</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(links), gap="small")
    for i, (bid, label, target) in enumerate(links):
        with cols[i]:
            if target not in valid_pages:
                st.caption("—")
                continue
            dis = current_page == target
            if st.button(
                label,
                key=bid,
                width="stretch",
                type="secondary",
                disabled=dis,
            ):
                st.session_state[pending_nav_key] = target
                st.rerun()
    st.markdown(
        '<p class="lib-corp-footer-note">'
        "主要ポリシー・お問い合わせへのショートカット（全ページは左サイドバーから）"
        "</p>",
        unsafe_allow_html=True,
    )
