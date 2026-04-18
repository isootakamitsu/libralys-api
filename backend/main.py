# ============================================================
# Libralys FastAPI Backend（完全版）
# ============================================================

from fastapi import FastAPI

from libralys_app.routes_ui import router as ui_router

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://libralys.com"],
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
    return {
        "status": "ok",
        "data": {},
    }


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
