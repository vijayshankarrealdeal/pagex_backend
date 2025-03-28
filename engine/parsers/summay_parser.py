import asyncio
import multiprocessing
from typing import List, Union
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
from prefect import get_run_logger, task
from langchain.prompts import PromptTemplate

from engine.models.url_model import BasePayload
from engine.models.youtube_payload import YoutubePayload
import re

PROMPT = """
You are a powerful llm, who is creative and intelligent as your role is to summarize the given text into 10-18 lines.
The text provided to you will have a title and webpage content.
Your task is to summarize the webpage content in 10-18 lines, and rephrase the title to make it more engaging but don't loose original title context and make a short description based on text of 2-3 line.

Below is the provided text:
{html_text}
"""


def clean_text(text: str) -> str:
    # Remove unwanted special characters (keep basic punctuation)
    text = re.sub(r"[^a-zA-Z0-9\s.,;:'\"!?()-]", "", text)

    # Replace multiple newlines with a single newline
    text = re.sub(r"\n{2,}", "\n", text)

    # Replace multiple spaces/tabs with a single space
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Trim leading/trailing whitespace
    text = text.strip()

    return text


def create_summary_title_from_payload(
    base_payload: Union[BasePayload, YoutubePayload],
) -> str:
    """Extract and clean text from the HTML content."""

    text = clean_text(base_payload.summary)
    if not base_payload.is_youtube:
        soup = BeautifulSoup(base_payload.summary, "html.parser")
        text = clean_text(soup.get_text(strip=True))

    return f"The title of the webpage is '{base_payload.title}'\nand its page content is:\n{text}"


@task(log_prints=True)
async def webpage_text_parsing_using_llm(payload: List[Union[BasePayload, YoutubePayload]]) -> int:
    logger = get_run_logger()

    try:
        with multiprocessing.Pool(processes=4) as pool:
            results = pool.map(create_summary_title_from_payload, payload)
    except Exception as e:
        logger.error(f"Error during multiprocessing: {e}")
        return 0

    logger.info(f"Extracted text from HTML: {[i[:100] for i in results]}")

    llm = AzureChatOpenAI(
        api_version="2024-08-01-preview",
        deployment_name="gpt-4o-0806",
        temperature=0.0,
        streaming=True,
        client=None,
    ).with_structured_output(BasePayload)

    prompt = PromptTemplate(
        template=PROMPT,
        input_variables=["html_text"],
    )

    chain = prompt | llm
    semaphore = asyncio.Semaphore(6)
    success_count = 0

    async def _summarize(i, value):
        nonlocal success_count
        async with semaphore:
            try:
                base_payload = await chain.ainvoke({"html_text": value})
                logger.info(f"LLM Summary [{i}]: {base_payload}")
                payload[i].summary = base_payload.summary
                payload[i].title = base_payload.title
                payload[i].short_description = base_payload.short_description
                success_count += 1
            except Exception as e:
                logger.error(f"LLM summarization failed at index {i}: {e}")

    await asyncio.gather(*(_summarize(i, value) for i, value in enumerate(results)))

    logger.info(f"Summarization completed for {success_count}/{len(payload)} payloads.")
    return payload

