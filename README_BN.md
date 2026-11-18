# Classic SMS Demo Hub — বাংলা নির্দেশিকা

এটি একটি নিরাপদ Telegram demo bot starter। এটি তৃতীয়-পক্ষের Facebook/Instagram বা অন্য অ্যাকাউন্টের OTP সংগ্রহ, ফরওয়ার্ড, বা verification bypass করে না। শুধু নিজের/অনুমোদিত নম্বর ও provider sandbox-এ বৈধ SMS testing workflow তৈরি করার ভিত্তি হিসেবে ব্যবহার করুন।

## ফাইল
- `main.py` — বটের মূল কোড
- `requirements.txt` — Python dependency
- `Dockerfile` — Railway-তে চালানোর নির্দেশনা
- `.env.example` — প্রয়োজনীয় environment variable-এর নমুনা

## GitHub-এ কোথায় রাখবেন
ZIP extract করে ফাইলগুলো repository-র মূল পৃষ্ঠায় (root) রাখুন। আলাদা folder-এর ভিতরে রাখবেন না, যদি না Dockerfile/Start Command সেই folder অনুযায়ী বদলানো হয়।

## Railway Variables
Railway → আপনার Service → Variables-এ:
- `BOT_TOKEN` = BotFather থেকে নতুন token
- `ADMIN_IDS` = আপনার Telegram numeric user ID (একাধিক হলে comma দিয়ে আলাদা)
- `DATABASE_PATH` = `/data/bot_data.sqlite3`

আসল token কখনো GitHub-এ দেবেন না। `.env` ফাইল commit করবেন না।

## Railway Volume
Service → Settings/Volumes থেকে `/data` mount path-এ একটি persistent volume যুক্ত করুন। তারপর `DATABASE_PATH=/data/bot_data.sqlite3` রাখুন। Volume ছাড়া SQLite ফাইল deployment/restart-এ হারিয়ে যেতে পারে।

## চালু করার আগে
1. পুরোনো প্রকাশিত bot token BotFather দিয়ে revoke করে নতুন token নিন।
2. একই token দিয়ে একাধিক Railway replica/service বা নিজের কম্পিউটারে একসঙ্গে polling চালাবেন না।
3. GitHub-এ `main.py`, `requirements.txt`, `Dockerfile`, `.env.example`, `README_BN.md` root-এ রাখুন।
4. Commit changes করুন; GitHub-connected Railway service স্বয়ংক্রিয়ভাবে deploy করতে পারে।
5. Railway Logs দেখুন।

## কমান্ড
- `/start`
- `/help`
- `/profile`
- `/referral`
- অ্যাডমিন: `/stats`
- অ্যাডমিন: `/credit USER_ID AMOUNT` (শুধু demo balance)
