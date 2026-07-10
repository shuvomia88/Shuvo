import os
import json
import threading
import datetime
import uuid
import random
import pyotp
import logging

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = "8738544813:AAHMBZucZMhEJyA88e-qI43RjzBYyL5_j_c"
ADMIN_ID = int(os.getenv("ADMIN_ID", "6470499890"))

DATA_FILE = "bot_data_dynamic.json"
_lock = threading.Lock()

# ============================================================
# DATABASE
# ============================================================

def _default_data():
    return {
        "users": {},
        "tasks": {},
        "submissions": {},
        "withdrawals": {},
        "passwords": {"ig_2fa": "shuvo9", "ig_cookies": "shuvo9"}
    }

def _load():
    if not os.path.exists(DATA_FILE):
        return _default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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

def generate_random_profile():
    first_names = ["wafaa", "ahmed", "youssef", "fatima", "omar", "nour", "ali"]
    last_names = ["Emad", "Khan", "Ahmed", "Ali", "Zayan", "Hassan"]
    f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    username = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))[:12]
    return f_name, username

# ============================================================
# KEYBOARDS
# ============================================================

def main_menu_keyboard(user_id: int):
    buttons = [
        ["💳 BALANCE", "📋 TASKS"],
        ["📤 WITHDRAW", "📊 YOUR REPORT"],
        ["🌐 LANGUAGE"],
    ]
    if user_id == ADMIN_ID:
        buttons.append(["🛠️ ADMIN PANEL"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

USER_STATE = {}

# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username or "")
    await update.message.reply_text(
        f"🌟 Welcome {user.first_name}! Choose an option:",
        reply_markup=main_menu_keyboard(user.id)
    )

# ============================================================
# MESSAGE HANDLER
# ============================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text.strip()
        user_profile = get_or_create_user(user_id, update.effective_user.username or "")
        db_data = _load()
        
        # --- MAIN MENU BUTTONS ---
        if text == "💳 BALANCE":
            await update.message.reply_text(f"💳 Your Balance: {user_profile['balance']} ৳", reply_markup=main_menu_keyboard(user_id))
            return
        
        if text == "📋 TASKS":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 INSTAGRAM TASK", callback_data="cat_instagram", style="primary")],
                [InlineKeyboardButton("🎯 FACEBOOK TASK", callback_data="cat_facebook", style="primary")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main_kb", style="primary")]
            ])
            await update.message.reply_text("📱 Select task category:", reply_markup=kb)
            return
        
        if text == "📤 WITHDRAW":
            bal = user_profile["balance"]
            msg = f"💳 Your Balance Dashboard\n\n💰 Balance: {bal} ৳\n💸 Minimum Withdraw: 50 ৳\n💳 Withdrawal Charge: 5 ৳\n✅ You Will Receive: {max(0, bal-5)} ৳"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 WITHDRAW", callback_data="start_withdraw", style="success"), InlineKeyboardButton("🔙 BACK", callback_data="back_main_kb", style="primary")]
            ])
            await update.message.reply_text(msg, reply_markup=kb)
            return
        
        if text == "📊 YOUR REPORT":
            s = user_profile.get('success_count', 0)
            r = user_profile.get('review_count', 0)
            rej = user_profile.get('rejected_count', 0)
            msg_text = f"📊 All Account Report\n\n✅ Success: [{s}]\n⏳ Reviewing: [{r}]\n❌ Rejected: [{rej}]"
            await update.message.reply_text(msg_text, reply_markup=main_menu_keyboard(user_id))
            return
        
        if text == "🌐 LANGUAGE":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🇬🇧 ENGLISH", callback_data="lang_en", style="primary"), InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn", style="primary")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_main_kb", style="primary")]
            ])
            await update.message.reply_text("🌐 Select Language:", reply_markup=kb)
            return
        
        if text == "🛠️ ADMIN PANEL":
            if user_id != ADMIN_ID:
                await update.message.reply_text("❌ Admin only!", reply_markup=main_menu_keyboard(user_id))
                return
            
            kb = ReplyKeyboardMarkup([
                ["➕ ADD TASK", "📊 PENDING"],
                ["👁️ HIDE/SHOW", "💰 PRICE"],
                ["🔑 PASSWORD", "📢 BROADCAST"],
                ["💸 ADD MONEY", "📋 ALL REPORTS"],
                ["🔙 BACK"]
            ], resize_keyboard=True)
            await update.message.reply_text("🛠️ ADMIN PANEL", reply_markup=kb)
            return
        
        # --- ADMIN ADD TASK ---
        if text == "➕ ADD TASK":
            if user_id != ADMIN_ID:
                return
            kb = ReplyKeyboardMarkup([
                ["🎯 Instagram"],
                ["🎯 Facebook"],
                ["🔙 BACK"]
            ], resize_keyboard=True)
            USER_STATE[user_id] = {"step": "add_task_category"}
            await update.message.reply_text("🎯 Select Category:", reply_markup=kb)
            return
        
        if text == "🎯 Instagram" and USER_STATE.get(user_id, {}).get("step") == "add_task_category":
            USER_STATE[user_id]["category"] = "instagram"
            USER_STATE[user_id]["step"] = "add_task_name"
            await update.message.reply_text("📝 Task Name (ex: Instagram Growth Task):")
            return
        
        if text == "🎯 Facebook" and USER_STATE.get(user_id, {}).get("step") == "add_task_category":
            USER_STATE[user_id]["category"] = "facebook"
            USER_STATE[user_id]["step"] = "add_task_name"
            await update.message.reply_text("📝 Task Name (ex: Facebook Engagement Task):")
            return
        
        if USER_STATE.get(user_id, {}).get("step") == "add_task_name":
            USER_STATE[user_id]["name"] = text
            USER_STATE[user_id]["step"] = "add_task_price"
            await update.message.reply_text("💰 Task Price (ex: 3.5):")
            return
        
        if USER_STATE.get(user_id, {}).get("step") == "add_task_price":
            try:
                price = float(text)
                USER_STATE[user_id]["price"] = price
                USER_STATE[user_id]["step"] = "add_task_rules"
                await update.message.reply_text("📋 Task Rules (ex: Min 10 followers, profile photo required):")
            except:
                await update.message.reply_text("❌ Invalid price! Send number:")
            return
        
        if USER_STATE.get(user_id, {}).get("step") == "add_task_rules":
            USER_STATE[user_id]["rules"] = text
            USER_STATE[user_id]["step"] = "add_task_type"
            kb = ReplyKeyboardMarkup([
                ["🔐 2FA"],
                ["🍪 COOKIES"],
                ["🔙 BACK"]
            ], resize_keyboard=True)
            await update.message.reply_text("📌 Task Type:", reply_markup=kb)
            return
        
        if text == "🔐 2FA" and USER_STATE.get(user_id, {}).get("step") == "add_task_type":
            state = USER_STATE[user_id]
            task_id = str(uuid.uuid4())[:8]
            
            with _lock:
                data = _load()
                data["tasks"][task_id] = {
                    "task_id": task_id,
                    "category": state["category"],
                    "name": state["name"],
                    "price": state["price"],
                    "rules": state["rules"],
                    "type": "2fa",
                    "status": "active",
                    "created_at": datetime.datetime.now().isoformat()
                }
                _save(data)
            
            await update.message.reply_text(f"✅ Task Created!\n\n📝 {state['name']}\n💰 {state['price']} ৳\n📌 Type: 2FA", reply_markup=ReplyKeyboardMarkup([["🔙 BACK"]], resize_keyboard=True))
            USER_STATE.pop(user_id, None)
            return
        
        if text == "🍪 COOKIES" and USER_STATE.get(user_id, {}).get("step") == "add_task_type":
            state = USER_STATE[user_id]
            task_id = str(uuid.uuid4())[:8]
            
            with _lock:
                data = _load()
                data["tasks"][task_id] = {
                    "task_id": task_id,
                    "category": state["category"],
                    "name": state["name"],
                    "price": state["price"],
                    "rules": state["rules"],
                    "type": "cookies",
                    "status": "active",
                    "created_at": datetime.datetime.now().isoformat()
                }
                _save(data)
            
            await update.message.reply_text(f"✅ Task Created!\n\n📝 {state['name']}\n💰 {state['price']} ৳\n📌 Type: Cookies", reply_markup=ReplyKeyboardMarkup([["🔙 BACK"]], resize_keyboard=True))
            USER_STATE.pop(user_id, None)
            return
        
        if text == "📊 PENDING":
            if user_id != ADMIN_ID:
                return
            d = _load()
            subs = [s for s in d["submissions"].values() if s["status"] == "pending"]
            if not subs:
                await update.message.reply_text("✅ No pending submissions", reply_markup=ReplyKeyboardMarkup([["🔙 BACK"]], resize_keyboard=True))
                return
            for s in subs[:5]:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ APPROVE", callback_data=f"rep_app:{s['sub_id']}", style="success"), InlineKeyboardButton("❌ REJECT", callback_data=f"rep_rej:{s['sub_id']}", style="danger")]
                ])
                msg = f"📋 Task: {s.get('task_name', 'Unknown')}\n👤 User ID: {s['user_id']}\n📱 Login: {s['login']}\n🔑 Password: {s['pass']}"
                await update.message.reply_text(msg, reply_markup=kb)
            return
        
        if text == "🔙 BACK":
            kb = main_menu_keyboard(user_id)
            await update.message.reply_text("🔙 Back to Main Menu", reply_markup=kb)
            USER_STATE.pop(user_id, None)
            return
        
        # --- 2FA INPUT ---
        if USER_STATE.get(user_id, {}).get("step") == "waiting_for_2fa":
            if text.upper() == "❌ CANCEL":
                USER_STATE.pop(user_id, None)
                await update.message.reply_text("❌ Cancelled", reply_markup=main_menu_keyboard(user_id))
                return
            
            state = USER_STATE[user_id]
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            current_code = totp.now()
            
            state["secret"] = secret
            state["2fa_input"] = text
            state["step"] = "2fa_verify"
            
            remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
            
            inline_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔑 Code: {current_code}", callback_data="show_2fa_code", style="primary")],
                [InlineKeyboardButton("🔄 REFRESH", callback_data="refresh_2fa_code", style="primary")],
                [InlineKeyboardButton("✅ ACCOUNT REGISTERED", callback_data="submit_2fa_verify", style="success")]
            ])
            
            msg_text = f"🔑 Your 2FA Code\n\n⏱️ Valid: {remaining}s"
            msg = await update.message.reply_text(msg_text, reply_markup=inline_kb)
            state["code_msg_id"] = msg.message_id
            return
        
        # --- COOKIES INPUT ---
        if USER_STATE.get(user_id, {}).get("step") == "waiting_for_cookies":
            if text.upper() == "❌ CANCEL":
                USER_STATE.pop(user_id, None)
                await update.message.reply_text("❌ Cancelled", reply_markup=main_menu_keyboard(user_id))
                return
            
            USER_STATE[user_id]["cookies_data"] = text
            USER_STATE[user_id]["step"] = "cookies_submitted"
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ ACCOUNT REGISTERED", callback_data="cookies_reg", style="success")],
                [InlineKeyboardButton("❌ CANCEL", callback_data="cancel_cookies", style="danger")]
            ])
            await update.message.reply_text("👉 Cookies Received. Click below to proceed.", reply_markup=kb)
            return
        
        # --- 2FA SUBMISSION ---
        if text == "✅ ACCOUNT REGISTERED (2FA)":
            state = USER_STATE.get(user_id)
            if state and state.get("step") == "2fa_submitted":
                sub_id = str(uuid.uuid4())[:8]
                file_content = f"Instagram 2FA Task Report\n{'='*40}\nUsername: {state['login']}\nPassword: {state['pass']}\n2FA Secret: {state.get('2fa_code', '')}\nSubmitted: {datetime.datetime.now()}"
                file_path = f"submission_{sub_id}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                    
                with _lock:
                    data = _load()
                    data["submissions"][sub_id] = {
                        "sub_id": sub_id,
                        "user_id": user_id,
                        "username": user_profile["username"],
                        "task_id": state.get("task_id"),
                        "task_name": state.get("task_name"),
                        "task_type": "2fa",
                        "login": state['login'],
                        "pass": state['pass'],
                        "status": "pending"
                    }
                    data["users"][str(user_id)]["review_count"] += 1
                    _save(data)
                    
                with open(file_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=ADMIN_ID,
                        document=f,
                        caption=f"📝 New 2FA Task\nUser: @{user_profile['username']}\nUID: {user_id}"
                    )
                os.remove(file_path)
                
                await update.message.reply_text("✅ Your report has been received!\n⏳ Please wait 16–24 hours.", reply_markup=main_menu_keyboard(user_id))
                USER_STATE.pop(user_id, None)
                return
    
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("❌ Error occurred. Please try again.", reply_markup=main_menu_keyboard(user_id))

# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data
        
        user_profile = get_or_create_user(user_id, query.from_user.username or "")
        db_data = _load()

        # --- CATEGORY SELECTION ---
        if data == "cat_instagram":
            tasks = [t for t in db_data["tasks"].values() if t["category"] == "instagram" and t["status"] == "active"]
            if not tasks:
                await query.answer("❌ No tasks available", show_alert=True)
                return
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🎯 {t['name']} ({t['price']} ৳)", callback_data=f"select_task:{t['task_id']}", style="primary")] for t in tasks
            ] + [[InlineKeyboardButton("🔙 BACK", callback_data="back_main_kb", style="primary")]])
            
            await query.edit_message_text("🎯 Select Instagram Task:", reply_markup=kb)
            return
        
        if data == "cat_facebook":
            tasks = [t for t in db_data["tasks"].values() if t["category"] == "facebook" and t["status"] == "active"]
            if not tasks:
                await query.answer("❌ No tasks available", show_alert=True)
                return
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🎯 {t['name']} ({t['price']} ৳)", callback_data=f"select_task:{t['task_id']}", style="primary")] for t in tasks
            ] + [[InlineKeyboardButton("🔙 BACK", callback_data="back_main_kb", style="primary")]])
            
            await query.edit_message_text("🎯 Select Facebook Task:", reply_markup=kb)
            return
        
        if data.startswith("select_task:"):
            task_id = data.split(":")[1]
            task = db_data["tasks"].get(task_id)
            
            if not task:
                await query.answer("❌ Task not found", show_alert=True)
                return
            
            USER_STATE[user_id] = {"task_id": task_id, "task_name": task["name"]}
            
            msg_text = f"🛡️ 🌟 {task['name']}\n\n💵 Payment: ৳{task['price']}\n\n📝 Rules:\n{task['rules']}\n\n🚀 Tap START below to begin."
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ START", callback_data="task_start", style="success")],
                [InlineKeyboardButton("❌ CANCEL", callback_data="back_main_kb", style="danger")]
            ])
            
            await query.edit_message_text(msg_text, reply_markup=kb)
            return
        
        if data == "task_start":
            state = USER_STATE.get(user_id)
            task_id = state.get("task_id")
            task = db_data["tasks"].get(task_id)
            
            if not task:
                return
            
            f_name, login_name = generate_random_profile()
            pass_val = db_data["passwords"].get("ig_2fa" if task["type"] == "2fa" else "ig_cookies", "shuvo9")
            
            state["login"] = login_name
            state["pass"] = pass_val
            
            cred_msg = f"First name: {f_name}\nLogin: {login_name}\nPassword: {pass_val}"
            await context.bot.send_message(user_id, cred_msg)
            
            if task["type"] == "2fa":
                state["step"] = "waiting_for_2fa"
                await context.bot.send_message(user_id, "👉 Please Send Your Instagram 2FA Secret Key")
            else:
                state["step"] = "waiting_for_cookies"
                await context.bot.send_message(user_id, "👉 Please Send Your Instagram Cookies")
            
            await query.delete_message()
            return
        
        # --- 2FA CALLBACKS ---
        if data == "show_2fa_code":
            state = USER_STATE.get(user_id)
            if state and state.get("step") == "2fa_verify" and "secret" in state:
                totp = pyotp.TOTP(state["secret"])
                current_code = totp.now()
                remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
                
                inline_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔑 Code: {current_code}", callback_data="show_2fa_code", style="primary")],
                    [InlineKeyboardButton("🔄 REFRESH", callback_data="refresh_2fa_code", style="primary")],
                    [InlineKeyboardButton("✅ ACCOUNT REGISTERED", callback_data="submit_2fa_verify", style="success")]
                ])
                
                msg_text = f"🔑 Your 2FA Code\n\n⏱️ Valid: {remaining}s"
                try:
                    await query.edit_message_text(msg_text, reply_markup=inline_kb)
                except:
                    pass
            return
        
        if data == "refresh_2fa_code":
            state = USER_STATE.get(user_id)
            if state and state.get("step") == "2fa_verify":
                secret = pyotp.random_base32()
                totp = pyotp.TOTP(secret)
                current_code = totp.now()
                
                state["secret"] = secret
                remaining = 30 - (int(datetime.datetime.now().timestamp()) % 30)
                
                inline_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔑 Code: {current_code}", callback_data="show_2fa_code", style="primary")],
                    [InlineKeyboardButton("🔄 REFRESH", callback_data="refresh_2fa_code", style="primary")],
                    [InlineKeyboardButton("✅ ACCOUNT REGISTERED", callback_data="submit_2fa_verify", style="success")]
                ])
                
                msg_text = f"🔑 Your 2FA Code\n\n⏱️ Valid: {remaining}s"
                try:
                    await query.edit_message_text(msg_text, reply_markup=inline_kb)
                except:
                    pass
            await query.answer("✅ Code refreshed!", show_alert=False)
            return
        
        if data == "submit_2fa_verify":
            state = USER_STATE.get(user_id)
            if state and state.get("step") == "2fa_verify":
                state["2fa_code"] = state.get("secret", "")
                state["step"] = "2fa_submitted"
                
                kb_submit = ReplyKeyboardMarkup([["✅ ACCOUNT REGISTERED (2FA)"], ["❌ CANCEL"]], resize_keyboard=True)
                await context.bot.send_message(
                    user_id,
                    "🔐 2FA Verified!\n\nTap 'Account Registered (2FA)' to submit your task.",
                    reply_markup=kb_submit
                )
            await query.delete_message()
            return
        
        # --- BACK ---
        if data == "back_main_kb":
            await context.bot.send_message(user_id, "🏠 Main Menu", reply_markup=main_menu_keyboard(user_id))
            try:
                await query.delete_message()
            except:
                pass
            return
        
        # --- LANGUAGE ---
        if data == "lang_en":
            with _lock:
                d = _load()
                d["users"][str(user_id)]["language"] = "en"
                _save(d)
            await query.answer("✅ Changed to English")
            await context.bot.send_message(user_id, "English Selected ✅", reply_markup=main_menu_keyboard(user_id))
            await query.delete_message()
            return
        
        if data == "lang_bn":
            with _lock:
                d = _load()
                d["users"][str(user_id)]["language"] = "bn"
                _save(d)
            await query.answer("✅ বাংলায় পরিবর্তন করা হয়েছে")
            await context.bot.send_message(user_id, "বাংলা নির্বাচিত ✅", reply_markup=main_menu_keyboard(user_id))
            await query.delete_message()
            return
        
        # --- WITHDRAWAL ---
        if data == "start_withdraw":
            if user_profile["balance"] < 50:
                await query.answer("❌ Minimum 50 ৳ required", show_alert=True)
                return
            USER_STATE[user_id] = {"step": "withdraw_method"}
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 bKash", callback_data="w_meth:bKash", style="primary"), InlineKeyboardButton("📱 Nagad", callback_data="w_meth:Nagad", style="primary")]
            ])
            await query.edit_message_text("💳 Select Your Withdraw Method:", reply_markup=kb)
            return
        
        if data.startswith("w_meth:"):
            method = data.split(":")[1]
            USER_STATE[user_id]["method"] = method
            USER_STATE[user_id]["step"] = "withdraw_num"
            await context.bot.send_message(user_id, f"📱 Please Send Your {method} Number")
            await query.delete_message()
            return
        
        # --- REPORT APPROVAL/REJECTION ---
        if data.startswith("rep_app:"):
            sub_id = data.split(":")[1]
            if user_id != ADMIN_ID:
                return
            with _lock:
                d = _load()
                s = d["submissions"].get(sub_id)
                if s:
                    s["status"] = "approved"
                    task = d["tasks"].get(s["task_id"])
                    price = task.get("price", 3.5) if task else 3.5
                    d["users"][str(s["user_id"])]["balance"] += price
                    d["users"][str(s["user_id"])]["success_count"] += 1
                    d["users"][str(s["user_id"])]["review_count"] -= 1
                    _save(d)
                    await query.edit_message_text(f"✅ Approved +৳{price}")
                    try:
                        await context.bot.send_message(s["user_id"], f"✅ Report approved! +৳{price}")
                    except:
                        pass
            return
        
        if data.startswith("rep_rej:"):
            sub_id = data.split(":")[1]
            if user_id != ADMIN_ID:
                return
            with _lock:
                d = _load()
                s = d["submissions"].get(sub_id)
                if s:
                    s["status"] = "rejected"
                    d["users"][str(s["user_id"])]["rejected_count"] += 1
                    d["users"][str(s["user_id"])]["review_count"] -= 1
                    _save(d)
                    await query.edit_message_text("❌ Rejected")
                    try:
                        await context.bot.send_message(s["user_id"], "❌ Report rejected.")
                    except:
                        pass
            return
        
        # --- COOKIES ---
        if data == "cookies_reg":
            await query.answer("✅ Cookies received", show_alert=False)
            state = USER_STATE.get(user_id)
            if state:
                state["step"] = "cookies_final"
                sub_id = str(uuid.uuid4())[:8]
                file_content = f"Cookies Report\n{'='*40}\nUsername: {state['login']}\nPassword: {state['pass']}\nCookies: [USER PROVIDED]\nSubmitted: {datetime.datetime.now()}"
                file_path = f"submission_{sub_id}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                
                with _lock:
                    d = _load()
                    d["submissions"][sub_id] = {"sub_id": sub_id, "user_id": user_id, "username": user_profile["username"], "task_id": state.get("task_id"), "task_name": state.get("task_name"), "task_type": "cookies", "login": state['login'], "pass": state['pass'], "status": "pending"}
                    d["users"][str(user_id)]["review_count"] += 1
                    _save(d)
                
                with open(file_path, "rb") as f:
                    await context.bot.send_document(ADMIN_ID, f, caption=f"📝 Cookies Task\nUser: {user_id}")
                os.remove(file_path)
                
                await context.bot.send_message(user_id, "✅ Thanks! Please Do Not Unfollow. Follow the Rules.", reply_markup=main_menu_keyboard(user_id))
                USER_STATE.pop(user_id, None)
            await query.delete_message()
            return
        
        if data == "cancel_cookies":
            USER_STATE.pop(user_id, None)
            await context.bot.send_message(user_id, "❌ Cancelled", reply_markup=main_menu_keyboard(user_id))
            await query.delete_message()
            return
    
    except Exception as e:
        logger.error(f"Error in callback_query: {e}")

# ============================================================
# MAIN
# ============================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    logger.info("Dynamic Task Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
