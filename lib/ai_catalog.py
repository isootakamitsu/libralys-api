"""AIツールカタログ：イラスト付きカードと st.dialog 体験デモ。"""

from __future__ import annotations

import base64
import html
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

DEFAULT_DEMO_SESSION_KEY = "ai_catalog_active_demo"

# app.py の NAV_PENDING_KEY と同一（カードからサイト内ページへ遷移する際に使用）
_NAV_PENDING_KEY = "_lib_nav_pending"
# 次ランで `flush_multipage_new_tab_opener()` が親ウィンドウで新規タブを開く
_NEW_TAB_PATH_KEY = "_lib_open_multipage_new_tab_path"


def flush_multipage_new_tab_opener() -> None:
    """`open_multipage_new_tab_path` 付きカードが設定したパスを、親ウィンドウの新しいタブで開く。"""
    seg = st.session_state.pop(_NEW_TAB_PATH_KEY, None)
    if not seg:
        return
    seg = str(seg).strip().strip("/")
    if not seg:
        return
    seg_json = json.dumps(seg)
    components.html(
        f"""
<script>
(function () {{
  try {{
    var p = window.parent;
    if (!p || !p.location) return;
    var seg = {seg_json};
    var url = p.location.origin + "/" + encodeURIComponent(seg).replace(/%2F/g, "/");
    p.open(url, "_blank", "noopener,noreferrer");
  }} catch (e) {{}}
}})();
</script>
""",
        height=0,
        width=0,
    )

# サムネイル（3列用）：上はタイトル帯（1行省略）／中央〜下がグラデ＋図／最下は CTA


def inject_ai_tool_catalog_card_css() -> None:
    """ツールカタログ／ダッシュボード共通：カード直下「デモを開く」ボタンの見た目を統一。"""
    if st.session_state.get("_lib_inject_ai_tool_css"):
        return
    st.session_state["_lib_inject_ai_tool_css"] = True
    st.markdown(
        """
<style>
/* カード（iframe）の直後＝デモ／案内を開くボタン */
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="stElementContainer"]:has(iframe) + div[data-testid="stElementContainer"] [data-testid="stButton"] button,
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="element-container"]:has(iframe) + div[data-testid="element-container"] [data-testid="stButton"] button {
  width: 100% !important;
  max-width: 300px !important;
  margin-top: 8px !important;
  min-height: 2.65rem !important;
  height: auto !important;
  padding: 0.55rem 1.1rem !important;
  border-radius: 999px !important;
  font-weight: 800 !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.03em !important;
  background: linear-gradient(168deg, #1b3555 0%, #0F1C2E 48%, #0c1829 100%) !important;
  color: #f8fafc !important;
  border: 1.5px solid rgba(201, 162, 77, 0.55) !important;
  box-shadow: 0 6px 22px rgba(15, 28, 46, 0.14) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
}
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="stElementContainer"]:has(iframe) + div[data-testid="stElementContainer"] [data-testid="stButton"] button:hover,
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="element-container"]:has(iframe) + div[data-testid="element-container"] [data-testid="stButton"] button:hover {
  border-color: #C9A24D !important;
  box-shadow: 0 8px 26px rgba(201, 162, 77, 0.22) !important;
  filter: brightness(1.06);
}
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="stElementContainer"]:has(iframe) + div[data-testid="stElementContainer"] [data-testid="stButton"] button:focus-visible,
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="element-container"]:has(iframe) + div[data-testid="element-container"] [data-testid="stButton"] button:focus-visible {
  outline: 2px solid #C9A24D !important;
  outline-offset: 2px !important;
}
/* 画像フォールバック（プレースホルダ）直後も同型 */
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="stElementContainer"]:has(.ai-tool-card-fallback) + div[data-testid="stElementContainer"] [data-testid="stButton"] button,
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="element-container"]:has(.ai-tool-card-fallback) + div[data-testid="element-container"] [data-testid="stButton"] button {
  width: 100% !important;
  max-width: 300px !important;
  margin-top: 8px !important;
  min-height: 2.65rem !important;
  height: auto !important;
  padding: 0.55rem 1.1rem !important;
  border-radius: 999px !important;
  font-weight: 800 !important;
  font-size: 0.9rem !important;
  letter-spacing: 0.03em !important;
  background: linear-gradient(168deg, #1b3555 0%, #0F1C2E 48%, #0c1829 100%) !important;
  color: #f8fafc !important;
  border: 1.5px solid rgba(201, 162, 77, 0.55) !important;
  box-shadow: 0 6px 22px rgba(15, 28, 46, 0.14) !important;
}
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="stElementContainer"]:has(.ai-tool-card-fallback) + div[data-testid="stElementContainer"] [data-testid="stButton"] button:hover,
[data-testid="column"] div[data-testid="stVerticalBlock"] div[data-testid="element-container"]:has(.ai-tool-card-fallback) + div[data-testid="element-container"] [data-testid="stButton"] button:hover {
  border-color: #C9A24D !important;
  box-shadow: 0 8px 26px rgba(201, 162, 77, 0.22) !important;
  filter: brightness(1.06);
}
</style>
""",
        unsafe_allow_html=True,
    )


def _ai_tool_open_action_label(proj: Dict[str, Any]) -> Tuple[str, str]:
    """（ボタン表記, help）"""
    name = (proj.get("name") or "ツール").strip()
    if proj.get("open_multipage_new_tab_path"):
        return (
            "▶ 案内ページを開く（新しいタブ）",
            f"{name}：案内ページを別タブで開き、地図ダッシュボードへ進みます。",
        )
    if proj.get("navigate_to_page"):
        return (
            f"▶ {name} を開く",
            f"{name} の本番ページへ移動します。",
        )
    return (
        "▶ 体験デモを開く",
        f"{name} のブラウザ内デモを開きます。",
    )


