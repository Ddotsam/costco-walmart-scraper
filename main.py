import json
import random
import re
import concurrent.futures

from pathlib import Path
from time import time
import pandas as pd
from cloakbrowser import launch

from process_costco_html import extract_costco_products
from process_walmart_html import extract_walmart_products

def get_html(site_url, product_name):
    # Launch CloakBrowser with strict stealth rules
    # headless=False is safer for heavy bot walls, humanize=True mimics real mouse/scroll paths
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()
    
    try:
        page.goto(site_url, wait_until="load")
        
        if "walmart" in site_url:
            company = 'Walmart'
            wait_selector = '[data-item-id]'
        elif "costco" in site_url:
            company = 'Costco'
            try:            
                guest_link = page.get_by_role("button", name=re.compile(r"guest", re.IGNORECASE))
                guest_link.wait_for(state="visible", timeout=5000)
                print("Found 'Continue as guest' link. Clicking it...")
                guest_link.click()
                time.sleep(random.uniform(2, 4))
            except Exception:
                print("No interstitial ad appeared. Proceeding to search...")
            wait_selector = '#productList'
        else:
            wait_selector = 'body'
            
        try:
            page.wait_for_selector(wait_selector, timeout=15000)
        except Exception as e:
            print(f"Timed out waiting for products. The page layout might be different, or a bot wall appeared. Error: {e}")
        
        html_content = page.content()

        output_folder = Path("raw_html")
        output_folder.mkdir(parents=True, exist_ok=True)
        file_path = output_folder / f"{company}_{product_name}.html"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)

    except Exception as e:
        print(f"Error fetching {product_name} HTML for {locals().get('company', 'Unknown')}: {e}")
        html_content = None

    return html_content

def compose_walmart_url(product_name):
    base_url = "https://www.walmart.com/search?q="
    encoded_query = product_name.replace(" ", "+")
    return f"{base_url}{encoded_query}"

def compose_costco_url(product_name):
    base_url = "https://sameday.costco.com/store/costco/s?k="
    encoded_query = product_name.replace(" ", "+")
    return f"{base_url}{encoded_query}"

def main():
    # products_to_scrape = ['honey', 'eggs', 'whole milk']
    products_to_scrape = ['lactose free milk']
    for product in products_to_scrape:
        walmart_url = compose_walmart_url(product)
        costco_url = compose_costco_url(product)


        costco_html = get_html(costco_url, product)
        df = extract_costco_products(costco_html)

if __name__ == "__main__":
    main()