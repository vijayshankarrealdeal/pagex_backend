import asyncio
from typing import List, Union
from prefect import get_run_logger, task
from engine.llm.app_llm import LLMResponse
from engine.llm.app_prompt import Prompt
from engine.models.search_helper_models import BasePayload, YoutubePayload


@task(log_prints=True)
async def llm_ranker(
    query: str, payload: List[Union[BasePayload, YoutubePayload]]
) -> List[Union[BasePayload, YoutubePayload]]:
    """
    Rank the payload based on the LLM's response.
    """
    logger = get_run_logger()
    semaphore = asyncio.Semaphore(6)

    async def _summarize(i, value):
        async with semaphore:
            try:
                base_payload = await LLMResponse.open_ai(
                    response_model=BasePayload,
                    prompt=Prompt.RANK_RESULT_PROMPT,
                    input_variables_payload={
                        "payload":value,
                        "query": query,
                    },
                    output_is_list=False,
                )
                logger.info(f"LLM Summary [{i}]: {base_payload}")
                payload[i].rank_reason = base_payload.rank_reason
                payload[i].result_rank = base_payload.result_rank
                
            except Exception as e:
                logger.error(f"Error during LLM summarization: {e}")
                pass
    llm_input_payload = [
        {
            "title": value.title,
            "summary": value.summary[:400],
            "short_description": value.short_description,
        }
        for value in payload
    ]
    await asyncio.gather(*(_summarize(i, value) for i, value in enumerate(llm_input_payload)))
    return payload
