{
  "title": "ライブラリーズ",
  "meta": {
    "streamlitTop": true,
    "hidePageTitle": true
  },
  "sections": [

    {
      "type": "hero",
      "layout": "streamlit",
      "meta": {
        "headline": "不動産鑑定 × AI分析",
        "subcopy_lines": [
          "価格の見える化を実現",
          "データとロジックで価値を説明する"
        ],
        "ctas": [
          {"label": "業務内容", "target": "#/services"},
          {"label": "DCF", "target": "#/dcf"}
        ]
      }
    },

    {
      "type": "cards",
      "layout": "streamlit-nav",
      "items": [
        {"title": "業務内容", "target": "#/services"},
        {"title": "市場分析", "target": "#/market"},
        {"title": "DCFシミュレータ", "target": "#/dcf"}
      ]
    },

    {
      "type": "markup",
      "layout": "top-news",
      "meta": {
        "html": "<p>最新情報：AI分析機能アップデート</p>"
      }
    },

    {
      "type": "trends",
      "meta": {
        "items": [
          {"label": "地価", "value": "+2.1%"},
          {"label": "建築費", "value": "+4.5%"},
          {"label": "金利", "value": "0.75%"}
        ]
      }
    },

    {
      "type": "cards",
      "layout": "streamlit-service",
      "title": "サービス",
      "items": [
        {"title": "鑑定評価", "text": "公的評価対応"},
        {"title": "AI分析", "text": "価格推定"},
        {"title": "コンサル", "text": "投資判断"}
      ]
    },

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
