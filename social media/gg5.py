"""
Instagram Brand Verification & Followers Scraper (Updated UI)

Steps:
- Reads brand names from Excel (brand.xlsx, column "Brand")
- Logs into Instagram
- Handles login popups (Save info / Turn on notifications)
- Uses search input directly
- Clicks on the first profile under the search tab (not feeds, posts, or tags)
- Checks if the account is verified
- Extracts follower count
- Writes result to new Excel file (instagram_results.xlsx)

Requirements:
pip install selenium webdriver-manager pandas openpyxl
"""

import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIG ---
INPUT_EXCEL = "brand_all24.xlsx"      # Input Excel with a column "Brand"
OUTPUT_EXCEL = "instagram_results_3012.xlsx"

# --- SETUP SELENIUM ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- LOGIN TO INSTAGRAM ---
def insta_login(username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    try:
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(10)

        # Handle "Save your login info?" popup
        try:
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]"))
            )
            save_button.click()
            print("Clicked 'Save' button")
            time.sleep(2)
        except:
            print("No 'Save' popup found.")

        # Handle "Turn on Notifications" popup
        try:
            not_now_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            print("Dismissed 'Turn on Notifications'")
            time.sleep(3)
        except:
            print("No 'Turn on Notifications' popup found.")
    except Exception as e:
        print(f"Login failed: {e}")
        raise

