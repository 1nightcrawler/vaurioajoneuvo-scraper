import requests
from bs4 import BeautifulSoup
import json
import time

PRODUCTS_FILE = "products.json"
SESSION_FILE = "session.json"
CHECK_INTERVAL = 600  # in seconds

def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_session():
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        session = json.load(f)
        return session["headers"], session["cookies"]

def fetch_product_data(url, headers, cookies):
    response = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, "html.parser")

    price_tag = soup.find("p", class_="price")
    if not price_tag:
        raise ValueError("Price not found.")
    price = parse_price(price_tag.get_text(strip=True))

    name_tag = soup.find("h1", class_="name")
    name = name_tag.get_text(strip=True) if name_tag else url

    location_tag = soup.find("div", class_="location")
    location = location_tag.get_text(strip=True) if location_tag else "Unknown"

    return {
        "price": price,
        "name": name,
        "location": location
    }

def parse_price(price_str: str) -> int:
    return int(price_str.replace("€", "").replace(" ", "").strip())

def main():
    products = load_products()
    headers, cookies = load_session()

    while True:
        for item in products:
            url = item["url"]
            target = item["target_price"]
            try:
                data = fetch_product_data(url, headers, cookies)
                price = data["price"]
                name = item.get("name") or data["name"]
                location = data["location"]

                if price <= target:
                    print(f"[ALERT] {name}: {price} € (target {target} €)")
                else:
                    print(f"{name}: {price} € (target {target} €)")

            except Exception as e:
                print("[WARNING]", item.get("name", item["url"]), "-", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
