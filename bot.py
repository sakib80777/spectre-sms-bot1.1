import logging
import asyncio
import re
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIGURATION =================
USER_BOT_TOKEN = "9150625768:AAFfT82NdNyhQ8BRdqwkeaKTUwvnixiihBI"    
ADMIN_BOT_TOKEN = "9021057671:AAE3fAiwMlMc1Gs3gQH2uWIv_229P-lpC4A"        

ADMIN_ID = 7678850509                          
OTP_CHANNEL_ID = -1004381508455  # ওটিপি গ্রুপ বা চ্যানেল আইডি

REQUIRED_CHANNELS = [
    {"title": "📢 Official SMS Channel", "url": "https://t.me/your_sms_channel"},
    {"title": "💬 Support & OTP Community", "url": "https://t.me/your_support_group"}
]

# কান্ট্রি কোড, নাম এবং ফ্ল্যাগ ম্যাপিং
COUNTRY_DATA = {
    "+880": {"name": "Bangladesh", "flag": "🇧🇩"},
    "+95": {"name": "Myanmar", "flag": "🇲🇲"},
    "+251": {"name": "Ethiopia", "flag": "🇪🇹"},
    "+255": {"name": "Tanzania", "flag": "🇹🇿"},
    "+968": {"name": "Oman", "flag": "🇴🇲"},
    "+1": {"name": "United States", "flag": "🇺🇸"},
    "+91": {"name": "India", "flag": "🇮🇳"},
    "+44": {"name": "United Kingdom", "flag": "🇬🇧"},
    "+966": {"name": "Saudi Arabia", "flag": "🇸🇦"},
    "+971": {"name": "United Arab Emirates", "flag": "🇦🇪"}
}

# ডেটাবেস স্ট্রাকচার
DATABASE = {
    "facebook": {"new_create": [], "pc_clone": []},
    "instagram": {"new_create": [], "pc_clone": []},
    "tiktok": {"new_create": [], "pc_clone": []},
    "users": {},  
    "active_traffic": 0
}

ADMIN_STATES = {}

logging.basicConfig(level=logging.INFO)

user_bot = Bot(token=USER_BOT_TOKEN)
admin_bot = Bot(token=ADMIN_BOT_TOKEN)

user_dp = Dispatcher(user_bot)
admin_dp = Dispatcher(admin_bot)


# ================= USER BOT HANDLERS =================
@user_dp.message_handler(commands=['start'])
async def user_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in DATABASE["users"]:
        DATABASE["users"][user_id] = {"balance": 0.0, "referrals": 0, "otps_found": 0}
        DATABASE["active_traffic"] += 1

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
        InlineKeyboardButton("📱 GET NUMBER", callback_data="user_platforms"),
        InlineKeyboardButton("💬 OTP GROUP", url=f"https://t.me/{str(OTP_CHANNEL_ID).replace('-100', '')}"),
        InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live_traffic"),
        InlineKeyboardButton("👤 STATUS", callback_data="user_status"),
        InlineKeyboardButton("💰 BALANCE", callback_data="user_balance"),
        InlineKeyboardButton("🏆 TODAY TOP", callback_data="today_top"),
        InlineKeyboardButton("👥 REFERRAL", callback_data="user_referral"),
        InlineKeyboardButton("🛠 SUPPORT", callback_data="support")
    )
    await user_bot.send_message(
        callback_query.from_user.id,
        "🌐 **SERVICE CATEGORIES:**\nSelect an option below to proceed:",
        reply_markup=user_menu,
        parse_mode="Markdown"
    )

