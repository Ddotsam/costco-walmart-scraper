import time
import json
import re
import pandas as pd
from cloakbrowser import launch
from bs4 import BeautifulSoup
from pathlib import Path

output_folder = Path("~/documents/costco/python1/output").expanduser()

output_folder.mkdir(parents=True, exist_ok=True)

def extract_costco_products(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    
    product_list = soup.find('div', id='productList')
    product_cards = product_list.find_all('div', attrs={'data-testid': re.compile(r'grid', re.IGNORECASE)})
    
    extracted_data = []
    card_number = 0

    output_folder = Path("~/documents/costco/python1/output").expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)

    for card in product_cards:
        file_path = output_folder / f"card_{card_number}.html"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(card.prettify())

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

if __name__ == "__main__":

    with open("costco_html.html", "r", encoding="utf-8") as file:
        file_contents = file.read()

    df = extract_costco_products(file_contents)
    df.to_json(output_folder / "costco_products.json", orient="records", indent=4)