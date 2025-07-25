# app/routes.py
import json
from flask import Blueprint, render_template, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
from .watcher_service import watcher_service

main = Blueprint("main", __name__)

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../watcher/products.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config.json")

FLARESOLVERR_URL = "http://localhost:8191/v1"

def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# Global session for API requests
api_flaresolverr_session = None

def ensure_api_session():
    """Ensure FlareSolverr session exists for API requests"""
    global api_flaresolverr_session
    if not api_flaresolverr_session:
        try:
            payload = {
                "cmd": "sessions.create",
                "session": "vaurioajoneuvo_api"
            }
            resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=30)
            if resp.ok and resp.json().get("status") == "ok":
                api_flaresolverr_session = "vaurioajoneuvo_api"
                print("[INFO] Created FlareSolverr session for API access")
            else:
                print(f"[WARNING] Failed to create FlareSolverr API session: {resp.text}")
        except Exception as e:
            print(f"[WARNING] Could not create FlareSolverr API session: {e}")

def fetch_product_data(url):
    ensure_api_session()
    
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    
    # Use session if available
    if api_flaresolverr_session:
        payload["session"] = api_flaresolverr_session
        
    try:
        resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=70)
        resp.raise_for_status()
        html = resp.json()["solution"]["response"]
    except Exception as e:
        return {"error": f"Flaresolverr error: {e}"}
    
    # Check if we got a CAPTCHA page instead of the product page
    if "captcha" in html.lower() or "recaptcha" in html.lower():
        return {"error": "Website is showing CAPTCHA - automated access temporarily blocked"}
        
    soup = BeautifulSoup(html, "html.parser")
    price_tag = soup.find("p", class_="price")
    if not price_tag:
        # Try alternative price selectors
        price_tag = soup.find("span", class_="price") or soup.find("div", class_="price")
        if not price_tag:
            # Look for any element containing price-related text
            price_elements = soup.find_all(text=lambda text: text and ("€" in text or "euro" in text.lower()))
            if price_elements:
                return {"error": f"Price element structure changed - found {len(price_elements)} price-like elements"}
            else:
                return {"error": "Price not found - page structure may have changed"}
                
    price = parse_price(price_tag.get_text(strip=True))
    name_tag = soup.find("h1", class_="name")
    name = name_tag.get_text(strip=True) if name_tag else url
    return {"price": price, "name": name}

def parse_price(price_str):
    # Extract digits from price string, e.g. "3 000 €" -> 3000
    import re
    price = re.sub(r"[^0-9]", "", price_str)
    return int(price) if price else 0

@main.route("/")
def index():
    products = load_products()
    return render_template("index.html", products=products)

# --- API endpoints ---
@main.route("/api/products", methods=["GET"])
def api_get_products():
    return jsonify(load_products())

@main.route("/api/products", methods=["POST"])
def api_add_product():
    data = request.json
    products = load_products()
    # name is optional, can be empty string
    products.append({
        "url": data["url"],
        "target_price": int(data["target_price"]),
        "name": data.get("name", "")
    })
    save_products(products)
    return jsonify({"success": True})

@main.route("/api/products/<int:idx>", methods=["PUT"])
def api_update_product(idx):
    data = request.json
    products = load_products()
    if 0 <= idx < len(products):
        products[idx]["url"] = data["url"]
        products[idx]["target_price"] = int(data["target_price"])
        products[idx]["name"] = data.get("name", "")
        save_products(products)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400

@main.route("/api/products/<int:idx>", methods=["DELETE"])
def api_delete_product(idx):
    products = load_products()
    if 0 <= idx < len(products):
        products.pop(idx)
        save_products(products)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400

@main.route("/api/interval", methods=["GET"])
def api_get_interval():
    config = load_config()
    return jsonify({"interval": config.get("interval", "")})

@main.route("/api/interval", methods=["PUT"])
def api_set_interval():
    data = request.json
    config = load_config()
    config["interval"] = data["interval"]
    save_config(config)
    return jsonify({"success": True})

@main.route("/api/telegram", methods=["GET"])
def api_get_telegram():
    config = load_config()
    return jsonify({
        "telegram_token": config.get("telegram_token", ""),
        "telegram_chat_id": config.get("telegram_chat_id", "")
    })

@main.route("/api/telegram", methods=["PUT"])
def api_set_telegram():
    data = request.json
    config = load_config()
    config["telegram_token"] = data["token"]
    config["telegram_chat_id"] = data["chat_id"]
    save_config(config)
    return jsonify({"success": True})

@main.route("/api/price", methods=["POST"])
def api_get_price():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    result = fetch_product_data(url)
    return jsonify(result)

@main.route("/api/watcher/start", methods=["POST"])
def api_start_watcher():
    success, message = watcher_service.start()
    return jsonify({"success": success, "message": message})

@main.route("/api/watcher/stop", methods=["POST"])
def api_stop_watcher():
    success, message = watcher_service.stop()
    return jsonify({"success": success, "message": message})

@main.route("/api/watcher/status", methods=["GET"])
def api_watcher_status():
    return jsonify(watcher_service.status())