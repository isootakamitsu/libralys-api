from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libralys_app.routes_ui import router as ui_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "Libralys API"}

@app.get("/api/texts")
def api_texts():
    return {
        "ja": {"brand_company": "ライブラリーズ"},
        "en": {"brand_company": "Libralys"}
    }

app.include_router(ui_router)
