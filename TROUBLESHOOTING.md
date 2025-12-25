# 🔧 Troubleshooting Guide - Telegram Forward Bot

Comprehensive solutions for common issues and errors.

## 📋 Quick Diagnosis

Before diving into specific issues, run this diagnostic checklist:

```bash
# 1. Check Python version
python --version  # Should be 3.8+

# 2. Verify dependencies
pip install -r requirements.txt --dry-run

# 3. Test configuration
python -c "from config import Config; Config.validate(); print('✅ Config valid')"

# 4. Check database
python -c "from database import db; import asyncio; asyncio.run(db.connect()); print('✅ DB connected')"

# 5. Test bot import
python -c "from bot import TelegramForwardBot; print('✅ Bot imports successfully')"
```

## 🚨 Common Issues

### 1. Bot Won't Start

**Symptoms:**
- `python bot.py` immediately exits
- No logs generated
- Error messages on startup

**Solutions:**

#### Missing Environment Variables
```bash
# Error: "API_ID is required"
# Fix: Add to .env file
echo "API_ID=your_api_id" >> .env
echo "API_HASH=your_api_hash" >> .env
echo "BOT_TOKEN=your_bot_token" >> .env
```

#### Python Version Too Old
```bash
# Error: Syntax errors or import failures
# Fix: Update Python
python --version  # Should show 3.8+

# If not, install newer version
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11

# macOS:
brew install python@3.11
```

#### Missing Dependencies
```bash
# Error: "ModuleNotFoundError"
# Fix: Install requirements
pip install -r requirements.txt

# If still failing, try:
pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
```

#### Port Already in Use
```bash
# Error: "Address already in use"
# Fix: Find and kill process
lsof -i :8080
kill -9 <PID>
```

### 2. Database Issues

**Symptoms:**
- "database is locked" errors
- Permission denied errors
- Data not persisting

**Solutions:**

#### Database Locked
```bash
# Error: "database is locked"
# Cause: Multiple instances or improper shutdown

# Fix 1: Wait and retry (SQLite automatically resolves)
sleep 10 && python bot.py

# Fix 2: Manual unlock
sqlite3 bot_database.db "PRAGMA integrity_check;"
```

#### Permission Errors
```bash
# Error: "Permission denied"
# Fix: Set correct permissions
sudo chown $USER:$USER bot_database.db
chmod 664 bot_database.db

# For sessions directory
sudo chown -R $USER:$USER sessions/
chmod -R 755 sessions/
```

#### Database Corruption
```bash
# Error: "database disk image is malformed"
# Fix: Restore from backup or recreate

# Backup current database
cp bot_database.db bot_database.db.backup

# Try to recover
sqlite3 bot_database.db ".recover" | sqlite3 new_database.db
mv new_database.db bot_database.db
```

### 3. Telegram API Issues

**Symptoms:**
- "API_ID is invalid" errors
- "Bot token is invalid" errors
- "UserDeactivated" errors

**Solutions:**

#### Invalid API Credentials
```bash
# Error: "API_ID is invalid"
# Fix: Get new credentials from https://my.telegram.org

# 1. Log in to https://my.telegram.org
# 2. Go to "API Development Tools"
# 3. Create new app or use existing
# 4. Copy API_ID and API_HASH

# Update .env
sed -i 's/API_ID=.*/API_ID=your_new_api_id/' .env
sed -i 's/API_HASH=.*/API_HASH=your_new_api_hash/' .env
```

#### Invalid Bot Token
```bash
# Error: "Bot token is invalid"
# Fix: Get correct token from @BotFather

# 1. Message @BotFather on Telegram
# 2. Send "/mybots"
# 3. Select your bot
# 4. Choose "API Token"
# 5. Copy the token

# Update .env
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=your_correct_token/' .env
```

#### UserDeactivated Error
```bash
# Error: "UserDeactivated"
# Cause: Account associated with API_ID is banned/deactivated

# Fix: Use different API credentials
# 1. Create new Telegram account
# 2. Get new API_ID/API_HASH from https://my.telegram.org
# 3. Update .env with new credentials
```

