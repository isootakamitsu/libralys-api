# ============================================================
# Libralys FastAPI Backend（完全版）
# ============================================================

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
for _p in (BASE_DIR, BACKEND_DIR):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lib.top_corporate import load_top_news_sorted
from lib.real_estate_trends import fetch_trend_items
from data.texts import TEXTS

from libralys_app.routes_ui import router as ui_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← 一時的に全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/texts")
async def get_texts(lang: str = "ja"):
    return {
        "status": "ok",
        "data": {},
    }


@app.get("/api/ui/top")
async def get_ui_top(lang: str = "ja"):
    lg = lang if lang in ("ja", "en") else "ja"

    texts = TEXTS.get(lg, TEXTS["ja"])

    news = load_top_news_sorted(BASE_DIR, lang=lg)
    if not news:
        news = [
            {
                "date": "2026-01-01",
                "category": "お知らせ",
                "title": "ニュース準備中",
                "body": "ニュースデータは現在準備中です。",
                "importance": 0,
                "link": ""
            }
        ]

    trends = fetch_trend_items(BASE_DIR)
    if not trends:
        trends = [
            {
                "title_ja": "市場データ準備中",
                "summary_ja": "トレンドデータは現在準備中です。",
                "source_url": "",
                "category": "市場",
                "published_date": "2026-01-01",
                "reliability_tier": "C"
            }
        ]

    return {
        "status": "ok",
        "data": {
            "texts": texts,
            "news": news,
            "trends": trends,
        },
    }

# ---------------- Router ----------------
app.include_router(ui_router)

# ---------------- Root ----------------
@app.get("/")
def root():
    return {
        "service": "Libralys API",
        "status": "ok",
    }


# ---------------- Texts ----------------
@app.get("/api/texts")
def api_texts():
    return {
        "ja": {
            "brand_company": "ライブラリーズ",
        },
        "en": {
            "brand_company": "Libralys",
        },
    }
