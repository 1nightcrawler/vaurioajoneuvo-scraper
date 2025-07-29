# app/routes.py
import json
import os
import requests
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from bs4 import BeautifulSoup
from .watcher_service import watcher_service
from .auth import User
from .validators import is_valid_url, is_valid_price, is_valid_name, sanitize_string
from . import limiter

main = Blueprint("main", __name__)

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "../watcher/products.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config.json")

# Get FlareSolverr URL from environment
FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191/v1')

def load_products():
    """Load products, creating empty list if missing"""
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create empty products file if it doesn't exist
        default_products = []
        # Ensure directory exists
        os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
        save_products(default_products)
        return default_products
    except Exception as e:
        # Log error and return empty list
        print(f"Error loading products: {e}")
        return []

def save_products(products):
    """Save products to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving products: {e}")
        raise

def load_config():
    """Load configuration, creating default if missing"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config if it doesn't exist
        default_config = {
            "interval": "600",  # 10 minutes default
            "telegram_token": "",
            "telegram_chat_id": ""
        }
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(default_config)
        return default_config
    except Exception as e:
        # Log error and return minimal config
        print(f"Error loading config: {e}")
        return {"interval": "600"}

def save_config(config):
    """Save configuration to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
        raise

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

# --- Authentication routes ---
@main.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == "POST":
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Basic input validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html', error='Username and password are required.')
        
        # Authenticate user
        user = User.authenticate(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'error')
            return render_template('login.html', error='Invalid username or password.')
    
    return render_template('login.html')

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route("/")
@login_required
def index():
    products = load_products()
    return render_template("index.html", products=products)

# --- API endpoints ---
@main.route("/api/products", methods=["GET"])
@login_required
def api_get_products():
    return jsonify(load_products())

@main.route("/api/products", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def api_add_product():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    url = data.get("url", "").strip()
    target_price = data.get("target_price")
    name = sanitize_string(data.get("name", ""))
    
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL format"}), 400
    
    if not is_valid_price(target_price):
        return jsonify({"error": "Invalid target price"}), 400
    
    if name and not is_valid_name(name):
        return jsonify({"error": "Invalid product name"}), 400
    
    products = load_products()
    
    # Check for duplicate URLs
    if any(p["url"] == url for p in products):
        return jsonify({"error": "Product with this URL already exists"}), 400
    
    products.append({
        "url": url,
        "target_price": int(target_price),
        "name": name
    })
    save_products(products)
    return jsonify({"success": True})

@main.route("/api/products/<int:idx>", methods=["PUT"])
@login_required
@limiter.limit("20 per minute")
def api_update_product(idx):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate input
    url = data.get("url", "").strip()
    target_price = data.get("target_price")
    name = sanitize_string(data.get("name", ""))
    
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL format"}), 400
    
    if not is_valid_price(target_price):
        return jsonify({"error": "Invalid target price"}), 400
    
    if name and not is_valid_name(name):
        return jsonify({"error": "Invalid product name"}), 400
    
    products = load_products()
    if 0 <= idx < len(products):
        # Check for duplicate URLs (excluding current product)
        if any(i != idx and p["url"] == url for i, p in enumerate(products)):
            return jsonify({"error": "Product with this URL already exists"}), 400
            
        products[idx]["url"] = url
        products[idx]["target_price"] = int(target_price)
        products[idx]["name"] = name
        save_products(products)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400

@main.route("/api/products/<int:idx>", methods=["DELETE"])
@login_required
@limiter.limit("30 per minute")
def api_delete_product(idx):
    products = load_products()
    if 0 <= idx < len(products):
        products.pop(idx)
        save_products(products)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400

@main.route("/api/interval", methods=["GET"])
@login_required
def api_get_interval():
    config = load_config()
    return jsonify({"interval": config.get("interval", "")})

@main.route("/api/interval", methods=["PUT"])
@login_required
@limiter.limit("10 per minute")
def api_set_interval():
    data = request.json
    if not data or "interval" not in data:
        return jsonify({"error": "Missing interval parameter"}), 400
    
    interval = sanitize_string(str(data["interval"]))
    if len(interval) > 50:  # Reasonable limit
        return jsonify({"error": "Interval string too long"}), 400
    
    config = load_config()
    config["interval"] = interval
    save_config(config)
    return jsonify({"success": True})

@main.route("/api/telegram", methods=["GET"])
@login_required
def api_get_telegram():
    # Get from environment variables instead of config file for security
    return jsonify({
        "telegram_token": os.environ.get("TELEGRAM_TOKEN", ""),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", "")
    })

@main.route("/api/telegram", methods=["PUT"])
@login_required
@limiter.limit("5 per minute")
def api_set_telegram():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Note: In production, these should be set via environment variables
    # This endpoint is kept for backward compatibility but discouraged
    token = sanitize_string(data.get("token", ""))
    chat_id = sanitize_string(data.get("chat_id", ""))
    
    config = load_config()
    config["telegram_token"] = token
    config["telegram_chat_id"] = chat_id
    save_config(config)
    return jsonify({"success": True, "warning": "Consider using environment variables for production"})

@main.route("/api/price", methods=["POST"])
@login_required
@limiter.limit("10 per minute")  # More restrictive as this makes external requests
def api_get_price():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    url = data.get("url", "").strip()
    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL format"}), 400
        
    try:
        result = fetch_product_data(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/watcher/start", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_start_watcher():
    success, message = watcher_service.start()
    return jsonify({"success": success, "message": message})

@main.route("/api/watcher/stop", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def api_stop_watcher():
    success, message = watcher_service.stop()
    return jsonify({"success": success, "message": message})

@main.route("/api/watcher/status", methods=["GET"])
@login_required
def api_watcher_status():
    return jsonify(watcher_service.status())

@main.route("/api/notifications", methods=["GET"])
@login_required
@limiter.limit("10 per minute")
def api_get_notifications():
    """Get notification settings"""
    try:
        config = load_config()
        return jsonify({
            "success": True,
            "notification_mode": config.get("notification_mode", "below_target")
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load notification settings: {str(e)}"}), 500

@main.route("/api/notifications", methods=["PUT"])
@login_required
@limiter.limit("5 per minute")
def api_set_notifications():
    """Update notification settings"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        mode = data.get("notification_mode", "").strip()
        valid_modes = ["any_change", "below_target", "both", "none"]
        
        if mode not in valid_modes:
            return jsonify({"error": f"Invalid notification mode. Must be one of: {', '.join(valid_modes)}"}), 400
        
        config = load_config()
        config["notification_mode"] = mode
        save_config(config)
        
        return jsonify({"success": True, "message": "Notification settings updated"})
        
    except Exception as e:
        return jsonify({"error": f"Failed to update notification settings: {str(e)}"}), 500