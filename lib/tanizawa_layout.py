# -*- coding: utf-8 -*-
"""
谷澤総合鑑定所トップに近い「帯・NEWS・フッターサイトマップ」レイアウト補助。

Streamlit はコーポレートサイトの完全再現向けではないが、columns + CSS + ボタン遷移で近似する。
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import streamlit as st

from lib.top_corporate import _html

_TZK_CSS = """
<style>
/* ヒーロー直下：3 分割の濃色帯（谷澤の斜めタブのイメージをフラットに） */
.lib-tzk-belt-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.22em;
  color: #64748b;
  margin: 0 0 0.35rem 0;
  text-transform: uppercase;
}
.lib-tzk-belt-note {
  font-size: 0.76rem;
  color: #94a3b8;
  margin: 0 0 0.65rem 0;
}
/* NEWS：左エディトリアル（見出しのみ・一覧は右カラム） */
.lib-tzk-news-edu {
  padding: 0.35rem 0.5rem 1.25rem 0;
  border-left: 3px solid #c9a24d;
  padding-left: 1.25rem;
  margin-left: 2px;
}
.lib-tzk-news-kicker {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.32em;
  color: #94a3b8;
  text-transform: uppercase;
  margin: 0 0 0.5rem 0;
}
.lib-tzk-news-mast {
  font-size: clamp(2rem, 4.5vw, 2.65rem);
  font-weight: 900;
  letter-spacing: 0.18em;
  color: #0f1c2e;
  margin: 0 0 0.65rem 0;
  line-height: 1.05;
}
.lib-tzk-news-lede {
  font-size: 0.95rem;
  line-height: 1.75;
  color: #475569;
  margin: 0 0 1rem 0;
  max-width: 22rem;
}
/* TOP 全幅レイアウト時：左コピーをやや広く */
.lib-tzk-news-wide .lib-tzk-news-lede {
  max-width: min(36rem, 100%);
}
.lib-tzk-news-wide .lib-tzk-news-mast {
  letter-spacing: 0.14em;
}
.lib-tzk-news-accent-bar {
  width: 48px;
  height: 3px;
  background: linear-gradient(90deg, #c9a24d, rgba(201, 162, 77, 0.2));
  border-radius: 2px;
}
/* 右：ニュース一覧パネル */
.lib-tzk-news-item-shell {
  border-radius: 16px;
  border: 1px solid rgba(15, 28, 46, 0.07);
  background: linear-gradient(165deg, #ffffff 0%, #f8fafc 55%, #f1f5f9 100%);
  box-shadow:
    0 2px 4px rgba(15, 28, 46, 0.04),
    0 12px 28px -8px rgba(15, 28, 46, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  padding: 0.5rem 1rem;
  margin-bottom: 0.45rem;
}
.lib-tzk-newsline-v2 {
  display: grid;
  grid-template-columns: 5.5rem 5.5rem 1fr 1.25rem;
  gap: 0.45rem 0.65rem;
  align-items: center;
  padding: 0.62rem 0;
  border-bottom: none;
  font-size: 0.9rem;
  transition: background 0.15s ease;
  margin: 0;
  padding: 0.35rem 0.15rem;
  border-radius: 10px;
}
.lib-tzk-newsline-v2:hover {
  background: rgba(15, 28, 46, 0.025);
}
.lib-tzk-news-date-v2 {
  color: #0f1c2e;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  font-size: 0.82rem;
}
.lib-tzk-tag {
  display: inline-block;
  font-size: 0.58rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  padding: 0.22rem 0.48rem;
  border-radius: 4px;
  color: #fff;
  text-align: center;
  min-width: 4.5rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
}
.lib-tzk-tag-report { background: linear-gradient(135deg, #dc2626, #991b1b); }
.lib-tzk-tag-release { background: linear-gradient(135deg, #2563eb, #1d4ed8); }
.lib-tzk-tag-site { background: linear-gradient(135deg, #0d9488, #0f766e); }
.lib-tzk-tag-notice { background: linear-gradient(135deg, #d97706, #b45309); }
.lib-tzk-tag-media { background: linear-gradient(135deg, #7c3aed, #5b21b6); }
.lib-tzk-tag-event { background: linear-gradient(135deg, #e11d48, #be123c); }
.lib-tzk-tag-governance { background: linear-gradient(135deg, #475569, #334155); }
.lib-tzk-tag-muted { background: linear-gradient(135deg, #64748b, #475569); }
.lib-tzk-news-title-v2 {
  color: #1e293b;
  margin: 0;
  line-height: 1.5;
  font-weight: 600;
  font-size: 0.92rem;
}
.lib-tzk-news-arrow-v2 {
  color: #c9a24d;
  text-align: right;
  font-size: 1.15rem;
  font-weight: 300;
}
.lib-tzk-news-detail-logo {
  margin: 0 0 0.85rem 0;
}
.lib-tzk-news-detail-logo img {
  max-height: 52px;
  width: auto;
  max-width: 100%;
  display: block;
  object-fit: contain;
}
/* 全幅 CTA 風 */
.lib-tzk-fw-cta-h {
  text-align: center;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.28em;
  color: rgba(255,255,255,0.72);
  margin: 0 0 0.35rem 0;
}
</style>
"""


def inject_tanizawa_landing_css() -> None:
    if st.session_state.get("_lib_inject_tzk_css"):
        return
    st.session_state["_lib_inject_tzk_css"] = True
    st.markdown(_TZK_CSS, unsafe_allow_html=True)


def _tag_class(category: str) -> Tuple[str, str]:
    c = (category or "").strip().lower()
    raw = (category or "").strip()
    if "report" in c or c in ("事例", "レポート"):
        return ("REPORT", "lib-tzk-tag-report")
    if "release" in c or "リリース" in c:
        return ("RELEASE", "lib-tzk-tag-release")
    if "サイト" in raw or "site" in c:
        return ("SITE", "lib-tzk-tag-site")
    if "media" in c or "メディア" in raw:
        return ("MEDIA", "lib-tzk-tag-media")
    if "event" in c or "イベント" in raw:
        return ("EVENT", "lib-tzk-tag-event")
    if "notice" in c or "お知らせ" in raw:
        return ("NOTICE", "lib-tzk-tag-notice")
    if "governance" in c or "方針" in raw or "統治" in raw or "policy" in c:
        return ("POLICY", "lib-tzk-tag-governance")
    return (raw[:8].upper() if raw else "NEWS", "lib-tzk-tag-muted")


def render_hero_subnav_belt(
    *,
    pending_nav_key: str,
    valid_pages: Sequence[str],
) -> None:
    """ヒーロー直下の 3 分割ナビ（谷澤の斜めタブ帯のイメージ）。"""
    inject_tanizawa_landing_css()
    st.markdown(
        '<p class="lib-tzk-belt-label">Message · Expertise · Library</p>'
        '<p class="lib-tzk-belt-note">主要な入口をすぐに開けます（フルリロードなし）。</p>',
        unsafe_allow_html=True,
    )
    specs: Tuple[Tuple[str, str, str], ...] = (
        ("tzk_b1", "代表メッセージ／プロフィール", "代表プロフィール"),
        ("tzk_b2", "業務・専門性", "業務内容"),
        ("tzk_b3", "実績・レポート・事例", "実績・ケーススタディ"),
    )
    c1, c2, c3 = st.columns(3, gap="small")
    for col, (kid, label, target) in zip((c1, c2, c3), specs):
        with col:
            if target not in valid_pages:
                st.caption("—")
                continue
            if st.button(label, key=kid, width="stretch", type="primary"):
                st.session_state[pending_nav_key] = target
                st.rerun()


def render_news_split_tanizawa_style(
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
    news_current_slot_count: int = 3,
    news_load_cap: Optional[int] = None,
) -> None:
    """
    NEWS：左にエディトリアル見出し、右にカード＋アコーディオン（`lib/news_section.py` に実装集約）。
    データは `data/top_news.json`（`load_top_news_sorted` で最大 news_load_cap 件まで読込）。
    """
    # 循環 import 回避のため遅延 import
    from lib.news_section import render_news_split_accordion_cards

    render_news_split_accordion_cards(
        base_dir=base_dir,
        max_items=max_items,
        section_title=section_title,
        wide_layout=wide_layout,
        site_category_logo_html=site_category_logo_html,
        detail_expander_label=detail_expander_label,
        news_mast_heading=news_mast_heading,
        news_kicker_label=news_kicker_label,
        lang=lang,
        news_featured_label=news_featured_label,
        news_more_expander_tpl=news_more_expander_tpl,
        news_archive_expander_label=news_archive_expander_label,
        news_archive_month_prefix=news_archive_month_prefix,
        news_link_label=news_link_label,
        news_empty_hint=news_empty_hint,
        current_slot_count=news_current_slot_count,
        load_cap=news_load_cap,
    )


def render_fullwidth_contact_cta(
    *,
    pending_nav_key: str,
    valid_pages: Sequence[str],
    cta_kicker: str = "コンタクト",
    button_label: str = "お問い合わせはこちら",
) -> None:
    """画面幅いっぱいに近いお問い合わせ帯。"""
    inject_tanizawa_landing_css()
    st.markdown(
        '<div style="height:10px" aria-hidden="true"></div>'
        f'<p class="lib-tzk-fw-cta-h">{html.escape(cta_kicker, quote=True)}</p>',
        unsafe_allow_html=True,
    )
    if "お問い合わせ" not in valid_pages:
        return
    if st.button(
        button_label,
        key="tzk_fw_contact",
        width="stretch",
        type="primary",
    ):
        st.session_state[pending_nav_key] = "お問い合わせ"
        st.rerun()


_DEFAULT_SITEMAP_SECTION_TITLES: Tuple[str, str, str, str] = (
    "企業・ご案内",
    "サービス・実績",
    "AI・ツール",
    "方針・統治",
)


def render_dark_footer_sitemap(
    *,
    pending_nav_key: str,
    valid_pages: Sequence[str],
    expander_title: str = "サイトマップ",
    section_titles: Optional[Sequence[str]] = None,
    format_page_label: Optional[Callable[[str], str]] = None,
) -> None:
    """ページ下部のサイトマップ（畳み込み・シンプル）。"""
    titles = (
        tuple(section_titles)
        if section_titles is not None
        else _DEFAULT_SITEMAP_SECTION_TITLES
    )
    _fmt = format_page_label or (lambda p: p)
    blocks: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
        ("ABOUT", ("TOP", "はじめての方へ", "会社概要", "代表プロフィール")),
        ("BUSINESS", ("業務内容", "業務の流れ", "実績・ケーススタディ")),
        (
            "TOOLS",
            ("AI分析ツール", "AI評価研究グループ", "価格の目利き", "不動産鑑定士マッチング"),
        ),
        (
            "GOVERNANCE",
            (
                "AI思想（Methodology）",
                "企業統治（Governance）",
                "情報セキュリティ（ISMS相当）",
                "倫理規程・不動産鑑定士職業倫理",
                "プライバシー",
                "お問い合わせ",
            ),
        ),
    )
    with st.expander(expander_title, expanded=False):
        for bi, (_key, pages) in enumerate(blocks):
            sec = titles[bi] if bi < len(titles) else _key
            st.markdown(f"**{sec}**")
            plist = [p for p in pages if p in valid_pages]
            for row_start in range(0, len(plist), 3):
                chunk = plist[row_start : row_start + 3]
                cols = st.columns(len(chunk))
                for ci, p in enumerate(chunk):
                    with cols[ci]:
                        key = f"smap_{bi}_{row_start}_{ci}"
                        if st.button(
                            _fmt(p),
                            key=key,
                            width="stretch",
                            type="secondary",
                        ):
                            st.session_state[pending_nav_key] = p
                            st.rerun()
