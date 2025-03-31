import asyncio
import multiprocessing
from typing import List, Union
from prefect import get_run_logger, task
from engine.llm.app_llm import LLMResponse
from engine.models.url_model import BasePayload
from engine.models.youtube_payload import YoutubePayload
from engine.llm.app_prompt import Prompt
from engine.utils import TRIM_CONSTANT, extract_text




def payload_clean_up_to_feed_in_llm(base_payload: Union[BasePayload, YoutubePayload]) -> str:
    """Extract and clean text from the HTML content."""
    text = extract_text(base_payload.summary)
    return f"The title of the webpage is '{base_payload.title}'\nand its page content is:\n{text}...\n"


@task(log_prints=True)
async def webpage_text_parsing_using_llm(
    payload: List[Union[BasePayload, YoutubePayload]],
) -> int:
    logger = get_run_logger()
    try:
        with multiprocessing.Pool(processes=4) as pool:
            results = pool.map(payload_clean_up_to_feed_in_llm, payload)
    except Exception as e:
        logger.error(f"Error during multiprocessing: {e}")
        return []

    logger.info(f"Extracted text from HTML: {[i[:100] for i in results]}")
    semaphore = asyncio.Semaphore(8)
    success_count = 0

    async def _summarize(i, value):
        nonlocal success_count
        async with semaphore:
            try:
                base_payload = await LLMResponse.open_ai(
                    response_model=BasePayload,
                    prompt=Prompt.SUMMARY_PROMPT,
                    input_variables_payload={
                        "html_text": value[: len(value) // TRIM_CONSTANT]
                    },
                )
                logger.info(f"LLM Summary [{i}]: {base_payload}")
                payload[i].summary = base_payload.summary
                payload[i].title = base_payload.title
                payload[i].short_description = base_payload.short_description
                success_count += 1
            except Exception as e:
                logger.error(f"LLM summarization failed at index {i}: {e}")
                pass

    await asyncio.gather(*(_summarize(i, value) for i, value in enumerate(results)))

    logger.info(f"Summarization completed for {success_count}/{len(payload)} payloads.")
    return payload
