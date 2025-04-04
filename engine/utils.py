from typing import List
from lxml import html as lxml_html
from prefect import get_run_logger, task
from lxml.html.clean import Cleaner
from engine.models.search_helper_models import BasePayload, ImagePayload, PageContent
import re
from bs4 import BeautifulSoup


TRIM_CONSTANT = 1


def clean_html(html_text: str) -> str:
    """Clean and extract text from HTML."""
    soup = BeautifulSoup(html_text, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()  # Removes these tags from the tree
    text = soup.get_text()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"<!--.*?-->", "", text)
    return text


def sanitize_text(text: str) -> str:
    """Sanitize the extracted text by removing unwanted characters."""
    # Basic example: strip HTML, remove emojis, control chars
    text = re.sub(r"<.*?>", "", text)  # Remove HTML tags
    text = re.sub(r"[^\x00-\x7F]+", "", text)  # Remove non-ASCII (emojis etc.)
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)  # Remove control chars
    return text


def extract_all_content(html: str):
    """Extract text, URLs, and images from HTML content, clean the text, and return a structured object."""
    tree = lxml_html.fromstring(html)
    # Extract URLs (links)
    anchors = tree.xpath("//a[@href]")
    url_results = []
    for a in anchors:
        link = a.get("href")
        if link.startswith("https"):
            text = a.text_content().strip()
            url_results.append(BasePayload(url=link, title=text))

    # Clean the HTML content
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
        frames=True,
    )

    cleaned_html = cleaner.clean_html(html)
    tree = lxml_html.fromstring(cleaned_html)

    # Optionally remove non-content tags like nav, footer, aside
    for tag in tree.xpath("//nav | //footer | //aside"):
        tag.drop_tree()

    # Extract meaningful text (paragraphs, headers, list items)
    parts = tree.xpath("//p | //h1 | //h2 | //h3 | //li | //span")
    text_chunks = [
        el.text_content().strip() for el in parts if el.text_content().strip()
    ]
    full_text = "\n".join(text_chunks)
    full_text = clean_html(full_text)  # Clean extracted text
    full_text = sanitize_text(full_text)  # Optionally sanitize the text
    return  full_text, url_results

@task
def extract_url_and_text(html: str) -> List[BasePayload]:
    logger = get_run_logger()
    _, url_results = extract_all_content(html)
    logger.info(f"Extracted URLs: {url_results}...")
    return url_results


def extract_texts(html: str) -> str:
    """Extract text and images from HTML content."""
    logger = get_run_logger()
    full_text, _ = extract_all_content(html)
    logger.info(f"Extracted text: {full_text}...")
    return full_text


def extract_image_data(html: str) -> List[ImagePayload]:
    soup = BeautifulSoup(html, "html.parser")
    image_data = []

    for img in soup.find_all("img"):
        src = img.get("src")
        width = img.get("width")
        height = img.get("height")

        # Fallback to style parsing if width/height not directly present
        if (not width or not height) and img.has_attr("style"):
            style = img["style"]
            width_match = re.search(r"width\s*:\s*(\d+)", style)
            height_match = re.search(r"height\s*:\s*(\d+)", style)
            if not width and width_match:
                width = width_match.group(1)
            if not height and height_match:
                height = height_match.group(1)

        # Convert height to int if possible
        try:
            height = int(float(height)) if height else None
        except ValueError:
            height = None

        if src:
            image_data.append({"src": src, "width": width, "height": height})

    return [ImagePayload(**i) for i in image_data if i and i['height']> 200]
