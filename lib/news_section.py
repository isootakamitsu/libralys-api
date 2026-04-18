# -*- coding: utf-8 -*-
"""
TOP の NEWS ブロック：注目1件（常時表示）＋通常一覧（expander・初期閉）＋アーカイブ（月別・初期閉）。
不動産トレンド情報のカードトーン（角丸・軽い影）に寄せ、CSS は .lib-news-* にスコープする。
データは `data/top_news.json`（`lib.top_corporate.load_top_news_sorted`）。
"""

from __future__ import annotations

import html
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import markdown
import streamlit as st

from lib.top_corporate import _html, load_top_news_sorted

_NEWS_CARD_CSS_KEY = "_lib_news_card_css_injected_v1"

_NEWS_CARD_CSS = """
<style>
/* NEWS カード（トレンド .lib-trend-card とトーン統一・他ページへ汎用展開しない） */
.lib-news-stack { display: flex; flex-direction: column; gap: 1rem; margin: 0.25rem 0 0.5rem 0; }
.lib-news-card {
  border: 1px solid rgba(15, 28, 46, 0.12);
  border-radius: 12px;
  padding: 1.05rem 1.12rem;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
  box-sizing: border-box;
  width: 100%;
}
.lib-news-card--featured {
  border-color: rgba(201, 162, 77, 0.45);
  background: linear-gradient(165deg, #faf8f5 0%, #ffffff 42%, #fafbfc 100%);
  box-shadow: 0 6px 22px rgba(15, 23, 42, 0.08);
  padding: 1.15rem 1.2rem;
}
.lib-news-card-meta {
  font-size: 0.78rem;
  color: #64748b;
  margin: 0 0 0.45rem 0;
  line-height: 1.5;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.65rem;
  align-items: center;
}
.lib-news-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.45;
  margin: 0 0 0.65rem 0;
  color: #0f1c2e;
}
.lib-news-tag {
  display: inline-block;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  color: #fff;
  text-transform: uppercase;
}
.lib-news-tag-report { background: linear-gradient(135deg, #dc2626, #991b1b); }
.lib-news-tag-release { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
.lib-news-tag-site { background: linear-gradient(135deg, #0d9488, #0f766e); }
.lib-news-tag-notice { background: linear-gradient(135deg, #d97706, #b45309); }
.lib-news-tag-media { background: linear-gradient(135deg, #7c3aed, #5b21b6); }
.lib-news-tag-event { background: linear-gradient(135deg, #e11d48, #be123c); }
.lib-news-tag-governance { background: linear-gradient(135deg, #475569, #334155); }
.lib-news-tag-muted { background: linear-gradient(135deg, #64748b, #475569); }
.lib-news-card-body {
  font-size: 0.9rem;
  line-height: 1.72;
  color: #334155;
  margin: 0;
}
.lib-news-card-body p { margin: 0 0 0.55rem 0; }
.lib-news-card-body p:last-child { margin-bottom: 0; }
.lib-news-card-body ul, .lib-news-card-body ol { margin: 0.35rem 0 0.55rem 1.1rem; padding: 0; }
.lib-news-detail-logo { margin: 0 0 0.75rem 0; }
.lib-news-detail-logo img { max-height: 52px; width: auto; max-width: 100%; display: block; object-fit: contain; }
.lib-news-archive-month {
  font-size: 0.85rem;
  font-weight: 700;
  color: #475569;
  margin: 0.85rem 0 0.4rem 0;
}
@media (max-width: 768px) {
  .lib-news-card { padding: 0.95rem 1rem; }
  .lib-news-card--featured { padding: 1rem 1.05rem; }
}
</style>
"""


def _inject_news_card_css_once() -> None:
    if st.session_state.get(_NEWS_CARD_CSS_KEY):
        return
    st.session_state[_NEWS_CARD_CSS_KEY] = True
    st.markdown(_NEWS_CARD_CSS, unsafe_allow_html=True)


def _news_tag_class(category: str) -> Tuple[str, str]:
    c = (category or "").strip().lower()
    raw = (category or "").strip()
    if "report" in c or c in ("事例", "レポート"):
        return ("REPORT", "lib-news-tag-report")
    if "release" in c or "リリース" in c:
        return ("RELEASE", "lib-news-tag-release")
    if "サイト" in raw or "site" in c:
        return ("SITE", "lib-news-tag-site")
    if "media" in c or "メディア" in c:
        return ("MEDIA", "lib-news-tag-media")
    if "event" in c or "イベント" in c:
        return ("EVENT", "lib-news-tag-event")
    if "notice" in c or "お知らせ" in c:
        return ("NOTICE", "lib-news-tag-notice")
    if "governance" in c or "方針" in c or "統治" in c or "policy" in c:
        return ("POLICY", "lib-news-tag-governance")
    return (raw[:8].upper() if raw else "NEWS", "lib-news-tag-muted")


