import os
import json
import threading
import datetime
import uuid
import random
import pyotp
import logging
from flask import Flask
from threading import Thread

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== FLASK KEEP-ALIVE (Render) =====================
_flask_app = Flask(__name__)

@_flask_app.route('/')
def _home():
    return "Bot is Running!"

def _run_flask():
    port = int(os.environ.get("PORT", 8080))
    _flask_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=_run_flask, daemon=True)
    t.start()

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = "8738544813:AAHMBZucZMhEJyA88e-qI43RjzBYyL5_j_c"
ADMIN_ID = int(os.getenv("ADMIN_ID", "6470499890"))

DATA_FILE = "bot_data_v3.json"
_lock = threading.Lock()

# ============================================================
# MULTI-LANGUAGE DICTIONARY
# ============================================================
LANGUAGES = {
    "en": {
        "welcome": "🌟 Welcome {name}! Choose an option:",
        "btn_balance": "💳 BALANCE",
        "btn_tasks": "📋 TASKS",
        "btn_withdraw": "📤 WITHDRAW",
        "btn_report": "📊 YOUR REPORT",
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
        "report_received": "✅ Your report has been received!\n⏳ Please wait 16–24 hours."
    },
    "bn": {
        "welcome": "🌟 স্বাগতম {name}! নিচের যেকোনো একটি অপশন বেছে নিন:",
        "btn_balance": "💳 ব্যালেন্স",
        "btn_tasks": "📋 কাজ (TASKS)",
        "btn_withdraw": "📤 টাকা তুলুন",
        "btn_report": "📊 আপনার রিপোর্ট",
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
        "withdraw_min_err": "❌ অপর্যাপ্ত ব্যালেন্স: সর্বনিম্ন ৫০ ৳ প্রয়োজন",
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
        "btn_subbed": "✅ হ্যাঁ | আমি সাবস্ক্রাইব করেছি",
        "thanks_msg": "✅ ধন্যবাদ! অনুগ্রহ করে আনফলো করবেন না। নিয়ম মেনে চলুন।",
        "report_received": "✅ আপনার রিপোর্টটি গ্রহণ করা হয়েছে!\n⏳ অনুগ্রহ করে ১৬–২৪ ঘণ্টা অপেক্ষা করুন।"
    }
}

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def _default_data():
    return {
        "users": {},
        "submissions": {},
        "withdrawals": {},
        "dynamic_tasks": {},
        "saved_usernames": [],
        "visibility": {"instagram_task": True, "facebook_task": True}
    }

def _load():
    if not os.path.exists(DATA_FILE):
        return _default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if "saved_usernames" not in d:
                d["saved_usernames"] = []
            if "dynamic_tasks" not in d:
                d["dynamic_tasks"] = {}
            return d
    except:
        return _default_data()

def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_or_create_user(user_id: int, username: str = ""):
    with _lock:
        data = _load()
        uid = str(user_id)
        if uid not in data["users"]:
            data["users"][uid] = {
                "user_id": user_id,
                "username": username,
                "balance": 0.0,
                "language": "en",
                "success_count": 0,
                "review_count": 0,
                "rejected_count": 0
            }
            _save(data)
        return data["users"][uid]

def generate_profile_or_get_saved():
    with _lock:
        data = _load()
        if data.get("saved_usernames"):
            login_name = data["saved_usernames"].pop(0)
            _save(data)
            first_names = ["fatima", "wafaa", "ahmed", "youssef", "omar", "nour", "ali"]
            last_names = ["Zayan", "Emad", "Khan", "Ahmed", "Ali", "Hassan"]
            f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            return f_name, login_name
            
    first_names = ["wafaa", "ahmed", "youssef", "fatima", "omar", "nour", "ali"]
    last_names = ["Emad", "Khan", "Ahmed", "Ali", "Zayan", "Hassan"]
    f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    username_chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    user_gen = "".join(random.choice(username_chars) for _ in range(5))
    return f_name, f"wa0fay__{user_gen}"

# ============================================================
# KEYBOARDS
# ============================================================

def _kb(text, style="primary"):
    btn = KeyboardButton(text)
    btn.__dict__["style"] = style
    return btn

