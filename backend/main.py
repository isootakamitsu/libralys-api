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

@app.get("/api/texts")
def api_texts():
    return {
        "ja": {
            "brand_company": "ライブラリーズ",
            "site_catchphrase": "不動産鑑定 × AI分析"
        },
        "en": {
            "brand_company": "Libralys",
            "site_catchphrase": "Real Estate Appraisal × AI"
        }
    }
