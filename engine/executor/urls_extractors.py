# Scrape the page.
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup


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
    time.sleep(2)  # wait for the page to load
    return driver.page_source


def extract_url_and_text(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        link = a["href"]
        text = a.get_text(strip=True)
        links.append({"url": link, "text": text})
    return links

def get_urls_and_title(links: list):
    ## call llm parser to get the urls and title
    pass
    