_THUMB_W = 300
_THUMB_IMG_H = 200
_THUMB_FOOTER_H = 32
_TEXT_BAND_H = 46


def _reveal_catalog_cmd(keypfx: str) -> None:
    st.session_state[f"{keypfx}catalog_cmd_exp"] = True
    st.session_state[f"{keypfx}catalog_scroll_pending"] = True


def _font_paths() -> List[Path]:
    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    fonts = windir / "Fonts"
    return [
        fonts / "meiryo.ttc",
        fonts / "msgothic.ttc",
        fonts / "YuGothM.ttc",
        fonts / "arial.ttf",
    ]


def _font_paths_catalog() -> List[Path]:
    """
    カード PNG 内の日本語描画用フォント探索順。

    Streamlit Cloud（Linux）では Windows の Fonts が無く、ここで失敗すると
    ``load_default()`` になり日本語が豆腐／化けする。リポジトリ同梱の Noto を最優先する。
    """
    paths: List[Path] = []
    repo_root = Path(__file__).resolve().parent.parent
    paths.append(repo_root / "fonts" / "NotoSansJP-VF.ttf")

    paths.extend(
        [
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto-cjk/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf"),
        ]
    )

    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    win_fonts = windir / "Fonts"
    paths.extend(
        [
            win_fonts / "msgothic.ttc",
            win_fonts / "YuGothM.ttc",
            win_fonts / "YuGothR.ttc",
            win_fonts / "meiryob.ttc",
            win_fonts / "meiryo.ttc",
            win_fonts / "arial.ttf",
        ]
    )
    return paths


def _text_px_width(draw: Any, text: str, font: Any) -> float:
    if not text:
        return 0.0
    try:
        return float(draw.textlength(text, font=font))
    except (AttributeError, TypeError):
        bbox = draw.textbbox((0, 0), text, font=font)
        return float(bbox[2] - bbox[0])


def _truncate_one_line(draw: Any, text: str, font: Any, max_w: float) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if _text_px_width(draw, t, font) <= max_w:
        return t
    ell = "…"
    while len(t) > 0 and _text_px_width(draw, t + ell, font) > max_w:
        t = t[:-1]
    return t + ell if t else ell


