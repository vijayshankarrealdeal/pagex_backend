import asyncio
from typing import List

from engine.llm.all_llm import LLMResponse
from engine.models.url_model import BasePayload, PageContent, URLResponseModel
from prefect import task, get_run_logger
from engine.utils import TRIM_CONSTANT


PROMPT_1 = """You are an intelligent and creative language model.

Your task is to extract the most relevant URLs as much you can and their titles based on the user's query.

**Instructions:**
- Remove any Google policy, login, support, or irrelevant URLs.
- Include as much URLs only if they relate to the user's query.
- Prefer social media (Instagram, Twitter/X, Reddit, Facebook), music platforms (Spotify, Apple Music, JioSaavn), News, Myntra, Amazon, Flipkart,  Wikipedia or YouTube links if available.

**Input:**
- URL List: {url_list}
- User Query: {user_query}

Return a list of the most relevant URLs and their titles.
"""


PROMPT_2 = """You are a helpful and informative writing assistant.

Your task is to convert the given web page text and image descriptions into a clean, engaging article based on the user's query, using Markdown formatting.

**Instructions:**
1. Summarize the most important facts — names, dates, achievements, numbers.
2. Write a clear, easy-to-read article in Markdown format:
   - Use headings, bullet points, and short paragraphs.
   - Keep the tone informative yet engaging.
3. Select the top 3 most relevant and meaningful image URLs (avoid restricted sources like `gstatic`).
4. Do NOT include any clickable links or raw URLs in the final article.

---

**Input:**
- User Query: {user_query}
- Full Page Text: {page_content_full_text}
- Image URLs with Descriptions: {page_content_images}
"""


@task(name="LLM Runs", log_prints=True)
async def url_link_parser(
    user_query, url_list: List[BasePayload], page_content: PageContent
) -> URLResponseModel:
    logger = get_run_logger()

    # Wait for both tasks to complete concurrently
    response_list, response_content = await asyncio.gather(
        LLMResponse.open_ai(
            response_model=BasePayload,
            prompt=PROMPT_1,
            input_variables_payload={
                "url_list": url_list,
                "user_query": user_query,
            },
            output_is_list=True,
        ),
        LLMResponse.open_ai(
            response_model=PageContent,
            prompt=PROMPT_2,
            input_variables_payload={
                "user_query": user_query,
                "page_content_full_text": page_content.full_text[
                    : len(page_content.full_text) // TRIM_CONSTANT
                ],
                "page_content_images": page_content.images,
            },
            output_is_list=False,
        ),
    )

    response = URLResponseModel(
        urls=response_list,
        page_content=response_content,
    )

    logger.info(f"LLM Response: {response}")
    return response
