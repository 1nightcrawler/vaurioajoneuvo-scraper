# app/auth.py
import os
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
    
    @staticmethod
    def get(username):
        """Get user by username"""
        expected_username = os.environ.get('USERNAME', 'admin')
        if username == expected_username:
            return User(username)
        return None
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user with username and password"""
        expected_username = os.environ.get('USERNAME', 'admin')
        expected_password = os.environ.get('PASSWORD', 'admin')
        
        if username == expected_username and password == expected_password:
            return User(username)
        return None
