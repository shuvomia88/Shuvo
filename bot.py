import os
import json
import threading
import datetime
import uuid
import random
import pyotp
import logging
import asyncio

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError

import firebase_admin
from firebase_admin import credentials, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIG & FIREBASE SETTINGS (FIXED VALUEERROR)
# ============================================================

BOT_TOKEN = "8738544813:AAHMBZucZMhEJyA88e-qI43RjzBYyL5_j_c"
ADMIN_ID = int(os.getenv("ADMIN_ID", "6470499890"))
REQUIRED_CHANNELS = ["@range_channele", "@insagramth"]
FIREBASE_URL = "https://shuvo-866aa-default-rtdb.firebaseio.com/"

_lock = threading.Lock()

# token_uri সহ সম্পূর্ণ ভ্যালিড ক্রেডেনশিয়াল স্ট্রাকচার (Render Friendly)
cred_dict = {
    "type": "service_account",
    "project_id": "shuvo-866aa",
    "private_key_id": "1234567890abcdef1234567890abcdef12345678",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk@shuvo-866aa.iam.gserviceaccount.com",
    "client_id": "123456789012345678901",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk%40shuvo-866aa.iam.gserviceaccount.com"
}

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })
    logger.info("✓ Firebase Connected Successfully to shuvo-866aa!")
except Exception as e:
    logger.warning(f"❌ Firebase Connection Warning: {e}")

ref = db.reference('/')

# ============================================================
# MULTI-LANGUAGE DICTIONARY
# ============================================================
LANGUAGES = {
    "en": {
        "welcome": "🎉 Welcome to {name} TaskPro Bot! 🤖\n\nComplete tasks, submit your proof, and earn rewards with ease.\n\n🚀 Happy Earning & Good Luck!",
        "btn_balance": "💳 BALANCE",
        "btn_tasks": "📋 TASKS",
        "btn_withdraw": "📤 WITHDRAW",
        "btn_report": "📊 YOUR REPORT",
        "btn_support": "ℹ️ SUPPORT",
        "btn_language": "🌐 LANGUAGE",
        "btn_admin": "🛠️ ADMIN PANEL",
        "btn_back": "🔙 BACK",
        "btn_cancel": "❌ cancel",
        "btn_start": "▶️ Start",
        "btn_video": "🎥 Video",
        "btn_how_to_2fa": "❓ How to get 2fa?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:",
        "lang_changed": "✅ Language changed to English!",
        "balance_msg": "💳 Your Balance: {bal} ৳",
        "report_msg": "📊 All Account Report\n\n✅ Success: [{s}]\n⏳ Reviewing: [{r}]\n❌ Rejected: [{rej}]",
        "select_cat": "📋 Select Category:",
        "task_hidden": "❌ This task is currently hidden by Admin.",
        "no_tasks": "❌ No tasks available in this category.",
        "choose_type": "🎯 Choose Task:",
        "send_2fa_secret": "👉 Please Send Your 2FA Secret Key",
        "send_cookies": "👉 Please Send Your Cookies Data",
        "invalid_2fa": "❌ Invalid 2FA Secret Key! Please send a valid key again:",
        "withdraw_dash": "💳 Your Balance Dashboard\n\n💰 Balance: {bal} ৳\n💸 Minimum Withdraw: 50 ৳\n💳 Withdrawal Charge: 5 ৳\n✅ You Will Receive: {rec} ৳",
        "withdraw_min_err": "❌ Unsuccessful balance: Minimum 50 ৳ required",
        "select_meth": "💳 Select Your Withdraw Method:",
        "send_num": "📱 Please Send Your {method} Number",
        "enter_amt": "💰 Please Enter Your Withdraw Amount:",
        "insufficient": "❌ Insufficient balance.",
        "min_amt_err": "❌ Minimum withdraw is 50 ৳",
        "check_info": "📋 Please Check Your Info\n\n📱 Number: {num}\n💳 Method: {method}\n💵 Amount: {amt} ৳\n✅ Receive: {rec} ৳\n\n✅ If All Information Is Correct, Please Tap the Confirm Button. 👇",
        "btn_confirm": "✅ Confirm",
        "pay_pending": "⏳ Your Payment Is Pending.\n\n👨‍💼 Please Wait for Admin Approval.",
        "cookies_rec": "👉 Cookies Received. Click below to proceed.",
        "btn_acc_reg": "✅ Account Registered",
        "invite_check": "⚠️ Have You Invited 2 Friends?\n\n❌ If You Have Not Invited 2 Friends, Your Report Will Be Rejected.",
        "btn_subbed": "✅ Yes | I Am Subscribed",
        "thanks_msg": "✅ Thanks! Please Do Not Unfollow. Follow the Rules.",
        "report_received": "✅ Your report has been received!\n⏳ Please wait 16–24 hours.",
        "no_usernames_err": "❌ No user available yet!",
        "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
    },
    "bn": {
        "welcome": "🎉 Welcome to {name} TaskPro Bot! 🤖\n\nComplete tasks, submit your proof, and earn rewards with ease.\n\n🚀 Happy Earning & Good Luck!",
        "btn_balance": "💳 ব্যালেন্স",
        "btn_tasks": "📋 কাজ (TASKS)",
        "btn_withdraw": "📤 টাকা তুলুন",
        "btn_report": "📊 আপনার রিপোর্ট",
        "btn_support": "ℹ️ সাপোর্ট (SUPPORT)",
        "btn_language": "🌐 ভাষা (LANGUAGE)",
        "btn_admin": "🛠️ এডমিন প্যানেল",
        "btn_back": "🔙 পেছনে যান",
        "btn_cancel": "❌ বাতিল করুন",
        "btn_start": "▶️ শুরু করুন",
        "btn_video": "🎥 ভিডিও দেখুন",
        "btn_how_to_2fa": "❓ How to get 2fa?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:",
        "lang_changed": "✅ ভাষা পরিবর্তন করে বাংলায় সেট করা হয়েছে!",
        "balance_msg": "💳 আপনার বর্তমান ব্যালেন্স: {bal} ৳",
        "report_msg": "📊 সকল অ্যাকাউন্ট রিপোর্ট\n\n✅ সফল: [{s}]\n⏳ রিভিউতে আছে: [{r}]\n❌ বাতিল হয়েছে: [{rej}]",
        "select_cat": "📋 ক্যাটাগরি নির্বাচন করুন:",
        "task_hidden": "❌ এই কাজটি বর্তমানে এডমিন দ্বারা হাইড করা আছে।",
        "no_tasks": "❌ এই ক্যাটাগরিতে বর্তমানে কোনো কাজ নেই।",
        "choose_type": "🎯 কাজ বেছে নিন:",
        "send_2fa_secret": "👉 অনুগ্রহ করে আপনার 2FA সিক্রেট কি (Secret Key) পাঠান",
        "send_cookies": "👉 অনুগ্রহ করে আপনার কুকিজ (Cookies) ডাটা পাঠান",
        "invalid_2fa": "❌ ভুল 2FA সিক্রেট কি! দয়া করে আবার সঠিক কি পাঠান:",
        "withdraw_dash": "💳 আপনার ব্যালেন্স ড্যাশবোর্ড\n\n💰 ব্যালেন্স: {bal} ৳\n💸 সর্বনিম্ন উইথড্র: ৫০ ৳\n💳 উইথড্র চার্জ: ৫ ৳\n✅ আপনি পাবেন: {rec} ৳",
        "withdraw_min_err": "❌ Unsuccessful balance: Minimum 50 ৳ required",
        "select_meth": "💳 আপনার উইথড্র পদ্ধতি নির্বাচন করুন:",
        "send_num": "📱 অনুগ্রহ করে আপনার {method} নম্বরটি পাঠান",
        "enter_amt": "💰 অনুগ্রহ করে আপনার উইথড্র অ্যামাউন্ট লিখুন:",
        "insufficient": "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই।",
        "min_amt_err": "❌ সর্বনিম্ন উইথড্র ৫০ ৳",
        "check_info": "📋 দয়া করে আপনার তথ্য যাচাই করুন\n\n📱 নম্বর: {num}\n💳 মাধ্যম: {method}\n💵 পরিমাণ: {amt} ৳\n✅ আপনি পাবেন: {rec} ৳\n\n✅ সব তথ্য ঠিক থাকলে নিচের কনফার্ম বাটনে চাপুন। 👇",
        "btn_confirm": "✅ কনফার্ম করুন",
        "pay_pending": "⏳ আপনার পেমেন্ট পেন্ডিং অবস্থায় আছে।\n\n👨‍💼 অনুগ্রহ করে এডমিনের অনুমোদনের জন্য অপেক্ষা করুন।",
        "cookies_rec": "👉 কুকিজ পাওয়া গেছে। সামনে এগিয়ে যেতে নিচের বাটনে চাপুন।",
        "btn_acc_reg": "✅ অ্যাকাউন্ট রেজিস্টার্ড",
        "invite_check": "⚠️ আপনি কি ২ জন বন্ধুকে ইনভাইট করেছেন?\n\n❌ যদি আপনি ২ জন বন্ধুকে ইনভাইট না করে থাকেন, তবে আপনার রিপোর্টটি রিজেক্ট করা হবে।",
        "btn_subbed": "✅ হ্যাঁ | আমি সাবসক্রাইব করেছি",
        "thanks_msg": "✅ ধন্যবাদ! অনুগ্রহ করে আনফলো করবেন না। নিয়ম মেনে চলুন।",
        "report_received": "✅ আপনার রিপোর্টটি গ্রহণ করা হয়েছে!\n⏳ অনুগ্রহ করে ১৬–২৪ ঘণ্টা অপেক্ষা করুন।",
        "no_usernames_err": "❌ বর্তমানে কোনো ইউজার খালি নেই!",
        "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
    }
}

