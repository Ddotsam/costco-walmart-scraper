import pandas as pd
from bs4 import BeautifulSoup
import re

# ==========================================
# 1. HTML SNIPPETS
# ==========================================

costco_html = """
<div class="e-cmecnr"><ul class="e-egal4z"><li><div data-item-card="true" class="e-1aytrge"><div aria-label="Product" role="group" class="e-fsno8i"><a role="button" href="/store/costco/products/32574207-kirkland-signature-raw-unfiltered-honey-48-oz" aria-disabled="false" data-item-card-button="true" class="e-1nw1bbv"><div><div class="e-19idom"><div class="e-1m0du6a"><div class="e-ec1gba"><img data-testid="item-card-image" alt="Kirkland Signature Northwest Raw &amp; Unfiltered Honey, 48 oz" class="e-19e3dsf" src="https://www.instacart.com/image-server/197x197/filters:fill(FFFFFF,true):format(jpg)/d2lnr5mha7bycj.cloudfront.net/product-image/file/large_4dc7e04f-4e37-4084-8f05-0c80e2073d69.jpeg" data-airgap-id="205"></div></div></div></div><div class="e-1916dlq"><div class="e-m67vuy"><div class="e-1f177aj"><div class="e-1632met"><span class="screen-reader-only" style="border: 0px; clip: rect(0px, 0px, 0px, 0px); height: 1px; width: 1px; margin: -1px; overflow: hidden; padding: 0px; position: absolute;">Current price: $13.61</span><span class="e-gx2pr0"><span aria-hidden="true" class="e-1s0dpuj">$</span><span aria-hidden="true" class="e-1qkvt8e">13</span><span aria-hidden="true" class="e-1s0dpuj">61</span></span></div><div class="e-1om9ohm"><div class="e-1rr4qq7"></div><div class="e-1rr4qq7"></div></div></div></div><div class="e-1gh06cz" role="heading" aria-level="3">Kirkland Signature Northwest Raw &amp; Unfiltered Honey, 48 oz</div><div class="e-1r6exdz"></div></div></a><section></section><div class="e-4mgja0"><div><div class="e-oedsod"><button aria-label="Add 1 ct Kirkland Signature Northwest Raw &amp; Unfiltered Honey, 48 oz" type="button" tabindex="0" class="e-1txn78m" data-ids-pressable="true" style="touch-action: var(--ids-pressable-touch-action, manipulation);"><span class="e-jry5p8"><div class="e-1xtfaq4"><svg width="24" height="24" viewBox="0 0 24 24" fill="#FFFFFF" xmlns="http://www.w3.org/2000/svg" size="24" color="systemGrayscale00" class="e-0" aria-hidden="true"><path d="M10.88 13.12V20h2.24v-6.88H20v-2.24h-6.88V4h-2.24v6.88H4v2.24z"></path></svg><span class="e-1uqi5g4">Add</span></div></span></button></div></div></div></div></div></li></ul></div>
"""

walmart_html = """
<div class="flex flex-wrap w-100 flex-grow-0 flex-shrink-0 ph0 ph2-m pr0-xl pl4-xl mt0-xl" data-testid="item-stack"><div class="mb0 ph0-xl pt0-xl bb b--near-white w-25"><div class="h-100 pr4-xl ph2 pv3" style="contain-intrinsic-size: 198px 340px;"><div role="group" data-item-id="575PIBDL9JKY" data-dca-guid="575PIBDL9JKY" data-dca-id="20647992" data-dca-name="stickyATC" data-dca-type="module" class="sans-serif mid-gray relative flex flex-column w-100 hide-child-opacity" data-test-id="gpt-main"><a link-identifier="20647992" class="w-100 h-100 z-1 hide-sibling-opacity  absolute" target="" data-dca-aid="L:7B06D07E1D" data-dca-intent="select" data-dca-event="unknown" href="/ip/Great-Value-Honey-12-oz-Plastic-Bear/20647992?classType=VARIANT&amp;athbdg=L1300&amp;from=/search"><span class="ld_Ec"><h3>Rollback Great Value Honey, 12 oz Plastic Bear $2.97 Was $3.74 24.8 ¢/oz</h3></span></a><div data-test-id="gpt-product-tile-grid-container"><div data-test-id="gpt-product-visual-meta-data"><img loading="eager" src="https://i5.walmartimages.com/seo/Great-Value-Honey-12-oz-Plastic-Bear_c07e5a16-fb71-4313-a8e2-5a5561a9b3d3.9f104c3a50f0a5278dd722c470f6b9a9.jpeg?odnHeight=576&amp;odnWidth=576&amp;odnBg=FFFFFF" id="is-0-productImage-0" width="" height="" class="absolute top-0 left-0" data-testid="productTileImage" alt="Great Value Honey, 12 oz Plastic Bear"></div><div class="" data-test-id="gpt-product-descriptive-meta-data-container"><div data-automation-id="product-price" class="mt1" data-test-id="gpt-global-product-price"><div class="flex flex-wrap justify-start items-baseline lh-title" data-test-id="gpt-price-flex-container"><span class="ld_Ec">current price Now $2.97, Was $3.74</span></div></div><h3 data-automation-id="product-title" class="normal dark-gray mb0 mt1 lh-title f6 f5-l">Great Value Honey, 12 oz Plastic Bear</h3></div></div></div></div></div></div>
"""

