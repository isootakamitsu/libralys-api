from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ★ 正しいimport（名前統一）
from libralys_app.routes_ui import router as ui_router

# ★ まずappを定義
app = FastAPI()

# CORS（最初は * にして動作確認推奨）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ←確認後に本番ドメインへ戻す
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルート確認
@app.get("/")
def root():
    return {
        "service": "Libralys API",
        "docs": "/docs"
    }

# texts（必要）
@app.get("/api/texts")
def api_texts():
    return {
        "ja": {"brand_company": "ライブラリーズ"},
        "en": {"brand_company": "Libralys"}
    }

# ★ ルーターは1回だけ
app.include_router(ui_router)
