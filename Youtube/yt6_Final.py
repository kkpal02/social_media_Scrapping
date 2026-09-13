import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Input / Output paths
input_file = r"D:\Youtube\brand_all.xlsx"     # <-- change to your file
output_file = r"D:\Youtube\youtube_verified_results8.xlsx"

# Read brand names
df = pd.read_excel(input_file)
brands = df.iloc[:, 0].tolist()

# Setup Chrome
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

results = []
channel_links = []

for brand in brands:
    brand_lower = str(brand).lower()
    status = "Channel Not Found"
    channel_url = "N/A"

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

        # Try first channel result
        try:
            first_channel = driver.find_element(By.XPATH, "(//a[@id='main-link'])[1]")
            channel_url = first_channel.get_attribute("href")
            driver.get(channel_url)
            time.sleep(3)
        except:
            # If first channel fails, look for hrefs with /@
            all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/@')]")
            matched = None
            for link in all_links:
                href = link.get_attribute("href")
                text = link.text.strip().lower()
                if href and (brand_lower in href.lower() or brand_lower in text):
                    matched = href
                    break

            if matched:
                channel_url = matched
                driver.get(channel_url)
                time.sleep(3)

        # If we reached a channel, check header <h1 aria-label="Brand, Verified">
        if channel_url != "N/A":
            try:
                header = driver.find_element(By.XPATH, "//h1[@class='dynamicTextViewModelH1']")
                aria_label = header.get_attribute("aria-label")
                if aria_label and "verified" in aria_label.lower():
                    status = "Verified"
                else:
                    status = "Not Verified"
            except NoSuchElementException:
                status = "Not Verified"

    except Exception as e:
        print(f"⚠️ Error with {brand}: {e}")
        status = "Error"

    results.append(status)
    channel_links.append(channel_url)

# Save to Excel with channel links
df["Channel Link"] = channel_links
df["YouTube Verification"] = results
df.to_excel(output_file, index=False)

driver.quit()
print("✅ Done! Results saved at:", output_file)
