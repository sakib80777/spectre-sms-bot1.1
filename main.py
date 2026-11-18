import asyncio
import logging
import os
from datetime import datetime, timezone

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# -------------------- CONFIG --------------------
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN", "")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.sqlite3")

# Comma-separated numeric Telegram chat IDs, e.g. -1001234567890,-1009876543210
REQUIRED_CHAT_IDS = [
    int(x.strip()) for x in os.getenv("REQUIRED_CHAT_IDS", "").split(",")
    if x.strip()
]
# Public invite/user links shown to users; keep order aligned with REQUIRED_CHAT_IDS.
REQUIRED_CHAT_LINKS = [
    x.strip() for x in os.getenv("REQUIRED_CHAT_LINKS", "").split(",")
    if x.strip()
]
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("classic-sms-bot")

user_dp = Dispatcher()
admin_dp = Dispatcher()


# -------------------- DATABASE --------------------
async def db_init():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL NOT NULL DEFAULT 0,
                referrals INTEGER NOT NULL DEFAULT 0,
                referred_by INTEGER,
                joined_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS credit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()


async def register_user(message: Message, referral_id: int | None):
    uid = message.from_user.id
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
        exists = await cur.fetchone()
        if exists:
            await db.execute(
                "UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (message.from_user.username, message.from_user.first_name, uid)
            )
        else:
            valid_ref = None
            if referral_id and referral_id != uid:
                cur = await db.execute(
                    "SELECT user_id FROM users WHERE user_id=?", (referral_id,)
                )
                if await cur.fetchone():
                    valid_ref = referral_id

            await db.execute("""
                INSERT INTO users(user_id, username, first_name, referred_by, joined_at)
                VALUES(?,?,?,?,?)
            """, (
                uid, message.from_user.username, message.from_user.first_name,
                valid_ref, datetime.now(timezone.utc).isoformat()
            ))
            if valid_ref:
                await db.execute(
                    "UPDATE users SET referrals=referrals+1 WHERE user_id=?",
                    (valid_ref,)
                )
        await db.commit()


async def user_count():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        return (await cur.fetchone())[0]


async def add_credit(user_id: int, admin_id: int, amount: float, note: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        if not await cur.fetchone():
            return False
        await db.execute(
            "UPDATE users SET balance=balance+? WHERE user_id=?",
            (amount, user_id)
        )
        await db.execute("""
            INSERT INTO credit_log(user_id, admin_id, amount, note, created_at)
            VALUES(?,?,?,?,?)
        """, (user_id, admin_id, amount, note,
              datetime.now(timezone.utc).isoformat()))
        await db.commit()
        return True


# -------------------- KEYBOARDS / UI --------------------
def join_keyboard():
    kb = InlineKeyboardBuilder()
    for i, link in enumerate(REQUIRED_CHAT_LINKS):
        kb.button(text=f"Join community {i+1}", url=link)
    kb.button(text="I've joined — verify", callback_data="verify_join")
    kb.adjust(1)
    return kb.as_markup()


def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="SMS Demo Lab", callback_data="demo_info")
    kb.button(text="My Profile", callback_data="profile")
    kb.button(text="Referral", callback_data="referral")
    kb.button(text="Wallet", callback_data="wallet")
    kb.button(text="Help & Support", url=SUPPORT_URL)
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Statistics", callback_data="admin_stats")
    kb.button(text="User lookup", callback_data="admin_lookup_help")
    kb.button(text="How to add test credit", callback_data="admin_credit_help")
    kb.adjust(1)
    return kb.as_markup()


async def is_member(bot: Bot, user_id: int) -> bool:
    if not REQUIRED_CHAT_IDS:
        return True
    for chat_id in REQUIRED_CHAT_IDS:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            log.exception("Membership check failed for chat %s", chat_id)
            return False
    return True


async def send_dashboard(bot: Bot, user_id: int):
    await bot.send_message(
        user_id,
        "CLASSIC SMS HUB\n\nWelcome. Choose an option below.",
        reply_markup=main_menu()
    )


# -------------------- USER BOT --------------------
@user_dp.message(Command("start"))
async def start_user(message: Message, command: CommandObject, bot: Bot):
    ref_id = None
    if command.args and command.args.isdigit():
        ref_id = int(command.args)
    await register_user(message, ref_id)

    if await is_member(bot, message.from_user.id):
        await send_dashboard(bot, message.from_user.id)
    else:
        await message.answer(
            "To use the demo hub, first join the required communities, then tap verify.",
            reply_markup=join_keyboard()
        )


@user_dp.callback_query(F.data == "verify_join")
async def verify_join(call: CallbackQuery, bot: Bot):
    if await is_member(bot, call.from_user.id):
        await call.answer("Membership verified.")
        await call.message.edit_text(
            "CLASSIC SMS HUB\n\nMembership verified. Choose an option:",
            reply_markup=main_menu()
        )
    else:
        await call.answer("Please join every required community first.", show_alert=True)