def _illustration_ai03(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """鑑定書・文書イメージ（アート領域の下寄せ）"""
    h_art = max(1, y_bot - y_top)
    pad = max(14, int(w * 0.07))
    pw = w - pad * 2
    ph = min(int(h_art * 0.72), h_art - 12)
    y0 = y_bot - 10 - ph
    if y0 < y_top + 4:
        y0 = y_top + 4
        ph = max(20, y_bot - 10 - y0)
    try:
        draw.rounded_rectangle([pad, y0, pad + pw, y0 + ph], radius=14, fill=(245, 248, 252))
        draw.rounded_rectangle([pad, y0, pad + pw, y0 + ph], radius=14, outline=(201, 162, 77), width=3)
    except AttributeError:
        draw.rectangle([pad, y0, pad + pw, y0 + ph], fill=(245, 248, 252), outline=(201, 162, 77), width=3)
    inner = pad + 22
    line_step = max(16, min(22, ph // 6))
    for i in range(5):
        yy = y0 + 24 + i * line_step
        if yy > y0 + ph - 8:
            break
        draw.line([(inner, yy), (pad + pw - 22, yy)], fill=(148, 163, 184), width=2)
    draw.rectangle([inner, y0 + 16, inner + 76, y0 + 28], fill=(201, 162, 77))


def _illustration_ai04(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """棒グラフ・DCF（下辺基準）"""
    h_art = max(1, y_bot - y_top)
    margin = 6
    base = y_bot - margin
    bh = min(int(h_art * 0.58), h_art - 12)
    by = base - bh
    if by < y_top + 4:
        by = y_top + 4
        bh = base - by
    bx = int(w * 0.1)
    bw = int(w * 0.8)
    vals = [0.35, 0.55, 0.45, 0.75, 0.5]
    n = len(vals)
    gap = max(4, int(w * 0.028))
    bar_w = max(8, (bw - gap * (n + 1)) // n)
    x = bx + gap
    for v in vals:
        bh_i = max(4, int(bh * v))
        top_y = max(by + 1, base - bh_i)
        draw.rectangle([x, top_y, x + bar_w, base], fill=(201, 162, 77))
        x += bar_w + gap
    draw.line([(bx, base), (bx + bw, base)], fill=(226, 232, 240), width=2)


def _illustration_ai05(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """事例DB・グリッド（下寄せ）"""
    cw = max(14, int(w * 0.09))
    ch = max(11, int(w * 0.068))
    gap = max(3, int(w * 0.02))
    rows, cols = 4, 8
    grid_h = rows * ch + (rows - 1) * gap
    gy = y_bot - 8 - grid_h
    if gy < y_top + 4:
        gy = y_top + 4
    gx = int(w * 0.08)
    for row in range(rows):
        for col in range(cols):
            cx = gx + col * (cw + gap)
            cy = gy + row * (ch + gap)
            if cy + ch > y_bot - 4:
                continue
            fill = (30, 58, 95) if (row + col) % 3 else (55, 90, 130)
            draw.rectangle([cx, cy, cx + cw, cy + ch], fill=fill, outline=(201, 162, 77), width=1)


def _illustration_ai06(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """収益・階段状積み上げ（下から積む）"""
    h_art = max(1, y_bot - y_top)
    cx = w // 2
    base = y_bot - 8
    max_rw = int(w * 0.72)
    widths = [int(max_rw * 0.45), int(max_rw * 0.6), int(max_rw * 0.78), max_rw]
    hh = max(10, min(int(h_art * 0.16), 26))
    gap = 5
    for i, rw in enumerate(widths):
        y1 = base - i * (hh + gap)
        y0s = y1 - hh
        if y0s < y_top + 2:
            break
        x0 = max(4, cx - rw // 2)
        x1 = min(w - 4, x0 + rw)
        draw.rectangle([x0, y0s, x1, y1], fill=(129, 140, 248), outline=(201, 162, 77), width=1)


def _illustration_ai07(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """再開発・クレーン風シルエット（地面を y_bot 付近に）"""
    ground = y_bot - 8
    h_art = max(1, y_bot - y_top)
    bh1 = min(int(h_art * 0.42), ground - y_top - 6)
    bh2 = min(int(h_art * 0.52), ground - y_top - 6)
    x1a, x1b = int(w * 0.18), int(w * 0.38)
    y1t = max(y_top + 4, ground - bh1)
    draw.rectangle([x1a, y1t, x1b, ground], fill=(71, 85, 105))
    x2a, x2b = int(w * 0.52), int(w * 0.74)
    y2t = max(y_top + 4, ground - bh2)
    draw.rectangle([x2a, y2t, x2b, ground], fill=(100, 116, 139))
    tip_y = max(y_top + 10, y2t - int(h_art * 0.38))
    lw = max(2, int(w * 0.012))
    draw.line([(x2b, y2t), (int(w * 0.86), tip_y)], fill=(201, 162, 77), width=lw)
    draw.line([(int(w * 0.86), tip_y), (int(w * 0.93), min(ground - 4, tip_y + int(h_art * 0.12)))], fill=(201, 162, 77), width=lw)


def _illustration_ai08(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """時系列ライン（下辺を基準に振れる）"""
    rng = np.random.default_rng(8)
    h_art = max(1, y_bot - y_top)
    base_y = y_bot - 10
    amp = min(34, max(12, int(h_art * 0.38)))
    pts = []
    for i in range(24):
        x = int(w * 0.1 + (w * 0.8) * i / 23)
        y = int(base_y - amp * np.sin(i / 3.5) + rng.normal(0, 4))
        y = max(y_top + 6, min(base_y - 2, y))
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(125, 211, 252), width=3)
    for p in pts[::3]:
        r = max(3, int(w * 0.014))
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(201, 162, 77))


def _illustration_ai09(draw: Any, w: int, y_top: int, y_bot: int) -> None:
    """公的価格・区域の色分け（コロプレス）＋路線・地点の地図マッピング風イメージ。"""
    h_art = max(1, y_bot - y_top)
    mx0, mx1 = int(w * 0.06), int(w * 0.94)
    my0, my1 = y_top + 4, y_bot - 4
    draw.rectangle([mx0, my0, mx1, my1], fill=(14, 52, 68), outline=(56, 118, 138), width=1)
    # 幹線道路（地図上のライン）
    draw.line([(mx0, my0 + h_art // 3), (mx1, my0 + h_art // 3)], fill=(130, 148, 168), width=2)
    draw.line([(mx0 + w // 2, my0), (mx0 + w // 2, my1)], fill=(110, 132, 155), width=2)
    draw.line([(mx0 + int(w * 0.12), my1 - 6), (mx1 - int(w * 0.08), my0 + int(h_art * 0.55))], fill=(118, 136, 158), width=1)
    # 区域メッシュ（変動率の段階色イメージ）
    nx, ny = 7, 5
    gap = max(1, int(w * 0.008))
    aw = max(4, (mx1 - mx0 - gap * (nx + 1)) // nx)
    ah = max(4, (my1 - my0 - gap * (ny + 1)) // ny)
    palette = [
        (22, 78, 62),
        (32, 105, 82),
        (48, 128, 98),
        (28, 88, 108),
        (55, 118, 72),
        (38, 95, 115),
        (62, 132, 88),
    ]
    for r in range(ny):
        for c in range(nx):
            x0 = mx0 + gap + c * (aw + gap)
            y0 = my0 + gap + r * (ah + gap)
            x1 = min(mx1 - gap, x0 + aw)
            y1 = min(my1 - gap, y0 + ah)
            if x1 <= x0 or y1 <= y0:
                continue
            idx = (r * 11 + c * 7) % len(palette)
            draw.rectangle([x0, y0, x1, y1], fill=palette[idx], outline=(20, 60, 75), width=1)
    # 公示地点・ピン（ゴールド）
    pin_xy = [(0.24, 0.38), (0.58, 0.32), (0.72, 0.55), (0.42, 0.68), (0.82, 0.72)]
    for px, py in pin_xy:
        cx = int(mx0 + (mx1 - mx0) * px)
        cy = int(my0 + (my1 - my0) * py)
        pr = max(3, int(w * 0.014))
        draw.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=(201, 162, 77), outline=(248, 250, 252), width=1)
        draw.line([(cx, cy + pr), (cx, cy + pr + max(4, ah // 2))], fill=(201, 162, 77), width=2)


def _dispatch_illustration(draw: Any, w: int, y_top: int, y_bot: int, slug: str) -> None:
    if slug == "ai03":
        _illustration_ai03(draw, w, y_top, y_bot)
    elif slug == "ai04":
        _illustration_ai04(draw, w, y_top, y_bot)
    elif slug == "ai05":
        _illustration_ai05(draw, w, y_top, y_bot)
    elif slug == "ai06":
        _illustration_ai06(draw, w, y_top, y_bot)
    elif slug == "ai07":
        _illustration_ai07(draw, w, y_top, y_bot)
    elif slug == "ai09":
        _illustration_ai09(draw, w, y_top, y_bot)
    else:
        _illustration_ai08(draw, w, y_top, y_bot)


def _draw_card_illustration(
    draw: Any, w: int, h: int, slug: str, *, text_band_h: Optional[int] = None
) -> None:
    palettes = {
        "ai03": ((30, 41, 59), (15, 23, 42)),
        "ai04": ((6, 78, 59), (15, 40, 35)),
        "ai05": ((30, 27, 75), (49, 46, 129)),
        "ai06": ((49, 46, 129), (30, 27, 75)),
        "ai07": ((67, 20, 7), (30, 27, 23)),
        "ai08": ((12, 74, 110), (15, 23, 42)),
        "ai09": ((12, 62, 78), (8, 42, 55)),
    }
    top, bot = palettes.get(slug, ((15, 23, 42), (30, 41, 59)))
    tbh = _TEXT_BAND_H if text_band_h is None else max(0, int(text_band_h))
    fh = _THUMB_FOOTER_H
    yb = h - fh
    if tbh > 0:
        draw.rectangle([0, 0, w, tbh], fill=(15, 23, 42))
    art_top, art_bot = tbh, yb
    h_art = max(1, art_bot - art_top)
    for iy in range(h_art):
        y = art_top + iy
        t = iy / max(h_art - 1, 1)
        r = int(top[0] * (1 - t) + bot[0] * t)
        g = int(top[1] * (1 - t) + bot[1] * t)
        b = int(top[2] * (1 - t) + bot[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    _dispatch_illustration(draw, w, art_top, art_bot, slug)
    draw.rectangle([0, yb, w, h], fill=(15, 23, 42))
    draw.rectangle([0, yb, w, yb + 4], fill=(201, 162, 77))


def generate_catalog_thumbnail(
    proj: Dict[str, Any], *, text_overlay: bool = True
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    ツール別グラデ＋イラスト。`text_overlay=True` のとき上帯に名称・概要、下帯に CTA。
    `text_overlay=False` は画像ファイル用（カード上に名称を HTML で出すとき）。

    Returns
    -------
    (png_bytes, font_warning)
        font_warning … 日本語非対応フォントにフォールバックしたときの UI 向けメッセージ（テキスト描画時のみ）。
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, None

    w, h = _THUMB_W, _THUMB_IMG_H
    img = Image.new("RGB", (w, h), "#0F1C2E")
    draw = ImageDraw.Draw(img)
    slug = proj.get("key_slug", "ai08")
    _draw_card_illustration(draw, w, h, slug, text_band_h=0 if not text_overlay else None)

    if not text_overlay:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), None

    font_title = font_tag = font_cta = None
    cjk_font_ok = False
    for fp in _font_paths_catalog():
        if fp.is_file():
            try:
                font_title = ImageFont.truetype(str(fp), 18)
                font_tag = ImageFont.truetype(str(fp), 12)
                font_cta = ImageFont.truetype(str(fp), 11)
                cjk_font_ok = True
                break
            except OSError:
                continue
    if font_title is None:
        font_title = font_tag = font_cta = ImageFont.load_default()

    font_warn: Optional[str] = None
    if not cjk_font_ok:
        font_warn = (
            "日本語対応フォントが見つかりません。カード画像の文字が化けることがあります。"
            "リポジトリに `fonts/NotoSansJP-VF.ttf` を含めてデプロイしてください。"
        )

    mx = 10
    max_txt = float(w - mx * 2)
    title_s = _truncate_one_line(draw, proj.get("name", ""), font_title, max_txt)
    draw.text((mx, 7), title_s, fill=(248, 250, 252), font=font_title)
    tag_src = (proj.get("tagline") or "").strip()
    if not tag_src:
        tag_src = (proj.get("summary") or "").strip()
    tag_s = _truncate_one_line(draw, tag_src, font_tag, max_txt)
    draw.text((mx, 29), tag_s, fill=(203, 213, 225), font=font_tag)

    yb = h - _THUMB_FOOTER_H
    if proj.get("open_multipage_new_tab_path"):
        cta = "クリックで案内"
    elif proj.get("navigate_to_page"):
        cta = "クリックで本番"
    else:
        cta = "クリックでデモ"
    draw.text((mx, yb + 10), cta, fill=(201, 162, 77), font=font_cta)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), font_warn


def ai_tool_card_image_dir() -> Path:
    """カード用画像（AI生成または自動フォールバック）の保存先。リポジトリの `image/`。"""
    return Path(__file__).resolve().parent.parent / "image"


def _png_bytes_for_card_embed(png: bytes) -> bytes:
    """高解像度の AI 画像を iframe 用に幅優先で縮小（オリジナルファイルは変更しない）。"""
    if len(png) < 180_000:
        return png
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(png)).convert("RGB")
        w, h = im.size
        target_w = min(640, max(_THUMB_W, int(w * 0.5)))
        if w > target_w:
            nh = max(1, int(h * (target_w / float(w))))
            im = im.resize((target_w, nh), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        im.save(out, format="PNG", optimize=True)
        return out.getvalue()
    except Exception:
        return png


def get_ai_tool_card_png_bytes(proj: Dict[str, Any]) -> Tuple[Optional[bytes], Optional[str]]:
    """
    `image/ai_tool_{key_slug}.png` を読む。無ければテキストなしサムネを生成して同パスへ保存。
    差し替え用に同名 PNG を `image/` に置けばその画像が使われる。
    """
    slug = proj.get("key_slug", "ai08")
    d = ai_tool_card_image_dir()
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    path = d / f"ai_tool_{slug}.png"
    if path.is_file() and path.stat().st_size > 64:
        try:
            raw = path.read_bytes()
            return _png_bytes_for_card_embed(raw), None
        except OSError:
            pass
    png, fw = generate_catalog_thumbnail(proj, text_overlay=False)
    if png:
        try:
            path.write_bytes(png)
        except OSError:
            pass
    return (_png_bytes_for_card_embed(png) if png else None), fw


def _emit_thumbnail_font_warning_once(msg: Optional[str]) -> None:
    """同一セッションでカード枚数分の警告が重複しないようにする。"""
    if not msg:
        return
    key = "_lib_ai_catalog_font_warning_shown"
    if st.session_state.get(key):
        return
    st.warning(msg)
    st.session_state[key] = True


def _format_cmd_block(proj: Dict[str, Any]) -> str:
    if not proj.get("private_full_launch_available"):
        return (
            "# フル版の作業フォルダと起動コマンドは、公開リポジトリには含めていません。\n"
            "# 契約・お問い合わせ後に、Streamlit Secrets（例: [ai_tools_private.ai03]）など限定配布でご案内します。"
        )
    lines = [f'cd "{proj["path"]}"']
    for line in proj.get("setup_cmds") or []:
        if str(line).strip():
            lines.append(str(line).strip())
    for line in proj.get("run_cmds") or []:
        if str(line).strip():
            lines.append(str(line).strip())
    return "\n".join(lines)


def try_launch_local_streamlit_app(
    proj: Dict[str, Any], *, run_setup: bool = False
) -> Tuple[bool, str]:
    """
    Windows: 一時 .bat 経由で新しい cmd ウィンドウを開き streamlit を起動。
    それ以外: shlex 分割した streamlit を cwd でバックグラウンド起動。
    """
    raw = proj.get("path")
    if raw is None:
        return (
            False,
            "プロジェクトパスが未設定です。`.streamlit/secrets.toml`（またはホストの Secrets）の `[ai_tools_private.<ツールの key_slug>]` に `path` を設定してください。",
        )
    cwd = Path(str(raw))
    if not cwd.is_dir():
        return (
            False,
            "ツール用フォルダが見つかりません。Secrets の `path` がこのPC上の実フォルダと一致しているか確認してください。"
            f"\n\n現在の指定: `{cwd}`",
        )
    run_cmds = proj.get("run_cmds") or []
    if not run_cmds:
        return False, "起動コマンド（run_cmds）が定義されていません。"
    entry = str(run_cmds[0]).strip()
    if not re.match(r"streamlit\s+run\s+", entry, re.I):
        return (
            False,
            "自動起動は `streamlit run …` の行のみ対応です。下の「フル版の起動コマンド」を PowerShell に貼り付けて実行してください。",
        )
    toks = shlex.split(entry, posix=os.name != "nt")
    if len(toks) < 3 or toks[0].lower() != "streamlit" or toks[1].lower() != "run":
        return False, "起動行を解釈できませんでした。手動でコマンドを実行してください。"
    script_name = toks[2]
    script_path = cwd / script_name
    if not script_path.is_file():
        return (
            False,
            f"スクリプトが見つかりません: `{script_path}`\nフォルダ構成を確認するか、手動で起動してください。",
        )
    if shutil.which("streamlit") is None:
        return (
            False,
            "`streamlit` が PATH にありません。Anaconda／venv を有効にするか、Python の `Scripts` を PATH に追加してください。",
        )

    if sys.platform == "win32":
        # NOTE: `start "title" cmd.exe /k ...` は環境によって title を実行ファイル名と誤解釈し
        # 「Streamlit-ai03 が見つかりません」等になる。start を使わず CREATE_NEW_CONSOLE で直接起動する。
        lines = ["@echo off", f'cd /d "{cwd}"']
        if run_setup:
            for c in proj.get("setup_cmds") or []:
                cs = str(c).strip()
                if cs:
                    lines.append(cs)
        lines.append(entry)
        bat_body = "\r\n".join(lines) + "\r\n"
        fd, bat_path = tempfile.mkstemp(suffix="_streamlit_run.bat", text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\r\n") as bf:
                bf.write(bat_body)
            bat_path_norm = str(Path(bat_path).resolve())
            subprocess.Popen(
                ["cmd.exe", "/k", bat_path_norm],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True,
            )
        except OSError as e:
            return False, f"起動に失敗しました: {e}"
        return (
            True,
            "新しいコンソールで起動しました。表示された URL（例: http://localhost:8501）をブラウザで開いてください。",
        )

    env = os.environ.copy()
    pre: list[str] = []
    if run_setup:
        for c in proj.get("setup_cmds") or []:
            cs = str(c).strip()
            if cs:
                pre.append(cs)
    shell_cmd = " && ".join(pre + [entry]) if pre else entry
    try:
        subprocess.Popen(
            ["/bin/sh", "-c", shell_cmd],
            cwd=str(cwd),
            env=env,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as e:
        return False, f"起動に失敗しました: {e}"
    return (
        True,
        "バックグラウンドで起動しました。ターミナルで URL を確認するか、ブラウザで localhost を開いてください。",
    )


_CARD_HTML_TITLE_MIN_H = 46


def _render_clickable_ai_tool_card(png: bytes, proj: Dict[str, Any], key_prefix: str) -> None:
    """名称帯＋画像を1枚のカードにし、クリックで同一カラム内の非表示トリガーボタンを発火。"""
    b64 = base64.standard_b64encode(png).decode("ascii")
    slug = proj.get("key_slug", "")
    safe_dom_id = re.sub(r"[^a-zA-Z0-9_]", "_", f"cat_{key_prefix}{slug}")[:80]
    wrap_id = f"{safe_dom_id}_wrap"
    if proj.get("open_multipage_new_tab_path"):
        act = "案内ページを新しいタブで開く（のち地図へ）"
    elif proj.get("navigate_to_page"):
        act = "本番ページへ移動"
    else:
        act = "体験デモを開く"
    badge = html.escape((proj.get("id") or "").strip())
    name = html.escape((proj.get("name") or "ツール").strip())
    badge_html = f'<span style="color:#C9A24D;font-weight:900;margin-right:8px;letter-spacing:0.02em;">{badge}</span>' if badge else ""
    html_page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body style="margin:0;padding:0;">
<div id="{wrap_id}" role="link" tabindex="0" title="{html.escape(act)}"
  style="max-width:{_THUMB_W}px;cursor:pointer;border-radius:12px;overflow:hidden;
  border:1px solid rgba(15,28,46,0.14);box-shadow:0 10px 28px rgba(15,28,46,0.08);box-sizing:border-box;background:#0F1C2E;">
  <div style="min-height:{_CARD_HTML_TITLE_MIN_H}px;padding:12px 14px 10px 14px;
    font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:0.98rem;font-weight:800;
    color:#f8fafc;line-height:1.35;word-break:break-word;">
    {badge_html}<span>{name}</span>
  </div>
  <img id="{safe_dom_id}" src="data:image/png;base64,{b64}" alt=""
    style="width:100%;height:{_THUMB_IMG_H}px;object-fit:cover;display:block;vertical-align:top;"/>
</div>
<script>
(function() {{
  function go() {{
    try {{
      var iframe = window.frameElement;
      if (!iframe || !iframe.parentElement) return;
      var col = iframe.closest("[data-testid=\\"column\\"]");
      if (!col) return;
      var buttons = col.querySelectorAll("button");
      if (!buttons.length) return;
      buttons[buttons.length - 1].click();
    }} catch (e) {{}}
  }}
  var w = document.getElementById("{wrap_id}");
  if (w) {{
    w.addEventListener("click", go);
    w.addEventListener("keydown", function (ev) {{
      if (ev.key === "Enter" || ev.key === " ") {{ ev.preventDefault(); go(); }}
    }});
  }}
}})();
</script>
</body></html>"""
    components.html(html_page, height=_CARD_HTML_TITLE_MIN_H + _THUMB_IMG_H + 14, scrolling=False)


def render_inline_demo(proj: Dict[str, Any], *, inside_dialog: bool = False) -> None:
    """各ツールの簡易インタラクティブ（ツールカタログ／ダッシュボードと同型の見出し・caption・段間）。"""
    slug = proj["key_slug"]
    if not inside_dialog:
        st.subheader(f"{proj['name']} — 体験デモ")
        st.caption(
            "この画面は **ブラウザだけで触れる簡易デモ** です。本番の画面・データ連携は、"
            "手元のPCにツール用フォルダを置き **フル版** で起動してください。"
        )
        st.markdown('<div style="height:10px" aria-hidden="true"></div>', unsafe_allow_html=True)

    keypfx = f"dlg_{slug}_" if inside_dialog else f"{slug}_"
    anchor_id = f"catalog-cmd-{'dlg' if inside_dialog else 'page'}-{slug}"

    if inside_dialog:
        if proj.get("private_full_launch_available"):
            st.markdown("##### フル版の起動")
            st.caption(
                "このPCにツール用フォルダと **Python（streamlit が PATH で使える状態）** があるとき、"
                "別ウィンドウのコンソールから起動できます。"
            )
            run_setup = False
            if proj.get("setup_cmds"):
                run_setup = st.checkbox(
                    "初回のみ: setup_cmds（例: pip install）を実行してから起動",
                    key=f"{keypfx}run_setup_first",
                    value=False,
                )
            lc1, lc2 = st.columns(2)
            with lc1:
                if st.button(
                    "フル版を起動（新しいコンソール）",
                    key=f"{keypfx}launch_full",
                    type="primary",
                    width="stretch",
                ):
                    ok, msg = try_launch_local_streamlit_app(proj, run_setup=run_setup)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            with lc2:
                if st.button(
                    "起動コマンドだけ表示",
                    key=f"{keypfx}open_cmd_strip",
                    type="secondary",
                    width="stretch",
                ):
                    _reveal_catalog_cmd(keypfx)
            st.markdown('<div style="height:8px" aria-hidden="true"></div>', unsafe_allow_html=True)
        else:
            st.markdown("##### フル版について")
            with st.expander("フル版について（詳細）", expanded=False):
                st.info(
                    "ローカルで動かす **フル版** のフォルダパスと起動コマンドは、公開リポジトリには載せていません。"
                    " 契約・限定配布では `.streamlit/secrets.toml` の `[ai_tools_private.<key_slug>]`（例: `ai04`）に `path` と `run_cmds` を置くと、この画面に起動用の案内が現れます。"
                )
            st.markdown('<div style="height:8px" aria-hidden="true"></div>', unsafe_allow_html=True)

    if proj["key_slug"] == "ai03":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    """
**この体験デモでできること**
- 論点・物件の要点をメモしたうえで、**鑑定評価書の章立てのたたき台（固定の例）**をすぐに眺める

**フル版（ローカル）で想定されること**
- 入力フォームや文章化など、アプリ本体の画面に沿った作業（フォルダと環境の準備が必要）

**できないこと**
- 公的な鑑定評価書の完成原稿の自動作成、価格や適否の断定（本サイトは参考分析です）
""".strip()
                )
        topic = st.text_input("評価・鑑定の論点・物件の要点（例）", key=f"{keypfx}topic")
        if st.button(
            "章立てのたたき台（参考）を表示",
            key=f"{keypfx}go",
            type="primary",
            width="stretch",
        ):
            st.session_state[f"{keypfx}show_outline"] = True
            _reveal_catalog_cmd(keypfx)

        if st.session_state.get(f"{keypfx}show_outline"):
            st.markdown(
                f"""
**（参考・自動生成ではありません）たたき台イメージ**

1. 評価目的・価格定義  
2. 対象不動産の概要（所在地・用途・権利）  
3. 最有効使用の整理  
4. 手法の選択理由（比較・収益・原価の関係）  
5. 補正・整合性のポイント  
6. 前提条件・限界の明示  

入力メモ: {topic or '（未入力）'}
"""
            )

    elif proj["key_slug"] == "ai04":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**体験デモ**はブラウザ内の簡易 DCF／DC 試算です。**フル版**は配布環境の収益試算・表計算・画面一式です。"
                )
            from lib.shisanhyo_dcf_demo import render_shisanhyo_embedded_dcf_dashboard

            render_shisanhyo_embedded_dcf_dashboard(show_page_anchor=False)
        else:
            st.info(
                "**入力／結果（DCF／DC）／留意点** のブラウザ試算は、"
                "ページ上部 **ダッシュボード** または **ツールカタログ**のカード画像から開く **ツール体験デモ** 内でご利用ください。"
            )

    elif proj["key_slug"] == "ai09":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**このサイト内**では、ダッシュボード右のカードから **新しいタブ**で **案内ページ → 地図** に進めます。"
                    " 地図を **別ポートの単体 Streamlit** として開く手順は、限定配布の Secrets に記載がある場合にのみ案内します。"
                )
        else:
            st.info(
                "**公的価格変動ダッシュボード**は、ページ上部 **ダッシュボード**右の**カード**（画像またはボタン）で **新しいタブ** の **案内ページ**を開くか、"
                "左サイドバーの **Streamlit ページ一覧** から **chika_map_intro**（案内）→ **chika_pydeck_dashboard**（地図）の順で移動できます（ツールカタログのグリッドには含みません）。"
            )

    elif proj["key_slug"] == "ai05":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**体験デモ**は事例数のイメージだけです。**フル版**は配布フォルダ内の Streamlit で、収集・DB 登録まわりの画面を使います。"
                )
        n = st.slider("登録想定事例数（イメージ）", 10, 500, 120, key=f"{keypfx}n")
        st.metric("インデックス化イメージ", f"{n} 件")
        st.dataframe(
            {
                "エリア": ["A区", "B区", "C区"],
                "件数イメージ": [n // 3, n // 3, n - 2 * (n // 3)],
            },
            width="stretch",
            hide_index=True,
        )
        if st.button(
            "事例イメージのあとで起動コマンドへ",
            key=f"{keypfx}to_cmd",
            type="secondary",
            width="stretch",
        ):
            _reveal_catalog_cmd(keypfx)

    elif proj["key_slug"] == "ai06":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**体験デモ**は還元価格のイメージ計算のみ。**フル版**は Income Intelligence の画面で、収益分析の詳細を扱います。"
                )
        egi = st.number_input("年間賃料収入イメージ（万円/年）", 100.0, 50000.0, 4800.0, key=f"{keypfx}egi")
        margin = st.slider("経費控除後マージン（%）", 40.0, 85.0, 62.0, key=f"{keypfx}m")
        cap = st.slider("利回り（%）", 3.0, 8.0, 4.8, 0.1, key=f"{keypfx}cap2")
        noi = egi * 10000 * (margin / 100.0)
        v = noi / (cap / 100.0)
        st.metric("還元価格イメージ", f"¥{v:,.0f}")
        if st.button(
            "試算結果から起動コマンドへ",
            key=f"{keypfx}to_cmd",
            type="secondary",
            width="stretch",
        ):
            _reveal_catalog_cmd(keypfx)

    elif proj["key_slug"] == "ai07":
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**体験デモ**はシナリオの説明のみ。**フル版**は再開発ダッシュボードの Streamlit で、表・指標の入力・閲覧ができます。"
                )
        scen = st.selectbox(
            "再開発シナリオ（例）",
            ["住商混合の再編", "老朽建替え＋賃料再設定", "容積移転・権利調整"],
            key=f"{keypfx}scen",
        )
        st.info(f"「{scen}」では、収益・期間・リスクを分けてシナリオ表に落とすのが一般的です（デモは説明のみ）。")
        if st.button(
            "シナリオ確認後、起動コマンドへ",
            key=f"{keypfx}to_cmd",
            type="secondary",
            width="stretch",
        ):
            _reveal_catalog_cmd(keypfx)

    else:
        if inside_dialog:
            with st.expander("体験デモとフル版の違い（詳細）", expanded=False):
                st.info(
                    "**体験デモ**はダミーの時系列チャートのみ。**フル版**は市場指数・DCF 関連のデータ管理ダッシュボードです。"
                )
        rng = np.random.default_rng(42)
        t = np.arange(0, 24)
        y = 100 + np.cumsum(rng.normal(0, 1.2, len(t)))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=y, mode="lines", name="指数イメージ"))
        fig.update_layout(
            title="時系列・指数の見え方（ダミーデータ）",
            height=320,
            paper_bgcolor="#F7F5F2",
            plot_bgcolor="#F7F5F2",
        )
        st.plotly_chart(fig, width="stretch")
        st.caption("実データではなく形状のイメージです。")
        if st.button(
            "チャート確認後、起動コマンドへ",
            key=f"{keypfx}to_cmd",
            type="secondary",
            width="stretch",
        ):
            _reveal_catalog_cmd(keypfx)

    st.markdown(
        f'<div id="{anchor_id}" style="scroll-margin-top:12px;height:1px;"></div>',
        unsafe_allow_html=True,
    )
    cmd_exp = st.session_state.get(f"{keypfx}catalog_cmd_exp", False)
    with st.expander("フル版の起動コマンド（詳細・手動コピー用）", expanded=cmd_exp):
        if proj.get("private_full_launch_available"):
            st.caption("ダイアログ上部の **フル版を起動** で自動起動できる場合は、ここを開かなくて構いません。")
        else:
            st.caption("実パスとコマンドは Secrets の `ai_tools_private` にある場合のみ表示されます（公開リポジトリには含めません）。")
        st.code(_format_cmd_block(proj), language="powershell")
        if proj.get("notes"):
            st.caption(proj["notes"])
        st.markdown(
            "**専門的な依頼・正式な評価**については、サイドバー「お問い合わせ」からご相談ください。"
        )

    if st.session_state.pop(f"{keypfx}catalog_scroll_pending", None):
        components.html(
            f"""
<script>
const el = window.parent.document.getElementById("{anchor_id}");
if (el) el.scrollIntoView({{behavior: "smooth", block: "start"}});
</script>
""",
            height=0,
            width=0,
        )


@st.dialog("ツール体験デモ", width="large")
def open_tool_demo_dialog(project: Dict[str, Any]) -> None:
    """メイン画面はそのまま。モーダル上でデモのみ開始（ページ先頭へジャンプしない）。

    ツールカタログ／ダッシュボードと同型：subheader → caption → 操作 → 10px → 本体。
    """
    st.subheader("ツール体験デモ")
    _dlg_cap = (
        f"**{project['name']}** — まず **体験デモ** でイメージを確認できます。"
        + (
            " 併せて **フル版を起動** もご利用ください。"
            if project.get("private_full_launch_available")
            else " **フル版**のパス・起動手順は公開リポジトリには載せておらず、契約先には Secrets 等で個別設定します。"
        )
        + " このパネルはブラウザ内の**簡易イメージ**です。**×** または **カタログに戻る** で閉じます。"
    )
    st.caption(_dlg_cap)
    if st.button("カタログに戻る", type="primary", width="stretch", key=f"dlg_back_{project['key_slug']}"):
        st.rerun()
    st.markdown('<div style="height:10px" aria-hidden="true"></div>', unsafe_allow_html=True)
    render_inline_demo(project, inside_dialog=True)


def _open_tool_demo_dialog_fresh(proj: Dict[str, Any]) -> None:
    """ダイアログを開く直前に dlg_{slug}_ のウィジェット状態を消してから表示する。"""
    pfx = f"dlg_{proj['key_slug']}_"
    for k in list(st.session_state.keys()):
        if isinstance(k, str) and k.startswith(pfx):
            del st.session_state[k]
    open_tool_demo_dialog(proj)


def _open_project_from_catalog(proj: Dict[str, Any]) -> None:
    """マルチページ URL を新規タブで開く／サイト内 radio 遷移／なければ体験デモ。"""
    mp = proj.get("open_multipage_new_tab_path")
    if mp:
        st.session_state[_NEW_TAB_PATH_KEY] = str(mp).strip().strip("/")
        st.rerun()
        return
    nav = proj.get("navigate_to_page")
    if nav:
        st.session_state[_NAV_PENDING_KEY] = nav
        st.rerun()
    else:
        _open_tool_demo_dialog_fresh(proj)


def render_dashboard_demo_entry_cards(entries: List[Tuple[Dict[str, Any], str]]) -> None:
    """ダッシュボード用：ツールカタログと同型の 3 列グリッドに、左から順にカードを配置。カード全体クリックで従来どおり遷移／デモ。

    `entries`: `(project_dict, key_prefix)` のリスト（最大 3 枚）。
    直前に `inject_ai_tool_catalog_card_css()` を呼ぶこと。
    """
    if not entries:
        return
    cols = st.columns(3, gap="small", vertical_alignment="top")
    for idx, (proj, key_prefix) in enumerate(entries[:3]):
        with cols[idx]:
            png, fw = get_ai_tool_card_png_bytes(proj)
            _emit_thumbnail_font_warning_once(fw)
            if png:
                _render_clickable_ai_tool_card(png, proj, key_prefix)
            else:
                st.markdown(
                    f'<div class="ai-tool-card-fallback" style="background:#0F1C2E;color:#f8fafc;padding:1rem;border-radius:12px;text-align:center;font-size:0.92rem;font-weight:700;max-width:{_THUMB_W}px;border:1px solid rgba(201,162,77,0.25);">{html.escape(proj.get("name", "ツール"))}</div>',
                    unsafe_allow_html=True,
                )
            _lbl, _hlp = _ai_tool_open_action_label(proj)
            if st.button(
                _lbl,
                key=f"{key_prefix}demo_open_{proj['key_slug']}",
                type="primary",
                width="stretch",
                help=_hlp,
            ):
                _open_project_from_catalog(proj)


def render_ai_catalog_experience(
    projects: List[Dict[str, Any]],
    *,
    demo_session_key: str = DEFAULT_DEMO_SESSION_KEY,
    key_prefix: str = "",
) -> None:
    """
    3列×n段のコンパクトカード。画像クリックで非表示トリガーボタン経由で st.dialog を開く。
    demo_session_key は互換のため残しています（未使用）。
    """
    _ = demo_session_key

    st.subheader("ツールカタログ")
    st.caption(
        "各カードの**上段にツール名称**、**下段にイメージ画像**（`image/ai_tool_*.png`、無い場合は自動生成）、その下の **ピル型ボタン**で開きます。"
        "**カード画像をクリック**しても同じ動作です（× または「カタログに戻る」で閉じる）。"
        "**⑨ 公的価格変動ダッシュボード**は上段 **ダッシュボード**右のカードにのみあり、**新しいタブ**で **案内ページ**→**地図**の順に進めます。"
    )
    inject_ai_tool_catalog_card_css()

    for r0 in range(0, len(projects), 3):
        if r0 > 0:
            st.markdown('<div style="height:10px" aria-hidden="true"></div>', unsafe_allow_html=True)
        row = projects[r0 : r0 + 3]
        cols = st.columns(3, gap="small", vertical_alignment="top")
        for j in range(3):
            with cols[j]:
                if j >= len(row):
                    continue
                proj = row[j]
                png, fw = get_ai_tool_card_png_bytes(proj)
                _emit_thumbnail_font_warning_once(fw)
                if png:
                    _render_clickable_ai_tool_card(png, proj, key_prefix)
                else:
                    st.markdown(
                        f'<div class="ai-tool-card-fallback" style="background:#0F1C2E;color:#f8fafc;padding:1rem;border-radius:12px;text-align:center;font-size:0.92rem;font-weight:700;max-width:{_THUMB_W}px;border:1px solid rgba(201,162,77,0.25);">{html.escape(proj.get("name", "ツール"))}</div>',
                        unsafe_allow_html=True,
                    )
                _lbl, _hlp = _ai_tool_open_action_label(proj)
                if st.button(
                    _lbl,
                    key=f"{key_prefix}demo_open_{proj['key_slug']}",
                    type="primary",
                    width="stretch",
                    help=_hlp,
                ):
                    _open_project_from_catalog(proj)
