import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Input / Output paths
input_file = r"D:\Youtube\brand_all.xlsx"     # <-- change to your file
output_file = r"D:\Youtube\youtube_verified_results5.xlsx"

# Read brand names
df = pd.read_excel(input_file)
brands = df.iloc[:, 0].tolist()

# Setup Chrome
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

results = []

for brand in brands:
    try:
        driver.get("https://www.youtube.com/")
        time.sleep(2)

        # Search brand
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.clear()
        search_box.send_keys(brand)
        search_box.send_keys(Keys.RETURN)

        # Wait for results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "contents"))
        )
        time.sleep(2)

        # Click on first channel result (not video)
        try:
            first_channel = driver.find_element(
                By.XPATH, "(//a[@id='main-link'])[1]"
            )
            channel_url = first_channel.get_attribute("href")
            driver.get(channel_url)
            time.sleep(3)
        except:
            results.append("Channel Not Found")
            continue

        # Check for verification badge on channel header
        try:
            driver.find_element(By.XPATH, "//ytd-badge-supported-renderer//yt-icon[@icon='check_circle']")
            results.append("Verified")
        except NoSuchElementException:
            results.append("Not Verified")

    except Exception as e:
        print(f"⚠️ Error with {brand}: {e}")
        results.append("Error")

# Save to Excel
df["YouTube Verification"] = results
df.to_excel(output_file, index=False)

driver.quit()
print("✅ Done! Results saved at:", output_file)
