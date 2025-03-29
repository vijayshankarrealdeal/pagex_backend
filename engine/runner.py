"""
Take user query run a search
Extract the urls and text from the search results
Run the LLM to extract the urls and text
Extract the content from the urls
"""

from prefect import flow
from engine.executor.urls_extractors import extract_external_links, extract_url_and_text, run_search
from engine.executor.youtube_metadata import fetch_youtube_multiple_metadata
from engine.parsers.ranker import llm_ranker
from engine.parsers.summay_parser import webpage_text_parsing_using_llm
from engine.parsers.url_parsers import url_link_parser
import asyncio
from engine.cache.llm_url_parser_cache import cached_llm_response_urls

@flow(name="search_and_extract")
async def run_query(query):
    html = run_search(query)
    links_with_text = extract_url_and_text(html)
    # Call LLM to extract the urls and title
    url_link_parser_response =  await url_link_parser(query, links_with_text)
    # extract the content from the urls

    external_urls = [i.url for i in url_link_parser_response.urls if "youtube" not in i.url]
    youtube_urls = [i.url for i in url_link_parser_response.urls if "youtube" in i.url]

    external_urls_payload, youtube_urls_payload = await asyncio.gather(
        extract_external_links(external_urls),
        asyncio.to_thread(fetch_youtube_multiple_metadata, youtube_urls)
    )
    payload = external_urls_payload + youtube_urls_payload
    payload = await webpage_text_parsing_using_llm(payload)
    ranked_payload = await llm_ranker(query, payload)
    return ranked_payload
