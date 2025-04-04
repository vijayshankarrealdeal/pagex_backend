"""
This module is responsible for executing search queries using Selenium WebDriver.
It handles the initialization of the WebDriver and the execution of search queries.
"""

from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
import time, re
from selenium import webdriver
from prefect import task, get_run_logger
from engine.models.search_helper_models import BasePayload, PageContent
from engine.utils import extract_image_data, extract_texts, extract_url_and_text


class SearchExecutor:

    def __init__(self):
        self.raw_html = None
        self.image_html = None

    @task(log_prints=True)
    def extract_search_information(
        self, query: str
    ) -> tuple[list[BasePayload], PageContent]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_search = executor.submit(self.run_search, query)
            future_image = executor.submit(self.run_image_search, query)
            future_search.result()
            future_image.result()

        urls_with_text, page_text = self.extract_from_webpage(self.raw_html)
        image_result = extract_image_data(self.image_html)
        self.image_html = None  # Clear the image HTML after extraction
        self.raw_html = None  # Clear the raw HTML after extraction
        return urls_with_text, PageContent(full_text=page_text, images=image_result)

    @staticmethod
    def get_driver():
        options = webdriver.ChromeOptions()
        # adding argument to disable the AutomationControlled flag
        options.add_argument("--disable-blink-features=AutomationControlled")

        # exclude the collection of enable-automation switches
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # turn-off userAutomationExtension
        options.add_experimental_option("useAutomationExtension", False)

        # setting the driver path and requesting a page
        driver = webdriver.Chrome(options=options)

        # changing the property of the navigator value for webdriver to undefined
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return driver

    @task(log_prints=True)
    def run_search(self, search_term) -> None:
        # create Chromeoptions instance
        logger = get_run_logger()
        driver = self.get_driver()
        driver.get(f"https://www.google.com/search?q={search_term}")
        logger.info(f"Searching for: {search_term} {driver.page_source}")
        time.sleep(2)  # wait for the page to load
        self.raw_html = driver.page_source
        driver.quit()

    @staticmethod
    def clean_text(text: str) -> str:
        # Remove unwanted special characters (keep basic punctuation)
        text = re.sub(r"[^a-zA-Z0-9\s.,;:'\"!?()\-]", "", text)
        text = re.sub(r"\n{2,}", "\n", text)  # Collapse newlines
        text = re.sub(r"[ \t]{2,}", " ", text)  # Collapse spaces/tabs
        text = re.sub(r"\s{2,}", " ", text)  # Extra safety
        return text.strip()

    @task(log_prints=True)
    def run_image_search(self, search_term) -> None:
        logger = get_run_logger()
        url = f"https://in.images.search.yahoo.com/search/images?p={search_term}"
        driver = self.get_driver()
        driver.get(url)
        time.sleep(2)  # Let the initial content load
        last_height = driver.execute_script("return document.body.scrollHeight")
        logger.info(f"Starting scroll for: {search_term}")
        for _ in range(2):  # Adjust number of scrolls if needed
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # Give time to load new content
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break  # No more content to scroll
            last_height = new_height

        self.image_html = driver.page_source
        logger.info(f"Finished scrolling. Length of HTML: {len(self.image_html)}")
        driver.quit()

    def extract_from_webpage(self, html: str) -> tuple[list[BasePayload], str]:
        """
        Extracts URLs and text from the given HTML content.
        """
        # Extract URLs and text
        urls_with_text = extract_url_and_text(html)

        # Extract images and full text
        page_text = extract_texts(html)

        # Clean the text in the page content
        page_text = self.clean_text(page_text)
        return urls_with_text, page_text