# --- CHECK BRAND ---
def check_brand(brand_name):
    try:
        wait = WebDriverWait(driver, 15)

        # 1) Open the left sidebar Search panel
        search_open_locators = [
            (By.XPATH, "//a[contains(@href,'/explore/search/')]"),
            (By.XPATH, "//span[normalize-space()='Search']/ancestor::a"),
            (By.XPATH, "//div[normalize-space()='Search' and @role='button']"),
        ]
        for by, locator in search_open_locators:
            try:
                el = wait.until(EC.element_to_be_clickable((by, locator)))
                el.click()
                print(f"Opened search panel using {locator}")
                time.sleep(2)
                break
            except Exception as e:
                print(f"Failed to open search with {locator}: {e}")
                continue
        else:
            # If we couldn't click open, the search input may already be visible; try to continue.
            try:
                _tmp_box = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Search input']"))
                )
                print("Search panel likely already open; proceeding with existing input.")
            except Exception:
                print("Could not open search panel and input not visible. Skipping brand.")
                return "Skipped", "profile skipped or no account found."

        # 2) Focus the search input
        input_locators = [
            (By.XPATH, "//input[@aria-label='Search input']"),
            (By.XPATH, "//input[@placeholder='Search']"),
            (By.XPATH, "//div[@role='dialog']//input"),
            (By.CSS_SELECTOR, "input[aria-label='Search input']"),
        ]

        search_box = None
        for by, locator in input_locators:
            try:
                search_box = wait.until(EC.element_to_be_clickable((by, locator)))
                print(f"Found search input using {locator}")
                break
            except TimeoutException:
                print(f"Search input not found with {locator}")
                continue

        if search_box is None:
            raise TimeoutException("Search input not found")

        # Ensure it's focused and visible
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_box)
        driver.execute_script("arguments[0].focus();", search_box)
        time.sleep(0.5)

        # Clear any existing text
        search_box.click()
        search_box.send_keys(Keys.CONTROL + 'a')
        search_box.send_keys(Keys.BACKSPACE)

        # Type the query
        print(f"Searching for: {brand_name}")
        search_box.send_keys(brand_name)
        time.sleep(4)  # Increased wait for suggestions to load fully

        # 3) Click FIRST profile strictly from the Search panel (avoid feed/global results)
        # Scope strictly to the sliding Search panel that wraps the active input
        try:
            panel_container = search_box.find_element(
                By.XPATH,
                "ancestor::div[contains(@class,'x7goit8')][1]"
            )
        except Exception:
            # Fallback to a known search panel scroller near the input
            try:
                panel_container = search_box.find_element(
                    By.XPATH,
                    "ancestor::div[contains(@class,'xvbhtw8')][1]"
                )
            except Exception:
                print("Search panel container not found near the input. Skipping brand.")
                try:
                    search_box.send_keys(Keys.ESCAPE)
                    time.sleep(0.2)
                    clear_btn = search_box.find_element(By.XPATH, "following::div[@aria-label='Clear the search box'][1]")
                    clear_btn.click()
                except Exception:
                    pass
                return "Skipped", "profile skipped or no account found."

        # Wait until at least one profile-like anchor appears within this panel only
        try:
            first_link = WebDriverWait(panel_container, 8).until(
                lambda c: c.find_element(
                    By.XPATH,
                    "(.//a[starts-with(@href,'/') and not(contains(@href,'/explore/')) and not(contains(@href,'/p/')) and not(contains(@href,'/tags/')) and not(contains(@href,'/stories/')) and not(contains(@href,'/direct/'))])[1]"
                )
            )
        except Exception:
            print("No profile result anchors found in Search panel. Skipping brand.")
            try:
                search_box.send_keys(Keys.ESCAPE)
                time.sleep(0.2)
                clear_btn = search_box.find_element(By.XPATH, "following::div[@aria-label='Clear the search box'][1]")
                clear_btn.click()
            except Exception:
                pass
            return "Skipped", "profile skipped or no account found."

        target_href = first_link.get_attribute("href") or ""
        if not target_href:
            raise TimeoutException("First result anchor has no href")

        # Normalize relative href like "/classmatebyitc/" to full URL
        if target_href.startswith("/"):
            target_href = f"https://www.instagram.com{target_href}"

        print(f"Navigating to first profile URL from Search panel: {target_href}")
        try:
            driver.get(target_href)
        except Exception:
            driver.execute_script("window.location.href = arguments[0];", target_href)

        # Wait for profile page to load
        WebDriverWait(driver, 10).until(
            lambda d: bool(re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", d.current_url))
        )
        time.sleep(2)

        # Wait for profile page to load
        WebDriverWait(driver, 10).until(
            lambda d: bool(re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", d.current_url))
        )
        time.sleep(3)
        print(f"Navigated to profile: {driver.current_url}")

        # Check verification (only within the profile header)
        verified = "Not Verified ❌"
        try:
            header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "header"))
            )
            header.find_element(
                By.XPATH, ".//*[name()='svg' and @aria-label='Verified'] | .//span[@aria-label='Verified']"
            )
            verified = "Verified ✅"
            print("Profile is verified")
        except Exception:
            print("Profile is not verified")

        # Followers
        followers = "Not Found"
        follower_locators = [
            "//header//a[contains(@href,'/followers')]//span/span",
            "//header//a[contains(@href,'/followers')]//span",
            "//header//ul/li[2]//span[@title]",
            "//header//ul/li[2]//span",
        ]
        for locator in follower_locators:
            try:
                el = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, locator))
                )
                text_val = (el.text or el.get_attribute("title") or "").strip()
                if text_val:
                    followers = text_val
                    print(f"Found followers: {followers}")
                    break
            except Exception:
                continue

        # Fallback to meta og:description
        if followers == "Not Found":
            try:
                meta_content = driver.find_element(
                    By.XPATH, "//meta[@property='og:description']"
                ).get_attribute("content")
                match = re.search(r"([\d,]+(?:\.\d+)?[KMB]?) Followers", meta_content)
                if match:
                    followers = match.group(1)
                    print(f"Found followers via meta: {followers}")
            except Exception:
                print("Could not find followers via meta")

        return verified, followers
    except Exception as e:
        print(f"Error processing {brand_name}: {e}")
        return "Error", str(e)

# --- MAIN WORKFLOW ---
def main():
    try:
        insta_login("Drone_Krishna", "@Kkpal2001@")  # ⚠️ Replace with your IG creds

        df = pd.read_excel(INPUT_EXCEL)
        results = []

        for brand in df["Brand"]:
            print(f"\nProcessing brand: {brand}")
            status, followers = check_brand(brand)
            results.append({"Brand": brand, "Verification": status, "Followers": followers})
            print(f"{brand} → {status}, Followers: {followers}")

        pd.DataFrame(results).to_excel(OUTPUT_EXCEL, index=False)
        print(f"✅ Results saved to {OUTPUT_EXCEL}")
    except Exception as e:
        print(f"Main workflow failed: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()