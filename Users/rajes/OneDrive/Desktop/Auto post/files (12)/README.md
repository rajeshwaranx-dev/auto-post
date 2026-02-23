# 🎬 Telegram Auto Post Bot System

A production-ready, modular 2-bot system that auto-posts movies to Telegram
channels with IMDb metadata and private file delivery.

---

## 📁 Project Structure

```
telegram_autopost/
├── .env.example                  ← Copy to .env and fill in values
├── requirements.txt
├── autopost_bot.service          ← systemd unit for AutoPosterBot
├── filestore_bot.service         ← systemd unit for FileStoreBot
│
├── shared/                       ← Code shared by both bots
│   ├── __init__.py
│   ├── config.py                 ← All env-var loading & validation
│   ├── database.py               ← Motor async MongoDB interface
│   ├── imdb.py                   ← Async OMDb API wrapper
│   └── utils.py                  ← Title cleaning, quality detect, ID gen
│
├── autobot/                      ← BOT 1: AutoPosterBot
│   ├── __init__.py
│   └── main.py                   ← Pyrogram client + channel handler
│
└── filebot/                      ← BOT 2: FileStoreBot
    ├── __init__.py
    └── main.py                   ← Pyrogram client + /start handler
```

---

## ⚙️ Prerequisites

| Requirement        | Version      |
|--------------------|--------------|
| Ubuntu             | 22.04 LTS    |
| Python             | 3.10+        |
| MongoDB            | 6.x          |
| Telegram API ID    | my.telegram.org |

---

## 🚀 Quick Setup

### 1. Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip git
# MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | sudo gpg --dearmor -o /usr/share/keyrings/mongodb.gpg
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update && sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

### 2. Clone / Upload Project

```bash
sudo mkdir -p /opt/telegram_autopost
sudo chown ubuntu:ubuntu /opt/telegram_autopost
cd /opt/telegram_autopost
# Copy project files here
```

### 3. Create Virtual Environment & Install Packages

```bash
cd /opt/telegram_autopost
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env          # Fill in all required values
```

Required values:

| Variable               | Description                                      |
|------------------------|--------------------------------------------------|
| `API_ID`               | From https://my.telegram.org                    |
| `API_HASH`             | From https://my.telegram.org                    |
| `AUTO_POSTER_BOT_TOKEN`| From @BotFather                                 |
| `FILE_STORE_BOT_TOKEN` | From @BotFather                                 |
| `SOURCE_CHANNEL`       | Numeric ID of source channel (e.g. -100123…)   |
| `MAIN_CHANNEL`         | Numeric ID of main/public channel               |
| `FILE_STORE_BOT_USERNAME` | FileStoreBot's username (no @)              |
| `MONGO_URI`            | `mongodb://localhost:27017` (default)           |
| `OMDB_API_KEY`         | Free key from https://www.omdbapi.com/apikey.aspx |

### 5. Test Both Bots Manually

```bash
source venv/bin/activate

# Terminal 1
python -m autobot.main

# Terminal 2
python -m filebot.main
```

Upload a test video to your source channel and verify the flow.

### 6. Install systemd Services

```bash
sudo cp autopost_bot.service  /etc/systemd/system/
sudo cp filestore_bot.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now autopost_bot
sudo systemctl enable --now filestore_bot
```

### 7. Check Logs

```bash
sudo journalctl -u autopost_bot  -f
sudo journalctl -u filestore_bot -f
```

---

## 🔑 Bot Permissions

### AutoPosterBot
- Must be an **admin** in `SOURCE_CHANNEL` with "Read Messages" permission.
- Must be an **admin** in `MAIN_CHANNEL` with "Post Messages" permission.

### FileStoreBot
- Does **not** need to be in any channel.
- Users must have started a conversation with it (or it cannot send them files).

---

## 🎯 How It Works

```
SOURCE_CHANNEL                AutoPosterBot               MAIN_CHANNEL
      │                            │                            │
      │  video/document uploaded   │                            │
      │ ─────────────────────────► │                            │
      │                            │  clean_title()             │
      │                            │  extract_quality()         │
      │                            │  fetch_imdb_data()         │
      │                            │  generate_unique_id()      │
      │                            │  insert_movie() → MongoDB  │
      │                            │  build_deep_link()         │
      │                            │  send_photo(poster+caption)│
      │                            │ ──────────────────────────►│
      │                            │                            │

User clicks Download link → deep-link → FileStoreBot
      │                            │
      │  /start <unique_id>        │
      │ ─────────────────────────► │
      │                            │  get_movie_by_unique_id()
      │                            │  → MongoDB
      │                            │  send_video(file_id)
      │ ◄───────────────────────── │
      │  Receives file privately   │
```

---

## 🧹 Title Cleaning Examples

| Raw Filename | Cleaned Title | Quality |
|---|---|---|
| `Oppenheimer.2023.1080p.BluRay.x264.AAC-YIFY.mkv` | `Oppenheimer` | `1080p` |
| `The.Dark.Knight.2008.4K.HEVC.HDR.DTS-HD.mkv` | `The Dark Knight` | `4K` |
| `Spider-Man.No.Way.Home.2021.720p.WEB-DL.Tamil.mkv` | `Spider-Man No Way Home` | `720p` |
| `Avengers_Endgame_2019_2160p_HDR_x265.mp4` | `Avengers Endgame` | `4K` |

---

## 🛡️ Duplicate Protection

Before inserting, the bot checks:
```
db.movies.findOne({ cleaned_title: <title>, quality: <quality> })
```
If a match is found, the file is silently skipped. This prevents re-posting
the same movie at the same quality even if re-uploaded to the source channel.

---

## 📦 MongoDB Document Schema

```json
{
  "_id": "ObjectId",
  "unique_id": "aB3kR7Xz",
  "file_id": "BQACAgIAAxkBAAI...",
  "cleaned_title": "Oppenheimer",
  "quality": "1080p",
  "imdb": {
    "title": "Oppenheimer",
    "year": "2023",
    "rating": "8.3",
    "genre": "Biography, Drama, History",
    "director": "Christopher Nolan",
    "plot": "The story of American scientist J. Robert Oppenheimer...",
    "poster": "https://m.media-amazon.com/images/..."
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 🔧 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Bot not seeing source channel messages | Bot not admin or wrong channel ID | Add bot as admin, verify `SOURCE_CHANNEL` |
| `N/A` for all IMDb data | Wrong/expired OMDb key | Get a new free key at omdbapi.com |
| File not sent to user | User never started FileStoreBot | User must `/start` the bot first |
| MongoDB connection refused | mongod not running | `sudo systemctl start mongod` |
| `KeyError` on startup | Missing `.env` variable | Check all required vars are set |
