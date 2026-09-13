"""
linkedln_with_login.py
- Reads company names from first column of Excel (D:\Linedln\Company.xlsx)
- Logs into LinkedIn with provided credentials
- Checks company /about/ page for a[aria-label="Verified"]
- Writes result to D:\Linedln\linkedin_verified_results.xlsx

Requirements:
pip install selenium webdriver-manager pandas openpyxl
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
HEADLESS = False   # set True to run without browser UI (might be more detectable)
MIN_DELAY = 0.5
MAX_DELAY = 1.0
# -----------------------------------

def human_delay(a=MIN_DELAY, b=MAX_DELAY):
    time.sleep(random.uniform(a, b))

def get_credentials():
    """
    Preferred: set environment vars LINKEDIN_USER and LINKEDIN_PASS before running.
    Fallback: interactive prompt (console).
    """
    user = os.environ.get("LINKEDIN_USER")
    pwd = os.environ.get("LINKEDIN_PASS")
    if user and pwd:
        return user, pwd

    # fallback to interactive input (safer than hardcoding)
    user = input("LinkedIn email/username: ").strip()
    pwd = input("LinkedIn password: ").strip()
    return user, pwd

def linkedin_login(driver, username, password, timeout=20):
    """Login to LinkedIn using provided credentials. Returns True on success."""
    driver.get("https://www.linkedin.com/login")
    wait = WebDriverWait(driver, timeout)

    try:
        # wait for email field and password field
        email_elem = wait.until(EC.presence_of_element_located((By.NAME, "session_key")))
        pass_elem = wait.until(EC.presence_of_element_located((By.NAME, "session_password")))

        email_elem.clear()
        email_elem.send_keys(username)
        human_delay(0.4, 0.8)

        pass_elem.clear()
        pass_elem.send_keys(password)
        human_delay(0.4, 0.8)

        # submit - find sign in button and click
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit' or contains(., 'Sign in')]")
        submit_btn.click()

        # wait until either login fails or main UI appears (search box / profile avatar / nav)
        # We'll wait for presence of the top nav or company search input
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "global-nav-search")),  # newer linkedin id
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.global-nav__me-photo"))
            )
        )
        # small delay to stabilize
        human_delay()
        return True

    except TimeoutException:
        # Could be 2FA / captcha / wrong creds / page changed
        print("⚠️ Login probably failed or LinkedIn requested additional verification (2FA/CAPTCHA).")
        return False
    except Exception as e:
        print("Login error:", e)
        return False

def check_verified_on_company_page(driver, company_slug):
    """Open /company/{slug}/about/ and return True if verified badge exists."""
    base = f"https://www.linkedin.com/company/{company_slug}/about/"
    driver.get(base)
    # short wait for page to load some DOM
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except TimeoutException:
        pass

    # small random delay for realism
    human_delay()

    try:
        driver.find_element(By.CSS_SELECTOR, "a[aria-label='Verified']")
        return True
    except NoSuchElementException:
        return False
    except Exception:
        # fallback: sometimes the badge is rendered differently; treat as unverified
        return False

def normalize_to_slug(name):
    """Basic normalization: replace spaces with '-' and lower. You can customize this if needed."""
    if not isinstance(name, str):
        name = str(name)
    slug = name.strip().replace(" ", "-").lower()
    # remove double hyphens etc.
    slug = "-".join([p for p in slug.split("-") if p])
    return slug

def main():
    # load companies
    df = pd.read_excel(EXCEL_FILE)
    if df.shape[1] == 0:
        print("No columns found in Excel.")
        return

    company_col = df.columns[0]
    df["Status"] = ""

    # chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")

    # install driver & start
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # login
        username, password = get_credentials()
        ok = linkedin_login(driver, username, password)
        if not ok:
            print("Login failed. Exiting. If you see 2FA/captcha, handle it manually in the opened browser session.")
            driver.quit()
            return

        # iterate companies
        for idx, row in df.iterrows():
            company_name = str(row[company_col])
            slug = normalize_to_slug(company_name)

            # Try direct slug first
            verified = check_verified_on_company_page(driver, slug)
            status = "Verified ✅" if verified else "Unverified ❌"

            # If unverified and likely wrong slug, you could add a search fallback here.
            print(f"{company_name} -> {status}")
            df.at[idx, "Status"] = status

            # small human delay between requests
            human_delay(1.2, 3.0)

        # save results
        df.to_excel(OUTPUT_FILE, index=False)
        print(f"\n✅ Done. Results saved to: {OUTPUT_FILE}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
