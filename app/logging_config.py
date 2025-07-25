# app/logging_config.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'product_url'):
            log_entry['product_url'] = record.product_url
        if hasattr(record, 'target_price'):
            log_entry['target_price'] = record.target_price
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging(app):
    """Setup comprehensive logging for the application"""
    
    # Create logs directory
    log_dir = os.path.join(app.root_path, '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, mode=0o750)
    
    # Remove default Flask handler to avoid duplicates
    app.logger.handlers.clear()
    
    # Set logging level based on environment
    log_level = logging.DEBUG if app.debug else logging.INFO
    app.logger.setLevel(log_level)
    
    # JSON Formatter for structured logs
    json_formatter = JSONFormatter()
    
    # Standard formatter for readable logs
    standard_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    )
    
    # 1. APPLICATION LOG - General application events
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, 'application.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(standard_formatter)
    app.logger.addHandler(app_handler)
    
    # 2. SECURITY LOG - Authentication, authorization, security events
    security_handler = RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=20  # Keep more security logs
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(json_formatter)
    
    # Create security logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False  # Don't propagate to root logger
    
    # 3. API LOG - All API requests and responses
    api_handler = RotatingFileHandler(
        os.path.join(log_dir, 'api.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(json_formatter)
    
    # Create API logger
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    api_logger.propagate = False
    
    # 4. WATCHER LOG - Price monitoring activities
    watcher_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'watcher.log'),
        when='midnight',
        interval=1,
        backupCount=30  # Keep 30 days
    )
    watcher_handler.setLevel(logging.INFO)
    watcher_handler.setFormatter(standard_formatter)
    
    # Create watcher logger
    watcher_logger = logging.getLogger('watcher')
    watcher_logger.setLevel(logging.INFO)
    watcher_logger.addHandler(watcher_handler)
    watcher_logger.propagate = False
    
    # 5. ERROR LOG - All errors and exceptions
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=20
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    app.logger.addHandler(error_handler)
    
    # 6. CONSOLE LOG for development
    if app.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(standard_formatter)
        app.logger.addHandler(console_handler)
    
    # Set proper permissions on log files
    for handler in [app_handler, security_handler, api_handler, watcher_handler, error_handler]:
        if hasattr(handler, 'stream') and hasattr(handler.stream, 'name'):
            try:
                os.chmod(handler.stream.name, 0o640)
            except (AttributeError, OSError):
                pass
    
    app.logger.info("Logging system initialized")
    return {
        'security': security_logger,
        'api': api_logger,
        'watcher': watcher_logger
    }


# Additional logging utilities
def log_security_event(logger, event_type, user_id=None, ip_address=None, details=None):
    """Log security-related events"""
    extra = {
        'user_id': user_id,
        'ip_address': ip_address,
        'event_type': event_type
    }
    if details:
        extra.update(details)
    
    logger.warning(f"Security event: {event_type}", extra=extra)

def log_api_request(logger, method, endpoint, user_id=None, ip_address=None, 
                   user_agent=None, status_code=None, response_time=None):
    """Log API requests and responses"""
    extra = {
        'method': method,
        'endpoint': endpoint,
        'user_id': user_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'status_code': status_code,
        'response_time': response_time
    }
    
    logger.info(f"{method} {endpoint} - {status_code}", extra=extra)

def log_watcher_event(logger, event_type, product_url=None, target_price=None, 
                     current_price=None, details=None):
    """Log price watcher events"""
    extra = {
        'event_type': event_type,
        'product_url': product_url,
        'target_price': target_price,
        'current_price': current_price
    }
    if details:
        extra.update(details)
    
    message = f"Watcher event: {event_type}"
    if product_url:
        message += f" for {product_url}"
    
    logger.info(message, extra=extra)
