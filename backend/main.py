from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://libralys.com", "https://www.libralys.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

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

# ←ここから追加
@app.get("/api/ui/top")
def ui_top(lang: str = "ja"):
    return {
        "title": "ライブラリーズ",
        "subtitle": "不動産鑑定 × AI分析",
        "sections": []
    }
