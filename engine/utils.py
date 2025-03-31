from lxml import html as lxml_html
from prefect import get_run_logger, task
from lxml.html.clean import Cleaner
from engine.models.url_model import BasePayload, ImagePayload, PageContent
import re
from bs4 import BeautifulSoup

TRIM_CONSTANT = 1

def clean_text(text: str) -> str:
    # Remove unwanted special characters (keep basic punctuation)
    text = re.sub(r"[^a-zA-Z0-9\s.,;:'\"!?()\-]", "", text)
    text = re.sub(r"\n{2,}", "\n", text)        # Collapse newlines
    text = re.sub(r"[ \t]{2,}", " ", text)      # Collapse spaces/tabs
    text = re.sub(r"\s{2,}", " ", text)         # Extra safety
    return text.strip()

def clean_html(html_text: str) -> str:
    soup = BeautifulSoup(html_text, 'html.parser')    
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()  # Removes these tags from the tree
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'<!--.*?-->', '', text)
    return text 

def sanitize_text(text: str) -> str:
    # Basic example: strip HTML, remove emojis, control chars
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII (emojis etc.)
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)  # Remove control chars
    return text

@task
def extract_text_and_images(html: str) -> PageContent:

    logger = get_run_logger()
    tree = lxml_html.fromstring(html)
    images = tree.xpath("//img[@src]")
    image_results = []
    for img in images:
        src = img.get("src")
        alt = img.get("alt") or ""
        image_results.append(ImagePayload(src=src, alt=alt.strip()))


    cleaner = Cleaner(
        scripts=True,
        javascript=True,
        style=True,
        links=False,
        meta=False,
        page_structure=False,
        safe_attrs_only=False,
        remove_unknown_tags=False,
        embedded=True,
        forms=True,
        frames=True
    )

    # Clean HTML content
    cleaned_html = cleaner.clean_html(html)
    tree = lxml_html.fromstring(cleaned_html)

    # Optionally remove nav, footer, aside (visually non-main content)
    for tag in tree.xpath('//nav | //footer | //aside'):
        tag.drop_tree()

    # Extract meaningful text elements (paragraphs, headers, list items)
    parts = tree.xpath("//p | //h1 | //h2 | //h3 | //li | //span")
    text_chunks = [el.text_content().strip() for el in parts if el.text_content().strip()]
    full_text = "\n".join(text_chunks)
    full_text = clean_html(full_text) 
    logger.info(f"Extracted text: {full_text}")
    return PageContent(
        images=image_results,
        full_text=full_text,
    )
    
@task
def extract_url_and_text(html: str) -> list[BasePayload]:
    logger = get_run_logger()
    tree = lxml_html.fromstring(html)
    anchors = tree.xpath("//a[@href]")
    results = []
    for a in anchors:
        link = a.get("href")
        if link.startswith("https"):
            text = a.text_content().strip()
            results.append(BasePayload(url=link, title=text))
    logger.info(f"Extracted URLs and text: {results}")
    return results

def extract_from_webpage(html: str) -> tuple[list[BasePayload], PageContent]:
    """
    Extracts URLs and text from the given HTML content.
    """
    # Extract URLs and text
    urls_with_text = extract_url_and_text(html)
    
    # Extract images and full text
    page_content = extract_text_and_images(html)
    
    # Clean the text in the page content
    page_content.full_text = clean_text(page_content.full_text)    
    return urls_with_text, page_content
