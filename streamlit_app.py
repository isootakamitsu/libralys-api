# ============================================================
# コード8（最終版・投資銀行級UI統合）ライブラリーズ
# ー 企業統治（Governance）/ 情報セキュリティ（ISMS相当）/ 職業倫理
# ー 実績・ケーススタディ公開型 / プライバシー統合版
# 重要：コード8の内容（文章・ページ構成・方針）を崩さず、
#       TOPのみ「ビジュアル化Hero」を追加統合（既存TOP本文は維持）
# 実行: streamlit run streamlit_app.py（本リポジトリ＝Render 本番と同一）
# ============================================================

import sys
from pathlib import Path

# Render / 任意 cwd でも `from lib...` が解決されるようリポジトリ根を先頭に追加
_APP_ROOT = Path(__file__).resolve().parent
_root_s = str(_APP_ROOT)
if _root_s not in sys.path:
    sys.path.insert(0, _root_s)

import streamlit as st

# sitemap 用（最優先で実行）
query_params = st.query_params
if "sitemap" in query_params:
    st.code(
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <url>
    <loc>https://libralys.com/</loc>
  </url>

  <url>
    <loc>https://libralys.com/?page=service</loc>
  </url>

  <url>
    <loc>https://libralys.com/?page=dcf</loc>
  </url>

</urlset>""",
        language="xml",
    )
    st.stop()

# 他の st.* より先に必須（違反するとフロントが白画面・接続失敗になり得る）
st.set_page_config(
    page_title="ライブラリーズ | Libralys",
    page_icon="🏢",
    layout="wide",
    # 初回のページ切替（selectbox）はサイドバー内。畳むとメニューが隠れ誤解を招きやすいので既定は展開。
    # 狭い画面ではユーザーが Streamlit 標準の操作で折りたたみ可能。ナビの正しさとは無関係（ロジックは main と同じ）。
    initial_sidebar_state="expanded",
)

from datetime import datetime
import hashlib
import html
import json
import re
import io
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import os
import base64
from urllib.parse import quote
from textwrap import dedent

import streamlit.components.v1 as components

from lib.ai_catalog import (
    flush_multipage_new_tab_opener,
    inject_ai_tool_catalog_card_css,
    render_ai_catalog_experience,
    render_dashboard_demo_entry_cards,
)
from lib.contact_submit import (
    build_resend_overrides_from_secrets_dict,
    build_smtp_overrides_from_secrets_dict,
    submit_contact,
)
import lib.services_catalog as services_catalog_module
from lib.services_catalog import CASE_STUDY_CASE_3, SERVICES, SERVICES_PAGE
from lib.notranslate_display import (
    caption_iframe_document,
    estimate_markdown_height,
    estimate_services_iframe_height,
    render_markdown_iframe,
    services_body_document_html,
)
from lib.static_page_markdown import (
    AI_METHODOLOGY_PAGE_MARKDOWN,
    AI_METHODOLOGY_PAGE_MARKDOWN_EN,
    AI_RESEARCH_GROUP_PAGE_MARKDOWN,
    AI_RESEARCH_GROUP_PAGE_MARKDOWN_EN,
    AI_TOOLS_INTRO_MARKDOWN,
    AI_TOOLS_INTRO_MARKDOWN_EN,
    CASE_STUDIES_INTRO_MARKDOWN,
    CASE_STUDIES_INTRO_MARKDOWN_EN,
    COMPANY_OVERVIEW_PAGE_MARKDOWN,
    COMPANY_OVERVIEW_PAGE_MARKDOWN_EN,
    HAJIMETE_PAGE_MARKDOWN,
    HAJIMETE_PAGE_MARKDOWN_EN,
    PRIVACY_PAGE_MARKDOWN,
    PRIVACY_PAGE_MARKDOWN_EN,
    SERVICES_PAGE_MARKDOWN_EN,
)
from lib.sidebar_hide import inject_hidden_sidebar_css
from lib.runtime_health import render_sidebar_health
from lib.ai_tools_private import merge_ai_tool_private_overrides
from lib.tanizawa_layout import (
    render_dark_footer_sitemap,
    render_fullwidth_contact_cta,
    render_news_split_tanizawa_style,
)
from lib.top_corporate import (
    inject_top_corporate_home_css,
    render_corporate_section_title,
)
from lib.breadcrumbs import SCROLL_TOP_ONCE_KEY, render_site_breadcrumbs
# 不動産トレンド情報（信頼ソース・スコアリング・将来の fetch/要約API 拡張は lib/real_estate_trends.py）
from lib.real_estate_trends import render_real_estate_trends_section
# ⑨ カード：新規タブで開く案内ページ（→ 地図は `pages/chika_pydeck_dashboard.py`）
CHIKA_MAP_INTRO_URL_PATH = "chika_map_intro"

# ------------------------------------------------------------
# i18n: session language + TEXTS / t()
# ------------------------------------------------------------
LANG_KEY = "lang"
if LANG_KEY not in st.session_state:
    st.session_state[LANG_KEY] = "ja"

TEXTS: Dict[str, Dict[str, str]] = {
    "ja": {
        "brand_company": "ライブラリーズ",
        "brand_tone": "静かな自信／誇張なし／説明責任",
        "logo_alt": "ライブラリーズ",
        "sidebar_pages": "ページ",
        "health_expander": "動作確認",
        "lang_ja": "日本語",
        "lang_en": "English",
        "breadcrumb_home": "ホーム",
        "breadcrumb_back_help": "トップ（ホーム）へ",
        "footer_line": "© {company}｜説明責任と再現性を重視した専門サービス",
        "footer_translation_note": "英語表示は海外の投資家・専門家向けの参考として提供しています。用語・概念の整理には国際評価基準（IVS）、RICS Valuation – Global Standards（いわゆる Red Book）、USPAP 等も参照しますが、当該諸基準や各国の法令・実務上の要請を代替・満たすものではありません。",
        "news_section_mast": "NEWS",
        "news_section_kicker": "最新情報",
        "news_section_lede": "最新のお知らせ・更新情報",
        "news_detail": "詳細を読む",
        "news_featured_label": "注目のお知らせ",
        "news_more_expander_tpl": "その他のお知らせ（{n}件）",
        "news_archive_expander": "アーカイブ（過去のお知らせ）",
        "news_archive_month_prefix": "掲載月",
        "news_link_label": "関連ページを開く",
        "news_empty_hint": "表示できるお知らせがありません。",
        "cta_kicker": "コンタクト",
        "cta_contact_btn": "お問い合わせはこちら",
        "sitemap_title": "サイトマップ",
        "smap_about": "企業・ご案内",
        "smap_services": "サービス・実績",
        "smap_tools": "AI・ツール",
        "smap_gov": "方針・統治",
        "group_nav_corp": "企業・ご案内",
        "group_nav_svc": "サービス・実績",
        "group_nav_ai": "AI・ツール・研究",
        "mekiki_subtitle": "価格説明支援ツール（業務用）",
        "match_subtitle": "不動産鑑定士マッチングツール",
        "flow_faq_intro": "## よくある質問\n\n*鑑定評価・コンサルに関する代表的なご質問*\n\n",
        "bc_grp_corp": "企業・ご案内",
        "bc_grp_svc": "サービス・実績",
        "bc_grp_ai": "AI・ツール・研究",
        "bc_grp_pol": "ガバナンス・ポリシー",
        "nav_TOP": "TOP",
        "nav_はじめての方へ": "はじめての方へ",
        "nav_業務内容": "業務内容",
        "nav_業務の流れ": "業務の流れ",
        "nav_AI分析ツール": "データ分析・ツール",
        "nav_AI評価研究グループ": "AI評価研究グループ",
        "nav_価格の目利き": "価格の目利き",
        "nav_不動産鑑定士マッチング": "不動産鑑定士マッチング",
        "nav_実績・ケーススタディ": "実績・ケーススタディ",
        "nav_会社概要": "会社概要",
        "nav_代表プロフィール": "代表プロフィール",
        "nav_AI思想（Methodology）": "AI思想（Methodology）",
        "nav_企業統治（Governance）": "企業統治（Governance）",
        "nav_情報セキュリティ（ISMS相当）": "情報セキュリティ（ISMS相当）",
        "nav_倫理規程・不動産鑑定士職業倫理": "倫理規程・不動産鑑定士職業倫理",
        "nav_プライバシー": "プライバシー",
        "nav_お問い合わせ": "お問い合わせ",
        "hero_kicker": "不動産鑑定評価・価格分析サービス",
        "hero_headline": "不動産価格の根拠を、構造として可視化する",
        "hero_sub": """不動産価格は単なる結論ではなく、地価公示・取引事例・収益性・リスクなど、複数の要因が交差して形成されます。
本サービスは、不動産鑑定評価の理論とAI分析を融合し、価格形成のプロセスを構造として整理・可視化します。
大阪を中心に不動産鑑定評価、DCF分析、価格調査を行っています。
AIを活用した高度な分析により、根拠ある価格説明を提供します。
40年の実務経験と2,000件超の鑑定評価に基づき、市場データ・制度・収益性を統合分析し、第三者が検証可能な説明を提供します。""",
        "hero_foot": "不動産鑑定士｜AI鑑定|ライブラリーズ",
        "hero_product_kicker": "AI REAL ESTATE ANALYSIS PLATFORM",
        "hero_product_headline": """不動産価格を
「説明できる」時代へ""",
        "hero_cta_primary": "無料で試す",
        "hero_cta_secondary": "詳細を見る",
        "hero_scroll_hint": "↓スクロール",
        "top_service_section_title": "提供サービス",
        "top_svc_card1_title": "価格の目利き",
        "top_svc_card1_desc": "AIで不動産価格を即時診断",
        "top_svc_card2_title": "DCF分析",
        "top_svc_card2_desc": "収益還元法による詳細分析",
        "top_svc_card3_title": "不動産鑑定",
        "top_svc_card3_desc": "専門鑑定士による評価",
        "top_cta_services": "業務内容を見る",
        "top_cta_ai": "分析ツールを見る",
        "m_kpi_office": "拠点",
        "m_kpi_office_v": "大阪",
        "m_kpi_cov": "対応",
        "m_kpi_cov_v": "全国対応",
        "m_kpi_exp": "代表の実務経験",
        "m_kpi_exp_v": "40年",
        "m_kpi_cases": "代表の実務件数",
        "m_kpi_cases_v": "実績2,000件以上",
        "exp_philosophy": "PHILOSOPHY",
        "about_title": "ライブラリーズとは",
        "about_sub": "専門性を、わかる言葉と構造で届ける。",
        "about_body": """ライブラリーズは、不動産に関する価格判断と説明を支えることを目的とした専門サービスです。
不動産鑑定評価の知見を基礎に、売買、相続、賃貸借、再開発、投資判断、資産整理など、
さまざまな場面で求められる価格情報を、公正かつ中立的な立場から整理・提供します。

不動産に関する意思決定では、単に価格を知るだけでなく、
その価格がどのような要因によって形成されているか、
どのような前提のもとで妥当と判断されるかを理解することが重要です。
当社は、この「説明できる価格情報」を重視し、専門性と分かりやすさの両立を目指しています。
ライブラリーズは、不動産評価を「価格の提示」ではなく、「価格の根拠を説明する技術」と捉えます。
価格は、市場環境・制度的要件・個別事情・収益構造・将来期待が交差する地点に現れる結果です。
そのため、結論だけを示しても本質は伝わりません。
重要なのは、**どの前提に立ち、どの手法を選び、どの補正・整合性検証を行ったのか**を、
第三者が追跡できる構造で示すことです。
(なお、現在、ライブラリーズは、不動産鑑定業者登録を行っていないので、不動産の鑑定評価に関する法律の基づく鑑定評価業務は行っていません。)""",
        "pillar_1_h": "01｜経験 × 検証",
        "pillar_1_b": """市場理解と実務判断を軸に、データと感応度分析で根拠を補強します。
数字は結論ではなく、説明責任を支える材料として扱います。""",
        "pillar_2_h": "02｜前提の開示",
        "pillar_2_b": """評価は前提に依存します。
前提条件・適用範囲・限界を明示し、第三者が追える形で提示します。""",
        "pillar_3_h": "03｜責任体制",
        "pillar_3_b": """まずは、受任可否を慎重に判断します。
無理な依頼は受けず、品質と納期の確実性を優先します。""",
        "exp_chika": "地価公示・地価調査",
        "chika_intro": """国交省の地価公示・地価調査等を想定した地点データ（CSV）を、<strong>案内ページ</strong>経由で
<strong>Web上の地図</strong>から確認できます。""",
        "chika_btn_web": "公的地価マップ（Web・案内から）",
        "chika_btn_qgis": "QGISで地図プロジェクトを開く",
        "chika_qgis_err": "QGISプロジェクトを開けませんでした: {e}",
        "dash_heading": "ダッシュボード",
        "invalid_page": "このページは PAGES にありますが、本文の分岐（elif）が未実装です。app.py を確認してください。",
        "invalid_page_name": "ページ名: {name!r}",
        "btn_back_top": "トップへ戻る",
        "float_nav_back": "戻る",
        "float_nav_top": "▲ TOP",
        # --- 不動産トレンド情報（TOPセクション・i18n） ---
        "trend_section_title": "不動産トレンド情報",
        "trend_notes_expander": "このセクションについて（説明・注意）",
        "trend_section_sub": "公的統計・市況レポート・J-REIT情報など、一次・準一次ソースへの短い案内です（全文転載は行いません）。",
        "trend_legal_note": "掲載内容は参考用の要約です。最新数値・条件は必ず各公式サイトでご確認ください。有料媒体の自動取得は行っていません。",
        "trend_filter_category": "用途カテゴリで絞り込み",
        "trend_cat_all": "すべて",
        "trend_filter_source": "情報ソースで絞り込み",
        "trend_src_all": "すべて",
        "trend_src_kokudo": "国交省",
        "trend_src_sanki": "三鬼商事",
        "trend_src_reit": "JAPAN-REIT.COM",
        "trend_src_other": "その他（CBRE 等）",
        "trend_featured_heading": "注目トレンド",
        "trend_by_use_heading": "用途別トレンド（展開して表示）",
        "trend_category_expander": "{name}（{n}件）",
        "trend_active_none_hint": "表示中のアクティブなトレンドはありません。下のアーカイブを展開してご確認ください。",
        "trend_spotlight_heading": "今日の注目トレンド（上位3件）",
        "trend_spotlight_empty": "（フィルタ条件に合致する注目枠はありません）",
        "trend_list_heading": "一覧（用途別・その他）",
        "trend_list_empty": "（一覧に表示する追加件はありません。フィルタを緩めてください）",
        "trend_archive_expander": "アーカイブ（過去の掲載枠・月別・カード表示）",
        "trend_archive_month_prefix": "掲載月",
        "trend_score_caption": "注目度スコア（信頼性・新しさ・閲覧記録の合成）: {score:.2f}",
        "trend_open_official": "公式ページを開く",
        "trend_empty": "表示できるトレンドがありません。`lib/real_estate_trends.py` または `data/trend_items.json` をご確認ください。",
    },
    "en": {
        "brand_company": "Libralys",
        "brand_tone": "Quiet confidence / no exaggeration / accountability",
        "logo_alt": "Libralys",
        "sidebar_pages": "Page",
        "health_expander": "Diagnostics",
        "lang_ja": "日本語",
        "lang_en": "English",
        "breadcrumb_home": "Home",
        "breadcrumb_back_help": "Back to home",
        "footer_line": "© {company}｜Professional services focused on accountability and reproducibility",
        "footer_translation_note": "English pages are provided for international readers. Terminology is informed, where appropriate, by the *International Valuation Standards (IVS)*, the *RICS Valuation – Global Standards* (“Red Book”, UK), and the *Uniform Standards of Professional Appraisal Practice (USPAP)* (US). This does not replace those publications or satisfy any specific foreign regulatory or professional requirements.",
        "news_section_mast": "NEWS",
        "news_section_kicker": "Updates",
        "news_section_lede": "Latest updates & announcements",
        "news_detail": "Read more",
        "news_featured_label": "Featured",
        "news_more_expander_tpl": "More updates ({n})",
        "news_archive_expander": "Archive (older announcements)",
        "news_archive_month_prefix": "Month",
        "news_link_label": "Open related page",
        "news_empty_hint": "No announcements to display.",
        "cta_kicker": "Contact",
        "cta_contact_btn": "Contact us",
        "sitemap_title": "Site map",
        "smap_about": "Corporate",
        "smap_services": "Services & work",
        "smap_tools": "AI & tools",
        "smap_gov": "Governance & policies",
        "group_nav_corp": "Corporate",
        "group_nav_svc": "Services & experience",
        "group_nav_ai": "AI, tools & research",
        "mekiki_subtitle": "Price communication aid (professional use)",
        "match_subtitle": "Appraiser matching workspace",
        "flow_faq_intro": "## Frequently asked questions\n\n*Representative questions on appraisal and consulting*\n\n",
        "bc_grp_corp": "Corporate & information",
        "bc_grp_svc": "Services & experience",
        "bc_grp_ai": "AI · tools · research",
        "bc_grp_pol": "Governance & policy",
        "nav_TOP": "Home",
        "nav_はじめての方へ": "First visit",
        "nav_業務内容": "Services",
        "nav_業務の流れ": "How we work",
        "nav_AI分析ツール": "Data analytics & tools",
        "nav_AI評価研究グループ": "AI valuation research",
        "nav_価格の目利き": "Price Insight",
        "nav_不動産鑑定士マッチング": "Appraiser matching",
        "nav_実績・ケーススタディ": "Experience & case studies",
        "nav_会社概要": "Company overview",
        "nav_代表プロフィール": "Representative profile",
        "nav_AI思想（Methodology）": "AI methodology",
        "nav_企業統治（Governance）": "Governance",
        "nav_情報セキュリティ（ISMS相当）": "Information security (ISMS-aligned)",
        "nav_倫理規程・不動産鑑定士職業倫理": "Ethics & professional standards",
        "nav_プライバシー": "Privacy policy",
        "nav_お問い合わせ": "Contact",
        "hero_kicker": "AI-assisted appraisal analytics & land-price intelligence",
        "hero_headline": "Make real estate value explainable—as a structured narrative",
        "hero_sub": """Property value is not a single headline figure; it emerges where official land benchmarks, comparable sales,
income prospects, and risk factors intersect. This site integrates Real Estate Appraisal discipline with AI-assisted analytics
to organize and visualize how value is formed—so conclusions can be reviewed by third parties.
Drawing on four decades of practice and 2,000+ appraisal assignments, we combine market data, institutional context, and income logic into transparent, verifiable explanations.""",
        "hero_foot": "Accountability · reproducibility · independence｜Analysis led by a real property appraiser",
        "hero_product_kicker": "AI REAL ESTATE ANALYSIS PLATFORM",
        "hero_product_headline": """Bring real estate prices
into an era where they can be explained""",
        "hero_cta_primary": "Try it free",
        "hero_cta_secondary": "See details",
        "hero_scroll_hint": "↓ Scroll",
        "top_service_section_title": "Services",
        "top_svc_card1_title": "Price Insight",
        "top_svc_card1_desc": "Instant property price diagnostics with AI",
        "top_svc_card2_title": "DCF analysis",
        "top_svc_card2_desc": "Income approach–based detailed analysis",
        "top_svc_card3_title": "Real estate appraisal",
        "top_svc_card3_desc": "Professional appraiser–led evaluation",
        "top_cta_services": "Explore services",
        "top_cta_ai": "View analytics tools",
        "m_kpi_office": "Office",
        "m_kpi_office_v": "Osaka",
        "m_kpi_cov": "Coverage",
        "m_kpi_cov_v": "Japan-wide (planned)",
        "m_kpi_exp": "Representative’s experience",
        "m_kpi_exp_v": "40 years",
        "m_kpi_cases": "Representative engagements",
        "m_kpi_cases_v": "2,000+ assignments",
        "exp_philosophy": "PHILOSOPHY",
        "about_title": "About Libralys",
        "about_sub": "Professional judgment—delivered in clear language and traceable structure.",
        "about_body": """Libralys supports real estate pricing decisions with transparent, third-party explainable analysis.
We draw on **Real Estate Appraisal** practice for sales, inheritance, leasing, redevelopment, investment, and portfolio decisions—always from a neutral, professional standpoint.

Good decisions require more than a number; they require clarity on **assumptions**, **methods**, and **limits**.
We treat valuation as the discipline of explaining *why* a value is reasonable—not only *what* it is.
Price emerges where market conditions, regulatory context, property-specific facts, income structure, and expectations meet.
Therefore, conclusions alone are insufficient: what matters is a **traceable path** from purpose and assumptions through method selection, adjustments, and consistency checks.
*(Libralys is not currently registered as a designated appraisal firm under the Japanese Real Estate Appraisal Act; statutory appraisal services under that Act are not provided.)*""",
        "pillar_1_h": "01｜Experience × verification",
        "pillar_1_b": """We combine market judgment with data and sensitivity analysis to strengthen the evidence base.
Numbers support accountability—they are not substitutes for it.""",
        "pillar_2_h": "02｜Explicit assumptions",
        "pillar_2_b": """Value depends on assumptions.
We disclose scope, premises, and limitations so reviewers can follow the logic.""",
        "pillar_3_h": "03｜Responsibility",
        "pillar_3_b": """We carefully decide whether to accept an engagement.
We decline work we cannot execute to the required quality within the required timeline.""",
        "exp_chika": "Official Land Price Publication & Prefectural Land Price Survey",
        "chika_intro": """Plot-level CSV data aligned with MLIT’s <strong>Official Land Price Publication</strong> and related official benchmarks can be reviewed via an <strong>intro page</strong>,
then explored on a <strong>web map</strong>.""",
        "chika_btn_web": "Official land-price map (web, via intro)",
        "chika_btn_qgis": "Open QGIS project",
        "chika_qgis_err": "Could not open the QGIS project: {e}",
        "dash_heading": "Dashboard",
        "invalid_page": "This route exists in PAGES but has no content branch in app.py.",
        "invalid_page_name": "Page key: {name!r}",
        "btn_back_top": "Back to home",
        "float_nav_back": "Back",
        "float_nav_top": "▲ Top",
        # --- Real estate trends (TOP section) ---
        "trend_section_title": "Real estate trend briefings",
        "trend_notes_expander": "About this section (notes)",
        "trend_section_sub": "Short pointers to official statistics, market reports and J-REIT portals—no full-text reproduction.",
        "trend_legal_note": "Summaries are for orientation only; verify figures and terms on each official site. No automated scraping of paid media.",
        "trend_filter_category": "Filter by use category",
        "trend_cat_all": "All",
        "trend_filter_source": "Filter by source",
        "trend_src_all": "All",
        "trend_src_kokudo": "MLIT (Japan)",
        "trend_src_sanki": "Miki Shoji",
        "trend_src_reit": "JAPAN-REIT.COM",
        "trend_src_other": "Other (e.g. CBRE)",
        "trend_featured_heading": "Featured trend",
        "trend_by_use_heading": "Trends by use (expand to view)",
        "trend_category_expander": "{name} ({n} items)",
        "trend_active_none_hint": "No active trends match your filters. Open the archive below.",
        "trend_spotlight_heading": "Today’s highlighted trends (top 3)",
        "trend_spotlight_empty": "(No items match the spotlight filter.)",
        "trend_list_heading": "More items (by use)",
        "trend_list_empty": "(No additional rows—try relaxing filters.)",
        "trend_archive_expander": "Archive (by month, cards)",
        "trend_archive_month_prefix": "Month",
        "trend_score_caption": "Attention score (reliability · freshness · views): {score:.2f}",
        "trend_open_official": "Open official page",
        "trend_empty": "No trend items to show. Check `lib/real_estate_trends.py` or `data/trend_items.json`.",
    },
}
TEXTS["ja"].update(
    {
        "caption_hajimete": "専門用語は“翻訳”しながら説明します。まずは全体像を掴むページです。",
        "caption_gyomu": "ライブラリーズは、不動産鑑定評価、価格等調査、簡易価格診断、市場分析、再開発・補償・相続・賃料・投資判断支援など、不動産に関する幅広い相談に対応する専門事務所です。不動産に関する価格判断は、売買、相続、賃貸借、再開発、投資、担保、会計など、目的によって求められる視点が異なります。\n専門性と説明責任を重視し、依頼者が安心して意思決定できる情報提供を行います。",
        "services_jp_expander": "原文（日本語）のサービス詳細を表示",
        "caption_nagare": "わかりやすく、各工程の意味を丁寧に説明します。",
        "caption_ai_tools": "ダッシュボードとツールカタログから各機能へ進めます。",
        "caption_ai_lab": "評価理論 × データ科学 × 制度整合の研究拠点",
        "caption_ai_method": "AIの位置づけ・用途・非目的・管理方針を整理します。",
        "caption_gov": "独立性・透明性・説明責任を、運用可能な統治構造として整理します。",
        "caption_sec": "コンサルティング業務の機密性を前提に、情報資産を保護する運用枠組みを定義します。",
        "caption_ethics": "独立性・公正性・誠実性・守秘・説明責任を、運用規範として明文化します。",
        "caption_cases": "守秘に配慮しつつ、評価の“考え方と構造”を公開します。",
        "caption_contact": "「依頼」ではなく、まずは、「相談」。状況整理から一緒に行います。",
        "caption_privacy": "SDGsへの取り組み／個人情報保護法に基づく公表事項／プライバシーポリシー",
        "contact_purpose": "ご相談種別",
        "contact_name": "お名前（必須）",
        "contact_email": "メールアドレス（必須）",
        "contact_tel": "電話番号（任意）",
        "contact_addr": "対象不動産の所在地（可能な範囲で）",
        "contact_msg": "ご相談内容（必須）",
        "contact_msg_ph": "目的、提出先、希望納期、対象不動産の概要（自用/賃貸）、権利関係の概要などをご記入ください。",
        "contact_agree": "プライバシーポリシーに同意します",
        "contact_submit": "送信",
        "contact_err_required": "必須項目（お名前・メール・ご相談内容・同意）をご確認ください。",
        "contact_err_exc": "送信処理中に予期しないエラーが発生しました: {exc}",
        "contact_copy": "送信内容の控え（コピー用）",
        "info_governance": "ライブラリーズは「結論の強さ」よりも「根拠の強さ」を優先します。統治はその前提条件です。",
        "info_security": "情報保護は“安心の表現”ではなく、事故を起こさないための業務設計です。",
        "info_ethics": "ライブラリーズは、倫理を“理念”ではなく“作業仕様”として扱い、結果に反映させます。",
        "info_cases": "ケースは順次拡充予定。",
        "info_privacy": "ライブラリーズは、評価業務における説明責任と同様に、\n情報管理についても高度な倫理性と透明性を維持します。",
        "info_ai_lab": "AIは判断主体ではありません。研究成果は不動産鑑定士の専門判断を補助します。",
        "mailto_subj_prefix": "[ライブラリーズ]",
        "mailto_body_note": "（お問い合わせフォーム経由／メールクライアントで送信）",
        "mailto_purpose_lbl": "相談種別",
        "mailto_name_lbl": "お名前",
        "mailto_email_lbl": "返信先メール",
        "mailto_tel_lbl": "電話",
        "mailto_addr_lbl": "所在地",
        "mailto_msg_hdr": "【ご相談内容】",
        "mekiki_story_h": "価格の目利き誕生秘話",
        "mekiki_story_body": """#### 不透明な不動産価格を、もっと見えるものに。
公的価格、取引事例、収益価格、建築費、金利。
本来つながるべき情報がバラバラであることに着目し、
それらを一つにつなぐ分析基盤として「価格の目利き」は生まれました。""",
        "mekiki_open_hint": "下のボタンで<strong>価格の目利き</strong>を開きます。開くと <strong>入力</strong>・<strong>結果</strong>・<strong>運用・免責（必読）</strong> のタブが表示されます。",
        "mekiki_open_main": "価格の目利きを開く（入力／結果／運用・免責）",
        "mekiki_status": " — 価格の目利き（表示中）",
        "mekiki_close": "ツールを閉じる",
        "mekiki_inner_hint": "入力・結果・運用・免責の各タブ、物件情報フォーム、参照帯・近隣事例などの画面は、下のボタンから表示します。",
        "mekiki_open_an": "価格の目利きを見る",
        "mekiki_tab_in": "入力",
        "mekiki_tab_out": "結果",
        "mekiki_tab_dis": "運用・免責（必読）",
        "mekiki_sec_prop": "物件情報（コピペ対応）",
        "mekiki_raw_lbl": "物件情報を貼り付け（URLだけでも可）",
        "mekiki_raw_ph": "例）建築条件付き土地 2,560万円 土地面積146.26㎡ ... 徒歩18分 ...",
        "mekiki_exp_parse": "自動読み取り結果（必要に応じて修正してください）",
        "mekiki_price": "価格（万円）",
        "mekiki_area": "土地面積（㎡）",
        "mekiki_walk": "駅徒歩（分）※不明なら0でOK",
        "mekiki_bcond": "建築条件付き",
        "mekiki_addr": "所在地（任意）",
        "mekiki_band_h": "価格の見え方の参照帯（暫定）",
        "mekiki_region": "参照レンジ（暫定）",
        "mekiki_walk_cap": "駅距離区分：{wb}",
        "mekiki_more_h": "追加の観点（任意）",
        "mekiki_road": "前面道路幅員（m）※不明なら0",
        "mekiki_shape": "画地形状（任意）",
        "shape_unknown": "不明",
        "shape_regular": "整形",
        "shape_irreg": "やや難あり",
        "mekiki_comp_h": "近隣事例（任意）",
        "mekiki_comp_cap": "各行に「2400万円 150㎡」のように貼り付け（保存はされません）。",
        "mekiki_comp_lbl": "近隣事例（任意）",
        "mekiki_comp_ph": "2400万円 150㎡\n2680万円 142.36㎡",
        "mekiki_run": "価格の見え方を整理する（参考）",
        "mekiki_ok": "結果タブに出力しました。",
        "mekiki_res_h": "結果（市場での見え方の整理）",
        "mekiki_need_input": "まず「入力」タブで入力し、ボタンを押してください。",
        "mekiki_err_pa": "価格（万円）と面積（㎡）を入力してください。",
        "mekiki_subj": "【対象】",
        "mekiki_lbl_addr": "所在地（任意）",
        "mekiki_na": "（未入力）",
        "mekiki_lbl_price": "価格",
        "mekiki_lbl_area": "面積",
        "mekiki_lbl_up": "単価（参考）",
        "mekiki_yen_m2": "円/㎡",
        "mekiki_man": "万円",
        "mekiki_lbl_walk": "駅距離区分",
        "mekiki_lbl_bcond": "建築条件",
        "mekiki_yes": "あり",
        "mekiki_no": "なし",
        "mekiki_view_h": "【価格の見え方（参考）】",
        "mekiki_why_h": "【そう見える理由】",
        "mekiki_band_disp_h": "【参照帯（参考）の表示】",
        "mekiki_band_cap": "※相場断定ではなく、見え方整理の参照帯（暫定）です。運用主体でカスタマイズしてください。",
        "mekiki_lbl_reg": "参照レンジ",
        "mekiki_band_line": "参照帯：下限 {lo} ／中心 {mid} ／上限 {hi}（円/㎡）",
        "mekiki_comp_pos_h": "【近隣事例（任意）との位置づけ】",
        "mekiki_notes_h": "【留意点（必ず表示）】",
        "mekiki_notes_body": "本出力は鑑定評価書ではなく、価格算定・適正価格の断定・不動産取引の勧誘を行いません。\n利用者入力に基づく参考整理であり、最終判断は利用者自身で行ってください。",
        "mekiki_ops_h": "運用・免責（必読）",
        "mekiki_save_h": "保存とプライバシー",
        "mekiki_ng_h": "NGワード（運用ルール）",
        "mekiki_ng_cap": "画面文言・広告文・出力テンプレで、下記のような断定語を避けてください。",
        "mekiki_lbl_modest": "控えめ（市場水準より低めに見える可能性）",
        "mekiki_lbl_ok": "概ね妥当（中心帯に見える可能性）",
        "mekiki_lbl_high": "やや強気（上限寄りに見える可能性）",
        "mekiki_r1": "参照帯（参考）の下限寄りまたは下回る水準。",
        "mekiki_r2": "参照帯（参考）の中心〜上限の範囲内。",
        "mekiki_r3": "参照帯（参考）の上限を上回る水準。",
        "mekiki_r4": "建築条件付きは自由度制約となり、土地単体比較では慎重評価になりやすい。",
        "mekiki_r5a": "前面道路幅員が4m未満の場合、接道要件・再建築等の論点が生じ得るため注意。",
        "mekiki_r5b": "前面道路幅員が4〜6m帯の場合、整備水準・交通性で差が出やすい。",
        "mekiki_r5c": "前面道路幅員が6m以上なら、住宅地では評価が安定しやすい。",
        "mekiki_r5d": "前面道路幅員が不明のため、接道条件の上振れ・下振れ要因は未反映。",
        "mekiki_r6a": "整形地は設計自由度が高く、市場での受容性が高い。",
        "mekiki_r6b": "不整形・間口狭小等がある場合、実需では敬遠要因となり得る。",
        "mekiki_r6c": "画地形状が不明のため、形状要因は未反映。",
        "mekiki_cc_none": "近隣事例（任意）が未入力のため、事例比較は省略。",
        "mekiki_cc_near": "入力事例の単価中央値（約{med:,}円/㎡）と近い水準。",
        "mekiki_cc_hi": "入力事例の単価中央値（約{med:,}円/㎡）より上側（+約{diff:,}円/㎡）に位置。",
        "mekiki_cc_lo": "入力事例の単価中央値（約{med:,}円/㎡）より下側（-約{diff:,}円/㎡）に位置。",
        "mekiki_col_line": "事例",
        "mekiki_col_price": "価格(万円)",
        "mekiki_col_area": "面積(㎡)",
        "mekiki_col_up": "単価(円/㎡)",
        "reg_nat": "全国（暫定）",
        "reg_kansai": "関西（暫定）",
        "reg_kanto": "首都圏（暫定）",
        "wb_10": "駅徒歩10分以内",
        "wb_15": "駅徒歩11-15分",
        "wb_20": "駅徒歩16-20分",
        "wb_21": "駅徒歩21分以上",
        "match_story_h": "不動産鑑定士マッチング秘話",
        "match_story_miss": "画像が見つかりません: `{path}` を `image` フォルダに配置してください。",
        "match_concept_h": "コンセプト",
        "match_concept_body": """#### 専門家との出会いを、もっと自然に。
不動産価格の悩みは、価格を知るだけでは解決しません。
最終的には、個別事情を踏まえて相談できる専門家との接点が必要です。

「価格の目利き」で価格の見え方を整理したあと、**依頼者と不動産鑑定士をつなぐ**入口として 本マッチングプラットフォームを構想しました。
**価格の見える化から、専門家相談へ。**
この流れを一つの体験としてつなぐことで、不動産判断をより安心で透明なものにします。""",
        "match_open_hint": "下のボタンで<strong>マッチングツール</strong>を開きます。開くと <strong>入力</strong>・<strong>結果</strong>・<strong>運用・免責（必読）</strong> のタブが表示されます。",
        "match_open_main": "マッチングツールを開く（入力／結果／運用・免責）",
        "match_status": " — マッチングツール（表示中）",
        "match_inner_hint": "入力・結果・運用・免責の各タブ、依頼概要フォームなどの画面は、下のボタンから表示します。（※実装予定）",
        "match_open_an": "不動産鑑定士マッチングを見る",
        "match_in_h": "依頼の入力（準備中）",
        "match_in_info": "マッチング用の入力フォーム・鑑定士側の受付画面は、今後の実装予定です。\n現時点では本タブはプレースホルダです。お急ぎのご相談は「お問い合わせ」ページからご連絡ください。",
        "match_btn_contact": "お問い合わせページへ",
        "match_out_h": "マッチング結果（準備中）",
        "match_out_info": "条件に応じた鑑定士の候補提示・マッチング状態の表示は、ツール実装後に本タブで提供予定です。",
        "match_ops_h": "運用・免責（必読）",
        "match_note_h": "留意事項",
        "match_note_cap": "マッチングは紹介に近い位置づけであり、特定の鑑定士の選定や契約内容の代行ではありません。また、紹介できる鑑定士のプロフィールや経歴等は、登録した不動産鑑定自らが提示した情報であり、当社はその内容の正確性を保証するものではありません。",
        "ai_ai03_name": "AI鑑定評価書作成アプリ",
        "ai_ai03_tag": "論点整理・章立てのイメージをつかむ",
        "ai_ai03_sum": "鑑定評価書の作成・下書き・整理を支援するStreamlitアプリです。資料入力や文章化の補助を想定しています（参考・作業補助であり、法的効力のある鑑定評価書そのものの代替ではありません）。",
        "ai_ai03_note": "APIキー（例：OpenAI、地図）を利用する機能は、各所定の設定ファイルや環境変数が必要です。",
        "ai_ai04_name": "DCF・資産評価ダッシュボード（shisanhyoメ・イン）",
        "ai_ai04_tag": "収益価格の骨格を数分で体感",
        "ai_ai04_sum": "ライブラリーズの**AI分析ツール群の拠点**となるフォルダです。DCF中心のダッシュボードや試算表をローカルで実行・検証できます。",
        "ai_ai04_note": "実務フル機能版は別エントリの Streamlit アプリがある場合があります（配布フォルダ内の README を参照）。",
        "ai_ai05_name": "CR事例DB自動収集システム",
        "ai_ai05_tag": "事例の集積イメージを掴む",
        "ai_ai05_sum": "事例データベースの収集・整理を行うStreamlitアプリです。",
        "ai_ai05_note": "初回のみ依存パッケージの導入が必要です。仮想環境の利用を推奨します。",
        "ai_ai06_name": "収益分析プラットフォーム（Income Intelligence）",
        "ai_ai06_tag": "収益の筋道をダイヤルで追う",
        "ai_ai06_sum": "収益不動産の分析・可視化を行うエンジンです。",
        "ai_ai06_note": "依存関係は配布パッケージ同梱の requirements を使用します。",
        "ai_ai07_name": "開発支援ダッシュボード",
        "ai_ai07_tag": "再開発シナリオの考え方を俯瞰",
        "ai_ai07_sum": "再開発・建替え等の検討を支援するダッシュボードです。",
        "ai_ai07_note": "ツール用フォルダをカレントにして起動します。",
        "ai_ai08_name": "不動産データ管理ダッシュボード",
        "ai_ai08_tag": "指数・時系列の見え方を体感",
        "ai_ai08_sum": "市場指数・時系列・DCF関連のデータ管理・可視化用ダッシュボードです。",
        "ai_ai08_note": "データソースやAPIの有無はローカル環境の設定に依存します。",
        "ai_ai09_name": "公的価格変動ダッシュボード",
        "ai_ai09_tag": "公示・路線の変動を地図マッピング",
        "ai_ai09_sum": "まず **案内ページ** でデータ要件を確認し、**Web 上の地図（pydeck）** で公示地点の変動率を俯瞰します（参考分析・既定 CSV はリポジトリの `data/kokoku/`。環境変数 `CHIKA_CSV_PATH` または Secrets の `CHIKA_CSV_PATH` / `[chika] csv_path` で変更可）。",
        "ai_ai09_note": "⑨ のカードは **新しいブラウザタブ** で **案内ページ**を開き、そこから地図ダッシュボードへ進みます。公式統計は国土交通省等を参照してください。",
        "contact_info_secrets_next": (
            "上の注意に従い Secrets を設定すると、次回からサーバーから自動で事務局に届きます。\n"
            "手順の全文はリポジトリの `.streamlit/secrets.toml.example` 先頭を参照してください。\n"
            "それまでの間は、下のボタンでメールソフトから送信できます。"
        ),
        "contact_mailto_btn": "メールソフトで事務局に送る（件名・本文を自動入力）",
        "contact_info_secrets_setup": (
            "事務局メールを Streamlit **Secrets**（Cloud: App → Settings → Secrets）の "
            "TOML で `[contact] to_email` または `[smtp] to_email`、"
            "または **自動送信**には **`[resend]`**（`api_key`・`from_email`・推奨・HTTPS）"
            "または `[smtp]`（`host`・`user`・`password`・`to_email`）を揃えてください。\n"
            "（ローカルは `.streamlit/secrets.toml`。例は `.streamlit/secrets.toml.example`）"
        ),
    }
)
TEXTS["en"].update(
    {
        "caption_hajimete": "We translate jargon into plain language—start with the big picture.",
        "caption_gyomu": """Libralys is a professional practice supporting **Real Estate Appraisal** thinking, **Property Price Analysis**, **Market Analysis**, and related advisory—from transactions and collateral to inheritance, rent disputes, redevelopment, and investment decisions. The right lens depends on the mandate; we emphasize accountability and clarity.""",
        "services_jp_expander": "Show full service descriptions (Japanese)",
        "caption_nagare": "A clear walkthrough of each step and what it means.",
        "caption_ai_tools": "Use the dashboard shortcuts and tool catalog to open each experience.",
        "caption_ai_lab": "Research at the intersection of valuation theory, data science, and regulatory alignment.",
        "caption_ai_method": "How AI is used—and what it is not intended to do.",
        "caption_gov": "Independence, transparency, and accountability as operable governance.",
        "caption_sec": "An ISMS-aligned framework for protecting information assets in consulting work.",
        "caption_ethics": "Independence, fairness, integrity, confidentiality, and accountability—documented as operating rules.",
        "caption_cases": "Public examples of analytical structure—without breaching confidentiality.",
        "caption_contact": "Start with a conversation—not a “mandate.” We help you structure the question first.",
        "caption_privacy": "SDGs commitment / statutory disclosures / privacy policy",
        "contact_purpose": "Topic",
        "contact_name": "Name (required)",
        "contact_email": "Email (required)",
        "contact_tel": "Phone (optional)",
        "contact_addr": "Property location (as much as you can share)",
        "contact_msg": "Message (required)",
        "contact_msg_ph": "Purpose, recipient requirements, desired timeline, property use (owner-occupied / leased), rights summary, etc.",
        "contact_agree": "I agree to the Privacy Policy",
        "contact_submit": "Submit",
        "contact_err_required": "Please complete name, email, message, and consent.",
        "contact_err_exc": "An unexpected error occurred while submitting: {exc}",
        "contact_copy": "Submission copy (for your records)",
        "info_governance": "Libralys prioritizes the strength of evidence over the loudness of conclusions. Governance is the precondition.",
        "info_security": "Information protection is operational design—not a slogan.",
        "info_ethics": "Ethics are treated as work specifications—not abstract ideals.",
        "info_cases": "Additional cases will be published over time.",
        "info_privacy": "As in valuation work, we apply the same standard of accountability and transparency to information management.",
        "info_ai_lab": "AI is not the decision-maker; research outputs assist the professional appraiser.",
        "mailto_subj_prefix": "[Libralys]",
        "mailto_body_note": "(Via contact form / sending from your mail client)",
        "mailto_purpose_lbl": "Topic",
        "mailto_name_lbl": "Name",
        "mailto_email_lbl": "Reply-to email",
        "mailto_tel_lbl": "Phone",
        "mailto_addr_lbl": "Location",
        "mailto_msg_hdr": "Message",
        "mekiki_story_h": "How Price Insight came about",
        "mekiki_story_body": """#### Making opaque property pricing easier to read.
Official land benchmarks, comparable sales, income value, construction cost, and interest rates.
**Price Insight** was built as an analytical layer that connects information that should travel together—but often sits in silos.""",
        "mekiki_open_hint": "Open <strong>Price Insight</strong> below. You will see tabs for <strong>Input</strong>, <strong>Results</strong>, and <strong>Operations & disclaimer (required reading)</strong>.",
        "mekiki_open_main": "Open Price Insight (input / results / disclaimer)",
        "mekiki_status": " — Price Insight (open)",
        "mekiki_close": "Close tool",
        "mekiki_inner_hint": "The property form, reference bands, optional comparables, and tabs appear after you open the analyzer below.",
        "mekiki_open_an": "Open Price Insight",
        "mekiki_tab_in": "Input",
        "mekiki_tab_out": "Results",
        "mekiki_tab_dis": "Operations & disclaimer",
        "mekiki_sec_prop": "Property information (paste-friendly)",
        "mekiki_raw_lbl": "Paste listing text (URL alone is OK)",
        "mekiki_raw_ph": "e.g., land with building conditions, ¥25.6m, 146.26㎡, … 18 min walk …",
        "mekiki_exp_parse": "Parsed fields (edit if needed)",
        "mekiki_price": "Price (JPY millions)",
        "mekiki_area": "Site area (㎡)",
        "mekiki_walk": "Walk time to station (min); use 0 if unknown",
        "mekiki_bcond": "Building conditions attached",
        "mekiki_addr": "Address (optional)",
        "mekiki_band_h": "Indicative reference band (draft)",
        "mekiki_region": "Reference region (draft)",
        "mekiki_walk_cap": "Walk-time bucket: {wb}",
        "mekiki_more_h": "Additional factors (optional)",
        "mekiki_road": "Frontage road width (m); use 0 if unknown",
        "mekiki_shape": "Lot shape (optional)",
        "shape_unknown": "Unknown",
        "shape_regular": "Regular",
        "shape_irreg": "Somewhat irregular",
        "mekiki_comp_h": "Optional comparables",
        "mekiki_comp_cap": "Paste one deal per line, e.g., “¥24m 150㎡” (nothing is stored).",
        "mekiki_comp_lbl": "Optional comparables",
        "mekiki_comp_ph": "¥24m 150㎡\n¥26.8m 142.36㎡",
        "mekiki_run": "Summarize how the price reads (reference)",
        "mekiki_ok": "Output is shown on the Results tab.",
        "mekiki_res_h": "Results (how the price reads in context)",
        "mekiki_need_input": "Please enter inputs on the Input tab and run the summary.",
        "mekiki_err_pa": "Enter price (JPY millions) and area (㎡).",
        "mekiki_subj": "Subject",
        "mekiki_lbl_addr": "Address (optional)",
        "mekiki_na": "(not provided)",
        "mekiki_lbl_price": "Price",
        "mekiki_lbl_area": "Area",
        "mekiki_lbl_up": "Unit price (indicative)",
        "mekiki_yen_m2": "JPY/㎡",
        "mekiki_man": "JPY m",
        "mekiki_lbl_walk": "Walk-time bucket",
        "mekiki_lbl_bcond": "Building conditions",
        "mekiki_yes": "Yes",
        "mekiki_no": "No",
        "mekiki_view_h": "How the price reads (reference)",
        "mekiki_why_h": "Why it reads that way",
        "mekiki_band_disp_h": "Reference band (indicative)",
        "mekiki_band_cap": "This is not a market “call”—only a draft band for communication. Calibrate to your operating policy.",
        "mekiki_lbl_reg": "Reference region",
        "mekiki_band_line": "Band: low {lo:,} / mid {mid:,} / high {hi:,} (JPY/㎡)",
        "mekiki_comp_pos_h": "Position vs. optional comparables",
        "mekiki_notes_h": "Important notice",
        "mekiki_notes_body": "This is not an Appraisal Report. It does not determine “fair value,” solicit transactions, or guarantee future prices. It organizes user inputs for discussion; you remain responsible for decisions.",
        "mekiki_ops_h": "Operations & disclaimer (required)",
        "mekiki_save_h": "Storage & privacy",
        "mekiki_ng_h": "Restricted wording (operations)",
        "mekiki_ng_cap": "Avoid definitive claims in UI, ads, and templates—examples below.",
        "mekiki_lbl_modest": "Conservative vs. the draft band (may read low)",
        "mekiki_lbl_ok": "Within the draft band (reasonable appearance)",
        "mekiki_lbl_high": "Above the draft band (may read strong)",
        "mekiki_r1": "Around/below the lower bound of the draft band.",
        "mekiki_r2": "Within the mid-to-upper part of the draft band.",
        "mekiki_r3": "Above the upper bound of the draft band.",
        "mekiki_r4": "Building conditions constrain flexibility—land-only benchmarks need care.",
        "mekiki_r5a": "Frontage under 4 m can trigger access/rebuildability issues—use caution.",
        "mekiki_r5b": "4–6 m frontage often drives wider quality spreads.",
        "mekiki_r5c": "≥6 m frontage tends to stabilize residential readability.",
        "mekiki_r5d": "Frontage unknown—access upside/downside not reflected.",
        "mekiki_r6a": "Regular lots typically enjoy better design flexibility and market acceptance.",
        "mekiki_r6b": "Irregular lots or narrow frontage can discount market appeal.",
        "mekiki_r6c": "Shape unknown—shape effects not reflected.",
        "mekiki_cc_none": "No comparables entered—comparison skipped.",
        "mekiki_cc_near": "Close to the median of entered comparables (~{med:,} JPY/㎡).",
        "mekiki_cc_hi": "Above the median of entered comparables (~{med:,} JPY/㎡) by about +{diff:,} JPY/㎡.",
        "mekiki_cc_lo": "Below the median of entered comparables (~{med:,} JPY/㎡) by about -{diff:,} JPY/㎡.",
        "mekiki_col_line": "Line",
        "mekiki_col_price": "Price (JPY m)",
        "mekiki_col_area": "Area (㎡)",
        "mekiki_col_up": "JPY/㎡",
        "reg_nat": "Japan-wide (indicative)",
        "reg_kansai": "Kansai (indicative)",
        "reg_kanto": "Greater Tokyo (indicative)",
        "wb_10": "≤10 min walk",
        "wb_15": "11–15 min walk",
        "wb_20": "16–20 min walk",
        "wb_21": "≥21 min walk",
        "match_story_h": "The story behind appraiser matching",
        "match_story_miss": "Image not found: place `{path}` under the `image` folder.",
        "match_concept_h": "Concept",
        "match_concept_body": """#### A natural path to the right specialist.
Price questions are rarely solved by a number alone—you need professional dialogue grounded in facts.

After **Price Insight** clarifies how a price reads, this matching entry is designed to connect clients with **real property appraisers**.
**From transparent price insight to professional advice**—one coherent journey toward sound real estate decisions.""",
        "match_open_hint": "Open the <strong>matching tool</strong> below to access <strong>Input</strong>, <strong>Results</strong>, and <strong>Operations & disclaimer</strong>.",
        "match_open_main": "Open matching tool (input / results / disclaimer)",
        "match_status": " — Matching tool (open)",
        "match_inner_hint": "Detailed forms will appear here as the tool is implemented (placeholder).",
        "match_open_an": "Open appraiser matching",
        "match_in_h": "Request input (under development)",
        "match_in_info": "Matcher forms and appraiser intake screens are planned.\nFor urgent matters, please use the Contact page.",
        "match_btn_contact": "Go to contact page",
        "match_out_h": "Matching results (under development)",
        "match_out_info": "Shortlists and status views will appear here after implementation.",
        "match_ops_h": "Operations & disclaimer (required)",
        "match_note_h": "Important notes",
        "match_note_cap": "Matching is introductory—we do not select appraisers or negotiate contracts on your behalf. Profiles originate from registrants; we do not warrant their accuracy.",
        "ai_ai03_name": "Appraisal report drafting assistant",
        "ai_ai03_tag": "See how chapters and issues can be structured",
        "ai_ai03_sum": "A Streamlit workspace to organize drafts and narratives for **Appraisal Reports** (supporting workflow only—not a substitute for a legally effective report).",
        "ai_ai03_note": "Features using API keys (e.g., OpenAI, maps) require local configuration.",
        "ai_ai04_name": "DCF / asset valuation dashboard (shisanhyo main)",
        "ai_ai04_tag": "Sketch income value in minutes",
        "ai_ai04_sum": "Hub folder for **AI analytics tools**—run DCF-style dashboards and worksheets locally.",
        "ai_ai04_note": "A fuller production app may exist separately; see the folder README.",
        "ai_ai05_name": "Comparable sales DB collector",
        "ai_ai05_tag": "Prototype how evidence piles accumulate",
        "ai_ai05_sum": "Streamlit utilities to collect and organize comparable evidence.",
        "ai_ai05_note": "Install dependencies on first run; a virtual environment is recommended.",
        "ai_ai06_name": "Income analysis platform (Income Intelligence)",
        "ai_ai06_tag": "Trace income drivers interactively",
        "ai_ai06_sum": "Engine to visualize and analyze income-producing real estate.",
        "ai_ai06_note": "Use the bundled requirements for dependencies.",
        "ai_ai07_name": "Redevelopment support dashboard",
        "ai_ai07_tag": "Bird’s-eye view of redevelopment scenarios",
        "ai_ai07_sum": "Dashboard supporting redevelopment and replacement studies.",
        "ai_ai07_note": "Launch from the tool folder as current working directory.",
        "ai_ai08_name": "Real estate data management dashboard",
        "ai_ai08_tag": "Explore indices and time series",
        "ai_ai08_sum": "Dashboard for indices, time series, and DCF-related data management.",
        "ai_ai08_note": "Data sources depend on your local configuration.",
        "ai_ai09_name": "Official land price movement dashboard",
        "ai_ai09_tag": "Map movements in official benchmarks",
        "ai_ai09_sum": "Review data requirements on the intro page, then explore movement rates on a **pydeck** web map (reference analysis; default CSV under `data/kokoku/`; override via `CHIKA_CSV_PATH` or Secrets).",
        "ai_ai09_note": "Card ⑨ opens the intro page in a new browser tab, then proceeds to the map dashboard. Consult official MLIT statistics for authoritative figures.",
        "contact_info_secrets_next": (
            "Configure **Secrets** as noted above so submissions can be delivered server-side on your next run.\n"
            "See `.streamlit/secrets.toml.example` at the top of the repository for full setup steps.\n"
            "Until then, use the button below to pre-fill your mail client."
        ),
        "contact_mailto_btn": "Send via mail client (subject and body pre-filled)",
        "contact_info_secrets_setup": (
            "Set the office inbox in Streamlit **Secrets** (Cloud: App → Settings → Secrets) using TOML keys "
            "`[contact] to_email` or `[smtp] to_email`. For automated delivery, configure **`[resend]`** "
            "(`api_key`, `from_email`, HTTPS recommended) or **`[smtp]`** "
            "(`host`, `user`, `password`, `to_email`).\n"
            "Locally, use `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)."
        ),
        "contact_svc_appraisal_intro": "Reference for sale / transfer pricing",
        "contact_svc_inheritance_gift": "Inheritance & gift valuation",
        "contact_svc_compensation": "Expropriation & loss compensation valuation",
        "contact_svc_litigation_rent": "Court-grade rent opinions (rent reset & litigation)",
        "contact_svc_corporate_asset": "Corporate real estate valuation (decision support)",
        "contact_svc_dcf_support": "Real estate securitization appraisal",
        "contact_svc_rent_support": "Ground rent, lease premiums & relocation allowance",
        "contact_svc_extra_chika": "Official land price trend bulletin",
        "contact_svc_extra_other": "Other",
    }
)


def _lang() -> str:
    return str(st.session_state.get(LANG_KEY, "ja"))


def t(key: str) -> str:
    """TEXTS 参照。欠損時は日本語↔英語でフォールバックし、未解決は空（キー名や None を UI に出さない）。"""
    if key is None:
        return ""
    k = str(key).strip()
    if not k:
        return ""
    lang = _lang()
    ja = TEXTS["ja"]
    en = TEXTS["en"]
    if lang == "ja":
        v = ja.get(k)
        if v is not None and str(v).strip() != "":
            return str(v)
        v_en = en.get(k)
        if v_en is not None and str(v_en).strip() != "":
            return str(v_en)
        return ""
    v_en = en.get(k)
    if v_en is not None and str(v_en).strip() != "":
        return str(v_en)
    v_ja = ja.get(k)
    if v_ja is not None and str(v_ja).strip() != "":
        return str(v_ja)
    return ""


def page_display_label(page_key: str) -> str:
    k = f"nav_{page_key}"
    return t(k) or str(page_key or "")


def breadcrumb_group_label(ja_group: str) -> str:
    m = {
        "企業・ご案内": "bc_grp_corp",
        "サービス・実績": "bc_grp_svc",
        "AI・ツール・研究": "bc_grp_ai",
        "ガバナンス・ポリシー": "bc_grp_pol",
    }
    if ja_group not in m:
        return ja_group
    return t(m[ja_group])


TEXTS["ja"].update(
    {
        "mekiki_disclaimer_top": (
            "※本サービスは不動産鑑定評価書の作成、適正価格の断定、不動産取引の勧誘、将来価値の保証を行いません。\n"
            "公開情報（利用者入力）に基づき、提示価格が市場の中でどのように「見えるか」を整理する参考情報です。\n"
            "最終判断は利用者自身で行ってください。"
        ),
        "mekiki_privacy_note": (
            "【保存しない方針】\n"
            "- 本ページは、入力内容を外部送信・学習・蓄積しません。\n"
            "- 画面表示のため、セッション中のみ一時的にメモリ上に保持される場合があります。\n"
        ),
        "matching_disclaimer_top": (
            "※本ページのマッチング案内は、不動産鑑定評価書の作成そのものや、特定の鑑定士との契約成立・成果を保証するものではありません。\n"
            "ご相談内容に応じた専門家との接点づくりを支援する参考情報です。最終的な依頼判断はご自身で行ってください。"
        ),
        "matching_privacy_note": (
            "【保存方針（ツール実装時）】\n"
            "- マッチング用の入力は、運用設計に応じて必要最小限の保存に留めます。\n"
            "- 現状のプレースホルダ画面では、永続保存を行いません（Streamlit セッションのみ）。\n"
            "- アクセスログ等のサーバーログはホスト側の設定に従います。"
        ),
    }
)
TEXTS["en"].update(
    {
        "mekiki_disclaimer_top": (
            "This tool does not produce an **Appraisal Report**, determine “fair market value,” solicit transactions, or guarantee future prices.\n"
            "Based on your inputs, it summarizes how an asking price may **read** against a draft reference band.\n"
            "You remain responsible for all decisions."
        ),
        "mekiki_privacy_note": (
            "**No-storage policy**\n"
            "- Inputs are not sent externally for training or retention.\n"
            "- Data may exist only temporarily in server memory for the active Streamlit session.\n"
        ),
        "matching_disclaimer_top": (
            "This page does not guarantee preparation of an **Appraisal Report**, matching success, or engagement with any specific appraiser.\n"
            "It is reference information to help you reach appropriate professionals. You decide whether to instruct counsel."
        ),
        "matching_privacy_note": (
            "**Retention (when implemented)**\n"
            "- Matching inputs will be minimized and retained only as required by operations.\n"
            "- The current placeholder does not persist data beyond the Streamlit session.\n"
            "- Server access logs follow the hosting configuration.\n"
        ),
    }
)


BASE_DIR = _APP_ROOT
# サイドバーは「PAGES に含まれるページ名文字列」だけを session に保持する（キーは _lib_nav_route）。
# 旧実装の nav_page / _lib_nav_page_idx は起動時に統合して削除し、二重状態による空ページを防ぐ。
NAV_PENDING_KEY = "_lib_nav_pending"
NAV_PAGE_ROUTER_KEY = "_lib_nav_route"
_LEGACY_NAV_IDX_KEY = "_lib_nav_page_idx"
_LEGACY_NAV_PAGE_KEY = "nav_page"


@st.cache_data(show_spinner=False)
def _cached_file_b64(path_resolved: str, cache_key: str) -> str:
    """画像ファイルを base64 に変換（cache_key に mtime と size を含め差し替えを確実に検知）。"""
    file_path = Path(path_resolved)
    if not file_path.is_file():
        return ""
    raw = file_path.read_bytes()
    ext = file_path.suffix.lower()
    if len(raw) <= 400_000:
        return base64.b64encode(raw).decode()
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(raw))
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            im.thumbnail((960, 960), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            return base64.b64encode(buf.getvalue()).decode()
        im = im.convert("RGB")
        im.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        # .png を CSS では image/png で埋め込むため、大きい RGB 画像も PNG で出す（JPEG にすると MIME 不一致で表示が壊れる）
        if ext == ".png":
            im.save(buf, format="PNG", optimize=True)
        else:
            im.save(buf, format="JPEG", quality=80, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def get_base64_image(rel_path: str) -> str:
    """CSS 埋め込み用。大きい画像は縮小して初回 WebSocket ペイロードの破綻・白画面を防ぐ。"""
    file_path = BASE_DIR / rel_path
    if not file_path.is_file():
        return ""
    try:
        st_info = file_path.stat()
        # mtime だけでは OS により更新が取りこぼされることがあるためサイズもキャッシュキーに含める
        cache_key = f"{st_info.st_mtime_ns}:{st_info.st_size}"
    except OSError:
        return ""
    return _cached_file_b64(str(file_path.resolve()), cache_key)


# TOP ナビカードは 8 枚分の背景を 1 本の <style> に埋め込む。フル解像度 PNG の base64 だけで
# 合計 ~15MB 超となり WebSocket / ブラウザが落ちるため縮小するが、Retina / wide 列でも破綻しない程度は確保する。
_TOPNAV_TILE_MAX_PX = 960
_TOPNAV_JPEG_QUALITY = 92
# 上記を変えたら必ず変える（@st.cache_data のキーに混ぜて古いエンコードを捨てる）
_TOPNAV_TILE_CACHE_VER = "960-q92-subs0"


@st.cache_data(show_spinner=False)
def _cached_topnav_card_bg_b64(path_resolved: str, cache_key: str) -> str:
    file_path = Path(path_resolved)
    if not file_path.is_file():
        return ""
    try:
        from PIL import Image

        raw = file_path.read_bytes()
        im = Image.open(io.BytesIO(raw))
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            rgb = Image.new("RGB", im.size, (255, 255, 255))
            rgb.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
            im = rgb
        else:
            im = im.convert("RGB")
        im.thumbnail((_TOPNAV_TILE_MAX_PX, _TOPNAV_TILE_MAX_PX), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(
            buf,
            format="JPEG",
            quality=_TOPNAV_JPEG_QUALITY,
            optimize=True,
            subsampling=0,  # 4:4:4 相当で色にじみを抑え鮮明に
        )
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def get_topnav_card_bg_b64(rel_path: str) -> str:
    """TOP ナビカード背景用（常に JPEG の base64。ペイロード肥大化を防ぐ）。"""
    file_path = BASE_DIR / rel_path
    if not file_path.is_file():
        return ""
    try:
        st_info = file_path.stat()
        cache_key = f"{st_info.st_mtime_ns}:{st_info.st_size}:{_TOPNAV_TILE_CACHE_VER}"
    except OSError:
        return ""
    return _cached_topnav_card_bg_b64(str(file_path.resolve()), cache_key)


@st.cache_data(show_spinner=False)
def _cached_hero_bg_b64(path_resolved: str, cache_key: str) -> str:
    """
    TOP 全画面ヒーロー背景用。通常の get_base64_image より解像度上限を高くし、
    cover 拡大時のピンボケ（過度な縮小エンコード）を抑える。
    """
    file_path = Path(path_resolved)
    if not file_path.is_file():
        return ""
    raw = file_path.read_bytes()
    # 〜2.4MB は再エンコードせずそのまま（画質優先。極端に大きい場合のみ縮小）
    if len(raw) <= 2_400_000:
        return base64.b64encode(raw).decode()
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(raw))
        try:
            from PIL import ImageOps

            im = ImageOps.exif_transpose(im)
        except Exception:
            pass
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            im.thumbnail((2880, 2880), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            return base64.b64encode(buf.getvalue()).decode()
        im = im.convert("RGB")
        im.thumbnail((2880, 2880), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=92, optimize=True, subsampling=0)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _mime_from_image_b64(b64_str: str) -> str:
    """
    data URI 用 MIME 推定。拡張子と実データがずれる場合の表示崩れを防ぐ（ヒーロー埋め込み専用）。
    """
    if not b64_str:
        return "image/jpeg"
    try:
        pad = (-len(b64_str)) % 4
        head = base64.b64decode(b64_str + ("=" * pad))[:16]
    except Exception:
        return "image/jpeg"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def get_hero_background_b64_for_css() -> str:
    """`image/ai_realestate_bg.jpg`（存在時）をヒーロー用に base64 化。"""
    file_path = BASE_DIR / "image" / "ai_realestate_bg.jpg"
    if not file_path.is_file():
        return ""
    try:
        st_info = file_path.stat()
        ck = f"{st_info.st_mtime_ns}:{st_info.st_size}"
    except OSError:
        return ""
    return _cached_hero_bg_b64(str(file_path.resolve()), ck)


@st.cache_data(show_spinner=False)
def _cached_logo_img_tag(path_resolved: str, logo_cache_key: str, alt_text: str) -> str:
    """1 ファイル分のロゴ img タグ（見つからない・失敗時は空文字）。"""
    p = Path(path_resolved)
    if not p.is_file():
        return ""
    try:
        from PIL import Image

        im = Image.open(p)
        im.thumbnail((480, 480), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        if im.mode in ("RGBA", "LA") or (
            im.mode == "P" and "transparency" in im.info
        ):
            im.save(buf, format="PNG", optimize=True)
            mime = "image/png"
        else:
            im.convert("RGB").save(buf, format="JPEG", quality=88, optimize=True)
            mime = "image/jpeg"
        b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception:
        try:
            raw = p.read_bytes()
        except OSError:
            return ""
        if len(raw) > 400_000:
            b64 = _cached_file_b64(str(p.resolve()), logo_cache_key)
            if not b64:
                return ""
        else:
            b64 = base64.b64encode(raw).decode()
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return (
        f'<img src="data:{mime};base64,{b64}" alt="{html.escape(alt_text, quote=True)}" '
        'style="max-width:240px;width:100%;height:auto;display:block;object-fit:contain;" />'
    )


def _logo_html_for_header() -> str:
    """
    TOP ヘッダー用ロゴ。列幅で st.image が潰れる環境があるため data URI の img で表示する。
    候補パスを順に試す（image / images / assets）。
    """
    candidates = (
        "image/logo.png",
        "images/logo.png",
        "assets/logo.png",
        "image/logo.jpg",
        "images/logo.jpg",
        "assets/logo.jpg",
    )
    for rel in candidates:
        p = BASE_DIR / rel
        if not p.is_file():
            continue
        try:
            st_logo = p.stat()
            lck = f"{st_logo.st_mtime_ns}:{st_logo.st_size}"
        except OSError:
            continue
        _alt = t("logo_alt")
        tag = _cached_logo_img_tag(str(p.resolve()), f"{lck}:{_alt}", _alt)
        if tag:
            return tag
    return ""


def inject_app_css() -> None:
    """サイト全体の CSS（ヒーロー背景は画像があれば使用、なければグラデーション）。"""
    if st.session_state.get("_lib_inject_app_css"):
        return
    st.session_state["_lib_inject_app_css"] = True
    bg_b64 = get_hero_background_b64_for_css() or get_base64_image("image/ai_realestate_bg.jpg")
    hero_mime = _mime_from_image_b64(bg_b64) if bg_b64 else "image/jpeg"
    # トップヒーロー：写真がある場合は .hero-visual 直下には載せず __bg に1回だけ載せる（二重 base64 回避）
    if bg_b64:
        hero_uri = f'url("data:{hero_mime};base64,{bg_b64}")'
        # 写真は .hero-visual__bg に1回だけ埋め込み（従来は .hero-visual と二重になりペイロード肥大）
        hero_bg_for_class = "none"
        hero_photo_var = hero_uri
        fullvp_root_bg = "none"
        fullvp_root_color = "#0b1628"
    else:
        hero_layers = (
            "linear-gradient(90deg, rgba(11,22,40,0.58) 0%, rgba(15,28,46,0.36) 50%, rgba(15,28,46,0.18) 100%), "
            "linear-gradient(135deg, #0F1C2E 0%, #182a46 55%, #0F1C2E 100%)"
        )
        hero_bg_for_class = hero_layers
        hero_photo_var = "none"
        fullvp_root_bg = hero_layers
        fullvp_root_color = "transparent"

    fullvp_fill = (
        f"background-color: {fullvp_root_color}; background-image: {fullvp_root_bg};"
        if bg_b64
        else ""
    )

    st.markdown(
        f"""
<style>
/* Base */
html, body, [data-testid="stAppViewContainer"] {{ background-color: #F7F5F2; }}
.block-container {{ max-width: 1120px; padding-top: 2rem; padding-bottom: 4rem; }}
/* TOP 専用の全幅オーバーライドは `if page == "TOP"` 内で注入（他ページは 1120px のまま） */
/* TOP 直上：パンくず「ホーム」・ブランド帯をブロック左端に揃える */
.block-container [data-testid="stMarkdownContainer"]:has(.lib-bc-home-row),
.block-container [data-testid="stMarkdownContainer"]:has(.lib-top-brand-strip--home) {{
  text-align: left !important;
}}
.block-container [data-testid="stMarkdownContainer"]:has(.lib-bc-home-row) p,
.block-container [data-testid="stMarkdownContainer"]:has(.lib-top-brand-strip--home) p {{
  text-align: left !important;
}}

h1, h2, h3 {{ color: #0F1C2E; font-weight: 800; letter-spacing: .01em; }}
p, li {{ line-height: 1.95; font-size: 1.05rem; color: #1f2937; }}

.small {{ color: #6B7280; font-size: .95rem; line-height: 1.8; }}
.hr {{ height: 1px; background: rgba(15,28,46,0.14); margin: 1.6rem 0; }}

/* Cards */
.card {{
  background: #fff;
  border: 1px solid rgba(15,28,46,0.12);
  border-radius: 16px;
  padding: 1.4rem 1.4rem;
  box-shadow: 0 14px 40px rgba(15,28,46,0.05);
}}

.hero {{
  background: #fff;
  border: 1px solid rgba(15,28,46,0.15);
  border-radius: 18px;
  padding: 2.6rem 2.4rem;
  box-shadow: 0 20px 60px rgba(15,28,46,0.08);
}}

.kicker {{
  color:#C9A24D;
  font-weight: 900;
  letter-spacing: .14em;
  font-size: .86rem;
}}

.badge {{
  display:inline-block;
  padding:.15rem .6rem;
  border-radius:999px;
  border:1px solid rgba(201,162,77,.40);
  background: rgba(201,162,77,.10);
  color:#0F1C2E;
  font-weight: 900;
  font-size: .86rem;
}}

.footer {{
  margin-top: 4.2rem;
  padding-top: 1.3rem;
  border-top: 1px solid rgba(15,28,46,0.15);
  font-size: .92rem;
  color: #6B7280;
}}

/* Sidebar（コード8）：文字をやや小さく */
[data-testid="stSidebar"] {{ background: #0F1C2E; font-size: 0.8125rem; }}
[data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.92); }}
[data-testid="stSidebar"] a {{ color: rgba(201,162,77,.95) !important; text-decoration:none; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  font-size: 1.02rem !important;
  line-height: 1.25 !important;
  font-weight: 800 !important;
  margin: 0 0 0.35rem 0 !important;
}}
[data-testid="stSidebar"] [data-baseweb="radio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stMarkdown"] p {{
  font-size: 0.78rem !important;
  line-height: 1.45 !important;
}}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
  font-size: 0.68rem !important;
  line-height: 1.45 !important;
  opacity: 0.9;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{
  font-size: 0.76rem !important;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
  gap: 0.35rem !important;
}}

/* TOP hero（背景＋オーバーレイを1レイヤーに統合） */
.hero-visual {{
  position: relative;
  min-height: 560px;
  border-radius: 22px;
  overflow: hidden;
  margin: 16px 0 14px 0;
  box-shadow:
    0 28px 80px rgba(15,28,46,0.32),
    0 0 0 1px rgba(201,162,77,0.18),
    inset 0 1px 0 rgba(255,255,255,0.06);
  border: 1px solid rgba(201,162,77,.24);
  background-image: {hero_bg_for_class};
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  color: rgba(255,255,255,.96);
  /* カスタム HTML ブロックで Source Sans 系のみだと日本語が豆腐化することがある */
  font-family:
    "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Hiragino Kaku Gothic Pro",
    "Yu Gothic UI", "Yu Gothic Medium", "Yu Gothic", "Meiryo", "MS PGothic",
    "Noto Sans JP", "Noto Sans CJK JP", "Takao Gothic", "IPAexGothic",
    system-ui, -apple-system, "Segoe UI", sans-serif;
}}
.hero-visual::before {{
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 22px;
  background:
    radial-gradient(ellipse 100% 70% at 0% 0%, rgba(201,162,77,0.14) 0%, transparent 45%),
    radial-gradient(ellipse 80% 50% at 100% 20%, rgba(59,130,246,0.08) 0%, transparent 40%),
    linear-gradient(180deg, rgba(0,0,0,0.12) 0%, rgba(0,0,0,0.38) 55%, rgba(0,0,0,0.62) 100%);
}}
.hero-visual::after {{
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 22px;
  opacity: 0.35;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
}}

.hero-visual .hero-inner {{
  position: relative;
  z-index: 1;
  min-height: 560px;
  padding: 52px 48px 44px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}}

.hero-visual .eyebrow {{
  letter-spacing: .16em;
  font-weight: 800;
  font-size: .78rem;
  color: rgba(201,162,77,.98);
  text-transform: uppercase;
  margin-bottom: 8px;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}}
.hero-visual .hero-tagline-jp {{
  margin: 0 0 8px 0;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: rgba(201,162,77,.98);
}}
.hero-visual .hero-footnote {{
  margin: 16px 0 0 0;
  padding: 0;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: rgba(255,255,255,.86);
}}

.hero-visual .hero-tagline-en {{
  font-size: .95rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: rgba(255,255,255,.72);
  margin-bottom: 6px;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}}

.hero-visual .headline {{
  font-size: clamp(1.75rem, 4.2vw, 2.5rem);
  line-height: 1.16;
  font-weight: 900;
  letter-spacing: .02em;
  color: rgba(255,255,255,.99);
  margin: 0 0 12px 0;
  max-width: 920px;
  text-shadow: 0 2px 24px rgba(0,0,0,0.35);
}}

.hero-visual .gold-line {{
  width: 88px;
  height: 4px;
  background: #C9A24D;
  border-radius: 10px;
  margin-bottom: 14px;
}}

.hero-visual .subcopy {{
  font-size: 1.05rem;
  line-height: 1.82;
  color: rgba(255,255,255,.90);
  max-width: 820px;
  margin-bottom: 14px;
}}

.hero-visual .hero-badge {{
  display: inline-block;
  margin-bottom: 14px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(201,162,77,.42);
  background: rgba(201,162,77,.14);
  color: rgba(255,255,255,.95);
  font-weight: 800;
  font-size: .8rem;
  letter-spacing: .04em;
}}

.hero-visual .pillbar {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 4px;
}}

.hero-visual .pill {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(201,162,77,.28);
  background: rgba(255,255,255,.08);
  color: rgba(255,255,255,.92);
  font-weight: 800;
  font-size: .88rem;
}}

.hero-visual .pill b {{ color: rgba(201,162,77,.96); }}

.hero-visual .hero-stats {{
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem 1.75rem;
  margin: 0.35rem 0 1rem 0;
  padding-top: 0.25rem;
}}
.hero-visual .hero-stat {{
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 5.5rem;
}}
.hero-visual .hero-stat .num {{
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: 0.02em;
  color: rgba(201,162,77,.98);
  line-height: 1.1;
}}
.hero-visual .hero-stat .lbl {{
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255,255,255,.55);
}}

/* TOP ヒーロー：ビューポートいっぱい（写真は __bg に分離し filter を写真のみに適用） */
.hero-visual.hero-visual--fullvp {{
  width: 100vw;
  max-width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  margin-top: -2rem;
  margin-bottom: 1.25rem;
  min-height: 100vh;
  min-height: 100dvh;
  border-radius: 0;
  box-shadow: 0 20px 64px rgba(15,28,46,0.22);
  /* 画像あり時：フォールバック紺＋写真は子レイヤー。画像なし時は fullvp_fill 空で親のグラデを継承 */
  {fullvp_fill}
  --lib-hero-photo: {hero_photo_var};
  background-size: cover;
  background-position: center center;
  background-attachment: scroll;
  image-rendering: auto;
}}
/* トップ全画面ヒーロー専用：背景写真レイヤー（鮮度：軽い露出・コントラスト・彩度＋わずかなオーバーサンプリングで解像感） */
.hero-visual.hero-visual--fullvp .hero-visual__bg {{
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image: var(--lib-hero-photo, none);
  background-size: cover;
  background-position: center 36%;
  background-repeat: no-repeat;
  filter: brightness(1.06) contrast(1.08) saturate(1.07);
  transform: scale(1.035);
  transform-origin: 50% 40%;
}}
@media (max-width: 768px) {{
  .hero-visual.hero-visual--fullvp .hero-visual__bg {{
    background-position: center 34%;
    transform: scale(1.05);
    filter: brightness(1.07) contrast(1.06) saturate(1.06);
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  .hero-visual.hero-visual--fullvp .hero-visual__bg {{
    transform: none;
  }}
}}
.hero-visual.hero-visual--fullvp::before {{
  border-radius: 0;
  z-index: 1;
  /* 左コピー可読用スクリーム＋下方向ヴィネットを紺寄りに調整（重すぎない範囲でコントラスト確保） */
  background:
    linear-gradient(90deg, rgba(11,22,40,0.76) 0%, rgba(15,28,46,0.38) 36%, rgba(28,56,96,0.12) 72%, rgba(255,255,255,0.04) 100%),
    radial-gradient(ellipse 90% 55% at 15% 15%, rgba(201,162,77,0.085) 0%, transparent 54%),
    radial-gradient(ellipse 72% 48% at 90% 20%, rgba(96,165,250,0.055) 0%, transparent 46%),
    linear-gradient(165deg, rgba(10,20,36,0.15) 0%, rgba(8,16,30,0.24) 44%, rgba(6,12,24,0.48) 100%);
}}
/* ノイズレイヤは写真のピンボケ感を増すため fullvp ではオフ */
.hero-visual.hero-visual--fullvp::after {{
  display: none;
}}
.hero-visual.hero-visual--fullvp .hero-inner {{
  position: relative;
  z-index: 2;
  min-height: 100vh;
  min-height: 100dvh;
  padding: clamp(28px, 5vw, 56px) clamp(22px, 6vw, 80px) clamp(36px, 8vh, 96px);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: flex-start;
  box-sizing: border-box;
}}
/* ガラス風パネル：コントラストとデザイン性を両立 */
.hero-visual.hero-visual--fullvp .hero-copy-panel {{
  position: relative;
  z-index: 1;
  max-width: min(36.5rem, 100%);
  width: 100%;
  padding: clamp(1.35rem, 3.2vw, 2.1rem) clamp(1.35rem, 3vw, 2.35rem);
  border-radius: clamp(14px, 2vw, 22px);
  border: 1px solid rgba(201, 162, 77, 0.28);
  background: rgba(15, 28, 46, 0.82);
  box-shadow:
    0 28px 56px rgba(0, 0, 0, 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset,
    0 1px 0 rgba(255, 255, 255, 0.07) inset;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}
@supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
  .hero-visual.hero-visual--fullvp .hero-copy-panel {{
    background: linear-gradient(
      155deg,
      rgba(15, 28, 46, 0.52) 0%,
      rgba(15, 28, 46, 0.38) 55%,
      rgba(24, 40, 62, 0.45) 100%
    );
    -webkit-backdrop-filter: blur(16px) saturate(1.12);
    backdrop-filter: blur(16px) saturate(1.12);
  }}
}}
.hero-visual.hero-visual--fullvp .hero-copy-panel::before {{
  content: "";
  position: absolute;
  z-index: 0;
  top: 0;
  left: 1.25rem;
  right: 1.25rem;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, rgba(201,162,77,0.85), rgba(201,162,77,0.35), transparent);
  opacity: 0.9;
  pointer-events: none;
}}
.hero-visual.hero-visual--fullvp .hero-copy-panel > * {{
  position: relative;
  z-index: 1;
}}
.hero-visual.hero-visual--fullvp .hero-tagline-jp {{
  margin-bottom: 0.35rem;
  font-size: clamp(0.78rem, 1.9vw, 0.88rem);
}}
.hero-visual.hero-visual--fullvp .hero-micro-en {{
  margin: 0 0 1rem 0;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.42);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}}
.hero-visual.hero-visual--fullvp .headline {{
  font-size: clamp(1.65rem, 4.8vw, 2.35rem);
  line-height: 1.18;
  margin-bottom: 14px;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}}
.hero-visual.hero-visual--fullvp .gold-line {{
  width: min(7.5rem, 42vw);
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #e8c66a 0%, #c9a24d 45%, #8b6914 100%);
  box-shadow: 0 0 20px rgba(201, 162, 77, 0.35);
  margin-bottom: 1rem;
}}
.hero-visual.hero-visual--fullvp .subcopy {{
  font-size: clamp(0.98rem, 2.4vw, 1.08rem);
  line-height: 1.78;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0;
  text-shadow: none;
}}
.hero-visual.hero-visual--fullvp .hero-footnote {{
  margin-top: 1.15rem;
  padding: 0.45rem 0.85rem;
  display: inline-block;
  border-radius: 999px;
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.88);
  background: rgba(201, 162, 77, 0.12);
  border: 1px solid rgba(201, 162, 77, 0.35);
}}
.hero-visual.hero-visual--fullvp .hero-stats {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem 1.25rem;
  max-width: 28rem;
}}
@media (max-width: 640px) {{
  .hero-visual.hero-visual--fullvp .hero-stats {{
    grid-template-columns: 1fr;
    max-width: 100%;
  }}
}}
.hero-visual.hero-visual--fullvp .pillbar {{
  max-width: 40rem;
}}

/* TOP ブランド帯（ロゴ＋社名） */
.lib-top-brand-strip {{
  margin: 0 0 6px 0;
  padding: 14px 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #faf8f5 100%);
  border: 1px solid rgba(15, 28, 46, 0.08);
  box-shadow: 0 8px 28px rgba(15, 28, 46, 0.06);
}}
.lib-top-brand-strip--home {{
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  justify-items: start;
  justify-content: start;
  text-align: left;
  column-gap: clamp(1rem, 3vw, 1.75rem);
  row-gap: 0.75rem;
  padding: clamp(14px, 2.5vw, 20px) clamp(16px, 3vw, 24px);
  margin: 0 0 12px 0;
  width: 100%;
  box-sizing: border-box;
}}
.lib-top-brand-strip__text {{
  text-align: left;
  justify-self: start;
  width: 100%;
  max-width: 100%;
}}
@media (max-width: 520px) {{
  .lib-top-brand-strip--home {{
    grid-template-columns: 1fr;
    justify-items: start;
  }}
}}
.lib-top-brand-strip__logo img {{
  display: block;
  max-width: min(200px, 46vw) !important;
  width: 100%;
  height: auto;
}}
.lib-top-brand-strip__name {{
  display: block;
  font-size: clamp(1.45rem, 4.2vw, 1.95rem);
  font-weight: 800;
  color: #0f1c2e;
  letter-spacing: 0.03em;
  line-height: 1.2;
  padding: 2px 0 4px 0;
  border-left: 4px solid #c9a24d;
  padding-left: 1rem;
  margin-left: 2px;
}}
@media (max-width: 520px) {{
  .lib-top-brand-strip__name {{
    border-left: none;
    padding-left: 0;
    border-bottom: 3px solid #c9a24d;
    padding-bottom: 6px;
    margin-left: 0;
  }}
}}

/* 言語切替マーカー（非表示）。詳細スタイルはグローバル secondary 定義の直後に配置 */
.lib-lang-switcher-mark {{
  display: none !important;
}}

/* ボタン — 紺ベースで統一（ラベルが内側 span/p にあるため子要素まで白を指定） */
[data-testid="stButton"] button {{
  font-weight: 700 !important;
}}
[data-testid="stButton"] button:hover {{
  border-color: #182a46 !important;
}}
[data-testid="stButton"] button:focus-visible {{
  box-shadow: 0 0 0 2px #F7F5F2, 0 0 0 4px #C9A24D !important;
}}
/* secondary — 白地＋黒字（子要素も黒） */
[data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stButton"] button[data-testid="baseButton-secondary"] * {{
  background-color: transparent !important;
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  fill: #000000 !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-secondary"] {{
  background-color: #ffffff !important;
  border: 2px solid #0F1C2E !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover * {{
  background-color: rgba(15, 28, 46, 0.07) !important;
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover {{
  border-color: #182a46 !important;
}}
/* primary — 紺地＋白字（子要素・SVG アイコンまで） */
[data-testid="stButton"] button[data-testid="baseButton-primary"],
[data-testid="stButton"] button[data-testid="baseButton-primary"] * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-primary"] {{
  background-color: #0F1C2E !important;
  border-color: #0F1C2E !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover * {{
  background-color: transparent !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover {{
  background-color: #182a46 !important;
  border-color: #182a46 !important;
}}
/* kind=secondary（Streamlit 1.5x）：data-testid 差異でも黒字・白地を維持 */
[data-testid="stButton"] button[kind="secondary"],
[data-testid="stButton"] button[kind="secondary"] * {{
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  fill: #000000 !important;
}}
[data-testid="stButton"] button[kind="secondary"] {{
  background-color: #ffffff !important;
  border: 2px solid #0F1C2E !important;
}}
[data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stButton"] button[kind="secondary"]:hover * {{
  background-color: rgba(15, 28, 46, 0.07) !important;
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}}

/* 言語切替 J|E（ヘッダー右上）：極小・薄地。マーク直後の横3列のみ対象（他ボタンに波及しない） */
[data-testid="element-container"]:has(.lib-lang-switcher-mark) {{
  display: flex !important;
  justify-content: flex-end !important;
  width: 100% !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"] {{
  gap: 0.08rem 0.14rem !important;
  align-items: center !important;
  justify-content: flex-end !important;
  width: 100% !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1)
  [data-testid="stButton"]
  button,
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3)
  [data-testid="stButton"]
  button {{
  font-size: 0.62rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  min-height: 1.28rem !important;
  padding: 0.04rem 0.22rem !important;
  line-height: 1 !important;
  border-width: 1px !important;
  border-radius: 5px !important;
  background-color: rgba(255, 255, 255, 0.35) !important;
  border-color: rgba(15, 28, 46, 0.16) !important;
  color: #0f1c2e !important;
  -webkit-text-fill-color: #0f1c2e !important;
  box-shadow: none !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1)
  [data-testid="stButton"]
  button *,
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3)
  [data-testid="stButton"]
  button * {{
  color: #0f1c2e !important;
  -webkit-text-fill-color: #0f1c2e !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1)
  [data-testid="stButton"]
  button:hover,
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3)
  [data-testid="stButton"]
  button:hover {{
  background-color: rgba(15, 28, 46, 0.07) !important;
  border-color: rgba(15, 28, 46, 0.35) !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1)
  [data-testid="stButton"]
  button:hover *,
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3)
  [data-testid="stButton"]
  button:hover * {{
  color: #0f1c2e !important;
  -webkit-text-fill-color: #0f1c2e !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1) [data-testid="stButton"],
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3) [data-testid="stButton"] {{
  min-width: 0 !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(1)
  [data-testid="stButton"]
  button:disabled,
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(3)
  [data-testid="stButton"]
  button:disabled {{
  opacity: 0.42 !important;
  cursor: default !important;
}}
[data-testid="element-container"]:has(.lib-lang-switcher-mark)
  + [data-testid="element-container"]
  [data-testid="stHorizontalBlock"]
  > [data-testid="column"]:nth-child(2)
  [data-testid="stMarkdownContainer"]
  p {{
  margin: 0 !important;
  padding: 0.18rem 0 0 0 !important;
  text-align: center !important;
  color: #94a3b8 !important;
  font-weight: 600 !important;
  font-size: 0.58rem !important;
}}
@media (max-width: 520px) {{
  [data-testid="element-container"]:has(.lib-lang-switcher-mark)
    + [data-testid="element-container"]
    [data-testid="stHorizontalBlock"]
    > [data-testid="column"]:nth-child(1)
    [data-testid="stButton"]
    button,
  [data-testid="element-container"]:has(.lib-lang-switcher-mark)
    + [data-testid="element-container"]
    [data-testid="stHorizontalBlock"]
    > [data-testid="column"]:nth-child(3)
    [data-testid="stButton"]
    button {{
    font-size: 0.58rem !important;
    min-height: 1.22rem !important;
    padding: 0.03rem 0.18rem !important;
  }}
}}

/* data-testid が付かない環境向け：secondary 以外は白字（kind=secondary は除外） */
[data-testid="stButton"] button:not([data-testid="baseButton-secondary"]):not([kind="secondary"]),
[data-testid="stButton"] button:not([data-testid="baseButton-secondary"]):not([kind="secondary"]) * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}

/* タブ見出し（入力／結果 等）を黒字に */
[data-testid="stTabs"] button,
[data-testid="stTabs"] button p,
[data-testid="stTabs"] button span,
[data-testid="stTabs"] [role="tab"],
[data-testid="stTabs"] [role="tab"] * {{
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stTabs"] [data-baseweb="tab"] * {{
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}}

/* st.link_button（stButton とは別コンポーネント）— primary は紺地＋白字 */
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"],
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"] * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"] {{
  background-color: #0F1C2E !important;
  border-color: #0F1C2E !important;
}}
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"]:hover,
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"]:hover * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"]:hover {{
  background-color: #182a46 !important;
  border-color: #182a46 !important;
}}
[data-testid="stLinkButton"] a[data-testid="stBaseLinkButton-primary"]:visited {{
  color: #ffffff !important;
}}

/* AI分析ツール：免責・カタログ文言の読みやすさ */
.ai-page-disclaimer {{
  background: rgba(255, 193, 7, 0.11);
  border-left: 4px solid #C9A24D;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 1.02rem;
  line-height: 1.9;
  color: #1f2937;
  margin: 0 0 1.1rem 0;
}}
p.ai-tool-title {{
  color: #0F1C2E;
  font-weight: 800;
  font-size: 1.05rem;
  line-height: 1.5;
  margin: 0.85rem 0 0.4rem 0;
  min-height: 2.85em;
}}
p.ai-tool-tag {{
  color: #4b5563;
  font-size: 0.93rem;
  line-height: 1.62;
  margin: 0 0 0.85rem 0;
  min-height: 3.05em;
}}

/* ツール体験デモ（st.dialog）：濃紺背景 → 白字、白背景 → 黒字 */

/* 濃紺（primary）：背景 #0F1C2E／ホバー #182a46、ラベル・子要素・SVG は白 */
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"] *,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"],
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"] *,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"] *,
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"],
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"] *,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"] *,
[role="dialog"] [data-testid="stButton"] button[kind="primary"],
[role="dialog"] [data-testid="stButton"] button[kind="primary"] * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"],
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"],
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"],
[role="dialog"] [data-testid="stButton"] button[kind="primary"] {{
  background-color: #0F1C2E !important;
  border-color: #0F1C2E !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover *,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"]:hover *,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover *,
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"]:hover *,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover *,
[role="dialog"] [data-testid="stButton"] button[kind="primary"]:hover,
[role="dialog"] [data-testid="stButton"] button[kind="primary"]:hover * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  fill: #ffffff !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[kind="primary"]:hover,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
[role="dialog"] [data-testid="stButton"] button[kind="primary"]:hover {{
  background-color: #182a46 !important;
  border-color: #182a46 !important;
}}

/* 白背景（secondary 等）：黒字（サイト全体の「非 secondary は白字」対策） */
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"] *,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"],
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"] *,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"] *,
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"],
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"] *,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"] *,
[role="dialog"] [data-testid="stButton"] button[kind="secondary"],
[role="dialog"] [data-testid="stButton"] button[kind="secondary"] * {{
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  fill: #111827 !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"],
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"],
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"],
[role="dialog"] [data-testid="stButton"] button[kind="secondary"] {{
  background-color: #ffffff !important;
  border: 2px solid #0F1C2E !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover *,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"]:hover *,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover *,
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"]:hover *,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover *,
[role="dialog"] [data-testid="stButton"] button[kind="secondary"]:hover,
[role="dialog"] [data-testid="stButton"] button[kind="secondary"]:hover * {{
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  fill: #111827 !important;
}}
[data-testid="stDialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stDialog"] [data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stModal"] [data-testid="stButton"] button[kind="secondary"]:hover,
[role="dialog"] [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover,
[role="dialog"] [data-testid="stButton"] button[kind="secondary"]:hover {{
  background-color: rgba(15, 28, 46, 0.06) !important;
}}

/* tertiary／その他（primary 以外）：黒字のフォールバック */
[data-testid="stDialog"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]),
[data-testid="stDialog"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]) *,
[data-testid="stModal"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]),
[data-testid="stModal"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]) *,
[role="dialog"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]),
[role="dialog"] [data-testid="stButton"] button:not([data-testid="baseButton-primary"]):not([kind="primary"]) * {{
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  fill: #111827 !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def inject_global_ui_css() -> None:
    """
    全体の余白リズムを整理し、フローティング導線と本文末尾の干渉を避けるための下余白を付与する。
    メイン列・block-container 中心に限定し、副作用を抑える。
    """
    if st.session_state.get("_lib_global_ui_css"):
        return
    st.session_state["_lib_global_ui_css"] = True
    st.markdown(
        """
<style>
/* ========== グローバル余白・フローティング導線（inject_global_ui_css） ========== */
section[data-testid="stMain"] .block-container {
  padding-top: 1.7rem !important;
  padding-bottom: 5.35rem !important;
  box-sizing: border-box !important;
}
@media (max-width: 768px) {
  section[data-testid="stMain"] .block-container {
    padding-top: 1.45rem !important;
    padding-bottom: 5.65rem !important;
  }
}
section[data-testid="stMain"] h1 {
  margin-top: 0.2rem !important;
  margin-bottom: 0.72rem !important;
}
section[data-testid="stMain"] h2 {
  margin-top: 1.2rem !important;
  margin-bottom: 0.52rem !important;
}
section[data-testid="stMain"] h3 {
  margin-top: 0.95rem !important;
  margin-bottom: 0.42rem !important;
}
section[data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
  margin-bottom: 0.62rem !important;
}
section[data-testid="stMain"] [data-testid="stVerticalBlock"] {
  gap: 0.82rem !important;
}
section[data-testid="stMain"] .hr {
  margin: 1.45rem 0 1.65rem !important;
}
section[data-testid="stMain"] .card {
  margin-bottom: 1.05rem !important;
}
section[data-testid="stMain"] [data-testid="stForm"] {
  margin-bottom: 0.35rem !important;
}
section[data-testid="stMain"] [data-testid="stTextInput"],
section[data-testid="stMain"] [data-testid="stTextArea"],
section[data-testid="stMain"] [data-testid="stSelectbox"] {
  margin-bottom: 0.28rem !important;
}
/* フローティング J|S ホスト（components が親 document に挿入） */
#lib-floating-nav-host {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 99950;
}
#lib-floating-nav-host .lib-fn-btn {
  pointer-events: auto;
  position: fixed;
  font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic UI", Meiryo, sans-serif;
  font-weight: 700;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  padding: 0.42rem 0.74rem;
  border-radius: 10px;
  border: 1px solid rgba(15, 28, 46, 0.2);
  background: rgba(255, 255, 255, 0.94);
  color: #0f1c2e;
  box-shadow: 0 6px 22px rgba(15, 28, 46, 0.12);
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.15s ease, box-shadow 0.18s ease;
}
#lib-floating-nav-host .lib-fn-btn:hover {
  background: #ffffff;
  border-color: rgba(201, 162, 77, 0.55);
  transform: translateY(-1px);
  box-shadow: 0 8px 26px rgba(15, 28, 46, 0.14);
}
#lib-floating-nav-host .lib-fn-btn:active {
  transform: translateY(0);
}
#lib-floating-nav-host .lib-fn-back {
  top: 4.85rem;
  right: clamp(0.55rem, 2.2vw, 1.15rem);
}
#lib-floating-nav-host .lib-fn-top {
  bottom: calc(1.05rem + env(safe-area-inset-bottom, 0px));
  right: clamp(0.55rem, 2.2vw, 1.15rem);
}
@media (max-width: 768px) {
  #lib-floating-nav-host .lib-fn-btn {
    font-size: 0.84rem;
    padding: 0.5rem 0.88rem;
    min-height: 2.65rem;
    border-radius: 11px;
  }
  #lib-floating-nav-host .lib-fn-back {
    top: 4.15rem;
  }
  #lib-floating-nav-host .lib-fn-top {
    bottom: calc(1.15rem + env(safe-area-inset-bottom, 0px));
  }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_floating_nav_buttons() -> None:
    """
    スクロールしても見える「戻る」「TOPへ」を親ウィンドウに固定配置する。
    戻るは ?_lib_back=1 でサーバ側 go_back_page と同期（ブラウザ履歴ではない）。
    """
    _lb = json.dumps(t("float_nav_back"), ensure_ascii=False)
    _lt = json.dumps(t("float_nav_top"), ensure_ascii=False)
    _lc = json.dumps(_lang(), ensure_ascii=False)
    _js = f"""
<script>
(function () {{
  try {{
    var p = window.parent.document;
    var L = {_lc};
    var host = p.getElementById("lib-floating-nav-host");
    if (host && host.getAttribute("data-lang") === L) return;
    if (host) host.remove();
    host = p.createElement("div");
    host.id = "lib-floating-nav-host";
    host.setAttribute("data-lang", L);
    host.setAttribute("aria-live", "polite");
    var back = p.createElement("button");
    back.type = "button";
    back.className = "lib-fn-btn lib-fn-back";
    back.id = "lib-fn-back-btn";
    back.textContent = {_lb};
    back.setAttribute("aria-label", {_lb});
    var topb = p.createElement("button");
    topb.type = "button";
    topb.className = "lib-fn-btn lib-fn-top";
    topb.id = "lib-fn-top-btn";
    topb.textContent = {_lt};
    topb.setAttribute("aria-label", {_lt});
    back.onclick = function () {{
      try {{
        var u = new URL(window.parent.location.href);
        u.searchParams.set("_lib_back", "1");
        window.parent.location.assign(u.toString());
      }} catch (e) {{}}
    }};
    topb.onclick = function () {{
      try {{
        var d = window.parent.document;
        var a = d.querySelector('[data-testid="stAppViewContainer"]');
        if (a) a.scrollTo({{ top: 0, behavior: "smooth" }});
        var m = d.querySelector("section.main");
        if (m) m.scrollTop = 0;
        window.parent.scrollTo({{ top: 0, behavior: "smooth" }});
      }} catch (e) {{}}
    }};
    host.appendChild(back);
    host.appendChild(topb);
    p.body.appendChild(host);
  }} catch (e) {{}}
}})();
</script>
"""
    components.html(_js, height=0, width=0)


# ------------------------------------------------------------
# 1) グローバル CSS（set_page_config はファイル先頭で実行済み）
# ------------------------------------------------------------
inject_app_css()
inject_global_ui_css()
inject_top_corporate_home_css()
inject_hidden_sidebar_css()

# ------------------------------------------------------------
# 3) Content Data（文章はここで一元管理）
# ------------------------------------------------------------

# 公開リポにローカルパス・起動コマンドは載せない。フル版は `.streamlit/secrets.toml` の
# `[ai_tools_private.<key_slug>]`（または Streamlit Cloud の Secrets）でのみ上書きする。
PUBLIC_AI_PROJECTS_BASE: List[Dict[str, Any]] = [
    {
        "id": "③",
        "key_slug": "ai03",
        "name": "AI鑑定評価書作成アプリ",
        "tagline": "論点整理・章立てのイメージをつかむ",
        "summary": "鑑定評価書の作成・下書き・整理を支援するStreamlitアプリです。資料入力や文章化の補助を想定しています（参考・作業補助であり、法的効力のある鑑定評価書そのものの代替ではありません）。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "APIキー（例：OpenAI、地図）を利用する機能は、各所定の設定ファイルや環境変数が必要です。",
    },
    {
        "id": "④",
        "key_slug": "ai04",
        "name": "DCF・資産評価ダッシュボード（shisanhyoメ・イン）",
        "tagline": "収益価格の骨格を数分で体感",
        "summary": "ライブラリーズの**AI分析ツール群の拠点**となるフォルダです。DCF中心のダッシュボードや試算表をローカルで実行・検証できます。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "実務フル機能版は別エントリの Streamlit アプリがある場合があります（配布フォルダ内の README を参照）。",
    },
    {
        "id": "⑤",
        "key_slug": "ai05",
        "name": "CR事例DB自動収集システム",
        "tagline": "事例の集積イメージを掴む",
        "summary": "事例データベースの収集・整理を行うStreamlitアプリです。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "初回のみ依存パッケージの導入が必要です。仮想環境の利用を推奨します。",
    },
    {
        "id": "⑥",
        "key_slug": "ai06",
        "name": "収益分析プラットフォーム（Income Intelligence）",
        "tagline": "収益の筋道をダイヤルで追う",
        "summary": "収益不動産の分析・可視化を行うエンジンです。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "依存関係は配布パッケージ同梱の requirements を使用します。",
    },
    {
        "id": "⑦",
        "key_slug": "ai07",
        "name": "開発支援ダッシュボード",
        "tagline": "再開発シナリオの考え方を俯瞰",
        "summary": "再開発・建替え等の検討を支援するダッシュボードです。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "ツール用フォルダをカレントにして起動します。",
    },
    {
        "id": "⑧",
        "key_slug": "ai08",
        "name": "不動産データ管理ダッシュボード",
        "tagline": "指数・時系列の見え方を体感",
        "summary": "市場指数・時系列・DCF関連のデータ管理・可視化用ダッシュボードです。",
        "setup_cmds": None,
        "run_cmds": [],
        "notes": "データソースやAPIの有無はローカル環境の設定に依存します。",
    },
    {
        "id": "⑨",
        "key_slug": "ai09",
        "name": "公的価格変動ダッシュボード",
        "tagline": "公示・路線の変動を地図マッピング",
        "summary": "まず **案内ページ** でデータ要件を確認し、**Web 上の地図（pydeck）** で公示地点の変動率を俯瞰します（参考分析・既定 CSV はリポジトリの `data/kokoku/`。環境変数 `CHIKA_CSV_PATH` または Secrets の `CHIKA_CSV_PATH` / `[chika] csv_path` で変更可）。",
        "setup_cmds": None,
        "run_cmds": [],
        "open_multipage_new_tab_path": CHIKA_MAP_INTRO_URL_PATH,
        "notes": "⑨ のカードは **新しいブラウザタブ** で **案内ページ**を開き、そこから地図ダッシュボードへ進みます。公式統計は国土交通省等を参照してください。",
    },
]


def get_resolved_ai_projects() -> List[Dict[str, Any]]:
    """Secrets をマージするため ``st.secrets`` に触れる。``@st.cache_data`` 内では使えないのでキャッシュしない。"""
    return merge_ai_tool_private_overrides(PUBLIC_AI_PROJECTS_BASE)


def get_resolved_ai_projects_for_catalog() -> List[Dict[str, Any]]:
    return [p for p in get_resolved_ai_projects() if p.get("key_slug") != "ai09"]


def get_office_inbox_email() -> str:
    """[contact] / [smtp] / 環境変数の宛先を ``build_smtp_overrides_from_secrets_dict`` と同じ規則で返す。"""
    try:
        ov = build_smtp_overrides_from_secrets_dict(st.secrets)
        if ov:
            te = str(ov.get("to_email") or "").strip()
            if te:
                return te
    except Exception:
        pass
    return (os.environ.get("CONTACT_TO_EMAIL") or "").strip()


def build_smtp_overrides_for_submit() -> Optional[Dict[str, Any]]:
    """secrets の [smtp] に加え、to_email 未設定なら [contact].to_email を補完。"""
    try:
        return build_smtp_overrides_from_secrets_dict(st.secrets)
    except Exception:
        return None


def build_resend_overrides_for_submit() -> Optional[Dict[str, Any]]:
    """secrets の [resend] と [contact].to_email 等をマージ（Resend API 用）。"""
    try:
        return build_resend_overrides_from_secrets_dict(st.secrets)
    except Exception:
        return None


def build_contact_mailto_href(to_addr: str, payload: Dict[str, Any]) -> str:
    subj = f"{t('mailto_subj_prefix')} {payload.get('purpose', '')}"
    body = "\n".join(
        [
            t("mailto_body_note"),
            "",
            f"{t('mailto_purpose_lbl')}: {payload.get('purpose', '')}",
            f"{t('mailto_name_lbl')}: {payload.get('name', '')}",
            f"{t('mailto_email_lbl')}: {payload.get('email', '')}",
            f"{t('mailto_tel_lbl')}: {payload.get('tel') or ''}",
            f"{t('mailto_addr_lbl')}: {payload.get('address') or ''}",
            "",
            t("mailto_msg_hdr"),
            payload.get("message", ""),
        ]
    )
    return f"mailto:{to_addr}?subject={quote(subj)}&body={quote(body)}"


PROFILE = {
    "name": "磯尾 隆光",
    "title": "不動産鑑定士",
    "edu": "同志社大学 経済学部 卒業",
    "career": "大手不動産鑑定会社に約40年在籍（地価公示等公的評価・証券化鑑定評価・企業資産評価・訴訟案件等に従事）",
    "cases": "鑑定評価件数 2,000件以上",
    "public": "(元)品川区財産価格審議会委員、(現)大阪市不動産評価審議会委員、(元)不動産鑑定士試験委員",
    "assoc": "(元)公益社団法人 日本不動産鑑定士協会連合会 常務理事、(現)公益社団法人大阪府不動産鑑定士協会副会長、(現)一般社団法人近畿不動産鑑定士協会連合会副会長",
    "philosophy": """
長年の鑑定評価の実務と公的役割を通じて確信しているのは、「価格は結論ではなく、構造である」ということです。
価格は、市場環境・制度設計・個別事情・収益構造・将来期待が交差する地点に現れます。

ライブラリーズでは、結論の提示だけでなく、前提条件・手法選択・補正・整合性検証の過程を可視化し、
第三者が追跡できる説明構造を重視します。

AIは、その透明性を補助する道具です。
但し、AIは判断主体ではなく、不動産鑑定評価の最終判断と説明責任は不動産鑑定士が負います。
"""
}

PROFILE_EN: Dict[str, str] = {
    "name": "Takamitsu Isoo",
    "title": "Real Property Appraiser (Japan)",
    "edu": "B.A., Faculty of Economics, Doshisha University",
    "career": "Approximately 40 years with a major Japanese appraisal firm—**Official Land Price Publication** and related public valuation, securitized real estate, corporate asset valuation, and dispute matters.",
    "cases": "2,000+ appraisal assignments",
    "public": "(Former) Shinagawa Property Price Council; (Current) Osaka Real Estate Valuation Council; (Former) Examination Committee member for the Real Property Appraiser Examination",
    "assoc": "(Former) Executive Director, Japan Federation of Real Property Appraiser Associations; (Current) Vice President, Osaka Prefecture Real Property Appraisers Association; (Current) Vice President, Kinki Federation of Real Property Appraiser Associations",
    "philosophy": """
Through practice and public roles, I am convinced that **price is structure—not a slogan**.

Price appears where market conditions, institutions, property-specific facts, income logic, and expectations intersect.

At Libralys, we emphasize traceability: not only conclusions, but the path through assumptions, method choice, adjustments, and reconciliation.
AI can assist transparency; it is not the decision-maker—professional judgment and accountability remain with the appraiser.

Where English is used on this site, wording is cross-checked against concepts familiar under *IVS*, the RICS *Valuation – Global Standards* (“Red Book”), and *USPAP*—without implying compliance with any foreign standard or statute.
""",
}

# SERVICES は lib.services_catalog（単一ソース）

# SERVICES に無い相談種別だけを列挙（単一ソースの末尾）
CONTACT_PURPOSE_EXTRAS: tuple[str, ...] = ("地価動向レポート", "その他")


def contact_purpose_options() -> list[str]:
    """ご相談種別の選択肢。業務内容の title（カタログ）と完全一致 + 追加分。"""
    if _lang() == "ja":
        return [str(s["title"]) for s in SERVICES] + list(CONTACT_PURPOSE_EXTRAS)
    return [t(f"contact_svc_{s['id']}") for s in SERVICES] + [
        t("contact_svc_extra_chika"),
        t("contact_svc_extra_other"),
    ]


FLOW = [
    {
        "title": "1. ご相談",
        "body": """
まずは状況整理から始めます。
依頼者が本当に必要としているのは「価格」だけではなく、
“なぜその価格になるのかを説明できること”である場合が多いためです。

目的（売買／担保／相続／訴訟等）、提出先、希望納期、対象不動産の概要（自用／賃貸、用途、権利関係の概略）を確認し、
想定される論点と必要資料の見取り図を作ります。
現在、ライブラリーズは、不動産鑑定業者登録を行っていないので、不動産の鑑定評価に関する法律の基づく
鑑定評価業務は行っていません。
"""
    },
    {
        "title": "2. 業務範囲確認・見積提示",
        "body": """
業務の範囲（成果物の種類、調査の深さ、必要な現地調査の有無、提出先の要件）を明確化し、
費用・工程・納期を提示します。

この段階で、独立性や品質確保が難しい場合、または能力・時間の制約から適切な成果が担保できない場合は、
受任を辞退します。小規模事務所として最も重要な品質管理です。
"""
    },
    {
        "title": "3. 現地調査",
        "body": """
机上資料だけでは把握できない要素が、不動産には必ず存在します。
接道状況、周辺環境、利用状況、近隣との関係性、建物や敷地の状態など、評価の前提に関わる情報を確認します。

現地確認を省略すると、説明責任の土台が弱くなるため、必要性がある案件では現地調査を重視します。
"""
    },
    {
        "title": "4. 市場分析・補助分析（AI補助を含む）",
        "body": """
取引事例、公的価格、賃料・利回り水準などを整理し、市場の輪郭を掴みます。
ここでAIは「結論を出す装置」ではなく、以下を補助する道具として使います。

・データ整理（オープンデータを構造化し、出所を管理）
・感応度分析（前提の変化に対して価格がどう動くか）
・整合チェック（外れ値や矛盾の検出、整合性の点検）

AIで“答え”を作るのではなく、不動産鑑定士の判断を“検証可能にする”のが目的です。
"""
    },
    {
        "title": "5. 報告書作成",
        "body": """
不動産鑑定評価基準に基づき、評価目的・価格時点・最有効使用を前提として、
手法選択理由→補正→整合性検証→前提条件・限界の表示、の順に構造化します。
ライブラリーズでは、読み手が「どこを見れば根拠が追えるか」が分かる文書設計を重視します。
(現在、ライブラリーズは、不動産鑑定業者登録を行っていないので、不動産の鑑定評価に関する法律の基づく鑑定評価業務は行っていません。)
"""
    },
    {
        "title": "6. 納品・説明",
        "body": """
コンサルティング業務は、理解されて初めて価値を持ちます。
算定構造と前提条件、結論の意味、限界を丁寧に説明します。

必要に応じて、前提差の影響（感応度）を補足資料として提示し、誤解を生まない形での意思決定を支援します。
"""
    }
]

# 業務の流れページ末尾「よくある質問」（iframe 用・原文固定）
FLOW_FAQ_ITEMS: List[Tuple[str, str]] = [
    (
        "Q1. 鑑定評価と価格査定(コンサル)の違いは何ですか？",
        """
不動産会社の査定は、売却想定価格の目安です。
不動産鑑定評価は、不動産鑑定評価基準に基づき、第三者に説明可能な価格を示す公式文書です。
(現在、ライブラリーズは、不動産鑑定業者登録を行っていないので、不動産の鑑定評価に関する法律の基づく鑑定評価業務は行っていません。)
""",
    ),
    (
        "Q2. 鑑定評価・コンサルにはどれくらい期間がかかりますか？",
        """
通常2〜3週間程度です。対象規模・資料状況により変動します。
""",
    ),
    (
        "Q3. 報酬額はどのように決まりますか？",
        """
規模・用途・目的・資料精度により決定します。正式なお見積りを事前に提示します。
""",
    ),
    (
        "Q4. 金融機関提出用にも使えますか？",
        """
担保評価・M&A・相続・事業再生など幅広く対応可能です。
""",
    ),
    (
        "Q5. 現地調査は必須ですか？",
        """
原則実施します。机上評価が合理的な場合のみ例外的に省略します。
""",
    ),
    (
        "Q6. 赤字物件でも評価できますか？",
        """
可能です。DCF分析により収益構造を再整理して評価します。
""",
    ),
    (
        "Q7. 土地だけの評価も可能ですか？",
        """
更地・底地・借地権など各種対応可能です。
""",
    ),
    (
        "Q8. 共有持分の評価はできますか？",
        """
市場性減価や処分制約を考慮して算定します。
""",
    ),
    (
        "Q9. 将来価格の予測は可能ですか？",
        """
シナリオ分析として提示可能です。将来保証ではありません。
""",
    ),
    (
        "Q10. 依頼を断ることはありますか？",
        """
利益相反や品質確保が困難な場合は受任しません。
""",
    ),
]

FLOW_EN: List[Dict[str, str]] = [
    {
        "title": "1. Initial consultation",
        "body": """
We begin by clarifying the question. Clients often need more than a number—they need an explanation that will stand up to third-party review.

We confirm the mandate (sale, collateral, inheritance, dispute, etc.), recipient requirements, timeline, and a concise property profile (use, tenancy, rights).
We then outline likely issues and a document roadmap.
*(Libralys is not currently registered to provide statutory appraisal services under the Japanese Real Estate Appraisal Act.)*
""",
    },
    {
        "title": "2. Scope, fee, and schedule",
        "body": """
We define deliverables, depth of investigation, site inspection needs, and recipient expectations—then propose fees, process, and timing.

Where independence or quality cannot be maintained, we decline the engagement. For a compact practice, this gatekeeping is core quality control.
""",
    },
    {
        "title": "3. Site inspection",
        "body": """
Real property always contains facts that desktop research cannot capture: access, neighborhood context, occupancy, relationships with surroundings, and physical condition.

Where site work is material to accountability, we treat inspection as part of the evidence base—not an optional extra.
""",
    },
    {
        "title": "4. Market analysis and assisted analytics (including AI)",
        "body": """
We organize comparables, **Official Land Price Data**, rent/yield context, and market narratives.

AI is not used to “decide” value. It assists with:
- structuring open data with traceable sourcing
- sensitivity analysis (how conclusions move when assumptions move)
- consistency checks (outliers and contradictions)

The objective is to make professional judgment **reviewable**, not to replace it.
""",
    },
    {
        "title": "5. Reporting structure",
        "body": """
Following the **Japanese Real Estate Appraisal Standards**, we structure work from valuation purpose and as-of date through **Highest and Best Use**,
method selection, adjustments, reconciliation, and explicit limitations—so readers know where to find the audit trail.
*(Statutory appraisal services under the Japanese Act are not currently provided.)*
""",
    },
    {
        "title": "6. Delivery and explanation",
        "body": """
Consulting value is realized only when decision-makers understand the result.

We explain the calculation architecture, assumptions, meaning of the conclusion, and boundaries. Where helpful, we add sensitivity supplements to reduce misunderstanding.
""",
    },
]

FLOW_FAQ_ITEMS_EN: List[Tuple[str, str]] = [
    (
        "Q1. Appraisal vs. brokerage pricing opinions?",
        """
Brokerage guidance often targets a marketing range. **Real Estate Appraisal** under Japanese standards produces an **Appraisal Report** intended for third-party scrutiny.
*(Libralys is not currently registered to provide statutory appraisal services under the Japanese Act.)*
""",
    ),
    (
        "Q2. How long does it take?",
        """
Typically on the order of two to three weeks, depending on scale and data availability.
""",
    ),
    (
        "Q3. How are fees determined?",
        """
By scale, use, purpose, and documentation burden. We provide a written estimate before formal engagement.
""",
    ),
    (
        "Q4. Can outputs be used for lenders?",
        """
We routinely support collateral, M&A, inheritance, and restructuring contexts—aligned to recipient requirements.
""",
    ),
    (
        "Q5. Is a site visit mandatory?",
        """
As a rule, yes. Desktop-only work is exceptional where it is demonstrably reasonable and adequately disclosed.
""",
    ),
    (
        "Q6. Can negative-income property be analyzed?",
        """
Yes. **Discounted Cash Flow (DCF) Analysis** and income restructuring are common tools—always with explicit scenarios.
""",
    ),
    (
        "Q7. Land-only assignments?",
        """
Yes—including vacant land, underlying land, and leasehold interests—subject to rights and use assumptions.
""",
    ),
    (
        "Q8. Undivided co-ownership interests?",
        """
Yes, reflecting marketability discounts and disposal constraints where material.
""",
    ),
    (
        "Q9. Future price forecasts?",
        """
Scenario analysis is possible; it is not a guarantee of future market outcomes.
""",
    ),
    (
        "Q10. Do you ever decline work?",
        """
Yes—where conflicts of interest or quality assurance cannot be maintained.
""",
    ),
]

# ------------------------------------------------------------
# 追加（コード8）：企業統治 / 情報セキュリティ / 倫理規程 / ケーススタディ
# ------------------------------------------------------------
GOVERNANCE_TEXT = """
ライブラリーズは、コンサルティング業務が「専門性」だけで成立するものではなく、
**独立性・透明性・説明責任（Accountability）**によって、信頼が担保される制度業務であることを前提とします。

そのため、規模の大小にかかわらず、上場企業水準の考え方（統治・統制・監督）を参照し、以下の3層でガバナンスを設計します。
(現在、ライブラリーズは、不動産鑑定業者登録を行っていないので、不動産の鑑定評価に関する法律の基づく鑑定評価業務は行っていません。)

**(1) 独立性の確保（Independence）**  
- 利害関係の有無、関係者構造、報酬条件、依頼目的を事前に点検し、独立性を害する恐れがある場合は受任しません。  
- 結論誘導の要請（価格の指定、前提の恣意的設定、資料隠し等）に対しては、業務中であっても是正を求め、是正困難な場合は中止します。

**(2) 品質管理（Quality）**  
- 目的→前提→手法→補正→整合性→限界、の順で構造化し、第三者が追跡できる形で提示します。  
- 誤解が生じやすい論点（価格時点、最有効使用、権利関係、特殊事情）を先に固定し、議論の地盤を整えます。

**(3) 透明性（Transparency）**  
- 参照データの出所、期間、適用範囲、採否理由を記録し、必要範囲で開示します。  
- AI等の補助分析を用いる場合は、何に使い、何をしないか（非目的）を明確にし、自動査定と誤認される表示を行いません。

ライブラリーズは、「小規模ゆえの統制不足」を許容せず、むしろ小規模であるからこそ**代表が全工程に責任を負い、
統治の実効性を担保する**運用を採用します。
"""

GOVERNANCE_TEXT_EN = """
Libralys treats consulting not as expertise alone, but as an institutional service where trust is earned through **independence, transparency, and accountability**.

Accordingly—regardless of firm size—we reference listed-company governance thinking and structure controls in three layers.
*(Libralys is not currently registered to provide statutory appraisal services under the Japanese Real Estate Appraisal Act.)*

**(1) Independence**  
Screen conflicts, related parties, fee structures, and mandate intent before acceptance. Decline or stop work where independence cannot be maintained or where conclusions would be improperly steered.

**(2) Quality**  
Structure deliverables as purpose → assumptions → methods → adjustments → reconciliation → limitations, so a reviewer can follow the trail. Fix volatile issues early (as-of date, **Highest and Best Use**, legal interests, special circumstances).

**(3) Transparency**  
Record data sources, periods, scope, and inclusion/exclusion rationale; disclose as appropriate. Where AI assists, document what it does—and what it does not do—so outputs are not mistaken for automated appraisal.

As a compact practice, **the representative remains accountable across the workflow** so governance stays operational—not decorative.
"""

SECURITY_TEXT = """
ライブラリーズは、コンサルティング業務が高い機密性を伴うこと（個人情報・資産情報・訴訟関連情報等）を踏まえ、
ISMS（Information Security Management System）相当の考え方に基づき、情報資産を保護します。

**1. 基本方針**  
- 機密性（Confidentiality）：権限なきアクセス・漏えいを防止します。  
- 完全性（Integrity）：改ざん・誤り・破損を防止し、正確性を維持します。  
- 可用性（Availability）：必要なときに必要な情報へアクセスできる状態を維持します。

**2. 主要な管理措置（代表例）**  
- アクセス制御：業務必要性に応じた最小権限（Least Privilege）  
- 端末管理：OS/ソフト更新、暗号化、パスコード、紛失対策  
- データ保護：保存時・送信時の保護、バックアップ、削除の手順化  
- 外部委託管理：委託の必要性評価、守秘・管理水準の確認、監督  
- 監査・見直し：運用点検、インシデントの予防と再発防止

**3. インシデント対応**  
万一の事故（漏えい、誤送信、紛失等）に備え、初動対応・封じ込め・原因分析・再発防止を事前に定義し、影響の最小化を図ります。
ライブラリーズは、情報保護を「宣言」ではなく、業務設計の一部として運用します。
"""

SECURITY_TEXT_EN = """
Because consulting routinely handles sensitive information (personal data, asset positions, dispute materials), Libralys protects information assets using an **ISMS-aligned** control model.

**1. Foundational principles**  
- Confidentiality: prevent unauthorized access and leakage  
- Integrity: protect against tampering, error, and loss  
- Availability: maintain legitimate access when required  

**2. Representative controls**  
Least-privilege access, endpoint hygiene (patching, encryption, device controls), secure handling in transit and at rest, backups and deletion procedures, vendor diligence, and periodic review.

**3. Incidents**  
We define initial response, containment, root-cause analysis, and recurrence prevention so impact is minimized if an incident occurs.

Information protection is **operating practice**, not marketing language.
"""

ETHICS_TEXT = """
不動産コンサルティング業務は、社会的信頼を基礎とする専門制度業務です。
ライブラリーズは、不動産鑑定士の職業倫理（独立性・誠実性・公正性）を中核規範として、
以下を厳格に遵守します。従来の実務知見に加え、AI・データ分析・地図情報なども活用し、
より精度と透明性の高いサービスを目指します。

**1. 独立性（Independence）**  
- 利害関係・関係者構造を点検し、独立性の疑義がある場合は受任しません。  
- 結論誘導・不当な圧力・恣意的前提の要求を排除します。

**2. 公正性（Fairness）**  
- 特定の立場に偏らず、中立的な視点で価格や条件を整理します。
特定当事者の利益のみを目的とした評価設計を行いません。  
- 反対仮説・代替説明を検討し、論理の偏りを抑制します。

**3. 誠実性（Integrity）**  
- 出所不明データの結論採用を行いません。  
- 限界・不確実性を隠さず明示します。

**4. 守秘義務（Confidentiality）**  
- 依頼者情報、資産情報、紛争情報等を適切に管理し、目的外利用をしません。

**5. 説明責任（Accountability）**  
- 数値だけでなく、その背景や理由まで含めて丁寧にご説明します。
目的→前提→手法→補正→整合性→限界、の筋道を明示し、第三者説明に耐える構造を採用します。

ライブラリーズは、倫理を「理念」ではなく「運用規程」として扱い、継続的に見直します。
"""

ETHICS_TEXT_EN = """
**Real Estate Consulting** rests on public trust. Libralys adheres to the appraiser’s professional ethics—**independence, integrity, and fairness**—while responsibly using AI, analytics, and geospatial tools to improve precision and transparency.

**1. Independence**  
Decline work where conflicts or appearances undermine neutrality. Reject pressure to engineer conclusions or hide material facts.

**2. Fairness**  
Maintain a balanced perspective; avoid designs that serve only one party. Consider counterfactuals and alternative narratives.

**3. Integrity**  
Do not rely on unverifiable data as primary evidence. Disclose limitations and uncertainty plainly.

**4. Confidentiality**  
Protect client, asset, and dispute information; no unrelated reuse.

**5. Accountability**  
Explain not only numbers but the reasoning chain: purpose → assumptions → methods → adjustments → reconciliation → limitations.

Ethics are maintained as **working rules**—reviewed on an ongoing basis.
"""

CASE_STUDIES = [
    {
        "title": "ケース1｜担保評価（第三者説明が主目的）",
        "summary": "提出先要件を起点に、手法選択と整合性検証を“見える化”して説明負担を軽減。",
        "focus": ["提出先要件の確認", "価格時点・最有効使用の固定", "補正プロセスの追跡性", "公的価格・市場整合"],
        "note": "守秘の観点から、所在地・数値等は匿名化しています。"
    },
    {
        "title": "ケース2｜相続",
        "summary": "前提差（権利関係・利用状況）の価格影響をシナリオ化し、争点を“価格”から“前提”へ移動。",
        "focus": ["権利関係の整理", "複数シナリオ提示", "説明文の論点設計", "当事者間の誤解防止"],
        "note": "税務判断の代替ではなく、合意形成の説明資料として提供します。"
    },
    dict(CASE_STUDY_CASE_3),
]

CASE_STUDIES_EN: List[Dict[str, Any]] = [
    {
        "title": "Case 1｜Collateral file (third-party explanation)",
        "summary": "Start from recipient requirements; make method choice and reconciliation **traceable** to reduce explanation friction.",
        "focus": [
            "Recipient checklist",
            "As-of date and **Highest and Best Use** pinned early",
            "Traceable adjustment path",
            "Reconciliation with **Official Land Price Data** and market evidence",
        ],
        "note": "Locations and figures are anonymized for confidentiality.",
    },
    {
        "title": "Case 2｜Inheritance",
        "summary": "Scenario-map how rights and use affect value—shifting debate from “the number” to “the assumptions.”",
        "focus": [
            "Rights and interests",
            "Multiple transparent scenarios",
            "Narrative structure for non-experts",
            "Reducing preventable misunderstandings",
        ],
        "note": "Not a substitute for tax advice; supports informed agreement.",
    },
    {
        "title": "Case 3｜Litigation rent opinion (evidence & consistency)",
        "summary": "For contested rent levels, align differential allocation, yield, and market comparables into a coherent evidence package.",
        "focus": [
            "Fixed premises (lease, use, micro-location)",
            "Cross-checked methods",
            "Reconciliation to market data",
            "Visible calculation trail and explicit limits",
        ],
        "note": "Neutrality is maintained regardless of client preference.",
    },
]


# ------------------------------------------------------------
# 4) UI Helpers
# ------------------------------------------------------------
def hr():
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)


def build_flow_faq_page_markdown() -> str:
    flow_src = FLOW if _lang() == "ja" else FLOW_EN
    faq_src = FLOW_FAQ_ITEMS if _lang() == "ja" else FLOW_FAQ_ITEMS_EN
    flow_chunks = [f"## {s['title']}\n\n{s['body'].strip()}" for s in flow_src]
    faq_intro = t("flow_faq_intro")
    faq_body = "\n\n".join(f"### {q}\n\n{a.strip()}" for q, a in faq_src)
    return "\n\n".join(flow_chunks) + "\n\n---\n\n" + faq_intro + faq_body


def build_case_studies_page_markdown() -> str:
    intro = (
        CASE_STUDIES_INTRO_MARKDOWN.strip()
        if _lang() == "ja"
        else CASE_STUDIES_INTRO_MARKDOWN_EN.strip()
    )
    chunks = [intro]
    case_src = CASE_STUDIES if _lang() == "ja" else CASE_STUDIES_EN
    for cs in case_src:
        bullets = "\n".join("- " + x for x in cs["focus"])
        chunks.append(
            f"## {cs['title']}\n\n**概要**：{cs['summary']}\n\n### 設計上の焦点\n\n{bullets}\n\n*{cs['note']}*"
        )
    return "\n\n---\n\n".join(chunks)


def build_profile_page_markdown() -> str:
    p = PROFILE if _lang() == "ja" else PROFILE_EN
    if _lang() == "ja":
        return "\n\n".join(
            [
                f"## {p['name']}（{p['title']}）",
                "",
                f"**学歴**：{p['edu']}",
                "",
                f"**職歴**：{p['career']}",
                "",
                "---",
                "",
                "## 実績（Experience）",
                "",
                f"**{p['cases']}**",
                "",
                """住宅地、商業地、業務ビル、収益不動産、証券化評価、公共補償案件など、用途・目的を問わず幅広い実務経験を有しています。

鑑定評価は“件数”だけで語れるものではありませんが、扱った案件の幅が広いほど、前提条件の見落としを減らし、
説明の選択肢を増やせるという利点があります。""",
                "",
                "---",
                "",
                "## 公職（Public Role）",
                "",
                f"**{p['public']}**",
                "",
                """公共の鑑定評価において、価格形成の妥当性を審議する立場を多く経験しました。
制度理解と市場合理性を同時に満たす判断が求められる場であり、「説明可能な価格」の重要性を、実務の枠を超えて体得した経験です。""",
                "",
                "---",
                "",
                "## 協会活動（Professional Associations）",
                "",
                f"**{p['assoc']}**",
                "",
                """業界全体の制度運営や鑑定評価基準の整備に関与し、鑑定評価制度の発展と透明性向上に取り組んできました。
鑑定評価は、個人の技能だけでなく、制度・倫理・運用の上に成立します。
ライブラリーズはこの前提を尊重し、品位を保った業務遂行を徹底します。""",
                "",
                "---",
                "",
                "## 専門家としての思想（Philosophy）",
                "",
                p["philosophy"].strip(),
            ]
        )
    return "\n\n".join(
        [
            f"## {p['name']} — {p['title']}",
            "",
            f"**Education:** {p['edu']}",
            "",
            f"**Professional background:** {p['career']}",
            "",
            "---",
            "",
            "## Experience",
            "",
            f"**{p['cases']}**",
            "",
            """Assignments span residential and commercial land, office and income properties, securitized portfolios, and public-sector contexts.
Volume alone does not define expertise—but breadth reduces blind spots and widens defensible analytical choices.""",
            "",
            "---",
            "",
            "## Public roles",
            "",
            f"**{p['public']}**",
            "",
            """Public valuation work requires reconciling institutional rules with market discipline—a setting where “explainable value” is not optional.""",
            "",
            "---",
            "",
            "## Professional associations",
            "",
            f"**{p['assoc']}**",
            "",
            """Appraisal is sustained by institutions and ethics—not only individual skill. Libralys honors that foundation in how work is executed.""",
            "",
            "---",
            "",
            "## Philosophy",
            "",
            p["philosophy"].strip(),
        ]
    )


def localized_ai_projects_for_catalog() -> List[Dict[str, Any]]:
    raw = get_resolved_ai_projects_for_catalog()
    if _lang() == "ja":
        return raw
    merged: List[Dict[str, Any]] = []
    for proj in raw:
        slug = str(proj.get("key_slug") or "")
        d = dict(proj)
        d["name"] = t(f"ai_{slug}_name") or str(proj.get("name") or "")
        d["tagline"] = t(f"ai_{slug}_tag") or str(proj.get("tagline") or "")
        d["summary"] = t(f"ai_{slug}_sum") or str(proj.get("summary") or "")
        if proj.get("notes"):
            d["notes"] = t(f"ai_{slug}_note") or str(proj.get("notes") or "")
        merged.append(d)
    return merged


def section_title(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def render_shisanhyo_main_demo_block() -> None:
    resolved = get_resolved_ai_projects()
    ai04_proj = next((p for p in resolved if p.get("key_slug") == "ai04"), None)
    st.subheader(t("dash_heading"))
    ai09_proj = next((p for p in resolved if p.get("key_slug") == "ai09"), None)
    inject_ai_tool_catalog_card_css()
    dash_entries: List[Tuple[Dict[str, Any], str]] = []
    if ai04_proj:
        dash_entries.append((ai04_proj, "dash_sc_"))
    if ai09_proj:
        dash_entries.append((ai09_proj, "dash_koji_"))
    if dash_entries:
        render_dashboard_demo_entry_cards(dash_entries)
    st.markdown('<div style="height:6px" aria-hidden="true"></div>', unsafe_allow_html=True)


def _scroll_app_view_to_top() -> None:
    """メイン列のスクロールコンテナを先頭へ。即時＋次フレーム＋短遅延で、遷移直後の DOM 差し替え後も追従する。"""
    components.html(
        """<script>
(function () {
  function go() {
    try {
      var p = window.parent;
      var d = p.document;
      var a = d.querySelector('[data-testid="stAppViewContainer"]');
      if (a) { a.scrollTop = 0; }
      var m = d.querySelector('section.main');
      if (m) { m.scrollTop = 0; }
      p.scrollTo(0, 0);
    } catch (e) {}
  }
  go();
  try { setTimeout(go, 0); } catch (e) {}
  try { setTimeout(go, 90); } catch (e) {}
})();
</script>""",
        height=0,
        width=0,
    )


def _top_immersive_css_block() -> str:
    """TOP 専用 CSS（Hero・サービスカード・埋め込みラッパー）。Markdown 断片内の style が欠落し得るためページ先頭の style に集約する。"""
    return (
        """
.lib-sh-root {
  position: relative;
  width: 100vw;
  max-width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  margin-top: -2rem;
  margin-bottom: 1.25rem;
  box-sizing: border-box;
  min-height: 88vh;
  min-height: 88dvh;
  background-color: #0b1628;
  background-image: var(--lib-sh-bg);
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  font-family:
    "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic UI", "Yu Gothic", Meiryo,
    "Noto Sans JP", system-ui, sans-serif;
  display: block;
}
.lib-sh-root::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.85) 100%);
}
.lib-sh-inner {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  min-height: inherit;
  width: 100%;
  padding: clamp(28px, 5vw, 56px) clamp(18px, 4vw, 40px) clamp(72px, 10vh, 120px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.lib-sh-card {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
  color: #fff;
  padding: clamp(1.5rem, 3.5vw, 2.5rem) clamp(1.25rem, 3vw, 2.25rem);
  border-radius: 20px;
  border: 1px solid rgba(201, 162, 77, 0.28);
  background: rgba(15, 28, 46, 0.55);
  box-shadow:
    0 28px 64px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset,
    0 1px 0 rgba(255, 255, 255, 0.08) inset;
  -webkit-font-smoothing: antialiased;
}
@supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
  .lib-sh-card {
    background: linear-gradient(
      155deg,
      rgba(15, 28, 46, 0.5) 0%,
      rgba(15, 28, 46, 0.36) 55%,
      rgba(24, 40, 62, 0.42) 100%
    );
    -webkit-backdrop-filter: blur(14px) saturate(1.1);
    backdrop-filter: blur(14px) saturate(1.1);
  }
}
.lib-sh-kicker {
  margin: 0 0 12px 0;
  font-size: clamp(0.75rem, 1.6vw, 0.95rem);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.82);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}
.lib-sh-title {
  margin: 0 0 clamp(1.25rem, 3vw, 1.75rem) 0;
  font-size: clamp(1.85rem, 5vw, 3rem);
  font-weight: 800;
  line-height: 1.28;
  letter-spacing: 0.02em;
  color: #fff;
  text-shadow: 0 2px 28px rgba(0, 0, 0, 0.45);
}
.lib-sh-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  align-items: center;
  margin-top: 8px;
}
.lib-sh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  min-height: 60px;
  padding: 0 clamp(1.5rem, 4vw, 2.25rem);
  border-radius: 12px;
  font-size: clamp(1rem, 2.2vw, 1.125rem);
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}
.lib-sh-btn--primary {
  color: #fff;
  background: #43a047;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.35);
}
.lib-sh-btn--primary:hover { background: #4caf50; }
.lib-sh-btn--secondary {
  color: #fff;
  background: rgba(255, 255, 255, 0.06);
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}
.lib-sh-btn--secondary:hover { background: rgba(255, 255, 255, 0.12); }
.lib-sh-scroll {
  position: absolute;
  left: 50%;
  bottom: clamp(16px, 3vh, 28px);
  transform: translateX(-50%);
  z-index: 2;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.88);
  text-shadow: 0 1px 12px rgba(0, 0, 0, 0.5);
  animation: lib-sh-scroll-bounce 2s ease-in-out infinite;
  pointer-events: none;
}
@keyframes lib-sh-scroll-bounce {
  0%, 100% { transform: translate(-50%, 0); }
  50% { transform: translate(-50%, 10px); }
}
@media (prefers-reduced-motion: reduce) {
  .lib-sh-scroll { animation: none !important; }
}
.lib-top-svc-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 8px 16px 0;
  box-sizing: border-box;
}
.lib-top-svc-heading {
  text-align: center;
  font-size: 1.75rem;
  font-weight: 800;
  color: #0F1C2E;
  margin: 0 0 8px 0;
  letter-spacing: 0.02em;
}
.lib-top-svc-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 40px;
}
.lib-top-svc-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: block;
  text-decoration: none;
  color: #111827;
  box-sizing: border-box;
}
.lib-top-svc-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 14px 32px rgba(0,0,0,0.12);
}
.lib-top-svc-card-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #0F1C2E;
}
.lib-top-svc-card-desc {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}
@media (max-width: 768px) {
  .lib-top-svc-cards { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
  .lib-top-svc-card { transition: none; }
  .lib-top-svc-card:hover { transform: none; }
}
[data-testid="stMarkdownContainer"] .lib-top-html-embed {
  width: 100% !important;
  max-width: 100% !important;
  overflow: visible !important;
}
[data-testid="stMarkdownContainer"] .lib-top-html-embed p {
  margin: 0 !important;
}
section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.lib-top-html-embed) {
  width: 100% !important;
  max-width: 100% !important;
  overflow: visible !important;
}
section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.lib-top-html-embed) p {
  margin: 0 !important;
}
"""
    ).strip()


def _standalone_hero_background_css_url() -> str:
    """TOP ヒーロー専用。ローカル `image/ai_realestate_bg.jpg` が無いときは HTTPS 画像にフォールバック。"""
    try:
        bg_b64 = get_hero_background_b64_for_css() or get_base64_image("image/ai_realestate_bg.jpg")
    except Exception:
        bg_b64 = ""
    if bg_b64:
        mime = _mime_from_image_b64(bg_b64)
        inner = bg_b64.replace("\\", "\\\\").replace("'", "\\'")
        return f"url('data:{mime};base64,{inner}')"
    return (
        "url('https://images.unsplash.com/photo-1503387762-592deb58ef4e"
        "?auto=format&fit=crop&w=1920&q=80')"
    )


def render_top_hero() -> None:
    """TOP ヒーロー（HTML のみ。見た目用 CSS は `page == \"TOP\"` 先頭の style に `_top_immersive_css_block()` で集約）。"""
    _hl = _lang()
    _nav_mekiki = quote("価格の目利き", safe="")
    _nav_services = quote("業務内容", safe="")
    _hl_raw = (t("hero_product_headline") or "").strip()
    _hl_lines = [ln.strip() for ln in _hl_raw.splitlines() if ln.strip()]
    _head_html = (
        "<br>".join(html.escape(ln, quote=True) for ln in _hl_lines)
        if _hl_lines
        else html.escape(_hl_raw or t("hero_headline"), quote=True)
    )
    _bg = _standalone_hero_background_css_url()
    st.markdown(
        '<div class="lib-top-html-embed">'
        + dedent(
            f"""
            <div class="lib-sh-root" lang="{html.escape(_hl, quote=True)}" style="--lib-sh-bg: {_bg};">
            <div class="lib-sh-inner">
            <div class="lib-sh-card">
            <p class="lib-sh-kicker">{html.escape(t("hero_product_kicker"), quote=True)}</p>
            <div class="lib-sh-title">{_head_html}</div>
            <div class="lib-sh-buttons">
            <a class="lib-sh-btn lib-sh-btn--primary" href="?nav={_nav_mekiki}">{html.escape(t("hero_cta_primary"), quote=True)}</a>
            <a class="lib-sh-btn lib-sh-btn--secondary" href="?nav={_nav_services}">{html.escape(t("hero_cta_secondary"), quote=True)}</a>
            </div>
            </div>
            <div class="lib-sh-scroll" aria-hidden="true">{html.escape(t("hero_scroll_hint"), quote=True)}</div>
            </div>
            </div>
            """
        ).strip()
        + "</div>",
        unsafe_allow_html=True,
    )


def render_top_service_cards_section() -> None:
    """TOP: Hero 直下のサービスカード（3列／モバイル1列・?nav 短リンク）。"""
    _nav_mekiki = quote("価格の目利き", safe="")
    _nav_dcf = "DCF"
    _nav_business = quote("業務内容", safe="")
    _t1 = html.escape(t("top_svc_card1_title"), quote=True)
    _d1 = html.escape(t("top_svc_card1_desc"), quote=True)
    _t2 = html.escape(t("top_svc_card2_title"), quote=True)
    _d2 = html.escape(t("top_svc_card2_desc"), quote=True)
    _t3 = html.escape(t("top_svc_card3_title"), quote=True)
    _d3 = html.escape(t("top_svc_card3_desc"), quote=True)
    _h = html.escape(t("top_service_section_title"), quote=True)
    st.markdown(
        '<div class="lib-top-html-embed">'
        + dedent(
            f"""
            <div class="lib-top-svc-wrap">
            <h2 class="lib-top-svc-heading">{_h}</h2>
            <div class="lib-top-svc-cards">
            <a href="?nav={_nav_mekiki}" class="lib-top-svc-card">
            <div class="lib-top-svc-card-title">{_t1}</div>
            <div class="lib-top-svc-card-desc">{_d1}</div>
            </a>
            <a href="?nav={_nav_dcf}" class="lib-top-svc-card">
            <div class="lib-top-svc-card-title">{_t2}</div>
            <div class="lib-top-svc-card-desc">{_d2}</div>
            </a>
            <a href="?nav={_nav_business}" class="lib-top-svc-card">
            <div class="lib-top-svc-card-title">{_t3}</div>
            <div class="lib-top-svc-card-desc">{_d3}</div>
            </a>
            </div>
            </div>
            """
        ).strip()
        + "</div>",
        unsafe_allow_html=True,
    )


def info_kpis():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(t("m_kpi_office"), t("m_kpi_office_v"))
    with c2:
        st.metric(t("m_kpi_cov"), t("m_kpi_cov_v"))
    with c3:
        st.metric(t("m_kpi_exp"), t("m_kpi_exp_v"))
    with c4:
        st.metric(t("m_kpi_cases"), t("m_kpi_cases_v"))

# ------------------------------------------------------------
# 5) 価格の目利き（ページ本体：関数化で事故防止）
# ------------------------------------------------------------
MEKIKI_PAGE_KEY = "価格の目利き"
MEKIKI_NG_WORDS = ["鑑定評価", "適正価格", "正常価格", "価格を決定", "保証", "断定", "買うべき", "買うな"]
MEKIKI_NG_WORDS_EN = [
    "real estate appraisal (as a legal conclusion)",
    "fair market value",
    "normal market value",
    "determines the price",
    "guarantee",
    "definitive statement",
    "you should buy",
    "do not buy",
]

_MEKIKI_REGION_I18N = {"全国（暫定）": "reg_nat", "関西（暫定）": "reg_kansai", "首都圏（暫定）": "reg_kanto"}
_MEKIKI_WALK_I18N = {
    "駅徒歩10分以内": "wb_10",
    "駅徒歩11-15分": "wb_15",
    "駅徒歩16-20分": "wb_20",
    "駅徒歩21分以上": "wb_21",
}
_SHAPE_KEYS = ("不明", "整形", "やや難あり")

@dataclass
class MekikiBand:
    low: float
    mid: float
    high: float

MEKIKI_BENCHMARKS: Dict[str, Dict[str, MekikiBand]] = {
    "全国（暫定）": {
        "駅徒歩10分以内": MekikiBand(low=180000, mid=230000, high=290000),
        "駅徒歩11-15分": MekikiBand(low=160000, mid=210000, high=270000),
        "駅徒歩16-20分": MekikiBand(low=140000, mid=190000, high=250000),
        "駅徒歩21分以上": MekikiBand(low=120000, mid=170000, high=230000),
    },
    "関西（暫定）": {
        "駅徒歩10分以内": MekikiBand(low=170000, mid=220000, high=280000),
        "駅徒歩11-15分": MekikiBand(low=150000, mid=200000, high=260000),
        "駅徒歩16-20分": MekikiBand(low=130000, mid=180000, high=240000),
        "駅徒歩21分以上": MekikiBand(low=110000, mid=160000, high=220000),
    },
    "首都圏（暫定）": {
        "駅徒歩10分以内": MekikiBand(low=240000, mid=320000, high=420000),
        "駅徒歩11-15分": MekikiBand(low=210000, mid=290000, high=380000),
        "駅徒歩16-20分": MekikiBand(low=180000, mid=260000, high=340000),
        "駅徒歩21分以上": MekikiBand(low=150000, mid=230000, high=300000),
    },
}

def mekiki_parse_listing_text(raw: str) -> Dict[str, Any]:
    raw = raw or ""
    r = raw.replace("\u3000", " ").replace("\n", " ")

    price_myen = None
    m = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*万\s*円", r)
    if m:
        price_myen = float(m.group(1).replace(",", ""))
    else:
        m2 = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*万円", r)
        if m2:
            price_myen = float(m2.group(1).replace(",", ""))

    area_sqm = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:m²|㎡|m2)", r)
    if m:
        area_sqm = float(m.group(1))

    walk_min = None
    m = re.search(r"徒歩\s*(\d+)\s*分", r)
    if m:
        walk_min = float(m.group(1))

    address = None
    m = re.search(
        r"所在地\s*([^\s]+(?:\s*[^\s]+){0,10})\s*(?:地図|交通|最寄|JR|地下鉄|都営|東京メトロ|阪急|阪神|近鉄|京阪|南海|名鉄)",
        r
    )
    if m:
        address = m.group(1).strip()

    has_building_condition = "建築条件" in r

    return {
        "price_myen": price_myen,
        "area_sqm": area_sqm,
        "walk_min": walk_min,
        "address": address,
        "building_condition": has_building_condition,
    }

def mekiki_unit_price_yen_per_sqm(price_myen: float, area_sqm: float) -> float:
    return (price_myen * 10000.0) / area_sqm

def mekiki_walk_bucket(mins: Optional[float]) -> str:
    if mins is None:
        return "駅徒歩16-20分"
    if mins <= 10:
        return "駅徒歩10分以内"
    if mins <= 15:
        return "駅徒歩11-15分"
    if mins <= 20:
        return "駅徒歩16-20分"
    return "駅徒歩21分以上"

def mekiki_region_display(ja_region: str) -> str:
    k = _MEKIKI_REGION_I18N.get(ja_region)
    return t(k) if k else ja_region


def mekiki_walk_display(ja_walk: str) -> str:
    k = _MEKIKI_WALK_I18N.get(ja_walk)
    return t(k) if k else ja_walk


def mekiki_shape_display_option(ja_shape: str) -> str:
    m = {"不明": "shape_unknown", "整形": "shape_regular", "やや難あり": "shape_irreg"}
    kk = m.get(ja_shape)
    return t(kk) if kk else ja_shape


def mekiki_appearance_label(
    up: float,
    band: MekikiBand,
    building_condition: bool,
    road_width_m: Optional[float],
    shape_risk: str,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []

    if up <= band.low:
        label = t("mekiki_lbl_modest")
        reasons.append(t("mekiki_r1"))
    elif up <= band.high:
        label = t("mekiki_lbl_ok")
        reasons.append(t("mekiki_r2"))
    else:
        label = t("mekiki_lbl_high")
        reasons.append(t("mekiki_r3"))

    if building_condition:
        reasons.append(t("mekiki_r4"))

    if road_width_m is not None:
        if road_width_m < 4.0:
            reasons.append(t("mekiki_r5a"))
        elif road_width_m < 6.0:
            reasons.append(t("mekiki_r5b"))
        else:
            reasons.append(t("mekiki_r5c"))
    else:
        reasons.append(t("mekiki_r5d"))

    if shape_risk == "整形":
        reasons.append(t("mekiki_r6a"))
    elif shape_risk == "やや難あり":
        reasons.append(t("mekiki_r6b"))
    else:
        reasons.append(t("mekiki_r6c"))

    return label, reasons


def mekiki_parse_comps_text(text: str) -> pd.DataFrame:
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue

        p = None
        a = None

        m = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*万\s*円", line)
        if m:
            p = float(m.group(1).replace(",", ""))
        else:
            m2 = re.search(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*万円", line)
            if m2:
                p = float(m2.group(1).replace(",", ""))

        m3 = re.search(r"(\d+(?:\.\d+)?)\s*(?:m²|㎡|m2)", line)
        if m3:
            a = float(m3.group(1))

        if p and a and a > 0:
            up = mekiki_unit_price_yen_per_sqm(p, a)
            rows.append({"事例": line, "価格(万円)": p, "面積(㎡)": a, "単価(円/㎡)": round(up)})

    return pd.DataFrame(rows)


def mekiki_comps_df_for_display(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        return df
    if _lang() == "ja":
        return df
    return df.rename(
        columns={
            "事例": t("mekiki_col_line"),
            "価格(万円)": t("mekiki_col_price"),
            "面積(㎡)": t("mekiki_col_area"),
            "単価(円/㎡)": t("mekiki_col_up"),
        }
    )


def mekiki_comps_comment(subject_up: float, df: Optional[pd.DataFrame]) -> str:
    if df is None or df.empty:
        return t("mekiki_cc_none")

    median = float(df["単価(円/㎡)"].median())
    diff = subject_up - median

    if abs(diff) < 15000:
        return t("mekiki_cc_near").format(med=int(median))
    if diff > 0:
        return t("mekiki_cc_hi").format(med=int(median), diff=int(diff))
    return t("mekiki_cc_lo").format(med=int(median), diff=int(abs(diff)))

def render_mekiki_page(page_key: str) -> None:
    """page_key は PAGES のルート文字列と完全一致させる（H1＝データ）。"""
    st.markdown(
        f'<h1 style="color:#000000 !important;font-weight:800;letter-spacing:.01em;">'
        f"{html.escape(page_display_label(MEKIKI_PAGE_KEY), quote=True)}</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(f"### {t('mekiki_story_h')}")
    st.image("image/mekiki_story_ai.png", width="stretch")
    st.markdown(t("mekiki_story_body"))

    if "mekiki_business_tool_open" not in st.session_state:
        st.session_state["mekiki_business_tool_open"] = False
    if "mekiki_analyzer_open" not in st.session_state:
        st.session_state["mekiki_analyzer_open"] = False

    _ms = t("mekiki_subtitle")
    if not st.session_state["mekiki_business_tool_open"]:
        st.markdown(
            f"""
