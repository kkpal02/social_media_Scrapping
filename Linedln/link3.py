"""
linkedln_with_login_fast.py
- Reads company names from first column of Excel (D:\Linedln\Company.xlsx)
- Logs into LinkedIn with provided credentials
- Checks company /about/ page for a[aria-label="Verified"]
- Writes result to D:\Linedln\linkedin_verified_results.xlsx
"""

import os
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ------------- CONFIG -------------
EXCEL_FILE = r"D:\Linedln\Company.xlsx"
OUTPUT_FILE = r"D:\Linedln\linkedin_verified_results.xlsx"
HEADLESS = False   # True = runs without browser window
MIN_DELAY = 0.4
MAX_DELAY = 0.9
# -----------------------------------

def human_delay(a=MIN_DELAY, b=MAX_DELAY):
    time.sleep(random.uniform(a, b))

def get_credentials():
    """Get creds from env vars or prompt."""
    user = os.environ.get("LINKEDIN_USER")
    pwd = os.environ.get("LINKEDIN_PASS")
    if user and pwd:
        return user, pwd
    user = input("LinkedIn email/username: ").strip()
    pwd = input("LinkedIn password: ").strip()
    return user, pwd

def linkedin_login(driver, username, password, timeout=20):
    """Login to LinkedIn."""
    driver.get("https://www.linkedin.com/login")
    wait = WebDriverWait(driver, timeout)
    try:
        email_elem = wait.until(EC.presence_of_element_located((By.NAME, "session_key")))
        pass_elem = wait.until(EC.presence_of_element_located((By.NAME, "session_password")))

        email_elem.clear()
        email_elem.send_keys(username)
        pass_elem.clear()
        pass_elem.send_keys(password)
        human_delay()

        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()

        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "global-nav-search")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.global-nav__me-photo"))
            )
        )
        return True
    except Exception as e:
        print("⚠️ Login failed or needs manual action:", e)
        return False

def check_verified_on_company_page(driver, company_slug):
    """Check company page for verified badge."""
    url = f"https://www.linkedin.com/company/{company_slug}/about/"
    driver.execute_script("window.location.href = arguments[0];", url)

    try:
        WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        pass

    human_delay()

    try:
        driver.find_element(By.CSS_SELECTOR, "a[aria-label='Verified']")
        return True
    except NoSuchElementException:
        return False

def normalize_to_slug(name):
    if not isinstance(name, str):
        name = str(name)
    slug = name.strip().replace(" ", "-").lower()
    slug = "-".join([p for p in slug.split("-") if p])
    return slug

def main():
    df = pd.read_excel(EXCEL_FILE)
    if df.shape[1] == 0:
        print("No columns found in Excel.")
        return

    company_col = df.columns[0]
    df["Status"] = ""

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")

    # 🚀 disable images/css/fonts for speed
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        username, password = get_credentials()
        if not linkedin_login(driver, username, password):
            print("Login failed. Handle manually if needed.")
            return

        for idx, row in df.iterrows():
            company_name = str(row[company_col])
            slug = normalize_to_slug(company_name)

            verified = check_verified_on_company_page(driver, slug)
            status = "Verified ✅" if verified else "Unverified ❌"

            print(f"{company_name} -> {status}")
            df.at[idx, "Status"] = status

            human_delay()  # shorter now

        df.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ Done. Results saved to: {OUTPUT_FILE}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
