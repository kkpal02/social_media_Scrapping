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
excel_file = r"D:\Linedln\Company.xlsx"

# Load Excel file
df = pd.read_excel(excel_file)
company_column = df.columns[0]
df["Status"] = ""
df["Followers"] = ""   # <-- Added column

# Setup Selenium with webdriver-manager
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
# chrome_options.add_argument("--headless")  # uncomment to run without browser UI

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
    company_slug = company_name.strip().replace(" ", "-").lower()
    urls = []

    urls.append(f"https://www.linkedin.com/company/{company_slug}/")
    urls.append(f"https://www.linkedin.com/company/{company_slug.replace('-', '')}/")

    if company_slug.endswith('-limited'):
        without_limited = company_slug.replace('-limited', '')
        urls.append(f"https://www.linkedin.com/company/{without_limited}/")

    if 'limited' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('limited', 'ltd')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('limited', '')}/")

    if 'corporation' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('corporation', 'corp')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('corporation', '')}/")

    if 'incorporated' in company_slug:
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('incorporated', 'inc')}/")
        urls.append(f"https://www.linkedin.com/company/{company_slug.replace('incorporated', '')}/")

    clean_slug = company_slug.replace('&', 'and').replace('+', 'plus').replace('%', 'percent').replace('@', 'at')
    if clean_slug != company_slug:
        urls.append(f"https://www.linkedin.com/company/{clean_slug}/")

    if company_slug[0].isdigit():
        without_number = '-'.join(company_slug.split('-')[1:]) if '-' in company_slug else company_slug[1:]
        if without_number:
            urls.append(f"https://www.linkedin.com/company/{without_number}/")

    return list(dict.fromkeys(urls))

# =======================
# 🔹 Iterate through companies
# =======================
total_companies = len(df)
print(f"\n🚀 Starting verification + follower count check for {total_companies} companies...")
print("="*60)

for index, row in df.iterrows():
    company_name = str(row[company_column])
    print(f"\n[{index + 1}/{total_companies}] Checking: {company_name}")

    urls_to_try = generate_company_urls(company_name)
    page_loaded = False

    for url in urls_to_try:
        print(f"   Trying URL: {url}")
        driver.get(url)
        time.sleep(3)

        if "unavailable" not in driver.current_url and "unavailable" not in driver.title.lower():
            print(f"   ✅ Page loaded successfully: {driver.current_url}")
            page_loaded = True
            break
        else:
            print(f"   ❌ Page not found: {driver.title}")

    if not page_loaded:
        print(f"   ⚠️ Could not find valid LinkedIn page for {company_name}")
        df.at[index, "Status"] = "Page Not Found ❌"
        df.at[index, "Followers"] = "N/A"
        continue

    status = "Unverified ❌"

    # =======================
    # 🔹 Extract follower count
    # =======================
    try:
        followers_elem = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'org-top-card-summary-info-list__info-item')][contains(normalize-space(.), 'followers')]"
        )
        followers_text = followers_elem.text.strip().replace("\n", " ")
        print(f"   👥 Followers: {followers_text}")
        df.at[index, "Followers"] = followers_text
    except NoSuchElementException:
        print("   ⚠️ Followers not found")
        df.at[index, "Followers"] = "N/A"

    # =======================
    # 🔹 Check verification badge
    # =======================
    verification_found = False
    try:
        driver.find_element(By.XPATH, "//*[contains(@aria-label, 'Verified')]")
        verification_found = True
    except NoSuchElementException:
        pass

    if verification_found:
        status = "Verified ✅"
        print(f"   ✅ {company_name}: {status}")
    else:
        status = "Unverified ❌"
        print(f"   ❌ {company_name}: {status}")

    df.at[index, "Status"] = status

# =======================
# 🔹 Save results
# =======================
output_file = r"D:\Linedln\linkedin_verified_results_with_followers_3012.xlsx"
df.to_excel(output_file, index=False)

print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"✅ Verified Companies: {len(df[df['Status'] == 'Verified ✅'])}")
print(f"❌ Unverified Companies: {len(df[df['Status'] == 'Unverified ❌'])}")
print(f"📈 Total Companies Checked: {total_companies}")
print(f"📁 Results saved to: {output_file}")
print("="*60)

driver.quit()
print("\n🎉 Check completed successfully!")
