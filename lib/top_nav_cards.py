# -*- coding: utf-8 -*-
"""
TOP 用：サイト内ナビカード群（AIテック風の統一ビジュアル＋ワンクリック遷移）。

【遷移】
- カード全体が 1 つの st.button（クリックで pending_nav_key にページ名を設定して rerun）。
- <a href="?nav"> はフルリロードで WebSocket が切れるため使わない。

【ビジュアル】
- 写真・Unsplash に依存せず、CSS 多層グラデ＋グリッドで統一（preset で色相のみ変化）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

import streamlit as st

TOP_NAV_GROUP_EN: Dict[str, str] = {
    "企業・ご案内": "CORPORATE",
    "サービス・実績": "SERVICES & WORKS",
    "AI・ツール・研究": "AI · TOOLS · RESEARCH",
}

@dataclass(frozen=True)
class TopNavCardSpec:
    card_id: str
    title: str
    target_page: str
    description: str = ""
    image_rel: Optional[str] = None
    button_label: str = "開く"
    ai_city_preset: int = 0
    # True のとき、ボタン（または「表示中」）の直上に image_rel の画像をそのまま表示する
    show_image_above: bool = False


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# スタイル署名の版。セレクタ方式を変えたら必ず上げる（session の古い CSS を捨てる）。
# stMain 付きセレクタは app.py 全体の primary ボタン background-color !important より詳細度を上げるため。
_LIB_TOPNAV_DOM_REV = "st-key-main-scope-v1"
# ボタン見た目・余白ロジックを変えたら上げる（キャッシュされた style ブロックを無効化）
_TOPNAV_CARD_LAYOUT_REV = "btn-bg-only-v4-emphasis-text"


def _topnav_streamlit_key(card_id: str) -> str:
    """render_top_nav_card の st.button(..., key=...) と同一文字列にすること。"""
    return f"topnav_{card_id.replace(chr(34), '')}"


def _topnav_button_css_selectors(card_id: str) -> str:
    """
    st.button の key から付く `st-key-{key}` クラスでラッパーを特定する。
    section[data-testid="stMain"] を付け、inject_app_css の [data-testid=stButton] button より詳細度を上げる。
    """
    key = _topnav_streamlit_key(card_id)
    return (
        f'section[data-testid="stMain"] div.st-key-{key} [data-testid="stButton"] button'
    )


def _topnav_onpage_css_selector(card_id: str) -> str:
    cid = card_id.replace('"', "")
    return f'div.lib-ai-nav-onpage[data-lib-topnav-id="{cid}"]'


def _mime_for_image_rel(rel: str) -> str:
    """CSS data URL 用。拡張子と実データの種類を一致させる（.png を jpeg と誤宣言しない）。"""
    ext = Path(rel).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext, "image/jpeg")


def inject_top_nav_card_css() -> None:
    if st.session_state.get("_lib_inject_topnav_css"):
        return
    st.session_state["_lib_inject_topnav_css"] = True
    st.markdown(
        """
