# Scrape the page.
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import threading
from prefect import task

# Create a thread-local driver pool to reuse drivers per thread.
driver_pool = {}

@task
def run_search(search_term):
    # create Chromeoptions instance 
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
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    driver.get(f"https://www.google.com/search?q={search_term}")
    time.sleep(3)  # wait for the page to load
    return driver.page_source

@task
def extract_url_and_text(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        link = a["href"]
        text = a.get_text(strip=True)
        links.append({"url": link, "text": text})
    return links


def get_driver():
    """ Initialize a headless Chrome WebDriver for Selenium """
    thread_id = threading.get_ident()
    if thread_id not in driver_pool:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        # Disable images to speed up loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        driver_pool[thread_id] = webdriver.Chrome(options=chrome_options)
    return driver_pool[thread_id]

def extract_page_info(url: str):
    """ Extract page info using Selenium WebDriver (not async, so we use threads) """
    driver = get_driver()
    try:
        driver.get(url)
        # Attempt to auto-click common cookie/consent buttons
        try:
            driver.execute_script(
                "document.querySelectorAll('[aria-label=\"Accept cookies\"],"
                "button.cookie-accept, button#accept-cookies').forEach(el => el.click());"
            )
        except Exception:
            pass  # Ignore if not found
        title = driver.title
        # Grab first 200 characters of page source for a snippet
        page_snippet = driver.page_source
    except Exception as e:
        title = f"Error: {e}"
        page_snippet = ""
    return {"url": url, "title": title, "snippet": page_snippet}

@task
@task
async def extract_external_links(urls: list):
    """Run page extraction asynchronously using threads"""
    results = []
    loop = asyncio.get_event_loop()

    # Use ThreadPoolExecutor with number of workers equal to CPU cores
    with ThreadPoolExecutor(max_workers=8) as executor:
        tasks = [loop.run_in_executor(executor, extract_page_info, url) for url in urls]
        results = await asyncio.gather(*tasks)

    # Close all drivers
    for driver in driver_pool.values():
        try:
            driver.quit()
        except Exception:
            pass
    driver_pool.clear()

    return results