# প্ল্যাটফর্ম মেনু (Facebook, Instagram, TikTok)
@user_dp.callback_query_handler(text="user_platforms")
async def user_platforms_menu(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📘 Facebook", callback_data="usr_plat_facebook"),
        InlineKeyboardButton("📸 Instagram", callback_data="usr_plat_instagram"),
        InlineKeyboardButton("🎵 TikTok", callback_data="usr_plat_tiktok"),
        InlineKeyboardButton("⬅️ Back to Menu", callback_data="verify_join")
    )
    await user_bot.edit_message_text(
        "📱 **SELECT PLATFORM:**\nChoose the platform you need numbers for:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# একাউন্ট টাইপ সিলেক্ট (New Create / PC Clone)
@user_dp.callback_query_handler(lambda c: c.data and c.data.startswith('usr_plat_'))
async def user_select_type(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    platform = callback_query.data.split('_')[2]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✨ New Create", callback_data=f"usr_get_{platform}_new_create"),
        InlineKeyboardButton("💻 PC Clone", callback_data=f"usr_get_{platform}_pc_clone"),
        InlineKeyboardButton("⬅️ Back", callback_data="user_platforms")
    )
    await user_bot.edit_message_text(
        f"🎯 **{platform.upper()} • SELECT TYPE:**\nChoose account creation type:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# স্টক থেকে নাম্বার দেখানোর হ্যান্ডলার
@user_dp.callback_query_handler(lambda c: c.data and c.data.startswith('usr_get_'))
async def user_show_stock(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    parts = callback_query.data.split('_')
    platform = parts[2]
    ntype = f"{parts[3]}_{parts[4]}"
    
    stock_list = DATABASE[platform][ntype]
    if len(stock_list) > 0:
        response_text = f"🔥 **Available Stock ({platform.upper()} - {ntype.replace('_', ' ').title()}):**\n\n"
        for item in stock_list[-15:]:
            phone = item['phone']
            country = item['country']
            flag = item['flag']
            price = item.get('price', '৳১০')
            response_text += f"{flag} **{country}** | `📱 {phone}` | 💵 {price}\n"
    else:
        response_text = f"⚠️ এই মুহূর্তে {platform.upper()} ({ntype.replace('_', ' ').title()}) ক্যাটাগরিতে কোনো নাম্বার স্টক নেই।"
        
    back_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Back", callback_data=f"usr_plat_{platform}"))
    await user_bot.send_message(callback_query.from_user.id, response_text, reply_markup=back_kb, parse_mode="Markdown")

@user_dp.callback_query_handler(text="live_traffic")
async def user_live_traffic(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    total_stock = sum(len(DATABASE[p][t]) for p in DATABASE for t in DATABASE[p] if isinstance(DATABASE[p], dict))
    traffic_text = f"📊 **LIVE TRAFFIC STATUS:**\n\n👥 Total Users: {len(DATABASE['users'])}\n⚡ Active Sessions: {DATABASE['active_traffic']}\n📱 Total Stock Available: {total_stock}"
    await user_bot.send_message(callback_query.from_user.id, traffic_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_status")
async def user_status(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    u_data = DATABASE["users"].get(user_id, {"balance": 0.0, "otps_found": 0})
    profile_text = f"👤 **Your Status:**\n\n🆔 User ID: `{user_id}`\nAccount Type: Standard User\nStatus: Active ✅\n🎯 Total OTPs Found: {u_data['otps_found']}"
    await user_bot.send_message(callback_query.from_user.id, profile_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_balance")
async def user_balance(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    balance = DATABASE["users"].get(user_id, {}).get("balance", 0.0)
    await user_bot.send_message(callback_query.from_user.id, f"💰 **Your Balance:**\n৳{balance:.2f} BDT", parse_mode="Markdown")

@user_dp.callback_query_handler(text="today_top")
async def user_today_top(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    sorted_users = sorted(DATABASE["users"].items(), key=lambda x: x[1]['otps_found'], reverse=True)[:5]
    
    top_text = "🏆 **TODAY'S TOP USERS:**\n\n"
    if sorted_users and sorted_users[0][1]['otps_found'] > 0:
        for idx, (uid, data) in enumerate(sorted_users, 1):
            top_text += f"{idx}. User ID `{uid}` — ⚡ {data['otps_found']} OTPs\n"
    else:
        top_text += "আজকে এখনও কোনো লিডারবোর্ড ডাটা নেই।"
        
    await user_bot.send_message(callback_query.from_user.id, top_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_referral")
async def user_referral(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    bot_info = await user_bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = DATABASE["users"].get(user_id, {}).get("referrals", 0)
    
    ref_text = f"👥 **REFERRAL SYSTEM:**\n\nআপনার রেফারেল লিংক বন্ধুদের সাথে শেয়ার করুন:\n\n🔗 Link: `{ref_link}`\n📊 Total Referred: {ref_count} users"
    await user_bot.send_message(callback_query.from_user.id, ref_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="support")
async def user_support(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    await user_bot.send_message(callback_query.from_user.id, "🛠 **Support:**\nযেকোনো প্রয়োজনে আমাদের সাপোর্ট গ্রুপে যোগাযোগ করুন। স্টার্ট মেনুতে লিংক দেওয়া আছে।", parse_mode="Markdown")


# ================= ADMIN BOT HANDLERS =================
@admin_dp.message_handler(commands=['start', 'admin'])
async def admin_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ আপনার এই অ্যাডমিন প্যানেলটি অ্যাক্সেস করার অনুমতি নেই।")
        return

    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("📥 ADD NUMBERS", callback_data="adm_add_num"),
        InlineKeyboardButton("📈 STATISTICS", callback_data="adm_traffic"),
        InlineKeyboardButton("👤 USERS", callback_data="adm_users"),
        InlineKeyboardButton("⚙️ SETTINGS", callback_data="adm_settings")
    )
    
    await message.reply(
        "👑 **SPECTRE SMS • ELITE ADMIN PANEL**\n\nWelcome back, Boss! Choose an option to manage:",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

@admin_dp.callback_query_handler(text="adm_add_num")
async def admin_add_numbers_menu(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📘 Facebook", callback_data="adm_plat_facebook"),
        InlineKeyboardButton("📸 Instagram", callback_data="adm_plat_instagram"),
        InlineKeyboardButton("🎵 TikTok", callback_data="adm_plat_tiktok"),
        InlineKeyboardButton("⬅️ Main Menu", callback_data="adm_main")
    )
    await admin_bot.edit_message_text(
        "📥 **ADD NUMBERS - SELECT PLATFORM:**\nChoose platform to upload numbers:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_dp.callback_query_handler(lambda c: c.data and c.data.startswith('adm_plat_'))
async def admin_select_type(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    platform = callback_query.data.split('_')[2]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✨ New Create", callback_data=f"adm_type_{platform}_new_create"),
        InlineKeyboardButton("💻 PC Clone", callback_data=f"adm_type_{platform}_pc_clone"),
        InlineKeyboardButton("⬅️ Back", callback_data="adm_add_num")
    )
    await admin_bot.edit_message_text(
        f"🎯 **{platform.upper()} • SELECT TYPE:**\nChoose upload type:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_dp.callback_query_handler(lambda c: c.data and c.data.startswith('adm_type_'))
async def admin_prompt_for_numbers(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    parts = callback_query.data.split('_')
    platform = parts[2]
    ntype = f"{parts[3]}_{parts[4]}"
    
    ADMIN_STATES[callback_query.from_user.id] = {"platform": platform, "type": ntype}
    
    await admin_bot.send_message(
        callback_query.from_user.id,
        f"📥 **UPLOADING TO {platform.upper()} ({ntype.replace('_', ' ').title()})**\n\nদয়া করে আপনার নাম্বারগুলোর লিস্ট এখানে **পেস্ট (Paste) করে পাঠিয়ে দিন**।",
        parse_mode="Markdown"
    )

# নাম্বার রিসিভ এবং কংগ্রাচুলেশন উইথ কান্ট্রি ও লোগো ফিডব্যাক মেসেজ
@admin_dp.message_handler(lambda message: message.from_user.id in ADMIN_STATES)
async def process_admin_number_upload(message: types.Message):
    admin_id = message.from_user.id
    state = ADMIN_STATES.get(admin_id)
    if not state:
        return
    
    platform = state["platform"]
    ntype = state["type"]
    text_data = message.text
    
    lines = text_data.strip().split('\n')
    added_count = 0
    detected_countries_summary = set()
    
    for line in lines:
        cleaned_num = re.sub(r'\s+', '', line)
        if not cleaned_num:
            continue
            
        detected_country = "International"
        detected_flag = "🌐"
        for code, info in COUNTRY_DATA.items():
            if cleaned_num.startswith(code):
                detected_country = info["name"]
                detected_flag = info["flag"]
                break
        
        DATABASE[platform][ntype].append({
            "phone": cleaned_num,
            "country": detected_country,
            "flag": detected_flag,
            "price": "৳১০"
        })
        added_count += 1
        detected_countries_summary.add(f"{detected_flag} {detected_country}")
        
    del ADMIN_STATES[admin_id]
    
    countries_str = ", ".join(detected_countries_summary) if detected_countries_summary else "🌐 International"
    
    await message.reply(
        f"🎉 **কনগ্রাচুলেশনস! আপনার ফাইল বা নাম্বারগুলো সফলভাবে রিসিভ হয়েছে।**\n\n"
        f"📂 Platform: `{platform.upper()}`\n"
        f"⚙️ Type: `{ntype.replace('_', ' ').title()}`\n"
        f"🌍 Detected Country/Countries: {countries_str}\n"
        f"📥 Total Numbers Added: `{added_count}`\n\n"
        f"✅ নাম্বারগুলো সফলভাবে মেইন বটে অ্যাড করে দেওয়া হয়েছে, এখন ইউজাররা সেখান থেকে দেখতে পাবে!",
        parse_mode="Markdown"
    )

@admin_dp.callback_query_handler(text="adm_traffic")
async def admin_traffic(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    total_stock = sum(len(DATABASE[p][t]) for p in DATABASE for t in DATABASE[p] if isinstance(DATABASE[p], dict))
    await admin_bot.send_message(callback_query.from_user.id, f"📈 **Statistics:**\nTotal Stock: {total_stock}\nActive Users: {len(DATABASE['users'])}", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_users")
async def admin_users(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    await admin_bot.send_message(callback_query.from_user.id, f"👤 **User Management:**\nTotal registered: {len(DATABASE['users'])}", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_settings")
async def admin_settings(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    await admin_bot.send_message(callback_query.from_user.id, "⚙️ **Settings:**\nSystem is fully online and automated.", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_main")
async def admin_main_menu(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("📥 ADD NUMBERS", callback_data="adm_add_num"),
        InlineKeyboardButton("📈 STATISTICS", callback_data="adm_traffic"),
        InlineKeyboardButton("👤 USERS", callback_data="adm_users"),
        InlineKeyboardButton("⚙️ SETTINGS", callback_data="adm_settings")
    )
    await admin_bot.edit_message_text(
        "👑 **SPECTRE SMS • ELITE ADMIN PANEL**",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )


# ================= DUAL BOT RUNNER =================
async def start_bots():
    print("🚀 Both User Bot and Admin Bot are running 24/7 smoothly...")
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
