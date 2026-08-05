import time
import json
import re

from pathlib import Path
import pandas as pd
from cloakbrowser import launch
from bs4 import BeautifulSoup

def main():
    main_data = []
    products_to_scrape = ['honey', 'eggs', 'whole milk', ]

def scrape_ecommerce(site_url, flat_data):
    # Launch CloakBrowser with strict stealth rules
    # headless=False is safer for heavy bot walls, humanize=True mimics real mouse/scroll paths
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()
    
    try:
        print(f"Navigating to {site_url}...")
        # Change "networkidle" to "load" so it doesn't get stuck on background trackers
        page.goto(site_url, wait_until="load")
        
        print("Waiting for product elements to render...")
        
        # Dynamically choose the selector to wait for based on the website
        if "walmart" in site_url:
            wait_selector = '[data-item-id]'
        elif "costco" in site_url:
            wait_selector = '[data-item-card="true"]'
        else:
            wait_selector = 'body' # Fallback
            
        # Explicitly wait up to 15 seconds for a product card to actually show up
        try:
            page.wait_for_selector(wait_selector, timeout=15000)
        except Exception:
            print("Timed out waiting for products. The page layout might be different, or a bot wall appeared.")
        
        # Give image assets a brief moment to finish rendering
        time.sleep(2)
        
        # Capture the fully rendered HTML DOM
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        output_folder = Path("raw_html")
        output_folder.mkdir(parents=True, exist_ok=True)
        file_path = output_folder / f"walmart_{flat_data}.html"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        
        # --- WALMART PARSING LOGIC ---
        if "walmart" in site_url:
            # Loop through each product card using the data-item-id identifier
            for item in soup.select('[data-item-id]'):
                title_el = item.select_one('[data-automation-id="product-title"]')
                price_container = item.select_one('[data-automation-id="product-price"]')
                image_el = item.select_one('[data-testid="productTileImage"]')
                
                if title_el:
                    # 1. Extract and clean Title
                    title = title_el.get_text(strip=True)
                    
                    # 2. Extract and clean Price
                    price = "N/A"
                    if price_container:
                        clean_price_el = price_container.select_one('.ld_Ec')
                        if clean_price_el:
                            price = clean_price_el.get_text(strip=True).replace("current price", "").strip()
                        else:
                            price = price_container.get_text(strip=True)
                    
                    # 3. Extract Image Source URL
                    image_src = image_el['src'] if image_el and image_el.has_attr('src') else None
                    
                    flat_data.append({
                        "search_term": item,
                        "title": title,
                        "price": price,
                        "image": image_src
                    })

        elif 'costco' in site_url:
            extract_costco_products(html_content)
                    
        # --- COSTCO PARSING LOGIC ---
        elif "costco" in site_url:
            # 2. A more resilient way to find products. 
            # Costco almost always wraps products in a grid link or block with an 'a' tag to the product page.
            # Let's find all links that contain ".product." in the URL (which is standard for Costco items)
            product_links = soup.select('a[href*=".product."]')
            
            # We will use a set to keep track of URLs so we don't get duplicates
            seen_urls = set()
            
            for link in product_links:
                url = link.get('href')
                if url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                # In Costco's HTML, the <a> tag is usually inside a main product wrapper.
                # Let's walk UP the HTML tree to find the main container (usually a div wrapping the whole card)
                # We'll look for a parent div that contains the image and price.
                card = link.find_parent('div') 
                # Go up a few levels to ensure we have the whole card
                for _ in range(3):
                    if card and card.parent:
                        card = card.parent

                if not card:
                    continue
                    
                # --- TITLE ---
                # The title is usually the text of the main link, or inside an h2/h3 nearby
                title = link.get_text(strip=True)
                if not title:
                    # Fallback: look for header tags inside the card
                    header = card.find(['h2', 'h3'])
                    title = header.get_text(strip=True) if header else "Unknown Title"
                    
                # Ignore empty links that might just be structural
                if not title or title == "Unknown Title":
                    continue

                # --- PRICE ---
                # Prices in HTML usually contain a dollar sign. Let's find text containing '$'
                price = "N/A"
                price_el = card.find(string=lambda t: t and "$" in t)
                if price_el:
                    price = price_el.strip()
                    
                # --- IMAGE ---
                # Find the first image tag in this product card
                image_src = None
                img_el = card.find('img')
                if img_el:
                    # Costco sometimes uses 'src' and sometimes lazy-loads with 'data-src' or 'srcset'
                    image_src = img_el.get('src') or img_el.get('data-src')

                products.append({
                    "title": title,
                    "price": price,
                    "image": image_src
                })

        return products

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    
        
    finally:
        print("Taking a snapshot of the current page state...")
        page.screenshot(path="debug_screenshot.png")
        with open("debug_dom.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        # Always close the browser instance to free up local memory
        browser.close()

def extract_costco_products(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    
    # Locate all the list items containing products
    product_cards = soup.find_all('li')
    
    extracted_data = []
    
    for card in product_cards:
        # 1. Extract Title
        # Updated to target the <h3> tag present in this specific HTML snippet
        title_tag = card.find('h3', class_='e-1gh06cz')
        
        # Fallback just in case the dynamic class name changes
        if not title_tag:
            title_tag = card.find('h3')
            
        title = title_tag.get_text(strip=True) if title_tag else None
        
        # 2. Extract Price
        # Look for the hidden screen-reader text inside the price container
        price_tag = card.find('span', class_='screen-reader-only')
        price = None
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            match = re.search(r'\$?([\d\.]+)', price_text)
            if match:
                price = float(match.group(1))
                
        # 3. Extract Image URL
        img_tag = card.find('img', {'data-testid': 'item-card-image'})
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
        
        # 4. Extract Product Link
        link_tag = card.find('a')
        link = "https://sameday.costco.com" + link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
        
        # Only append if we successfully found a product title
        if title:
            extracted_data.append({
                "Store": "Costco",
                "Title": title,
                "Price": price,
                "Image_URL": image_url,
                "Product_Link": link
            })
            
    # Convert list of dictionaries to a Pandas DataFrame
    df = pd.DataFrame(extracted_data)
    return df

if __name__ == "__main__":
    main()
    master_rows = []

    # Test URLs
    walmart_url = "https://www.walmart.com/search?q=eggs"
    costco_url = "https://www.costco.com/s?keyword=honey"
    
    # Run the Costco scraper
    # print("--- Scraping Costco ---")
    # costco_results = scrape_ecommerce(costco_url, "honey")
    # print(json.dumps(costco_results, indent=2))
    
    # Run the Walmart scraper
    print("\n--- Scraping Walmart ---")
    walmart_results = scrape_ecommerce(walmart_url, "eggs")
    print(json.dumps(walmart_results, indent=2))