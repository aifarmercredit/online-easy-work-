# Online Easy Work

Install: `pip install -r requirements.txt`
Run: `uvicorn backend:app --host 0.0.0.0 --port 8000`

Configure TELEGRAM_TOKEN, BOT_USERNAME and a REAL channel in CHANNEL_USERNAME. `@Online_essywork_bot` is a bot username, not a channel. Add your bot as channel admin for membership verification.

For production: use strict Telegram initData validation, implement server-side referral/deep-link registration, real video/ad completion callbacks, and an official payment API for automatic payouts.