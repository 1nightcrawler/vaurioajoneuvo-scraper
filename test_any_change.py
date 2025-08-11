#!/usr/bin/env python3
"""
Test the "any_change" notification logic by simulating price changes
"""
import json
import os
import sys
import time

def load_products():
    """Load current products"""
    products_file = "watcher/products.json"
    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No products.json found. Please add some products first.")
        return []

def save_products(products):
    """Save products back to file"""
    products_file = "watcher/products.json"
    os.makedirs(os.path.dirname(products_file), exist_ok=True)
    with open(products_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def load_config():
    """Load config"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return {}

def test_any_change_logic():
    """Test the any_change notification logic by modifying product prices"""
    
    print("🧪 Testing 'any_change' notification logic")
    print("=" * 50)
    
    # Check config
    config = load_config()
    notification_mode = config.get('notification_mode', 'below_target')
    print(f"📋 Current notification mode: {notification_mode}")
    
    if notification_mode not in ['any_change', 'both']:
        print("⚠️  Note: Your notification mode is not 'any_change' or 'both'")
        print("   You may not receive notifications for price changes")
        change_mode = input("\n🔧 Change to 'any_change' mode for testing? (y/n): ")
        if change_mode.lower() == 'y':
            config['notification_mode'] = 'any_change'
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            print("✅ Changed notification mode to 'any_change'")
        else:
            print("📝 Continuing with current mode...")
    
    # Load products
    products = load_products()
    if not products:
        print("❌ No products to test with. Add some products first.")
        return
    
    print(f"\n📦 Found {len(products)} products:")
    for i, product in enumerate(products):
        last_price = product.get('last_price', 'Unknown')
        print(f"  {i+1}. {product.get('name', 'Unnamed')} - Target: €{product['target_price']}, Last: €{last_price}")
    
    # Choose product
    try:
        choice = input(f"\n🎯 Choose a product to test (1-{len(products)}) or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return
        
        product_idx = int(choice) - 1
        if product_idx < 0 or product_idx >= len(products):
            print("❌ Invalid choice")
            return
    except ValueError:
        print("❌ Invalid input")
        return
    
    product = products[product_idx]
    original_price = product.get('last_price')
    target_price = product['target_price']
    
    print(f"\n🎯 Testing with: {product.get('name', 'Unnamed Product')}")
    print(f"📊 Target price: €{target_price}")
    print(f"💰 Current last_price: €{original_price if original_price else 'None'}")
    
    # Backup original data
    backup_file = "watcher/products_backup.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"💾 Backed up products to {backup_file}")
    
    try:
        # Test 1: Set initial price if none exists
        if not original_price:
            test_price = target_price + 100
            product['last_price'] = test_price
            save_products(products)
            print(f"\n🔧 Set initial price to €{test_price}")
            print("⏳ Waiting 2 seconds...")
            time.sleep(2)
        
        # Test 2: Price increase (should trigger any_change)
        new_price = (original_price or target_price) + 50
        print(f"\n🧪 TEST 1: Price INCREASE")
        print(f"💰 Changing price: €{product['last_price']} → €{new_price}")
        print("📝 This should trigger 'any_change' notification")
        
        product['last_price'] = new_price
        save_products(products)
        
        print("✅ Price changed in products.json")
        print("🚀 Now start your watcher to see if notification is sent!")
        print("📱 Check Telegram for notification...")
        
        input("\n⏸️  Press Enter when you've checked for notifications...")
        
        # Test 3: Price decrease above target (should trigger any_change)
        new_price2 = new_price - 30
        print(f"\n🧪 TEST 2: Price DECREASE (but above target)")
        print(f"💰 Changing price: €{new_price} → €{new_price2}")
        print("📝 This should trigger 'any_change' notification")
        
        product['last_price'] = new_price2
        save_products(products)
        
        print("✅ Price changed in products.json")
        print("🚀 Watcher should detect this change on next cycle!")
        
        input("\n⏸️  Press Enter when you've checked for notifications...")
        
        # Test 4: Price drops below target (should trigger both notifications if mode is 'both')
        if notification_mode == 'both':
            below_target_price = target_price - 20
            print(f"\n🧪 TEST 3: Price drops BELOW target")
            print(f"💰 Changing price: €{new_price2} → €{below_target_price}")
            print("📝 This should trigger BOTH 'any_change' AND 'below_target' notifications")
            
            product['last_price'] = below_target_price
            save_products(products)
            
            print("✅ Price changed in products.json")
            print("🚀 Watcher should detect this change and send notifications!")
            
            input("\n⏸️  Press Enter when you've checked for notifications...")
    
    finally:
        # Restore original data
        print(f"\n🔄 Restoring original products from backup...")
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_products = json.load(f)
        save_products(original_products)
        os.remove(backup_file)
        print("✅ Products restored")
    
    print("\n🎉 Testing completed!")
    print("📝 Summary:")
    print("   - Modified product prices to simulate changes")
    print("   - Your watcher should have detected these changes")
    print("   - Check your Telegram for notifications")
    print("   - Original data has been restored")

if __name__ == "__main__":
    print("🔍 'Any Change' Notification Logic Tester")
    print("This will modify product prices to test notification logic")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("config.json"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if products exist
    if not os.path.exists("watcher/products.json"):
        print("❌ No products found. Please add some products through the web interface first.")
        sys.exit(1)
    
    test_any_change_logic()
