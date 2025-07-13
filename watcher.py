import os
import time
import json
import sys
import random
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Config and product file paths
CONFIG_FILE = "config.json"
PRODUCTS_FILE = "products.json"

# Default interval in seconds
DEFAULT_INTERVAL = 360

# URL for the FlareSolverr service (used to bypass anti-bot protections)
FLARESOLVERR_URL = "http://localhost:8191/v1"  # Change if needed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )
}

def load_config():
    """
    Load configuration from CONFIG_FILE. Returns a dict. If not found, returns empty dict.
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid config format")
            return data
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to load config: {e}" + Style.RESET_ALL)
        return {}

def parse_interval(interval_str):
    """
    Parse interval string. Supports:
      - seconds: '120'
      - minutes: '2m' or '2min'
      - random: 'random:60-300' or 'random:1m-5m'
    Returns a tuple: (is_random, interval or (min, max))
    """
    s = interval_str.strip().lower()
    if s.startswith("random:"):
        range_part = s[7:]
        if '-' not in range_part:
            raise ValueError("Random interval must be in format random:min-max")
        min_s, max_s = range_part.split('-', 1)
        min_sec = parse_single_interval(min_s)
        max_sec = parse_single_interval(max_s)
        if min_sec > max_sec:
            raise ValueError("Random interval min must be <= max")
        return True, (min_sec, max_sec)
    else:
        return False, parse_single_interval(s)

def parse_single_interval(s):
    """
    Parse a single interval string (seconds or minutes). Returns seconds as int.
    """
    s = s.strip().lower()
    if s.endswith("m"):
        return int(float(s[:-1]) * 60)
    if s.endswith("min"):
        return int(float(s[:-3]) * 60)
    return int(float(s))

def get_interval_from_args_or_config():
    """
    Determine interval config from CLI args, config file, or default.
    Returns (is_random, interval or (min, max)).
    """
    # CLI: --interval or -i
    for i, arg in enumerate(sys.argv):
        if arg in ("--interval", "-i") and i + 1 < len(sys.argv):
            try:
                return parse_interval(sys.argv[i + 1])
            except Exception as e:
                print(Fore.RED + f"[ERROR] Invalid interval argument: {e}" + Style.RESET_ALL)
                break
    # Config file
    config = load_config()
    interval_val = config.get("interval")
    if interval_val:
        try:
            return parse_interval(str(interval_val))
        except Exception as e:
            print(Fore.RED + f"[ERROR] Invalid interval in config: {e}" + Style.RESET_ALL)
    # Default
    return False, DEFAULT_INTERVAL

def parse_price(price_str: str) -> int:
    """
    Convert a price string like '2 200 €' to an integer 2200.
    Removes euro sign, spaces, and converts to int.
    """
    return int(price_str.replace("€", "").replace(" ", "").strip())

def fetch_product_data(url: str):
    """
    Fetch product data (name and price) from the given URL using FlareSolverr.
    Returns a dict with 'price' and 'name'.
    Raises an error if the request fails or price is not found.
    """
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    try:
        # Use FlareSolverr to bypass anti-bot protections
        resp = requests.post(FLARESOLVERR_URL, json=payload, timeout=70)
        resp.raise_for_status()
        html = resp.json()["solution"]["response"]
    except Exception as e:
        raise RuntimeError(f"Flaresolverr error: {e}")

    # Parse the HTML to extract price and name
    soup = BeautifulSoup(html, "html.parser")
    price_tag = soup.find("p", class_="price")
    if not price_tag:
        raise ValueError("Price not found.")
    price = parse_price(price_tag.get_text(strip=True))

    name_tag = soup.find("h1", class_="name")
    name = name_tag.get_text(strip=True) if name_tag else url

    return {
        "price": price,
        "name": name,
    }

def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Invalid format")
            return data
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to load product list: {e}" + Style.RESET_ALL)
        return []

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def print_divider():
    print(Fore.BLUE + Style.BRIGHT + "=" * 60 + Style.RESET_ALL)

def print_products_table(products):
    if not products:
        print(Fore.YELLOW + "No products are currently being watched." + Style.RESET_ALL)
        return
    print(Fore.CYAN + Style.BRIGHT + f"{'#':<3} {'Name':<30} {'Target (€)':<12} URL" + Style.RESET_ALL)
    print(Fore.CYAN + "-" * 60 + Style.RESET_ALL)
    for idx, item in enumerate(products, 1):
        name = (item.get('name') or '')[:28] + (".." if len(item.get('name','')) > 28 else "")
        print(f"{idx:<3} {name:<30} {item['target_price']:<12} {item['url']}")

def add_product():
    print_divider()
    print(Fore.GREEN + Style.BRIGHT + "Add a New Product" + Style.RESET_ALL)
    url = input("Enter product URL: ").strip()
    try:
        target = int(input("Enter target price (€): ").strip())
    except ValueError:
        print(Fore.RED + "[ERROR] Invalid price. Please enter a number." + Style.RESET_ALL)
        return
    try:
        data = fetch_product_data(url)
        name = data["name"]
    except Exception as e:
        print(Fore.YELLOW + f"[WARNING] Failed to fetch product data: {e}" + Style.RESET_ALL)
        return
    products = load_products()
    products.append({"url": url, "target_price": target, "name": name})
    save_products(products)
    print(Fore.GREEN + f"[INFO] Added: {name} at target {target} €" + Style.RESET_ALL)

def watch_loop():
    """
    Main loop to periodically check all products' prices.
    Uses interval from config/CLI/default, supports random intervals.
    """
    is_random, interval_val = get_interval_from_args_or_config()
    print_divider()
    if is_random and isinstance(interval_val, tuple):
        min_iv, max_iv = interval_val
        print(Fore.MAGENTA + Style.BRIGHT + f"Watching prices... Random interval: {min_iv}-{max_iv}s. Press Ctrl+C to stop." + Style.RESET_ALL)
    else:
        print(Fore.MAGENTA + Style.BRIGHT + f"Watching prices... Interval: {interval_val}s. Press Ctrl+C to stop." + Style.RESET_ALL)
    while True:
        products = load_products()
        for item in products:
            url = item["url"]
            target = item["target_price"]
            try:
                data = fetch_product_data(url)
                price = data["price"]
                name = item.get("name", data["name"])
                if price <= target:
                    print(Fore.GREEN + Style.BRIGHT + f"[ALERT] {name}: {price} € (target {target} €)" + Style.RESET_ALL)
                else:
                    print(Fore.CYAN + f"{name}: {price} € (target {target} €)" + Style.RESET_ALL)
            except Exception as e:
                print(Fore.YELLOW + f"[WARNING] {item.get('name', item['url'])} - {e}" + Style.RESET_ALL)
        if is_random and isinstance(interval_val, tuple):
            sleep_time = random.randint(min_iv, max_iv)
        else:
            # interval_val is not a tuple here
            sleep_time = int(interval_val) if not isinstance(interval_val, tuple) else 1
        print(Fore.BLUE + f"[INFO] Waiting {sleep_time} seconds before next check..." + Style.RESET_ALL)
        time.sleep(sleep_time)

def remove_product():
    products = load_products()
    if not products:
        print(Fore.YELLOW + "No products to remove." + Style.RESET_ALL)
        return
    print_divider()
    print(Fore.RED + Style.BRIGHT + "Remove a Product" + Style.RESET_ALL)
    print_products_table(products)
    try:
        idx = int(input(Fore.RED + "Enter the number of the product to remove: " + Style.RESET_ALL).strip())
        if not (1 <= idx <= len(products)):
            print(Fore.RED + "Invalid number." + Style.RESET_ALL)
            return
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)
        return
    removed = products.pop(idx - 1)
    save_products(products)
    print(Fore.GREEN + f"Removed: {removed.get('name', removed['url'])}" + Style.RESET_ALL)

def edit_product():
    products = load_products()
    if not products:
        print(Fore.YELLOW + "No products to edit." + Style.RESET_ALL)
        return
    print_divider()
    print(Fore.MAGENTA + Style.BRIGHT + "Edit a Product" + Style.RESET_ALL)
    print_products_table(products)
    try:
        idx = int(input(Fore.MAGENTA + "Enter the number of the product to edit: " + Style.RESET_ALL).strip())
        if not (1 <= idx <= len(products)):
            print(Fore.RED + "Invalid number." + Style.RESET_ALL)
            return
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)
        return
    product = products[idx - 1]
    print(Fore.CYAN + f"Editing: {product.get('name', product['url'])}" + Style.RESET_ALL)
    new_url = input(f"New URL [{product['url']}]: ").strip()
    if new_url:
        product['url'] = new_url
    new_price = input(f"New target price (€) [{product['target_price']}]: ").strip()
    if new_price:
        try:
            product['target_price'] = int(new_price)
        except ValueError:
            print(Fore.RED + "Invalid price. Keeping previous value." + Style.RESET_ALL)
    new_name = input(f"New name [{product.get('name', '')}]: ").strip()
    if new_name:
        product['name'] = new_name
    save_products(products)
    print(Fore.GREEN + "Product updated." + Style.RESET_ALL)

def set_interval():
    """
    Prompt the user to set a new polling interval and save it to config.json.
    """
    print_divider()
    print(Fore.CYAN + Style.BRIGHT + "Set Polling Interval" + Style.RESET_ALL)
    print("Enter interval in seconds (e.g. 120), minutes (e.g. 2m), or random (e.g. random:60-300 or random:1m-5m)")
    new_interval = input("New interval: ").strip()
    if not new_interval:
        print(Fore.YELLOW + "No interval entered. Keeping current setting." + Style.RESET_ALL)
        return
    try:
        # Validate by parsing
        parse_interval(new_interval)
    except Exception as e:
        print(Fore.RED + f"[ERROR] Invalid interval: {e}" + Style.RESET_ALL)
        return
    # Save to config
    config = load_config()
    config["interval"] = new_interval
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(Fore.GREEN + f"Interval set to: {new_interval}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to save config: {e}" + Style.RESET_ALL)

def main():
    while True:
        print_divider()
        print(Fore.BLUE + Style.BRIGHT + "PRICE WATCH MENU" + Style.RESET_ALL)
        products = load_products()
        print_products_table(products)
        print_divider()
        print(Fore.YELLOW + "1." + Style.RESET_ALL, "Add new product")
        print(Fore.YELLOW + "2." + Style.RESET_ALL, "Start watching")
        print(Fore.YELLOW + "3." + Style.RESET_ALL, "Remove product")
        print(Fore.YELLOW + "4." + Style.RESET_ALL, "Edit product")
        print(Fore.YELLOW + "5." + Style.RESET_ALL, "Set polling interval")
        print(Fore.YELLOW + "6." + Style.RESET_ALL, "Exit")
        choice = input(Fore.CYAN + Style.BRIGHT + "Select an option: " + Style.RESET_ALL).strip()
        if choice == "1":
            add_product()
        elif choice == "2":
            try:
                watch_loop()
            except KeyboardInterrupt:
                print(Fore.MAGENTA + "\n[INFO] Stopped watching." + Style.RESET_ALL)
        elif choice == "3":
            remove_product()
        elif choice == "4":
            edit_product()
        elif choice == "5":
            set_interval()
        elif choice == "6":
            confirm = input(Fore.RED + "Are you sure you want to exit? (y/N): " + Style.RESET_ALL).strip().lower()
            if confirm == "y":
                print(Fore.BLUE + "Goodbye!" + Style.RESET_ALL)
                break
        else:
            print(Fore.RED + "Invalid choice. Please select 1, 2, 3, 4, 5, or 6." + Style.RESET_ALL)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "watch":
        print(Fore.MAGENTA + Style.BRIGHT + "[INFO] Running in watch mode (no menu). Press Ctrl+C to stop." + Style.RESET_ALL)
        try:
            watch_loop()
        except KeyboardInterrupt:
            print(Fore.MAGENTA + "\n[INFO] Stopped watching." + Style.RESET_ALL)
    else:
        main()
