from fastapi import FastAPI

app = FastAPI()


@app.get("/api/borrame")
async def borrame():
    return {"message": "hola"}
