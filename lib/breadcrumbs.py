# -*- coding: utf-8 -*-
"""
サイト内パンくず（谷澤総合鑑定所型：ホーム ＞ セクション ＞ 現在ページ）。

表示はメイン列先頭・通常フロー（固定・sticky なし）。TOP ページでは帯自体を出さない。
.lib-bc-root 配下のみスタイルを適用し副作用を限定。
遷移は app.py の ?nav= ハンドラと同期する <a href="?nav=..."> を使用。
"""

from __future__ import annotations

import html
from typing import Callable, Optional, Sequence, Tuple
from urllib.parse import quote

import streamlit as st

# app.py TOP で先頭スクロールするための 1 ショットフラグ（パンくず「ホーム」遷移時にセット）
SCROLL_TOP_ONCE_KEY = "_lib_scroll_to_top_once"

# TOP ナビのグループと整合（＋サイドバー単独ページ用グループ）
_BREADCRUMB_GROUPS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        "企業・ご案内",
        (
            "TOP",
            "はじめての方へ",
            "会社概要",
            "代表プロフィール",
            "お問い合わせ",
        ),
    ),
    ("サービス・実績", ("業務内容", "業務の流れ", "実績・ケーススタディ")),
    (
        "AI・ツール・研究",
        (
            "AI分析ツール",
            "AI評価研究グループ",
            "価格の目利き",
            "不動産鑑定士マッチング",
        ),
    ),
    (
        "ガバナンス・ポリシー",
        (
            "AI思想（Methodology）",
            "企業統治（Governance）",
            "情報セキュリティ（ISMS相当）",
            "倫理規程・不動産鑑定士職業倫理",
            "プライバシー",
        ),
    ),
)

# セレクタはすべて .lib-bc-root 配下に限定（他コンポーネントへの CSS 漏れを防ぐ）
# v5: カード／シャドウを廃止し、本文フロー上のインライン型（フローティング見えをしない）
_BC_CSS = """
<style>
.lib-bc-root {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0 0 0.45rem 0;
  padding: 0;
}
.lib-bc-root .lib-bc-panel {
  position: static;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  text-align: left;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(15, 28, 46, 0.12);
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
}
.lib-bc-root .lib-bc-panel__accent {
  display: none;
}
.lib-bc-root .lib-bc-panel__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 0.2rem 0.35rem;
  padding: 0.3rem 0 0.45rem 0;
  box-sizing: border-box;
  font-size: 0.78rem;
  line-height: 1.45;
  color: #334155;
}
@media (max-width: 640px) {
  .lib-bc-root .lib-bc-panel__inner {
    font-size: 0.72rem;
    gap: 0.15rem 0.28rem;
  }
}
.lib-bc-root .lib-bc-sep {
  color: #94a3b8;
  font-size: 0.7rem;
  user-select: none;
  font-weight: 500;
  margin: 0 0.04rem;
}
.lib-bc-root .lib-bc-current-page {
  font-weight: 600;
  font-size: inherit;
  color: #0f172a;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  letter-spacing: 0.01em;
}
.lib-bc-root .lib-bc-a {
  display: inline;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: #1d4ed8 !important;
  text-decoration: underline;
  text-decoration-color: rgba(29, 78, 216, 0.35);
  text-underline-offset: 0.12em;
  font-weight: 500;
  font-size: inherit;
  transition: text-decoration-color 0.15s ease, color 0.15s ease;
}
.lib-bc-root .lib-bc-a:hover {
  color: #1e40af !important;
  text-decoration-color: rgba(30, 64, 175, 0.75);
  background: transparent;
  border: none;
  box-shadow: none;
}
.lib-bc-root .lib-bc-a:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
  border-radius: 2px;
}
.lib-bc-root .lib-bc-back {
  min-width: 0;
  padding: 0 0.2rem 0 0;
  text-decoration: none;
  color: #475569 !important;
}
.lib-bc-root .lib-bc-back:hover {
  color: #1d4ed8 !important;
  text-decoration: underline;
  text-decoration-color: rgba(29, 78, 216, 0.5);
}
.lib-bc-root .lib-bc-muted {
  font-weight: 500;
  color: #94a3b8;
  font-size: inherit;
}
.lib-bc-root .lib-bc-spacer-after {
  display: none;
}
</style>
"""


def _find_group(page: str) -> Optional[Tuple[str, Tuple[str, ...]]]:
    for label, plist in _BREADCRUMB_GROUPS:
        if page in plist:
            return (label, plist)
    return None


def _hub_page(pages: Sequence[str]) -> str:
    if not pages:
        return "TOP"
    if pages[0] == "TOP" and len(pages) > 1:
        return pages[1]
    return pages[0]


def _category_nav_target(pages: Sequence[str], current: str) -> str:
    """セクション名クリック：ハブへ。すでにハブならホーム（TOP）へ。"""
    hub = _hub_page(pages)
    if current != hub:
        return hub
    return "TOP"


def _nav_query_href(target: str, valid: frozenset[str]) -> str:
    """app.py の ?nav= ハンドラ向けリンク（未登録ページは #）。"""
    if target not in valid:
        return "#"
    return f"?nav={quote(target, safe='')}"


