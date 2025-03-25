from fastapi import FastAPI
from engine.llm import get_results
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/")
async def read_search(query: str):   
    results = await get_results(query)
    return results
