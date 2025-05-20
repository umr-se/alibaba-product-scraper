from flask import Flask, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from chrome_setup import create_chrome_driver
import time
import json

app = Flask(__name__)

def search_alibaba_products():
    driver = None

    try:
        driver = create_chrome_driver()
        print("Opening Alibaba.com...")
        driver.get("https://www.alibaba.com")
        time.sleep(1)

        # Accept cookies if prompted
        try:
            cookie_btn = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.ui-cookie-disclaimer__button"))
            )
            cookie_btn.click()
            print("Accepted cookies")
        except Exception as e:
            print(f"Cookie consent skipped or error: {str(e)}")

        # Locate and submit search
        print("Locating search box...")
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-bar-input"))
        )
        print("Typing search query...")
        search_box.send_keys("Samsung Electronics")
        time.sleep(1)
        search_box.send_keys(Keys.ENTER)
        print("Search submitted for Samsung Electronics...")

        categories = ["Samsung Electronics", "Samsung Products"]
        product_data = []
        seen = set()

        for category in categories:
            print(f"\nSearching for category: {category}")
            search_box = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-bar-input"))
            )
            search_box.clear()
            search_box.send_keys(category)
            time.sleep(1)
            search_box.send_keys(Keys.ENTER)
            time.sleep(3)

            scroll_pause_time = 2
            last_height = driver.execute_script("return document.body.scrollHeight")

            while True:
                card_elements = driver.find_elements(By.CSS_SELECTOR, "div.card-info")

                for card in card_elements:
                    try:
                        # Extract title and link
                        title_link_elem = card.find_element(By.CSS_SELECTOR, "h2.search-card-e-title a")
                        title = title_link_elem.text.strip()
                        link = title_link_elem.get_attribute("href")

                        # Extract price
                        price_elem = card.find_element(By.CSS_SELECTOR, "div.search-card-e-price-main")
                        price = price_elem.text.strip()

                        identifier = f"{title}-{price}-{link}"

                        if identifier not in seen and title and "$" in price:
                            seen.add(identifier)
                            product_data.append({
                                "title": title,
                                "price": price,
                                "link": link
                            })

                        if len(product_data) >= 100:
                            break
                    except Exception:
                        continue

                if len(product_data) >= 100:
                    break

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)

                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("No more results to load.")
                    break
                last_height = new_height

        # Write to JSON file
        print("Writing data to search_prices.json...")
        with open("search_prices.json", "w", encoding="utf-8") as f:
            json.dump(product_data, f, ensure_ascii=False, indent=4)

        print("Data written to JSON file successfully.")
        return product_data

    except Exception as e:
        print(f"Main process error: {str(e)}")
        return []
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

@app.route('/')
def home():
    count = search_alibaba_products()
    return jsonify({
        "status": "success" if count else "error",
        "prices_found": len(count),
        "message": "Search completed successfully!" if count else "Search failed",
        "file": "search_prices.json"
    })

@app.route('/download_prices')
def download_prices():
    try:
        return send_file("search_prices.json", as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)