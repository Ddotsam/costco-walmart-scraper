import time
import json
import urllib.parse
import pandas as pd
from cloakbrowser import launch

def scrape_sameday_costco_api(product_name):
    print("Launching stealth browser session...")
    browser = launch(headless=False, humanize=True)
    page = browser.new_page()

    try:
        print("Navigating to homepage to establish session and pass bot checks...")
        page.goto("https://sameday.costco.com/", wait_until="load")
        time.sleep(3) 

        try:            
            guest_link = page.get_by_text("continue as guest", ignore_case=True)
            guest_link.wait_for(state="visible", timeout=5000)
            print("Found 'Continue as guest' link. Clicking it...")
            guest_link.click()
            time.sleep(4) 
            print("Successfully bypassed the interstitial!")
        except Exception:
            print("No interstitial ad appeared. Proceeding to search...")
            
        # ------------------------------------------
        # THE FIX: NETWORK INTERCEPTION
        # ------------------------------------------
        encoded_query = urllib.parse.quote(product_name)
        
        # This is the frontend URL for a search on Sameday Costco
        search_url = f"https://sameday.costco.com/store/costco/search/{encoded_query}"

        print(f"Intercepting background API fetch for: '{product_name}'...")
        
        # We tell Playwright to listen for the specific GraphQL response
        # It waits until it sees a URL containing "SearchResultsPlacements"
        with page.expect_response(lambda response: "SearchResultsPlacements" in response.url and response.status == 200, timeout=15000) as response_info:
            
            # Navigating to the page forces Costco's own code to make the authenticated API request
            page.goto(search_url)
            
        # Snatch the JSON payload directly from the intercepted network traffic!
        json_response = response_info.value.json()

        return json_response

    except Exception as e:
        print(f"Error making API request or Intercepting data: {e}")
        return None
        
    finally:
        browser.close()

def process_and_save_to_parquet(raw_json, filename="sameday_costco_data.parquet"):
    """
    Parses the deeply nested GraphQL JSON and saves it as a Parquet file.
    """
    try:
        # GraphQL usually buries the list of items deep in the 'data' object.
        # Note: You may need to adjust these dictionary keys slightly based on the 
        # exact structure printed in your terminal.
        # This assumes a typical Instacart/Costco GraphQL structure.
        item_modules = raw_json['data']['searchResultsPlacements']['placements']
        
        # Flatten the data structure
        items_list = []
        for module in item_modules:
            if 'items' in module:
                items_list.extend(module['items'])

        if not items_list:
            print("No items found in the JSON to save.")
            return

        # Load the list of items into a Pandas DataFrame
        # pd.json_normalize automatically flattens nested JSON objects into distinct columns!
        df = pd.json_normalize(items_list)
        
        print(f"\nExtracted {len(df)} items. DataFrame Preview:")
        print(df.head())

        # Save the DataFrame to a Databricks-compatible Parquet file
        df.to_parquet(filename, engine='pyarrow', index=False)
        print(f"\n✅ Successfully saved to {filename}!")
        
    except KeyError as e:
        print(f"Failed to parse JSON. The GraphQL structure might be different. Missing key: {e}")

if __name__ == "__main__":
    # 1. Fetch the data
    raw_api_data = scrape_sameday_costco_api("banana")
    
    # 2. Convert and save it
    if raw_api_data:
        process_and_save_to_parquet(raw_api_data, "costco_bananas.parquet")
    else:
        print("There was no raw_api_data")