# 🤖 AutoFilter Bot

A production-ready Telegram AutoFilter Bot built with **Pyrogram** and dual **MongoDB** databases.

---

## ✨ Features

| Category | Features |
|---|---|
| **Search** | Auto-filter, spell-check fallback, paginated results, inline / link mode |
| **Verification** | Shortlink-based, 24h access, premium bypass |
| **Premium** | 4 plan tiers (Basic/Premium/VIP/Lifetime), expiry tracking |
| **FSub** | Force Subscribe with Request-to-Join support, auto-approve |
| **File Mgmt** | Auto-index, auto-delete, protect content, per-group settings |
| **Captions** | Custom captions + IMDB-style templates |
| **Broadcast** | Users broadcast + group broadcast |
| **Logging** | Custom log channel for all bot events |
| **Database** | Separate MongoDB databases for files and users |
| **Deploy** | Heroku · Railway · Koyeb · VPS |

---

## 📁 Repository Structure

```
AutoFilterBot/
├── bot.py              # Entry point
├── config.py           # All config / env vars
├── requirements.txt
├── Procfile
├── .env.example
├── database/
│   ├── __init__.py
│   ├── files_db.py     # Files + group settings DB
│   └── users_db.py     # Users + premium + verification DB
├── plugins/
│   ├── start.py        # /start, /help, verification deep-link
│   ├── admin.py        # All admin commands
│   ├── filters.py      # Core AutoFilter logic
│   ├── premium.py      # Premium management commands
│   ├── broadcast.py    # /broadcast, /gbroadcast
│   └── fsub.py         # FSub enforcement + group tracking
└── utils/
    ├── helpers.py      # File info, pagination, spell-check
    ├── shortlink.py    # Shortlink API wrapper
    └── decorators.py   # @admin_only, @premium_or_admin
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/yourname/AutoFilterBot
cd AutoFilterBot
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env   # Fill in all values
```

### 3. Run
```bash
python bot.py
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | From @BotFather |
| `API_ID` | ✅ | From my.telegram.org |
| `API_HASH` | ✅ | From my.telegram.org |
| `FILES_DB_URI` | ✅ | MongoDB URI for files database |
| `USERS_DB_URI` | ✅ | MongoDB URI for users database |
| `FILES_DB_NAME` | ✅ | Files database name |
| `USERS_DB_NAME` | ✅ | Users database name |
| `ADMINS` | ✅ | Space-separated admin user IDs |
| `LOG_CHANNEL` | ✅ | Channel ID for bot logs |
| `FSUB_CHANNEL` | ⭕ | Force-subscribe channel ID (0 = off) |
| `SHORTLINK_URL` | ⭕ | Shortlink domain (e.g. shrinkme.io) |
| `SHORTLINK_API` | ⭕ | Shortlink API key |
| `VERIFY_EXPIRE` | ⭕ | Verification duration in seconds (default: 86400) |
| `VERIFICATION_ON` | ⭕ | Enable verification (default: true) |
| `PROTECT_CONTENT` | ⭕ | Protect files from forwarding (default: false) |
| `AUTO_DELETE` | ⭕ | Auto-delete sent files after N seconds (0 = off) |
| `SPELL_CHECK` | ⭕ | Enable spell-check fallback (default: true) |
| `LINK_MODE` | ⭕ | Send deep links instead of files (default: false) |
| `MAX_RESULTS` | ⭕ | Max search results per query (default: 10) |

---

## 📜 Bot Commands

### User Commands
| Command | Description |
|---|---|
| `/start` | Check bot status |
| `/help` | Show all commands |
| `/myplan` | View your current plan |
| `/plan` | See available premium plans |

### Admin Commands
| Command | Usage | Description |
|---|---|---|
| `/shortlink` | `/shortlink <api_url> <api_key>` | Set shortlink for verification |
| `/tutorial` | Reply to video | Set tutorial video |
| `/caption` | `/caption <text>` | Set custom file caption |
| `/template` | `/template <text>` | Set IMDB template |
| `/fsub` | `/fsub <channel_id>` | Set FSub channel |
| `/log` | `/log <channel_id>` | Set log channel |
| `/ginfo` | `/ginfo [chat_id]` | Get group/channel info |
| `/index` | — | Display index status |
| `/addpremium` | `/addpremium <id> [plan] [days]` | Add premium user |
| `/removepremium` | `/removepremium <id>` | Remove premium user |
| `/premiumuser` | — | List all premium users |
| `/broadcast` | `/broadcast <text>` or reply | Broadcast to all users |
| `/gbroadcast` | `/gbroadcast <text>` or reply | Broadcast to all groups |
| `/deleteall` | `/deleteall confirm` | Delete all indexed files |
| `/deletefiles` | `/deletefiles <name>` | Delete specific files |
| `/setverify` | `/setverify on\|off` | Toggle verification |
| `/setprotect` | `/setprotect on\|off` | Toggle content protection |

---

## ☁️ Deployment

### Heroku
```bash
heroku create your-app-name
heroku config:set BOT_TOKEN=... API_ID=... API_HASH=... FILES_DB_URI=... USERS_DB_URI=...
git push heroku main
heroku ps:scale worker=1
```

### Railway
1. Connect GitHub repo → Railway
2. Add all env variables in the Railway dashboard
3. Set start command: `python bot.py`

### Koyeb
1. Create a new app → Deploy from GitHub
2. Set build command: `pip install -r requirements.txt`
3. Set run command: `python bot.py`
4. Add environment variables

### VPS (systemd)
```ini
# /etc/systemd/system/autofilterbot.service
[Unit]
Description=AutoFilter Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/AutoFilterBot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable autofilterbot
systemctl start autofilterbot
```

---

## 🔧 Caption & Template Variables

**Caption variables:** `{file_name}` · `{file_size}` · `{file_type}`

**IMDB template variables:** `{title}` · `{year}` · `{rating}` · `{genres}` · `{plot}`

---

## 🛡 License
MIT — free to use, modify, and distribute.