# ==========================================
# 2. PARSING FUNCTIONS
# ==========================================

def get_costco_dataframe(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    product_cards = soup.find_all('li')
    extracted_data = []
    
    for card in product_cards:
        title_tag = card.find('div', role='heading')
        title = title_tag.get_text(strip=True) if title_tag else None
        
        price_tag = card.find('span', class_='screen-reader-only')
        price = None
        if price_tag:
            match = re.search(r'\$?([\d\.]+)', price_tag.get_text(strip=True))
            if match:
                price = float(match.group(1))
                
        img_tag = card.find('img', {'data-testid': 'item-card-image'})
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
        
        link_tag = card.find('a')
        link = "https://sameday.costco.com" + link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
        
        if title:
            extracted_data.append({
                "Store": "Costco",
                "Title": title,
                "Price": price,
                "Image_URL": image_url,
                "Product_Link": link
            })
            
    return pd.DataFrame(extracted_data)

def get_walmart_dataframe(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    product_cards = soup.find_all('div', attrs={'data-item-id': True})
    extracted_data = []
    
    for card in product_cards:
        title_tag = card.find('h3', attrs={'data-automation-id': 'product-title'})
        title = title_tag.get_text(strip=True) if title_tag else None
        
        price = None
        price_container = card.find('div', attrs={'data-automation-id': 'product-price'})
        if price_container:
            sr_price_tag = price_container.find('span', class_='ld_Ec')
            if sr_price_tag:
                match = re.search(r'\$?([\d\.]+)', sr_price_tag.get_text(strip=True))
                if match:
                    price = float(match.group(1))
                
        img_tag = card.find('img', attrs={'data-testid': 'productTileImage'})
        image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
        
        link_tag = card.find('a', href=re.compile(r'^/ip/'))
        link = "https://www.walmart.com" + link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
        
        if title:
            extracted_data.append({
                "Store": "Walmart",
                "Title": title,
                "Price": price,
                "Image_URL": image_url,
                "Product_Link": link
            })
            
    return pd.DataFrame(extracted_data)

# ==========================================
# 3. MERGE AND SAVE
# ==========================================

if __name__ == "__main__":
    print("Parsing Costco data...")
    df_costco = get_costco_dataframe(costco_html)
    
    print("Parsing Walmart data...")
    df_walmart = get_walmart_dataframe(walmart_html)
    
    print("\nConcatenating DataFrames...")
    # pd.concat merges the rows of both DataFrames into one large table
    # ignore_index=True resets the row numbers so they flow sequentially (0, 1, 2, 3...)
    df_combined = pd.concat([df_costco, df_walmart], ignore_index=True)
    
    print("\nCombined DataFrame Preview:")
    print(df_combined.head())
    
    # Save the unified DataFrame to a Parquet file
    output_filename = "combined_honey_prices.parquet"
    df_combined.to_parquet(output_filename, engine='pyarrow', index=False)
    print(f"\n✅ All data successfully merged and saved to '{output_filename}'!")