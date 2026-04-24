from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import time
from datetime import datetime

def get_wired_articles(limit=50):
    options = Options()
    #options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    driver.get("https://www.wired.com")
    driver.save_screenshot('/app/output/bukti_scraping.png')
    wait = WebDriverWait(driver, 10)
    semua_link = driver.find_elements(By.TAG_NAME, "a")
    
    story_urls = []

    for link in semua_link:
        href = link.get_attribute("href")

        if not href:
            continue

        if (
        href.startswith("https://www.wired.com/story/")
        and "#" not in href
        and "?" not in href
        and len(href.split("/")) > 5  # filter slug pendek
        and href not in story_urls
    ):story_urls.append(href)

    print(f"Ditemukan {len(story_urls)} artikel")

# ==============================
# TAHAP 2 - Scrape tiap artikel
# ==============================
    hasil = []

    for url in story_urls:
        try:
            print(f"Scraping: {url}")
            driver.get(url)

        # Tunggu judul muncul dulu
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="ContentHeaderHed"]')
        ))

            title = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ContentHeaderHed"]')))
            print(title.text)

            description = driver.find_element(By.CSS_SELECTOR, "[class*='SplitScreenContentHeaderDek']")
            print(description.text)

            author = driver.find_element(By.CSS_SELECTOR, '[data-testid="BylineName"]')
            print(repr(author.text))

            # Scrapped at
            scrapped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            hasil.append({
            "title": title.text.strip(),
            "url": url,
            "description": description.text.strip(),
            "author": author.text.strip(),
            "scrapped_at": scrapped_at
        })

            print(f"✅ Berhasil: {title.text[:50]}...")
            time.sleep(2)  # jeda antar request biar tidak kena block

        except Exception as e:
            print(f"⚠️ Gagal scrape {url}: {e}")
            continue

    driver.quit()
    return hasil

def save_to_json(data, filename="articles.json"):
    now = datetime.now()
    results = [
    {
        "session_id": now.strftime("wired_session_%Y%m%d_%H%M%S"),
        "timestamp": now.isoformat(),
        "articles_count": len(data),
        "articles": data
    }
]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nData berhasil disimpan ke {filename}")

if __name__ == "__main__":
    data = get_wired_articles()
    save_to_json(data, "/app/output/articles.json")