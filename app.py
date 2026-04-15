from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.libralys.com",
        "https://libralys.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/top")
def top():
    return {"message": "Libralys API OK"}

# ★これを追加
@app.get("/api/ui/top")
def top_ui():
    return {"message": "Libralys API OK"}
