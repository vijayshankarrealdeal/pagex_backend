import time
import concurrent.futures
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from engine.executor.youtube_metadata import fetch_multiple_metadata

# Create a thread-local driver pool to reuse drivers per thread.
driver_pool = {}

def get_driver():
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

def extract_page_info(url):
    driver = get_driver()
    try:
        driver.get(url)
        #time.sleep(2)  # Wait for the page to load
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

def main():
    urls = [
        "https://www.youtube.com/watch?v=9k3Ky2nn6MY",
        "https://www.youtube.com/watch?v=-AuK92Jq4yQ",
        "https://www.youtube.com/watch?v=WM1XcYXix0Y",
        "https://www.reddit.com/r/Cooking/comments/lm5vlt/what_are_the_secrets_to_making_delicious_homemade/",
        "https://www.reddit.com/r/Cooking/comments/lm5vlt/what_are_the_secrets_to_making_delicious_homemade/gntez09/",
        "https://www.reddit.com/r/Cooking/comments/lm5vlt/what_are_the_secrets_to_making_delicious_homemade/gnte1zy/",
        "https://www.simplyrecipes.com/recipes/homemade_pizza/",
        "https://www.indianhealthyrecipes.com/pizza-recipe-make-pizza/",
        "https://www.tasty.co/recipe/pizza-dough",
        "https://www.instructables.com/How-to-Make-The-Best-Homemade-Pizza/",
        "https://www.bbcgoodfood.com/recipes/pizza-margherita-4-easy-steps",
        "https://www.quora.com/How-do-I-make-pizza-at-home-like-Zomato",
        "https://www.quora.com/How-do-I-make-a-homemade-pizza-What-is-the-process-ingredients-and-specifics-such-as-temperature",
        "https://www.loveandlemons.com/homemade-pizza/",
        "https://www.sallysbakingaddiction.com/homemade-pizza-crust-recipe/",
        "https://www.patioandpizza.com/blogs/pizza-life/ingredients-in-pizza"
    ]

    # Filter out YouTube watch URLs.
    filtered_urls = [i for i in urls if "https://www.youtube.com/watch?v=" not in i]
    youtube_urls = [i for i in urls if "https://www.youtube.com/watch?v=" in i]
    start_time = time.time()
    res = fetch_multiple_metadata(youtube_urls) 
    result_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(extract_page_info, url): url for url in filtered_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            result = future.result()
            result_list.append(result)
    # Quit all drivers once done
    for drv in driver_pool.values():
        drv.quit()

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    # print("Results:")
    # for result in result_list:
    #     print(result)
    # print("YouTube Metadata:")
    # for metadata in res:
    #     print(metadata)
if __name__ == "__main__":
    main()
