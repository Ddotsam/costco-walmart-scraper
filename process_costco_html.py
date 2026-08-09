import re
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

def extract_costco_products(html_string):
    """Parses raw Costco HTML and returns a DataFrame with product details"""

    soup = BeautifulSoup(html_string, 'html.parser')

    product_list_main = soup.find('div', attrs={'role': 'region', 'aria-label': re.compile(r'results for', re.IGNORECASE)})
    if product_list_main:
        product_cards_main = product_list_main.find_all('div', recursive=False)

    product_list_backup = soup.find('div', id='productList')
    if product_list_backup:
        product_cards_backup = product_list_backup.find_all('div', attrs={'data-testid': re.compile(r'grid', re.IGNORECASE)})

    product_cards = product_cards_main if product_cards_main is not None else product_cards_backup
    
    extracted_data = []

    output_folder = Path("~/documents/costco/python1/output").expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)

    if product_cards_main:
        for card in product_cards_main:
            if card.find('div', attrs={'data-testid': re.compile(r'display-ad', re.IGNORECASE)}):
                continue
            product_cards = card.find_all('div', attrs = {'aria-label': re.compile(r'product', re.IGNORECASE)})
            if not product_cards:
                continue

            for product in product_cards:

                # Find Title
                title_div = product.find('h3')
                if title_div:
                    title_text = title_div.get_text(strip=True)

                # Find Price
                price_span = product.find('span', string=re.compile('current price', re.IGNORECASE))
                if price_span: 
                    price_text = price_span.get_text(strip=True)
                    match = re.search(r'\$?([\d\.]+)', price_text)
                    price = float(match.group(1).replace(',', '')) if match else None

                # Find Image URL
                img_tag = product.find('img', attrs={'data-testid': re.compile(r'item-card-image', re.IGNORECASE)})
                if img_tag:
                    img_srcset = img_tag['srcset'] if 'srcset' in img_tag.attrs else None
                    if img_srcset:
                        entries = re.split(r',\s+', img_srcset.strip())
                        img_url = entries[-1].split(' ')[0] # returns highest resolution image

                # Find Product Link
                product_link_anchor = card.find('a', href=True, role='button')
                if product_link_anchor:
                    product_link = f'https://sameday.costco.com{product_link_anchor["href"]}'

                if title_text:
                    extracted_data.append({
                        "Store": "Costco"
                        , "Title": title_text
                        , "Price": price or None
                        , "Image_URL": img_url or None
                        , "Product_Link": product_link or None
                    })
    elif product_cards_backup:
        for card in product_cards_backup:

            # Find Title
            title_div = card.find('h3', attrs={'id': re.compile(r'producttile', re.IGNORECASE)})
            if title_div:
                title_text = title_div.get_text(strip=True)

            # Find Price
            price_div = card.find('div', attrs={'data-testid': re.compile(r'text_price', re.IGNORECASE)})
            if price_div: 
                price_text = price_div.get_text(strip=True)
                match = re.search(r'\$?([\d\.]+)', price_text)
                price = float(match.group(1).replace(',', '')) if match else None

            # Find Image URL
            img_div = card.find('div', attrs={'data-testid': re.compile(r'productimage', re.IGNORECASE)})
            if img_div:
                img_tag = img_div.find('img')
                img_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None

            # Find Product Link
            product_link_anchor = card.find('a', href=True, attrs={'data-testid': re.compile(r'link', re.IGNORECASE)})
            if product_link_anchor:
                product_link = product_link_anchor['href']
            
            if title_text:
                extracted_data.append({
                    "Store": "Costco"
                    , "Title": title_text
                    , "Price": price or None
                    , "Image_URL": img_url or None
                    , "Product_Link": product_link or None
                })
    else: 
        print("No product cards found in the HTML. The page layout might be different, or a bot wall appeared.")
        return pd.DataFrame()  # Return an empty DataFrame if no products are found
            
    df = pd.DataFrame(extracted_data)
    return df