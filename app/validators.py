# app/validators.py
import re
from urllib.parse import urlparse

def is_valid_url(url):
    """Validate URL format and ensure it's a legitimate web URL"""
    if not url or not isinstance(url, str):
        return False
        
    try:
        # Parse the URL
        result = urlparse(url.strip())
        
        # Check for required components
        if not all([result.scheme, result.netloc]):
            return False
            
        # Only allow http/https
        if result.scheme not in ['http', 'https']:
            return False
            
        # Basic domain validation
        domain = result.netloc.lower()
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:[0-9]+)?$', domain):
            return False
            
        # Reject localhost/internal IPs for security
        if any(local in domain for local in ['localhost', '127.0.0.1', '192.168.', '10.', '172.']):
            return False
            
        return True
        
    except Exception:
        return False

def is_valid_price(price):
    """Validate price is a positive number"""
    try:
        price_num = float(price)
        return price_num > 0 and price_num < 1000000  # Reasonable upper limit
    except (ValueError, TypeError):
        return False

def is_valid_name(name):
    """Validate product name"""
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    if len(name) < 1 or len(name) > 200:
        return False
        
    # Basic sanitization - no special characters that could cause issues
    if re.search(r'[<>"\']', name):
        return False
        
    return True

def sanitize_string(text):
    """Basic string sanitization"""
    if not isinstance(text, str):
        return ""
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()[:200]  # Limit length
