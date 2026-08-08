import re
import pandas as pd
from cloakbrowser import launch
from bs4 import BeautifulSoup
from pathlib import Path

def extract_costco_products(html_string):
    """Parses raw Costco HTML and returns a DataFrame with product details"""

    soup = BeautifulSoup(html_string, 'html.parser')

    product_list_main = soup.find('div', attrs={'role': 'region', 'aria-label': re.compile(r'results for', re.IGNORECASE)})
    product_cards_main = product_list_main.find_all('div', recursive=False)

    product_list_backup = soup.find('div', id='productList')
    product_cards_backup = product_list_backup.find_all('div', attrs={'data-testid': re.compile(r'grid', re.IGNORECASE)})

    product_cards = product_cards_main if product_cards_main is not None else product_cards_backup
    
    extracted_data = []
    card_number = 0

    output_folder = Path("~/documents/costco/python1/output").expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)

    for card in product_cards:

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
                "Store": "Costco",
                "Title": title_text,
                "Price": price,
                "Image_URL": img_url,
                "Product_Link": product_link
            })
            
    df = pd.DataFrame(extracted_data)
    return df