import json
import random
import re
import asyncio

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import time
from datetime import datetime
from cloakbrowser import launch
import pandas as pd

from process_costco_html import extract_costco_products
from process_walmart_html import extract_walmart_products

def compose_walmart_url(product_name):
    base_url = "https://www.walmart.com/search?q="
    encoded_query = product_name.replace(" ", "+")
    return f"{base_url}{encoded_query}"

def compose_costco_url(product_name):
    base_url = "https://sameday.costco.com/store/costco/s?k="
    encoded_query = product_name.replace(" ", "+")
    return f"{base_url}{encoded_query}"

def get_html(site_url, product_name):
    # Clear any asyncio event loop that may have leaked into this thread.
    # This prevents "Sync API inside the asyncio loop" errors.
    try:
        asyncio.set_event_loop(None)
    except Exception:
        pass  # ignore if already cleared

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

def fetch_and_extract(domain, url, product):
    """Fetch HTML and extract products, returning a DataFrame."""
    html = get_html(url, product)
    if domain == "costco":
        return extract_costco_products(html)
    elif domain == "walmart":
        return extract_walmart_products(html)
    else:
        raise ValueError(f"Unknown domain: {domain}")

def main():
    products_to_scrape = ['diapers', 'mayonaise', 'ground beef']
    dfs_list = []

    output_dir = Path("~/documents/costco/python1/output").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    with (
        ThreadPoolExecutor(max_workers=1) as costco_executor,
        ThreadPoolExecutor(max_workers=1) as walmart_executor,
    ):
        futures = []
        for product in products_to_scrape:
            costco_url = compose_costco_url(product)
            walmart_url = compose_walmart_url(product)
            futures.append(costco_executor.submit(fetch_and_extract, "costco", costco_url, product))
            futures.append(walmart_executor.submit(fetch_and_extract, "walmart", walmart_url, product))

        for future in as_completed(futures):
            try:
                df = future.result()
                if df is not None and not df.empty:
                    dfs_list.append(df)
            except Exception as e:
                print(f"A scrape task failed: {e}")
    
    if not dfs_list:
        print("No data collected. Exiting without saving.")
        return

    products_df = pd.concat(dfs_list, ignore_index=True)
    products_df = products_df.convert_dtypes()

    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"products_{today_str}.parquet"
    filepath = output_dir / filename

    products_df.to_parquet(filepath, index=False, engine='pyarrow')
    print(f"Saved {len(products_df)} products to {filepath}")

if __name__ == "__main__":
    main()