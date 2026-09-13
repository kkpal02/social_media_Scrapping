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
# 🔹 Iterate through companies
# =======================
for index, row in df.iterrows():
    company_name = str(row[company_column])
    company_slug = company_name.strip().replace(" ", "-").lower()

    url = f"https://www.linkedin.com/company/{company_slug}"
    driver.get(url)
    time.sleep(3)

    status = "Unverified ❌"
    try:
        driver.find_element(By.CSS_SELECTOR, "a[aria-label='Verified']")
        status = "Verified ✅"
    except NoSuchElementException:
        status = "Unverified ❌"

    print(company_name, ":", status)
    df.at[index, "Status"] = status

# Save results
output_file = r"D:\Linedln\linkedin_verified_results.xlsx"
df.to_excel(output_file, index=False)

driver.quit()
print(f"\n✅ Done! Results saved to: {output_file}")
