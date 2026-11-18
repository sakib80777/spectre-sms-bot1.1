import logging
import asyncio
import re
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIGURATION =================
USER_BOT_TOKEN = "9150625768:AAFfT82NdNyhQ8BRdqwkeaKTUwvnixiihBI"    
ADMIN_BOT_TOKEN = "9021057671:AAE3fAiwMlMc1Gs3gQH2uWIv_229P-lpC4A"        

ADMIN_ID = 7678850509                          
OTP_CHANNEL_ID = -1004381508455  # লাইভ ওটিপি গ্রুপ আইডি

REQUIRED_CHANNELS = [
    {"title": "📢 Official SMS Channel", "url": "https://t.me/your_sms_channel"},
    {"title": "💬 Support & OTP Community", "url": "https://t.me/your_support_group"}
]

# কান্ট্রি কোড, নাম এবং ফ্ল্যাগ ম্যাপিং (সুদান +249 সহ অন্যান্য দেশ)
COUNTRY_DATA = {
    "+249": {"name": "Sudan", "flag": "🇸🇩"},
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
    
    keyboard.add(InlineKeyboardButton("🚀 Enter Service Hub", callback_data="verify_join"))
    await message.reply(
        "✨ **Welcome to Premium SMS Gateway** ✨\n\nবটটি ব্যবহার করতে প্রথমে নিচের চ্যানেল ও গ্রুপগুলোতে জয়েন করুন:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@user_dp.callback_query_handler(text="verify_join")
async def user_verify(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id, "⚡ Access Granted!")
    user_menu = InlineKeyboardMarkup(row_width=2)
    user_menu.add(
        InlineKeyboardButton("📱 GET NUMBER", callback_data="user_platforms"),
        InlineKeyboardButton("💬 LIVE OTP GROUP", url=f"https://t.me/{str(OTP_CHANNEL_ID).replace('-100', '')}"),
        InlineKeyboardButton("📊 LIVE TRAFFIC", callback_data="live_traffic"),
        InlineKeyboardButton("👤 MY PROFILE", callback_data="user_status"),
        InlineKeyboardButton("💰 WALLET", callback_data="user_balance"),
        InlineKeyboardButton("🏆 LEADERBOARD", callback_data="today_top"),
        InlineKeyboardButton("👥 REFERRAL", callback_data="user_referral"),
        InlineKeyboardButton("🛠 HELP & SUPPORT", callback_data="support")
    )
    await user_bot.send_message(
        callback_query.from_user.id,
        "🌟 **DASHBOARD MENU:**\nআপনার প্রয়োজনীয় অপশনটি নিচে থেকে সিলেক্ট করুন:",
        reply_markup=user_menu,
        parse_mode="Markdown"
    )

@user_dp.callback_query_handler(text="user_platforms")
async def user_platforms_menu(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📘 Facebook", callback_data="usr_plat_facebook"),
        InlineKeyboardButton("📸 Instagram", callback_data="usr_plat_instagram"),
        InlineKeyboardButton("🎵 TikTok", callback_data="usr_plat_tiktok"),
        InlineKeyboardButton("🔙 Main Menu", callback_data="verify_join")
    )
    await user_bot.edit_message_text(
        "📂 **SELECT PLATFORM:**\nযে প্ল্যাটফর্মের জন্য নাম্বার নিতে চান তা বেছে নিন:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@user_dp.callback_query_handler(lambda c: c.data and c.data.startswith('usr_plat_'))
async def user_select_type(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    platform = callback_query.data.split('_')[2]
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✨ New Create", callback_data=f"usr_get_{platform}_new_create"),
        InlineKeyboardButton("💻 PC Clone", callback_data=f"usr_get_{platform}_pc_clone"),
        InlineKeyboardButton("🔙 Back", callback_data="user_platforms")
    )
    await user_bot.edit_message_text(
        f"🎯 **{platform.upper()} • ACCOUNT TYPE:**\nএকাউন্ট তৈরির ধরণ সিলেক্ট করুন:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# স্টক থেকে নাম্বার দেখানোর হ্যান্ডলার এবং ডাইনামিক Change Number লজিক
@user_dp.callback_query_handler(lambda c: c.data and c.data.startswith('usr_get_'))
async def user_show_stock(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id, "🔄 Fetching Number...")
    parts = callback_query.data.split('_')
    platform = parts[2]
    ntype = f"{parts[3]}_{parts[4]}"
    
    stock_list = DATABASE[platform][ntype]
    if len(stock_list) > 0:
        # সর্বোচ্চ ২টি বা ৩টি নাম্বার দেখাবে, ডলার সেন্ট ফরম্যাটে (কোনো টাকার অংক ছাড়াই)
        current_batch = stock_list[-2:] 
        response_text = f"🔥 **Live Number Feed ({platform.upper()} - {ntype.replace('_', ' ').title()}):**\n\n"
        for item in current_batch:
            phone = item['phone']
            country = item['country']
            flag = item['flag']
            price = item.get('price', '$0.20') # শুধুমাত্র ডলার সেন্ট অ্যামাউন্ট
            response_text += f"{flag} **{country}**\n`📱 {phone}`\n💵 Price: {price}\n-------------------\n"
        
        # Change Number এবং Live OTP Group বাটন
        action_kb = InlineKeyboardMarkup(row_width=1)
        action_kb.add(
            InlineKeyboardButton("🔄 Change Number", callback_data=f"usr_get_{platform}_{ntype}"),
            InlineKeyboardButton("💬 Live OTP Group", url=f"https://t.me/{str(OTP_CHANNEL_ID).replace('-100', '')}"),
            InlineKeyboardButton("🔙 Back to Platform", callback_data=f"usr_plat_{platform}")
        )
    else:
        response_text = f"⚠️ এই মুহূর্তে {platform.upper()} ({ntype.replace('_', ' ').title()}) ক্যাটাগরিতে কোনো নাম্বার স্টক নেই। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
        action_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Back", callback_data=f"usr_plat_{platform}"))
        
    try:
        await user_bot.edit_message_text(
            response_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=action_kb,
            parse_mode="Markdown"
        )
    except Exception:
        await user_bot.send_message(
            callback_query.from_user.id,
            response_text,
            reply_markup=action_kb,
            parse_mode="Markdown"
        )

@user_dp.callback_query_handler(text="live_traffic")
async def user_live_traffic(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    total_stock = sum(len(DATABASE[p][t]) for p in DATABASE for t in DATABASE[p] if isinstance(DATABASE[p], dict))
    traffic_text = f"📊 **SYSTEM LIVE TRAFFIC:**\n\n👥 Total Members: `{len(DATABASE['users'])}`\n⚡ Active Sessions: `{DATABASE['active_traffic']}`\n📱 Available Stock: `{total_stock}`"
    await user_bot.send_message(callback_query.from_user.id, traffic_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_status")
async def user_status(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    u_data = DATABASE["users"].get(user_id, {"balance": 0.0, "otps_found": 0})
    profile_text = f"👤 **USER PROFILE INFO:**\n\n🆔 Telegram ID: `{user_id}`\n🔰 Tier: Premium Member\n✅ Status: Active & Verified\n🎯 Verified OTPs: `{u_data['otps_found']}`"
    await user_bot.send_message(callback_query.from_user.id, profile_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_balance")
async def user_balance(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    balance = DATABASE["users"].get(user_id, {}).get("balance", 0.0)
    await user_bot.send_message(callback_query.from_user.id, f"💰 **WALLET BALANCE:**\n\n${balance:.2f}", parse_mode="Markdown")

@user_dp.callback_query_handler(text="today_top")
async def user_today_top(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    sorted_users = sorted(DATABASE["users"].items(), key=lambda x: x[1]['otps_found'], reverse=True)[:5]
    
    top_text = "🏆 **TODAY'S TOP PERFORMERS:**\n\n"
    if sorted_users and sorted_users[0][1]['otps_found'] > 0:
        for idx, (uid, data) in enumerate(sorted_users, 1):
            top_text += f"{idx}. User ID `{uid}` — ⚡ `{data['otps_found']}` OTPs\n"
    else:
        top_text += "আজকের লিডারবোর্ড ডাটা এখনও আপডেট হয়নি।"
        
    await user_bot.send_message(callback_query.from_user.id, top_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="user_referral")
async def user_referral(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    bot_info = await user_bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    ref_count = DATABASE["users"].get(user_id, {}).get("referrals", 0)
    
    ref_text = f"👥 **REFER & EARN PROGRAM:**\n\nআপনার বন্ধু বা গ্রুপে নিচের ইউনিক লিংকটি শেয়ার করুন:\n\n🔗 Referral Link:\n`{ref_link}`\n\n📊 Total Referred: `{ref_count}` users"
    await user_bot.send_message(callback_query.from_user.id, ref_text, parse_mode="Markdown")

@user_dp.callback_query_handler(text="support")
async def user_support(callback_query: types.CallbackQuery):
    await user_bot.answer_callback_query(callback_query.id)
    await user_bot.send_message(callback_query.from_user.id, f"🛠 **HELP & SUPPORT:**\nযেকোনো সমস্যায় আমাদের অফিশিয়াল সাপোর্ট গ্রুপে বা এডমিনকে মেনশন করুন: [Admin Support](https://t.me/{str(OTP_CHANNEL_ID).replace('-100', '')})", parse_mode="Markdown", disable_web_page_preview=True)


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
        InlineKeyboardButton("👤 USERS INFO", callback_data="adm_users"),
        InlineKeyboardButton("⚙️ CONFIG", callback_data="adm_settings")
    )
    
    await message.reply(
        "👑 **EXPERT • MASTER ADMIN CONTROL PANEL**\n\nস্বাগতম বস! আপনার ম্যানেজমেন্ট অপশন বেছে নিন:",
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
        InlineKeyboardButton("🔙 Main Menu", callback_data="adm_main")
    )
    await admin_bot.edit_message_text(
        "📥 **UPLOAD NUMBERS - SELECT PLATFORM:**\nকোন প্ল্যাটফর্মে নাম্বার যোগ করতে চান?",
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
        InlineKeyboardButton("🔙 Back", callback_data="adm_add_num")
    )
    await admin_bot.edit_message_text(
        f"🎯 **{platform.upper()} • SELECT CATEGORY:**\nউপার্জন বা আপলোড ক্যাটাগরি সিলেক্ট করুন:",
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
        f"📥 **UPLOADING TO {platform.upper()} ({ntype.replace('_', ' ').title()})**\n\nদয়া করে আপনার নাম্বারগুলোর লিস্ট এখানে **পেস্ট (Paste) করে পাঠিয়ে দিন**। বট অটোমেটিক কান্ট্রি কোড ও পতাকা ডিটেক্ট করে নেবে।",
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
            "price": "$0.20" # শুধুমাত্র ডলার সেন্ট অ্যামাউন্ট
        })
        added_count += 1
        detected_countries_summary.add(f"{detected_flag} {detected_country}")
        
    del ADMIN_STATES[admin_id]
    
    countries_str = ", ".join(detected_countries_summary) if detected_countries_summary else "🌐 International"
    
    await message.reply(
        f"🎉 **কনগ্রাচুলেশনস! আপনার ফাইল বা নাম্বারগুলো সফলভাবে রিসিভ হয়েছে।**\n\n"
        f"📂 Platform: `{platform.upper()}`\n"
        f"⚙️ Type: `{ntype.replace('_', ' ').title()}`\n"
        f"🌍 Detected Country: {countries_str}\n"
        f"📥 Total Numbers Added: `{added_count}`\n\n"
        f"✅ নাম্বারগুলো সফলভাবে মেইন বটে অ্যাড করে দেওয়া হয়েছে, এখন ইউজাররা সেখান থেকে দেখতে পাবে!",
        parse_mode="Markdown"
    )

@admin_dp.callback_query_handler(text="adm_traffic")
async def admin_traffic(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    total_stock = sum(len(DATABASE[p][t]) for p in DATABASE for t in DATABASE[p] if isinstance(DATABASE[p], dict))
    await admin_bot.send_message(callback_query.from_user.id, f"📈 **Live Analytics:**\nTotal Stock: `{total_stock}`\nRegistered Users: `{len(DATABASE['users'])}`", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_users")
async def admin_users(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    await admin_bot.send_message(callback_query.from_user.id, f"👤 **User Management:**\nTotal Database Users: `{len(DATABASE['users'])}`", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_settings")
async def admin_settings(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    await admin_bot.send_message(callback_query.from_user.id, "⚙️ **System Configuration:**\nAll services are active and running stably.", parse_mode="Markdown")

@admin_dp.callback_query_handler(text="adm_main")
async def admin_main_menu(callback_query: types.CallbackQuery):
    await admin_bot.answer_callback_query(callback_query.id)
    admin_keyboard = InlineKeyboardMarkup(row_width=2)
    admin_keyboard.add(
        InlineKeyboardButton("📥 ADD NUMBERS", callback_data="adm_add_num"),
        InlineKeyboardButton("📈 STATISTICS", callback_data="adm_traffic"),
        InlineKeyboardButton("👤 USERS INFO", callback_data="adm_users"),
        InlineKeyboardButton("⚙️ CONFIG", callback_data="adm_settings")
    )
    await admin_bot.edit_message_text(
        "👑 **EXPERT • MASTER ADMIN CONTROL PANEL**",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )


# ================= DUAL BOT RUNNER (24/7) =================
async def start_bots():
    print("🚀 Expert User Bot and Admin Bot are running successfully 24/7 on Railway...")
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