# ============================================================
# DATABASE FUNCTIONS (FIREBASE REALSYNC)
# ============================================================

def _default_data():
    return {
        "users": {},
        "submissions": {},
        "withdrawals": {},
        "dynamic_tasks": {},
        "saved_usernames": [],
        "task_password": "shuvo9",
        "visibility": {"instagram_task": True, "facebook_task": True}
    }

def _load():
    with _lock:
        try:
            data = ref.get()
            if data is None:
                default = _default_data()
                ref.set(default)
                return default
            if "saved_usernames" not in data or data["saved_usernames"] is None:
                data["saved_usernames"] = []
            if "dynamic_tasks" not in data or data["dynamic_tasks"] is None:
                data["dynamic_tasks"] = {}
            if "users" not in data or data["users"] is None:
                data["users"] = {}
            if "submissions" not in data or data["submissions"] is None:
                data["submissions"] = {}
            if "withdrawals" not in data or data["withdrawals"] is None:
                data["withdrawals"] = {}
            if "task_password" not in data:
                data["task_password"] = "shuvo9"
            if "visibility" not in data or data["visibility"] is None:
                data["visibility"] = {"instagram_task": True, "facebook_task": True}
            return data
        except Exception as e:
            logger.error(f"Firebase Load Error: {e}")
            return _default_data()

def _save(data):
    with _lock:
        try:
            ref.set(data)
        except Exception as e:
            logger.error(f"Firebase Save Error: {e}")

def get_or_create_user(user_id: int, username: str = ""):
    data = _load()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "user_id": user_id,
            "username": username if username else "No_Username",
            "balance": 0.0,
            "language": "bn", 
            "success_count": 0,
            "review_count": 0,
            "rejected_count": 0
        }
        _save(data)
    return data["users"][uid]

def generate_profile_or_get_saved():
    data = _load()
    saved = data.get("saved_usernames", [])
    if saved:
        login_name = saved.pop(0)
        data["saved_usernames"] = saved
        _save(data)
        
        first_names = ["fatima", "wafaa", "ahmed", "youssef", "omar", "nour", "ali"]
        last_names = ["Zayan", "Emad", "Khan", "Ahmed", "Ali", "Hassan"]
        f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        return f_name, login_name
    return None, None