@user_dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    row = await get_user(call.from_user.id)
    if not row:
        await call.answer("Send /start first.", show_alert=True)
        return
    name = row["first_name"] or "User"
    await call.message.edit_text(
        f"MY PROFILE\n\nName: {name}\n"
        f"User ID: {row['user_id']}\n"
        f"Balance: {row['balance']:.2f} credits\n"
        f"Referrals: {row['referrals']}\n"
        "Membership: Verified on access",
        reply_markup=main_menu()
    )
    await call.answer()


@user_dp.callback_query(F.data == "wallet")
async def wallet(call: CallbackQuery):
    row = await get_user(call.from_user.id)
    balance = row["balance"] if row else 0
    await call.message.edit_text(
        f"WALLET\n\nAvailable demo credits: {balance:.2f}\n"
        "This starter has no payment gateway. Credits can only be adjusted "
        "by the configured administrator for testing.",
        reply_markup=main_menu()
    )
    await call.answer()


@user_dp.callback_query(F.data == "referral")
async def referral(call: CallbackQuery, bot: Bot):
    me = await bot.get_me()
    row = await get_user(call.from_user.id)
    link = f"https://t.me/{me.username}?start={call.from_user.id}"
    await call.message.edit_text(
        f"REFERRAL\n\nYour invite link:\n{link}\n\n"
        f"Successful referrals: {row['referrals'] if row else 0}",
        reply_markup=main_menu()
    )
    await call.answer()


@user_dp.callback_query(F.data == "demo_info")
async def demo_info(call: CallbackQuery):
    await call.message.edit_text(
        "SMS DEMO LAB\n\n"
        "This starter is intentionally in demo mode. It does not provide "
        "Facebook/Instagram verification numbers, collect third-party OTPs, "
        "or bypass account verification. A lawful SMS testing provider or "
        "sandbox can be connected after its approved API documentation is reviewed.",
        reply_markup=main_menu()
    )
    await call.answer()


# -------------------- ADMIN BOT --------------------
@admin_dp.message(Command("start"))
async def admin_start(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Access denied.")
        return
    await message.answer("CLASSIC ADMIN CONSOLE", reply_markup=admin_menu())


@admin_dp.message(Command("stats"))
async def admin_stats_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"Registered users: {await user_count()}")


@admin_dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Access denied.", show_alert=True)
        return
    await call.message.edit_text(
        f"ADMIN STATISTICS\n\nRegistered users: {await user_count()}",
        reply_markup=admin_menu()
    )
    await call.answer()


@admin_dp.callback_query(F.data == "admin_lookup_help")
async def admin_lookup_help(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Access denied.", show_alert=True)
        return
    await call.message.answer("User lookup: use /user USER_ID")
    await call.answer()


@admin_dp.message(Command("user"))
async def admin_user_lookup(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    if not command.args or not command.args.isdigit():
        await message.answer("Usage: /user USER_ID")
        return
    row = await get_user(int(command.args))
    if not row:
        await message.answer("User not found.")
        return
    await message.answer(
        f"User: {row['user_id']}\nName: {row['first_name']}\n"
        f"Balance: {row['balance']:.2f}\nReferrals: {row['referrals']}"
    )


@admin_dp.callback_query(F.data == "admin_credit_help")
async def admin_credit_help(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Access denied.", show_alert=True)
        return
    await call.message.answer(
        "For demo testing only, use:\n/credit USER_ID AMOUNT NOTE\n"
        "Example: /credit 123456789 5.00 test_adjustment"
    )
    await call.answer()


@admin_dp.message(Command("credit"))
async def admin_credit(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    parts = (command.args or "").split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Usage: /credit USER_ID AMOUNT [NOTE]")
        return
    try:
        target_id = int(parts[0])
        amount = float(parts[1])
        note = parts[2] if len(parts) > 2 else "admin_demo_adjustment"
        if amount <= 0 or amount > 10000:
            raise ValueError
    except ValueError:
        await message.answer("Invalid user ID or amount. Amount must be > 0 and <= 10000.")
        return
    ok = await add_credit(target_id, message.from_user.id, amount, note)
    await message.answer("Demo credit added." if ok else "User not found.")


# -------------------- RUN BOTH BOTS --------------------
async def run_bot(token: str, dispatcher: Dispatcher, label: str):
    bot = Bot(token=token)
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()


async def main():
    if not USER_BOT_TOKEN or not ADMIN_BOT_TOKEN or not ADMIN_ID:
        raise RuntimeError(
            "Set USER_BOT_TOKEN, ADMIN_BOT_TOKEN and ADMIN_ID in environment secrets."
        )
    if len(REQUIRED_CHAT_IDS) != len(REQUIRED_CHAT_LINKS):
        raise RuntimeError(
            "REQUIRED_CHAT_IDS and REQUIRED_CHAT_LINKS must have the same number of entries."
        )
    await db_init()
    await asyncio.gather(
        run_bot(USER_BOT_TOKEN, user_dp, "user"),
        run_bot(ADMIN_BOT_TOKEN, admin_dp, "admin")
    )


if __name__ == "__main__":
    asyncio.run(main())
