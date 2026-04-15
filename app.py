from fastapi import FastAPI

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

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
@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/top")
def top():
    return {"message": "Libralys API OK"}
