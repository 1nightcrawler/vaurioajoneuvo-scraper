# Security Setup Guide

## Security Features Implemented

Your application now includes comprehensive security measures:

### Authentication & Authorization
- **Login system** with username/password protection
- **Session management** with Flask-Login
- **All routes protected** - dashboard and API endpoints require authentication
- **Logout functionality** with session cleanup

### Rate Limiting
- **API endpoints protected** with different limits:
  - Login: 10 attempts per minute
  - Product operations: 20 per minute
  - Price fetching: 10 per minute (more restrictive due to external requests)
  - Watcher controls: 10 per minute
  - Telegram settings: 5 per minute

### Input Validation
- **URL validation** - only accepts valid http/https URLs
- **Price validation** - ensures positive numbers within reasonable limits
- **Name sanitization** - removes potentially dangerous characters
- **Duplicate prevention** - prevents adding duplicate product URLs

### Environment Variables
- **Secrets moved to .env file** - no more hardcoded credentials
- **Telegram credentials** sourced from environment variables
- **FlareSolverr URL** configurable via environment

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Quick Start

### 1. Configure Environment Variables
Edit the `.env` file with your actual values:

```bash
# Copy from .env.example and modify
cp .env.example .env
nano .env
```

Set these values:
```
SECRET_KEY=your-super-secret-random-key-here-change-this-123456
USERNAME=your_username
PASSWORD=your_secure_password_123
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
FLARESOLVERR_URL=http://localhost:8191/v1
```

### 2. Start the Application
```bash
python run.py
```

### 3. Login
- Visit http://127.0.0.1:5050
- You'll be redirected to the login page
- Use the credentials from your `.env` file

## Production Deployment Checklist

### Before Going Live:

#### Essential Security
- [ ] Change default username/password in `.env`
- [ ] Generate a strong SECRET_KEY (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Set up proper environment variables on your server
- [ ] Ensure `.env` file is not accessible via web

#### Infrastructure
- [ ] Use a production WSGI server (Gunicorn, uWSGI)
- [ ] Set up reverse proxy (Nginx/Apache) with HTTPS
- [ ] Configure firewall to block direct access to port 8191 (FlareSolverr)
- [ ] Run application as non-root user

#### Application
- [ ] Set `DEBUG = False` in production
- [ ] Configure proper logging instead of print statements
- [ ] Set up monitoring/alerting
- [ ] Regular security updates for dependencies

#### Backups
- [ ] Backup `products.json` and `config.json` regularly
- [ ] Version control your code (excluding sensitive files)

## 🔧 Advanced Security (Optional)

### HTTPS Setup Example (Nginx)
```nginx
server {
    listen 443 ssl;
    server_name your-subdomain.yourdomain.com;
    
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service Example
```ini
[Unit]
Description=Vaurioajoneuvo Price Scraper
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/.venv/bin
ExecStart=/path/to/your/app/.venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Warnings

1. **Never commit `.env` files** to version control
2. **FlareSolverr security**: Ensure port 8191 is firewalled from external access
3. **Regular updates**: Keep all dependencies updated
4. **Monitor logs**: Watch for suspicious login attempts
5. **Strong passwords**: Use complex passwords for your accounts

## Rate Limits Summary

| Endpoint | Limit | Reason |
|----------|--------|---------|
| Login | 10/min | Prevent brute force |
| Add/Edit Product | 20/min | Normal usage |
| Delete Product | 30/min | Higher limit for bulk operations |
| Price Fetch | 10/min | External requests, more restrictive |
| Watcher Control | 10/min | System operations |
| Settings | 5/min | Configuration changes |

## What's Now Secure

- [x] **Dashboard access** - requires login  
- [x] **API endpoints** - all protected with authentication  
- [x] **Input validation** - prevents malicious data  
- [x] **Rate limiting** - prevents abuse  
- [x] **Secure headers** - prevents common web attacks  
- [x] **Environment variables** - secrets not in code  
- [x] **Session management** - proper login/logout flow  

Your application is now **production-ready** from a security perspective! 🎉
