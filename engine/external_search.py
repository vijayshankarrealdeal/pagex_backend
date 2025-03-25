import asyncio
import aiohttp
from duckduckgo_search import DDGS
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from engine.models.classifier_model import ClassifierOutput

# Global semaphore and shared LLM clients
semaphore = asyncio.Semaphore(5)  # Adjust concurrency level
shared_summary_llm = AzureChatOpenAI(
    api_version="2024-08-01-preview",
    deployment_name="gpt-4o-0806",
    temperature=0.0,
    streaming=False,
    client=None,
)

shared_classify_llm = AzureChatOpenAI(
    api_version="2024-08-01-preview",
    deployment_name="gpt-4o-0806",
    temperature=0.0,
    streaming=False,
    client=None,
).with_structured_output(ClassifierOutput)

# ----------- Summary Function -----------
async def summary_external(text: str):
    prompt = PromptTemplate(
        template="""
        Given a paragraph of text, provide a concise and detailed overview that covers the main sentences and key points:
        {text}
        """,
        input_variables=["text"],
    )
    rendered_prompt = prompt.format(text=text)
    return await shared_summary_llm.ainvoke(rendered_prompt)

# ----------- Quick View Function (Summarization of URLs) -----------
async def quick_view_link(session: aiohttp.ClientSession, url: str):
    prefix = "https://r.jina.ai/"
    try:
        async with semaphore:
            async with session.get(f"{prefix}{url}", timeout=aiohttp.ClientTimeout(total=10)) as response:
                text = await response.text()
        return await summary_external(text)
    except Exception as e:
        return f"Error fetching summary: {str(e)}"

# ----------- Search and Process External URLs -----------
async def search_external(query: str):
    results = DDGS().text(query, max_results=20)
    
    # Filter and deduplicate URLs
    seen = set()
    urls = []
    for v in results:
        href = v.get("href")
        if href and href not in seen:
            urls.append(href)
            seen.add(href)
    async with aiohttp.ClientSession() as session:
        tasks = [quick_view_link(session, url) for url in urls]
        quick_views = await asyncio.gather(*tasks, return_exceptions=True)

    for i, v in enumerate(results):
        v["result_rank"] = len(results) - i
        if i < len(quick_views):
            summary = quick_views[i]
            v["quick_view"] = summary if not isinstance(summary, Exception) else "Error generating summary"
        else:
            v["quick_view"] = "Summary not available"

    return results

# ----------- Categorization Function -----------
async def get_categories(query: str) -> ClassifierOutput:
    categories  = [
    # People
    "Person", "Fictional Character", "Title", "Actor", "Actress", "Musician",
    "Athlete", "Politician", "Author",
    "Artist", "Influencer", "Entrepreneur", "Scientist", "Historical Figure",

    # Organizations
    "Corporation", "Non-profit", "Government Agency", "Educational Institution",

    # Locations / Places
    "Continent", "Country", "State/Province", "City", "Landmark", "Address",

    # Products
    "Technology Product", "Book", "Movie", "TV Show", "Consumer Product", "Vehicle",

    # Events
    "Historical Event", "Sports Event", "Conference", "Festival", "Holiday",

    # Dates / Time
    "Date", "Year", "Time", "Season",

    # Monetary / Financial
    "Currency", "Cryptocurrency", "Monetary Amount",

    # Quantities / Measurements
    "Distance", "Weight", "Volume", "Percentage", "Temperature",

    # Works of Art / IP
    "Painting", "Song", "Patent", "Trademark", "Sculpture",

    # Language / Nationality / Religion
    "Language", "Nationality", "Religion",

    # Legal
    "Law", "Treaty", "Court Case",

    # Science / Medicine
    "Disease", "Drug", "Scientific Term", "Invention", "Technology",

    # Natural Entities
    "Animal", "Plant", "Celestial Body", "Natural Phenomenon",

    # Internet / Tech-Specific
    "Website", "App", "Domain", "Protocol", "Hashtag", "Social Media Handle",

    # Miscellaneous
    "Award", "ID Number", "License Plate", "Vehicle Model", "Tool", "Software"
]


    prompt = PromptTemplate(
        template="""
        Given a list of categories:
        {categories}

        Classify the following query under the most relevant categories, and assign a probability to each:
        {text}
        """,
        input_variables=["text", "categories"],
    )
    rendered_prompt = prompt.format(text=query, categories=", ".join(categories))
    return await shared_classify_llm.ainvoke(rendered_prompt)
