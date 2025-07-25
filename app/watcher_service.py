# app/watcher_service.py
import os
import sys
import threading
import time
import json
import requests
from bs4 import BeautifulSoup

# Add watcher directory to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'watcher'))

FLARESOLVERR_URL = "http://localhost:8191/v1"

class WatcherService:
    def __init__(self):
        self.is_running = False
        self.watcher_thread = None
        self.stop_event = threading.Event()
        self.next_check_time = None
        self.current_interval = None
        self.flaresolverr_session = None
        
    def start(self):
        """Start the watcher service in a background thread"""
        if self.is_running:
            return False, "Watcher is already running"
            
        self.stop_event.clear()
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        self.is_running = True
        return True, "Watcher started successfully"
        
    def stop(self):
        """Stop the watcher service"""
        if not self.is_running:
            return False, "Watcher is not running"
            
        self.stop_event.set()
        self.is_running = False
        return True, "Watcher stopped successfully"
        
    def status(self):
        """Get current watcher status"""
        status_data = {
            "is_running": self.is_running,
            "status": "Running" if self.is_running else "Stopped"
        }
        
        if self.is_running and self.next_check_time:
            remaining = max(0, int(self.next_check_time - time.time()))
            status_data["countdown"] = remaining
            status_data["next_check"] = self.next_check_time
            status_data["interval"] = self.current_interval
        
        return status_data
    
    def _load_config(self):
        """Load configuration from config.json"""
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _load_products(self):
        """Load products from products.json"""
        products_path = os.path.join(os.path.dirname(__file__), "..", "watcher", "products.json")
        try:
            with open(products_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    
    def _send_telegram_message(self, text: str):
        """Send a Telegram message"""
        config = self._load_config()
        token = config.get("telegram_token")
        chat_id = config.get("telegram_chat_id")
        
        if not token or not chat_id:
            return  # Telegram is not configured
            
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                print(f"[ERROR] Telegram send failed: {response.text}")
        except Exception as e:
            print(f"[ERROR] Telegram exception: {e}")
    
    def _ensure_session(self):
        """Ensure FlareSolverr session exists"""
        if not hasattr(self, 'flaresolverr_session') or not self.flaresolverr_session:
            try:
                payload = {
                    "cmd": "sessions.create",
                    "session": "vaurioajoneuvo_watcher"
                }
                resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=30)
                if resp.ok and resp.json().get("status") == "ok":
                    self.flaresolverr_session = "vaurioajoneuvo_watcher"
                    print("[INFO] Created FlareSolverr session for persistent access")
                else:
                    print(f"[WARNING] Failed to create FlareSolverr session: {resp.text}")
            except Exception as e:
                print(f"[WARNING] Could not create FlareSolverr session: {e}")
                self.flaresolverr_session = None
    
    def _fetch_product_data(self, url):
        """Fetch product data using FlareSolverr"""
        self._ensure_session()
        
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000
        }
        
        # Use session if available
        if self.flaresolverr_session:
            payload["session"] = self.flaresolverr_session
            
        try:
            resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=70)
            resp.raise_for_status()
            html = resp.json()["solution"]["response"]
        except Exception as e:
            raise Exception(f"Flaresolverr error: {e}")
            
        # Check if we got a CAPTCHA page instead of the product page
        if "captcha" in html.lower() or "recaptcha" in html.lower():
            raise Exception("Website is showing CAPTCHA - automated access temporarily blocked")
            
        soup = BeautifulSoup(html, "html.parser")
        price_tag = soup.find("p", class_="price")
        if not price_tag:
            # Try alternative price selectors
            price_tag = soup.find("span", class_="price") or soup.find("div", class_="price")
            if not price_tag:
                # Look for any element containing price-related text
                price_elements = soup.find_all(text=lambda text: text and ("€" in text or "euro" in text.lower()))
                if price_elements:
                    raise Exception(f"Price element structure changed - found {len(price_elements)} price-like elements")
                else:
                    raise Exception("Price not found - page structure may have changed")
            
        price = self._parse_price(price_tag.get_text(strip=True))
        name_tag = soup.find("h1", class_="name")
        name = name_tag.get_text(strip=True) if name_tag else url
        return {"price": price, "name": name}
    
    def _parse_price(self, price_str):
        """Extract digits from price string, e.g. "3 000 €" -> 3000"""
        import re
        price = re.sub(r"[^0-9]", "", price_str)
        return int(price) if price else 0
    
    def _parse_interval(self, interval_str):
        """Parse interval string and return seconds"""
        import random
        
        try:
            s = str(interval_str).strip().lower()
            
            # Handle random intervals like "random:60-300"
            if s.startswith('random:'):
                range_part = s[7:]  # Remove "random:" prefix
                if '-' in range_part:
                    min_val, max_val = range_part.split('-', 1)
                    min_seconds = int(min_val.strip())
                    max_seconds = int(max_val.strip())
                    return random.randint(min_seconds, max_seconds)
                else:
                    # Single value after random: - use it as max with 60 as min
                    max_seconds = int(range_part.strip())
                    return random.randint(60, max_seconds)
            
            # Handle minute notation
            elif s.endswith('m') or s.endswith('min'):
                return int(s.rstrip('min')) * 60
            
            # Handle plain seconds
            else:
                return int(s)
                
        except Exception:
            return 60  # Default to 60 seconds
    
    def _watch_loop(self):
        """Main watcher loop"""
        print("[INFO] Watcher service started")
        
        while not self.stop_event.is_set():
            try:
                config = self._load_config()
                products = self._load_products()
                
                if not products:
                    print("[INFO] No products to watch")
                    time.sleep(30)
                    continue
                
                print(f"[INFO] Checking {len(products)} products...")
                
                for item in products:
                    if self.stop_event.is_set():
                        break
                        
                    url = item["url"]
                    target = item["target_price"]
                    
                    try:
                        data = self._fetch_product_data(url)
                        price = data["price"]
                        name = item.get("name", data["name"])
                        
                        if price < target:  # Changed from <= to < for "below" target
                            print(f"[ALERT] {name}: {price} € (dropped below target {target} €)")
                            self._send_telegram_message(
                                f"PRICE ALERT: {name} has dropped to {price} € (below your target of {target} €)!\n{url}"
                            )
                        else:
                            print(f"[INFO] {name}: {price} € (target {target} €)")
                            
                    except Exception as e:
                        print(f"[WARNING] {item.get('name', item['url'])} - {e}")
                
                # Parse interval and wait
                interval_str = config.get("interval", "60")
                interval_seconds = self._parse_interval(interval_str)
                self.current_interval = interval_seconds
                self.next_check_time = time.time() + interval_seconds
                
                print(f"[INFO] Waiting {interval_seconds} seconds until next check...")
                
                # Wait with ability to stop and countdown tracking
                for i in range(interval_seconds):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[ERROR] Watcher loop error: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying
        
        print("[INFO] Watcher service stopped")

# Global watcher instance
watcher_service = WatcherService()
