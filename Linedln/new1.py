import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# =======================
# 🔹 Your LinkedIn credentials
# =======================
LINKEDIN_EMAIL = "krishnakantapal1912@gmail.com"
LINKEDIN_PASSWORD = "@Kkpal1912@"

# Path to your Excel file
excel_file = r"D:\Linedln\subs.xlsx"

# Load Excel file
df = pd.read_excel(excel_file)
company_column = df.columns[0]
df["Status"] = ""

# Setup Selenium with webdriver-manager
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
# chrome_options.add_argument("--headless")  # uncomment if you don’t want browser UI

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# =======================
# 🔹 Login to LinkedIn
# =======================
driver.get("https://www.linkedin.com/login")
time.sleep(3)

driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
driver.find_element(By.XPATH, "//button[@type='submit']").click()

time.sleep(5)  # wait for login to complete

# =======================
# 🔹 Helper function to generate company URLs
# =======================
def generate_company_urls(company_name):
    """Generate multiple URL variations for a company name"""
    # Clean and normalize the company name
    company_slug = company_name.strip().replace(" ", "-").lower()
    
    urls = []
    
    # Basic slug
    urls.append(f"https://www.linkedin.com/company/{company_slug}/")
    
    # Remove hyphens
    urls.append(f"https://www.linkedin.com/company/{company_slug.replace('-', '')}/")
    
    # Special case: Remove "Limited" from the end for some companies
    if company_slug.endswith('-limited'):
        without_limited = company_slug.replace('-limited', '')
        urls.append(f"https://www.linkedin.com/company/{without_limited}/")
    
    # Handle common company suffixes
    if 'limited' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('limited', 'ltd')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('limited', '')}/")
    
    if 'corporation' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('corporation', 'corp')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('corporation', '')}/")
    
    if 'incorporated' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('incorporated', 'inc')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('incorporated', '')}/")
    
    # Handle special characters
    clean_slug = company_slug.replace('&', 'and').replace('+', 'plus').replace('%', 'percent').replace('@', 'at')
    if clean_slug != company_slug:
        urls.append(f"https://www.linkedin.com/company/{clean_slug}/")
    
    # Handle numbers at the beginning (like "24 Mantra")
    if company_slug[0].isdigit():
        # Try with and without the number
        without_number = '-'.join(company_slug.split('-')[1:]) if '-' in company_slug else company_slug[1:]
        if without_number:
            urls.append(f"https://www.linkedin.com/company/{without_number}/")
    
    # Remove duplicate URLs
    return list(dict.fromkeys(urls))

# =======================
# 🔹 Iterate through companies
# =======================
total_companies = len(df)
print(f"\n🚀 Starting verification check for {total_companies} companies...")
print("="*60)

