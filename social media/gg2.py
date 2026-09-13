"""
Instagram Brand Verification & Followers Scraper (Updated UI)

Steps:
- Reads brand names from Excel (brand.xlsx, column "Brand")
- Logs into Instagram
- Handles login popups (Save info / Turn on notifications)
- Uses search input directly
- Clicks on profile under the search tab (not feeds)
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
                time.sleep(2)
                break
            except Exception:
                continue

        # 2) Focus the actual search input
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
        time.sleep(0.5)

        # Clear any existing text
        search_box.click()
        search_box.send_keys(Keys.CONTROL + 'a')
        search_box.send_keys(Keys.BACKSPACE)

        # Type the query
        search_box.send_keys(brand_name)
        time.sleep(3)

        # 3) Click on the first profile under the search tab (not feeds)
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )

        # Select profiles specifically under the search tab
        candidates = driver.find_elements(
            By.XPATH,
            (
                "//div[@role='dialog']//a[starts-with(@href,'/') and not(contains(@href,'/explore/')) and not(contains(@href,'/p/')) and not(contains(@href,'/tags/'))]"
            ),
        )

        # Filter to plausible profile links and deduplicate by username
        ordered_unique = []
        seen_usernames = set()
        for el in candidates:
            try:
                href = el.get_attribute("href") or ""
                if not href:
                    continue
                if not re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", href):
                    continue
                username = href.rstrip("/").split("/")[-1].split("?")[0]
                if username not in seen_usernames:
                    seen_usernames.add(username)
                    ordered_unique.append(el)
            except Exception:
                continue

        if not ordered_unique:
            raise TimeoutException("No profile results found under search tab")

        # Click the first profile
        try:
            target = ordered_unique[0]
            wait.until(EC.element_to_be_clickable(target)).click()
        except Exception:
            driver.execute_script("arguments[0].click();", target)

        # Wait for profile page to load
        WebDriverWait(driver, 10).until(
            lambda d: bool(re.search(r"https?://(www\.)?instagram\.com/[^/]+/?$", d.current_url))
        )
        time.sleep(2)

        # Check verification (only within the profile header)
        verified = "Not Verified ❌"
        try:
            header = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "header"))
            )
            header.find_element(By.XPATH, ".//*[name()='svg' and @aria-label='Verified'] | .//span[@aria-label='Verified']")
            verified = "Verified ✅"
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
                text_val = (el.text or el.get_attribute("title") or "").strip()
                if text_val:
                    followers = text_val
                    break
            except Exception:
                continue

        # Fallback to meta og:description
        if followers == "Not Found":
            try:
                meta_content = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute("content")
                match = re.search(r"([\d,]+(?:\.\d+)?[KMB]?) Followers", meta_content)
                if match:
                    followers = match.group(1)
            except Exception:
                pass

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