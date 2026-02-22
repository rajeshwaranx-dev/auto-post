# 🚀 Deployment Fix Guide

## Why the Build Failed
1. `requirements.txt` was missing from the repo root
2. Python 3.14 is too new — Pyrogram doesn't support it yet

Both are now fixed in this updated repo.

---

## ✅ Fix Your GitHub Repo (do this once)

```bash
# 1. Clone your repo
git clone https://github.com/rajeshwaranx-dev/claude-filter
cd claude-filter

# 2. Copy ALL these files into your repo root (replacing old ones):
#    - requirements.txt
#    - .python-version
#    - runtime.txt
#    - render.yaml
#    - config.py
#    - bot.py
#    - Procfile
#    - database/  (folder)
#    - plugins/   (folder)
#    - utils/     (folder)

# 3. Commit and push
git add .
git commit -m "fix: add requirements.txt and pin Python 3.11"
git push origin main
```

---

## 🖥️ Render Deployment (Free Tier)

1. Go to https://render.com → **New → Background Worker**
2. Connect your GitHub repo `rajeshwaranx-dev/claude-filter`
3. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Python Version:** `3.11.9`  ← set this in Environment
4. Add these **Environment Variables**:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | From @BotFather |
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `FILES_DB_URI` | MongoDB Atlas URI |
| `USERS_DB_URI` | MongoDB Atlas URI (can be same) |
| `FILES_DB_NAME` | `AutoFilterFiles` |
| `USERS_DB_NAME` | `AutoFilterUsers` |
| `LOG_CHANNEL` | Your log channel ID (e.g. `-1001234567890`) |
| `ADMINS` | Your Telegram user ID (e.g. `123456789`) |
| `FSUB_CHANNEL` | Your FSub channel ID (or `0` to disable) |
| `SHORTLINK_URL` | e.g. `shrinkme.io` |
| `SHORTLINK_API` | Your shortlink API key |

5. Click **Create Background Worker** → Deploy!

---

## 🗄️ MongoDB Atlas (Free)

1. Go to https://cloud.mongodb.com → Create free cluster
2. **Database Access** → Add user with password
3. **Network Access** → Add IP `0.0.0.0/0` (allow all)
4. **Connect** → Copy the URI:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
   ```
5. Paste that URI into both `FILES_DB_URI` and `USERS_DB_URI` env vars
   (or use two separate clusters for isolation)

---

## ⚙️ Bot Setup in Telegram

1. Create bot via @BotFather → get `BOT_TOKEN`
2. Get `API_ID` and `API_HASH` from https://my.telegram.org
3. Create a log channel → make bot admin → copy channel ID
4. Create FSub channel → make bot admin with invite link permission
5. Get your user ID from @userinfobot

---

## 🧪 Test Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your values
python bot.py
```