for index, row in df.iterrows():
    company_name = str(row[company_column])
    
    print(f"\n[{index + 1}/{total_companies}] Checking: {company_name}")
    
    # Generate multiple URL variations dynamically for any company
    urls_to_try = generate_company_urls(company_name)
    
    page_loaded = False
    for url in urls_to_try:
        print(f"   Trying URL: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Check if page loaded successfully (not redirected to unavailable page)
        if "unavailable" not in driver.current_url and "unavailable" not in driver.title.lower():
            print(f"   ✅ Page loaded successfully: {driver.current_url}")
            print(f"   📄 Page Title: {driver.title}")
            page_loaded = True
            break
        else:
            print(f"   ❌ Page not found: {driver.title}")
    
    if not page_loaded:
        print(f"   ⚠️ Could not find valid LinkedIn page for {company_name}")
        status = "Page Not Found ❌"
        df.at[index, "Status"] = status
        continue

    status = "Unverified ❌"
    verification_method = ""

    # ✅ For the first company only: dump HTML for debugging
    if index == 0:
        print("\n========== DEBUG HTML (first 3000 chars) ==========")
        print(driver.page_source[:3000])
        print("\n✅ Pausing for 15s so you can inspect above output...")
        time.sleep(15)

    # 🔍 Comprehensive verification detection for all companies
    verification_found = False
    verification_method = ""
    
    # Method 1: Check for aria-label containing 'Verified' (most common)
    try:
        driver.find_element(By.XPATH, "//*[contains(@aria-label, 'Verified')]")
        verification_found = True
        verification_method = "aria-label"
    except NoSuchElementException:
        pass
    
    # Method 2: Check for SVG with title 'Verified'
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//svg[@title='Verified']")
            verification_found = True
            verification_method = "svg-title"
        except NoSuchElementException:
            pass
    
    # Method 3: Check for text containing 'Verified' (but exclude empty elements)
    if not verification_found:
        try:
            # Look for elements with actual visible text containing 'Verified'
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Verified')]")
            for elem in elements:
                if elem.text.strip() and 'verified' in elem.text.lower():
                    verification_found = True
                    verification_method = "text-content"
                    break
        except NoSuchElementException:
            pass
    
    # Method 4: Check for CSS selector with aria-label
    if not verification_found:
        try:
            driver.find_element(By.CSS_SELECTOR, "[aria-label*='Verified']")
            verification_found = True
            verification_method = "css-aria-label"
        except NoSuchElementException:
            pass
    
    # Method 5: Check for verification badge in company header
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//div[contains(@class, 'org-top-card')]//*[contains(@aria-label, 'Verified')]")
            verification_found = True
            verification_method = "company-header"
        except NoSuchElementException:
            pass
    
    # Method 6: Check for any element with 'verified' in class name
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//*[contains(@class, 'verified')]")
            verification_found = True
            verification_method = "class-name"
        except NoSuchElementException:
            pass
    
    # Method 7: Check for verification icon in the company name area
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//h1//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
            verification_found = True
            verification_method = "company-name-area"
        except NoSuchElementException:
            pass
    
    # Method 8: Look for LinkedIn's specific verification patterns
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//*[contains(@class, 'org-verified-badge') or contains(@class, 'verified-badge') or contains(@class, 'verification-badge')]")
            verification_found = True
            verification_method = "linkedin-specific"
        except NoSuchElementException:
            pass
    
    # Method 9: Look for data attributes
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//*[@data-test-id='verified-badge' or @data-verification='true' or contains(@data-testid, 'verified')]")
            verification_found = True
            verification_method = "data-attributes"
        except NoSuchElementException:
            pass
    
    # Method 10: Look for checkmark symbols
    if not verification_found:
        try:
            driver.find_element(By.XPATH, "//*[contains(@class, 'check') or contains(@class, 'tick') or contains(@class, 'badge')]//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
            verification_found = True
            verification_method = "checkmark-symbols"
        except NoSuchElementException:
            pass
    
    # Method 11: More specific verification badge detection (exclude empty elements)
    if not verification_found:
        try:
            # Look for elements that are actually verification badges, not just any text
            verification_elements = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified') or contains(@class, 'verified') or contains(@class, 'verification')]")
            for elem in verification_elements:
                # Check if it's a real verification badge (not empty code elements)
                if (elem.get_attribute('aria-label') and 'verified' in elem.get_attribute('aria-label').lower()) or \
                   (elem.get_attribute('title') and 'verified' in elem.get_attribute('title').lower()) or \
                   (elem.get_attribute('class') and any(keyword in elem.get_attribute('class').lower() for keyword in ['verified', 'verification', 'badge'])):
                    verification_found = True
                    verification_method = "specific-badge-detection"
                    break
        except NoSuchElementException:
            pass
    
    if verification_found:
        status = "Verified ✅"
        print(f"   ✅ {company_name}: {status} (Method: {verification_method})")
    else:
        status = "Unverified ❌"
        print(f"   ❌ {company_name}: {status}")
    
    df.at[index, "Status"] = status

# Save results
output_file = r"D:\Linedln\linkedin_verified_results2.xlsx"
df.to_excel(output_file, index=False)

# Summary
verified_count = len(df[df["Status"] == "Verified ✅"])
unverified_count = len(df[df["Status"] == "Unverified ❌"])

print("\n" + "="*60)
print("📊 VERIFICATION SUMMARY")
print("="*60)
print(f"✅ Verified Companies: {verified_count}")
print(f"❌ Unverified Companies: {unverified_count}")
print(f"📈 Total Companies Checked: {total_companies}")
print(f"📁 Results saved to: {output_file}")
print("="*60)

driver.quit()
print(f"\n🎉 Verification check completed successfully!")
