import asyncio
from typing import List

from engine.llm.app_llm import LLMResponse
from engine.llm.app_prompt import Prompt
from engine.models.search_helper_models import (
    BasePayload,
    PageContent,
    URLResponseModel,
)
from prefect import task, get_run_logger
from engine.utils import TRIM_CONSTANT


@task(name="LLM Runs", log_prints=True)
async def url_link_parser(
    user_query, url_list: List[BasePayload], page_content: PageContent
) -> URLResponseModel:
    logger = get_run_logger()

    # Wait for both tasks to complete concurrently
    response_list, response_content = await asyncio.gather(
        LLMResponse.open_ai(
            response_model=BasePayload,
            prompt=Prompt.URL_EXTRACTOR_PROMPT,
            input_variables_payload={
                "url_list": url_list,
                "user_query": user_query,
            },
            output_is_list=True,
        ),
        LLMResponse.open_ai(
            prompt=Prompt.QUERY_SUMMERY_AND_IMAGE_PROMPT,
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
        page_content=PageContent(
            full_text=response_content, images=page_content.images
        ),
    )

    logger.info(f"LLM Response: {response}")
    return response
