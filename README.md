# 🚀 Telegram Forward Bot - Industrial Strength

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-orange.svg)](https://docs.pyrogram.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Render](https://img.shields.io/badge/deployable-Render-blueviolet.svg)](https://render.com)

An industrial-strength Telegram bot designed for comprehensive message forwarding with enterprise-grade reliability, real-time monitoring, and crash recovery capabilities.

## ✨ Key Features

### 🎯 Complete Content Migration
- ✅ **All Message Types**: Text, photos, videos, documents, audio, voice, stickers, animations, polls, contacts, locations
- ✅ **Large File Support**: Handles files up to Telegram's 2GB limit
- ✅ **Media Groups**: Forwards albums as complete units
- ✅ **Metadata Preservation**: Maintains original formatting, captions, and message structure
- ✅ **Inline Keyboards**: Supports messages with buttons and interactive elements

### 🛡️ Advanced Error Handling
- ✅ **Multi-Strategy Forwarding**: Direct forward → Download & re-upload → Chunk-based streaming
- ✅ **Exponential Backoff**: Intelligent retry with configurable attempts (default: 3)
- ✅ **Flood Protection**: Adaptive delays to prevent rate limiting
- ✅ **Crash Recovery**: Automatic session restoration after unexpected shutdowns
- ✅ **Never-Skip Guarantee**: No message is ever skipped until successfully forwarded

### 📊 Real-Time Monitoring
- ✅ **Dual Status Formats**: Decorative and technical status displays
- ✅ **Live Updates**: Status updates every 3-5 seconds
- ✅ **Progress Tracking**: Visual progress bars and percentage completion
- ✅ **Speed Metrics**: Real-time messages/minute calculation
- ✅ **ETA Calculation**: Estimated time of arrival for completion

### 🗄️ Session Management
- ✅ **Persistent Sessions**: SQLite database for progress tracking
- ✅ **Automatic Saves**: Progress saved every 10 messages
- ✅ **Resume Capability**: Continue from exact failure point
- ✅ **Duplicate Detection**: Prevents forwarding the same message twice
- ✅ **Statistics Tracking**: Lifetime metrics and performance analytics

### 🎮 Comprehensive Command System
- ✅ **25+ Commands**: Full-featured command interface
- ✅ **Interactive Configuration**: Easy channel and parameter setup
- ✅ **Range Forwarding**: Forward specific message ranges
- ✅ **Speed Control**: Fast, normal, and safe operation modes
- ✅ **Session Management**: Pause, resume, cancel, and reset operations

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram API credentials ([Get them here](https://my.telegram.org/))
- Telegram Bot Token ([Create with @BotFather](https://t.me/BotFather))

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram-forward-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Render Deployment

1. **Fork this repository**

2. **Create a new Web Service on Render**
   - Connect your forked repository
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`

3. **Configure Environment Variables**
   ```env
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   ```

4. **Deploy**
   - Click "Deploy" and your bot will start automatically

## 📋 Complete Command Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show welcome menu |
| `/status` | Show current status and configuration |
| `/pause` | Pause current forwarding operation |
| `/resume` | Resume from last saved position |
| `/cancel` | Cancel current operation (saves progress) |
| `/reset` | Reset all data (requires confirmation) |

### Configuration Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/set_source` | `/set_source @channel` | Set source channel |
| `/set_target` | `/set_target @channel` | Set target channel |
| `/from_id` | `/from_id 1` | Set starting message ID |
| `/to_id` | `/to_id 1000` | Set ending message ID |
| `/range` | `/range 1 1000` | Set message range |

### Speed & Safety Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/delay` | `/delay 1.5` | Set delay between messages (0.1-60s) |
| `/speed` | `/speed normal` | Set speed mode (fast/normal/safe) |
| `/retry` | `/retry 5` | Set retry attempts (0-10) |
| `/flood_protect` | `/flood_protect on` | Toggle flood protection |

### Monitoring Commands

| Command | Description |
|---------|-------------|
| `/stats` | Show bot statistics and performance metrics |
| `/failed` | Show recently failed messages |
| `/help` | Show complete help information |

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_ID` | Required | Telegram API ID |
| `API_HASH` | Required | Telegram API Hash |
| `BOT_TOKEN` | Required | Bot token from @BotFather |
| `DATABASE_PATH` | `bot_database.db` | SQLite database file path |
| `DELAY_BETWEEN_MESSAGES` | `1.0` | Delay between messages in seconds |
| `MAX_RETRIES` | `3` | Maximum retry attempts for failed messages |
| `FLOOD_PROTECT` | `true` | Enable flood protection |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `STATUS_UPDATE_INTERVAL` | `5` | Status update interval in seconds |
| `MAX_FILE_SIZE_MB` | `2048` | Maximum file size in MB |

### Speed Modes

| Mode | Delay | Use Case |
|------|-------|----------|
| `fast` | 0.5s | High-speed forwarding (risky) |
| `normal` | 1.0s | Recommended for most cases |
| `safe` | 2.5s | Conservative, prevents flooding |

## 🔧 Advanced Features

### File Handling Strategies

The bot implements a multi-layered approach for maximum reliability:

1. **Direct Forward** - Fastest method, tries first
2. **Download & Re-upload** - Fallback for direct failures
3. **Chunk-based Streaming** - For very large files (>50MB)
4. **Exponential Backoff** - Intelligent retry with increasing delays

### Database Schema

The bot uses SQLite for persistent storage with the following key tables:

- `forwarding_progress` - Tracks active sessions and progress
- `failed_messages` - Logs failed messages for retry
- `message_tracker` - Prevents duplicate forwarding
- `bot_settings` - Stores configuration
- `bot_statistics` - Lifetime metrics

### Error Recovery

The bot handles various error scenarios:

- **FloodWait**: Automatic backoff and retry
- **Session Expiry**: Automatic reconnection
- **Network Issues**: Retry with exponential backoff
- **File Access**: Multiple forwarding strategies
- **Bot Permissions**: Validation before forwarding

## 📊 Status Formats

### Decorative Status
```
╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪
║┣⪼🕵 ғᴇᴛᴄʜᴇᴅ Msɢ : 1000
║┣⪼✅ sᴜᴄᴄᴇғᴜʟʟʏ Fᴡᴅ : 950
║┣⪼👥 ᴅᴜᴘʟɪᴄᴀᴛᴇ Msɢ : 25
║┣⪼🗑 ᴅᴇʟᴇᴛᴇᴅ Msɢ : 10
║┣⪼🪆 Sᴋɪᴘᴘᴇᴅ Msɢ : 5
║┣⪼🔁 Fɪʟᴛᴇʀᴇᴅ Msɢ : 10
║┣⪼📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: forwarding
║┣⪼𖨠 Pᴇʀᴄᴇɴᴛᴀɢᴇ: 95.0 %
╚════❰ Almost done 🎯 ❱══❍⊱❁۪۪
```

### Technical Status
```
🚀 MIGRATION LIVE STATUS
━━━━━━━━━━━━━━━━━━━━
📤 Source: My Source Channel
📥 Target: My Target Channel
━━━━━━━━━━━━━━━━━━━━
📊 Progress Details:
✅ Success: 950
❌ Failed: 10
♻️ Duplicate: 25
━━━━━━━━━━━━━━━━━━━━
⚡ Speed: 45.2 msgs/min
⏱ Time Elapsed: 21m 15s
📂 Currently Processing: ID 12345
━━━━━━━━━━━━━━━━━━━━
🟢 Bot Status: RUNNING
```

## 🚨 Troubleshooting

### Common Issues

**1. "Bot doesn't have access to channel"**
- Add the bot as an administrator to both channels
- Ensure the bot has "Post Messages" permission in target channel

**2. "FloodWait errors"**
- Increase delay between messages using `/delay 2.0`
- Switch to safe mode using `/speed safe`
- Enable flood protection using `/flood_protect on`

**3. "Session expired"**
- Use `/resume` to continue from last position
- Check `/status` to see current progress

**4. "Large files failing"**
- Ensure bot has enough storage space
- Check network connection stability
- Increase retry count using `/retry 5`

### Debug Mode

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

This will provide detailed logs for troubleshooting issues.

## 🏗️ Architecture

### Project Structure

```
telegram-forward-bot/
├── bot.py                 # Main application entry point
├── config.py              # Configuration management
├── database.py            # Database operations
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── Dockerfile            # Container configuration
├── .env.example          # Environment template
├── README.md             # This file
├── handlers/
│   ├── commands.py       # Command implementations
│   ├── forwarding.py     # Core forwarding logic
│   └── status.py         # Status updates
└── utils/
    ├── logger.py         # Logging utilities
    ├── helpers.py        # Helper functions
    └── validators.py     # Input validation
```

### Key Components

1. **Bot Core** (`bot.py`): Main application logic, signal handling, graceful shutdown
2. **Configuration** (`config.py`): Centralized configuration with validation
3. **Database** (`database.py`): SQLite operations with async support
4. **Command Handler** (`handlers/commands.py`): All bot command implementations
5. **Forwarding Handler** (`handlers/forwarding.py`): Core forwarding logic with strategies
6. **Status Handler** (`handlers/status.py`): Real-time status updates
7. **Utilities** (`utils/`): Logging, helpers, validators

## 🔒 Security Considerations

1. **API Credentials**: Never share your API_ID, API_HASH, or BOT_TOKEN
2. **Channel Permissions**: Bot only accesses channels you explicitly configure
3. **File Access**: Temporary files are cleaned up after use
4. **Session Storage**: Sessions are stored securely in ./sessions directory
5. **Database**: SQLite database contains only forwarding metadata

## 📈 Performance Optimization

1. **Batch Operations**: Status updates are batched to reduce API calls
2. **Async Operations**: Full async/await implementation for concurrency
3. **Memory Management**: Large files are streamed, not loaded entirely
4. **Database Optimization**: Indexes and WAL mode for better performance
5. **Rate Limiting**: Intelligent delays to maximize throughput

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pyrogram](https://docs.pyrogram.org/) - Telegram API framework
- [Render](https://render.com/) - Cloud hosting platform
- Telegram team for the Bot API

## 📞 Support

For support and questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Command Reference](#complete-command-reference)
3. Check the [FAQ](#faq) below

## ❓ FAQ

**Q: Can the bot forward messages from private channels?**
A: Yes, as long as the bot has been added to the channel and has appropriate permissions.

**Q: What happens if the bot crashes during forwarding?**
A: The bot automatically saves progress every 10 messages. Use `/resume` to continue from the last successful message.

**Q: Can I run multiple instances of the bot?**
A: Yes, but each instance should use its own database file to avoid conflicts.

**Q: Does the bot work with channels that have restricted forwarding?**
A: The bot will attempt to forward content, but success depends on the specific restrictions in place.

**Q: How much storage does the bot need?**
A: The bot itself uses minimal storage (~50MB). Temporary files for large media are cleaned up automatically.

**Q: Can I deploy this on other platforms besides Render?**
A: Yes! The bot can run on any platform that supports Python 3.8+, including VPS, Heroku, Railway, etc.

---

**Made with ❤️ by an Expert Python Developer with 100+ years of experience**

*This bot is designed for production use with enterprise-grade reliability and monitoring capabilities.*