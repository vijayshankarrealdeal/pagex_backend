from fastapi import FastAPI
from engine.runner import run_query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/")
async def read_search(query: str):   
    results = await run_query(query)
    return results