def _ibtn(text, callback_data, style="primary"):
    btn = InlineKeyboardButton(text, callback_data=callback_data)
    btn.__dict__["style"] = style
    return btn

def main_menu_keyboard(user_id: int, lang: str):
    ln = LANGUAGES[lang]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.keyboard = [
        [_kb(ln["btn_balance"], "primary"),  _kb(ln["btn_tasks"], "primary")],
        [_kb(ln["btn_withdraw"], "success"), _kb(ln["btn_report"], "primary")],
        [_kb(ln["btn_language"], "primary")],
    ]
    if user_id == ADMIN_ID:
        kb.keyboard.append([_kb(ln["btn_admin"], "danger")])
    return kb

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
    lang = u_data.get("language", "en")
    await update.message.reply_text(
        LANGUAGES[lang]["welcome"].format(name=user.first_name),
        reply_markup=main_menu_keyboard(user.id, lang)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, update.effective_user.username or "")
    lang = user_profile.get("language", "en")
    ln = LANGUAGES[lang]
    
    if text == "❓ How to get 2fa?":
        await update.message.reply_text("📹 How to setup 2FA Video Link:\n\nhttps://t.me/range_channele/955")
        return

    # --------------------------------------------------------
    # ADMIN FLOWS
    # --------------------------------------------------------
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
        kb = InlineKeyboardMarkup([
            [_ibtn("🍪 Cookies Work", "adm_t_type:cookies", "success")],
            [_ibtn("🛡️ 2FA Work", "adm_t_type:2fa", "primary")]
        ])
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
        await update.message.reply_text("💵 Enter Amount to Add:")
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
            kb = ReplyKeyboardMarkup([[ln["btn_confirm"], ln["btn_cancel"]]], resize_keyboard=True)
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
            
            admin_kb = InlineKeyboardMarkup([
                [_ibtn("✅ APPROVE", f"w_app:{w_id}", "success"),
                 _ibtn("❌ REJECT", f"w_rej:{w_id}", "danger")]
            ])
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
        kb = ReplyKeyboardMarkup([[_kb(ln["btn_acc_reg"], "success")], [_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True)
        await update.message.reply_text(ln["cookies_rec"], reply_markup=kb)
        return

    if text == ln["btn_acc_reg"]:
        state = USER_STATE.get(user_id)
        if state and (state.get("step") == "cookies_submitted" or state.get("step") == "2fa_verify"):
            kb = ReplyKeyboardMarkup([[_kb(ln["btn_subbed"], "success")], [_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True)
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
                    "task_type": "cookies", "task_id": data["task_id"], "login": state['login'], "pass": state['pass'], "status": "pending"
                }
                data["users"][str(user_id)]["review_count"] += 1
                _save(data)
            with open(file_path, "rb") as f:
                await context.bot.send_document(chat_id=ADMIN_ID, document=f, caption=f"🍪 Dynamic Cookies Task Submission\nUser: @{user_profile['username']}\nUID: {user_id}\nSub ID: {sub_id}")
            os.remove(file_path)
            await update.message.reply_text(ln["thanks_msg"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

    # --- 2FA SECRET KEY SUBMISSION (CUSTOM FORMATTED BOX WITH REFRESH BUTTON ONLY) ---
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
        
        reg_kb = ReplyKeyboardMarkup([[_kb(ln["btn_acc_reg"], "success")], [_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True)
        await update.message.reply_text("👉 2FA Key Received. Now verify and submit using the panel below.", reply_markup=reg_kb)

        inline_kb = InlineKeyboardMarkup([
            [_ibtn("🔄 Refresh", "refresh_2fa_code", "primary")]
        ])
        
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

    if text in ["🌐 LANGUAGE", "🌐 ভাষা (LANGUAGE)"]:
        kb = InlineKeyboardMarkup([
            [_ibtn("🇧🇩 বাংলা", "lang_bn", "primary"), _ibtn("🇬🇧 English", "lang_en", "primary")]
        ])
        await update.message.reply_text(ln["select_lang"], reply_markup=kb)
        return

    if text in ["📋 TASKS", "📋 কাজ (TASKS)"]:
        task_list = []
        if db_data["visibility"].get("instagram_task", True) or user_id == ADMIN_ID:
            task_list.append([_kb("🎯 Instagram Task" if lang == "en" else "🎯 ইনস্টাগ্রাম কাজ", "primary")])
        if db_data["visibility"].get("facebook_task", True) or user_id == ADMIN_ID:
            task_list.append([_kb("🎯 Facebook Task" if lang == "en" else "🎯 ফেসবুক কাজ", "primary")])
        task_list.append([_kb(ln["btn_back"], "danger")])
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
            sub_tasks.append([_kb(f"📌 {t['name']} ({t['price']} ৳)", "primary")])
        sub_tasks.append([_kb(ln["btn_cancel"], "danger")])
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
            kb = ReplyKeyboardMarkup([[_kb(ln["btn_start"], "success")], [_kb(ln["btn_video"], "primary")], [_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True)
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
                pass_val = "shuvo9"
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
                    task_2fa_kb = ReplyKeyboardMarkup([[_kb(ln["btn_how_to_2fa"], "primary")], [_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True)
                    await update.message.reply_text(ln["send_2fa_secret"], reply_markup=task_2fa_kb)
                else:
                    state["step"] = "waiting_for_cookies"
                    await update.message.reply_text(ln["send_cookies"], reply_markup=ReplyKeyboardMarkup([[_kb(ln["btn_cancel"], "danger")]], resize_keyboard=True))
            return

    if text in ["📤 WITHDRAW", "📤 টাকা তুলুন"]:
        bal = user_profile["balance"]
        if bal < 50:
            await update.message.reply_text(ln["withdraw_min_err"])
            return
        inline_wb = InlineKeyboardMarkup([[_ibtn("Withdraw", "start_withdraw", "success")]])
        await update.message.reply_text(ln["withdraw_dash"].format(bal=bal, rec=max(0.0, bal - 5.0)), reply_markup=inline_wb)
        return

    # --- ADMIN CONTROL DASHBOARD PANEL ---
    if text in ["🛠️ ADMIN PANEL", "🛠️ এডমিন প্যানেল"] and user_id == ADMIN_ID:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.keyboard = [
            [_kb("➕ Add Task", "success"), _kb("❌ Delete Task", "danger")],
            [_kb("👁️ Task Hide/Show", "primary"), _kb("👤 User Broadcast", "primary")],
            [_kb("➕ Add Money", "success"), _kb("📥 Username Save", "primary")],
            [_kb("🗂️ All Report", "primary"), _kb(ln["btn_back"], "danger")],
        ]
        await update.message.reply_text("🛠️ Admin Control Dashboard", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "❌ Delete Task":
        kb = InlineKeyboardMarkup([
            [_ibtn("Instagram Tasks", "adm_del_cat:instagram", "danger"),
             _ibtn("Facebook Tasks", "adm_del_cat:facebook", "danger")]
        ])
        await update.message.reply_text("🗑️ কোন ক্যাটাগরির কাজ ডিলিট করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "📥 Username Save":
        USER_STATE[user_id] = {"step": "admin_save_username"}
        await update.message.reply_text("📥 আপনি যে ইউজারনেমগুলো সেভ করে রাখতে চান সেগুলো পাঠান:\n(একাধিক ইউজারনেম স্পেস বা কমা দিয়ে একসাথে পাঠাতে পারেন)")
        return

    if user_id == ADMIN_ID and text == "➕ Add Task":
        kb = InlineKeyboardMarkup([
            [_ibtn("Instagram", "adm_cat:instagram", "primary"),
             _ibtn("Facebook", "adm_cat:facebook", "primary")]
        ])
        await update.message.reply_text("📁 কোন ক্যাটাগরিতে কাজ যুক্ত করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "👁️ Task Hide/Show":
        v = db_data["visibility"]
        kb = InlineKeyboardMarkup([
            [_ibtn(f"IG Cat [{'ON' if v.get('instagram_task',True) else 'OFF'}]", "h_ig_m", "primary"), 
             _ibtn(f"FB Cat [{'ON' if v.get('facebook_task',True) else 'OFF'}]", "h_fb_m", "primary")]
        ])
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

    if user_id == ADMIN_ID and text == "🗂️ All Report":
        pending_subs = [s for s in db_data["submissions"].values() if s["status"] == "pending"]
        if not pending_subs:
            await update.message.reply_text("✅ No pending item reports.")
            return
        for s in pending_subs:
            inline_ap = InlineKeyboardMarkup([
                [_ibtn("Approve", f"rep_app:{s['sub_id']}", "success"),
                 _ibtn("Reject", f"rep_rej:{s['sub_id']}", "danger")]
            ])
            await update.message.reply_text(f"User ID: {s['user_id']}\nType: {s['task_type']}\nLogin: {s['login']}\nStatus: Pending", reply_markup=inline_ap)
        return

    if text in [ln["btn_cancel"], ln["btn_back"], "cancel", "❌ cancel", "🔙 BACK"]:
        USER_STATE.pop(user_id, None)
        await update.message.reply_text("🔙 Menu", reply_markup=main_menu_keyboard(user_id, lang))

# ============================================================
# CALLBACK QUERY PROCESSING
# ============================================================

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, query.from_user.username or "")
    lang = user_profile.get("language", "en")

    if data == "refresh_2fa_code":
        state = USER_STATE.get(user_id)
        if state and state.get("step") == "2fa_verify" and "secret" in state:
            try:
                totp = pyotp.TOTP(state["secret"])
                current_code = totp.now()
                remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
                
                inline_kb = InlineKeyboardMarkup([
                    [_ibtn("🔄 Refresh", "refresh_2fa_code", "primary")]
                ])
                
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

    # --- DELETE TASK SELECTION OPTIONS ---
    if data.startswith("adm_del_cat:"):
        cat = data.split(":")[1]
        active_tasks = [t for t in db_data.get("dynamic_tasks", {}).values() if t.get("category") == cat]
        if not active_tasks:
            await query.message.reply_text("❌ এই ক্যাটাগরিতে ডিলিট করার মতো কোনো একটিভ কাজ পাওয়া যায়নি।")
            return
            
        buttons = []
        for t in active_tasks:
            buttons.append([_ibtn(f"🗑️ {t['name']} ({t['price']}৳)", f"adm_do_del:{t['id']}", "danger")])
            
        await query.message.reply_text("👇 নিচে থেকে যে টাস্কটি ডিলিট করতে চান সেটির উপর চাপুন:", reply_markup=InlineKeyboardMarkup(buttons))
        try: await query.delete_message()
        except: pass
        return

    # --- ACTION EXECUTE DELETE TASK ---
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
            await query.answer(LANGUAGES[lang]["withdraw_min_err"], show_alert=True)
            return
        USER_STATE[user_id] = {"step": "withdraw_method"}
        kb = InlineKeyboardMarkup([
            [_ibtn("bKash", "w_meth:bKash", "success"), _ibtn("Nagad", "w_meth:Nagad", "success")]
        ])
        await query.edit_message_text(LANGUAGES[lang]["select_meth"], reply_markup=kb)
        return

    if data.startswith("w_meth:"):
        method = data.split(":")[1]
        USER_STATE[user_id]["method"] = method
        USER_STATE[user_id]["step"] = "withdraw_num"
        await context.bot.send_message(chat_id=user_id, text=LANGUAGES[lang]["send_num"].format(method=method), reply_markup=ReplyKeyboardMarkup([[LANGUAGES[lang]["btn_cancel"]]], resize_keyboard=True))
        try: await query.delete_message()
        except: pass
        return

    if user_id != ADMIN_ID:
        return

    if data.startswith("h_"):
        key_map = {"h_ig_m": "instagram_task", "h_fb_m": "facebook_task"}
        target_key = key_map[data]
        with _lock:
            d = _load()
            d["visibility"][target_key] = not d["visibility"].get(target_key, True)
            _save(d)
        v = d["visibility"]
        kb = InlineKeyboardMarkup([
            [_ibtn(f"IG Master [{'ON' if v.get('instagram_task',True) else 'OFF'}]", "h_ig_m", "primary"), 
             _ibtn(f"FB Master [{'ON' if v.get('facebook_task',True) else 'OFF'}]", "h_fb_m", "primary")]
        ])
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
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    logger.info("Bot structure deployed with Fixed Dynamic Tasks module.")
    app.run_polling()

if __name__ == "__main__":
    main()