### 4. Channel Access Issues

**Symptoms:**
- "Channel not found" errors
- "Bot is not admin" errors
- "Forwarding is restricted" errors

**Solutions:**

#### Channel Not Found
```bash
# Error: "Username not found" or "Chat not found"

# Fix 1: Use correct format
# Public channels: @channel_username
# Private channels: -1001234567890 (full numeric ID)
# Use /set_source @username or /set_source -1001234567890

# Fix 2: Check if channel exists
# Try accessing via web: https://t.me/channel_username

# Fix 3: Get channel ID
# Forward any message from channel to @userinfobot
# It will show the channel ID
```

#### Bot Not Admin
```bash
# Error: "Bot needs admin permissions"
# Fix: Add bot as admin to target channel

# Steps:
# 1. Go to target channel
# 2. Channel Info → Administrators → Add Administrator
# 3. Search for your bot username
# 4. Add with these permissions:
#    - Post messages
#    - Edit messages
#    - Delete messages
#    - Post media
```

#### Forwarding Restricted
```bash
# Error: "Forwarding is restricted in this chat"
# Cause: Source channel has forwarding restrictions

# Fix 1: Check channel settings
# Channel Info → Discussion → Save Restrictions

# Fix 2: Use download-reupload strategy
# Bot will automatically try this if direct forward fails

# Fix 3: Contact channel admin to allow forwarding
```

### 5. Message Forwarding Failures

**Symptoms:**
- Messages not forwarding
- "Message too long" errors
- "Media empty" errors

**Solutions:**

#### Message Too Long
```bash
# Error: "MessageTooLong"
# Fix: Bot automatically handles this by splitting or truncating

# Manual fix: Use /skip to skip problematic message
```

#### Media Empty
```bash
# Error: "WebpageMediaEmpty" or "Media empty"
# Cause: Original media was deleted or inaccessible

# Fix 1: Bot will mark as deleted and continue
# Fix 2: Use /skip to skip the message
# Fix 3: Check if original message still exists in source
```

#### File Too Large
```bash
# Error: "File is too large"
# Cause: File exceeds Telegram's 2GB limit

# Fix: Bot will skip files > 2GB automatically
# Check: Use /failed to see skipped files
```

### 6. Performance Issues

**Symptoms:**
- Very slow forwarding
- High memory usage
- Bot crashes frequently

**Solutions:**

#### Slow Forwarding
```bash
# Cause: Too many retries, large files, network issues

# Fix 1: Increase delay
/delay 2.0

# Fix 2: Switch to safe mode
/speed safe

# Fix 3: Check network speed
ping api.telegram.org

# Fix 4: Monitor system resources
htop  # Check CPU/RAM usage
```

#### High Memory Usage
```bash
# Cause: Large files, many concurrent operations

# Fix 1: Reduce chunk size
# In .env: CHUNK_SIZE=524288  # 512KB instead of 1MB

# Fix 2: Increase save interval
# In .env: PROGRESS_SAVE_INTERVAL=50

# Fix 3: Restart bot periodically
# Use cron to restart daily
```

#### Bot Crashes
```bash
# Check logs for error
tail -50 bot.log | grep ERROR

# Common causes:
# 1. Out of memory
# 2. Database locked
# 3. Network timeout
# 4. Unhandled exception

# Fix: Use process manager
# PM2: pm2 start bot.py --name telegram-bot
# Systemd: See DEPLOYMENT.md
# Screen: screen -dmS bot python bot.py
```

### 7. Session and Authentication Issues

**Symptoms:**
- "Session expired" errors
- "Auth key not found" errors
- Bot keeps asking to login

**Solutions:**

#### Session Expired
```bash
# Error: "Session expired"
# Fix: Delete old session and restart

rm -rf sessions/
python bot.py
```

#### Auth Key Not Found
```bash
# Error: "Auth key not found"
# Fix: Regenerate session

# 1. Stop bot
# 2. Delete sessions directory
rm -rf sessions/

# 3. Start bot (will create new session)
python bot.py
```

