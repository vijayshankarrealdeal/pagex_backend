from fastapi import FastAPI
from engine.runner import run_query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow specific origins for Flutter web + dev setup
origins = [
    "http://localhost:64168/",        # Flutter web dev (if using web)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_search(query: str):   
    results = await run_query(query)
    return results
