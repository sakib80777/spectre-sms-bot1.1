import asyncio
import logging
import os
from contextlib import suppress

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.sqlite3")

dp = Dispatcher()


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance INTEGER NOT NULL DEFAULT 0,
                referred_by INTEGER,
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_user(message: Message, referrer_id: int | None = None):
    user = message.from_user
    if user is None:
        return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
        exists = await cur.fetchone()
        if exists is None:
            valid_referrer = None
            if referrer_id and referrer_id != user.id:
                cur = await db.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)
                )
                if await cur.fetchone():
                    valid_referrer = referrer_id
            await db.execute(
                """INSERT INTO users(user_id, username, first_name, referred_by)
                   VALUES (?, ?, ?, ?)""",
                (user.id, user.username, user.first_name, valid_referrer),
            )
        else:
            await db.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (user.username, user.first_name, user.id),
            )
        await db.commit()


@dp.message(CommandStart())
async def start(message: Message):
    referrer_id = None
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].startswith("ref_"):
        candidate = parts[1][4:]
        if candidate.isdigit():
            referrer_id = int(candidate)

    await save_user(message, referrer_id)
    await message.answer(
        "স্বাগতম! এটি একটি নিরাপদ SMS testing/demo hub।\n\n"
        "এখানে কোনো তৃতীয়-পক্ষের অ্যাকাউন্টের OTP সংগ্রহ বা ফরওয়ার্ড করা হয় না।\n\n"
        "কমান্ড:\n"
        "/profile — প্রোফাইল ও ডেমো ব্যালেন্স\n"
        "/referral — আপনার রেফারেল লিংক\n"
        "/help — সাহায্য"
    )


@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "সাহায্য:\n"
        "/start — বট শুরু\n"
        "/profile — আপনার তথ্য\n"
        "/referral — রেফারেল লিংক\n\n"
        "এটি কেবল অনুমোদিত নম্বর ও sandbox-ভিত্তিক পরীক্ষার জন্য ডেমো।"
    )


@dp.message(Command("profile"))
async def profile(message: Message):
    await save_user(message)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT balance, joined_at FROM users WHERE user_id = ?",
            (message.from_user.id,),
        )
        row = await cur.fetchone()
    balance, joined_at = row if row else (0, "N/A")
    await message.answer(
        f"আপনার প্রোফাইল\n"
        f"নাম: {message.from_user.full_name}\n"
        f"ইউজার ID: {message.from_user.id}\n"
        f"ডেমো ব্যালেন্স: {balance}\n"
        f"যোগ দিয়েছেন: {joined_at}"
    )


@dp.message(Command("referral"))
async def referral(message: Message, bot: Bot):
    await save_user(message)
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?",
            (message.from_user.id,),
        )
        count = (await cur.fetchone())[0]
    await message.answer(f"আপনার রেফারেল লিংক:\n{link}\n\nরেফারেল ব্যবহারকারী: {count}")


@dp.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("এই কমান্ডটি শুধু অ্যাডমিনের জন্য।")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total = (await cur.fetchone())[0]
    await message.answer(f"বট পরিসংখ্যান\nমোট নিবন্ধিত ব্যবহারকারী: {total}")


@dp.message(Command("credit"))
async def credit(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("এই কমান্ডটি শুধু অ্যাডমিনের জন্য।")
    parts = (message.text or "").split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return await message.answer("ব্যবহার: /credit USER_ID AMOUNT")
    target_id, amount = int(parts[1]), int(parts[2])
    if amount < 1:
        return await message.answer("Amount অবশ্যই ১ বা তার বেশি হতে হবে।")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (target_id,))
        if await cur.fetchone() is None:
            return await message.answer("এই User ID বটের ডেটাবেসে নেই।")
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, target_id),
        )
        await db.commit()
    await message.answer("ডেমো ক্রেডিট যোগ হয়েছে।")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN সেট করা নেই। Railway Variables-এ BOT_TOKEN যোগ করুন।")
    logging.basicConfig(level=logging.INFO)
    await init_db()
    bot = Bot(BOT_TOKEN)
    try:
        # Only one running polling instance should use this token.
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
