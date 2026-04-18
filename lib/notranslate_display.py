# -*- coding: utf-8 -*-
"""ブラウザ自動翻訳で本文が置き換わらないよう、translate=no の iframe 内に表示する。"""

from __future__ import annotations

import html as html_module
from typing import Any, Dict, List, Optional, Sequence

import markdown
import streamlit.components.v1 as components


def catalog_bold_only_to_html(text: str) -> str:
    """カタログ本文の **太字** のみ解釈（業務内容 SERVICES 用）。"""
    if not text:
        return ""
    segments = text.split("**")
    if len(segments) % 2 == 0:
        return "<div>" + html_module.escape(text).replace("\n", "<br />\n") + "</div>"
    parts: List[str] = []
    for i, seg in enumerate(segments):
        esc = html_module.escape(seg).replace("\n", "<br />\n")
        if i % 2 == 1:
            parts.append("<strong>" + esc + "</strong>")
        else:
            parts.append(esc)
    return '<div class="lib-svc-md">' + "".join(parts) + "</div>"


def _standard_styles_fragment() -> str:
    return (
        "<style>"
        "body{font-family:'Source Sans Pro',sans-serif;padding:12px 18px;line-height:1.65;"
        "font-size:1rem;color:#31333F;background:#FFFFFF;margin:0;}"
        "h1{font-size:1.55rem;font-weight:600;margin:0.2em 0 0.6em;color:#262730;}"
        "h2{font-size:1.28rem;font-weight:600;margin:1.15em 0 0.45em;color:#262730;}"
        "h3{font-size:1.08rem;font-weight:600;margin:0.9em 0 0.35em;color:#262730;}"
        "p{margin:0.55em 0;} ul,ol{margin:0.45em 0;padding-left:1.45em;}"
        "li{margin:0.2em 0;}"
        "strong{font-weight:600;color:#262730;}"
        "hr{border:0;border-top:1px solid rgba(49,51,63,0.18);margin:1.6em 0;}"
        ".info-box{background:rgba(49,130,206,0.11);border-left:4px solid #1c83e1;"
        "padding:12px 14px;margin:18px 0 8px;border-radius:4px;font-size:0.98rem;}"
        ".lib-page-md{max-width:100%;}"
        "</style>"
    )


def wrap_notranslate_document(inner_html: str) -> str:
    return (
        "<!DOCTYPE html><html translate=\"no\" lang=\"ja\" class=\"notranslate\"><head>"
        "<meta charset=\"utf-8\"><meta name=\"google\" content=\"notranslate\">"
        + _standard_styles_fragment()
        + "</head><body class=\"notranslate\">"
        + inner_html
        + "</body></html>"
    )


def caption_iframe_document(caption: str) -> str:
    esc = html_module.escape(caption)
    return (
        "<!DOCTYPE html><html translate=\"no\" lang=\"ja\" class=\"notranslate\"><head>"
        "<meta charset=\"utf-8\"><meta name=\"google\" content=\"notranslate\">"
        "<style>body{margin:0;padding:4px 2px 12px;font-family:'Source Sans Pro',sans-serif;"
        "font-size:0.92rem;line-height:1.55;color:#6d6d6d;background:transparent;}"
        "</style></head><body class=\"notranslate\"><p style=\"margin:0;\">"
        + esc
        + "</p></body></html>"
    )


def markdown_to_inner_html(md_source: str) -> str:
    return markdown.markdown(
        md_source.strip(),
        extensions=["nl2br", "sane_lists"],
    )


def estimate_markdown_height(md_source: str) -> int:
    return min(8000, max(380, int(len(md_source) * 0.42)))


def render_markdown_iframe(
    md_source: str,
    *,
    height: Optional[int] = None,
    info_boxes: Optional[Sequence[str]] = None,
) -> None:
    inner: List[str] = ['<div class="lib-page-md">', markdown_to_inner_html(md_source), "</div>"]
    if info_boxes:
        for txt in info_boxes:
            inner.append(
                '<div class="info-box">' + html_module.escape(txt.strip()) + "</div>"
            )
    extra = 100 * len(info_boxes or [])
    h = height if height is not None else min(8000, estimate_markdown_height(md_source) + extra)
    components.html(wrap_notranslate_document("".join(inner)), height=h, scrolling=True)


def services_body_document_html(services: List[Dict[str, Any]]) -> str:
    buf: List[str] = [
        "<!DOCTYPE html>",
        '<html translate="no" lang="ja" class="notranslate">',
        "<head><meta charset=\"utf-8\">",
        '<meta name="google" content="notranslate">',
        "<style>",
        "body{font-family:'Source Sans Pro',sans-serif;padding:8px 4px 24px;line-height:1.65;"
        "font-size:1rem;color:#31333F;background:#FFFFFF;margin:0;}",
        "h2.h-svc{font-size:1.35rem;font-weight:600;margin:1.5em 0 0.45em;color:#262730;}",
        "h2.h-svc:first-of-type{margin-top:0.15em;}",
        "details.d-svc{margin:0.4em 0;border:1px solid rgba(49,51,63,0.18);"
        "border-radius:6px;padding:7px 10px;background:rgba(49,51,63,0.03);}",
        "summary.sum-svc{cursor:pointer;font-weight:600;color:#262730;}",
        "div.bd-svc{padding:8px 2px 2px 8px;border-top:1px solid rgba(49,51,63,0.12);"
        "margin-top:8px;}",
        ".lib-svc-md strong{font-weight:600;color:#262730;}",
        "hr.sep{border:0;height:1px;background:rgba(49,51,63,0.15);margin:1.75em 0;}",
        "</style></head>",
        '<body class="notranslate">',
    ]
    for idx, item in enumerate(services):
        if idx > 0:
            buf.append('<hr class="sep" />')
        buf.append('<h2 class="h-svc">' + html_module.escape(item["title"]) + "</h2>")
        for block in item["blocks"]:
            op = " open" if block.get("expanded") else ""
            buf.append(f"<details class=\"d-svc\"{op}>")
            buf.append('<summary class="sum-svc">' + html_module.escape(block["label"]) + "</summary>")
            buf.append(
                '<div class="bd-svc">' + catalog_bold_only_to_html(block["text"]) + "</div>"
            )
            buf.append("</details>")
    buf.append("</body></html>")
    return "".join(buf)


def estimate_services_iframe_height(services: List[Dict[str, Any]]) -> int:
    h = 56
    for item in services:
        h += 52
        for block in item.get("blocks") or []:
            if block.get("expanded"):
                h += 72
                raw = block.get("text") or ""
                h += min(2200, max(140, int(len(raw) * 0.55)))
            else:
                h += 44
        h += 24
    return min(max(h, 320), 8000)