def _parse_news_date(s: str) -> date:
    t = (s or "").strip().replace("/", ".").replace("-", ".")
    parts = [p for p in t.split(".") if p]
    if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
        try:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
        except ValueError:
            return date.min
    return date.min


def get_featured_news(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not items:
        return None
    return items[0]


def split_current_and_archive_news(
    items: List[Dict[str, Any]],
    *,
    featured: bool = True,
    current_max: int = 3,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    featured=True のとき先頭1件を注目、次の current_max 件を「通常」、残りをアーカイブ。
    items は新しい順（importance 考慮済み）を想定。
    """
    if not items:
        return None, [], []
    if featured:
        feat = items[0]
        tail = items[1:]
    else:
        feat = None
        tail = list(items)
    current = tail[: max(0, current_max)]
    archive = tail[max(0, current_max) :]
    return feat, current, archive


def _body_to_html(body: str) -> str:
    if not (body or "").strip():
        return ""
    text = body.strip()
    for ext in (["fenced_code", "tables", "nl2br"], ["fenced_code", "tables"]):
        try:
            return markdown.markdown(text, extensions=ext)
        except Exception:
            continue
    return html.escape(text).replace("\n", "<br/>")


def render_news_card(
    row: Dict[str, Any],
    *,
    featured: bool,
    site_category_logo_html: Optional[str],
    widget_key_prefix: str,
    link_label: str,
) -> None:
    d_esc = html.escape(str(row.get("date", "—")), quote=True)
    raw_cat = str(row.get("category", ""))
    title = str(row.get("title", ""))
    title_esc = html.escape(title, quote=True)
    tag_txt, tag_cls = _news_tag_class(raw_cat)
    tag_txt_esc = html.escape(tag_txt, quote=True)
    body = str(row.get("body", "") or "")
    body_html = _body_to_html(body)
    card_cls = "lib-news-card lib-news-card--featured" if featured else "lib-news-card"
    logo_block = ""
    if site_category_logo_html and tag_cls == "lib-news-tag-site":
        logo_block = (
            f'<div class="lib-news-detail-logo">{site_category_logo_html}</div>'
        )
    inner = ""
    if body_html:
        inner = f'<div class="lib-news-card-body">{logo_block}{body_html}</div>'
    elif logo_block:
        inner = logo_block

    st.markdown(
        f"""
<div class="{card_cls}">
  <div class="lib-news-card-meta">
    <span>{d_esc}</span>
    <span class="lib-news-tag {tag_cls}">{tag_txt_esc}</span>
  </div>
  <h3 class="lib-news-card-title">{title_esc}</h3>
  {inner}
</div>
        """,
        unsafe_allow_html=True,
    )
    link = str(row.get("link", "") or "").strip()
    if link.startswith("http://") or link.startswith("https://"):
        try:
            st.link_button(
                link_label,
                link,
                key=f"{widget_key_prefix}_lnk",
                use_container_width=True,
            )
        except TypeError:
            try:
                st.link_button(link_label, link, use_container_width=True)
            except TypeError:
                st.markdown(
                    f'<p class="lib-news-stack"><a href="{html.escape(link, quote=True)}" '
                    f'target="_blank" rel="noopener noreferrer">{html.escape(link_label)}</a></p>',
                    unsafe_allow_html=True,
                )


def render_featured_news(
    row: Dict[str, Any],
    *,
    site_category_logo_html: Optional[str],
    link_label: str,
) -> None:
    st.markdown(
        '<div id="lib-tzk-news-anchor" style="height:0;margin:0;" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    render_news_card(
        row,
        featured=True,
        site_category_logo_html=site_category_logo_html,
        widget_key_prefix="lib_news_feat",
        link_label=link_label,
    )


def render_current_news_section(
    items: List[Dict[str, Any]],
    *,
    site_category_logo_html: Optional[str],
    link_label: str,
) -> None:
    st.markdown('<div class="lib-news-stack">', unsafe_allow_html=True)
    for i, row in enumerate(items):
        render_news_card(
            row,
            featured=False,
            site_category_logo_html=site_category_logo_html,
            widget_key_prefix=f"lib_news_cur_{i}",
            link_label=link_label,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_news_archive(
    items: List[Dict[str, Any]],
    *,
    month_prefix: str,
    site_category_logo_html: Optional[str],
    link_label: str,
) -> None:
    by_month: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in items:
        d = _parse_news_date(str(row.get("date", "")))
        ym = d.strftime("%Y-%m") if d != date.min else "—"
        by_month[ym].append(row)
    order = sorted(by_month.keys(), reverse=True)
    for ym in order:
        st.markdown(
            f'<p class="lib-news-archive-month">{html.escape(month_prefix)} {html.escape(ym)}</p>',
            unsafe_allow_html=True,
        )
        month_items = sorted(
            by_month[ym],
            key=lambda r: (
                _parse_news_date(str(r.get("date", ""))).toordinal(),
                str(r.get("title", "")),
            ),
            reverse=True,
        )
        ym_key = ym.replace("-", "_").replace("—", "na")
        st.markdown('<div class="lib-news-stack">', unsafe_allow_html=True)
        for j, row in enumerate(month_items):
            render_news_card(
                row,
                featured=False,
                site_category_logo_html=site_category_logo_html,
                widget_key_prefix=f"lib_news_arc_{ym_key}_{j}",
                link_label=link_label,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_news_split_accordion_cards(
    *,
    base_dir: Path,
    max_items: int = 8,
    section_title: str = "最新のお知らせ・更新情報",
    wide_layout: bool = False,
    site_category_logo_html: Optional[str] = None,
    detail_expander_label: str = "詳細を読む",
    news_mast_heading: str = "NEWS",
    news_kicker_label: str = "Updates",
    lang: str = "ja",
    news_featured_label: Optional[str] = None,
    news_more_expander_tpl: Optional[str] = None,
    news_archive_expander_label: Optional[str] = None,
    news_archive_month_prefix: Optional[str] = None,
    news_link_label: Optional[str] = None,
    news_empty_hint: Optional[str] = None,
    current_slot_count: int = 3,
    load_cap: Optional[int] = None,
) -> None:
    """
    左：従来どおりエディトリアル見出し／右：注目カード＋通常（expander）＋アーカイブ（expander・月別）。
    """
    from lib.tanizawa_layout import inject_tanizawa_landing_css

    inject_tanizawa_landing_css()
    _inject_news_card_css_once()

    cap = int(load_cap) if load_cap is not None else max(48, int(max_items or 8))
    items = load_top_news_sorted(base_dir, lang=lang, load_cap=cap)

    if lang == "en":
        feat_lbl = news_featured_label or "Featured"
        more_tpl = news_more_expander_tpl or "More updates ({n})"
        arch_lbl = news_archive_expander_label or "Archive (older announcements)"
        month_pfx = news_archive_month_prefix or "Month"
        link_lbl = news_link_label or "Open related page"
        empty_hint = news_empty_hint or "—"
    else:
        feat_lbl = news_featured_label or "注目のお知らせ"
        more_tpl = news_more_expander_tpl or "その他のお知らせ（{n}件）"
        arch_lbl = news_archive_expander_label or "アーカイブ（過去のお知らせ）"
        month_pfx = news_archive_month_prefix or "掲載月"
        link_lbl = news_link_label or "関連ページを開く"
        empty_hint = news_empty_hint or "（該当がありません）"

    featured, current, archive = split_current_and_archive_news(
        items,
        featured=True,
        current_max=max(0, int(current_slot_count)),
    )

    if wide_layout:
        left, right = st.columns([0.26, 0.74], gap="large")
        edu_cls = "lib-tzk-news-edu lib-tzk-news-wide"
    else:
        left, right = st.columns([0.34, 0.66], gap="large")
        edu_cls = "lib-tzk-news-edu"
    _lede = (
        f'<p class="lib-tzk-news-lede">{_html(section_title)}</p>'
        if (section_title or "").strip()
        else ""
    )
    with left:
        st.markdown(
            f'<div class="{edu_cls}">'
            f'<p class="lib-tzk-news-kicker">{_html(news_kicker_label)}</p>'
            f'<h2 class="lib-tzk-news-mast">{_html(news_mast_heading)}</h2>'
            f"{_lede}"
            f'<div class="lib-tzk-news-accent-bar" aria-hidden="true"></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f'<p style="font-size:0.82rem;font-weight:700;color:#475569;margin:0 0 0.55rem 0;">'
            f"{html.escape(feat_lbl)}</p>",
            unsafe_allow_html=True,
        )
        if featured:
            render_featured_news(
                featured,
                site_category_logo_html=site_category_logo_html,
                link_label=link_lbl,
            )
        else:
            st.caption(empty_hint)

        if current:
            exp_label = more_tpl.format(n=len(current))
            with st.expander(exp_label, expanded=False):
                render_current_news_section(
                    current,
                    site_category_logo_html=site_category_logo_html,
                    link_label=link_lbl,
                )

        if archive:
            with st.expander(arch_lbl, expanded=False):
                render_news_archive(
                    archive,
                    month_prefix=month_pfx,
                    site_category_logo_html=site_category_logo_html,
                    link_label=link_lbl,
                )

    _ = detail_expander_label  # 旧 UI 互換：カード内に本文を直接表示したため未使用
