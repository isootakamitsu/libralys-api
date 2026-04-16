# ============================================================
# UI Builder（Streamlit完全再現）
# ============================================================

def build_ui_top(lang: str = "ja"):

    return {
        "title": "ライブラリーズ",
        "meta": {
            "streamlitTop": True,
            "hidePageTitle": True
        },
        "sections": [

            # ---------------- HERO ----------------
            {
                "type": "hero",
                "layout": "streamlit",
                "meta": {
                    "headline": "不動産鑑定 × AI分析",
                    "subcopy_lines": [
                        "価格の見える化を実現",
                        "データとロジックで価値を説明する"
                    ],
                    "background": "/image/ai_realestate_bg.jpg",
                    "ctas": [
                        {"label": "業務内容を見る", "target": "#/services"},
                        {"label": "分析ツールへ", "target": "#/dcf"}
                    ]
                }
            },

            # ---------------- QUICK NAV ----------------
            {
                "type": "cards",
                "layout": "streamlit-nav",
                "items": [
                    {"title": "業務内容", "target": "#/services"},
                    {"title": "市場分析", "target": "#/market"},
                    {"title": "DCF", "target": "#/dcf"},
                ]
            },

            # ---------------- NEWS ----------------
            {
                "type": "markup",
                "layout": "top-news",
                "meta": {
                    "html": """
                    <div class='news'>
                        <p>2026.04 サイト公開</p>
                        <p>AI分析機能を強化</p>
                    </div>
                    """
                }
            },

            # ---------------- TRENDS ----------------
            {
                "type": "trends",
                "meta": {
                    "items": [
                        {"label": "地価動向", "value": "+2.3%"},
                        {"label": "建築費", "value": "+5.1%"},
                        {"label": "金利", "value": "0.75%"},
                    ]
                }
            },

            # ---------------- SERVICES ----------------
            {
                "type": "cards",
                "layout": "streamlit-service",
                "title": "業務内容",
                "items": [
                    {"title": "鑑定評価", "text": "公的評価対応"},
                    {"title": "AI分析", "text": "価格推定・可視化"},
                    {"title": "コンサル", "text": "投資判断支援"},
                ]
            },

            # ---------------- NAV MULTI ----------------
            {
                "type": "cards",
                "layout": "streamlit-nav-multi",
                "meta": {
                    "groups": [
                        [
                            {"title": "価格の目利き", "target": "#/mekiki"},
                            {"title": "AI分析", "target": "#/ai"}
                        ],
                        [
                            {"title": "会社概要", "target": "#/company"},
                            {"title": "お問い合わせ", "target": "#/contact"}
                        ]
                    ]
                }
            }
        ]
    }
