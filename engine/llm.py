from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import AzureChatOpenAI
from engine.external_search import get_categories, search_external
from engine.models.search_model import SearchOut
from engine.prompt import PROMPT
from dotenv import load_dotenv
import asyncio
from langchain.prompts import PromptTemplate


load_dotenv()
checkpointer = MemorySaver()
llm = AzureChatOpenAI(
    api_version="2024-08-01-preview",
    deployment_name="gpt-4o-0806",
    temperature=0.0,
    streaming=True,
    client=None,  # Ensure this is correctly set or omitted if not needed
).with_structured_output(SearchOut)
prompt = PromptTemplate(
        template=PROMPT,
        input_variables=["query", "external_search"],
    )
# Combine the prompt and LLM into a chain
chain = prompt | llm

# Configuration dictionary
# config = {"configurable": {"thread_id": "thread-1"}}


async def get_results(query):
    print("Query:", query)

    # Kick off both tasks at the same time
    classification_task = asyncio.create_task(get_categories(query))
    external_search_task = asyncio.create_task(search_external(query))

    # Wait for both to finish concurrently
    classification, external_search = await asyncio.gather(
        classification_task,
        external_search_task,
    )

    print("Classify:", classification.model_dump())
    print("External search:", external_search)

    res = await chain.ainvoke({"query": query, "external_search": external_search})
    return res.model_dump()
