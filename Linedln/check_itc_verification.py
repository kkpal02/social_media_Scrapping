import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# LinkedIn credentials
LINKEDIN_EMAIL = "krishnakantapal1912@gmail.com"
LINKEDIN_PASSWORD = "@Kkpal1912@"

def check_itc_verification():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Step 1: Login to LinkedIn
        print("🔐 Logging into LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        # Step 2: Navigate to ITC Hotels Limited profile
        print("🔍 Navigating to ITC Hotels Limited LinkedIn profile...")
        itc_url = "https://www.linkedin.com/company/itc-hotels/"
        driver.get(itc_url)
        time.sleep(5)
        
        print(f"📄 Current URL: {driver.current_url}")
        print(f"📄 Page Title: {driver.title}")
        
        # Step 3: Check for verification status
        print("\n🔍 Checking for verification status...")
        
        verification_found = False
        verification_methods = []
        
        # Method 1: Check for aria-label containing 'Verified'
        try:
            driver.find_element(By.XPATH, "//*[contains(@aria-label, 'Verified')]")
            verification_found = True
            verification_methods.append("aria-label containing 'Verified'")
        except NoSuchElementException:
            pass
        
        # Method 2: Check for SVG with title 'Verified'
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//svg[@title='Verified']")
                verification_found = True
                verification_methods.append("SVG with title 'Verified'")
            except NoSuchElementException:
                pass
        
        # Method 3: Check for text containing 'Verified'
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//*[contains(text(), 'Verified')]")
                verification_found = True
                verification_methods.append("text containing 'Verified'")
            except NoSuchElementException:
                pass
        
        # Method 4: Check for CSS selector with aria-label
        if not verification_found:
            try:
                driver.find_element(By.CSS_SELECTOR, "[aria-label*='Verified']")
                verification_found = True
                verification_methods.append("CSS selector with aria-label")
            except NoSuchElementException:
                pass
        
        # Method 5: Check for verification badge in company header
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//div[contains(@class, 'org-top-card')]//*[contains(@aria-label, 'Verified')]")
                verification_found = True
                verification_methods.append("verification badge in company header")
            except NoSuchElementException:
                pass
        
        # Method 6: Check for any element with 'verified' in class name
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//*[contains(@class, 'verified')]")
                verification_found = True
                verification_methods.append("element with 'verified' in class name")
            except NoSuchElementException:
                pass
        
        # Method 7: Check for verification icon in the company name area
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//h1//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
                verification_found = True
                verification_methods.append("verification icon in company name area")
            except NoSuchElementException:
                pass
        
        # Method 8: Look for LinkedIn's specific verification patterns
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//*[contains(@class, 'org-verified-badge') or contains(@class, 'verified-badge') or contains(@class, 'verification-badge')]")
                verification_found = True
                verification_methods.append("LinkedIn's specific verification patterns")
            except NoSuchElementException:
                pass
        
        # Method 9: Look for data attributes
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//*[@data-test-id='verified-badge' or @data-verification='true' or contains(@data-testid, 'verified')]")
                verification_found = True
                verification_methods.append("data attributes for verification")
            except NoSuchElementException:
                pass
        
        # Method 10: Look for checkmark symbols
        if not verification_found:
            try:
                driver.find_element(By.XPATH, "//*[contains(@class, 'check') or contains(@class, 'tick') or contains(@class, 'badge')]//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
                verification_found = True
                verification_methods.append("checkmark symbols")
            except NoSuchElementException:
                pass
        
        # Display results
        print("\n" + "="*60)
        print("📊 VERIFICATION STATUS RESULTS")
        print("="*60)
        
        if verification_found:
            print("✅ STATUS: VERIFIED")
            print(f"🔍 Detection Method: {', '.join(verification_methods)}")
        else:
            print("❌ STATUS: UNVERIFIED")
            print("🔍 No verification badges found using any detection method")
        
        print(f"🌐 Profile URL: {itc_url}")
        print(f"📄 Page Title: {driver.title}")
        
        # Additional debugging - show all verification-related elements found
        print("\n🔍 DEBUGGING: All verification-related elements found:")
        verification_elements = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified') or contains(text(), 'Verified') or contains(@class, 'verified')]")
        print(f"Found {len(verification_elements)} verification-related elements:")
        
        for i, elem in enumerate(verification_elements[:10]):  # Show first 10
            try:
                print(f"  {i+1}. Tag: {elem.tag_name}")
                print(f"     Text: '{elem.text}'")
                print(f"     Aria-label: '{elem.get_attribute('aria-label')}'")
                print(f"     Title: '{elem.get_attribute('title')}'")
                print(f"     Class: '{elem.get_attribute('class')}'")
                print(f"     Data-testid: '{elem.get_attribute('data-testid')}'")
                print("     " + "-"*40)
            except Exception as e:
                print(f"  {i+1}. Element found but couldn't get details: {e}")
        
        # Show page source snippet for manual inspection
        print("\n🔍 DEBUGGING: Page source snippet (first 2000 characters):")
        print("-" * 60)
        print(driver.page_source[:2000])
        print("-" * 60)
        
        print("\n⏳ Pausing for 10 seconds for manual inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
    
    finally:
        driver.quit()
        print("\n✅ Browser closed. Check complete!")

if __name__ == "__main__":
    check_itc_verification()

