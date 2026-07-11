import os
import json
import threading
import datetime
import uuid
import random
import pyotp
import logging
import asyncio
from flask import Flask
from threading import Thread

import firebase_admin
from firebase_admin import credentials, db as fdb

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# FLASK KEEP-ALIVE (Render)
# ============================================================
_flask_app = Flask(__name__)

@_flask_app.route('/')
def _home():
    return "Bot is Running!"

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    t = Thread(target=lambda: _flask_app.run(host="0.0.0.0", port=port), daemon=True)
    t.start()

# ============================================================
# FIREBASE INIT
# ============================================================
FIREBASE_CRED = {
    "type": "service_account",
    "project_id": "shuvo-866aa",
    "private_key_id": "21ae4fa0c2f9a8b8392dba63a9672709e08c5d44",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQDTPR//ELuR8phl\nC3at3UPaDc5quupB+6NqE5bYDKVB8hu5SHOmL3hZ3lYAtMV42xhn00WbxEoTgdpt\nUEaMQVIe1wwBRinB+LxMFkVv5yZIJxBGQNa+gWmK6RaBoAocpggbbygbLbulW2i4\nHorFy6UeERsyRDw9TEo6dLP4UQoiG2BFzOxiFQS+mFvk3l44M2qbjoxXElvTZiBq\ns+WtU75mSvJBUx0LsKMx+rLxGepu3qczqqec/v6e8VNWDHZ0jai03Jd2GUzoR7Ld\nCmMEDpO9RWo1e7BFo4Den2J6dF0oDlqs3Mf2dkCNLoKeP96UR2ZTcLWAjcOIbzO1\nSc5jh843AgMBAAECgf9FF97fWmUO5vgP9tWXCP1dTeqJSdZVzdOPIo3hlYyWdlbI\nS3mIcRyZsfoGE+2wob0lKaLt304BIn+xbuNKGyKbmXAfGK5ivFsXAIw9Ub/wBvUX\nFKW/mzpqagByku3o+IPbhGmhax9XWMOGDFlIwpdHGLq1+iNBjzKaN4LikFQD8XZg\n0ryqRMtK/YJBy3Pb38/Tl1d4q80J3YXU+ri2oApLR0c1cxB+dY8RVAtiXcmx0L/r\nwJDS0V6kMtZImH9zW2hm1qXArTp62auAhFq1tL3h4QGUHvPYNfXHyxGVyWrkUMh1\n5R1B0gFrB6oXqlWahBGf2FjeAOlXJZdLU0R8Rj0CgYEA64iLrPhq6HMGrrausYkb\nf0IGbWHhh1ABb2nuXO1NQUDHVmi/toLGGwS/SNHmzmnPTPYYImjXfe+tTpV9ULUL\nj+vIAXp+kszQxcSo9LeYHXMAb6JLxnJBPuBKF26StP3mntw2rqQR/cOLAC/yI2G2\n51cTAE5qKPMtIAvxHY7wMpUCgYEA5Zgk7kBfyDZJt8EV2z33BspoOY/+F6vjYUVf\nlQTsLS+ClCbrOb+DxcdtyTxtHuQDeUJsE2d+lU+QEPIhZRbnVD1+ACsrdv+eZGuG\nG4JR1VWXDmWownTrQzBz950X3r0uCGQzlTcThQxuHW/nLWHHuAPpnoQ9/1Ho/ykE\nm3gG9psCgYAC8Jddt1QORrFEqP8RNDblpbtSzi/0cmkyLM5O1p9qOxbB21jZPFSg\nrbR9gjExTlzKByBR/aEC72ToYDFKOphEWZsLea3uwyOv9D5vn4MEixTsT8hGV9K8\nqCwEktq965VfUjxUfbPDyRcJD5AkJOoVhR61mET28eIUTlHaHpic6QKBgCw9SMBv\nvwUBEOtLVT7Njc/NKJAO4tME1+diSqyYKjn6sZqCdUjHUkjFyK3B6vTM0q6G0fRb\nONTkY8ogHbcw1powzxqRNurTDl4jKdAbKFGHEHhBtmbhyINFztKjfnn40enkBNx3\npFc6se0SJuVjtewLNPTKXnfX/KFN8glS82SJAoGBAOYjwt3jxalPVPOTPwnmdIbP\n65I40NVo4L6SPAd2HqAyvmcXPjwrmeSjyEgj5IlAQBuGSMaGZgkqw+TrvDNRalq/\nTPmtjzq4hqyyGS5r3lHC916QBJfVXv2QV4jUGKD+KWejwU3PrtF4wiLvF4EIbPJ1\nIb+nDcQ7FeRIiO27dkQ7\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@shuvo-866aa.iam.gserviceaccount.com",
    "client_id": "101947082739477661394",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40shuvo-866aa.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
FIREBASE_URL = "https://shuvo-866aa-default-rtdb.firebaseio.com/"

cred = credentials.Certificate(FIREBASE_CRED)
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})

_lock = threading.Lock()

# ============================================================
# FIREBASE DB HELPERS
# ============================================================
def fb_get(path):
    try:
        return fdb.reference(path).get()
    except Exception as e:
        logger.error(f"fb_get error {path}: {e}")
        return None

def fb_set(path, value):
    try:
        fdb.reference(path).set(value)
    except Exception as e:
        logger.error(f"fb_set error {path}: {e}")

def fb_update(path, value):
    try:
        fdb.reference(path).update(value)
    except Exception as e:
        logger.error(f"fb_update error {path}: {e}")

def fb_delete(path):
    try:
        fdb.reference(path).delete()
    except Exception as e:
        logger.error(f"fb_delete error {path}: {e}")

# ============================================================
# DATA HELPERS — Firebase backend
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
    """Firebase থেকে সব ডেটা লোড করো"""
    try:
        data = fb_get("/") or {}
        # defaults
        data.setdefault("users", {})
        data.setdefault("submissions", {})
        data.setdefault("withdrawals", {})
        data.setdefault("dynamic_tasks", {})
        data.setdefault("saved_usernames", [])
        data.setdefault("task_password", "shuvo9")
        data.setdefault("visibility", {"instagram_task": True, "facebook_task": True})
        return data
    except Exception:
        return _default_data()

def _save_user(uid, user_data):
    fb_set(f"/users/{uid}", user_data)

def _save_submission(sub_id, sub_data):
    fb_set(f"/submissions/{sub_id}", sub_data)

