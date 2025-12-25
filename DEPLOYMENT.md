# 🚀 Deployment Guide - Telegram Forward Bot

This guide covers deployment strategies for the Telegram Forward Bot, with special focus on Render's free tier.

## 📋 Table of Contents

1. [Render Deployment (Recommended)](#render-deployment)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [VPS Deployment](#vps-deployment)
5. [Heroku Deployment](#heroku-deployment)
6. [Post-Deployment Setup](#post-deployment-setup)

## 🎯 Render Deployment (Recommended)

Render offers a generous free tier perfect for this bot.

### Prerequisites

1. [Render account](https://dashboard.render.com/)
2. GitHub/GitLab account
3. Telegram API credentials
4. Bot token from @BotFather

### Step-by-Step Instructions

#### 1. Fork the Repository

1. Fork this repository to your GitHub account
2. Keep it public (Render free tier requires public repos)

#### 2. Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your forked repository

#### 3. Configure Service Settings

**Basic Settings:**
- **Name**: `telegram-forward-bot`
- **Environment**: `Python`
- **Region**: Choose closest to you
- **Branch**: `main`

**Build & Start Commands:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`

**Instance Type:**
- Select **Free** plan

#### 4. Set Environment Variables

Add the following environment variables in Render:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
DATABASE_URL=sqlite:///bot_database.db
LOG_LEVEL=INFO
DELAY_BETWEEN_MESSAGES=1.0
MAX_RETRIES=3
FLOOD_PROTECT=true
```

#### 5. Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete (~2-3 minutes)
3. Your bot is now running!

#### 6. Important Notes for Render

- **Free tier limitations**: 512MB RAM, 100GB bandwidth/month
- **Sleep after inactivity**: First request after sleep may take 30s
- **Persistent storage**: Database survives restarts
- **Logs**: Available in Render dashboard

## 💻 Local Deployment

Perfect for development and testing.

### Prerequisites

- Python 3.8+
- Telegram API credentials
- Bot token

### Step-by-Step Instructions

#### 1. Clone Repository

```bash
git clone <repository-url>
cd telegram-forward-bot
```

#### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

#### 5. Run Bot

```bash
python bot.py
```

#### 6. Local Development Tips

- Use `LOG_LEVEL=DEBUG` for detailed logs
- Monitor `bot.log` file for issues
- Use `screen` or `tmux` for persistent sessions

## 🐳 Docker Deployment

Containerized deployment for consistency across environments.

### Prerequisites

- Docker installed
- Telegram API credentials

### Step-by-Step Instructions

#### 1. Build Docker Image

```bash
docker build -t telegram-forward-bot .
```

#### 2. Run Container

```bash
docker run -d \
  --name telegram-forward-bot \
  -e API_ID=your_api_id \
  -e API_HASH=your_api_hash \
  -e BOT_TOKEN=your_bot_token \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/sessions:/app/sessions \
  telegram-forward-bot
```

#### 3. Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: telegram-forward-bot
    restart: unless-stopped
    environment:
      - API_ID=${API_ID}
      - API_HASH=${API_HASH}
      - BOT_TOKEN=${BOT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./sessions:/app/sessions
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

## 🖥️ VPS Deployment

Deploy on your own server for maximum control.

### Prerequisites

- VPS with Ubuntu/Debian/CentOS
- SSH access
- Python 3.8+

### Step-by-Step Instructions

#### 1. Connect to VPS

```bash
ssh user@your-vps-ip
```

#### 2. Install Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip git screen

# CentOS/RHEL
sudo yum update
sudo yum install python3 python3-pip git screen
```

#### 3. Clone Repository

```bash
git clone <repository-url>
cd telegram-forward-bot
```

#### 4. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

#### 5. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

#### 6. Create Systemd Service

Create `/etc/systemd/system/telegram-forward-bot.service`:

```ini
[Unit]
Description=Telegram Forward Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/telegram-forward-bot
ExecStart=/usr/bin/python3 /home/your-username/telegram-forward-bot/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-forward-bot
sudo systemctl start telegram-forward-bot
```

#### 7. Monitor Logs

```bash
sudo journalctl -u telegram-forward-bot -f
```

## 🔷 Heroku Deployment

Alternative platform with free tier (requires credit card).

### Prerequisites

- Heroku account
- Heroku CLI installed
- Git

### Step-by-Step Instructions

#### 1. Clone Repository

```bash
git clone <repository-url>
cd telegram-forward-bot
```

#### 2. Create Heroku App

```bash
heroku create your-bot-name
```

#### 3. Configure Buildpacks

```bash
heroku buildpacks:set heroku/python
```

#### 4. Set Environment Variables

```bash
heroku config:set API_ID=your_api_id
heroku config:set API_HASH=your_api_hash
heroku config:set BOT_TOKEN=your_bot_token
```

#### 5. Create Procfile

Create `Procfile`:
```
worker: python bot.py
```

#### 6. Deploy

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### 7. Scale Worker

```bash
heroku ps:scale worker=1
```

#### 8. Important Notes for Heroku

- Use Heroku Postgres instead of SQLite
- Ephemeral file system - sessions lost on restart
- Worker dyno required (web dyno won't work)
- Free dyno sleeps after 30 minutes of inactivity

## 🎮 Post-Deployment Setup

After deploying, you need to configure the bot.

### 1. Start Bot Conversation

Send `/start` to your bot on Telegram.

### 2. Configure Source Channel

```
/set_source @your_source_channel
# OR
/set_source -1001234567890
```

### 3. Configure Target Channel

```
/set_target @your_target_channel
# OR
/set_target -1009876543210
```

### 4. Set Starting Message ID

```
/from_id 1
```

### 5. Begin Forwarding

The bot will automatically start forwarding from the configured position.

## 🔧 Monitoring & Maintenance

### Log Monitoring

#### Render
- View logs in Render dashboard
- Download logs for analysis

#### Local/VPS
```bash
tail -f bot.log
tail -f errors.log
```

#### Docker
```bash
docker logs -f telegram-forward-bot
```

### Health Checks

The bot includes built-in health monitoring:

```bash
# Check if bot is responding
curl http://localhost:8080/health
```

### Backup Strategy

#### Database Backup
```bash
# Local/VPS
sqlite3 bot_database.db ".backup backup.db"

# Docker
docker exec telegram-forward-bot sqlite3 /app/data/bot_database.db ".backup /app/data/backup.db"
```

#### Session Backup
```bash
# Backup sessions directory
tar -czf sessions_backup.tar.gz sessions/
```

### Updates

#### Update Bot Code
```bash
# Pull latest changes
git pull origin main

# Restart service (VPS)
sudo systemctl restart telegram-forward-bot

# Redeploy (Render)
# Manual deploy through dashboard

# Rebuild (Docker)
docker-compose down
docker-compose up --build
```

## 🚨 Troubleshooting Deployment

### Common Issues

#### 1. Bot Not Responding

**Check logs:**
```bash
# Render
dashboard → Logs

# VPS
sudo journalctl -u telegram-forward-bot -f

# Docker
docker logs telegram-forward-bot
```

**Verify environment variables:**
```bash
# Render
dashboard → Environment

# VPS
cat /etc/systemd/system/telegram-forward-bot.service

# Docker
docker exec telegram-forward-bot env
```

#### 2. Database Permission Errors

**Fix file permissions:**
```bash
sudo chown your-username:your-username bot_database.db
sudo chmod 664 bot_database.db
```

#### 3. Session Expiry

**Delete old sessions:**
```bash
rm -rf sessions/
systemctl restart telegram-forward-bot
```

#### 4. Memory Issues

**Monitor memory usage:**
```bash
# Check current usage
free -h

# Monitor over time
watch -n 1 free -h
```

**Reduce memory usage:**
- Decrease `STATUS_UPDATE_INTERVAL`
- Increase `PROGRESS_SAVE_INTERVAL`
- Use smaller chunk sizes

#### 5. Network Timeouts

**Increase timeouts:**
```python
# In config.py
MAX_RETRIES = 5
DELAY_BETWEEN_MESSAGES = 2.0
```

## 📊 Performance Tuning

### Optimize for Speed

```env
DELAY_BETWEEN_MESSAGES=0.5
MAX_RETRIES=2
FLOOD_PROTECT=false
STATUS_UPDATE_INTERVAL=10
```

### Optimize for Reliability

```env
DELAY_BETWEEN_MESSAGES=2.0
MAX_RETRIES=5
FLOOD_PROTECT=true
STATUS_UPDATE_INTERVAL=3
```

### Optimize for Low Memory

```env
LOG_LEVEL=WARNING
STATUS_UPDATE_INTERVAL=30
PROGRESS_SAVE_INTERVAL=50
CHUNK_SIZE=524288  # 512KB chunks
```

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit credentials to git
   - Use platform secret management
   - Rotate keys regularly

2. **Bot Permissions**
   - Only add bot to required channels
   - Remove bot when not needed
   - Monitor bot activity logs

3. **Database Security**
   - Regular backups
   - Encrypt sensitive data
   - Limit file permissions

4. **Network Security**
   - Use HTTPS for webhooks
   - Firewall unnecessary ports
   - Monitor traffic patterns

## 📈 Scaling Considerations

### Horizontal Scaling

For high-volume forwarding, consider:

1. **Multiple Bot Instances**
   - Each with different API credentials
   - Different channel ranges
   - Load balancer for distribution

2. **Queue System**
   - Redis/RabbitMQ for message queuing
   - Worker processes for forwarding
   - Result aggregation

3. **Database Scaling**
   - PostgreSQL for better concurrency
   - Read replicas for statistics
   - Connection pooling

### Vertical Scaling

Increase resources:

- **RAM**: More memory for larger file caching
- **CPU**: Faster message processing
- **Storage**: SSD for better database performance
- **Network**: Higher bandwidth for large files

## 🎯 Platform Comparison

| Platform | Free Tier | Ease of Use | Persistence | Best For |
|----------|-----------|-------------|-------------|----------|
| Render | ✅ Generous | ⭐⭐⭐⭐⭐ | ✅ SQLite | Beginners |
| Heroku | ✅ Limited | ⭐⭐⭐⭐ | ❌ Ephemeral | Quick testing |
| VPS | ❌ Paid | ⭐⭐⭐ | ✅ Full control | Production |
| Docker | ❌ Self-hosted | ⭐⭐⭐⭐ | ✅ Volumes | Consistency |

## 📞 Support

If you encounter deployment issues:

1. Check the [Troubleshooting](#troubleshooting-deployment) section
2. Review logs for specific error messages
3. Verify environment variables are set correctly
4. Test locally before deploying
5. Check platform-specific documentation

---

**Happy Deploying! 🚀**