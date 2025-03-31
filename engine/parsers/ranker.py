import asyncio
from typing import List, Union

from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from prefect import get_run_logger, task
from engine.models.url_model import BasePayload
from engine.models.youtube_payload import YoutubePayload


PROMPT = """
You are an advanced LLM with deep knowledge of real-world ranking algorithms (e.g., TF-IDF, semantic similarity, embedding-based relevance). Your task is to **assign a rank from 0 to 10** for each item in a list, based on its relevance to a given user query.

**Guidelines**:
1. A rank of **0** indicates completely irrelevant or off-topic content.
2. A rank of **10** indicates highly relevant, comprehensive coverage of the user query.
3. Consider:
   - **Semantic overlap** between the item’s title/summary and the user query.
   - **Depth and detail** of the item’s coverage regarding the query’s key points.
   - **Real-world utility**: how well this item would satisfy a user searching for that query.
4. Provide a **brief explanation** (1–2 lines) for each item’s score, referencing the main factors that influenced your ranking.

Below is the list of information (each item has a title, summary, and/or numbers):

{payload}

Below is the user query:

{query}

Please output a ranking (0–10) for each item, along with a concise reason for that rank.

"""

@task(log_prints=True)
async def llm_ranker(
    query: str, payload: List[Union[BasePayload, YoutubePayload]]
) -> List[Union[BasePayload, YoutubePayload]]:
    """
    Rank the payload based on the LLM's response.
    """
    logger = get_run_logger()
    llm = AzureChatOpenAI(
        api_version="2024-08-01-preview",
        deployment_name="gpt-4o-0806",
        temperature=0.0,
        streaming=True,
        client=None,  # Ensure this is correctly set or omitted if not needed
    ).with_structured_output(BasePayload)
    prompt = PromptTemplate(
            template=PROMPT,
            input_variables=["html_text"],
        )
    chain = prompt | llm
    semaphore = asyncio.Semaphore(6)
    async def _summarize(i, value):
        async with semaphore:
            try:
                base_payload = await chain.ainvoke({"payload": value.model_dump(), "query": query})
                logger.info(f"LLM Summary [{i}]: {base_payload}")
                payload[i].rank_reason = base_payload.rank_reason
                payload[i].result_rank = base_payload.result_rank
            except Exception as e:
                logger.error(f"Error during LLM summarization: {e}")
                pass
    await asyncio.gather(*(_summarize(i, value) for i, value in enumerate(payload)))
    return payload
