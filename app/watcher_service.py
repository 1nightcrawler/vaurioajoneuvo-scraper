# app/watcher_service.py
import os
import sys
import threading
import time
import json
import requests
import logging
from bs4 import BeautifulSoup
from .logging_config import log_watcher_event

# Add watcher directory to path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'watcher'))

FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191/v1')

class WatcherService:
    def __init__(self):
        self.is_running = False
        self.watcher_thread = None
        self.stop_event = threading.Event()
        self.next_check_time = None
        self.current_interval = None
        self.flaresolverr_session = None
        self.logger = logging.getLogger('watcher')
        self.price_history = {}  # Track previous prices for change detection
        
    def start(self):
        """Start the watcher service in a background thread"""
        if self.is_running:
            self.logger.warning("Attempted to start watcher that's already running")
            return False, "Watcher is already running"
            
        self.stop_event.clear()
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        self.is_running = True
        self.logger.info("Watcher service started successfully")
        return True, "Watcher started successfully"
        
    def stop(self):
        """Stop the watcher service"""
        if not self.is_running:
            self.logger.warning("Attempted to stop watcher that's not running")
            return False, "Watcher is not running"
            
        self.stop_event.set()
        self.is_running = False
        self.logger.info("Watcher service stopped")
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
        except FileNotFoundError:
            # Create default config if it doesn't exist
            default_config = {
                "interval": "600",  # 10 minutes default
                "telegram_token": "",
                "telegram_chat_id": "",
                "notification_mode": "below_target"  # New setting
            }
            self._create_default_config(config_path, default_config)
            return default_config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {"interval": "600", "notification_mode": "below_target"}  # Fallback
    
    def _create_default_config(self, config_path, default_config):
        """Create default config.json file"""
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
            self.logger.info(f"Created default config file at {config_path}")
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")
    
    def _load_products(self):
        """Load products from products.json"""
        products_path = os.path.join(os.path.dirname(__file__), "..", "watcher", "products.json")
        
        # Ensure watcher directory exists
        watcher_dir = os.path.dirname(products_path)
        if not os.path.exists(watcher_dir):
            try:
                os.makedirs(watcher_dir, mode=0o755)
                self.logger.info(f"Created watcher directory at {watcher_dir}")
            except Exception as e:
                self.logger.error(f"Error creating watcher directory: {e}")
                return []
        
        try:
            with open(products_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Create empty products file if it doesn't exist
            default_products = []
            self._create_default_products(products_path, default_products)
            return default_products
        except Exception as e:
            self.logger.error(f"Error loading products: {e}")
            return []
    
    def _create_default_products(self, products_path, default_products):
        """Create default products.json file"""
        try:
            with open(products_path, "w", encoding="utf-8") as f:
                json.dump(default_products, f, indent=2)
            self.logger.info(f"Created default products file at {products_path}")
        except Exception as e:
            self.logger.error(f"Error creating default products file: {e}")
    
    def _send_telegram_message(self, text: str):
        """Send a Telegram message"""
        # Get credentials from environment variables first, fallback to config
        token = os.environ.get('TELEGRAM_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Fallback to config file if env vars not set
        if not token or not chat_id:
            config = self._load_config()
            token = token or config.get("telegram_token")
            chat_id = chat_id or config.get("telegram_chat_id")
        
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
        
    def _cleanup_sessions(self):
        """Clean up crashed FlareSolverr sessions"""
        try:
            # Destroy all sessions
            payload = {"cmd": "sessions.destroy", "session": "vaurioajoneuvo_watcher"}
            requests.post(FLARESOLVERR_URL, json=payload, timeout=10)
            payload = {"cmd": "sessions.destroy", "session": "vaurioajoneuvo_api"}  
            requests.post(FLARESOLVERR_URL, json=payload, timeout=10)
            self.flaresolverr_session = None
        except:
            pass
    
    def _watch_loop(self):
        """Main watcher loop with enhanced logging"""
        self.logger.info("Watcher service started")
        
        while not self.stop_event.is_set():
            try:
                config = self._load_config()
                products = self._load_products()
                
                if not products:
                    self.logger.info("No products to watch, sleeping...")
                    time.sleep(30)
                    continue
                
                self.logger.info(f"Starting price check for {len(products)} products")
                
                alerts_sent = 0
                errors_count = 0
                
                for item in products:
                    if self.stop_event.is_set():
                        break
                        
                    url = item["url"]
                    target = item["target_price"]
                    product_name = item.get("name", "Unknown Product")
                    
                    try:
                        start_time = time.time()
                        data = self._fetch_product_data(url)
                        fetch_time = time.time() - start_time
                        
                        price = data["price"]
                        name = item.get("name", data["name"])
                        
                        # Get previous price for change detection
                        previous_price = self.price_history.get(url, None)
                        self.price_history[url] = price
                        
                        # Determine notification mode
                        notification_mode = config.get("notification_mode", "below_target")
                        
                        log_watcher_event(
                            self.logger,
                            'price_check',
                            product_url=url,
                            target_price=target,
                            current_price=price,
                            details={
                                'product_name': name,
                                'fetch_time': fetch_time,
                                'price_difference': price - target,
                                'previous_price': previous_price,
                                'notification_mode': notification_mode
                            }
                        )
                        
                        # Check for notifications based on mode
                        should_notify = False
                        alert_message = ""
                        
                        if notification_mode == "any_change" and previous_price is not None and price != previous_price:
                            # Notify on any price change
                            change = price - previous_price
                            direction = "increased" if change > 0 else "decreased"
                            should_notify = True
                            alert_message = f"💰 PRICE CHANGE: {name} {direction} from €{previous_price} to €{price} (target: €{target})\n{url}"
                            
                        elif notification_mode == "below_target" and price < target:
                            # Notify only when below target (current behavior)
                            should_notify = True
                            alert_message = f"🎯 PRICE ALERT: {name} has dropped to €{price} (below your target of €{target})!\n{url}"
                            
                        elif notification_mode == "both":
                            # Notify on any change OR below target
                            if previous_price is not None and price != previous_price:
                                change = price - previous_price
                                direction = "increased" if change > 0 else "decreased"
                                should_notify = True
                                alert_message = f"💰 PRICE CHANGE: {name} {direction} from €{previous_price} to €{price} (target: €{target})\n{url}"
                            elif price < target:
                                should_notify = True
                                alert_message = f"🎯 PRICE ALERT: {name} has dropped to €{price} (below your target of €{target})!\n{url}"
                        
                        # notification_mode == "none" means no notifications
                        
                        if should_notify:
                            self.logger.info(f"ALERT: {alert_message.split(':', 1)[1].split(chr(10))[0].strip()}")
                            log_watcher_event(
                                self.logger,
                                'price_alert',
                                product_url=url,
                                target_price=target,
                                current_price=price,
                                details={
                                    'product_name': name, 
                                    'alert_type': 'price_change' if 'CHANGE' in alert_message else 'price_drop',
                                    'previous_price': previous_price,
                                    'notification_mode': notification_mode
                                }
                            )
                            self._send_telegram_message(alert_message)
                            alerts_sent += 1
                        else:
                            self.logger.debug(f"Price check: {name} = €{price} (target: €{target}, previous: €{previous_price})")
                            
                    except Exception as e:
                        errors_count += 1
                        self.logger.error(
                            f"Error checking {product_name}: {str(e)}",
                            extra={
                                'product_url': url, 
                                'target_price': target,
                                'product_name': product_name
                            },
                            exc_info=True
                        )
                        log_watcher_event(
                            self.logger,
                            'price_check_error',
                            product_url=url,
                            target_price=target,
                            details={
                                'product_name': product_name,
                                'error': str(e)
                            }
                        )
                
                self.logger.info(
                    f"Price check completed: {len(products)} products checked, "
                    f"{alerts_sent} alerts sent, {errors_count} errors"
                )
                
                # Parse interval and wait
                interval_str = config.get("interval", "60")
                interval_seconds = self._parse_interval(interval_str)
                self.current_interval = interval_seconds
                self.next_check_time = time.time() + interval_seconds
                
                self.logger.info(f"Next check in {interval_seconds} seconds")
                
                # Wait with ability to stop
                for i in range(interval_seconds):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Watcher loop error: {str(e)}", exc_info=True)
                time.sleep(30)  # Wait 30 seconds before retrying
        
        self.logger.info("Watcher service stopped")

# Global watcher instance
watcher_service = WatcherService()
