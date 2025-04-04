class Prompt:

    SUMMARY_PROMPT = """
You are a helpful and concise assistant. Your job is to analyze and summarize the following web page content.

Instructions:
1. Summarize the webpage content in **10 to 18 clear and informative lines that covers all major information, if metric like dates, numbers, etc. include those also.**.
2. Rephrase the given title to make it more engaging, but **keep the original meaning**.
3. Create a short 2-3 line description based on the webpage content.
4. Avoid speculation or sensitive content. Stay neutral and factual.
5. If content is missing or incomplete, respond appropriately with a summary from your knowlege.
6. Your output should be a formatted and represntable markdown.
Content to summarize:
{html_text}
"""

    URL_EXTRACTOR_PROMPT = """You are an intelligent and creative language model.

Your task is to extract the most relevant URLs as much you can from `URL List` and create their titles based on the user's query.

**Instructions:**
- Remove any Google policy, login, support, or irrelevant URLs.
- Include as much URLs only if they relate to the user's query.
- Prefer social media (Instagram, Twitter/X, Reddit, Facebook), music platforms (Spotify, Apple Music, JioSaavn), News, Myntra, Amazon, Flipkart,  Wikipedia or YouTube links if available.

**Input:**
- URL List: {url_list}
- User Query: {user_query}

Return a list of the most relevant URLs and their titles.
"""

    QUERY_SUMMERY_AND_IMAGE_PROMPT = """You are a helpful and informative writing assistant.

Your task is to convert the given web page text and image descriptions into a clean, comprehesive long engaging article based on the user's query, using Markdown formatting.

**Instructions:**
1. Summarize the most important facts — names, dates, achievements, numbers.
2. Write a clear, easy-to-read article in Markdown format:
   - Use headings, bullet points, and short paragraphs.
   - Keep the tone informative yet engaging.
   - Use Images list to add images in the article, but don't all images, only few which are relevant to the content.
3. Make the article informative and engaging.
4. If the content is missing or incomplete, respond appropriately with a summary from your knowledge.

---

**Input:**
- User Query: {user_query}
- Full Page Text: {page_content_full_text}
- Image URLs with Descriptions: {page_content_images}
"""

    RANK_RESULT_PROMPT = """
You are an advanced LLM with deep knowledge of real-world ranking algorithms (e.g., TF-IDF, semantic similarity, embedding-based relevance). Your task is to **assign a rank from 0 to 10** for each item in a list, based on its relevance to a given user query.

**Guidelines**:
1. A rank of **0** indicates completely irrelevant or off-topic content.
2. A rank of **10** indicates highly relevant, comprehensive coverage of the user query.
3. Consider:
   - **Semantic overlap** between the item's title/summary and the user query.
   - **Depth and detail** of the item's coverage regarding the query's key points.
   - **Real-world utility**: how well this item would satisfy a user searching for that query.
4. Provide a **brief explanation** (1-2 lines) for each item's score, referencing the main factors that influenced your ranking.

Below is the list of information (each item has a title, summary, and/or numbers):

{payload}

Below is the user query:

{query}

Please output a ranking (0-10) for each item, along with a concise reason for that rank.

"""
