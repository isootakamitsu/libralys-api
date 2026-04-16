from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/api/texts")
def api_texts():
    return {"message": "OK"}
