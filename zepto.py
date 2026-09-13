import time
import argparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import os
from urllib.parse import urljoin, quote_plus
import json

class ZeptoScraper:
    def __init__(self, headless=False):
        """Initialize the Zepto scraper with Chrome driver"""
        self.driver = None
        self.base_url = "https://www.zeptonow.com"
        self.setup_driver(headless)
        self.products_data = []
       
    def setup_driver(self, headless=False):
        """Setup Chrome driver with necessary options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
       
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            print("Please make sure you have Chrome and ChromeDriver installed")
           
    def search_products(self, search_query):
        """Search for products and get all product links by scrolling"""
        # Format search query for URL (replace spaces with +)
        formatted_query = quote_plus(search_query)
        # Always use base search URL without city scoping
        search_url = f"{self.base_url}/search?query={formatted_query}"
       
        print(f"Searching for: {search_query}")
        print(f"URL: {search_url}")
       
        self.driver.get(search_url)
        time.sleep(4)  # Increased wait time for page load
       
        # Attempt to close cookie/location popups if present
        for xpath in [
            "//button[contains(., 'Accept') or contains(., 'Got it') or contains(., 'Agree')]",
            "//button[contains(., 'Allow') or contains(., 'Enable')]",
            "//button[contains(., 'Not now') or contains(., 'No thanks')]",
            "//div[contains(@class, 'modal')]//button[contains(., 'Close') or contains(., '×') or contains(., 'close')]"
        ]:
            try:
                el = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].click();", el)
                time.sleep(0.9)
            except Exception:
                pass
       
        # Wait for either the products grid or any product tile/link to appear
        try:
            self.wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='item-list-container'][class*='search-result-screen-v2']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid.w-full.gap-x-3.gap-y-5.overflow-x-hidden")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/pn/']")),
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/pn/')]"))
                )
            )
        except TimeoutException:
            print("Products grid or product tiles not found. The page may be city-locked or layout changed.")
            print(f"Page title: {self.driver.title}")
            return []
       
        # Try to identify a scrollable container in addition to window
        scroll_container = None
        for sel in [
            "div[class*='item-list-container'][class*='search-result-screen-v2']",
            "div.grid.w-full.gap-x-3.gap-y-5.overflow-x-hidden"
        ]:
            try:
                scroll_container = self.driver.find_element(By.CSS_SELECTOR, sel)
                break
            except Exception:
                continue
       
        product_links = []
        seen_hrefs = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        stable_scrolls = 0
        max_scrolls = 300  # Increased from 120 to 300
        no_growth_rounds = 0
        max_no_growth_rounds = 8  # Increased from 3 to 8
        consecutive_empty_scrolls = 0
        max_empty_scrolls = 15  # New limit for consecutive empty scrolls
       
        print("Starting product collection with enhanced scrolling...")
       
        while True:
            # Scroll window
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Also scroll container if available
            if scroll_container is not None:
                try:
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_container)
                except Exception:
                    pass
            time.sleep(1.5)  # Increased wait time for content to load
            
            # Attempt to click any 'Show more' button if present
            show_more_clicked = False
            for button_text in ['Show more', 'Load more', 'View more', 'See more']:
                try:
                    show_more = self.driver.find_element(By.XPATH, f"//button[contains(., '{button_text}')]")
                    self.driver.execute_script("arguments[0].click();", show_more)
                    show_more_clicked = True
                    time.sleep(2)  # Wait for new content to load
                    print(f"Clicked '{button_text}' button")
                    break
                except Exception:
                    continue
            
            # Check for pagination links
            try:
                pagination_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'page=') or contains(@href, 'p=')]")
                for link in pagination_links:
                    if link.is_displayed() and link.is_enabled():
                        try:
                            self.driver.execute_script("arguments[0].click();", link)
                            time.sleep(3)  # Wait for page to load
                            print("Clicked pagination link")
                            break
                        except Exception:
                            continue
            except Exception:
                pass
            
            # Collect links incrementally and track growth
            current_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href,'/pn/')]")
            before = len(seen_hrefs)
            new_links_this_round = 0
            
            for el in current_elements:
                try:
                    href = el.get_attribute('href')
                    if href and '/pn/' in href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        new_links_this_round += 1
                except Exception:
                    continue
            
            after = len(seen_hrefs)
            print(f"Collected unique product URLs: {after} (new this round: {new_links_this_round})")
            
            if new_links_this_round == 0:
                no_growth_rounds += 1
                consecutive_empty_scrolls += 1
            else:
                no_growth_rounds = 0
                consecutive_empty_scrolls = 0
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                stable_scrolls += 1
                if stable_scrolls >= 5 and no_growth_rounds >= max_no_growth_rounds:  # Increased stable scrolls check
                    print("Reached end of products (no further growth)")
                    break
            else:
                stable_scrolls = 0
            last_height = new_height
            
            # Check for consecutive empty scrolls
            if consecutive_empty_scrolls >= max_empty_scrolls:
                print(f"Stopping after {max_empty_scrolls} consecutive empty scrolls")
                break
            
            if max_scrolls is not None:
                max_scrolls -= 1
                if max_scrolls <= 0:
                    print("Hit max scroll attempts; proceeding with collected links.")
                    break
       
        # Extract all product links and stock status from the final DOM using enhanced method
        print("Extracting final product data...")
        final_products = self.extract_product_links_from_page()
        
        # Merge with already collected products
        for product in final_products:
            if product['url'] not in [p['url'] for p in product_links]:
                product_links.append(product)
       
        if not product_links:
            print("No product links extracted. If the site enforces location, please sign in or set location manually in the visible browser.")
           
        print(f"Total unique products found: {len(product_links)}")
        return product_links
   
    def scrape_product_details(self, product_url, out_of_stock_status, with_images: bool = False):
        """Scrape detailed information from a product page. Set with_images=True to click thumbnails and capture large images."""
        print(f"Scraping product: {product_url}")

        self.driver.get(product_url)
        time.sleep(3)

        product_data = {
            'url': product_url,
            'out_of_stock': out_of_stock_status,
            'images': [],
            'product_info': {}
        }

        try:
            # Product name
            try:
                product_name = self.driver.find_element(By.CSS_SELECTOR,
                    "h1, [data-slot-id='ProductName'], .product-name").text
                product_data['product_name'] = product_name
            except NoSuchElementException:
                product_data['product_name'] = "N/A"

            # Price
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR,
                    "[data-slot-id='Price'], .price")
                product_data['price'] = price_element.text
            except NoSuchElementException:
                product_data['price'] = "N/A"

            # Pack size
            try:
                pack_size = self.driver.find_element(By.CSS_SELECTOR,
                    "[data-slot-id='PackSize'], .pack-size").text
                product_data['pack_size'] = pack_size
            except NoSuchElementException:
                product_data['pack_size'] = "N/A"

            # Rating
            try:
                rating = self.driver.find_element(By.CSS_SELECTOR,
                    ".rating, [class*='rating']").text
                product_data['rating'] = rating
            except NoSuchElementException:
                product_data['rating'] = "N/A"

            if with_images:
                # Scrape all images from the carousel containers
                def _to_high_res(u: str) -> str:
                    if not u:
                        return u
                    for small in ("tr:w-88","tr:w-240","tr:w-470","tr:w-520","tr:w-600"):
                        if small in u:
                            return u.replace(small, "tr:w-1280")
                    return u

                def _uuid_from_url(u: str) -> str | None:
                    if "/cms/product_variant/" not in u:
                        return None
                    try:
                        return u.split("/cms/product_variant/")[1].split("/")[0].split(".")[0]
                    except Exception:
                        return None

                # Find all image containers in the carousel
                image_containers = self.driver.find_elements(By.CSS_SELECTOR, "div.relative.aspect-square img[data-nimg='fill']")
                print(f"Found {len(image_containers)} image containers")

                captured_ids = set()
               
                for i, img_elem in enumerate(image_containers):
                    try:
                        src = img_elem.get_attribute("src") or ""
                        if not src:
                            continue
                       
                        img_id = _uuid_from_url(src)
                        if not img_id or img_id in captured_ids:
                            continue
                       
                        captured_ids.add(img_id)
                        hi = _to_high_res(src)
                       
                        product_data['images'].append({
                            'image_index': i,
                            'image_url': hi,
                            'source_type': 'carousel_container'
                        })
                        print(f"✅ Captured image {i+1}: {hi}")
                       
                    except Exception as e:
                        print(f"❌ Error processing image container {i+1}: {e}")
                        continue

                print(f"\n🎯 Total unique images captured: {len(product_data['images'])}")

            # Info sections
            info_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.flex.items-start.gap-3")
            for section in info_sections:
                try:
                    key_element = section.find_element(By.CSS_SELECTOR, "h3")
                    key = key_element.text.strip().lower()
                    value_element = section.find_element(By.CSS_SELECTOR, "p")
                    value = value_element.text.strip()
                    if key and value:
                        product_data['product_info'][key] = value
                except NoSuchElementException:
                    continue

            print(f"Scraped {len(product_data['product_info'])} product details")

        except Exception as e:
            print(f"Error scraping product details: {e}")

        return product_data
   
    def scrape_all_products(self, search_query):
        """Main method to scrape all products for a search query"""
        # Get all product links with retry mechanism
        product_links = self.search_products(search_query)
       
        # If no products found, try alternative search strategies
        if not product_links:
            print("No products found with primary search, trying alternative strategies...")
            
            # Try with different URL patterns
            alternative_urls = [
                f"{self.base_url}/search?q={quote_plus(search_query)}",
                f"{self.base_url}/search?search={quote_plus(search_query)}",
                f"{self.base_url}/products?search={quote_plus(search_query)}"
            ]
            
            for alt_url in alternative_urls:
                try:
                    print(f"Trying alternative URL: {alt_url}")
                    self.driver.get(alt_url)
                    time.sleep(3)
                    
                    # Extract products from this page
                    alt_products = self.extract_product_links_from_page()
                    if alt_products:
                        product_links = alt_products
                        print(f"Found {len(product_links)} products with alternative URL")
                        break
                except Exception as e:
                    print(f"Error with alternative URL {alt_url}: {e}")
                    continue
        
        if not product_links:
            print("No products found after trying all strategies")
            return []
       
        # Scrape details for each product
        all_products_data = []
       
        for i, product in enumerate(product_links, 1):
            print(f"\nScraping product {i}/{len(product_links)}")
            try:
                product_data = self.scrape_product_details(
                    product['url'], product['out_of_stock'], with_images=False)
                all_products_data.append(product_data)
                time.sleep(2)
            except Exception as e:
                print(f"Error scraping product {i}: {e}")
                continue
       
        self.products_data = all_products_data
        return all_products_data
   
    def scrape_images_for_urls(self, urls: list[str] | list[dict]) -> None:
        """Open each product URL from the filtered list and capture images/details.

        Accepts either a list of URLs (backward compatible) or a list of dicts with
        keys 'url' and 'out_of_stock'.
        """
        self.products_data = []
        for i, entry in enumerate(urls, 1):
            if isinstance(entry, dict):
                url = entry.get('url') or entry.get('Product URL') or entry.get('product_url')
                out_of_stock_status = str(entry.get('out_of_stock', entry.get('Out of Stock', 'false'))).lower()
            else:
                url = str(entry)
                out_of_stock_status = "false"
            print(f"\nScraping images for filtered product {i}/{len(urls)}")
            try:
                data = self.scrape_product_details(url, out_of_stock_status=out_of_stock_status, with_images=True)
                self.products_data.append(data)
                time.sleep(1.5)
            except Exception as e:
                print(f"Error scraping images for URL {i}: {url} ({e})")
                continue
   
    def save_to_excel(self, filename="zepto_products.xlsx"):
        """Save scraped data to Excel with separate columns"""
        if not self.products_data:
            print("No data to save")
            return
       
        # Prepare data for Excel
        excel_data = []
       
        for product in self.products_data:
            # Base product information
            row_data = {
                'Product URL': product.get('url', ''),
                'Out of Stock': product.get('out_of_stock', ''),
                'Product Name': product.get('product_name', ''),
                'Price': product.get('price', ''),
                'Pack Size': product.get('pack_size', ''),
                'Rating': product.get('rating', ''),
            }
           
            # Add all product info fields as separate columns
            for key, value in product.get('product_info', {}).items():
                row_data[key.title()] = value
           
            # Add image URLs (combine all images in one column)
            image_urls = []
            for img in product.get('images', []):
                image_urls.append(img.get('image_url', ''))
            row_data['Image URLs'] = ' | '.join(image_urls)
            row_data['Number of Images'] = len(product.get('images', []))
           
            excel_data.append(row_data)
       
        # Create DataFrame and save to Excel
        df = pd.DataFrame(excel_data)
       
        # Ensure directory exists for the Excel file
        target_dir = os.path.dirname(os.path.abspath(filename))
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # Save to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\nData saved to {filename}")
        print(f"Total products scraped: {len(excel_data)}")
        print(f"Columns saved: {list(df.columns)}")
       
        return filename

    def save_links_to_excel(self, rows, filename):
        """Save product links to Excel file"""
        df = pd.DataFrame(rows)
       
        # Ensure directory exists
        target_dir = os.path.dirname(os.path.abspath(filename))
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
       
        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"Links saved to Excel: {filename}")
        except Exception as e:
            # Fallback to CSV if Excel fails
            csv_filename = os.path.splitext(filename)[0] + '.csv'
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"Excel write failed ({e}). Saved CSV instead: {csv_filename}")
            filename = csv_filename
       
        return filename
   
    def download_images(self, download_folder="product_images", brand_override: str | None = None):
        """Download all product images organized by brand > product name.

        If brand_override is provided, use it as the brand folder name instead of
        inferring from the product details.
        """
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
       
        for i, product in enumerate(self.products_data):
            # Get brand name from product info or extract from product name
            brand_name = brand_override or product.get('product_info', {}).get('brand', 'Unknown_Brand')
            if brand_name == 'Unknown_Brand':
                # Try to extract brand from product name
                product_name_guess = product.get('product_name', '')
                if product_name_guess:
                    for brand in ['Sunfeast', 'Parle', 'Britannia', 'ITC', 'Cadbury', 'Nestle', 'Aashirvaad', 'Hatsun']:
                        if brand.lower() in product_name_guess.lower():
                            brand_name = brand
                            break
           
            # Clean and limit brand name for folder
            safe_brand = "".join(c for c in brand_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_brand = safe_brand.replace(' ', '_')[:40]
            
            # Create brand folder
            brand_folder = os.path.join(download_folder, safe_brand or "Brand")
            if not os.path.exists(brand_folder):
                os.makedirs(brand_folder)
            
            # Get product name and create product subfolder (truncate for Windows path limits)
            product_name = product.get('product_name', f'product_{i}')
            safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')
            if not safe_product_name:
                safe_product_name = f'product_{i}'
            # Hard limit product name to avoid MAX_PATH issues
            safe_product_name = safe_product_name[:80]
            
            # Create product folder under brand, with an index prefix
            folder_basename = f"product_{i+1}_{safe_product_name}"
            product_folder = os.path.join(brand_folder, folder_basename)
            # If still too long, aggressively shorten the basename
            if len(product_folder) > 230:
                folder_basename = f"p_{i+1}_{safe_product_name[:40]}"
                product_folder = os.path.join(brand_folder, folder_basename)
            
            if not os.path.exists(product_folder):
                os.makedirs(product_folder)
            
            print(f"Downloading images for: {safe_brand} > {product.get('product_name', '')}")
            
            for img_data in product.get('images', []):
                try:
                    img_url = img_data.get('image_url')
                    img_index = img_data.get('image_index', 0)
                    
                    if img_url:
                        response = requests.get(img_url, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        if response.status_code == 200:
                            # Extract file extension from URL or default to jpg
                            file_ext = 'jpg'
                            if '.' in img_url:
                                file_ext = img_url.split('.')[-1].split('?')[0]
                                if file_ext not in ['jpg', 'jpeg', 'png', 'webp']:
                                    file_ext = 'jpg'
                                
                            img_filename = f"image_{img_index + 1}.{file_ext}"
                            img_path = os.path.join(product_folder, img_filename)
                            
                            with open(img_path, 'wb') as f:
                                f.write(response.content)
                            print(f"  Downloaded: {img_filename}")
                        
                except Exception as e:
                    print(f"  Error downloading image {img_index}: {e}")
                
            print(f"  Total images downloaded: {len(product.get('images', []))}")
   
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

    def extract_product_links_from_page(self):
        """Extract product links from the current page using multiple strategies"""
        product_links = []
        seen_hrefs = set()
        
        # Strategy 1: Direct product links with multiple URL patterns
        selectors = [
            "a[href*='/pn/']",
            "a[href*='/product/']",
            "a[href*='/p/']",
            "a[href*='/item/']",
            "a[href*='/prod/']",
            "[data-product-url]",
            "[data-product-id] a",
            ".product-card a",
            ".product-item a",
            "[class*='product'] a",
            "[class*='item'] a",
            ".card a",
            ".tile a"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        href = element.get_attribute('href')
                        if href and href not in seen_hrefs:
                            # Check if it's a product URL with expanded patterns
                            if any(pattern in href for pattern in ['/pn/', '/product/', '/p/', '/item/', '/prod/']):
                                seen_hrefs.add(href)
                                product_links.append({
                                    'url': href,
                                    'out_of_stock': self.check_stock_status(element)
                                })
                    except Exception:
                        continue
            except Exception:
                continue
        
        # Strategy 2: Look for product containers and extract links
        container_selectors = [
            "[class*='product']",
            "[class*='item']",
            "[data-product]",
            ".card",
            ".tile"
        ]
        
        for selector in container_selectors:
            try:
                containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for container in containers:
                    try:
                        # Look for links within the container
                        links = container.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute('href')
                            if href and href not in seen_hrefs:
                                if any(pattern in href for pattern in ['/pn/', '/product/', '/p/', '/item/', '/prod/']):
                                    seen_hrefs.add(href)
                                    product_links.append({
                                        'url': href,
                                        'out_of_stock': self.check_stock_status(container)
                                    })
                    except Exception:
                        continue
            except Exception:
                continue
        
        return product_links
    
    def check_stock_status(self, element):
        """Check if a product element indicates out of stock status"""
        try:
            # Check for out of stock indicators
            out_of_stock_indicators = [
                "out of stock",
                "out-of-stock", 
                "unavailable",
                "sold out",
                "not available"
            ]
            
            # Check text content
            text = element.text.lower()
            for indicator in out_of_stock_indicators:
                if indicator in text:
                    return "true"
            
            # Check data attributes
            for attr in ['data-is-out-of-stock', 'data-stock-status', 'data-availability']:
                try:
                    value = element.get_attribute(attr)
                    if value and value.lower() in ['true', 'out', 'unavailable']:
                        return "true"
                except Exception:
                    continue
            
            # Check for disabled/out of stock classes
            classes = element.get_attribute('class') or ''
            if any(cls in classes.lower() for cls in ['out-of-stock', 'unavailable', 'disabled']):
                return "true"
                
        except Exception:
            pass
        
        return "false"

def main():
    """Main function to run the scraper"""
    parser = argparse.ArgumentParser(description="Zepto product scraper")
    parser.add_argument("--brand", required=True, help="Brand name to search (use spaces, we will convert to '+')")
    parser.add_argument("--out-dir", default=os.path.join(os.getcwd(), "output"), help="Base folder to save Excel and images")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    brand_query = args.brand.strip()
    output_dir = os.path.abspath(args.out_dir)
    brand_underscore = brand_query.replace(' ', '_')
   
    # Define file paths
    excel_path = os.path.join(output_dir, f"zepto_{brand_underscore}_products.xlsx")

    print(f"Brand provided: {brand_query}")
    print(f"Output directory: {output_dir}")

    # Initialize scraper
    scraper = ZeptoScraper(headless=args.headless)

    try:
        print(f"\n{'='*50}")
        print(f"Scraping products for brand: {brand_query}")
        print(f"Search URL will use query: {brand_query.replace(' ', '+')}")
        print(f"{'='*50}")

        # Scrape listing (details only) and save
        scraper.scrape_all_products(brand_query)
        scraper.save_to_excel(excel_path)

        # Build filtered file (Product Name contains brand)
        try:
            df_all = pd.read_excel(excel_path)
        except Exception:
            print("Could not read Excel file for filtering")
            df_all = None

        if df_all is not None and not df_all.empty and 'Product Name' in df_all.columns:
            mask = df_all['Product Name'].astype(str).str.contains(brand_query, case=False, na=False)
            df_filtered = df_all.loc[mask].copy()
            filtered_path_xlsx = os.path.join(output_dir, f"zepto_{brand_underscore}_products_filtered.xlsx")

            try:
                df_filtered.to_excel(filtered_path_xlsx, index=False, engine='openpyxl')
                filtered_links_path = filtered_path_xlsx
                print(f"Saved filtered products: {filtered_path_xlsx}")
            except Exception as e:
                filtered_path_csv = os.path.splitext(filtered_path_xlsx)[0] + '.csv'
                df_filtered.to_csv(filtered_path_csv, index=False, encoding='utf-8-sig')
                filtered_links_path = filtered_path_csv
                print(f"Filtered Excel write failed ({e}). Saved CSV instead: {filtered_path_csv}")

            # Scrape images ONLY for filtered URLs, then download
            if 'Product URL' in df_filtered.columns:
                # Build entries with URL and Out of Stock so OOS images are also captured
                filtered_entries = []
                for _, row in df_filtered.iterrows():
                    url_val = row.get('Product URL')
                    if isinstance(url_val, str) and url_val.strip():
                        filtered_entries.append({
                            'url': url_val,
                            'out_of_stock': str(row.get('Out of Stock', 'false')).lower()
                        })
            else:
                filtered_entries = []

            if filtered_entries:
                print(f"\nScraping images for {len(filtered_entries)} filtered products...")
                scraper.scrape_images_for_urls(filtered_entries)
                scraper.download_images(download_folder=output_dir, brand_override=brand_query)
            else:
                print("No filtered URLs to scrape; not downloading images.")
        else:
            print("No filtered products found; skipping image scraping.")

    except Exception as e:
        print(f"Error in main execution: {e}")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
