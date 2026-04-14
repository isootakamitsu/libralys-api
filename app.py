from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "API running"}

@app.get("/top")
def top():
    return {"message": "Libralys API OK"}