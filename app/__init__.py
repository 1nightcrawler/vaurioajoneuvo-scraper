import os
import time
from flask import Flask, request, g
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Import logging
from .logging_config import setup_logging, log_security_event, log_api_request

# Load environment variables
load_dotenv()

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app():
    app = Flask(__name__)
    
    # Security configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Setup comprehensive logging first
    loggers = setup_logging(app)
    
    # Store loggers in app config for access elsewhere
    app.config['LOGGERS'] = loggers
    
    # Setup request/response logging middleware
    @app.before_request
    def before_request_logging():
        """Log incoming requests and track timing"""
        g.start_time = time.time()
        
        # Get user info
        user_id = current_user.username if current_user.is_authenticated else 'anonymous'
        
        # Log security-relevant requests
        if request.endpoint in ['main.login', 'main.logout']:
            log_security_event(
                loggers['security'],
                f"auth_attempt_{request.endpoint.split('.')[-1]}",
                user_id=user_id,
                ip_address=request.remote_addr,
                details={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            )
    
    @app.after_request
    def after_request_logging(response):
        """Log request completion and security events"""
        
        # Calculate response time
        response_time = (time.time() - g.start_time) * 1000  # Convert to milliseconds
        
        user_id = current_user.username if current_user.is_authenticated else 'anonymous'
        
        # Log API requests
        if request.endpoint and (request.endpoint.startswith('main.api_') or request.endpoint in ['main.login', 'main.logout']):
            log_api_request(
                loggers['api'],
                method=request.method,
                endpoint=request.endpoint,
                user_id=user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                status_code=response.status_code,
                response_time=round(response_time, 2)
            )
        
        # Log security events based on status codes
        if response.status_code == 401:
            log_security_event(
                loggers['security'],
                'unauthorized_access',
                user_id=user_id,
                ip_address=request.remote_addr,
                details={'endpoint': request.endpoint, 'method': request.method}
            )
        elif response.status_code == 403:
            log_security_event(
                loggers['security'],
                'forbidden_access',
                user_id=user_id,
                ip_address=request.remote_addr,
                details={'endpoint': request.endpoint, 'method': request.method}
            )
        elif response.status_code == 429:
            log_security_event(
                loggers['security'],
                'rate_limit_exceeded',
                user_id=user_id,
                ip_address=request.remote_addr,
                details={'endpoint': request.endpoint, 'method': request.method}
            )
        
        # Log successful authentication events
        if request.endpoint == 'main.login' and response.status_code == 302:  # Redirect after successful login
            log_security_event(
                loggers['security'],
                'successful_login',
                user_id=user_id,
                ip_address=request.remote_addr,
                details={'user_agent': request.headers.get('User-Agent', '')}
            )
        elif request.endpoint == 'main.logout':
            log_security_event(
                loggers['security'],
                'logout',
                user_id=user_id,
                ip_address=request.remote_addr
            )
        
        return response
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize rate limiting
    limiter.init_app(app)
    
    # User loader for Flask-Login
    from .auth import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    # Add security headers
    @app.after_request
    def after_request(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    return app