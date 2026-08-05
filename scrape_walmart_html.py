import re
import pandas as pd
from cloakbrowser import launch
from bs4 import BeautifulSoup
from pathlib import Path

output_folder = Path("~/documents/costco/python1/output").expanduser()

output_folder.mkdir(parents=True, exist_ok=True)

def extract_walmart_products(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    
    product_list = soup.find('div', attrs={'data-testid': 'item-stack'})
    product_cards = product_list.find_all('div', recursive=False)
    
    extracted_data = []
    card_number = 0

    output_folder = Path("~/documents/costco/python1/output").expanduser()
    output_folder.mkdir(parents=True, exist_ok=True)

    for card in product_cards:
        file_path = output_folder / f"card_{card_number}.html"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(card.prettify())

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
            product_link = product_link_anchor['href']
        
        if title_text:
            extracted_data.append({
                "Store": "Walmart",
                "Title": title_text,
                "Price": price,
                "Image_URL": img_url,
                "Product_Link": product_link
            })
            
    df = pd.DataFrame(extracted_data)
    return df

if __name__ == "__main__":

    with open("raw_html/walmart_eggs.html", "r", encoding="utf-8") as file:
        file_contents = file.read()

    df = extract_walmart_products(file_contents)
    df.to_json(output_folder / "walmart_products.json", orient="records", indent=4)