from prefect import flow, get_run_logger
from engine.executor.urls_extractors import extract_external_links, run_search
from engine.executor.youtube_metadata import fetch_youtube_multiple_metadata
from engine.models.url_model import URLResponseModel
from engine.parsers.ranker import llm_ranker
from engine.parsers.summay_parser import webpage_text_parsing_using_llm
from engine.parsers.url_parsers import url_link_parser
import asyncio
from engine.utils import extract_from_webpage

@flow(name="search_and_extract")
async def run_query(query):
    logger = get_run_logger()
    html = run_search(query)
    links_with_text, page_content = extract_from_webpage(html)
    # Call LLM to extract the urls and title
    url_link_parser_response =  await url_link_parser(query, links_with_text, page_content)
    # extract the content from the urls

    external_urls = [i.url for i in url_link_parser_response.urls if "youtube" not in i.url]
    youtube_urls = [i.url for i in url_link_parser_response.urls if "youtube" in i.url]
    logger.info(f"External urls: {external_urls}, Youtube urls: {youtube_urls}")
    external_urls_payload, youtube_urls_payload = await asyncio.gather(
        extract_external_links(external_urls),
        asyncio.to_thread(fetch_youtube_multiple_metadata, youtube_urls)
    )
    youtube_urls_payload = [i for i in youtube_urls_payload if i.summary is not None]
    payload = external_urls_payload + youtube_urls_payload
    logger.info(f"Payload: {payload}")
    payload = await webpage_text_parsing_using_llm(payload)
    ranked_payload = await llm_ranker(query, payload)
    return URLResponseModel(urls =  ranked_payload, page_content=url_link_parser_response.page_content)