def _save_withdrawal(w_id, w_data):
    fb_set(f"/withdrawals/{w_id}", w_data)

def _save_task(t_id, task_data):
    fb_set(f"/dynamic_tasks/{t_id}", task_data)

def _delete_task(t_id):
    fb_delete(f"/dynamic_tasks/{t_id}")

def _save_visibility(visibility):
    fb_set("/visibility", visibility)

def _save_password(pwd):
    fb_set("/task_password", pwd)

def _save_usernames(usernames):
    fb_set("/saved_usernames", usernames)

def get_or_create_user(user_id: int, username: str = ""):
    uid = str(user_id)
    user_data = fb_get(f"/users/{uid}")
    if not user_data:
        user_data = {
            "user_id": user_id,
            "username": username,
            "balance": 0.0,
            "language": "bn",
            "success_count": 0,
            "review_count": 0,
            "rejected_count": 0
        }
        _save_user(uid, user_data)
    return user_data

def generate_profile_or_get_saved():
    saved = fb_get("/saved_usernames") or []
    if isinstance(saved, dict):
        saved = list(saved.values())
    if saved:
        login_name = saved.pop(0)
        _save_usernames(saved)
        first_names = ["fatima", "wafaa", "ahmed", "youssef", "omar", "nour", "ali"]
        last_names  = ["Zayan", "Emad", "Khan", "Ahmed", "Ali", "Hassan"]
        f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        return f_name, login_name
    return None, None

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN          = "8738544813:AAHMBZucZMhEJyA88e-qI43RjzBYyL5_j_c"
ADMIN_ID           = int(os.getenv("ADMIN_ID", "6470499890"))
REQUIRED_CHANNELS  = ["@range_channele", "@insagramth"]

# ============================================================
# MULTI-LANGUAGE
# ============================================================
LANGUAGES = {
    "en": {
        "welcome": "🎉 Welcome to {name} TaskPro Bot! 🤖\n\nComplete tasks, submit your proof, and earn rewards with ease.\n\n🚀 Happy Earning & Good Luck!",
        "btn_balance": "💳 BALANCE", "btn_tasks": "📋 TASKS", "btn_withdraw": "📤 WITHDRAW",
        "btn_report": "📊 YOUR REPORT", "btn_support": "ℹ️ SUPPORT", "btn_language": "🌐 LANGUAGE",
        "btn_admin": "🛠️ ADMIN PANEL", "btn_back": "🔙 BACK", "btn_cancel": "❌ cancel",
        "btn_start": "▶️ Start", "btn_video": "🎥 Video", "btn_how_to_2fa": "❓ How to get 2fa?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:", "lang_changed": "✅ Language changed to English!",
        "balance_msg": "💳 Your Balance: {bal} ৳",
        "report_msg": "📊 All Account Report\n\n✅ Success: [{s}]\n⏳ Reviewing: [{r}]\n❌ Rejected: [{rej}]",
        "select_cat": "📋 Select Category:", "task_hidden": "❌ This task is currently hidden by Admin.",
        "no_tasks": "❌ No tasks available in this category.", "choose_type": "🎯 Choose Task:",
        "send_2fa_secret": "👉 Please Send Your 2FA Secret Key", "send_cookies": "👉 Please Send Your Cookies Data",
        "invalid_2fa": "❌ Invalid 2FA Secret Key! Please send a valid key again:",
        "withdraw_dash": "💳 Your Balance Dashboard\n\n💰 Balance: {bal} ৳\n💸 Minimum Withdraw: 50 ৳\n💳 Withdrawal Charge: 5 ৳\n✅ You Will Receive: {rec} ৳",
        "withdraw_min_err": "❌ Unsuccessful balance: Minimum 50 ৳ required", "select_meth": "💳 Select Your Withdraw Method:",
        "send_num": "📱 Please Send Your {method} Number", "enter_amt": "💰 Please Enter Your Withdraw Amount:",
        "insufficient": "❌ Insufficient balance.", "min_amt_err": "❌ Minimum withdraw is 50 ৳",
        "check_info": "📋 Please Check Your Info\n\n📱 Number: {num}\n💳 Method: {method}\n💵 Amount: {amt} ৳\n✅ Receive: {rec} ৳\n\n✅ If All Information Is Correct, Please Tap the Confirm Button. 👇",
        "btn_confirm": "✅ Confirm", "pay_pending": "⏳ Your Payment Is Pending.\n\n👨‍💼 Please Wait for Admin Approval.",
        "cookies_rec": "👉 Cookies Received. Click below to proceed.", "btn_acc_reg": "✅ Account Registered",
        "invite_check": "⚠️ Have You Invited 2 Friends?\n\n❌ If You Have Not Invited 2 Friends, Your Report Will Be Rejected.",
        "btn_subbed": "✅ Yes | I Am Subscribed", "thanks_msg": "✅ Thanks! Please Do Not Unfollow. Follow the Rules.",
        "report_received": "✅ Your report has been received!\n⏳ Please wait 16–24 hours.",
        "no_usernames_err": "❌ No user available yet!", "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
    },
    "bn": {
        "welcome": "🎉 Welcome to {name} TaskPro Bot! 🤖\n\nComplete tasks, submit your proof, and earn rewards with ease.\n\n🚀 Happy Earning & Good Luck!",
        "btn_balance": "💳 ব্যালেন্স", "btn_tasks": "📋 কাজ (TASKS)", "btn_withdraw": "📤 টাকা তুলুন",
        "btn_report": "📊 আপনার রিপোর্ট", "btn_support": "ℹ️ সাপোর্ট (SUPPORT)", "btn_language": "🌐 ভাষা (LANGUAGE)",
        "btn_admin": "🛠️ এডমিন প্যানেল", "btn_back": "🔙 পেছনে যান", "btn_cancel": "❌ বাতিল করুন",
        "btn_start": "▶️ শুরু করুন", "btn_video": "🎥 ভিডিও দেখুন", "btn_how_to_2fa": "❓ How to get 2fa?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:", "lang_changed": "✅ ভাষা পরিবর্তন করে বাংলায় সেট করা হয়েছে!",
        "balance_msg": "💳 আপনার বর্তমান ব্যালেন্স: {bal} ৳",
        "report_msg": "📊 সকল অ্যাকাউন্ট রিপোর্ট\n\n✅ সফল: [{s}]\n⏳ রিভিউতে আছে: [{r}]\n❌ বাতিল হয়েছে: [{rej}]",
        "select_cat": "📋 ক্যাটাগরি নির্বাচন করুন:", "task_hidden": "❌ এই কাজটি বর্তমানে এডমিন দ্বারা হাইড করা আছে।",
        "no_tasks": "❌ এই ক্যাটাগরিতে বর্তমানে কোনো কাজ নেই।", "choose_type": "🎯 কাজ বেছে নিন:",
        "send_2fa_secret": "👉 অনুগ্রহ করে আপনার 2FA সিক্রেট কি (Secret Key) পাঠান",
        "send_cookies": "👉 অনুগ্রহ করে আপনার কুকিজ (Cookies) ডাটা পাঠান",
        "invalid_2fa": "❌ ভুল 2FA সিক্রেট কি! দয়া করে আবার সঠিক কি পাঠান:",
        "withdraw_dash": "💳 আপনার ব্যালেন্স ড্যাশবোর্ড\n\n💰 ব্যালেন্স: {bal} ৳\n💸 সর্বনিম্ন উইথড্র: ৫০ ৳\n💳 উইথড্র চার্জ: ৫ ৳\n✅ আপনি পাবেন: {rec} ৳",
        "withdraw_min_err": "❌ Unsuccessful balance: Minimum 50 ৳ required", "select_meth": "💳 আপনার উইথড্র পদ্ধতি নির্বাচন করুন:",
        "send_num": "📱 অনুগ্রহ করে আপনার {method} নম্বরটি পাঠান", "enter_amt": "💰 অনুগ্রহ করে আপনার উইথড্র অ্যামাউন্ট লিখুন:",
        "insufficient": "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই।", "min_amt_err": "❌ সর্বনিম্ন উইথড্র ৫০ ৳",
        "check_info": "📋 দয়া করে আপনার তথ্য যাচাই করুন\n\n📱 নম্বর: {num}\n💳 মাধ্যম: {method}\n💵 পরিমাণ: {amt} ৳\n✅ আপনি পাবেন: {rec} ৳\n\n✅ সব তথ্য ঠিক থাকলে নিচের কনফার্ম বাটনে চাপুন। 👇",
        "btn_confirm": "✅ কনফার্ম করুন", "pay_pending": "⏳ আপনার পেমেন্ট পেন্ডিং অবস্থায় আছে।\n\n👨‍💼 অনুগ্রহ করে এডমিনের অনুমোদনের জন্য অপেক্ষা করুন।",
        "cookies_rec": "👉 কুকিজ পাওয়া গেছে। সামনে এগিয়ে যেতে নিচের বাটনে চাপুন।", "btn_acc_reg": "✅ অ্যাকাউন্ট রেজিস্টার্ড",
        "invite_check": "⚠️ আপনি কি ২ জন বন্ধুকে ইনভাইট করেছেন?\n\n❌ যদি আপনি ২ জন বন্ধুকে ইনভাইট না করে থাকেন, তবে আপনার রিপোর্টটি রিজেক্ট করা হবে।",
        "btn_subbed": "✅ হ্যাঁ | আমি সাবসক্রাইব করেছি", "thanks_msg": "✅ ধন্যবাদ! অনুগ্রহ করে আনফলো করবেন না। নিয়ম মেনে চলুন।",
        "report_received": "✅ আপনার রিপোর্টটি গ্রহণ করা হয়েছে!\n⏳ অনুগ্রহ করে ১৬–২৪ ঘণ্টা অপেক্ষা করুন।",
        "no_usernames_err": "❌ বর্তমানে কোনো ইউজার খালি নেই!",
        "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
    }
}

