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

    # Extract images
    images = tree.xpath("//img[@src]")
    image_results = []
    for img in images:
        src = img.get("src")
        alt = img.get("alt") or ""
        image_results.append(ImagePayload(src=src, alt=alt.strip()))

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
    return image_results, full_text, url_results


# @task
# def extract_text(html: str) -> str:
#     logger = get_run_logger()
#     _, full_text, _ = extract_all_content(html)
#     logger.info(f"Extracted text: {full_text}...")
#     return full_text


# @task
# def extract_images(html: str) -> List[ImagePayload]:
#     logger = get_run_logger()
#     image_results, _, _ = extract_all_content(html)
#     logger.info(f"Extracted images: {image_results}...")
#     return image_results


@task
def extract_url_and_text(html: str) -> List[BasePayload]:
    logger = get_run_logger()
    _, _, url_results = extract_all_content(html)
    logger.info(f"Extracted URLs: {url_results}...")
    return url_results


def extract_text_and_images(html: str) -> PageContent:
    """Extract text and images from HTML content."""
    logger = get_run_logger()
    image_results, full_text, _ = extract_all_content(html)
    logger.info(f"Extracted text: {full_text}...")
    return PageContent(
        full_text=full_text,
        images=image_results,
    )
