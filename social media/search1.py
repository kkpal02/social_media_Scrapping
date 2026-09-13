"""
Instagram Brand Verification & Followers Scraper (Updated UI)

Steps:
- Reads brand names from Excel (brand.xlsx, column "Brand")
- Logs into Instagram
- Handles login popups (Save info / Turn on notifications)
- Uses search input directly
- Opens first result
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
from difflib import SequenceMatcher

# --- CONFIG ---
INPUT_EXCEL = "brand.xlsx"      # input excel with a column "Brand"
OUTPUT_EXCEL = "instagram_results.xlsx"

# --- SETUP SELENIUM ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# --- LOGIN TO INSTAGRAM ---
def insta_login(username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(7)

    # Handle "Save your login info?" popup
    try:
        save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Save info')]")
        save_button.click()
        print("Clicked 'Save info'")
        time.sleep(0.5)
    except:
        print("No 'Save info' popup found.")

    # Handle "Turn on Notifications" popup
    try:
        not_now_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
        not_now_button.click()
        print("Dismissed 'Turn on Notifications'")
        time.sleep(3)
    except:
        print("No 'Turn on Notifications' popup found.")

# --- CHECK BRAND ---
def check_brand(brand_name):
    try:
        wait = WebDriverWait(driver, 15)

        # 1) Open the left sidebar Search panel (robust across layouts)
        opened_search = False
        search_open_locators = [
            (By.XPATH, "//a[contains(@href,'/explore/search/')]"),
            (By.XPATH, "//span[normalize-space()='Search']/ancestor::a"),
            (By.XPATH, "//div[normalize-space()='Search' and @role='button']"),
        ]
        for by, locator in search_open_locators:
            try:
                el = wait.until(EC.element_to_be_clickable((by, locator)))
                el.click()
                opened_search = True
                break
            except Exception:
                continue

        # It's okay if it's already open; proceed to find the input

        # 2) Focus the actual search input (try multiple selectors)
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
                break
            except TimeoutException:
                continue

        if search_box is None:
            raise TimeoutException("Search input not found")

        # Ensure it's focused and visible
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_box)
        driver.execute_script("arguments[0].focus();", search_box)
        time.sleep(0.2)

        # Clear any existing text
        try:
            search_box.click()
            search_box.send_keys(Keys.CONTROL, 'a')
            search_box.send_keys(Keys.BACK_SPACE)
        except Exception:
            pass

        # Try to type the query normally first
        try:
            search_box.send_keys(brand_name)
            time.sleep(0.2)
        except Exception:
            pass

        # If value is still empty, fall back to JS to set and dispatch events
        try:
            current_value = search_box.get_attribute("value") or ""
            if current_value.strip() == "":
                driver.execute_script(
                    """
                    const el = arguments[0];
                    const val = arguments[1];
                    el.focus();
                    el.value = '';
                    const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    setValue.call(el, val);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
                    """,
                    search_box,
                    brand_name,
                )
                time.sleep(1.0)
        except Exception:
            pass

        # 2.5) Quick attempt: use keyboard to open the top suggestion
        navigated_via_keyboard = False
        try:
            search_box.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.2)
            search_box.send_keys(Keys.ENTER)
            # If this worked, URL should become a profile within a short time
            try:
                WebDriverWait(driver, 4).until(
                    lambda d: bool(re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", d.current_url))
                )
                navigated_via_keyboard = True
            except Exception:
                pass
        except Exception:
            pass

        # 3) If not already navigated, click the FIRST (top-most) valid profile suggestion
        try:
            if navigated_via_keyboard:
                raise TimeoutException("Already navigated via keyboard; skip clicking suggestions")
            # Wait for dropdown suggestions to render
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")),
                    EC.presence_of_element_located((By.XPATH, "//div[@role='none']")),
                )
            )

            candidates = driver.find_elements(
                By.XPATH,
                (
                    "//div[@role='dialog']//a[starts-with(@href,'/')] | "
                    "//div[@role='none']//a[starts-with(@href,'/')] | "
                    "//a[@role='link' and starts-with(@href,'/')]"
                ),
            )

            # Filter to plausible profile links and deduplicate by username in DOM order
            ordered_unique = []
            seen_usernames = set()
            for el in candidates:
                try:
                    href = el.get_attribute("href") or ""
                    if not href:
                        continue
                    if any(x in href for x in ["/explore", "/reels", "/p/", "/stories", "/direct/", "/tags/"]):
                        continue
                    if not re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", href):
                        continue
                    username = href.rstrip("/").split("/")[-1]
                    username = username.split("?")[0]
                    if username not in seen_usernames:
                        seen_usernames.add(username)
                        ordered_unique.append(el)
                except Exception:
                    continue

            target = ordered_unique[0] if ordered_unique else None
            if target is None:
                raise TimeoutException("No search results available")

            try:
                wait.until(EC.element_to_be_clickable(target)).click()
            except Exception:
                driver.execute_script("arguments[0].click();", target)
        except Exception as e:
            raise TimeoutException(f"No search results clickable: {e}")

        # Wait for profile page to load
        try:
            WebDriverWait(driver, 10).until(
                lambda d: bool(re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", d.current_url))
            )
        except Exception:
            time.sleep(2)
        time.sleep(1.5)

        # Check verification (only within the profile header)
        verified = "Not Verified ❌"
        try:
            header = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//header"))
            )
            # Look for the badge strictly inside header
            try:
                header.find_element(By.XPATH, ".//*[name()='svg' and @aria-label='Verified'] | .//span[@aria-label='Verified']")
                verified = "Verified ✅"
            except Exception:
                verified = "Not Verified ❌"
        except Exception:
            verified = "Not Verified ❌"

        # Followers
        followers = "Not Found"
        follower_locators = [
            "//header//a[contains(@href,'/followers')]//span/span",
            "//header//a[contains(@href,'/followers')]//span",
            "//header//ul/li[2]//span",
        ]
        for locator in follower_locators:
            try:
                el = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, locator))
                )
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                except Exception:
                    pass
                text_val = (el.text or el.get_attribute("title") or "").strip()
                if text_val:
                    followers = text_val
                    break
            except Exception:
                continue

        return verified, followers
    except Exception as e:
        return "Error", str(e)

# --- MAIN WORKFLOW ---
def main():
    insta_login("Drone_Krishna", "@Kkpal2001@")  # ⚠️ Replace with your IG creds

    df = pd.read_excel(INPUT_EXCEL)
    results = []

    for brand in df["Brand"]:
        status, followers = check_brand(brand)
        results.append({"Brand": brand, "Verification": status, "Followers": followers})
        print(f"{brand} → {status}, Followers: {followers}")

    pd.DataFrame(results).to_excel(OUTPUT_EXCEL, index=False)
    driver.quit()
    print(f"✅ Results saved to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()
