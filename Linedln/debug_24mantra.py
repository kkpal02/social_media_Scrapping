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

def debug_24mantra():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Login to LinkedIn
        print("🔐 Logging into LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        # Navigate to 24 Mantra Organic profile
        print("🔍 Navigating to 24 Mantra Organic - India LinkedIn profile...")
        company_slug = "24-mantra-organic-india"
        url = f"https://www.linkedin.com/company/{company_slug}/"
        driver.get(url)
        time.sleep(5)
        
        print(f"📄 Current URL: {driver.current_url}")
        print(f"📄 Page Title: {driver.title}")
        
        # Check each verification method individually
        print("\n🔍 Testing each verification method individually:")
        print("="*60)
        
        methods = [
            ("Method 1: aria-label containing 'Verified'", "//*[contains(@aria-label, 'Verified')]"),
            ("Method 2: SVG with title 'Verified'", "//svg[@title='Verified']"),
            ("Method 3: text containing 'Verified'", "//*[contains(text(), 'Verified')]"),
            ("Method 4: CSS selector with aria-label", "[aria-label*='Verified']"),
            ("Method 5: company header verification", "//div[contains(@class, 'org-top-card')]//*[contains(@aria-label, 'Verified')]"),
            ("Method 6: class name with 'verified'", "//*[contains(@class, 'verified')]"),
            ("Method 7: company name area verification", "//h1//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]"),
            ("Method 8: LinkedIn specific patterns", "//*[contains(@class, 'org-verified-badge') or contains(@class, 'verified-badge') or contains(@class, 'verification-badge')]"),
            ("Method 9: data attributes", "//*[@data-test-id='verified-badge' or @data-verification='true' or contains(@data-testid, 'verified')]"),
            ("Method 10: checkmark symbols", "//*[contains(@class, 'check') or contains(@class, 'tick') or contains(@class, 'badge')]//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
        ]
        
        verification_found = False
        for method_name, xpath in methods:
            try:
                elements = driver.find_elements(By.XPATH, xpath) if not xpath.startswith("[") else driver.find_elements(By.CSS_SELECTOR, xpath)
                if elements:
                    print(f"✅ {method_name}: FOUND {len(elements)} element(s)")
                    verification_found = True
                    # Show details of found elements
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        try:
                            print(f"   Element {i+1}: Tag={elem.tag_name}, Text='{elem.text}', Aria-label='{elem.get_attribute('aria-label')}', Title='{elem.get_attribute('title')}', Class='{elem.get_attribute('class')}'")
                        except:
                            print(f"   Element {i+1}: Found but couldn't get details")
                else:
                    print(f"❌ {method_name}: NOT FOUND")
            except Exception as e:
                print(f"❌ {method_name}: ERROR - {e}")
        
        print("\n" + "="*60)
        if verification_found:
            print("🚨 ISSUE FOUND: Script incorrectly reports as VERIFIED")
            print("🔍 This suggests there are false positive elements being detected")
        else:
            print("✅ CORRECT: No verification elements found - should be UNVERIFIED")
        
        # Look for any elements that might be causing false positives
        print("\n🔍 Searching for any elements containing 'verified' (case insensitive):")
        all_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verified') or contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verified') or contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verified') or contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verified')]")
        
        print(f"Found {len(all_elements)} elements with 'verified' in any attribute:")
        for i, elem in enumerate(all_elements[:10]):  # Show first 10
            try:
                print(f"  {i+1}. Tag: {elem.tag_name}")
                print(f"     Text: '{elem.text}'")
                print(f"     Aria-label: '{elem.get_attribute('aria-label')}'")
                print(f"     Title: '{elem.get_attribute('title')}'")
                print(f"     Class: '{elem.get_attribute('class')}'")
                print("     " + "-"*40)
            except:
                print(f"  {i+1}. Element found but couldn't get details")
        
        print("\n⏳ Pausing for 10 seconds for manual inspection...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
    
    finally:
        driver.quit()
        print("\n✅ Browser closed. Debug complete!")

if __name__ == "__main__":
    debug_24mantra()

