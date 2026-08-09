import random
import re
import asyncio

from pathlib import Path
from datetime import datetime
import pandas as pd
from cloakbrowser import launch_async as launch

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

async def get_html_async(browser, site_url, product_name):
    company = "Unknown" 

    page = await browser.new_page()
    try:
        await page.goto(site_url, wait_until="load")

        if "walmart" in site_url:
            company = 'Walmart'
            primary = page.locator('div[data-testid="item-stack"]')
            fallback = page.locator('[data-item-id]')
        elif "costco" in site_url:
            company = 'Costco'
            try:
                guest_link = page.get_by_role("button", name=re.compile(r"guest", re.IGNORECASE))
                await guest_link.wait_for(state="visible", timeout=5000)
                print("Found 'Continue as guest' link. Clicking it...")
                await guest_link.click()
                await asyncio.sleep(random.uniform(2, 4))
            except Exception:
                print("No interstitial ad appeared. Proceeding to search...")

            primary = page.locator('div[role="region"][aria-label*="results for" i]')
            fallback = page.locator('#productList')
        else:
            primary = page.locator('body')
            fallback = page.locator('body')

        try:
            await primary.or_(fallback).wait_for(state="visible", timeout=30000)
            if "costco" in site_url:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"Timed out waiting for products: {e}")

        html_content = await page.content()

        output_folder = Path("raw_html")
        output_folder.mkdir(parents=True, exist_ok=True)
        file_path = output_folder / f"{company}_{product_name}.html"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_content

    except Exception as e:
        print(f"Error fetching {product_name} HTML for {company}: {e}")
        return None
    finally:
        await page.close()

async def fetch_and_extract_async(domain, browser, url, product):
    html = await get_html_async(browser, url, product)
    if not html:
        return pd.DataFrame()
    if domain == "costco":
        return extract_costco_products(html)
    elif domain == "walmart":
        return extract_walmart_products(html)

async def async_main(products_to_scrape):
    dfs_list = []
    output_dir = Path("~/documents/costco/python1/output").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    browser = await launch(headless=False, humanize=True)

    try:
        for product in products_to_scrape:
            costco_url = compose_costco_url(product)
            walmart_url = compose_walmart_url(product)

            results = await asyncio.gather(
                fetch_and_extract_async("costco", browser, costco_url, product),
                fetch_and_extract_async("walmart", browser, walmart_url, product),
                return_exceptions=True   # so one failure doesn't cancel the other
            )

            for df in results:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    dfs_list.append(df)
                elif isinstance(df, Exception):
                    print(f"A scrape task failed: {df}")

    finally:
        await browser.close()

    if not dfs_list:
        print("No data collected.")
        return

    products_df = pd.concat(dfs_list, ignore_index=True)
    products_df = products_df.convert_dtypes()
    today_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = output_dir / f"products_{today_str}.parquet"
    
    products_df.to_parquet(filepath, index=False, engine='pyarrow')
    print(f"Saved {len(products_df)} products to {filepath}")

def main():
    products_to_scrape = ['chocolate', 'waffle mix', 'chicken thighs']
    asyncio.run(async_main(products_to_scrape))

if __name__ == "__main__":
    main()