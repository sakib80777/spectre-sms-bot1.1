# Classic SMS Hub — নিরাপদ Starter

এটি User Bot + Admin Bot-এর প্রাথমিক ভিত্তি। এতে আছে:
- SQLite-এ স্থায়ী user data
- আসল Telegram membership verification
- referral start parameter ও referral count
- profile ও demo wallet
- admin statistics, user lookup ও demo credit adjustment

## চালানোর নিয়ম
1. Python 3.10+ ব্যবহার করুন।
2. `pip install -r requirements.txt`
3. `.env.example`-এর মানগুলো Replit Secrets / environment variables-এ দিন।
4. `python main.py` চালান।

## গুরুত্বপূর্ণ
- BotFather থেকে **নতুন** দুইটি token তৈরি করে Secrets-এ রাখুন। পুরোনো প্রকাশিত token revoke করুন।
- `REQUIRED_CHAT_IDS`-এ private/public channel বা group-এর numeric chat ID দিন।
- `REQUIRED_CHAT_LINKS`-এ সংশ্লিষ্ট invite/public links দিন। দুই তালিকার ক্রম ও সংখ্যা একই হতে হবে।
- বটকে required channel/group-এ admin/member status দেখার অনুমতি দিতে হবে।
- এই starter কোনো Facebook/Instagram verification number বা third-party OTP সংগ্রহ/ফরওয়ার্ড করে না।
- বাস্তব SMS testing integration-এর জন্য নিজের/অনুমোদিত provider-এর sandbox/API documentation দরকার।
