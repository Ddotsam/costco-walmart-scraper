import re
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

def extract_walmart_products(html_string):
    """Parses raw Walmart HTML and returns a DataFrame with product details"""

    soup = BeautifulSoup(html_string, 'html.parser')
    
    product_list = soup.find('div', attrs={'data-testid': 'item-stack'})
    product_cards = product_list.find_all('div', recursive=False)
    
    extracted_data = []

    output_folder = Path("~/documents/costco/python1/output").expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)

    for card in product_cards:

        # Find Title
        title_div = card.find('h3', attrs={'data-automation-id': 'product-title'})
        if title_div:
            title_text = title_div.get_text(strip=True)
        else: 
            continue

        # Find Price
        price_div = card.find('div', attrs={'data-test-id': 'gpt-price-flex-container'})
        if price_div: 
            current_price_span = price_div.find('span', string=re.compile(r'current price', re.IGNORECASE))
            raw_price_text = current_price_span.get_text(strip=True)
            match = re.search(r'\$?([\d,]+\.\d{2})', raw_price_text)
            price = float(match.group(1).replace(',', '')) if match else None
        else:
            continue

        # Find Image URL
        img_tag = card.find('img', attrs={'data-testid': 'productTileImage'})
        if img_tag:
            img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

        # Find Product Link
        product_link_anchor = card.find('a', href=True)
        if product_link_anchor:
            product_link = f"https://www.walmart.com{product_link_anchor['href']}"
        
        if title_text:
            extracted_data.append({
                "Store": "Walmart"
                , "Title": title_text
                , "Price": price or None
                , "Image_URL": img_url or None
                , "Product_Link": product_link
            })
            
    df = pd.DataFrame(extracted_data)
    return df