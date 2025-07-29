#!/usr/bin/env python3
"""
Initialize configuration files for the price monitoring application
Run this script after deploying to a new server.
"""

import os
import json

def create_config_file():
    """Create default config.json if it doesn't exist"""
    config_path = "config.json"
    
    if os.path.exists(config_path):
        print(f"✅ {config_path} already exists")
        return
    
    default_config = {
        "interval": "600",  # 10 minutes
        "telegram_token": "",
        "telegram_chat_id": ""
    }
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        print(f"✅ Created {config_path} with default settings")
        print("   Edit this file to configure your Telegram bot settings")
    except Exception as e:
        print(f"❌ Error creating {config_path}: {e}")

def create_products_file():
    """Create default watcher/products.json if it doesn't exist"""
    watcher_dir = "watcher"
    products_path = os.path.join(watcher_dir, "products.json")
    
    # Create watcher directory if it doesn't exist
    if not os.path.exists(watcher_dir):
        try:
            os.makedirs(watcher_dir, mode=0o755)
            print(f"✅ Created {watcher_dir} directory")
        except Exception as e:
            print(f"❌ Error creating {watcher_dir} directory: {e}")
            return
    
    if os.path.exists(products_path):
        print(f"✅ {products_path} already exists")
        return
    
    default_products = []
    
    try:
        with open(products_path, "w", encoding="utf-8") as f:
            json.dump(default_products, f, indent=2)
        print(f"✅ Created {products_path} (empty product list)")
        print("   Add products through the web interface")
    except Exception as e:
        print(f"❌ Error creating {products_path}: {e}")

def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = "logs"
    
    if os.path.exists(logs_dir):
        print(f"✅ {logs_dir} directory already exists")
        return
    
    try:
        os.makedirs(logs_dir, mode=0o750)
        print(f"✅ Created {logs_dir} directory")
    except Exception as e:
        print(f"❌ Error creating {logs_dir} directory: {e}")

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"⚠️  {env_path} does not exist")
        print("   Copy .env.example to .env and configure your settings")
        return
    
    required_vars = ['SECRET_KEY', 'USERNAME', 'PASSWORD']
    missing_vars = []
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
            for var in required_vars:
                if f"{var}=" not in content or f"{var}=" in content and content.split(f"{var}=")[1].split('\n')[0].strip() == "":
                    missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing or empty variables in {env_path}: {', '.join(missing_vars)}")
        else:
            print(f"✅ {env_path} has all required variables")
            
    except Exception as e:
        print(f"❌ Error reading {env_path}: {e}")

def main():
    print("🚀 Initializing Price Monitoring Application")
    print("=" * 50)
    
    create_config_file()
    create_products_file() 
    create_logs_directory()
    check_env_file()
    
    print("\n" + "=" * 50)
    print("✅ Initialization complete!")
    print("\nNext steps:")
    print("1. Configure your .env file with SECRET_KEY, USERNAME, PASSWORD")
    print("2. Add Telegram bot settings to config.json (optional)")
    print("3. Start the application with: ./start.sh")

if __name__ == "__main__":
    main()
