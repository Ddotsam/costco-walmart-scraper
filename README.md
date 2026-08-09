# grocery-price-scraper

Concurrently scrapes product data from **Costco Same‑Day** and **Walmart** for a given list of grocery items. Results are saved as a Parquet file, ready for analysis or upload to Databricks. The purpose of this is to figure out if the Costco membership actually saves you money by buying in bulk vs. buying products at a conventional grocery store, such as Walmart.

Tl;dr: You spend more at Costco for the same products most of the time.

## Features

- **Dual‑store scraping** – fetches Costco & Walmart in parallel using a single browser with two tabs, staying within the free CloakBrowser license limit.
- **Human‑like browsing** – random pauses, scroll events, and non‑headless mode help avoid bot detection.
- **Robust selectors** – uses semantic locators (roles, ARIA labels, data‑testids) instead of brittle CSS classes.
- **Automatic retry / fallback** – if a primary page element doesn’t load, a fallback selector captures the HTML for debugging.
- **Error resilience** – failed tasks are logged and skipped; successful results are always saved.

## Tech Stack

- [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) (stealth Chromium)
- [Playwright](https://playwright.dev/python/) (async API)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [pandas](https://pandas.pydata.org/) & PyArrow (Parquet output)
- Python `asyncio` for concurrency

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/grocery-price-scraper.git
cd grocery-price-scraper

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt   # if you have one, or manually:

# Install Playwright browsers
playwright install chromium