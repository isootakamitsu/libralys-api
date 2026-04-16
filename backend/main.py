from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ★ これが重要（routes_ui を使う）
from libralys_app.routes_ui import router as ui_router

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://libralys.com", "https://www.libralys.com"],
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

# ★ ここが最重要
app.include_router(ui_router)
