from prefect import flow, get_run_logger
from engine.executor.search_executor import SearchExecutor
from engine.executor.extract_url_executor import extract_external_links_info
from engine.executor.youtube_metadata_executor import fetch_youtube_multiple_metadata
from engine.models.search_helper_models import URLResponseModel
from engine.parsers.ranker import llm_ranker
from engine.parsers.summay_parser import webpage_text_parsing_using_llm
from engine.parsers.url_parsers import url_link_parser
import asyncio

@flow(name="search_and_extract")
async def run_query(query):
    search_exe = SearchExecutor()
    urls_with_text, page_content = search_exe.extract_search_information(query)
    for i in page_content.images:
        if len(i.src) > 1200:
            page_content.images.remove(i)
    if len(page_content.full_text) > 120000:
        page_content.full_text = page_content.full_text[:128000]

    url_link_parser_response =  await url_link_parser(query, urls_with_text, page_content)
    # good 
    external_urls = [i.url for i in url_link_parser_response.urls if "youtube" not in i.url]
    youtube_urls = [i.url for i in url_link_parser_response.urls if "youtube" in i.url]    
    external_urls_payload, youtube_urls_payload = await asyncio.gather(
        extract_external_links_info(external_urls),
        asyncio.to_thread(fetch_youtube_multiple_metadata, youtube_urls)
    )
    youtube_urls_payload = [i for i in youtube_urls_payload if i.summary is not None]
    payload = external_urls_payload + youtube_urls_payload


    payload = await webpage_text_parsing_using_llm(payload)
    ranked_payload = await llm_ranker(query, payload)
    return URLResponseModel(urls = ranked_payload, page_content=url_link_parser_response.page_content)