# ============================================================
# CHECK JOIN
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
    btn_ch1    = InlineKeyboardButton("📢 Range Channel", url="https://t.me/range_channele")
    btn_ch2    = InlineKeyboardButton("📢 Instagram TH",  url="https://t.me/insagramth")
    btn_verify = InlineKeyboardButton("✅ Verify Membership", callback_data="verify_join")
    object.__setattr__(btn_ch1,    'style', 'primary')
    object.__setattr__(btn_ch2,    'style', 'primary')
    object.__setattr__(btn_verify, 'style', 'success')
    return InlineKeyboardMarkup([[btn_ch1], [btn_ch2], [btn_verify]])

# ============================================================
# KEYBOARDS
# ============================================================
def main_menu_keyboard(user_id: int, lang: str):
    ln = LANGUAGES[lang]
    def kb(text, style):
        b = KeyboardButton(text)
        object.__setattr__(b, 'style', style)
        return b
    buttons = [
        [kb(ln["btn_balance"], "success"),  kb(ln["btn_tasks"],    "primary")],
        [kb(ln["btn_withdraw"], "success"), kb(ln["btn_report"],   "primary")],
        [kb(ln["btn_support"],  "primary"), kb(ln["btn_language"], "primary")],
    ]
    if user_id == ADMIN_ID:
        b = KeyboardButton(ln["btn_admin"])
        object.__setattr__(b, 'style', 'danger')
        buttons.append([b])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ============================================================
# USER STATE
# ============================================================
USER_STATE = {}

# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    u_data = get_or_create_user(user.id, user.username or "")
    lang   = u_data.get("language", "bn")
    if not await is_user_joined_all(context.bot, user.id):
        await update.message.reply_text(LANGUAGES[lang]["force_join_msg"], reply_markup=get_force_join_keyboard(lang))
        return
    await update.message.reply_text(
        LANGUAGES[lang]["welcome"].format(name=user.first_name),
        reply_markup=main_menu_keyboard(user.id, lang)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id      = update.effective_user.id
    text         = update.message.text.strip()
    db_data      = _load()
    user_profile = get_or_create_user(user_id, update.effective_user.username or "")
    lang         = user_profile.get("language", "bn")
    ln           = LANGUAGES[lang]

    if not await is_user_joined_all(context.bot, user_id):
        await update.message.reply_text(ln["force_join_msg"], reply_markup=get_force_join_keyboard(lang))
        return

    if text == "❓ How to get 2fa?":
        await update.message.reply_text("📹 How to setup 2FA Video Link:\n\nhttps://t.me/range_channele/955")
        return

    def kb(t, s):
        b = KeyboardButton(t); object.__setattr__(b,'style',s); return b
    def ib(t, cb, s="primary"):
        b = InlineKeyboardButton(t, callback_data=cb); object.__setattr__(b,'style',s); return b

    # ---- ADMIN FLOWS ----
    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_change_password":
        USER_STATE.pop(user_id, None)
        _save_password(text)
        await update.message.reply_text(f"🔐 নতুন পাসওয়ার্ড সেভ হয়েছে!\nবর্তমান পাসওয়ার্ড: `{text}`", parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_save_username":
        USER_STATE.pop(user_id, None)
        raw_names = text.replace(",", " ").split()
        saved     = fb_get("/saved_usernames") or []
        if isinstance(saved, dict): saved = list(saved.values())
        for r in raw_names:
            if r not in saved: saved.append(r)
        _save_usernames(saved)
        await update.message.reply_text(f"✅ ইউজারনেম সেভ হয়েছে! মোট: {len(saved)} টি।", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_name":
        USER_STATE[user_id]["task_name"] = text
        USER_STATE[user_id]["step"]      = "admin_task_price"
        await update.message.reply_text("💵 টাস্কের দাম কত হবে লিখুন (যেমন: 3.5):")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_price":
        try:
            price = float(text)
            USER_STATE[user_id]["task_price"] = price
            USER_STATE[user_id]["step"]       = "admin_task_rules"
            await update.message.reply_text("📝 টাস্কের নিয়মাবলী লিখুন:")
        except:
            await update.message.reply_text("❌ সঠিক সংখ্যা দিন।")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_rules":
        USER_STATE[user_id]["task_rules"] = text
        USER_STATE[user_id]["step"]       = "admin_task_type"
        kb_ = InlineKeyboardMarkup([[ib("🍪 Cookies Work","adm_t_type:cookies","success")],[ib("🛡️ 2FA Work","adm_t_type:2fa","primary")]])
        await update.message.reply_text("🎯 এটি কি ধরনের কাজ হবে?", reply_markup=kb_)
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "broadcast_msg":
        USER_STATE.pop(user_id, None)
        all_uids = list((fb_get("/users") or {}).keys())
        count = 0
        for u in all_uids:
            try:
                await context.bot.send_message(chat_id=int(u), text=f"📢 ADMIN NOTICE:\n\n{text}")
                count += 1
            except: pass
        await update.message.reply_text(f"✅ Broadcast sent to {count} users.", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "add_money_uid":
        USER_STATE[user_id]["target_uid"] = text
        USER_STATE[user_id]["step"]       = "add_money_amount"
        await update.message.reply_text("💵 Enter Amount to Add:")
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "add_money_amount":
        try:
            amount = float(text)
            target = USER_STATE[user_id]["target_uid"]
            u_data = fb_get(f"/users/{target}") or {}
            new_bal = round(u_data.get("balance", 0) + amount, 2)
            fb_update(f"/users/{target}", {"balance": new_bal})
            await update.message.reply_text(f"✅ Added ৳{amount} to UID {target}")
            try: await context.bot.send_message(chat_id=int(target), text=f"💰 Admin added ৳{amount} to your balance!")
            except: pass
        except:
            await update.message.reply_text("❌ Invalid Amount.")
        USER_STATE.pop(user_id, None)
        return

    # ---- WITHDRAW FLOW ----
    if USER_STATE.get(user_id, {}).get("step") == "withdraw_num":
        if text in [ln["btn_cancel"], "cancel"]:
            USER_STATE.pop(user_id, None)
            await update.message.reply_text("❌", reply_markup=main_menu_keyboard(user_id, lang))
            return
        USER_STATE[user_id]["number"] = text
        USER_STATE[user_id]["step"]   = "withdraw_amt"
        await update.message.reply_text(ln["enter_amt"])
        return

    if USER_STATE.get(user_id, {}).get("step") == "withdraw_amt":
        try:
            amt    = float(text)
            bal    = user_profile["balance"]
            if amt > bal:
                await update.message.reply_text(ln["insufficient"]); USER_STATE.pop(user_id,None); return
            if amt < 50:
                await update.message.reply_text(ln["min_amt_err"]); USER_STATE.pop(user_id,None); return
            method  = USER_STATE[user_id]["method"]
            num     = USER_STATE[user_id]["number"]
            charge  = 5.0
            receive = amt - charge
            USER_STATE[user_id].update({"amt": amt, "receive": receive, "step": "withdraw_confirm"})
            confirm_text = ln["check_info"].format(num=num, method=method, amt=amt, rec=receive)
            kb_ = ReplyKeyboardMarkup([[kb(ln["btn_confirm"],"success"), kb(ln["btn_cancel"],"danger")]], resize_keyboard=True)
            await update.message.reply_text(confirm_text, reply_markup=kb_)
        except:
            await update.message.reply_text("❌ Invalid format.")
            USER_STATE.pop(user_id, None)
        return

    if USER_STATE.get(user_id, {}).get("step") == "withdraw_confirm":
        if text == ln["btn_confirm"]:
            state = USER_STATE[user_id]
            w_id  = str(uuid.uuid4())[:8]
            w_data = {
                "w_id": w_id, "user_id": user_id, "username": user_profile["username"],
                "number": state["number"], "method": state["method"],
                "amount": state["amt"], "status": "pending"
            }
            _save_withdrawal(w_id, w_data)
            await update.message.reply_text(ln["pay_pending"], reply_markup=main_menu_keyboard(user_id, lang))
            admin_kb = InlineKeyboardMarkup([[ib("✅ APPROVE", f"w_app:{w_id}", "success"), ib("❌ REJECT", f"w_rej:{w_id}", "danger")]])
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💸 New Payment Request\n\n👤 User: @{user_profile['username']}\n🆔 UID: {user_id}\n📱 Number: {state['number']}\n💳 Method: {state['method']}\n💰 Amount: {state['amt']} ৳",
                reply_markup=admin_kb
            )
        else:
            await update.message.reply_text("❌", reply_markup=main_menu_keyboard(user_id, lang))
        USER_STATE.pop(user_id, None)
        return

    # ---- COOKIES ----
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_cookies":
        if text in [ln["btn_cancel"], "cancel"]:
            USER_STATE.pop(user_id, None)
            await update.message.reply_text("❌", reply_markup=main_menu_keyboard(user_id, lang))
            return
        USER_STATE[user_id]["cookies_data"] = text
        USER_STATE[user_id]["step"]         = "cookies_submitted"
        kb_ = ReplyKeyboardMarkup([[kb(ln["btn_acc_reg"],"success")],[kb(ln["btn_cancel"],"danger")]], resize_keyboard=True)
        await update.message.reply_text(ln["cookies_rec"], reply_markup=kb_)
        return

    if text == ln["btn_acc_reg"]:
        state = USER_STATE.get(user_id)
        if state and state.get("step") in ("cookies_submitted","2fa_verify"):
            kb_ = ReplyKeyboardMarkup([[kb(ln["btn_subbed"],"success")],[kb(ln["btn_cancel"],"danger")]], resize_keyboard=True)
            await update.message.reply_text(ln["invite_check"], reply_markup=kb_)
            USER_STATE[user_id]["step"] = "cookies_final_confirm" if state["step"]=="cookies_submitted" else "2fa_final_confirm"
            return

    if text == ln["btn_subbed"]:
        state = USER_STATE.get(user_id)
        if state and state.get("step") == "2fa_final_confirm":
            sub_id    = str(uuid.uuid4())[:8]
            sub_data  = {
                "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                "task_type": "2fa", "task_id": state.get("task_id"),
                "login": state["login"], "pass": state["pass"], "status": "pending"
            }
            _save_submission(sub_id, sub_data)
            fb_update(f"/users/{str(user_id)}", {"review_count": user_profile.get("review_count",0)+1})
            # txt ফাইল admin কে
            import io
            file_bytes = io.BytesIO(
                f"Dynamic 2FA Report\nTask Name: {state.get('t_name','')}\nUsername: {state['login']}\nPassword: {state['pass']}\n2FA Key: {state.get('secret','')}".encode()
            )
            file_bytes.name = f"submission_{sub_id}.txt"
            await context.bot.send_document(chat_id=ADMIN_ID, document=file_bytes, filename=f"submission_{sub_id}.txt",
                caption=f"Dynamic 2FA Task\nUser: @{user_profile['username']}\nUID: {user_id}")
            await update.message.reply_text(ln["report_received"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

        if state and state.get("step") == "cookies_final_confirm":
            sub_id   = str(uuid.uuid4())[:8]
            sub_data = {
                "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                "task_type": "cookies", "task_id": state.get("task_id"),
                "login": state["login"], "pass": state["pass"], "status": "pending"
            }
            _save_submission(sub_id, sub_data)
            fb_update(f"/users/{str(user_id)}", {"review_count": user_profile.get("review_count",0)+1})
            import io
            file_bytes = io.BytesIO(
                f"Task Name: {state['t_name']}\nUsername: {state['login']}\nPassword: {state['pass']}\nCookies: {state['cookies_data']}".encode()
            )
            file_bytes.name = f"submission_{sub_id}.txt"
            await context.bot.send_document(chat_id=ADMIN_ID, document=file_bytes, filename=f"submission_{sub_id}.txt",
                caption=f"🍪 Cookies Task\nUser: @{user_profile['username']}\nUID: {user_id}\nSub ID: {sub_id}")
            await update.message.reply_text(ln["thanks_msg"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

    # ---- 2FA SECRET ----
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_2fa":
        if text in [ln["btn_cancel"], "cancel"]:
            await update.message.reply_text("❌", reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return
        user_secret = text.replace(" ", "")
        try:
            totp         = pyotp.TOTP(user_secret)
            current_code = totp.now()
        except:
            await update.message.reply_text(ln["invalid_2fa"])
            return
        state          = USER_STATE[user_id]
        state["secret"]= user_secret
        state["step"]  = "2fa_verify"
        remaining      = 30 - (int(datetime.datetime.now().timestamp()) % 30)
        kb_  = ReplyKeyboardMarkup([[kb(ln["btn_acc_reg"],"success")],[kb(ln["btn_cancel"],"danger")]], resize_keyboard=True)
        await update.message.reply_text("👉 2FA Key Received.", reply_markup=kb_)
        btn_ref = InlineKeyboardButton("🔄 Refresh", callback_data="refresh_2fa_code")
        object.__setattr__(btn_ref, 'style', 'primary')
        msg = await update.message.reply_text(
            f"╔══════════╗\n🔑 Your 2FA Code\n╚══════════╝\n\n🔢 Code : `{current_code}`\n\n⏱️ Valid : {remaining}s\n━━━━━━━━━━",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[btn_ref]])
        )
        state["code_msg_id"] = msg.message_id
        return

    # ---- MENU ----
    if text in ["💳 BALANCE", "💳 ব্যালেন্স"]:
        await update.message.reply_text(ln["balance_msg"].format(bal=user_profile['balance']), reply_markup=main_menu_keyboard(user_id, lang))
        return

    if text in ["📊 YOUR REPORT", "📊 আপনার রিপোর্ট"]:
        await update.message.reply_text(
            ln["report_msg"].format(s=user_profile.get('success_count',0), r=user_profile.get('review_count',0), rej=user_profile.get('rejected_count',0)),
            reply_markup=main_menu_keyboard(user_id, lang)
        )
        return

    if text in ["ℹ️ SUPPORT", "ℹ️ সাপোর্ট (SUPPORT)"]:
        btn_adm = InlineKeyboardButton("👤 Admin", url="https://t.me/adim_shuvo")
        object.__setattr__(btn_adm, 'style', 'primary')
        await update.message.reply_text(ln["support_msg"], reply_markup=InlineKeyboardMarkup([[btn_adm]]))
        return

    if text in ["🌐 LANGUAGE", "🌐 ভাষা (LANGUAGE)"]:
        btn_bn = InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")
        btn_en = InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        object.__setattr__(btn_bn, 'style', 'success')
        object.__setattr__(btn_en, 'style', 'primary')
        await update.message.reply_text(ln["select_lang"], reply_markup=InlineKeyboardMarkup([[btn_bn, btn_en]]))
        return

    if text in ["📋 TASKS", "📋 কাজ (TASKS)"]:
        vis       = db_data.get("visibility", {})
        task_list = []
        if vis.get("instagram_task", True) or user_id == ADMIN_ID:
            b = KeyboardButton("🎯 Instagram Task" if lang=="en" else "🎯 ইনস্টাগ্রাম কাজ")
            object.__setattr__(b,'style','primary'); task_list.append([b])
        if vis.get("facebook_task", True) or user_id == ADMIN_ID:
            b = KeyboardButton("🎯 Facebook Task" if lang=="en" else "🎯 ফেসবুক কাজ")
            object.__setattr__(b,'style','primary'); task_list.append([b])
        b = KeyboardButton(ln["btn_back"]); object.__setattr__(b,'style','danger'); task_list.append([b])
        await update.message.reply_text(ln["select_cat"], reply_markup=ReplyKeyboardMarkup(task_list, resize_keyboard=True))
        return

    if text in ["🎯 Instagram Task","🎯 ইনস্টাগ্রাম কাজ","🎯 Facebook Task","🎯 ফেসবুক কাজ"]:
        cat_key      = "instagram" if "Insta" in text or "ইনস্টা" in text else "facebook"
        vis          = db_data.get("visibility", {})
        if not vis.get(f"{cat_key}_task", True) and user_id != ADMIN_ID:
            await update.message.reply_text(ln["task_hidden"]); return
        active_tasks = [t for t in db_data.get("dynamic_tasks",{}).values() if t.get("category")==cat_key]
        if not active_tasks:
            await update.message.reply_text(ln["no_tasks"]); return
        sub_tasks = []
        for t in active_tasks:
            b = KeyboardButton(f"📌 {t['name']} ({t['price']} ৳)")
            object.__setattr__(b,'style','success'); sub_tasks.append([b])
        b = KeyboardButton(ln["btn_cancel"]); object.__setattr__(b,'style','danger'); sub_tasks.append([b])
        await update.message.reply_text(ln["choose_type"], reply_markup=ReplyKeyboardMarkup(sub_tasks, resize_keyboard=True))
        return

    if text.startswith("📌 "):
        clean_name  = text.replace("📌 ","").split(" (")[0]
        all_tasks   = db_data.get("dynamic_tasks",{})
        target_task = next((t for t in all_tasks.values() if t["name"]==clean_name), None)
        if target_task:
            tid = target_task["id"]
            USER_STATE[user_id] = {"task_id": tid, "task_type": target_task["type"]}
            bstr = KeyboardButton(ln["btn_start"]); object.__setattr__(bstr,'style','success')
            bvid = KeyboardButton(ln["btn_video"]); object.__setattr__(bvid,'style','primary')
            bcnc = KeyboardButton(ln["btn_cancel"]); object.__setattr__(bcnc,'style','danger')
            kb_  = ReplyKeyboardMarkup([[bstr],[bvid],[bcnc]], resize_keyboard=True)
            await update.message.reply_text(
                f"🛡️ 🌟 *{target_task['name']}*\n\n💵 Payout: ৳{target_task['price']}\n\n📝 *Rules:*\n{target_task['rules']}\n\n🚀 Tap START to continue.",
                parse_mode="Markdown", reply_markup=kb_
            )
        return

    if text in [ln["btn_video"], "🎥 ভিডিও দেখুন"]:
        await update.message.reply_text("🎥 Video Link:\n\nhttps://t.me/range_channele/955")
        return

    if text == ln["btn_start"]:
        state  = USER_STATE.get(user_id)
        if state and "task_id" in state:
            t_data = db_data.get("dynamic_tasks",{}).get(state["task_id"])
            if t_data:
                f_name, login_name = generate_profile_or_get_saved()
                if login_name is None:
                    await update.message.reply_text(ln["no_usernames_err"]); return
                pass_val = db_data.get("task_password","shuvo9")
                state.update({"login": login_name, "pass": pass_val, "t_name": t_data["name"]})
                await update.message.reply_text(f"First name: `{f_name}`\nLogin: `{login_name}`\nPassword: `{pass_val}`", parse_mode="Markdown")
                if state["task_type"] == "2fa":
                    state["step"] = "waiting_for_2fa"
                    b2 = KeyboardButton(ln["btn_how_to_2fa"]); object.__setattr__(b2,'style','primary')
                    bc = KeyboardButton(ln["btn_cancel"]);     object.__setattr__(bc,'style','danger')
                    await update.message.reply_text(ln["send_2fa_secret"], reply_markup=ReplyKeyboardMarkup([[b2],[bc]], resize_keyboard=True))
                else:
                    state["step"] = "waiting_for_cookies"
                    bc = KeyboardButton(ln["btn_cancel"]); object.__setattr__(bc,'style','danger')
                    await update.message.reply_text(ln["send_cookies"], reply_markup=ReplyKeyboardMarkup([[bc]], resize_keyboard=True))
        return

    if text in ["📤 WITHDRAW","📤 টাকা তুলুন"]:
        bal = user_profile["balance"]
        if bal < 50:
            btn_fake = InlineKeyboardButton("⚠️ Insufficient Balance", callback_data="popup_error_alert")
            await update.message.reply_text("❌ Click below:", reply_markup=InlineKeyboardMarkup([[btn_fake]]))
            return
        btn_wth = InlineKeyboardButton("Withdraw", callback_data="start_withdraw")
        object.__setattr__(btn_wth,'style','success')
        await update.message.reply_text(ln["withdraw_dash"].format(bal=bal, rec=max(0.0,bal-5.0)), reply_markup=InlineKeyboardMarkup([[btn_wth]]))
        return

    # ---- ADMIN PANEL ----
    if text in ["🛠️ ADMIN PANEL","🛠️ ENDMIN PANEL","🛠️ এডমিন প্যানেল"] and user_id==ADMIN_ID:
        def ab(t,s): b=KeyboardButton(t); object.__setattr__(b,'style',s); return b
        kb_ = ReplyKeyboardMarkup([
            [ab("➕ Add Task","success"),      ab("❌ Delete Task","danger")],
            [ab("👁️ Task Hide/Show","primary"),ab("👤 User Broadcast","primary")],
            [ab("➕ Add Money","success"),      ab("📥 Username Save","success")],
            [ab("🗂️ All Report","primary"),    ab("🗑️ User Delete","danger")],
            [ab("🔐 Password Change","primary"),ab(ln["btn_back"],"danger")],
        ], resize_keyboard=True)
        await update.message.reply_text("🛠️ Admin Control Dashboard", reply_markup=kb_)
        return

    if user_id==ADMIN_ID and text=="🔐 Password Change":
        USER_STATE[user_id] = {"step":"admin_change_password"}
        current_pwd = fb_get("/task_password") or "shuvo9"
        await update.message.reply_text(f"🔐 বর্তমান পাসওয়ার্ড: `{current_pwd}`\n\nনতুন পাসওয়ার্ড লিখুন:", parse_mode="Markdown")
        return

    if user_id==ADMIN_ID and text=="❌ Delete Task":
        kb_ = InlineKeyboardMarkup([[
            ib("Instagram Tasks","adm_del_cat:instagram","danger"),
            ib("Facebook Tasks","adm_del_cat:facebook","danger")
        ]])
        await update.message.reply_text("🗑️ কোন ক্যাটাগরির কাজ ডিলিট করতে চান?", reply_markup=kb_)
        return

    if user_id==ADMIN_ID and text=="📥 Username Save":
        USER_STATE[user_id] = {"step":"admin_save_username"}
        saved_count = len(fb_get("/saved_usernames") or [])
        await update.message.reply_text(f"📥 ইউজারনেম পাঠান:\n(বর্তমানে সেভ আছে: {saved_count} টি)")
        return

    if user_id==ADMIN_ID and text=="➕ Add Task":
        kb_ = InlineKeyboardMarkup([[ib("Instagram","adm_cat:instagram","success"), ib("Facebook","adm_cat:facebook","success")]])
        await update.message.reply_text("📁 কোন ক্যাটাগরিতে কাজ যুক্ত করতে চান?", reply_markup=kb_)
        return

    if user_id==ADMIN_ID and text=="👁️ Task Hide/Show":
        v   = fb_get("/visibility") or {"instagram_task":True,"facebook_task":True}
        kb_ = InlineKeyboardMarkup([[
            ib(f"IG Cat [{'ON' if v.get('instagram_task',True) else 'OFF'}]","h_ig_m","primary"),
            ib(f"FB Cat [{'ON' if v.get('facebook_task',True) else 'OFF'}]","h_fb_m","primary")
        ]])
        await update.message.reply_text("👁️ Click to Toggle:", reply_markup=kb_)
        return

    if user_id==ADMIN_ID and text=="👤 User Broadcast":
        USER_STATE[user_id] = {"step":"broadcast_msg"}
        await update.message.reply_text("📢 সব ইউজারকে পাঠানোর মেসেজ লিখুন:")
        return

    if user_id==ADMIN_ID and text=="➕ Add Money":
        USER_STATE[user_id] = {"step":"add_money_uid"}
        await update.message.reply_text("👤 UID দিন:")
        return

    if user_id==ADMIN_ID and text=="🗑️ User Delete":
        saved_count = len(fb_get("/saved_usernames") or [])
        btn_del = InlineKeyboardButton("⚠️ ডিলিট নিশ্চিত করুন", callback_data="adm_confirm_delete_all_saved_usernames")
        object.__setattr__(btn_del,'style','danger')
        await update.message.reply_text(f"📊 সেভ করা ইউজারনেম: {saved_count} টি।\n\nসব ডিলিট করবেন?", reply_markup=InlineKeyboardMarkup([[btn_del]]))
        return

    if user_id==ADMIN_ID and text=="🗂️ All Report":
        subs = fb_get("/submissions") or {}
        pending = [s for s in subs.values() if s.get("status")=="pending"]
        if not pending:
            await update.message.reply_text("✅ No pending reports."); return
        for s in pending:
            kb_ = InlineKeyboardMarkup([[ib("Approve",f"rep_app:{s['sub_id']}","success"), ib("Reject",f"rep_rej:{s['sub_id']}","danger")]])
            await update.message.reply_text(f"User ID: {s['user_id']}\nType: {s['task_type']}\nLogin: {s['login']}\nStatus: Pending", reply_markup=kb_)
        return

    if text in [ln["btn_cancel"],ln["btn_back"],"cancel","❌ cancel","🔙 BACK"]:
        USER_STATE.pop(user_id, None)
        await update.message.reply_text("🔙 Menu", reply_markup=main_menu_keyboard(user_id, lang))

# ============================================================
# CALLBACK QUERY
# ============================================================
async def delete_message_after_delay(context, chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try: await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except: pass

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query        = update.callback_query
    user_id      = query.from_user.id
    data         = query.data
    user_profile = get_or_create_user(user_id, query.from_user.username or "")
    lang         = user_profile.get("language","bn")
    ln           = LANGUAGES[lang]

    def ib(t,cb,s="primary"):
        b = InlineKeyboardButton(t,callback_data=cb); object.__setattr__(b,'style',s); return b

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
            msg = await context.bot.send_message(chat_id=user_id, text=ln["verify_success"])
            asyncio.create_task(delete_message_after_delay(context, user_id, msg.message_id, 5))
            await asyncio.sleep(5)
            await context.bot.send_message(chat_id=user_id, text=ln["welcome"].format(name=query.from_user.first_name), reply_markup=main_menu_keyboard(user_id, lang))
        else:
            await context.bot.send_message(chat_id=user_id, text=ln["not_joined_all"])
        return

    if data == "refresh_2fa_code":
        state = USER_STATE.get(user_id)
        if state and state.get("step")=="2fa_verify" and "secret" in state:
            try:
                totp         = pyotp.TOTP(state["secret"])
                current_code = totp.now()
                remaining    = 30-(int(datetime.datetime.now().timestamp())%30)
                btn_ref      = InlineKeyboardButton("🔄 Refresh", callback_data="refresh_2fa_code")
                object.__setattr__(btn_ref,'style','primary')
                await query.edit_message_text(
                    f"╔══════════╗\n🔑 Your 2FA Code\n╚══════════╝\n\n🔢 Code : `{current_code}`\n\n⏱️ Valid : {remaining}s\n━━━━━━━━━━",
                    parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[btn_ref]])
                )
            except: pass
        return

    if data.startswith("adm_cat:"):
        cat = data.split(":")[1]
        USER_STATE[user_id] = {"category": cat, "step": "admin_task_name"}
        await query.message.reply_text("📝 টাস্কের নাম দিন:")
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_del_cat:"):
        cat          = data.split(":")[1]
        all_tasks    = fb_get("/dynamic_tasks") or {}
        active_tasks = [t for t in all_tasks.values() if t.get("category")==cat]
        if not active_tasks:
            await query.message.reply_text("❌ এই ক্যাটাগরিতে কোনো কাজ নেই।"); return
        buttons = [[ib(f"🗑️ {t['name']} ({t['price']}৳)", f"adm_do_del:{t['id']}", "danger")] for t in active_tasks]
        await query.message.reply_text("👇 কোনটি ডিলিট করবেন?", reply_markup=InlineKeyboardMarkup(buttons))
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_do_del:"):
        task_id  = data.split(":")[1]
        all_tasks= fb_get("/dynamic_tasks") or {}
        if task_id in all_tasks:
            removed = all_tasks[task_id]
            _delete_task(task_id)
            await query.message.reply_text(f"✅ টাস্ক ডিলিট হয়েছে!\n🗑️ {removed['name']}")
        else:
            await query.message.reply_text("❌ টাস্ক পাওয়া যায়নি।")
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_t_type:"):
        t_type = data.split(":")[1]
        state  = USER_STATE.get(user_id)
        if state and "category" in state and "task_name" in state:
            t_id     = str(uuid.uuid4())[:8]
            new_task = {"id": t_id, "category": state["category"], "name": state["task_name"],
                        "price": state.get("task_price",0.0), "rules": state.get("task_rules",""), "type": t_type}
            _save_task(t_id, new_task)
            USER_STATE.pop(user_id, None)
            await query.message.reply_text(f"✅ নতুন টাস্ক সেভ হয়েছে Firebase-এ!\n\n📌 নাম: {new_task['name']}\n💵 পেমেন্ট: {new_task['price']} ৳\n🎯 টাইপ: {new_task['type'].upper()}")
            try: await query.delete_message()
            except: pass
        return

    if data.startswith("lang_"):
        new_lang = "bn" if data=="lang_bn" else "en"
        fb_update(f"/users/{str(user_id)}", {"language": new_lang})
        await query.message.reply_text(LANGUAGES[new_lang]["lang_changed"], reply_markup=main_menu_keyboard(user_id, new_lang))
        try: await query.delete_message()
        except: pass
        return

    if data == "start_withdraw":
        if user_profile["balance"] < 50:
            await query.answer(ln["withdraw_min_err"], show_alert=True); return
        USER_STATE[user_id] = {"step":"withdraw_method"}
        kb_ = InlineKeyboardMarkup([[ib("bKash","w_meth:bKash","success"), ib("Nagad","w_meth:Nagad","success")]])
        await query.edit_message_text(ln["select_meth"], reply_markup=kb_)
        return

    if data.startswith("w_meth:"):
        method = data.split(":")[1]
        USER_STATE[user_id]["method"] = method
        USER_STATE[user_id]["step"]   = "withdraw_num"
        bc = KeyboardButton(LANGUAGES[lang]["btn_cancel"]); object.__setattr__(bc,'style','danger')
        await context.bot.send_message(chat_id=user_id, text=LANGUAGES[lang]["send_num"].format(method=method), reply_markup=ReplyKeyboardMarkup([[bc]], resize_keyboard=True))
        try: await query.delete_message()
        except: pass
        return

    if user_id != ADMIN_ID:
        return

    if data == "adm_confirm_delete_all_saved_usernames":
        _save_usernames([])
        await query.message.reply_text("💥 সব সেভ করা ইউজারনেম ডিলিট হয়েছে!", reply_markup=main_menu_keyboard(user_id, lang))
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("h_"):
        key_map    = {"h_ig_m":"instagram_task","h_fb_m":"facebook_task"}
        target_key = key_map.get(data)
        if target_key:
            v = fb_get("/visibility") or {"instagram_task":True,"facebook_task":True}
            v[target_key] = not v.get(target_key,True)
            _save_visibility(v)
            kb_ = InlineKeyboardMarkup([[
                ib(f"IG Master [{'ON' if v.get('instagram_task',True) else 'OFF'}]","h_ig_m","primary"),
                ib(f"FB Master [{'ON' if v.get('facebook_task',True) else 'OFF'}]","h_fb_m","primary")
            ]])
            await query.edit_message_text("👁️ Category Visibility toggled:", reply_markup=kb_)
        return

    if data.startswith("w_app:") or data.startswith("w_rej:"):
        w_id       = data.split(":")[1]
        is_approve = data.startswith("w_app:")
        w_rec      = fb_get(f"/withdrawals/{w_id}")
        if w_rec and w_rec.get("status")=="pending":
            if is_approve:
                fb_update(f"/withdrawals/{w_id}", {"status":"approved"})
                uid_str = str(w_rec["user_id"])
                u_data  = fb_get(f"/users/{uid_str}") or {}
                new_bal = round(u_data.get("balance",0) - w_rec["amount"], 2)
                fb_update(f"/users/{uid_str}", {"balance": new_bal})
                msg   = f"✅ Approved ৳{w_rec['amount']}"
                u_msg = "✅ Your withdrawal request has been approved."
            else:
                fb_update(f"/withdrawals/{w_id}", {"status":"rejected"})
                msg   = "❌ Rejected"
                u_msg = "❌ Your withdrawal request has been rejected."
            await query.edit_message_text(msg)
            try: await context.bot.send_message(chat_id=w_rec["user_id"], text=u_msg)
            except: pass
        return

    if data.startswith("rep_app:") or data.startswith("rep_rej:"):
        sub_id     = data.split(":")[1]
        is_approve = data.startswith("rep_app:")
        s_rec      = fb_get(f"/submissions/{sub_id}")
        if s_rec and s_rec.get("status")=="pending":
            uid_str = str(s_rec["user_id"])
            u_data  = fb_get(f"/users/{uid_str}") or {}
            if is_approve:
                fb_update(f"/submissions/{sub_id}", {"status":"approved"})
                all_tasks = fb_get("/dynamic_tasks") or {}
                t_info    = all_tasks.get(s_rec.get("task_id",""), {})
                p_add     = t_info.get("price", 3.5)
                fb_update(f"/users/{uid_str}", {
                    "balance":        round(u_data.get("balance",0)+p_add, 2),
                    "success_count":  u_data.get("success_count",0)+1,
                    "review_count":   max(0, u_data.get("review_count",0)-1),
                })
                msg   = "✅ Approved submission."
                u_msg = f"✅ Report approved, +৳{p_add}"
            else:
                fb_update(f"/submissions/{sub_id}", {"status":"rejected"})
                fb_update(f"/users/{uid_str}", {
                    "rejected_count": u_data.get("rejected_count",0)+1,
                    "review_count":   max(0, u_data.get("review_count",0)-1),
                })
                msg   = "❌ Rejected submission."
                u_msg = "❌ Your Report Has Been Rejected 🥹"
            await query.edit_message_text(msg)
            try: await context.bot.send_message(chat_id=s_rec["user_id"], text=u_msg)
            except: pass
        return

# ============================================================
# ERROR HANDLER
# ============================================================
async def error_handler(update, context):
    logger.error(f"Exception: {context.error}", exc_info=context.error)

# ============================================================
# MAIN
# ============================================================
def main():
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    app.add_error_handler(error_handler)
    logger.info("Bot started with Firebase backend.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
