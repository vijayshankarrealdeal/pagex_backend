from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from engine.models.url_model import BasePayload, URLResponseModel
from prefect import task, get_run_logger
from dotenv import load_dotenv
load_dotenv()


PROMPT = """
You are a powerful llm, who is creative and intelligent.
when extracting the url remove all google polices, support and login urls, and irrelevant urls which dono't have any content to user query,
if present include social media urls (instagram, X(Twitter), Reddit, Facebook), Music Platform(Spotify, Apple Music, Jio Saavan) and youtube urls.
given a list of urls : {url_list}
and a user query : {user_query}
Extract the urls and their titles from the list of urls, extract as much as relevance url you can.
"""

@task(name="LLM Runs", retries=3, retry_delay_seconds=5, log_prints=True)
async def url_link_parser(user_query, url_list: List[BasePayload]):
    logger = get_run_logger()
    llm = AzureChatOpenAI(
        api_version="2024-08-01-preview",
        deployment_name="gpt-4o-0806",
        temperature=0.0,
        streaming=True,
        client=None,  # Ensure this is correctly set or omitted if not needed
    ).with_structured_output(URLResponseModel)
    prompt = PromptTemplate(
            template=PROMPT,
            input_variables=["user_query", "url_list"],
        )
    chain = prompt | llm
    response = await chain.ainvoke({"user_query": user_query, "url_list": [i.url for i in url_list]})
    logger.info(f"LLM Response: {response}")
    return response