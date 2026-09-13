"""
Instagram Brand Verification & Followers Scraper (Updated UI)

Steps:
- Reads brand names from Excel (brand.xlsx, column "Brand")
- Logs into Instagram
- Handles login popups (Save info / Turn on notifications)
- Uses search input directly
- Clicks on the first profile under the search tab
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
INPUT_EXCEL = "brand.xlsx"      # Input Excel with a column "Brand"
OUTPUT_EXCEL = "instagram_results.xlsx"

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
        time.sleep(8)

        # Handle "Save your login info?" popup
        try:
            save_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save')]"))
            )
            save_button.click()
            time.sleep(2)
        except:
            pass

        # Handle "Turn on Notifications" popup
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            time.sleep(2)
        except:
            pass
    except Exception as e:
        print(f"Login failed: {e}")
        raise

# --- CHECK BRAND ---
def check_brand(brand_name):
    try:
        wait = WebDriverWait(driver, 15)

        # find search input
        search_box = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Search input'] | //input[@placeholder='Search']"))
        )
        search_box.clear()
        search_box.send_keys(brand_name)
        time.sleep(3)

        # wait for dropdown results
        results = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='dialog']//a"))
        )

        profile_link = None
        for el in results:
            href = el.get_attribute("href") or ""
            if re.match(r"https://www\.instagram\.com/[^/]+/?$", href):
                profile_link = el
                break

        if not profile_link:
            print(f"❌ No valid profile found for {brand_name}")
            return "Not Found", "Not Found"

        # click profile safely
        driver.execute_script("arguments[0].click();", profile_link)
        time.sleep(5)

        # check verification
        verified = "Not Verified ❌"
        try:
            driver.find_element(By.XPATH, "//header//*[name()='svg' and @aria-label='Verified'] | //header//span[@aria-label='Verified']")
            verified = "Verified ✅"
        except NoSuchElementException:
            pass

        # follower count
        followers = "Not Found"
        try:
            follower_el = wait.until(
                EC.presence_of_element_located((By.XPATH, "//header//a[contains(@href,'/followers')]//span"))
            )
            followers = follower_el.text.strip()
        except:
            try:
                meta_content = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute("content")
                match = re.search(r"([\d,.]+[KMB]?) Followers", meta_content)
                if match:
                    followers = match.group(1)
            except:
                pass

        return verified, followers

    except Exception as e:
        print(f"⚠️ Error with {brand_name}: {e}")
        return "Error", str(e)

# --- MAIN WORKFLOW ---
def main():
    try:
        insta_login("Drone_Krishna", "@Kkpal2001@")  # ⚠️ Replace with IG creds

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