def render_site_breadcrumbs(
    *,
    current_page: str,
    pending_nav_key: str,
    valid_pages: Sequence[str],
    home_label: str = "ホーム",
    back_button_help: str = "トップ（ホーム）へ",
    format_page_label: Optional[Callable[[str], str]] = None,
    format_group_label: Optional[Callable[[str], str]] = None,
) -> None:
    _ = pending_nav_key  # 互換のため引数は維持（遷移は ?nav= に統一）

    # TOP はパンくず帯を出さない（ヒーロー直上の帯を避け、従来のトップ構成に戻す）
    if current_page == "TOP":
        return

    # v5: インライン型（固定なし・カード／シャドウなし）
    if not st.session_state.get("_lib_inject_bc_css_v5"):
        st.session_state["_lib_inject_bc_css_v5"] = True
        st.markdown(_BC_CSS, unsafe_allow_html=True)

    _fmt_page = format_page_label or (lambda p: p)
    _fmt_group = format_group_label or (lambda g: g)
    _valid = frozenset(valid_pages)

    _hl = html.escape(home_label, quote=True)
    _bh = html.escape(back_button_help, quote=True)

    grp = _find_group(current_page)
    cat_label = grp[0] if grp else None
    cat_pages = grp[1] if grp else ()
    cat_target = _category_nav_target(cat_pages, current_page) if grp else "TOP"

    href_top = _nav_query_href("TOP", _valid)
    href_cat = _nav_query_href(cat_target, _valid)

    parts = [
        f'<a class="lib-bc-a lib-bc-back" href="{html.escape(href_top, quote=True)}" '
        f'title="{_bh}" aria-label="{_bh}">←</a>',
        f'<a class="lib-bc-a" href="{html.escape(href_top, quote=True)}">{_hl}</a>',
        '<span class="lib-bc-sep" aria-hidden="true">＞</span>',
    ]
    if cat_label:
        _cg = html.escape(_fmt_group(cat_label), quote=True)
        parts.append(
            f'<a class="lib-bc-a" href="{html.escape(href_cat, quote=True)}">{_cg}</a>'
        )
    else:
        parts.append('<span class="lib-bc-muted">—</span>')
    parts.append('<span class="lib-bc-sep" aria-hidden="true">＞</span>')
    _cur = html.escape(_fmt_page(current_page), quote=True)
    parts.append(
        f'<span class="lib-bc-current-page" aria-current="page">{_cur}</span>'
    )
    inner = "\n".join(parts)

    st.markdown(
        f"""
<div class="lib-bc-root">
  <nav class="lib-bc-panel" aria-label="breadcrumb">
    <div class="lib-bc-panel__accent" aria-hidden="true"></div>
    <div class="lib-bc-panel__inner">
{inner}
    </div>
  </nav>
</div>
        """,
        unsafe_allow_html=True,
    )


def main_app_nav_href(nav_target: str) -> str:
    """`app.py` の `?nav=` ルータ向けの絶対パス（先頭 `/`）。マルチページからメインへ戻る際に使う。"""
    return f"/?nav={quote(nav_target, safe='')}"


def _safe_multipage_href(href: str) -> str:
    h = (href or "").strip()
    if not h or h.startswith("//") or "javascript:" in h.lower():
        return main_app_nav_href("TOP")
    if not h.startswith("/"):
        return main_app_nav_href("TOP")
    return h


def render_multipage_breadcrumb_bar(
    *,
    current_label: str,
    middle_links: Optional[Sequence[Tuple[str, str]]] = None,
    home_label: str = "ホーム",
    back_button_help: str = "トップ（ホーム）へ",
) -> None:
    """
    `pages/*.py` 用パンくず。`render_site_breadcrumbs` と同一の `_BC_CSS`（v5）を使い見た目を揃える。

    メイン `app.py` は別スクリプトのためセッションは共有されない。ホーム・中間リンクは HTML の
    `<a href>` で遷移する（`?nav=` は `app.py` と整合）。

    新規タブ／iframe で開いた別 URL も、同じモジュールを import すれば同じ見た目になる。
    別 origin の埋め込みはリポジトリ外のため対象外。
    """
    if not st.session_state.get("_lib_inject_bc_css_v5"):
        st.session_state["_lib_inject_bc_css_v5"] = True
        st.markdown(_BC_CSS, unsafe_allow_html=True)

    href_top = _safe_multipage_href(main_app_nav_href("TOP"))
    _hl = html.escape(home_label, quote=True)
    _bh = html.escape(back_button_help, quote=True)
    _cur = html.escape(current_label, quote=True)

    parts: list[str] = [
        f'<a class="lib-bc-a lib-bc-back" href="{html.escape(href_top, quote=True)}" '
        f'title="{_bh}" aria-label="{_bh}">←</a>',
        f'<a class="lib-bc-a" href="{html.escape(href_top, quote=True)}">{_hl}</a>',
        '<span class="lib-bc-sep" aria-hidden="true">＞</span>',
    ]
    for href, text in middle_links or ():
        safe_h = _safe_multipage_href(href)
        parts.append(
            f'<a class="lib-bc-a" href="{html.escape(safe_h, quote=True)}">'
            f"{html.escape(text, quote=True)}</a>"
        )
        parts.append('<span class="lib-bc-sep" aria-hidden="true">＞</span>')
    parts.append(
        f'<span class="lib-bc-current-page" aria-current="page">{_cur}</span>'
    )
    inner = "\n".join(parts)

    st.markdown(
        f"""
<div class="lib-bc-root">
  <nav class="lib-bc-panel" aria-label="breadcrumb">
    <div class="lib-bc-panel__accent" aria-hidden="true"></div>
    <div class="lib-bc-panel__inner">
{inner}
    </div>
  </nav>
</div>
        """,
        unsafe_allow_html=True,
    )
