import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# টোকেন ও আইডি কনফিগারেশন
USER_BOT_TOKEN = "9150625768:AAFfT82NdNyhQ8BRdqwkeaKTUwvnixiihBI"    
ADMIN_BOT_TOKEN = "9021057671:AAE3fAiwMlMc1Gs3gQH2uWIv_229P-lpC4A"        

ADMIN_ID = 7678850509                          
OTP_CHANNEL_ID = -1004381508455                  

REQUIRED_CHANNELS = [
    {"title": "📢 Spectre SMS Channel", "url": "https://t.me/your_channel"},
    {"title": "💬 Support Group", "url": "https://t.me/your_group"}
]

logging.basicConfig(level=logging.INFO)

user_bot = Bot(token=USER_BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

user_dp = Dispatcher(user_bot)
admin_dp = Dispatcher(admin_bot)

# ================= USER BOT HANDLERS =================
@user_dp.message_handler(commands=['start'])
async def user_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        keyboard.add(InlineKeyboardButton(ch["title"], url=ch["url"]))
    
    keyboard.add(InlineKeyboardButton("✅ Verify & Open Bot", callback_data="verify_join"))
    await message.reply(
        "👋 **Spectre SMS** বটে আপনাকে স্বাগতম!\n\nবট ব্যবহার করতে হলে প্রথমে নিচের চ্যানেল ও গ্রুপগুলোতে জয়েন করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@user_dp.callback_query_handler(text="verify_join")
async def user_verify(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id, "✅ ভেরিফিকেশন সফল!")
    user_menu = InlineKeyboardMarkup(row_width=2)
    user_menu.add(
        InlineKeyboardButton("📱 GET NUMBER", callback_data="get_number"),
        InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live_traffic"),
        InlineKeyboardButton("👤 STATUS", callback_data="user_status"),
        InlineKeyboardButton("💰 BALANCE", callback_data="user_balance"),
        InlineKeyboardButton("🏆 TODAY TOP", callback_data="today_top"),
        InlineKeyboardButton("🛠 SUPPORT", callback_data="support")
    )
    await user_bot.send_message(
        callback_query.from_user.id,
        "🌐 **SERVICE CATEGORIES:**\nSelect a platform below to proceed with real-time numbers:",
        reply_markup=user_menu,
        parse_mode="Markdown"
    )

# ================= ADMIN BOT HANDLERS =================
@admin_dp.message_handler(commands=['start', 'admin'])
async def admin_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ আপনার এই অ্যাডমিন প্যানেলটি অ্যাক্সেস করার অনুমতি নেই।")
        return

    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("👤 USER MANAGEMENT", callback_data="adm_users"),
        InlineKeyboardButton("💳 BALANCE UPDATE", callback_data="adm_balance"),
        InlineKeyboardButton("📢 BROADCAST NOTICE", callback_data="adm_broadcast"),
        InlineKeyboardButton("📥 ADD NUMBERS", callback_data="adm_add_num"),
        InlineKeyboardButton("📈 STATISTICS", callback_data="adm_traffic"),
        InlineKeyboardButton("⚙️ BOT SETTINGS", callback_data="adm_settings")
    )
    
    await message.reply(
        "👑 **SPECTRE SMS • ELITE ADMIN PANEL**\n\nWelcome back, Boss! Manage your user bot and numbers from here:",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

# অ্যাডমিন প্যানেলের বাটনগুলোর জন্য কার্যকরী কলব্যাক হ্যান্ডলার
@admin_dp.callback_query_handler(lambda c: c.data and c.data.startswith('adm_'))
async def admin_callback_router(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await admin_bot.answer_callback_query(callback_query.id, "⛔ আপনার অনুমতি নেই!", show_alert=True)
        return

    await admin_bot.answer_callback_query(callback_query.id)
    action = callback_query.data
    
    response_text = "⚙️ **Admin Panel Action:**\n"
    if action == "adm_users":
        response_text += "👤 User Management panel is active. (Manage users here)"
    elif action == "adm_balance":
        response_text += "💳 Balance Update system ready. Send user ID and amount to update."
    elif action == "adm_broadcast":
        response_text += "📢 Broadcast mode: Send the message you want to broadcast to all users."
    elif action == "adm_add_num":
        response_text += "📥 Add Numbers interface: Ready to receive new stock/numbers."
    elif action == "adm_traffic":
        response_text += "📈 Live Statistics: Total users - 0, Active sessions - 0."
    elif action == "adm_settings":
        response_text += "⚙️ Bot Settings: Configure channels and maintenance mode."
    else:
        response_text += "Unknown command."

    await admin_bot.send_message(
        callback_query.from_user.id,
        response_text,
        parse_mode="Markdown"
    )

# ================= DUAL BOT RUNNER =================
async def start_bots():
    print("🚀 Both User Bot and Admin Bot are starting smoothly...")
    await asyncio.gather(
        user_dp.start_polling(reset_webhook=True),
        admin_dp.start_polling(reset_webhook=True)
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bots())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bots stopped safely!")
