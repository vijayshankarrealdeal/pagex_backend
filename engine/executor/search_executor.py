"""
This module is responsible for executing search queries using Selenium WebDriver.
It handles the initialization of the WebDriver and the execution of search queries.
"""

from selenium import webdriver
import time, re
from selenium import webdriver
from prefect import task, get_run_logger
from engine.models.url_model import BasePayload, PageContent
from engine.utils import extract_text_and_images, extract_url_and_text


class SearchExecutor:

    def __init__(self):
        self.raw_html = None

    def extract_search_information(
        self, query: str
    ) -> tuple[list[BasePayload], PageContent]:
        self.run_search(query)
        urls_with_text, page_content = self.extract_from_webpage(self.raw_html)
        return urls_with_text, page_content

    @task(log_prints=True)
    def run_search(self, search_term) -> None:
        # create Chromeoptions instance
        logger = get_run_logger()
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

    def extract_from_webpage(self, html: str) -> tuple[list[BasePayload], PageContent]:
        """
        Extracts URLs and text from the given HTML content.
        """
        # Extract URLs and text
        urls_with_text = extract_url_and_text(html)

        # Extract images and full text
        page_content = extract_text_and_images(html)

        # Clean the text in the page content
        page_content.full_text = self.clean_text(page_content.full_text)
        return urls_with_text, page_content
