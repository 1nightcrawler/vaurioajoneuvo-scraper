# Deployment Guide - Vaurioajoneuvo Price Scraper

## Pre-Deployment Checklist Complete

- [x] **Strong SECRET_KEY** generated and set
- [x] **Strong password** set for login
- [x] **Production requirements.txt** created
- [x] **Gunicorn production server** installed and tested
- [x] **Startup script** created
- [x] **Authentication & security** implemented
- [x] **Rate limiting** configured
- [x] **Input validation** implemented

## Quick Deployment Options

### Option 1: Simple VPS Deployment

1. **Upload your code** (excluding .env):
```bash
rsync -av --exclude='.env' --exclude='__pycache__' \
  /path/to/your/app/ user@your-vps:/var/www/price-monitor/
```

2. **Setup on VPS**:
```bash
cd /var/www/price-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Create production .env**:
```bash
nano .env
# Copy your .env content but update values for production
```

4. **Install FlareSolverr** (if not already running):
```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  --restart unless-stopped \
  ghcr.io/flaresolverr/flaresolverr:latest
```

5. **Start the application**:
```bash
./start.sh
```

6. **Setup reverse proxy** (Nginx example):
```nginx
server {
    listen 80;
    server_name your-subdomain.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Cloud Platform (Railway/Heroku)

1. **Create account** on Railway.app or Heroku
2. **Connect Git repository**
3. **Set environment variables** in platform dashboard:
   - SECRET_KEY=your-secret-key
   - USERNAME=your-username
   - PASSWORD=your-password
   - TELEGRAM_TOKEN=your-token
   - TELEGRAM_CHAT_ID=your-chat-id
4. **Deploy automatically** from Git

### Option 3: Docker Deployment

1. **Create Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5050

CMD ["./start.sh"]
```

2. **Build and run**:
```bash
docker build -t price-monitor .
docker run -d \
  --env-file .env \
  -p 5050:5050 \
  --name price-monitor \
  price-monitor
```

## Production Security Checklist

- [x] **Strong SECRET_KEY** set
- [x] **Strong login credentials** configured
- [x] **Rate limiting** active on all endpoints
- [x] **Input validation** protecting against injection
- [x] **Authentication** required for all access
- [x] **Security headers** automatically added
- [ ] **HTTPS** setup with SSL certificate
- [ ] **Firewall** configured (block 8191 externally)
- [ ] **Regular updates** scheduled
- [ ] **Backups** configured for data files

## Environment Variables for Production

Update these in your production .env:

```env
SECRET_KEY=your-64-character-random-string
USERNAME=your-production-username
PASSWORD=your-strong-production-password
TELEGRAM_TOKEN=your-real-bot-token
TELEGRAM_CHAT_ID=your-real-chat-id
FLARESOLVERR_URL=http://localhost:8191/v1
```

## Next Steps

1. **Choose deployment method** (VPS recommended for learning)
2. **Setup domain/subdomain** pointing to your server
3. **Configure HTTPS** with Let's Encrypt
4. **Test login and functionality**
5. **Setup monitoring** (optional)

## Troubleshooting

### Common Issues:
- **Port conflicts**: Change port in start.sh if needed
- **FlareSolverr not accessible**: Check if Docker container is running
- **Login fails**: Verify .env file is loaded correctly
- **Rate limiting errors**: Normal for development, reduces in production

### Logs:
```bash
# Check application logs
journalctl -u your-service-name -f

# Check Gunicorn logs
tail -f /var/log/gunicorn/access.log
```

**Your application is now secure and ready for production deployment!** 🎉