<style>
/* --- グループ帯：白背景・黒文字 --- */
.lib-topnav-group-panel {
  margin: 0 0 0.85rem 0;
  padding: clamp(0.55rem, 1.4vw, 0.75rem) clamp(0.75rem, 2vw, 1.2rem);
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 24px -6px rgba(15, 28, 46, 0.08);
  width: 100%;
  box-sizing: border-box;
}
.lib-topnav-group-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.35rem 0.9rem;
}
.lib-topnav-group-title-jp {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #0f172a;
}
.lib-topnav-group-title-en { margin: 0; }
.lib-topnav-en-geom {
  display: inline-block;
  font-size: 0.56rem;
  font-weight: 800;
  letter-spacing: 0.22em;
  color: #0f172a;
  text-transform: uppercase;
  padding: 0.22rem 0.55rem;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  border-radius: 4px;
}
.lib-topnav-group-hr {
  margin-top: 0.45rem;
  height: 1px;
  background: linear-gradient(90deg, #cbd5e1, transparent);
  opacity: 1;
  border-radius: 1px;
}
.lib-topnav-section-kicker {
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: #64748b;
  text-transform: uppercase;
  margin: 0 0 0.3rem 0;
}
.lib-topnav-section-title {
  margin: 0 0 0.9rem 0;
  font-size: 1.28rem;
  font-weight: 800;
  color: #0f1c2e;
  letter-spacing: 0.02em;
}
/* カード列：ナビカード同士の縦余白を統一（タップしやすさ） */
[data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
  margin-bottom: 0.55rem !important;
}
[data-testid="column"] [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-child {
  margin-bottom: 0 !important;
}
/* ナビ画像の角をカードと揃える */
[data-testid="column"] [data-testid="stImage"] img {
  border-radius: 12px !important;
}
/* グループ同士の間隔 */
.lib-topnav-after-group-spacer {
  height: 0.85rem;
  min-height: 0.85rem;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _ai_nav_background_layers(preset: int) -> str:
    """AIイメージ統一：多層グラデ＋淡いグリッド＋光彩（写真に依存しない）。"""
    p = int(preset) % 8
    palettes = (
        (195, 245, 38, 220),
        (265, 290, 48, 200),
        (175, 205, 42, 210),
        (210, 240, 45, 230),
        (155, 185, 40, 195),
        (230, 260, 50, 215),
        (200, 225, 44, 235),
        (185, 215, 36, 205),
    )
    a, b, sat, glow = palettes[p]
    core = (
        f"linear-gradient(155deg, hsl({a},{sat}%,16%) 0%, hsl({b},{sat+8}%,10%) 48%, #070b12 100%)"
    )
    grid = (
        "repeating-linear-gradient(0deg, transparent, transparent 18px, rgba(148,200,255,0.04) 18px, rgba(148,200,255,0.04) 19px), "
        "repeating-linear-gradient(90deg, transparent, transparent 18px, rgba(148,200,255,0.04) 18px, rgba(148,200,255,0.04) 19px)"
    )
    glow_r = (
        f"radial-gradient(ellipse 90% 60% at 20% 30%, hsla({glow},55%,45%,0.22) 0%, transparent 55%), "
        f"radial-gradient(ellipse 70% 50% at 85% 75%, hsla({a},70%,50%,0.12) 0%, transparent 50%)"
    )
    scan = "linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.04) 50%, transparent 60%)"
    return f"{core}, {glow_r}, {grid}, {scan}"


def _inject_ai_nav_styles_for_specs(
    specs: Sequence[TopNavCardSpec],
    featured_card_ids: Optional[Set[str]] = None,
    *,
    base_dir: Path,
    b64_loader: Callable[[str], str],
    css_data_url_mime: Optional[str] = None,
    tile_b64_revision: str = "",
) -> None:
    featured_card_ids = featured_card_ids or set()
    # mtime に加え size も含め、差し替え・同一秒更新も検知。Streamlit の各 rerun では必ず style を出す（早期 return しない）。
    img_meta: List[Tuple[Optional[str], int, int]] = []
    for s in specs:
        if s.image_rel:
            p = base_dir / s.image_rel
            try:
                fi = p.stat()
                img_meta.append((s.image_rel, int(fi.st_mtime_ns), int(fi.st_size)))
            except OSError:
                img_meta.append((s.image_rel, 0, 0))
        else:
            img_meta.append((None, 0, 0))
    sig = (
        tuple(sorted(s.card_id for s in specs)),
        tuple(sorted(featured_card_ids)),
        tuple(img_meta),
        css_data_url_mime or "",
        _LIB_TOPNAV_DOM_REV,
        tile_b64_revision,
        _TOPNAV_CARD_LAYOUT_REV,
    )
    if st.session_state.get("_lib_ai_nav_style_sig") != sig:
        rules: List[str] = []
        for spec in specs:
            cid = spec.card_id.replace('"', "")
            tall = spec.card_id in featured_card_ids
            # 画像はボタン背景に統合済みのため、タップ領域をやや大きめに確保（特にスマホ）
            mh = "132px" if tall else "118px"
            fs = "clamp(1.02rem, 2.6vw, 1.22rem)" if tall else "clamp(0.95rem, 2.3vw, 1.08rem)"

            if spec.image_rel:
                b64 = b64_loader(spec.image_rel)
                if b64:
                    _mime = css_data_url_mime or _mime_for_image_rel(spec.image_rel)
                    # 画像上の暗幕なし（写真をそのまま見せる）
                    bg_img = (
                        "linear-gradient(155deg, rgba(15,28,46,0) 0%, rgba(7,11,18,0) 52%, rgba(15,28,46,0) 100%), "
                        f"url('data:{_mime};base64,{b64}')"
                    )
                    bg_extra = (
                        "background-size: auto, cover !important;\n"
                        "  background-position: center, center !important;\n"
                        "  background-repeat: no-repeat, no-repeat !important;"
                    )
                else:
                    bg_img = _ai_nav_background_layers(spec.ai_city_preset)
                    bg_extra = "background-blend-mode: normal, normal, normal, normal !important;"
            else:
                bg_img = _ai_nav_background_layers(spec.ai_city_preset)
                bg_extra = "background-blend-mode: normal, normal, normal, normal !important;"

            _sel_btn = _topnav_button_css_selectors(spec.card_id)
            _sel_on = _topnav_onpage_css_selector(spec.card_id)
            rules.append(
                f"""
{_sel_btn},
{_sel_on} {{
  background-color: transparent !important;
  background-image: {bg_img} !important;
  {bg_extra}
  min-height: {mh} !important;
  height: auto !important;
  white-space: normal !important;
  text-align: left !important;
  align-items: flex-start !important;
  justify-content: flex-end !important;
  padding: 1.05rem 1.1rem 1.15rem 1.1rem !important;
  color: #ffffff !important;
  font-weight: 800 !important;
  font-size: {fs} !important;
  line-height: 1.4 !important;
  letter-spacing: 0.04em !important;
  border: 1px solid rgba(201, 169, 98, 0.55) !important;
  border-radius: 16px !important;
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.06),
    0 16px 48px rgba(15, 28, 46, 0.35),
    0 0 40px rgba(56, 189, 248, 0.06) !important;
  transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease !important;
}}
{_sel_on} {{
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  box-sizing: border-box !important;
}}
{_sel_btn}:hover {{
  background-color: transparent !important;
  cursor: pointer !important;
  transform: translateY(-2px);
  box-shadow:
    inset 0 0 0 1px rgba(255,255,255,0.1),
    0 22px 56px rgba(15, 28, 46, 0.42),
    0 0 48px rgba(201, 169, 98, 0.12) !important;
  border-color: rgba(201, 169, 98, 0.85) !important;
}}
{_sel_btn}:focus-visible {{
  outline: 2px solid rgba(201, 169, 98, 0.95) !important;
  outline-offset: 2px !important;
}}
@media (max-width: 640px) {{
  {_sel_btn} {{
    min-height: calc({mh} + 12px) !important;
    padding: 1.05rem 1rem 1.15rem 1rem !important;
  }}
}}
{_sel_btn} p,
{_sel_on} p,
{_sel_btn} span,
{_sel_on} span {{
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
}}
"""
            )
        st.session_state["_lib_ai_nav_style_sig"] = sig
        st.session_state["_lib_ai_nav_style_block"] = "".join(rules)

    _block = st.session_state.get("_lib_ai_nav_style_block", "")
    if _block:
        st.markdown(f"<style>{_block}</style>", unsafe_allow_html=True)


def render_top_nav_card(
    *,
    spec: TopNavCardSpec,
    base_dir: Path,
    b64_loader: Callable[[str], str],
    valid_pages: Sequence[str],
    current_page: str,
    pending_nav_key: str,
    featured: bool = False,
) -> None:
    _ = (base_dir, b64_loader, featured, spec.show_image_above)  # API 互換（画像は CSS 背景のみ）
    if spec.target_page not in valid_pages:
        st.error(f"設定エラー: 「{spec.target_page}」は PAGES にありません。")
        return

    on_page = spec.target_page == current_page
    _aid = _escape_html(spec.card_id)

    # カード背景画像は CSS で st.button 上に載る。上に別要素で st.image を出すと
    # 「画像は押せない・下のボタンだけ」になりスマホで不利。クリック可能領域はボタン 1 枚に統一する。

    if on_page:
        st.markdown(
            f'<div class="lib-ai-nav-onpage" data-lib-topnav-id="{_aid}">'
            f"<p>表示中：{_escape_html(spec.title)}</p></div>",
            unsafe_allow_html=True,
        )
        return

    label = spec.title

    if st.button(
        label,
        key=f"topnav_{spec.card_id}",
        width="stretch",
        type="primary",
    ):
        st.session_state[pending_nav_key] = spec.target_page
        st.rerun()


def render_top_nav_card_grid(
    *,
    specs: List[TopNavCardSpec],
    base_dir: Path,
    b64_loader: Callable[[str], str],
    valid_pages: Sequence[str],
    current_page: str,
    pending_nav_key: str,
    columns_per_row: int = 3,
    section_kicker: str = "",
    section_title: str = "",
    css_data_url_mime: Optional[str] = None,
    tile_b64_revision: str = "",
) -> None:
    if not specs:
        return

    inject_top_nav_card_css()
    _inject_ai_nav_styles_for_specs(
        specs,
        set(),
        base_dir=base_dir,
        b64_loader=b64_loader,
        css_data_url_mime=css_data_url_mime,
        tile_b64_revision=tile_b64_revision,
    )

    if (section_kicker or section_title).strip():
        st.markdown(
            f'<p class="lib-topnav-section-kicker">{_escape_html(section_kicker)}</p>'
            f'<h2 class="lib-topnav-section-title">{_escape_html(section_title)}</h2>',
            unsafe_allow_html=True,
        )

    n = max(1, min(int(columns_per_row), 6))
    for i in range(0, len(specs), n):
        batch = specs[i : i + n]
        cols = st.columns(n, gap="small")
        for j in range(n):
            with cols[j]:
                if j < len(batch):
                    render_top_nav_card(
                        spec=batch[j],
                        base_dir=base_dir,
                        b64_loader=b64_loader,
                        valid_pages=valid_pages,
                        current_page=current_page,
                        pending_nav_key=pending_nav_key,
                    )
                else:
                    st.empty()


def grouped_default_top_nav_specs() -> List[Tuple[str, List[TopNavCardSpec]]]:
    by_page = {s.target_page: s for s in default_top_nav_card_specs()}
    bundles: List[Tuple[str, List[str]]] = [
        (
            "企業・ご案内",
            [
                "TOP",
                "はじめての方へ",
                "会社概要",
                "代表プロフィール",
            ],
        ),
        (
            "サービス・実績",
            ["業務内容", "業務の流れ", "実績・ケーススタディ"],
        ),
        (
            "AI・ツール・研究",
            [
                "AI分析ツール",
                "AI評価研究グループ",
                "価格の目利き",
                "不動産鑑定士マッチング",
            ],
        ),
    ]
    out: List[Tuple[str, List[TopNavCardSpec]]] = []
    for label, pages in bundles:
        specs = [by_page[p] for p in pages if p in by_page]
        if specs:
            out.append((label, specs))
    return out


def render_top_nav_card_groups(
    *,
    groups: List[Tuple[str, List[TopNavCardSpec]]],
    base_dir: Path,
    b64_loader: Callable[[str], str],
    valid_pages: Sequence[str],
    current_page: str,
    pending_nav_key: str,
    show_group_headers: bool = True,
    css_data_url_mime: Optional[str] = None,
    tile_b64_revision: str = "",
) -> None:
    if not groups:
        return
    flat_specs = [sp for _, sl in groups for sp in sl]
    featured_ids = {sl[0].card_id for _, sl in groups if len(sl) == 1}
    inject_top_nav_card_css()
    _inject_ai_nav_styles_for_specs(
        flat_specs,
        featured_ids,
        base_dir=base_dir,
        b64_loader=b64_loader,
        css_data_url_mime=css_data_url_mime,
        tile_b64_revision=tile_b64_revision,
    )
    _groups_show = [(t, s) for t, s in groups if s]
    for _gi, (group_title, specs) in enumerate(_groups_show):
        if show_group_headers:
            en = TOP_NAV_GROUP_EN.get(group_title, "SECTION")
            st.markdown(
                f"""
<div class="lib-topnav-group-panel">
  <div class="lib-topnav-group-title-row">
    <p class="lib-topnav-group-title-jp">{_escape_html(group_title)}</p>
    <p class="lib-topnav-group-title-en"><span class="lib-topnav-en-geom">{_escape_html(en)}</span></p>
  </div>
  <div class="lib-topnav-group-hr"></div>
</div>
""",
                unsafe_allow_html=True,
            )
        n = len(specs)
        if n == 1:
            _c1, _c2, _c3 = st.columns([0.22, 4.56, 0.22], gap="small")
            with _c2:
                render_top_nav_card(
                    spec=specs[0],
                    base_dir=base_dir,
                    b64_loader=b64_loader,
                    valid_pages=valid_pages,
                    current_page=current_page,
                    pending_nav_key=pending_nav_key,
                    featured=True,
                )
        else:
            cols_per = min(5, max(1, n))
            cols = st.columns(cols_per, gap="medium")
            for j in range(cols_per):
                with cols[j]:
                    if j < n:
                        render_top_nav_card(
                            spec=specs[j],
                            base_dir=base_dir,
                            b64_loader=b64_loader,
                            valid_pages=valid_pages,
                            current_page=current_page,
                            pending_nav_key=pending_nav_key,
                            featured=False,
                        )
                    else:
                        st.empty()

        if _gi < len(_groups_show) - 1:
            st.markdown(
                '<div class="lib-topnav-after-group-spacer" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )


def default_top_nav_card_specs() -> Tuple[TopNavCardSpec, ...]:
    # (card_id, title, preset, desc, image_rel, show_image_above) — 最後はカード直上に画像を出すか
    rows: List[Tuple[str, str, int, str, Optional[str], bool]] = [
        ("nav_top", "TOP", 0, "サイト全体の入り口・俯瞰", "assets/topnav/topnav-bg-top.png", True),
        (
            "nav_hajimete",
            "はじめての方へ",
            1,
            "初めての方へのご案内と読み方",
            "assets/topnav/topnav-bg-hajimete.png",
            True,
        ),
        ("nav_gyomu", "業務内容", 2, "提供領域とアプローチの要点", "assets/topnav/topnav-bg-gyomu.png", True),
        ("nav_nagare", "業務の流れ", 3, "ご依頼から成果物までのイメージ", "assets/topnav/topnav-bg-nagare.png", True),
        ("nav_ai_tools", "AI分析ツール", 4, "参考分析・ローカルデモの入口", "assets/topnav/topnav-bg-ai-tools.png", True),
        ("nav_ai_lab", "AI評価研究グループ", 5, "検証・研究の位置づけ", "assets/topnav/topnav-bg-ai-lab.png", True),
        ("nav_mekiki", "価格の目利き", 6, "価格説明支援ツール（業務用）", "assets/topnav/topnav-bg-mekiki.png", True),
        ("nav_matching", "不動産鑑定士マッチング", 7, "専門家マッチングの考え方", "assets/topnav/topnav-bg-matching.png", True),
        ("nav_cases", "実績・ケーススタディ", 8, "公開事例・スタディの入口", "assets/topnav/topnav-bg-cases.png", True),
        ("nav_kaisha", "会社概要", 9, "体制・方針の要約", "assets/topnav/topnav-bg-kaisha.png", True),
        ("nav_profile", "代表プロフィール", 10, "代表の経歴と実務の軸", "assets/topnav/topnav-bg-profile.png", True),
    ]
    out: List[TopNavCardSpec] = []
    for cid, title, preset, desc, img, show_img_above in rows:
        btn = "開く"
        out.append(
            TopNavCardSpec(
                card_id=cid,
                title=title,
                target_page=title,
                description=desc,
                image_rel=img,
                button_label=btn,
                ai_city_preset=preset,
                show_image_above=show_img_above,
            )
        )
    return tuple(out)
