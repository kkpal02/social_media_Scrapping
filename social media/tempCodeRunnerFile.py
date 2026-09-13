"""
Instagram Brand Verification & Followers Scraper (Updated UI)

Steps:
- Reads brand names from Excel (brand.xlsx, column "Brand")
- Logs into Instagram
- Handles login popups (Save info / Turn on notifications)
- Clicks Search button, searches brand
- Opens first result
- Checks if the account is verified
- Extracts follower count
- Writes result to new Excel file (instagram_results.xlsx)

Requirements:
pip install selenium webdriver-manager pandas openpyxl
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        time.sleep(3)
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
        # Click search button (SVG)
        search_button = driver.find_element(By.XPATH, "//svg[@aria-label='Search']")
        search_button.click()
        time.sleep(2)

        # Find search input
        search_box = driver.find_element(By.XPATH, "//input[@aria-label='Search input']")
        search_box.send_keys(brand_name)
        time.sleep(3)

        # Hit Enter twice to open first result
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        search_box.send_keys(Keys.RETURN)
        time.sleep(7)

        # Check verification
        try:
            driver.find_element(By.XPATH, "//span[@aria-label='Verified']")
            verified = "Verified ✅"
        except:
            verified = "Not Verified ❌"

        # Followers
        try:
            followers = driver.find_element(By.XPATH, "//ul/li[1]//span").text
        except:
            followers = "Not Found"

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
