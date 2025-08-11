#!/usr/bin/env python3
"""
Test script to simulate price changes and test notification system
"""
import json
import os
import sys
import time
import requests
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.watcher_service import watcher_service
except ImportError:
    print("❌ Could not import watcher_service. Make sure you're in the project root.")
    sys.exit(1)

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

def simulate_price_change():
    """Simulate a price change by temporarily modifying product data"""
    products = load_products()
    
    if not products:
        print("❌ No products to test with. Add some products first.")
        return
    
    print("🧪 Testing notification system...")
    print("📋 Current products:")
    for i, product in enumerate(products):
        print(f"  {i+1}. {product.get('name', 'Unnamed')} - Target: €{product['target_price']}")
    
    # Let user choose a product to test with
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
    print(f"💰 Last known price: €{original_price if original_price else 'Unknown'}")
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Price increase (any_change notification)',
            'new_price': target_price + 100,
            'description': 'Price goes UP - should trigger "any_change" notification'
        },
        {
            'name': 'Price decrease above target (any_change notification)', 
            'new_price': target_price + 50,
            'description': 'Price goes DOWN but still above target - should trigger "any_change" notification'
        },
        {
            'name': 'Price drops below target (both notifications)',
            'new_price': target_price - 50,
            'description': 'Price drops BELOW target - should trigger BOTH "any_change" AND "below_target" notifications'
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test {i}: {scenario['name']}")
        print(f"📝 {scenario['description']}")
        print(f"💰 Setting test price to: €{scenario['new_price']}")
        
        # Temporarily modify the product's last price
        product['last_price'] = scenario['new_price']
        save_products(products)
        
        print("⏳ Running watcher check...")
        
        # Simulate a watcher check
        try:
            # This will check the products and send notifications based on price changes
            watcher_service._check_products()
            print("✅ Watcher check completed")
        except Exception as e:
            print(f"❌ Error during watcher check: {e}")
        
        input("\n⏸️  Press Enter to continue to next test...")
    
    # Restore original price
    if original_price:
        product['last_price'] = original_price
        save_products(products)
        print(f"\n🔄 Restored original price: €{original_price}")
    
    print("\n✅ Testing completed!")
    print("📱 Check your Telegram for notifications")

if __name__ == "__main__":
    print("🚀 Notification System Tester")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("config.json"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if products exist
    if not os.path.exists("watcher/products.json"):
        print("❌ No products found. Please add some products through the web interface first.")
        sys.exit(1)
    
    simulate_price_change()
