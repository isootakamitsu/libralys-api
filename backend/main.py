# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =========================
# FastAPI本体
# =========================
app = FastAPI(title="Libralys API")

# =========================
# CORS設定（必須）
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://libralys.com",
        "https://www.libralys.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ルート確認
# =========================
@app.get("/")
def root():
    return {
        "service": "Libralys API",
        "status": "ok",
        "endpoints": [
            "/api/texts",
            "/api/ui/top",
            "/health"
        ]
    }

# =========================
# ヘルスチェック（重要）
# =========================
@app.get("/health")
def health():
    return {"ok": True}

# =========================
# テキストAPI（最低限）
# =========================
@app.get("/api/texts")
def api_texts():
    return {
        "ja": {
            "brand_company": "ライブラリーズ"
        },
        "en": {
            "brand_company": "Libralys"
        }
    }

# =========================
# UI API（暫定：確実動作版）
# =========================
@app.get("/api/ui/top")
def ui_top(lang: str = "ja"):
    return {
        "title": "ライブラリーズ",
        "meta": {
            "streamlitTop": True
        },
        "sections": [
            {
                "type": "hero",
                "title": "不動産鑑定 × AI分析",
                "text": "価格の見える化を実現"
            },
            {
                "type": "cards",
                "title": "業務内容",
                "items": [
                    {"title": "業務内容", "target": "#/services"},
                    {"title": "市場分析", "target": "#/market"},
                    {"title": "DCF", "target": "#/dcf"},
                ]
            }
        ]
    }