<div style="border:2px solid #C9A962;border-radius:14px;padding:20px 22px;margin:6px 0 12px 0;
background:linear-gradient(165deg,#FFFFFF 0%,#F7F5F2 55%,#EFEBE4 100%);
box-shadow:0 2px 14px rgba(15,28,46,0.07);">
  <div style="font-weight:700;font-size:1.2rem;color:#0F1C2E;letter-spacing:0.02em;">{html.escape(_ms, quote=True)}</div>
  <p style="margin:12px 0 0 0;font-size:0.92rem;color:#334155;line-height:1.65;">
    {t("mekiki_open_hint")}
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(t("mekiki_disclaimer_top"))
        if st.button(
            t("mekiki_open_main"),
            type="secondary",
            width="stretch",
            key="mekiki_open_business_tool",
        ):
            st.session_state["mekiki_business_tool_open"] = True
            st.session_state["mekiki_analyzer_open"] = False
            st.rerun()
        return

    st.markdown(
        f'<div style="border:1px solid rgba(201,169,98,0.45);border-radius:12px;padding:14px 16px;margin-bottom:10px;background:#FAFAF8;">'
        f'<span style="font-weight:700;color:#0F1C2E;">{html.escape(_ms, quote=True)}</span>'
        f'<span style="color:#64748b;font-size:0.9rem;">{html.escape(t("mekiki_status"), quote=True)}</span></div>',
        unsafe_allow_html=True,
    )
    c_open, _ = st.columns([1, 3])
    with c_open:
        if st.button(t("mekiki_close"), type="secondary", key="mekiki_close_business_tool"):
            st.session_state["mekiki_business_tool_open"] = False
            st.session_state["mekiki_analyzer_open"] = False
            st.rerun()
    st.caption(t("mekiki_disclaimer_top"))

    if not st.session_state["mekiki_analyzer_open"]:
        st.markdown(
            f"""
<div style="margin:10px 0 6px 0;padding:14px 16px;border-radius:12px;border:1px solid rgba(15,28,46,0.12);
background:#fff;font-size:0.95rem;color:#1f2937;line-height:1.7;">
{html.escape(t("mekiki_inner_hint"), quote=True)}
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button(
            t("mekiki_open_an"),
            type="secondary",
            width="stretch",
            key="mekiki_open_analyzer",
        ):
            st.session_state["mekiki_analyzer_open"] = True
            st.rerun()
        return

    hr()

    tabs = st.tabs([t("mekiki_tab_in"), t("mekiki_tab_out"), t("mekiki_tab_dis")])

    with tabs[0]:
        st.subheader(t("mekiki_sec_prop"))
        raw = st.text_area(
            t("mekiki_raw_lbl"),
            height=180,
            placeholder=t("mekiki_raw_ph"),
            key="mekiki_raw",
        )

        parsed = mekiki_parse_listing_text(raw)

        with st.expander(t("mekiki_exp_parse"), expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                price_myen = st.number_input(
                    t("mekiki_price"),
                    min_value=0.0,
                    value=float(parsed["price_myen"] or 0.0),
                    step=10.0,
                    key="mekiki_price_myen",
                )
                area_sqm = st.number_input(
                    t("mekiki_area"),
                    min_value=0.0,
                    value=float(parsed["area_sqm"] or 0.0),
                    step=1.0,
                    key="mekiki_area_sqm",
                )
            with c2:
                walk_min = st.number_input(
                    t("mekiki_walk"),
                    min_value=0.0,
                    value=float(parsed["walk_min"] or 0.0),
                    step=1.0,
                    key="mekiki_walk_min",
                )
                building_condition = st.checkbox(
                    t("mekiki_bcond"),
                    value=bool(parsed["building_condition"]),
                    key="mekiki_building_condition",
                )

            address = st.text_input(t("mekiki_addr"), value=parsed["address"] or "", key="mekiki_address")

        st.subheader(t("mekiki_band_h"))
        _regions = list(MEKIKI_BENCHMARKS.keys())
        region = st.selectbox(
            t("mekiki_region"),
            options=_regions,
            index=0,
            key="mekiki_region",
            format_func=mekiki_region_display,
        )
        wb = mekiki_walk_bucket(walk_min if walk_min > 0 else None)
        st.caption(t("mekiki_walk_cap").format(wb=mekiki_walk_display(wb)))

        st.subheader(t("mekiki_more_h"))
        c3, c4 = st.columns(2)
        with c3:
            road_width_val = st.number_input(
                t("mekiki_road"), min_value=0.0, value=0.0, step=0.5, key="mekiki_road_width"
            )
            road_width_m = None if road_width_val <= 0 else float(road_width_val)
        with c4:
            shape_risk = st.selectbox(
                t("mekiki_shape"),
                list(_SHAPE_KEYS),
                index=0,
                key="mekiki_shape",
                format_func=mekiki_shape_display_option,
            )

        st.subheader(t("mekiki_comp_h"))
        st.caption(t("mekiki_comp_cap"))
        comps_raw = st.text_area(
            t("mekiki_comp_lbl"),
            height=120,
            placeholder=t("mekiki_comp_ph"),
            key="mekiki_comps_raw",
        )
        df_comps = mekiki_parse_comps_text(comps_raw)
        if df_comps is not None and not df_comps.empty:
            st.dataframe(mekiki_comps_df_for_display(df_comps), width="stretch")

        hr()
        run = st.button(t("mekiki_run"), type="secondary", key="mekiki_run")

        if run:
            st.session_state["mekiki_inputs"] = {
                "price_myen": float(price_myen),
                "area_sqm": float(area_sqm),
                "walk_min": (float(walk_min) if walk_min > 0 else None),
                "building_condition": bool(building_condition),
                "address": address,
                "region": region,
                "walk_bucket": wb,
                "road_width_m": road_width_m,
                "shape_risk": shape_risk,
                "df_comps": df_comps,
            }
            st.success(t("mekiki_ok"))

    with tabs[1]:
        st.subheader(t("mekiki_res_h"))
        if "mekiki_inputs" not in st.session_state:
            st.info(t("mekiki_need_input"))
        else:
            inp = st.session_state["mekiki_inputs"]
            price_myen = inp["price_myen"]
            area_sqm = inp["area_sqm"]

            if price_myen <= 0 or area_sqm <= 0:
                st.error(t("mekiki_err_pa"))
            else:
                up = mekiki_unit_price_yen_per_sqm(price_myen, area_sqm)
                band = MEKIKI_BENCHMARKS[inp["region"]][inp["walk_bucket"]]
                label, reasons = mekiki_appearance_label(
                    up=up,
                    band=band,
                    building_condition=inp["building_condition"],
                    road_width_m=inp["road_width_m"],
                    shape_risk=inp["shape_risk"],
                )

                st.markdown(f"### {t('mekiki_subj')}")
                st.write(f"- {t('mekiki_lbl_addr')}：{inp['address'] or t('mekiki_na')}")
                st.write(f"- {t('mekiki_lbl_price')}：{price_myen:,.0f}{t('mekiki_man')}")
                st.write(f"- {t('mekiki_lbl_area')}：{area_sqm:,.2f}㎡")
                st.write(f"- {t('mekiki_lbl_up')}：**{int(round(up)):,} {t('mekiki_yen_m2')}**")
                st.write(f"- {t('mekiki_lbl_walk')}：{mekiki_walk_display(inp['walk_bucket'])}")
                yn = t("mekiki_yes") if inp["building_condition"] else t("mekiki_no")
                st.write(f"- {t('mekiki_lbl_bcond')}：{yn}")

                st.markdown(f"### {t('mekiki_view_h')}")
                st.success(label)

                st.markdown(f"### {t('mekiki_why_h')}")
                for i, r in enumerate(reasons, start=1):
                    st.write(f"{i}. {r}")

                st.markdown(f"### {t('mekiki_band_disp_h')}")
                st.caption(t("mekiki_band_cap"))
                st.write(f"- {t('mekiki_lbl_reg')}：{mekiki_region_display(inp['region'])}")
                st.write(
                    "- "
                    + t("mekiki_band_line").format(
                        lo=int(band.low), mid=int(band.mid), hi=int(band.high)
                    )
                )

                st.markdown(f"### {t('mekiki_comp_pos_h')}")
                df_comps = inp["df_comps"]
                st.write(mekiki_comps_comment(up, df_comps))
                if df_comps is not None and not df_comps.empty:
                    st.dataframe(mekiki_comps_df_for_display(df_comps), width="stretch")

                st.markdown(f"### {t('mekiki_notes_h')}")
                st.warning(t("mekiki_notes_body"))

    with tabs[2]:
        st.subheader(t("mekiki_ops_h"))
        st.markdown(t("mekiki_disclaimer_top"))
        hr()
        st.markdown(f"### {t('mekiki_save_h')}")
        st.markdown(t("mekiki_privacy_note"))
        st.markdown(f"### {t('mekiki_ng_h')}")
        st.caption(t("mekiki_ng_cap"))
        _ng = MEKIKI_NG_WORDS if _lang() == "ja" else MEKIKI_NG_WORDS_EN
        st.write("・" + "\n・".join(_ng))

# ------------------------------------------------------------
# 5b) 不動産鑑定士マッチング（価格の目利きと同型の導線）
# ------------------------------------------------------------
MATCHING_PAGE_KEY = "不動産鑑定士マッチング"
MATCHING_STORY_IMAGE = "image/appraiser_matching_story.png"


def render_matching_page(page_key: str) -> None:
    """page_key は PAGES のルート文字列と完全一致させる（H1＝データ）。"""
    st.markdown(
        f'<h1 style="color:#000000 !important;font-weight:800;letter-spacing:.01em;">'
        f"{html.escape(page_display_label(MATCHING_PAGE_KEY), quote=True)}</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(f"### {t('match_story_h')}")
    _img_path = BASE_DIR / MATCHING_STORY_IMAGE
    if _img_path.is_file():
        st.image(MATCHING_STORY_IMAGE, width="stretch")
    else:
        st.warning(t("match_story_miss").format(path=MATCHING_STORY_IMAGE))

    st.markdown(f"### {t('match_concept_h')}")
    st.markdown(t("match_concept_body"))

    if "matching_business_tool_open" not in st.session_state:
        st.session_state["matching_business_tool_open"] = False
    if "matching_analyzer_open" not in st.session_state:
        st.session_state["matching_analyzer_open"] = False

    _mt = t("match_subtitle")
    if not st.session_state["matching_business_tool_open"]:
        st.markdown(
            f"""
<div style="border:2px solid #C9A962;border-radius:14px;padding:20px 22px;margin:6px 0 12px 0;
background:linear-gradient(165deg,#FFFFFF 0%,#F7F5F2 55%,#EFEBE4 100%);
box-shadow:0 2px 14px rgba(15,28,46,0.07);">
  <div style="font-weight:700;font-size:1.2rem;color:#0F1C2E;letter-spacing:0.02em;">{html.escape(_mt, quote=True)}</div>
  <p style="margin:12px 0 0 0;font-size:0.92rem;color:#334155;line-height:1.65;">
    {t("match_open_hint")}
  </p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(t("matching_disclaimer_top"))
        if st.button(
            t("match_open_main"),
            type="secondary",
            width="stretch",
            key="matching_open_business_tool",
        ):
            st.session_state["matching_business_tool_open"] = True
            st.session_state["matching_analyzer_open"] = False
            st.rerun()
        return

    st.markdown(
        f'<div style="border:1px solid rgba(201,169,98,0.45);border-radius:12px;padding:14px 16px;margin-bottom:10px;background:#FAFAF8;">'
        f'<span style="font-weight:700;color:#0F1C2E;">{html.escape(_mt, quote=True)}</span>'
        f'<span style="color:#64748b;font-size:0.9rem;">{html.escape(t("match_status"), quote=True)}</span></div>',
        unsafe_allow_html=True,
    )
    c_open, _ = st.columns([1, 3])
    with c_open:
        if st.button(t("mekiki_close"), type="secondary", key="matching_close_business_tool"):
            st.session_state["matching_business_tool_open"] = False
            st.session_state["matching_analyzer_open"] = False
            st.rerun()
    st.caption(t("matching_disclaimer_top"))

    if not st.session_state["matching_analyzer_open"]:
        st.markdown(
            f"""
<div style="margin:10px 0 6px 0;padding:14px 16px;border-radius:12px;border:1px solid rgba(15,28,46,0.12);
background:#fff;font-size:0.95rem;color:#1f2937;line-height:1.7;">
{html.escape(t("match_inner_hint"), quote=True)}
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button(
            t("match_open_an"),
            type="secondary",
            width="stretch",
            key="matching_open_analyzer",
        ):
            st.session_state["matching_analyzer_open"] = True
            st.rerun()
        return

    hr()

    tabs = st.tabs([t("mekiki_tab_in"), t("mekiki_tab_out"), t("mekiki_tab_dis")])

    with tabs[0]:
        st.subheader(t("match_in_h"))
        st.info(t("match_in_info"))
        if st.button(
            t("match_btn_contact"),
            type="secondary",
            key="matching_nav_contact",
        ):
            st.session_state[NAV_PENDING_KEY] = "お問い合わせ"
            st.rerun()

    with tabs[1]:
        st.subheader(t("match_out_h"))
        st.info(t("match_out_info"))

    with tabs[2]:
        st.subheader(t("match_ops_h"))
        st.markdown(t("matching_disclaimer_top"))
        hr()
        st.markdown(f"### {t('mekiki_save_h')}")
        st.markdown(t("matching_privacy_note"))
        st.markdown(f"### {t('match_note_h')}")
        st.caption(t("match_note_cap"))

# ------------------------------------------------------------
# 6) Sidebar（コード8のページ群）
# ※ 重要：PAGESのカンマ抜けを修正（SyntaxError防止）
# ------------------------------------------------------------
PAGES = [
    "TOP",
    "はじめての方へ",
    "業務内容",
    "業務の流れ",
    "AI分析ツール",
    "AI評価研究グループ",
    "価格の目利き",
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
]

_PAGES_SET = frozenset(PAGES)
_PAGES_OPTIONS = tuple(PAGES)

assert MEKIKI_PAGE_KEY in _PAGES_SET
assert MATCHING_PAGE_KEY in _PAGES_SET

# ========== Floating nav: ページ履歴（フローティング「戻る」用・NAV_PAGE_ROUTER_KEY 本体は従来どおり） ==========
PAGE_HISTORY_STACK_KEY = "_lib_page_stack"
PAGE_HISTORY_LAST_KEY = "_lib_last_committed_page"
MAX_PAGE_HISTORY = 24


# 前回ランで表示していたページ（ページ切替検知・先頭スクロール用。履歴スタックとは別）
_lib_scroll_prev_page_key = "_lib_scroll_prev_page"


def init_navigation_state() -> None:
    """履歴スタックをリストで初期化（既存キーは上書きしない）。"""
    if PAGE_HISTORY_STACK_KEY not in st.session_state:
        st.session_state[PAGE_HISTORY_STACK_KEY] = []
    elif not isinstance(st.session_state[PAGE_HISTORY_STACK_KEY], list):
        st.session_state[PAGE_HISTORY_STACK_KEY] = []


def detect_page_change(current_page: str) -> None:
    """
    サイドバー・ボタン・パンくず等でページキーが変わったときだけ、先頭スクロール用フラグを立てる。
    同一ページ上のウィジェット操作による再描画ではフラグを立てない。
    """
    if current_page not in _PAGES_SET:
        return
    prev = st.session_state.get(_lib_scroll_prev_page_key)
    if prev is not None and prev != current_page:
        st.session_state[SCROLL_TOP_ONCE_KEY] = True


def handle_page_top_reset(current_page: str) -> None:
    """ラン終了時：次回 detect_page_change 用に、いま表示したページ名を保存する。"""
    if current_page in _PAGES_SET:
        st.session_state[_lib_scroll_prev_page_key] = current_page


def inject_scroll_to_top_script() -> None:
    """SCROLL_TOP_ONCE_KEY が True のときだけ 1 回先頭へスクロール（無限ループにならない）。"""
    if st.session_state.pop(SCROLL_TOP_ONCE_KEY, False):
        _scroll_app_view_to_top()


def _lib_pop_nav_destination() -> str:
    """履歴があれば直前ページ、なければ TOP。"""
    init_navigation_state()
    stack = st.session_state.setdefault(PAGE_HISTORY_STACK_KEY, [])
    if stack:
        return stack.pop()
    return "TOP"


def go_back_page() -> None:
    """
    アプリ内の1つ前のページへ（履歴が空なら TOP）。
    ブラウザの history.back ではない。遷移なしでも rerun し URL を整える用途あり。
    """
    dest = _lib_pop_nav_destination()
    if dest not in _PAGES_SET:
        dest = "TOP"
    cur = st.session_state.get(NAV_PAGE_ROUTER_KEY)
    if cur != dest:
        st.session_state[NAV_PAGE_ROUTER_KEY] = dest
        st.session_state[PAGE_HISTORY_LAST_KEY] = dest
        st.session_state[SCROLL_TOP_ONCE_KEY] = True
    st.rerun()


def push_page_history(current_page: str) -> None:
    """
    ラン終了時に呼び出し、前回表示ページから current_page へ変わったときだけ履歴に積む。
    同一ページの連続では積まない。
    """
    init_navigation_state()
    if current_page not in _PAGES_SET:
        return
    last = st.session_state.get(PAGE_HISTORY_LAST_KEY)
    if last is None:
        st.session_state[PAGE_HISTORY_LAST_KEY] = current_page
        return
    if last == current_page:
        return
    stack = st.session_state[PAGE_HISTORY_STACK_KEY]
    stack.append(last)
    while len(stack) > MAX_PAGE_HISTORY:
        stack.pop(0)
    st.session_state[PAGE_HISTORY_LAST_KEY] = current_page


def _lib_handle_float_back_query() -> None:
    """?_lib_back=1 を消費して go_back_page 相当の遷移を行う（components から URL で起動）。"""
    qb = st.query_params.get("_lib_back")
    if qb is None:
        return
    try:
        if "_lib_back" in st.query_params:
            del st.query_params["_lib_back"]
    except Exception:
        pass
    go_back_page()


init_navigation_state()


def _lib_coalesce_nav_router() -> None:
    """現在のページキーを NAV_PAGE_ROUTER_KEY に一本化。旧キーは削除する。"""
    r = st.session_state.get(NAV_PAGE_ROUTER_KEY)
    if r not in _PAGES_SET:
        _migrated = False
        if _LEGACY_NAV_IDX_KEY in st.session_state:
            try:
                _ix = int(st.session_state[_LEGACY_NAV_IDX_KEY])
                if 0 <= _ix < len(PAGES):
                    st.session_state[NAV_PAGE_ROUTER_KEY] = PAGES[_ix]
                    _migrated = True
            except (TypeError, ValueError):
                pass
        if not _migrated and _LEGACY_NAV_PAGE_KEY in st.session_state:
            _leg = st.session_state[_LEGACY_NAV_PAGE_KEY]
            _leg = _leg.strip() if isinstance(_leg, str) else _leg
            if isinstance(_leg, str) and _leg in _PAGES_SET:
                st.session_state[NAV_PAGE_ROUTER_KEY] = _leg
        if st.session_state.get(NAV_PAGE_ROUTER_KEY) not in _PAGES_SET:
            st.session_state[NAV_PAGE_ROUTER_KEY] = PAGES[0]
    st.session_state.pop(_LEGACY_NAV_IDX_KEY, None)
    st.session_state.pop(_LEGACY_NAV_PAGE_KEY, None)


_lib_coalesce_nav_router()

# ブックマーク／外部リンク用：初回のみ ?nav= を読み session と同期（通常遷移はボタンでフルリロードなし）
_nav_qp = st.query_params.get("nav")
if _nav_qp is not None:
    _raw = _nav_qp[0] if isinstance(_nav_qp, list) else _nav_qp
    _nav_val = _raw.strip() if isinstance(_raw, str) else ""
    # TOP サービスカード等の短リンク → 既存ページキーへ正規化
    _nav_aliases = {"DCF": "AI分析ツール"}
    _nav_val = _nav_aliases.get(_nav_val, _nav_val)
    _nav_removed = False
    try:
        if "nav" in st.query_params:
            del st.query_params["nav"]
            _nav_removed = True
    except Exception:
        pass
    if _nav_val in PAGES:
        if st.session_state.get(NAV_PAGE_ROUTER_KEY) != _nav_val:
            st.session_state[NAV_PAGE_ROUTER_KEY] = _nav_val
            st.rerun()
    elif _nav_val and _nav_removed:
        # クエリを消せたときだけ 1 回 rerun（消せないと無限 rerun → WS 切断ログが大量に出る）
        st.rerun()

# フローティング「戻る」ボタン（親ウィンドウが ?_lib_back=1 で起動）
_lib_handle_float_back_query()

_pending = st.session_state.pop(NAV_PENDING_KEY, None)
if _pending in PAGES:
    st.session_state[NAV_PAGE_ROUTER_KEY] = _pending
    # TOPのCTA/カード等はここで遷移する。従来は TOP 行きだけフラグを立てており、
    # 別ページへ飛ぶときは detect_page_change 頼みでタイミングによって先頭スクロールが欠けることがあった。
    st.session_state[SCROLL_TOP_ONCE_KEY] = True

_lib_coalesce_nav_router()

st.sidebar.markdown(f"### {t('brand_company')}")


def _lib_on_nav_router_change() -> None:
    if st.session_state.get(NAV_PAGE_ROUTER_KEY) == "TOP":
        st.session_state[SCROLL_TOP_ONCE_KEY] = True


page = st.sidebar.selectbox(
    t("sidebar_pages"),
    options=_PAGES_OPTIONS,
    key=NAV_PAGE_ROUTER_KEY,
    format_func=page_display_label,
    on_change=_lib_on_nav_router_change,
)
if page not in _PAGES_SET:
    page = PAGES[0]

# ページ切替時のみ先頭スクロールフラグ（同一ページの rerun では立てない）
detect_page_change(page)

st.sidebar.markdown("---")
st.sidebar.caption(t("brand_tone"))

with st.sidebar.expander(t("health_expander"), expanded=False):
    render_sidebar_health(BASE_DIR)


def _top_brand_strip_html() -> str:
    """TOP 専用・ヘッダー左側のブランド帯（社名のみ）。"""
    return f"""
<div class="lib-top-brand-strip lib-top-brand-strip--home">
  <div class="lib-top-brand-strip__text">
    <span class="lib-top-brand-strip__name">{html.escape(t("brand_company"), quote=True)}</span>
  </div>
</div>
"""


def _render_compact_lang_switcher() -> None:
    """ヘッダー右列用の極小 J | E（session の LANG_KEY のみ更新）。"""
    st.markdown(
        '<span class="lib-lang-switcher-mark" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )
    _ja, _sep, _en = st.columns([0.4, 0.1, 0.4], gap="small")
    with _ja:
        if st.button(
            "J",
            key="_lib_lang_ja",
            disabled=_lang() == "ja",
            width="stretch",
            help="日本語",
        ):
            st.session_state[LANG_KEY] = "ja"
            st.rerun()
    with _sep:
        st.markdown(
            '<p style="margin:0;padding:0;text-align:center;">|</p>',
            unsafe_allow_html=True,
        )
    with _en:
        if st.button(
            "E",
            key="_lib_lang_en",
            disabled=_lang() == "en",
            width="stretch",
            help="English",
        ):
            st.session_state[LANG_KEY] = "en"
            st.rerun()


def _render_app_header_row(*, current_page: str) -> None:
    """
    メイン先頭の1行：左にパンくず（TOP 以外）またはブランド帯（TOP）、右端に言語 J|E。
    """
    try:
        _left, _lang = st.columns([11.65, 0.55], gap="small", vertical_alignment="center")
    except TypeError:
        _left, _lang = st.columns([11.65, 0.55], gap="small")
    with _left:
        if current_page != "TOP":
            render_site_breadcrumbs(
                current_page=current_page,
                pending_nav_key=NAV_PENDING_KEY,
                valid_pages=PAGES,
                home_label=t("breadcrumb_home"),
                back_button_help=t("breadcrumb_back_help"),
                format_page_label=page_display_label,
                format_group_label=breadcrumb_group_label,
            )
        else:
            st.markdown(_top_brand_strip_html().strip(), unsafe_allow_html=True)
    with _lang:
        _render_compact_lang_switcher()


_render_app_header_row(current_page=page)

# ページ遷移などでフラグが立っているときだけ 1 回、ビュー先頭へ（全ページ共通）
inject_scroll_to_top_script()

# ============================================================
# 7) Pages
# ============================================================

# ---------------- TOP ----------------
if page == "TOP":
    st.markdown(
        """
<style>
/* TOP：ヒーロー直下〜を画面幅いっぱいに近づける（サイドバー分は除きメイン列内で 100%） */
section[data-testid="stMain"] .block-container {
  max-width: 100% !important;
  width: 100% !important;
  padding-left: clamp(12px, 4.5vw, 72px) !important;
  padding-right: clamp(12px, 4.5vw, 72px) !important;
  box-sizing: border-box !important;
}
section[data-testid="stMain"] .block-container .hr {
  margin: 1.35rem 0 1.6rem 0 !important;
  opacity: 0.85;
}
"""
        + _top_immersive_css_block()
        + """
</style>
""",
        unsafe_allow_html=True,
    )
    # 先頭スクロールは inject_scroll_to_top_script()（ヘッダー直後）で全ページ共通処理済み

    # TOP：ヒーロー → サービスカード → NEWS → トレンド → 以降（旧・大型ナビカード群は撤去して UI 一本化）
    render_top_hero()
    render_top_service_cards_section()
    hr()
    render_news_split_tanizawa_style(
        base_dir=BASE_DIR,
        max_items=8,
        section_title=t("news_section_lede"),
        wide_layout=True,
        site_category_logo_html=_logo_html_for_header() or None,
        detail_expander_label=t("news_detail"),
        news_mast_heading=t("news_section_mast"),
        news_kicker_label=t("news_section_kicker"),
        lang=_lang(),
        news_featured_label=t("news_featured_label"),
        news_more_expander_tpl=t("news_more_expander_tpl"),
        news_archive_expander_label=t("news_archive_expander"),
        news_archive_month_prefix=t("news_archive_month_prefix"),
        news_link_label=t("news_link_label"),
        news_empty_hint=t("news_empty_hint"),
        news_current_slot_count=3,
        news_load_cap=80,
    )
    hr()
    # 【不動産トレンド情報】表示: 注目1件（常時表示）→ 用途別4カテゴリ（expander・初期閉）→ アーカイブ（expander・月別カード）
    # データ追加: `lib/real_estate_trends.py` の CURATED_TREND_ITEMS、または `data/trend_items.json`
    render_real_estate_trends_section(
        base_dir=BASE_DIR,
        t=t,
        lang=_lang(),
        render_section_title=render_corporate_section_title,
    )
    hr()

    with st.expander(t("exp_philosophy"), expanded=False):
        render_corporate_section_title(
            title_jp=t("about_title"),
            title_en="",
            subtitle=t("about_sub"),
        )
        st.write(t("about_body"))
        hr()
        info_kpis()
        hr()

        cols = st.columns(3)
        with cols[0]:
            st.markdown('<div class="card lib-corp-pillar-card">', unsafe_allow_html=True)
            st.markdown(f"### {t('pillar_1_h')}")
            st.write(t("pillar_1_b"))
            st.markdown("</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown('<div class="card lib-corp-pillar-card">', unsafe_allow_html=True)
            st.markdown(f"### {t('pillar_2_h')}")
            st.write(t("pillar_2_b"))
            st.markdown("</div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown('<div class="card lib-corp-pillar-card">', unsafe_allow_html=True)
            st.markdown(f"### {t('pillar_3_h')}")
            st.write(t("pillar_3_b"))
            st.markdown("</div>", unsafe_allow_html=True)

    # 地価公示・地価調査（既定で畳み込み）
    with st.expander(t("exp_chika"), expanded=False):
        st.markdown(
            f"""
<div style="color:#111827;font-size:1.05rem;line-height:1.85;">
{t("chika_intro")}
</div>
""",
            unsafe_allow_html=True,
        )
        c_chika_a, c_chika_b = st.columns(2)
        with c_chika_a:
            if st.button(
                t("chika_btn_web"),
                key="chika_open_web_map",
                width="stretch",
            ):
                st.switch_page("pages/chika_map_intro.py")
        with c_chika_b:
            _chika_qgis: Optional[Path] = None
            _chika_env = os.environ.get("CHIKA_QGIS_PROJECT", "").strip()
            if _chika_env and Path(_chika_env).is_file():
                _chika_qgis = Path(_chika_env)
            elif (BASE_DIR / "data" / "koutei_chika.qgz").is_file():
                _chika_qgis = BASE_DIR / "data" / "koutei_chika.qgz"
            elif (BASE_DIR / "data" / "koutei_chika.qgs").is_file():
                _chika_qgis = BASE_DIR / "data" / "koutei_chika.qgs"
            else:
                try:
                    _sec_chika = st.secrets["chika"]
                    _qp = Path(str(_sec_chika.get("qgis_project_path", "")).strip())
                    if _qp.is_file():
                        _chika_qgis = _qp
                except Exception:
                    pass
            if _chika_qgis is not None:
                if st.button(
                    t("chika_btn_qgis"),
                    key="chika_open_qgis",
                    width="stretch",
                ):
                    try:
                        os.startfile(str(_chika_qgis))  # type: ignore[attr-defined]
                    except OSError as e:
                        st.error(t("chika_qgis_err").format(e=e))

    render_fullwidth_contact_cta(
        pending_nav_key=NAV_PENDING_KEY,
        valid_pages=PAGES,
        cta_kicker=t("cta_kicker"),
        button_label=t("cta_contact_btn"),
    )
    render_dark_footer_sitemap(
        pending_nav_key=NAV_PENDING_KEY,
        valid_pages=PAGES,
        expander_title=t("sitemap_title"),
        section_titles=(
            t("smap_about"),
            t("smap_services"),
            t("smap_tools"),
            t("smap_gov"),
        ),
        format_page_label=page_display_label,
    )

# --------- はじめての方へ ----------
elif page == "はじめての方へ":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_hajimete")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        HAJIMETE_PAGE_MARKDOWN if _lang() == "ja" else HAJIMETE_PAGE_MARKDOWN_EN
    )

# --------- 業務内容 ----------
elif page == "業務内容":
    st.title(page_display_label(page))
    # キャプションはメイン DOM の翻訳対象になるため、カタログ原文どおり出すには iframe に隔離する
    components.html(
        caption_iframe_document(
            SERVICES_PAGE["caption"] if _lang() == "ja" else t("caption_gyomu")
        ),
        height=104,
        scrolling=False,
    )
    hr()

    if st.checkbox(SERVICES_PAGE["debug_checkbox_label"], key="services_data_dump"):
        st.caption(f"読み込み元: `{services_catalog_module.__file__}`")
        st.warning(
            "Streamlit の **`st.json` は DOM 上のテキストになるため、ブラウザ翻訳が **キー・値・true/false** まで置き換えることがあります。"
            " その表示は **データと一致しません**（見た目だけの問題）。"
            " 本ページでは **ダウンロード用バイト列を唯一のソース**とし、プレビューも **同一バイト列を UTF-8 デコードした文字列**だけを使います。"
        )
        _lit_svc = next(s for s in SERVICES if s.get("id") == "litigation_rent")
        _title_sha = hashlib.sha256(_lit_svc["title"].encode("utf-8")).hexdigest()
        _title_sha_catalog = hashlib.sha256(
            services_catalog_module.TITLE_LITIGATION_RENT.encode("utf-8")
        ).hexdigest()
        st.info(
            "**照合手順:** ① 下のボタンで `services_dump.json` を保存 ② **メモ帳**で開く（**ブラウザで .json を開かない**）。"
            " ③ 下の **ファイル全体 SHA-256** を PowerShell の `Get-FileHash .\\services_dump.json -Algorithm SHA256` と比較。"
        )
        st.caption(
            f"実行中 `litigation_rent.title` の SHA-256(UTF-8) = `{_title_sha}` "
            f"| カタログ定数 `TITLE_LITIGATION_RENT` と一致: **{_title_sha == _title_sha_catalog}**"
        )
        _svc_dump = {"services_page": SERVICES_PAGE, "services": SERVICES}
        _svc_dump_bytes = json.dumps(_svc_dump, ensure_ascii=False, indent=2).encode("utf-8")
        _svc_dump_text = _svc_dump_bytes.decode("utf-8")
        _dump_sha256 = hashlib.sha256(_svc_dump_bytes).hexdigest()
        st.caption(
            f"`services_dump.json` 全体（UTF-8 バイト列）の SHA-256 = `{_dump_sha256}` "
            "← ダウンロード後のファイルと一致すれば、メモ帳に保存した内容とサーバー出力は同一です。"
        )
        st.download_button(
            label="services_dump.json をダウンロード（UTF-8・上記 SHA と一致確認可）",
            data=_svc_dump_bytes,
            file_name="services_dump.json",
            mime="application/json; charset=utf-8",
            key="services_json_download",
        )
        with st.expander(
            "画面内プレビュー（ダウンロードと同一テキスト・翻訳抑制用 iframe）",
            expanded=False,
        ):
            st.caption(
                "次の枠は **上記バイト列を `decode('utf-8')` した文字列**を HTML エスケープして表示しています。"
                " `st.json` は使いません。親ページの翻訳の影響を減らすため **別 iframe** に `translate=no` / `notranslate` / `google:notranslate` を付与しています。"
            )
            _preview_html = (
                "<!DOCTYPE html><html translate=\"no\" lang=\"ja\" class=\"notranslate\">"
                "<head><meta charset=\"utf-8\">"
                '<meta name="google" content="notranslate">'
                "<style>"
                "body{margin:0;padding:10px;font:13px/1.45 ui-monospace,Consolas,monospace;"
                "white-space:pre-wrap;word-break:break-word;background:transparent;color:inherit;}"
                "</style></head><body class=\"notranslate\">"
                + html.escape(_svc_dump_text)
                + "</body></html>"
            )
            components.html(_preview_html, height=520, scrolling=True)

    # 本番本文: st.subheader / st.expander / st.markdown はブラウザ翻訳で文言が変わるため使わない。
    # カタログの文字列をそのまま iframe（translate=no）内で表示し、** のみ HTML 太字に変換する。
    if _lang() == "en":
        _svc_en_h = min(5200, estimate_markdown_height(SERVICES_PAGE_MARKDOWN_EN) + 240)
        render_markdown_iframe(SERVICES_PAGE_MARKDOWN_EN, height=_svc_en_h)
        with st.expander(t("services_jp_expander"), expanded=False):
            _body_iframe_h = estimate_services_iframe_height(SERVICES)
            components.html(
                services_body_document_html(SERVICES),
                height=_body_iframe_h,
                scrolling=True,
            )
    else:
        _body_iframe_h = estimate_services_iframe_height(SERVICES)
        components.html(
            services_body_document_html(SERVICES),
            height=_body_iframe_h,
            scrolling=True,
        )

# --------- 業務の流れ ----------
elif page == "業務の流れ":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_nagare")),
        height=112,
        scrolling=False,
    )
    hr()
    _flow_faq_md = build_flow_faq_page_markdown()
    render_markdown_iframe(
        _flow_faq_md,
        height=min(8000, estimate_markdown_height(_flow_faq_md) + 200),
    )

# --------- AI分析ツール ----------
elif page == "AI分析ツール":
    flush_multipage_new_tab_opener()
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_ai_tools")),
        height=112,
        scrolling=False,
    )
    render_markdown_iframe(
        AI_TOOLS_INTRO_MARKDOWN if _lang() == "ja" else AI_TOOLS_INTRO_MARKDOWN_EN,
        height=132,
    )
    render_shisanhyo_main_demo_block()
    hr()
    render_ai_catalog_experience(
        localized_ai_projects_for_catalog(),
        demo_session_key="ai_catalog_demo_tools_page",
        key_prefix="ait_",
    )

# --------- AI評価研究グループ ----------
elif page == "AI評価研究グループ":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_ai_lab")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        AI_RESEARCH_GROUP_PAGE_MARKDOWN
        if _lang() == "ja"
        else AI_RESEARCH_GROUP_PAGE_MARKDOWN_EN,
        info_boxes=[t("info_ai_lab")],
    )


# --------- 価格の目利き ----------
elif page == "価格の目利き":
    render_mekiki_page(page)

# --------- 不動産鑑定士マッチング ----------
elif page == "不動産鑑定士マッチング":
    render_matching_page(page)

# --------- AI思想（Methodology） ----------
elif page == "AI思想（Methodology）":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_ai_method")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        AI_METHODOLOGY_PAGE_MARKDOWN
        if _lang() == "ja"
        else AI_METHODOLOGY_PAGE_MARKDOWN_EN
    )

# --------- 企業統治（Governance） ----------
elif page == "企業統治（Governance）":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_gov")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        GOVERNANCE_TEXT if _lang() == "ja" else GOVERNANCE_TEXT_EN,
        info_boxes=[t("info_governance")],
    )

# --------- 情報セキュリティ（ISMS相当） ----------
elif page == "情報セキュリティ（ISMS相当）":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_sec")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        SECURITY_TEXT if _lang() == "ja" else SECURITY_TEXT_EN,
        info_boxes=[t("info_security")],
    )

# --------- 倫理規程・不動産鑑定士職業倫理 ----------
elif page == "倫理規程・不動産鑑定士職業倫理":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_ethics")),
        height=112,
        scrolling=False,
    )
    hr()
    render_markdown_iframe(
        ETHICS_TEXT if _lang() == "ja" else ETHICS_TEXT_EN,
        info_boxes=[t("info_ethics")],
    )

# --------- 実績・ケーススタディ ----------
elif page == "実績・ケーススタディ":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_cases")),
        height=112,
        scrolling=False,
    )
    hr()
    _cs_md = build_case_studies_page_markdown()
    render_markdown_iframe(
        _cs_md,
        info_boxes=[t("info_cases")],
        height=min(8000, estimate_markdown_height(_cs_md) + 200),
    )

# --------- 代表プロフィール ----------
elif page == "代表プロフィール":
    st.title(page_display_label(page))
    hr()
    _prof_md = build_profile_page_markdown()
    render_markdown_iframe(_prof_md)

# --------- 会社概要 ----------
elif page == "会社概要":
    st.title(page_display_label(page))
    hr()
    render_markdown_iframe(
        COMPANY_OVERVIEW_PAGE_MARKDOWN
        if _lang() == "ja"
        else COMPANY_OVERVIEW_PAGE_MARKDOWN_EN
    )

# --------- お問い合わせ ----------
elif page == "お問い合わせ":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_contact")),
        height=112,
        scrolling=False,
    )
    hr()

    purpose = st.selectbox(
        t("contact_purpose"),
        contact_purpose_options(),
        key="contact_purpose",
    )

    with st.form("contact_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(t("contact_name"), key="contact_name")
            email = st.text_input(t("contact_email"), key="contact_email")
        with c2:
            tel = st.text_input(t("contact_tel"), key="contact_tel")
            address = st.text_input(t("contact_addr"), key="contact_addr")

        message = st.text_area(
            t("contact_msg"),
            height=180,
            placeholder=t("contact_msg_ph"),
            key="contact_msg",
        )

        agree = st.checkbox(t("contact_agree"), key="contact_agree")
        submitted = st.form_submit_button(t("contact_submit"))

    if submitted:
        if not (name and email and message and agree):
            st.error(t("contact_err_required"))
        else:
            payload = {
                "purpose": purpose,
                "name": name.strip(),
                "email": email.strip(),
                "tel": (tel or "").strip(),
                "address": (address or "").strip(),
                "message": message.strip(),
            }
            smtp_ov = build_smtp_overrides_for_submit()
            resend_ov = build_resend_overrides_for_submit()
            try:
                ok, msg, extra_warn, email_sent, storage_note = submit_contact(
                    BASE_DIR, payload, smtp_ov, resend_ov
                )
            except Exception as exc:  # noqa: BLE001
                st.error(t("contact_err_exc").format(exc=exc))
            else:
                if ok:
                    st.success(msg)
                    if storage_note:
                        st.caption(storage_note)
                    if extra_warn:
                        st.warning(extra_warn)
                    if not email_sent:
                        inbox = get_office_inbox_email()
                        if inbox:
                            st.info(t("contact_info_secrets_next"))
                            st.link_button(
                                t("contact_mailto_btn"),
                                build_contact_mailto_href(inbox, payload),
                                type="primary",
                            )
                        else:
                            st.info(t("contact_info_secrets_setup"))
                    with st.expander(t("contact_copy"), expanded=False):
                        st.json(
                            {**payload, "submitted_at": datetime.now().isoformat(timespec="seconds")}
                        )
                else:
                    st.error(msg)

# --------- プライバシー（統合版） ----------
elif page == "プライバシー":
    st.title(page_display_label(page))
    components.html(
        caption_iframe_document(t("caption_privacy")),
        height=112,
        scrolling=False,
    )
    hr()
    _priv = PRIVACY_PAGE_MARKDOWN if _lang() == "ja" else PRIVACY_PAGE_MARKDOWN_EN
    render_markdown_iframe(
        _priv,
        info_boxes=[t("info_privacy")],
        height=min(8000, estimate_markdown_height(_priv) + 250),
    )

else:
    st.error(t("invalid_page"))
    st.caption(t("invalid_page_name").format(name=page))
    if st.button(t("btn_back_top"), key="lib_nav_invalid_reset_top", type="primary"):
        st.session_state[NAV_PAGE_ROUTER_KEY] = PAGES[0]
        st.rerun()

# ------------------------------------------------------------
# 8) Footer
# ------------------------------------------------------------
hr()
st.markdown(
    f"""
<div class="footer">
{t("footer_line").format(company=html.escape(t("brand_company"), quote=True))}
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(t("footer_translation_note"))

# ========== ページ履歴の確定・固定ナビ（各ランの末尾で実行） ==========
push_page_history(page)
handle_page_top_reset(page)
render_floating_nav_buttons()
