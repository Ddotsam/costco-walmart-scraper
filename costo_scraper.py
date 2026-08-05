from bs4 import BeautifulSoup
import json

def test_local_html():
    # 1. Open the file we saved to avoid hitting the Costco servers again
    with open("debug_dom.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    products = []

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

    print(json.dumps(products, indent=2))
    print(f"\nTotal products found: {len(products)}")

if __name__ == "__main__":
    test_local_html()