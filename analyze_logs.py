#!/usr/bin/env python3
"""
Simple log analysis script for the price monitoring application
Usage: python analyze_logs.py
"""

import json
import os
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def analyze_security_logs():
    """Analyze security.log for suspicious patterns"""
    
    log_file = 'logs/security.log'
    if not os.path.exists(log_file):
        print("No security.log found")
        return
    
    failed_logins = defaultdict(int)
    suspicious_ips = Counter()
    auth_events = []
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                
                event_type = log_entry.get('event_type', '')
                ip = log_entry.get('ip_address', 'unknown')
                
                if 'auth_attempt_login' in event_type:
                    auth_events.append((log_entry.get('timestamp'), ip))
                    
                if event_type == 'unauthorized_access':
                    failed_logins[ip] += 1
                    
                if log_entry.get('status_code') in [403, 429]:
                    suspicious_ips[ip] += 1
                    
            except json.JSONDecodeError:
                continue
    
    print("=== SECURITY ANALYSIS ===")
    print(f"Total authentication events: {len(auth_events)}")
    
    if failed_logins:
        print(f"\nFailed access attempts by IP:")
        for ip, count in failed_logins.items():
            print(f"  {ip}: {count} attempts")
    
    if suspicious_ips:
        print(f"\nSuspicious activity by IP:")
        for ip, count in suspicious_ips.most_common(10):
            print(f"  {ip}: {count} suspicious requests")

def analyze_api_logs():
    """Analyze api.log for usage patterns"""
    
    log_file = 'logs/api.log'
    if not os.path.exists(log_file):
        print("No api.log found")
        return
    
    endpoint_usage = Counter()
    slow_requests = []
    error_counts = Counter()
    users = set()
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                
                endpoint = log_entry.get('endpoint', 'unknown')
                endpoint_usage[endpoint] += 1
                
                response_time = log_entry.get('response_time', 0)
                if response_time > 2000:  # Requests over 2 seconds
                    slow_requests.append((endpoint, response_time))
                
                status_code = log_entry.get('status_code', 200)
                if status_code >= 400:
                    error_counts[status_code] += 1
                
                user_id = log_entry.get('user_id')
                if user_id and user_id != 'anonymous':
                    users.add(user_id)
                    
            except json.JSONDecodeError:
                continue
    
    print("\n=== API ANALYSIS ===")
    print(f"Total unique users: {len(users)}")
    print("Most used endpoints:")
    for endpoint, count in endpoint_usage.most_common(10):
        print(f"  {endpoint}: {count} requests")
    
    if slow_requests:
        print(f"\nSlow requests (>2s): {len(slow_requests)}")
        for endpoint, response_time in sorted(slow_requests, key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {endpoint}: {response_time:.0f}ms")
    
    if error_counts:
        print(f"\nHTTP Error codes:")
        for code, count in error_counts.most_common():
            print(f"  {code}: {count} errors")

def analyze_watcher_logs():
    """Analyze watcher.log for monitoring patterns"""
    
    log_file = 'logs/watcher.log'
    if not os.path.exists(log_file):
        print("No watcher.log found")
        return
    
    price_checks = 0
    alerts_sent = 0
    errors = 0
    products = set()
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'Price check completed:' in line:
                price_checks += 1
            elif 'ALERT:' in line:
                alerts_sent += 1
            elif 'Error checking' in line:
                errors += 1
            elif 'Starting price check for' in line:
                try:
                    # Extract number of products
                    parts = line.split(' products')
                    if parts:
                        num_str = parts[0].split()[-1]
                        if num_str.isdigit():
                            products.add(int(num_str))
                except:
                    pass
    
    print("\n=== WATCHER ANALYSIS ===")
    print(f"Total price check cycles: {price_checks}")
    print(f"Total alerts sent: {alerts_sent}")
    print(f"Total errors: {errors}")
    if products:
        print(f"Products being monitored: {max(products) if products else 0}")

def analyze_errors():
    """Analyze errors.log for application issues"""
    
    log_file = 'logs/errors.log'
    if not os.path.exists(log_file):
        print("No errors.log found")
        return
    
    error_types = Counter()
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                error_type = log_entry.get('error_type', 'Unknown')
                error_types[error_type] += 1
            except json.JSONDecodeError:
                continue
    
    print("\n=== ERROR ANALYSIS ===")
    if error_types:
        print("Error types:")
        for error_type, count in error_types.most_common():
            print(f"  {error_type}: {count} occurrences")
    else:
        print("No errors logged")

if __name__ == "__main__":
    print("Log Analysis Report")
    print("=" * 50)
    
    analyze_security_logs()
    analyze_api_logs() 
    analyze_watcher_logs()
    analyze_errors()
    
    print("\n" + "=" * 50)
    print("Analysis complete")
