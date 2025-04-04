# Scrape the page.
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
from prefect import task
from engine.models.search_helper_models import BasePayload
from engine.utils import extract_all_content

# Create a thread-local driver pool to reuse drivers per thread.
driver_pool = {}

def _get_driver():
    """Initialize a headless Chrome WebDriver for Selenium."""
    thread_id = threading.get_ident()
    if thread_id not in driver_pool:
        chrome_options = Options()
        # Use the new headless mode (Chrome 109+) which can be faster/stabler
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # Load only initial HTML without waiting for full resources
        chrome_options.page_load_strategy = "eager"

        # Disable images to speed up loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        driver_pool[thread_id] = webdriver.Chrome(options=chrome_options)
        # Set load timeouts (adjust if needed)
        driver_pool[thread_id].set_page_load_timeout(10)
        driver_pool[thread_id].set_script_timeout(10)

    return driver_pool[thread_id]


def extract_page_info(url: str):
    """Extract page info using Selenium WebDriver (not async, so we use threads)."""
    driver = _get_driver()
    summary = ""
    try:
        # Hide the 'webdriver' property (sometimes websites block automation tools)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        driver.get(url)
        time.sleep(2)  # Wait for the page to load
        # Attempt to auto-click common cookie/consent buttons
        try:
            driver.execute_script(
                """
                document.querySelectorAll('[aria-label="Accept cookies"], 
                button.cookie-accept, button#accept-cookies')
                .forEach(el => el.click());
            """
            )
        except Exception:
            pass  # Ignore if not found

        title = driver.title
        # Grab first 200 characters of page source for a snippet
        page_snippet = driver.page_source
        _, summary, _ = extract_all_content(page_snippet)
    except Exception as e:
        title = f"Error: {e}"
    return BasePayload(url=url, title=title, summary=summary, is_youtube=False)


@task
async def extract_external_links_info(urls: list):
    """Run page extraction asynchronously using threads."""
    results = []
    loop = asyncio.get_event_loop()

    # Use a ThreadPoolExecutor with enough workers (8 or more, if your machine can handle it).
    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = [loop.run_in_executor(executor, extract_page_info, url) for url in urls]
        results = await asyncio.gather(*tasks)

    # Close all drivers after completing.
    for driver in driver_pool.values():
        try:
            driver.quit()
        except Exception:
            pass
    driver_pool.clear()

    return results
