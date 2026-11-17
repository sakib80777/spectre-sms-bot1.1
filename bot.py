import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# ১. কনফিগারেশন সেটিংস (এখানে তোমার টোকেনগুলো বসাও)
# ==========================================
USER_BOT_TOKEN = "9150625768:AAGFN3a8-tNGITvaaDcCFxvOhR26m6ajrpY"    # ক্লায়েন্ট/ইউজাররা যে বটে কাজ করবে তার টোকেন
ADMIN_BOT_TOKEN = "9021057671:AAHKv_QdjncaQISCyjPeKdIv3lDJRGCfK50"        # তুমি যেখান থেকে কন্ট্রোল করবে সেই অ্যাডমিন বটের টোকেন

ADMIN_ID = 6213339142                          # তোমার নিজস্ব টেলিগ্রাম ইউজার আইডি
OTP_CHANNEL_ID =-1004381508455                  # ওটিপি চ্যানেলের আইডি

# ফোর্স সাবস্ক্রাইবের জন্য চ্যানেল বা গ্রুপ
REQUIRED_CHANNELS = [
    {"title": "📢 Spectre SMS Channel", "url": "https://t.me/your_channel"},
    {"title": "💬 Support Group", "url": "https://t.me/your_group"}
]

logging.basicConfig(level=logging.INFO)

# দুটি আলাদা বট ইনস্ট্যান্স তৈরি করা হলো
user_bot = Bot(token=USER_BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

user_dp = Dispatcher(user_bot)
admin_dp = Dispatcher(admin_bot)


# ==========================================
# ২. ইউজার বট (Client Bot) ফ্লো ও হ্যান্ডলার
# ==========================================
@user_dp.message_handler(commands=['start'])
async def user_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        keyboard.add(InlineKeyboardButton(ch["title"], url=ch["url"]))
    
    keyboard.add(InlineKeyboardButton("✅ Verify & Open Bot", callback_data="verify_join"))
    
    await message.reply(
        "👋 **Spectre SMS** বটে আপনাকে স্বাগতম!\n\nবট ব্যবহার করতে হলে প্রথমে নিচের চ্যানেল ও গ্রুপগুলোতে জয়েন করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@user_dp.callback_query_handler(text="verify_join")
async def user_verify(callback_query: types.CallbackQuery):
    is_joined = True  # জয়েনিং চেক লজিক
    
    if is_joined:
        await user_bot.answer_callback_query(callback_query.id, "✅ ভেরিফিকেশন সফল!")
        
        # ইউজার মেনু (ক্লায়েন্টরা যা দেখবে)
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
    else:
        await user_bot.answer_callback_query(callback_query.id, "❌ আপনি সব চ্যানেল বা গ্রুপে জয়েন করেননি!", show_alert=True)


# ==========================================
# ৩. অ্যাডমিন বট (Admin Bot) ফ্লো ও কন্ট্রোল প্যানেল
# ==========================================
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

# রান করার জন্য পুলিং (উভয় বট একসাথে চলবে)
if __name__ == '__main__':
    import asyncio
    
    loop = asyncio.get_event_loop()
    print("Bot is running...")
    
    # একসাথে দুটি বট রান করার ব্যবস্থা
    loop.create_task(executor.start_polling(user_dp, skip_updates=True))
    loop.create_task(executor.start_polling(admin_dp, skip_updates=True))
    
    loop.run_forever()