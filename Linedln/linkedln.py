import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Path to your Excel file
excel_file = "D:\Linedln\Company.xlsx"
df = pd.read_excel(excel_file)
df["Status"] = ""

# Setup Selenium with webdriver-manager
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
# chrome_options.add_argument("--headless")  # optional

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

for index, row in df.iterrows():
    company_name = row["CompanyName"]
    company_slug = company_name.strip().replace(" ", "-").lower()  

    url = f"https://www.linkedin.com/company/{company_slug}/about/"
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

df.to_excel("linkedin_verified_results.xlsx", index=False)
driver.quit()