#### Persistent Login Issues
```bash
# If login keeps failing:

# 1. Verify API credentials
echo $API_ID  # Should show your API ID
echo $API_HASH  # Should show your API hash

# 2. Check for special characters in API_HASH
# If API_HASH contains $, wrap in single quotes
API_HASH='your_hash_with_$pecial_chars'

# 3. Try new API credentials
# Go to https://my.telegram.org and create new app
```

## 🔍 Advanced Debugging

### Enable Debug Logging

```bash
# Set log level to DEBUG
echo "LOG_LEVEL=DEBUG" >> .env

# Run bot with verbose output
python bot.py 2>&1 | tee debug.log
```

### Database Inspection

```bash
# Check database contents
sqlite3 bot_database.db ".tables"

# View active sessions
sqlite3 bot_database.db "SELECT * FROM forwarding_progress;"

# View failed messages
sqlite3 bot_database.db "SELECT * FROM failed_messages LIMIT 10;"

# Check settings
sqlite3 bot_database.db "SELECT * FROM bot_settings;"
```

### Network Testing

```bash
# Test Telegram API connectivity
ping api.telegram.org
nslookup api.telegram.org

# Test with curl
curl -I https://api.telegram.org

# Check for proxy/firewall issues
curl -x http://proxy.example.com:8080 https://api.telegram.org
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory tracking
mprof run python bot.py
mprof plot
```

### Code Profiling

```bash
# Install profiler
pip install cProfile

# Profile bot startup
python -m cProfile -o profile.stats bot.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## 🚨 Emergency Recovery

### Complete Reset

If nothing else works, perform a complete reset:

```bash
# 1. Stop bot
pkill -f bot.py

# 2. Backup data
cp bot_database.db bot_database.db.backup.$(date +%Y%m%d_%H%M%S)
tar -czf sessions_backup.tar.gz sessions/

# 3. Reset everything
rm -f bot_database.db
rm -rf sessions/
rm -f bot.log errors.log

# 4. Start fresh
python bot.py
```

### Recovery from Backup

```bash
# Restore database
cp bot_database.db.backup bot_database.db

# Restore sessions
tar -xzf sessions_backup.tar.gz

# Start bot
python bot.py
```

### Manual Database Repair

```bash
# Dump database to SQL
sqlite3 bot_database.db ".dump" > backup.sql

# Create new database from dump
sqlite3 new_database.db < backup.sql

# Replace corrupted database
mv new_database.db bot_database.db
```

## 📞 Getting Help

If you're still stuck:

1. **Check logs**: Look for ERROR messages in `bot.log`
2. **Run diagnostics**: Use the diagnostic script at the top
3. **Search issues**: Check if your issue is already documented
4. **Provide details**: When asking for help, include:
   - Error messages (full stack trace)
   - Your `.env` file (remove sensitive data)
   - Bot logs (relevant portions)
   - Steps you've already tried

## 🎯 Prevention Tips

### Regular Maintenance

```bash
# Weekly maintenance script
#!/bin/bash
echo "=== Bot Maintenance ==="

# 1. Check disk space
df -h | grep -E "(Use%|/dev/)"

# 2. Check memory usage
free -h

# 3. Rotate logs
mv bot.log bot.log.old
mv errors.log errors.log.old

# 4. Check database integrity
sqlite3 bot_database.db "PRAGMA integrity_check;"

# 5. Update dependencies
pip install --upgrade -r requirements.txt

echo "=== Maintenance Complete ==="
```

### Monitoring Script

```bash
# monitor.sh - Check bot health
#!/bin/bash

# Check if bot is running
if ! pgrep -f "python bot.py" > /dev/null; then
    echo "Bot is not running!"
    # Restart bot
    cd /path/to/bot
    python bot.py &
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "High memory usage: $MEM_USAGE%"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Low disk space: $DISK_USAGE% used"
fi
```

---

**Remember**: Most issues can be resolved by checking logs, verifying configuration, and ensuring proper permissions!