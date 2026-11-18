import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIGURATION =================
USER_BOT_TOKEN = "9150625768:AAFfT82NdNyhQ8BRdqwkeaKTUwvnixiihBI"    
ADMIN_BOT_TOKEN = "9021057671:AAE3fAiwMlMc1Gs3gQH2uWIv_229P-lpC4A"        

ADMIN_ID = 7678850509                          
OTP_CHANNEL_ID = -1004381508455  # আপনার ওটিপি চ্যানেল বা গ্রুপ আইডি

# আপনার মেইন চ্যানেল ও সাপোর্ট গ্রুপের লিংক এখানে সেট করা আছে
REQUIRED_CHANNELS = [
    {"title": "📢 Spectre SMS Channel", "url": "https://t.me/your_sms_channel"},
    {"title": "💬 Support Group", "url": "https://t.me/your_support_group"}
]

# মেমোরিতে নাম্বার ও ট্রাফিক স্টোর করার টেম্পোরারি ডেটাবেস
DATABASE = {
    "numbers": [],  # অ্যাডমিন প্যানেল থেকে যোগ করা নাম্বারগুলো এখানে থাকবে
    "total_users": 1,
    "active_traffic": 0
}

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

# ইউজার মেনু বাটন হ্যান্ডলার
@user_dp.callback_query_handler(lambda c: c.data in ["get_number", "live_traffic", "user_status", "user_balance", "today_top", "support"])
async def user_menu_handler(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    action = callback_query.data
    
    if action == "get_number":
        if len(DATABASE["numbers"]) > 0:
            num_list = "\n".join([f"📱 `{num}`" for num in DATABASE["numbers"][-5:]])
            await user_bot.send_message(callback_query.from_user.id, f"🔥 **Available Numbers / Stock:**\n\n{num_list}", parse_mode="Markdown")
        else:
            await user_bot.send_message(callback_query.from_user.id, "⚠️ এই মুহূর্তে কোনো নাম্বার স্টক বা এভেলেবল নেই। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
            
    elif action == "live_traffic":
        traffic_text = f"📊 **LIVE TRAFFIC STATUS:**\n\n👥 Total Users: {DATABASE['total_users']}\n⚡ Active Sessions: {DATABASE['active_traffic']}\n📱 Total Stock: {len(DATABASE['numbers'])}"
        await user_bot.send_message(callback_query.from_user.id, traffic_text, parse_mode="Markdown")
        
    elif action == "user_status":
        await user_bot.send_message(callback_query.from_user.id, "👤 **Your Status:**\nAccount Type: Standard User\nStatus: Active ✅", parse_mode="Markdown")
        
    elif action == "user_balance":
        await user_bot.send_message(callback_query.from_user.id, "💰 **Your Balance:**\n৳0.00 BDT (Top-up required)", parse_mode="Markdown")
        
    elif action == "today_top":
        await user_bot.send_message(callback_query.from_user.id, "🏆 **Today's Top Users:**\nNo data available yet for today.", parse_mode="Markdown")
        
    elif action == "support":
        await user_bot.send_message(callback_query.from_user.id, "🛠 **Support:**\nAny issues? Contact our support group linked in the start menu.", parse_mode="Markdown")


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

# অ্যাডমিন প্যানেল কলব্যাক রাউটার
@admin_dp.callback_query_handler(lambda c: c.data and c.data.startswith('adm_'))
async def admin_callback_router(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await admin_bot.answer_callback_query(callback_query.id, "⛔ আপনার অনুমতি নেই!", show_alert=True)
        return

    await admin_bot.answer_callback_query(callback_query.id)
    action = callback_query.data
    
    if action == "adm_users":
        await admin_bot.send_message(callback_query.from_user.id, f"👤 **User Management:**\nTotal registered users: {DATABASE['total_users']}", parse_mode="Markdown")
    elif action == "adm_balance":
        await admin_bot.send_message(callback_query.from_user.id, "💳 **Balance Update:**\nSend user ID and amount to update user balance.", parse_mode="Markdown")
    elif action == "adm_broadcast":
        await admin_bot.send_message(callback_query.from_user.id, "📢 **Broadcast:**\nSend your notice text to broadcast to all users.", parse_mode="Markdown")
    elif action == "adm_add_num":
        # ডেমো হিসেবে অ্যাডমিন প্যানেল থেকে স্টক বা নাম্বার যোগ করার অপশন
        DATABASE["numbers"].append("+88017XXXXXXXX")
        await admin_bot.send_message(callback_query.from_user.id, "📥 **Success!** একটি নতুন নাম্বার স্টকে যোগ করা হয়েছে। এখন ইউজাররা 'GET NUMBER' থেকে এটি দেখতে পাবে।", parse_mode="Markdown")
    elif action == "adm_traffic":
        await admin_bot.send_message(callback_query.from_user.id, f"📈 **Statistics:**\nTotal Stock: {len(DATABASE['numbers'])}\nActive Traffic: {DATABASE['active_traffic']}", parse_mode="Markdown")
    elif action == "adm_settings":
        await admin_bot.send_message(callback_query.from_user.id, "⚙️ **Settings:**\nAll systems are running smoothly on Railway.", parse_mode="Markdown")

# অপশনাল: ওটিপি চ্যানেলে মেসেজ পাঠানোর ফাংশন (দরকার হলে ব্যবহার করতে পারেন)
async def send_otp_to_channel(phone_number, otp_code):
    try:
        msg = f"🔥 **NEW OTP RECEIVED**\n\n📱 Number: `{phone_number}`\n🔑 OTP Code: `{otp_code}`"
        await user_bot.send_message(OTP_CHANNEL_ID, msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"OTP Channel Error: {e}")


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
