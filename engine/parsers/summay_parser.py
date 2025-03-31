import asyncio
import multiprocessing
from typing import List, Union
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
from prefect import get_run_logger, task
from langchain.prompts import PromptTemplate
from engine.llm.all_llm import LLMResponse
from engine.models.url_model import BasePayload
from engine.models.youtube_payload import YoutubePayload
from engine.utils import TRIM_CONSTANT, clean_html, clean_text, sanitize_text

PROMPT = """
You are a helpful and concise assistant. Your job is to analyze and summarize the following web page content.

Instructions:
1. Summarize the webpage content in **10 to 18 clear and informative lines**.
2. Rephrase the given title to make it more engaging, but **keep the original meaning**.
3. Create a short 2-3 line description based on the webpage content.
4. Avoid speculation or sensitive content. Stay neutral and factual.
5. If content is missing or incomplete, respond appropriately with a polite message.

Content to summarize:
{html_text}
"""


def create_summary_title_from_payload(base_payload) -> str:
    """Extract and clean text from the HTML content."""
    text = clean_html(base_payload.summary)
    text = clean_text(text)
    text = sanitize_text(text)
    return f"The title of the webpage is '{base_payload.title}'\nand its page content is:\n{text[: len(text)]}...\n"


@task(log_prints=True)
async def webpage_text_parsing_using_llm(
    payload: List[Union[BasePayload, YoutubePayload]],
) -> int:
    logger = get_run_logger()
    try:
        with multiprocessing.Pool(processes=4) as pool:
            results = pool.map(create_summary_title_from_payload, payload)
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
                    prompt=PROMPT,
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