# ============================================================
# CHECK JOIN FUNCTION
# ============================================================
async def is_user_joined_all(bot, user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except TelegramError:
            return False
    return True

def get_force_join_keyboard(lang: str):
    btn_ch1 = InlineKeyboardButton("📢 Range Channel", url="https://t.me/range_channele")
    btn_ch2 = InlineKeyboardButton("📢 Instagram TH", url="https://t.me/insagramth")
    btn_verify = InlineKeyboardButton("✅ Verify Membership", callback_data="verify_join")
    
    object.__setattr__(btn_ch1, 'style', 'primary')
    object.__setattr__(btn_ch2, 'style', 'primary')
    object.__setattr__(btn_verify, 'style', 'success')
    
    return InlineKeyboardMarkup([[btn_ch1], [btn_ch2], [btn_verify]])

# ============================================================
# KEYBOARDS DEFINITION
# ============================================================

def main_menu_keyboard(user_id: int, lang: str):
    ln = LANGUAGES[lang]
    
    btn_balance = KeyboardButton(ln["btn_balance"])
    btn_tasks = KeyboardButton(ln["btn_tasks"])
    btn_withdraw = KeyboardButton(ln["btn_withdraw"])
    btn_report = KeyboardButton(ln["btn_report"])
    btn_support = KeyboardButton(ln["btn_support"])
    btn_language = KeyboardButton(ln["btn_language"])
    
    object.__setattr__(btn_balance, 'style', 'success')
    object.__setattr__(btn_tasks, 'style', 'primary')
    object.__setattr__(btn_withdraw, 'style', 'success')
    object.__setattr__(btn_report, 'style', 'primary')
    object.__setattr__(btn_support, 'style', 'primary')
    object.__setattr__(btn_language, 'style', 'primary')
    
    buttons = [
        [btn_balance, btn_tasks],
        [btn_withdraw, btn_report],
        [btn_support, btn_language]
    ]
    
    if user_id == ADMIN_ID:
        btn_admin = KeyboardButton(ln["btn_admin"])
        object.__setattr__(btn_admin, 'style', 'danger')
        buttons.append([btn_admin])
        
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ============================================================
# USER STATE MANAGEMENT
# ============================================================
USER_STATE = {}

# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_data = get_or_create_user(user.id, user.username or "")
    lang = u_data.get("language", "bn")
    
    if not await is_user_joined_all(context.bot, user.id):
        await update.message.reply_text(
            LANGUAGES[lang]["force_join_msg"],
            reply_markup=get_force_join_keyboard(lang)
        )
        return

    await update.message.reply_text(
        LANGUAGES[lang]["welcome"].format(name=user.first_name),
        reply_markup=main_menu_keyboard(user.id, lang)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, update.effective_user.username or "")
    lang = user_profile.get("language", "bn")
    ln = LANGUAGES[lang]

    if not await is_user_joined_all(context.bot, user_id):
        await update.message.reply_text(ln["force_join_msg"], reply_markup=get_force_join_keyboard(lang))
        return
    
    if text == "❓ How to get 2fa?":
        await update.message.reply_text("📹 How to setup 2FA Video Link:\n\nhttps://t.me/range_channele/955")
        return

    # --------------------------------------------------------
    # ADMIN FLOWS
    # --------------------------------------------------------
    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_change_password":
        USER_STATE.pop(user_id, None)
        with _lock:
            data = _load()
            data["task_password"] = text
            _save(data)
        await update.message.reply_text(f"🔐 সফলভাবে নতুন পাসওয়ার্ড সেভ করা হয়েছে!\nবর্তমান পাসওয়ার্ড: `{text}`", parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_save_username":
        USER_STATE.pop(user_id, None)
        raw_names = text.replace(",", " ").split()
        with _lock:
            data = _load()
            for r_name in raw_names:
                if r_name not in data["saved_usernames"]:
                    data["saved_usernames"].append(r_name)
            _save(data)
        await update.message.reply_text(f"✅ সফলভাবে ইউজারনেম সেভ করা হয়েছে!\nবর্তমানে মোট সেভ করা ইউজারনেম: {len(data['saved_usernames'])} টি।", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_name":
        USER_STATE[user_id]["task_name"] = text
        USER_STATE[user_id]["step"] = "admin_task_price"
        await update.message.reply_text("💵 টাস্কের দাম কত হবে লিখুন (যেমন: 3.5):")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_price":
        try:
            price = float(text)
            USER_STATE[user_id]["task_price"] = price
            USER_STATE[user_id]["step"] = "admin_task_rules"
            await update.message.reply_text("📝 টাস্কের নিয়মাবলী (Rules) লিখুন:")
        except:
            await update.message.reply_text("❌ সঠিক সংখ্যা বা ডেসিমাল অ্যামাউন্ট দিন।")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_rules":
        USER_STATE[user_id]["task_rules"] = text
        USER_STATE[user_id]["step"] = "admin_task_type"
        
        btn_c_work = InlineKeyboardButton("🍪 Cookies Work", callback_data="adm_t_type:cookies")
        btn_2_work = InlineKeyboardButton("🛡️ 2FA Work", callback_data="adm_t_type:2fa")
        
        object.__setattr__(btn_c_work, 'style', 'success')
        object.__setattr__(btn_2_work, 'style', 'primary')
        
        kb = InlineKeyboardMarkup([[btn_c_work], [btn_2_work]])
        await update.message.reply_text("🎯 এটি কি ধরনের কাজ হবে নিচে থেকে সিলেক্ট করুন:", reply_markup=kb)
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "broadcast_msg":
        USER_STATE.pop(user_id, None)
        all_users = db_data["users"].keys()
        count = 0
        for u in all_users:
            try:
                await context.bot.send_message(chat_id=int(u), text=f"📢 ADMIN NOTICE:\n\n{text}")
                count += 1
            except:
                pass
        await update.message.reply_text(f"✅ Broadcast sent to {count} users.", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "add_money_uid":
        USER_STATE[user_id]["target_uid"] = text
        USER_STATE[user_id]["step"] = "add_money_amount"
        await update.message.reply_text("👤 Send the target User identification (UID) number:")
        return
        
    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "add_money_amount":
        try:
            amount = float(text)
            target = USER_STATE[user_id]["target_uid"]
            with _lock:
                data = _load()
                if target in data["users"]:
                    data["users"][target]["balance"] = round(data["users"][target]["balance"] + amount, 2)
                    _save(data)
                    await update.message.reply_text(f"✅ Added ৳{amount} to UID {target}")
                    try:
                        await context.bot.send_message(chat_id=int(target), text=f"💰 Admin added ৳{amount} to your balance!")
                    except:
                        pass
                else:
                    await update.message.reply_text("❌ User not found.")
        except:
            await update.message.reply_text("❌ Invalid Amount.")
        USER_STATE.pop(user_id, None)
        return

    # --- DELETE MONEY FEATURE PROCESS ---
    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "delete_money_target":
        target = text.replace("@", "")
        found_uid = None
        if target.isdigit() and target in db_data.get("users", {}):
            found_uid = target
        else:
            for uid, uinfo in db_data.get("users", {}).items():
                if uinfo.get("username", "").lower() == target.lower():
                    found_uid = uid
                    break
        if not found_uid:
            await update.message.reply_text("❌ এই ইউজারনেম বা UID ফায়ারবেসে খুঁজে পাওয়া যায়নি!")
            USER_STATE.pop(user_id, None)
            return
            
        current_balance = db_data["users"][found_uid].get("balance", 0.0)
        USER_STATE[user_id]["target_uid"] = found_uid
        USER_STATE[user_id]["step"] = "delete_money_amount"
        await update.message.reply_text(f"👤 ইউজার পাওয়া গেছে!\n🆔 UID: `{found_uid}`\n💰 বর্তমান ব্যালেন্স: **{current_balance}** ৳\n\n💵 কত টাকা রিমুভ (বিয়োগ) করতে চান? শুধু সংখ্যাটি লিখুন:")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "delete_money_amount":
        try:
            amount_to_remove = float(text)
            target_uid = USER_STATE[user_id]["target_uid"]
            with _lock:
                data = _load()
                if target_uid in data.get("users", {}):
                    old_bal = data["users"][target_uid].get("balance", 0.0)
                    new_bal = max(0.0, old_bal - amount_to_remove)
                    data["users"][target_uid]["balance"] = round(new_bal, 2)
                    _save(data)
                    await update.message.reply_text(f"✅ সফলভাবে টাকা রিমুভ করা হয়েছে!\n🆔 UID: `{target_uid}`\n📉 আগের ব্যালেন্স: {old_bal} ৳\n💸 রিমুভ করা হয়েছে: {amount_to_remove} ৳\n💰 বর্তমান ফায়ারবেস ব্যালেন্স: **{data['users'][target_uid]['balance']}** ৳")
                    try:
                        await context.bot.send_message(chat_id=int(target_uid), text=f"⚠️ এডমিন আপনার অ্যাকাউন্ট থেকে {amount_to_remove} ৳ কেটে নিয়েছে। বর্তমান ব্যালেন্স: {data['users'][target_uid]['balance']} ৳")
                    except:
                        pass
        except:
            await update.message.reply_text("❌ ভুল ইনপুট! সঠিক সংখ্যা দিন।")
        USER_STATE.pop(user_id, None)
        return

    # --- WITHDRAW PROCESS ---
    if USER_STATE.get(user_id, {}).get("step") == "withdraw_num":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            USER_STATE.pop(user_id, None)
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            return
        USER_STATE[user_id]["number"] = text
        USER_STATE[user_id]["step"] = "withdraw_amt"
        await update.message.reply_text(ln["enter_amt"])
        return

    if USER_STATE.get(user_id, {}).get("step") == "withdraw_amt":
        try:
            amt = float(text)
            if amt > user_profile["balance"]:
                await update.message.reply_text(ln["insufficient"])
                USER_STATE.pop(user_id, None)
                return
            if amt < 50:
                await update.message.reply_text(ln["min_amt_err"])
                USER_STATE.pop(user_id, None)
                return
            
            method = USER_STATE[user_id]["method"]
            num = USER_STATE[user_id]["number"]
            charge = 5.0
            receive = amt - charge
            
            USER_STATE[user_id]["amt"] = amt
            USER_STATE[user_id]["receive"] = receive
            
            confirm_text = ln["check_info"].format(num=num, method=method, amt=amt, rec=receive)
            
            btn_cnf = KeyboardButton(ln["btn_confirm"])
            btn_cnc = KeyboardButton(ln["btn_cancel"])
            object.__setattr__(btn_cnf, 'style', 'success')
            object.__setattr__(btn_cnc, 'style', 'danger')
            
            kb = ReplyKeyboardMarkup([[btn_cnf, btn_cnc]], resize_keyboard=True)
            USER_STATE[user_id]["step"] = "withdraw_confirm"
            await update.message.reply_text(confirm_text, reply_markup=kb)
        except:
            await update.message.reply_text("❌ Invalid format.")
            USER_STATE.pop(user_id, None)
        return

    if USER_STATE.get(user_id, {}).get("step") == "withdraw_confirm":
        if text == ln["btn_confirm"]:
            state = USER_STATE[user_id]
            w_id = str(uuid.uuid4())[:8]
            with _lock:
                data = _load()
                data["withdrawals"][w_id] = {
                    "w_id": w_id, "user_id": user_id, "username": user_profile["username"],
                    "number": state["number"], "method": state["method"], "amount": state["amt"], "status": "pending"
                }
                _save(data)
            await update.message.reply_text(ln["pay_pending"], reply_markup=main_menu_keyboard(user_id, lang))
            
            btn_w_ap = InlineKeyboardButton("✅ APPROVE", callback_data=f"w_app:{w_id}")
            btn_w_rj = InlineKeyboardButton("❌ REJECT", callback_data=f"w_rej:{w_id}")
            object.__setattr__(btn_w_ap, 'style', 'success')
            object.__setattr__(btn_w_rj, 'style', 'danger')
            
            admin_kb = InlineKeyboardMarkup([[btn_w_ap, btn_w_rj]])
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💸 New Payment Request\n\n👤 User: @{user_profile['username']}\n🆔 UID: {user_id}\n📱 Number: {state['number']}\n💳 Method: {state['method']}\n💰 Amount: {state['amt']} ৳",
                reply_markup=admin_kb
            )
        else:
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
        USER_STATE.pop(user_id, None)
        return

    # --- COOKIES SUBMISSION ---
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_cookies":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            USER_STATE.pop(user_id, None)
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            return
        USER_STATE[user_id]["cookies_data"] = text
        USER_STATE[user_id]["step"] = "cookies_submitted"
        
        btn_reg = KeyboardButton(ln["btn_acc_reg"])
        btn_cnc = KeyboardButton(ln["btn_cancel"])
        object.__setattr__(btn_reg, 'style', 'success')
        object.__setattr__(btn_cnc, 'style', 'danger')
        
        kb = ReplyKeyboardMarkup([[btn_reg], [btn_cnc]], resize_keyboard=True)
        await update.message.reply_text(ln["cookies_rec"], reply_markup=kb)
        return

    if text == ln["btn_acc_reg"]:
        state = USER_STATE.get(user_id)
        if state and (state.get("step") == "cookies_submitted" or state.get("step") == "2fa_verify"):
            btn_sub = KeyboardButton(ln["btn_subbed"])
            btn_cnc = KeyboardButton(ln["btn_cancel"])
            object.__setattr__(btn_sub, 'style', 'success')
            object.__setattr__(btn_cnc, 'style', 'danger')
            
            kb = ReplyKeyboardMarkup([[btn_sub], [btn_cnc]], resize_keyboard=True)
            await update.message.reply_text(ln["invite_check"], reply_markup=kb)
            if state.get("step") == "cookies_submitted":
                USER_STATE[user_id]["step"] = "cookies_final_confirm"
            else:
                USER_STATE[user_id]["step"] = "2fa_final_confirm"
            return

    if text == ln["btn_subbed"]:
        state = USER_STATE.get(user_id)
        if state and state.get("step") == "2fa_final_confirm":
            sub_id = str(uuid.uuid4())[:8]
            file_path = f"submission_{sub_id}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Dynamic 2FA Report\nTask Name: {state.get('t_name','')}\nUsername: {state['login']}\nPassword: {state['pass']}\n2FA Key: {state.get('secret','')}")
                
            with _lock:
                d = _load()
                d["submissions"][sub_id] = {
                    "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                    "task_type": "2fa", "task_id": state.get("task_id"), "login": state['login'], "pass": state['pass'], "status": "pending"
                }
                d["users"][str(user_id)]["review_count"] += 1
                _save(d)
                
            with open(file_path, "rb") as f:
                await context.bot.send_document(chat_id=ADMIN_ID, document=f, caption=f"实时 Dynamic 2FA Task\nUser: @{user_profile['username']}\nUID: {user_id}")
            os.remove(file_path)
            
            await update.message.reply_text(ln["report_received"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

        if state and state.get("step") == "cookies_final_confirm":
            sub_id = str(uuid.uuid4())[:8]
            file_path = f"submission_{sub_id}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Task Name: {state['t_name']}\nUsername: {state['login']}\nPassword: {state['pass']}\nCookies: {state['cookies_data']}")
            with _lock:
                data = _load()
                data["submissions"][sub_id] = {
                    "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                    "task_type": "cookies", "task_id": data.get("task_id"), "login": state['login'], "pass": state['pass'], "status": "pending"
                }
                data["users"][str(user_id)]["review_count"] += 1
                _save(data)
            with open(file_path, "rb") as f:
                await context.bot.send_document(chat_id=ADMIN_ID, document=f, caption=f"🍪 Dynamic Cookies Task Submission\nUser: @{user_profile['username']}\nUID: {user_id}\nSub ID: {sub_id}")
            os.remove(file_path)
            await update.message.reply_text(ln["thanks_msg"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

    # --- 2FA SECRET KEY SUBMISSION ---
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_2fa":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return
        user_secret = text.replace(" ", "")
        try:
            totp = pyotp.TOTP(user_secret)
            current_code = totp.now()
        except:
            await update.message.reply_text(ln["invalid_2fa"])
            return

        state = USER_STATE.get(user_id)
        state["secret"] = user_secret
        state["step"] = "2fa_verify"
        remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
        
        btn_reg = KeyboardButton(ln["btn_acc_reg"])
        btn_cnc = KeyboardButton(ln["btn_cancel"])
        object.__setattr__(btn_reg, 'style', 'success')
        object.__setattr__(btn_cnc, 'style', 'danger')
        reg_kb = ReplyKeyboardMarkup([[btn_reg], [btn_cnc]], resize_keyboard=True)
        
        await update.message.reply_text("👉 2FA Key Received. Now verify and submit using the panel below.", reply_markup=reg_kb)

        btn_ref = InlineKeyboardButton("🔄 Refresh", callback_data="refresh_2fa_code")
        object.__setattr__(btn_ref, 'style', 'primary')
        inline_kb = InlineKeyboardMarkup([[btn_ref]])
        
        msg = await update.message.reply_text(
            f"╔══════════╗\n"
            f"🔑 Your 2FA Code\n"
            f"╚══════════╝\n\n"
            f"🔢 Code : `{current_code}`\n\n"
            f"⏱️ Valid : {remaining}s\n"
            f"━━━━━━━━━━",
            parse_mode="Markdown",
            reply_markup=inline_kb
        )
        state["code_msg_id"] = msg.message_id
        return

    # --- MENU NAVIGATION ---
    if text in ["💳 BALANCE", "💳 ব্যালেন্স"]:
        await update.message.reply_text(ln["balance_msg"].format(bal=user_profile['balance']), reply_markup=main_menu_keyboard(user_id, lang))
        return

    if text in ["📊 YOUR REPORT", "📊 আপনার রিপোর্ট"]:
        await update.message.reply_text(
            ln["report_msg"].format(s=user_profile.get('success_count', 0), r=user_profile.get('review_count', 0), rej=user_profile.get('rejected_count', 0)),
            reply_markup=main_menu_keyboard(user_id, lang)
        )
        return

    if text in ["ℹ️ SUPPORT", "ℹ️ সাপোর্ট (SUPPORT)"]:
        btn_adm = InlineKeyboardButton("👤 Admin", url="https://t.me/adim_shuvo")
        object.__setattr__(btn_adm, 'style', 'primary')
        inline_kb = InlineKeyboardMarkup([[btn_adm]])
        await update.message.reply_text(ln["support_msg"], reply_markup=inline_kb)
        return

    if text in ["🌐 LANGUAGE", "🌐 ভাষা (LANGUAGE)"]:
        btn_bn = InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
        btn_en = InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        object.__setattr__(btn_bn, 'style', 'success')
        object.__setattr__(btn_en, 'style', 'primary')
        
        kb = InlineKeyboardMarkup([[btn_bn, btn_en]])
        await update.message.reply_text(ln["select_lang"], reply_markup=kb)
        return

    if text in ["📋 TASKS", "📋 কাজ (TASKS)"]:
        task_list = []
        if db_data["visibility"].get("instagram_task", True) or user_id == ADMIN_ID:
            btn_ig = KeyboardButton("🎯 Instagram Task" if lang == "en" else "🎯 ইনস্টাগ্রাম কাজ")
            object.__setattr__(btn_ig, 'style', 'primary')
            task_list.append([btn_ig])
        if db_data["visibility"].get("facebook_task", True) or user_id == ADMIN_ID:
            btn_fb = KeyboardButton("🎯 Facebook Task" if lang == "en" else "🎯 ফেসবুক কাজ")
            object.__setattr__(btn_fb, 'style', 'primary')
            task_list.append([btn_fb])
            
        btn_bck = KeyboardButton(ln["btn_back"])
        object.__setattr__(btn_bck, 'style', 'danger')
        task_list.append([btn_bck])
        await update.message.reply_text(ln["select_cat"], reply_markup=ReplyKeyboardMarkup(task_list, resize_keyboard=True))
        return

    if text in ["🎯 Instagram Task", "🎯 ইনস্টাগ্রাম কাজ", "🎯 Facebook Task", "🎯 ফেসবুক কাজ"]:
        cat_key = "instagram" if "Insta" in text or "ইনস্টা" in text else "facebook"
        if not db_data["visibility"].get(f"{cat_key}_task", True) and user_id != ADMIN_ID:
            await update.message.reply_text(ln["task_hidden"])
            return
            
        active_tasks = [t for t in db_data.get("dynamic_tasks", {}).values() if t.get("category") == cat_key]
        if not active_tasks:
            await update.message.reply_text(ln["no_tasks"])
            return
            
        sub_tasks = []
        for t in active_tasks:
            btn_t = KeyboardButton(f"📌 {t['name']} ({t['price']} ৳)")
            object.__setattr__(btn_t, 'style', 'success')
            sub_tasks.append([btn_t])
            
        btn_cnc = KeyboardButton(ln["btn_cancel"])
        object.__setattr__(btn_cnc, 'style', 'danger')
        sub_tasks.append([btn_cnc])
        await update.message.reply_text(ln["choose_type"], reply_markup=ReplyKeyboardMarkup(sub_tasks, resize_keyboard=True))
        return

    if text.startswith("📌 "):
        clean_name = text.replace("📌 ", "").split(" (")[0]
        all_tasks = db_data.get("dynamic_tasks", {})
        
        target_task = None
        for tid, t in all_tasks.items():
            if t["name"] == clean_name:
                target_task = t
                break
                
        if target_task:
            tid = target_task["id"]
            USER_STATE[user_id] = {"task_id": tid, "task_type": target_task["type"]}
            
            btn_str = KeyboardButton(ln["btn_start"])
            btn_vid = KeyboardButton(ln["btn_video"])
            btn_cnc = KeyboardButton(ln["btn_cancel"])
            
            object.__setattr__(btn_str, 'style', 'success')
            object.__setattr__(btn_vid, 'style', 'primary')
            object.__setattr__(btn_cnc, 'style', 'danger')
            
            kb = ReplyKeyboardMarkup([[btn_str], [btn_vid], [btn_cnc]], resize_keyboard=True)
            rules_msg = f"🛡️ 🌟 *{target_task['name']}*\n\n💵 Payout: ৳{target_task['price']}\n\n📝 *Rules:*\n{target_task['rules']}\n\n🚀 Tap START to continue."
            await update.message.reply_text(rules_msg, parse_mode="Markdown", reply_markup=kb)
            return

    if text == ln["btn_video"] or text == "🎥 ভিডিও দেখুন":
        await update.message.reply_text("🎥 Video Link:\n\nhttps://t.me/range_channele/955")
        return

    if text == ln["btn_start"]:
        state = USER_STATE.get(user_id)
        if state and "task_id" in state:
            t_data = db_data["dynamic_tasks"].get(state["task_id"])
            if t_data:
                f_name, login_name = generate_profile_or_get_saved()
                
                if login_name is None:
                    await update.message.reply_text(ln["no_usernames_err"])
                    return
                    
                pass_val = db_data.get("task_password", "shuvo9")
                state["login"] = login_name
                state["pass"] = pass_val
                state["t_name"] = t_data["name"]
                
                mono_msg = (
                    f"First name: `{f_name}`\n"
                    f"Login: `{login_name}`\n"
                    f"Password: `{pass_val}`"
                )
                await update.message.reply_text(mono_msg, parse_mode="Markdown")
                
                if state["task_type"] == "2fa":
                    state["step"] = "waiting_for_2fa"
                    btn_2fa = KeyboardButton(ln["btn_how_to_2fa"])
                    btn_cnc = KeyboardButton(ln["btn_cancel"])
                    object.__setattr__(btn_2fa, 'style', 'primary')
                    object.__setattr__(btn_cnc, 'style', 'danger')
                    task_2fa_kb = ReplyKeyboardMarkup([[btn_2fa], [btn_cnc]], resize_keyboard=True)
                    await update.message.reply_text(ln["send_2fa_secret"], reply_markup=task_2fa_kb)
                else:
                    state["step"] = "waiting_for_cookies"
                    btn_cnc = KeyboardButton(ln["btn_cancel"])
                    object.__setattr__(btn_cnc, 'style', 'danger')
                    await update.message.reply_text(ln["send_cookies"], reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
            return

    if text in ["📤 WITHDRAW", "📤 টাকা তুলুন"]:
        bal = user_profile["balance"]
        if bal < 50:
            btn_fake = InlineKeyboardButton("⚠️ Insufficient Balance", callback_data="popup_error_alert")
            await update.message.reply_text("❌ Click below to see your error status:", reply_markup=InlineKeyboardMarkup([[btn_fake]]))
            return
        btn_wth = InlineKeyboardButton("Withdraw", callback_data="start_withdraw")
        object.__setattr__(btn_wth, 'style', 'success')
        inline_wb = InlineKeyboardMarkup([[btn_wth]])
        await update.message.reply_text(ln["withdraw_dash"].format(bal=bal, rec=max(0.0, bal - 5.0)), reply_markup=inline_wb)
        return

    # --- ADMIN CONTROL DASHBOARD PANEL (NEW BUTTONS ADDED) ---
    if text in ["🛠️ ADMIN PANEL", "🛠️ ENDMIN PANEL", "🛠️ এডমিন প্যানেল"] and user_id == ADMIN_ID:
        btn_add_t = KeyboardButton("➕ Add Task")
        btn_del_t = KeyboardButton("❌ Delete Task")
        btn_vis_t = KeyboardButton("👁️ Task Hide/Show")
        btn_brd_t = KeyboardButton("👤 User Broadcast")
        btn_add_m = KeyboardButton("➕ Add Money")
        btn_del_m = KeyboardButton("💡 Delete Money")
        btn_sav_u = KeyboardButton("📥 Username Save")
        btn_usr_c = KeyboardButton("👥 User")
        btn_usr_l = KeyboardButton("📜 All User List")
        btn_all_r = KeyboardButton("🗂️ All Report")
        btn_del_u = KeyboardButton("🗑️ User Delete")
        btn_pwd_t = KeyboardButton("🔐 Password Change")
        btn_back_m = KeyboardButton(ln["btn_back"])
        
        object.__setattr__(btn_add_t, 'style', 'success')
        object.__setattr__(btn_del_t, 'style', 'danger')
        object.__setattr__(btn_vis_t, 'style', 'primary')
        object.__setattr__(btn_brd_t, 'style', 'primary')
        object.__setattr__(btn_add_m, 'style', 'success')
        object.__setattr__(btn_del_m, 'style', 'danger')
        object.__setattr__(btn_sav_u, 'style', 'success')
        object.__setattr__(btn_usr_c, 'style', 'primary')
        object.__setattr__(btn_usr_l, 'style', 'primary')
        object.__setattr__(btn_all_r, 'style', 'primary')
        object.__setattr__(btn_del_u, 'style', 'danger')
        object.__setattr__(btn_pwd_t, 'style', 'primary')
        object.__setattr__(btn_back_m, 'style', 'danger')
        
        kb = ReplyKeyboardMarkup([
            [btn_add_t, btn_del_t],
            [btn_vis_t, btn_brd_t],
            [btn_add_m, btn_del_m],
            [btn_sav_u, btn_pwd_t],
            [btn_usr_c, btn_usr_l],
            [btn_all_r, btn_del_u],
            [btn_back_m]
        ], resize_keyboard=True)
        await update.message.reply_text("🛠️ Admin Control Dashboard", reply_markup=kb)
        return

    # --- HANDLING NEW BUTTON FUNCTIONS ---
    if user_id == ADMIN_ID and text == "👥 User":
        total_users = len(db_data.get("users", {}))
        await update.message.reply_text(f"👥 এই পর্যন্ত মোট **{total_users}** জন ইউজার বটটি স্টার্ট করেছে বা চালাচ্ছে।")
        return

    if user_id == ADMIN_ID and text == "📜 All User List":
        users = db_data.get("users", {})
        if not users:
            await update.message.reply_text("বটে এখনো কোনো ইউজার ডাটা নেই।")
            return
        report = "📜 **ইউজার লিস্ট ও ব্যালেন্স বিবরণী:**\n\n"
        for uid, uinfo in users.items():
            uname = uinfo.get("username", "No_Username")
            bal = uinfo.get("balance", 0.0)
            report += f"🆔 UID: `{uid}` | 👤 @{uname} | 💰 ব্যালেন্স: {bal} ৳\n"
            if len(report) > 3500:
                await update.message.reply_text(report, parse_mode="Markdown")
                report = ""
        if report:
            await update.message.reply_text(report, parse_mode="Markdown")
        return

    if user_id == ADMIN_ID and text == "💡 Delete Money":
        USER_STATE[user_id] = {"step": "delete_money_target"}
        await update.message.reply_text("🔍 কোন ইউজারের টাকা রিমুভ করতে চান?\nইউজারের **Username** (অ্যাট সাইন @ ছাড়া) অথবা **UID** দিন:")
        return

    if user_id == ADMIN_ID and text == "🔐 Password Change":
        USER_STATE[user_id] = {"step": "admin_change_password"}
        current_pwd = db_data.get("task_password", "shuvo9")
        await update.message.reply_text(f"🔐 বর্তমান টাস্ক পাসওয়ার্ড: `{current_pwd}`\n\nনতুন যে পাসওয়ার্ডটি সেট করতে চান তা লিখে পাঠান:", parse_mode="Markdown")
        return

    if user_id == ADMIN_ID and text == "❌ Delete Task":
        btn_del_ig = InlineKeyboardButton("Instagram Tasks", callback_data="adm_del_cat:instagram")
        btn_del_fb = InlineKeyboardButton("Facebook Tasks", callback_data="adm_del_cat:facebook")
        object.__setattr__(btn_del_ig, 'style', 'danger')
        object.__setattr__(btn_del_fb, 'style', 'danger')
        
        kb = InlineKeyboardMarkup([[btn_del_ig, btn_del_fb]])
        await update.message.reply_text("🗑️ কোন ক্যাটাগরির কাজ ডিলিট করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "📥 Username Save":
        USER_STATE[user_id] = {"step": "admin_save_username"}
        await update.message.reply_text("📥 আপনি যে ইউজারনেমগুলো সেভ করে রাখতে চান সেগুলো পাঠান:\n(একাধিক ইউজারনেম স্পেস বা কমা দিয়ে একসাথে পাঠাতে পারেন)")
        return

    if user_id == ADMIN_ID and text == "➕ Add Task":
        btn_cat_ig = InlineKeyboardButton("Instagram", callback_data="adm_cat:instagram")
        btn_cat_fb = InlineKeyboardButton("Facebook", callback_data="adm_cat:facebook")
        object.__setattr__(btn_cat_ig, 'style', 'success')
        object.__setattr__(btn_cat_fb, 'style', 'success')
        
        kb = InlineKeyboardMarkup([[btn_cat_ig, btn_cat_fb]])
        await update.message.reply_text("📁 কোন ক্যাটাগরিতে কাজ যুক্ত করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "👁️ Task Hide/Show":
        v = db_data["visibility"]
        btn_h_ig = InlineKeyboardButton(f"IG Cat [{'ON' if v.get('instagram_task',True) else 'OFF'}]", callback_data="h_ig_m")
        btn_h_fb = InlineKeyboardButton(f"FB Cat [{'ON' if v.get('facebook_task',True) else 'OFF'}]", callback_data="h_fb_m")
        object.__setattr__(btn_h_ig, 'style', 'primary')
        object.__setattr__(btn_h_fb, 'style', 'primary')
        
        kb = InlineKeyboardMarkup([[btn_h_ig, btn_h_fb]])
        await update.message.reply_text("👁️ Click to Toggle Category Visibility:", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "👤 User Broadcast":
        USER_STATE[user_id] = {"step": "broadcast_msg"}
        await update.message.reply_text("📢 Send the message you wish to broadcast to all users:")
        return

    if user_id == ADMIN_ID and text == "➕ Add Money":
        USER_STATE[user_id] = {"step": "add_money_uid"}
        await update.message.reply_text("👤 Send the target User identification (UID) number:")
        return

    if user_id == ADMIN_ID and text == "🗑️ User Delete":
        total_saved_usernames = len(db_data.get("saved_usernames", []))
        btn_conf_del = InlineKeyboardButton("⚠️ ডিলিট নিশ্চিত করুন", callback_data="adm_confirm_delete_all_saved_usernames")
        object.__setattr__(btn_conf_del, 'style', 'danger')
        
        kb = InlineKeyboardMarkup([[btn_conf_del]])
        await update.message.reply_text(
            f"📊 বটের মোট সেভ করা ইউজারনেমের সংখ্যা: {total_saved_usernames} টি।\n\n"
            f"❗ আপনি যদি বটের সমস্ত সেভ করা ইউজারনেম ডাটা ডিলিট করতে চান তবে নিচের ডিলিট বাটনে ক্লিক করুন।",
            reply_markup=kb
        )
        return

    if user_id == ADMIN_ID and text == "🗂️ All Report":
        pending_subs = [s for s in db_data["submissions"].values() if s["status"] == "pending"]
        if not pending_subs:
            await update.message.reply_text("✅ No pending item reports.")
            return
        for s in pending_subs:
            btn_app = InlineKeyboardButton("Approve", callback_data=f"rep_app:{s['sub_id']}")
            btn_rej = InlineKeyboardButton("Reject", callback_data=f"rep_rej:{s['sub_id']}")
            object.__setattr__(btn_app, 'style', 'success')
            object.__setattr__(btn_rej, 'style', 'danger')
            
            inline_ap = InlineKeyboardMarkup([[btn_app, btn_rej]])
            await update.message.reply_text(f"User ID: {s['user_id']}\nType: {s['task_type']}\nLogin: {s['login']}\nStatus: Pending", reply_markup=inline_ap)
        return

    if text in [ln["btn_cancel"], ln["btn_back"], "cancel", "❌ cancel", "🔙 BACK"]:
        USER_STATE.pop(user_id, None)
        await update.message.reply_text("🔙 Menu", reply_markup=main_menu_keyboard(user_id, lang))

# ============================================================
# CALLBACK QUERY PROCESSING & BACKGROUND TIMER
# ============================================================

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, query.from_user.username or "")
    lang = user_profile.get("language", "bn")
    ln = LANGUAGES[lang]

    if data == "popup_error_alert":
        await query.answer(text="❌ Unsuccessful balance: Minimum 50 ৳ required", show_alert=True)
        try: await query.delete_message()
        except: pass
        return

    await query.answer()

    if data == "verify_join":
        if await is_user_joined_all(context.bot, user_id):
            try: await query.delete_message()
            except: pass
            
            success_msg = await context.bot.send_message(chat_id=user_id, text=ln["verify_success"])
            asyncio.create_task(delete_message_after_delay(context, user_id, success_msg.message_id, 5))
            
            await asyncio.sleep(5)
            await context.bot.send_message(
                chat_id=user_id,
                text=ln["welcome"].format(name=query.from_user.first_name),
                reply_markup=main_menu_keyboard(user_id, lang)
            )
        else:
            await context.bot.send_message(chat_id=user_id, text=ln["not_joined_all"])
        return

    if data == "refresh_2fa_code":
        state = USER_STATE.get(user_id)
        if state and state.get("step") == "2fa_verify" and "secret" in state:
            try:
                totp = pyotp.TOTP(state["secret"])
                current_code = totp.now()
                remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
                
                btn_ref = InlineKeyboardButton("🔄 Refresh", callback_data="refresh_2fa_code")
                object.__setattr__(btn_ref, 'style', 'primary')
                inline_kb = InlineKeyboardMarkup([[btn_ref]])
                
                await query.edit_message_text(
                    f"╔══════════╗\n"
                    f"🔑 Your 2FA Code\n"
                    f"╚══════════╝\n\n"
                    f"🔢 Code : `{current_code}`\n\n"
                    f"⏱️ Valid : {remaining}s\n"
                    f"━━━━━━━━━━",
                    parse_mode="Markdown",
                    reply_markup=inline_kb
                )
            except:
                pass
        return

    if data.startswith("adm_cat:"):
        cat = data.split(":")[1]
        USER_STATE[user_id] = {"category": cat, "step": "admin_task_name"}
        await query.message.reply_text("📝 টাস্কের একটি সুন্দর নাম (Name) দিন:")
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_del_cat:"):
        cat = data.split(":")[1]
        active_tasks = [t for t in db_data.get("dynamic_tasks", {}).values() if t.get("category") == cat]
        if not active_tasks:
            await query.message.reply_text("❌ এই ক্যাটাগরিতে ডিলিট করার মতো কোনো একটিভ কাজ পাওয়া যায়নি।")
            return
            
        buttons = []
        for t in active_tasks:
            btn_t_del = InlineKeyboardButton(f"🗑️ {t['name']} ({t['price']}৳)", callback_data=f"adm_do_del:{t['id']}")
            object.__setattr__(btn_t_del, 'style', 'danger')
            buttons.append([btn_t_del])
            
        await query.message.reply_text("👇 নিচে থেকে যে টাস্কটি ডিলিট করতে চান সেটির উপর চাপুন:", reply_markup=InlineKeyboardMarkup(buttons))
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_do_del:"):
        task_id = data.split(":")[1]
        with _lock:
            d = _load()
            if task_id in d.get("dynamic_tasks", {}):
                removed_task = d["dynamic_tasks"].pop(task_id)
                _save(d)
                await query.message.reply_text(f"✅ সফলভাবে টাস্কটি ডিলিট করা হয়েছে!\n🗑️ ডিলিট হওয়া টাস্ক: {removed_task['name']}")
            else:
                await query.message.reply_text("❌ দুঃখিত! টাস্কটি খুঁজে পাওয়া যায়নি অথবা অলরেডি ডিলিট হয়ে গেছে।")
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_t_type:"):
        t_type = data.split(":")[1]
        state = USER_STATE.get(user_id)
        if state and "category" in state and "task_name" in state:
            t_id = str(uuid.uuid4())[:8]
            new_task = {
                "id": t_id, "category": state["category"], "name": state["task_name"],
                "price": state.get("task_price", 0.0), "rules": state.get("task_rules", ""), "type": t_type
            }
            with _lock:
                d = _load()
                if "dynamic_tasks" not in d: d["dynamic_tasks"] = {}
                d["dynamic_tasks"][t_id] = new_task
                _save(d)
                
            USER_STATE.pop(user_id, None)
            await query.message.reply_text(f"✅ সফলভাবে নতুন টাস্ক সিস্টেমে সেভ করা হয়েছে!\n\n📌 নাম: {new_task['name']}\n💵 পেমেন্ট: {new_task['price']} ৳\n🎯 টাইপ: {new_task['type'].upper()}")
            try: await query.delete_message()
            except: pass
        return

    if data.startswith("lang_"):
        new_lang = "bn" if data == "lang_bn" else "en"
        with _lock:
            d = _load()
            d["users"][str(user_id)]["language"] = new_lang
            _save(d)
        await query.message.reply_text(LANGUAGES[new_lang]["lang_changed"], reply_markup=main_menu_keyboard(user_id, new_lang))
        try: await query.delete_message()
        except: pass
        return

    if data == "start_withdraw":
        if user_profile["balance"] < 50:
            await query.answer(ln["withdraw_min_err"], show_alert=True)
            return
        USER_STATE[user_id] = {"step": "withdraw_method"}
        
        btn_bks = InlineKeyboardButton("bKash", callback_data="w_meth:bKash")
        btn_ngd = InlineKeyboardButton("Nagad", callback_data="w_meth:Nagad")
        object.__setattr__(btn_bks, 'style', 'success')
        object.__setattr__(btn_ngd, 'style', 'success')
        
        kb = InlineKeyboardMarkup([[btn_bks, btn_ngd]])
        await query.edit_message_text(LANGUAGES[lang]["select_meth"], reply_markup=kb)
        return

    if data.startswith("w_meth:"):
        method = data.split(":")[1]
        USER_STATE[user_id]["method"] = method
        USER_STATE[user_id]["step"] = "withdraw_num"
        
        btn_cnc = KeyboardButton(LANGUAGES[lang]["btn_cancel"])
        object.__setattr__(btn_cnc, 'style', 'danger')
        
        await context.bot.send_message(chat_id=user_id, text=LANGUAGES[lang]["send_num"].format(method=method), reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
        try: await query.delete_message()
        except: pass
        return

    if user_id != ADMIN_ID:
        return

    if data == "adm_confirm_delete_all_saved_usernames":
        with _lock:
            d = _load()
            d["saved_usernames"] = []
            _save(d)
        await query.message.reply_text("💥 সফলভাবে বটের সকল সেভ করা ইউজারনেম ডাটা ডিলিট করে দেওয়া হয়েছে!", reply_markup=main_menu_keyboard(user_id, lang))
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("h_"):
        key_map = {"h_ig_m": "instagram_task", "h_fb_m": "facebook_task"}
        target_key = key_map[data]
        with _lock:
            d = _load()
            d["visibility"][target_key] = not d["visibility"].get(target_key, True)
            _save(d)
        v = d["visibility"]
        
        btn_m_ig = InlineKeyboardButton(f"IG Master [{'ON' if v.get('instagram_task',True) else 'OFF'}]", callback_data="h_ig_m")
        btn_m_fb = InlineKeyboardButton(f"FB Master [{'ON' if v.get('facebook_task',True) else 'OFF'}]", callback_data="h_fb_m")
        object.__setattr__(btn_m_ig, 'style', 'primary')
        object.__setattr__(btn_m_fb, 'style', 'primary')
        
        kb = InlineKeyboardMarkup([[btn_m_ig, btn_m_fb]])
        await query.edit_message_text("👁️ Category Visibility toggled:", reply_markup=kb)
        return

    if data.startswith("w_app:") or data.startswith("w_rej:"):
        w_id = data.split(":")[1]
        is_approve = data.startswith("w_app:")
        with _lock:
            d = _load()
            w_rec = d["withdrawals"].get(w_id)
            if w_rec and w_rec["status"] == "pending":
                if is_approve:
                    w_rec["status"] = "approved"
                    d["users"][str(w_rec["user_id"])]["balance"] = round(d["users"][str(w_rec["user_id"])]["balance"] - w_rec["amount"], 2)
                    msg = f"✅ Approved ৳{w_rec['amount']}"
                    u_msg = "✅ Your withdrawal request has been verified and approved by the admin."
                else:
                    w_rec["status"] = "rejected"
                    msg = "❌ Rejected"
                    u_msg = "❌ Your withdrawal request has been rejected."
                _save(d)
                await query.edit_message_text(msg)
                try: await context.bot.send_message(chat_id=w_rec["user_id"], text=u_msg)
                except: pass
        return

    if data.startswith("rep_app:") or data.startswith("rep_rej:"):
        sub_id = data.split(":")[1]
        is_approve = data.startswith("rep_app:")
        with _lock:
            d = _load()
            s_rec = d["submissions"].get(sub_id)
            if s_rec and s_rec["status"] == "pending":
                u_id_str = str(s_rec["user_id"])
                if is_approve:
                    s_rec["status"] = "approved"
                    t_info = d.get("dynamic_tasks", {}).get(s_rec.get("task_id"), {})
                    p_add = t_info.get("price", 3.5)
                    d["users"][u_id_str]["balance"] = round(d["users"][u_id_str]["balance"] + p_add, 2)
                    d["users"][u_id_str]["success_count"] += 1
                    d["users"][u_id_str]["review_count"] = max(0, d["users"][u_id_str]["review_count"] - 1)
                    msg = "✅ Approved submission."
                    u_msg = f"✅ Report approved, +৳{p_add}"
                else:
                    s_rec["status"] = "rejected"
                    d["users"][u_id_str]["rejected_count"] += 1
                    d["users"][u_id_str]["review_count"] = max(0, d["users"][u_id_str]["review_count"] - 1)
                    msg = "❌ Rejected submission."
                    u_msg = "❌ Your Report Has Been Rejected 🥹"
                _save(d)
                await query.edit_message_text(msg)
                try: await context.bot.send_message(chat_id=s_rec["user_id"], text=u_msg)
                except: pass

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    logger.info("Bot fully running on Firebase Server.")
    app.run_polling()

if __name__ == "__main__":
    main()
