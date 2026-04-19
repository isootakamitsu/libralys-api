# -*- coding: utf-8 -*-
"""
Streamlit TOP（render_top_hero / render_top_service_cards_section / フッター文言）と
同一の TEXTS キー・遷移先ページキーを API JSON に載せる。
nav のページ名は lib.streamlit_top_nav と streamlit_app の該当関数で共有する。
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_rs = str(_REPO_ROOT)
if _rs not in sys.path:
    sys.path.insert(0, _rs)

from lib.streamlit_top_nav import HERO_CTA_PRIMARY_PAGE, HERO_CTA_SECONDARY_PAGE, TOP_SERVICE_CARD_NAV


def _headline_lines(product_headline: str) -> List[str]:
    raw = (product_headline or "").strip()
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(x) for x in obj]
    if isinstance(obj, tuple):
        return [_json_safe(x) for x in obj]
    return str(obj)


def build_streamlit_top_json(lang: str, base_dir: Path, texts_bucket: Dict[str, str]) -> Dict[str, Any]:
    """
    戻り値トップレベル: hero, services, news, trends, footer
    文言はすべて texts_bucket（TEXTS[lang]）由来。news/trends はファイル・CURATED のみ。
    """
    tr = texts_bucket
    lg = lang if lang in ("ja", "en") else "ja"

    from lib.top_corporate import load_top_news_sorted
    from lib.real_estate_trends import fetch_trend_items

    ph = tr.get("hero_product_headline") or ""
    lines = _headline_lines(str(ph))
    hero: Dict[str, Any] = {
        "product_kicker": tr.get("hero_product_kicker", ""),
        "product_headline": tr.get("hero_product_headline", ""),
        "product_headline_lines": lines,
        "headline_fallback": tr.get("hero_headline", ""),
        "use_headline_fallback": len(lines) == 0,
        "cta_primary_label": tr.get("hero_cta_primary", ""),
        "cta_secondary_label": tr.get("hero_cta_secondary", ""),
        "scroll_hint": tr.get("hero_scroll_hint", ""),
        "cta_primary_nav_page": HERO_CTA_PRIMARY_PAGE,
        "cta_secondary_nav_page": HERO_CTA_SECONDARY_PAGE,
        "service_cards_section_title": tr.get("top_service_section_title", ""),
    }

    services: List[Dict[str, Any]] = []
    for i in range(3):
        nav_page = TOP_SERVICE_CARD_NAV[i]
        n = i + 1
        services.append(
            {
                "title": tr.get(f"top_svc_card{n}_title", ""),
                "description": tr.get(f"top_svc_card{n}_desc", ""),
                "nav_page": nav_page,
            }
        )

    news = load_top_news_sorted(base_dir, lang=lg)
    trends_raw = fetch_trend_items(base_dir)

    footer_line_tmpl = tr.get("footer_line", "")
    brand = tr.get("brand_company", "")
    try:
        footer_line_resolved = footer_line_tmpl.format(company=brand)
    except (KeyError, ValueError):
        footer_line_resolved = footer_line_tmpl

    footer: Dict[str, Any] = {
        "footer_line": footer_line_resolved,
        "brand_company": brand,
        "footer_translation_note": tr.get("footer_translation_note", ""),
        "cta_kicker": tr.get("cta_kicker", ""),
        "cta_contact_btn": tr.get("cta_contact_btn", ""),
        "sitemap_title": tr.get("sitemap_title", ""),
        "smap_about": tr.get("smap_about", ""),
        "smap_services": tr.get("smap_services", ""),
        "smap_tools": tr.get("smap_tools", ""),
        "smap_gov": tr.get("smap_gov", ""),
    }

    return {
        "hero": hero,
        "services": services,
        "news": _json_safe(news),
        "trends": _json_safe(trends_raw),
        "footer": footer,
    }
