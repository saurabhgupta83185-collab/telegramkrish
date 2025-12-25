# ⚡ Quick Start Guide - Telegram Forward Bot

Get your bot running in under 10 minutes!

## 🎯 Prerequisites Checklist

Before you start, make sure you have:

- [ ] Python 3.8 or higher installed
- [ ] Telegram API credentials ([Get them here](https://my.telegram.org/))
- [ ] Bot token from @BotFather
- [ ] Git installed

## 🚀 5-Minute Setup

### Step 1: Get the Code (1 minute)

```bash
git clone <repository-url>
cd telegram-forward-bot
```

### Step 2: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

### Step 3: Configure Bot (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
# Windows: notepad .env
# macOS/Linux: nano .env
```

Add your credentials to `.env`:
```env
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxyz
```

### Step 4: Test Run (1 minute)

```bash
python bot.py
```

You should see:
```
2024-XX-XX XX:XX:XX - telegram_forward_bot - INFO - Telegram Forward Bot starting up
2024-XX-XX XX:XX:XX - telegram_forward_bot - INFO - Database initialized successfully
2024-XX-XX XX:XX:XX - telegram_forward_bot - INFO - Pyrogram client started successfully
2024-XX-XX XX:XX:XX - telegram_forward_bot - INFO - Bot started successfully
```

## 🎮 First Time Setup

### 1. Start Conversation with Your Bot

- Open Telegram
- Find your bot (search for its username)
- Send `/start`

### 2. Configure Channels

```
/set_source @your_source_channel
/set_target @your_target_channel
```

### 3. Set Starting Point

```
/from_id 1
```

### 4. Begin Forwarding

The bot will automatically start forwarding messages!

## 📱 Essential Commands

| Command | What it does |
|---------|--------------|
| `/status` | Check current progress |
| `/pause` | Pause forwarding |
| `/resume` | Continue forwarding |
| `/help` | Show all commands |

## 🎓 Basic Workflow

1. **Setup** → Configure source and target channels
2. **Configure** → Set starting message ID
3. **Forward** → Bot automatically forwards all messages
4. **Monitor** → Use `/status` to check progress
5. **Control** → Pause/resume as needed

## ⚡ Quick Commands Reference

### Most Used Commands

```bash
# Set channels
/set_source @source_channel
/set_target @target_channel

# Control forwarding
/from_id 1          # Start from message 1
/to_id 1000         # Stop at message 1000
/range 1 1000       # Forward messages 1-1000

# Adjust speed
/speed normal       # Recommended speed
/delay 1.0          # 1 second delay
/flood_protect on   # Enable protection

# Monitor progress
/status             # Current status
/stats              # Statistics
/failed             # Failed messages
```

## 🚀 Deploy to Cloud (2 minutes)

### Render (Easiest)

1. Fork this repository
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect your repository
5. Set environment variables:
   ```
   API_ID=your_id
   API_HASH=your_hash
   BOT_TOKEN=your_token
   ```
6. Click Deploy!

### Other Platforms

- **Heroku**: Use `Procfile` and Heroku CLI
- **VPS**: Use systemd service (see DEPLOYMENT.md)
- **Docker**: Use provided Dockerfile

## 🎓 Next Steps

After getting your bot running:

1. **Read the [README](README.md)** for full feature documentation
2. **Check [DEPLOYMENT.md](DEPLOYMENT.md)** for advanced deployment options
3. **Review [TROUBLESHOOTING](TROUBLESHOOTING.md)** for common issues
4. **Explore all commands** with `/help`

## 🆘 Need Help?

### Common Issues

**Bot not responding?**
- Check if it's running: `python bot.py`
- Verify API credentials in `.env`
- Check logs: `tail -f bot.log`

**"Channel not found" error?**
- Make sure bot is added to both channels
- Use correct channel format: `@channel_username` or `-1001234567890`

**Messages not forwarding?**
- Check bot permissions (needs admin in target channel)
- Verify source channel allows forwarding
- Check `/status` for errors

### Quick Debug Commands

```bash
# Check bot status
python -c "from bot import TelegramForwardBot; print('Bot imported successfully')"

# Test database
python -c "from database import db; import asyncio; asyncio.run(db.connect()); print('DB connected')"

# Verify configuration
python -c "from config import Config; Config.validate(); print('Config valid')"
```

## 📊 Monitoring Your Bot

### Local Monitoring

Watch logs in real-time:
```bash
tail -f bot.log
```

Check database:
```bash
sqlite3 bot_database.db "SELECT * FROM forwarding_progress;"
```

### Cloud Monitoring

- **Render**: Dashboard → Logs
- **Heroku**: `heroku logs --tail`
- **VPS**: `journalctl -u telegram-forward-bot -f`

## 🎉 Success Checklist

You're successfully running the bot if you can:

- [ ] Send `/start` and get welcome message
- [ ] Use `/set_source` without errors
- [ ] Use `/set_target` without errors
- [ ] See status updates during forwarding
- [ ] Pause and resume forwarding

## 🚀 Advanced Features (Explore Later)

Once you're comfortable with basics:

- **Range forwarding**: `/range 100 200`
- **Speed control**: `/speed fast|normal|safe`
- **Error handling**: Automatic retries and recovery
- **Statistics**: `/stats` for detailed metrics
- **Failed message tracking**: `/failed` to see errors

## 📚 Documentation Map

- **README.md** - Complete feature documentation
- **DEPLOYMENT.md** - Advanced deployment options
- **QUICKSTART.md** - This file (quick start)
- **TROUBLESHOOTING.md** - Common issues and solutions

---

**🎉 Congratulations! You're now running an industrial-strength Telegram forwarding bot!**

Ready to explore advanced features? Check out the [README](README.md) for the complete guide.