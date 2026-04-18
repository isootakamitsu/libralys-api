# ============================================================
# Libralys FastAPI Backend（完全版）
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libralys_app.routes_ui import router as ui_router

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発用：全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Router ----------------
app.include_router(ui_router)

# ---------------- Root ----------------
@app.get("/")
def root():
    return {
        "service": "Libralys API",
        "status": "ok"
    }

# ---------------- Texts ----------------
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
