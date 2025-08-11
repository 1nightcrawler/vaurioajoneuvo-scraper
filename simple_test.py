#!/usr/bin/env python3
"""
Simple notification test - manually trigger a test notification
"""
import json
import requests
import os

def send_test_notification():
    """Send a test notification using your Telegram settings"""
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return
    
    token = config.get('telegram_token')
    chat_id = config.get('telegram_chat_id')
    
    if not token or not chat_id:
        print("❌ Telegram settings not configured")
        return
    
    # Test message
    message = """🧪 **NOTIFICATION SYSTEM TEST**

🎯 **Product**: Test Item
💰 **Price Change**: €1,200 → €1,150 (-€50)
📊 **Status**: Below target price of €1,200!

🔔 **Notification Mode**: any_change + below_target
⏰ **Time**: Just now

This is a test of your notification system. If you receive this, notifications are working! ✅"""

    # Send via Telegram API
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Test notification sent successfully!")
            print("📱 Check your Telegram for the test message")
        else:
            print(f"❌ Failed to send notification: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

if __name__ == "__main__":
    print("🧪 Simple Notification Test")
    print("=" * 30)
    send_test_notification()
