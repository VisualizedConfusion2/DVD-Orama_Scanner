import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TITLE_RE = re.compile(r"EAN \d+ - (.+?) \| EAN-Search\.org")


def lookup(driver, ean):
    driver.get("https://www.ean-search.org/")
    box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-box"))
    )
    box.clear()
    box.send_keys(ean)
    box.submit()
    WebDriverWait(driver, 10).until(lambda d: ean in d.title or "Not found" in d.page_source)
    match = TITLE_RE.search(driver.title)
    return match.group(1).strip() if match else None


def main():
    options = Options()
    options.add_argument("--headless")
    options.set_preference("dom.webdriver.enabled", False)
    driver = webdriver.Firefox(options=options)

    print("Ready to scan. Press Ctrl+C to quit.")
    try:
        while True:
            ean = input("Scan: ").strip()
            if not ean:
                continue
            title = lookup(driver, ean)
            print(title if title else "Not found")
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
