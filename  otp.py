import os
import json
import time
import uuid
import threading
import logging
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import Conflict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ============================================================
# কনফিগারেশন — এই অংশটা তোমার নিজের তথ্য দিয়ে বদলে নাও
# ============================================================
BOT_TOKEN = "8987252167:AAH5DYG8EYqvLAwCwJjBNhbQcLAF3z2ti_M"

REQUIRED_CHANNELS = ["tem_with", "insagramth", "range_channele"]  # ফোর্স-জয়েন চ্যানেল (@ ছাড়া ইউজারনেম)

ADMIN_ID = 6136815573  # তোমার Telegram User ID — নতুন বট যুক্ত/ডিলিট হলে এখানে নোটিফিকেশন যাবে
ADMIN_CONTACT_USERNAME = "your_admin_username"          # 👈 এখানে তোমার নিজের Telegram ইউজারনেম বসাও
ADD_BOT_TUTORIAL_LINK = "https://t.me/range_channele/955"  # 👈 এখানে "কীভাবে বট যুক্ত করবেন" ভিডিও/পোস্টের লিংক বসাও

EMOJI_OPTIONS = ["👍", "❤️", "🔥", "🎉", "😁", "🤩", "🙏", "💯"]

_lock = threading.Lock()

# ============================================================
# বাটনে রঙ (style) বসানোর নিরাপদ হেল্পার
# ============================================================
def _style(btn, style_name: str):
    try:
        object.__setattr__(btn, 'style', style_name)
    except Exception:
        pass

# ============================================================
# ডেটা স্টোরেজ — Firebase Realtime Database
# (আগের টাস্ক বটের একই ডাটাবেসেই, কিন্তু আলাদা নোডে — "reaction_bots"
# path-এ — তাই টাস্ক বটের ডেটার সাথে মিশবে না)
# ============================================================
FIREBASE_BASE_URL = "https://realtime-database-7310e-default-rtdb.firebaseio.com"
FIREBASE_PATH = "reaction_bots"

_DATA_CACHE = None

def _firebase_get():
    try:
        r = requests.get(f"{FIREBASE_BASE_URL}/{FIREBASE_PATH}.json", timeout=10)
        if r.status_code == 200:
            return r.json()
        logger.error(f"Firebase GET failed: HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Firebase GET Error: {e}")
    return None

def _firebase_put(data):
    try:
        r = requests.put(f"{FIREBASE_BASE_URL}/{FIREBASE_PATH}.json", json=data, timeout=10)
        if r.status_code == 200:
            return True
        logger.error(f"Firebase PUT failed: HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Firebase PUT Error: {e}")
    return False

def _load():
    global _DATA_CACHE
    if _DATA_CACHE is not None:
        return _DATA_CACHE
    remote = _firebase_get()
    d = remote if isinstance(remote, dict) else {}
    if "bots" not in d:
        d["bots"] = {}
    _DATA_CACHE = d
    return _DATA_CACHE

def _save(data):
    global _DATA_CACHE
    _DATA_CACHE = data
    ok = _firebase_put(data)
    if not ok:
        logger.error("⚠️ ডেটা Firebase-এ সেভ করা যায়নি! (network/permission সমস্যা হতে পারে)")

USER_STATE = {}

# ============================================================
# চাইল্ড বট রিয়েক্টর — প্রতিটা যুক্ত করা বটের জন্য আলাদা ব্যাকগ্রাউন্ড
# থ্রেডে চলে, চ্যানেল পোস্ট এলেই সেট করা ইমোজি দিয়ে react করে
# ============================================================
ACTIVE_REACTORS = {}  # short_id -> threading.Event (stop signal)

def run_child_bot_reactor(token: str, emoji: str, stop_event: threading.Event):
    offset = None
    api = f"https://api.telegram.org/bot{token}"
    while not stop_event.is_set():
        try:
            resp = requests.get(
                f"{api}/getUpdates",
                params={
                    "timeout": 25,
                    "offset": offset,
                    "allowed_updates": json.dumps(["channel_post"])
                },
                timeout=30
            )
            data = resp.json()
            if not data.get("ok"):
                # টোকেন invalid/revoked হয়ে থাকলে বারবার চেষ্টা করে লাভ নেই
                if data.get("error_code") == 401:
                    logger.error(f"চাইল্ড বট টোকেন অকেজো, রিয়েক্টর বন্ধ হচ্ছে: {token[:10]}...")
                    return
                time.sleep(5)
                continue

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                post = upd.get("channel_post")
                if not post:
                    continue
                chat_id = post["chat"]["id"]
                message_id = post["message_id"]
                try:
                    requests.post(
                        f"{api}/setMessageReaction",
                        json={
                            "chat_id": chat_id,
                            "message_id": message_id,
                            "reaction": [{"type": "emoji", "emoji": emoji}]
                        },
                        timeout=10
                    )
                except Exception as e:
                    logger.error(f"রিয়েকশন সেট করা যায়নি: {e}")
        except Exception as e:
            logger.error(f"চাইল্ড বট পোলিং এরর ({token[:10]}...): {e}")
            time.sleep(5)

def start_child_bot(short_id: str, token: str, emoji: str):
    stop_event = threading.Event()
    t = threading.Thread(target=run_child_bot_reactor, args=(token, emoji, stop_event), daemon=True)
    t.start()
    ACTIVE_REACTORS[short_id] = stop_event

def stop_child_bot(short_id: str):
    ev = ACTIVE_REACTORS.pop(short_id, None)
    if ev:
        ev.set()

def check_user_joined_all_channels(user_id: int) -> bool:
    """ম্যানেজার বটের নিজের টোকেন দিয়ে সরাসরি HTTP কল করে মেম্বারশিপ চেক করে (সিঙ্ক্রোনাস, থ্রেড থেকে ব্যবহারযোগ্য)"""
    for ch in REQUIRED_CHANNELS:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
                params={"chat_id": f"@{ch}", "user_id": user_id},
                timeout=10
            )
            info = r.json()
            if not info.get("ok"):
                return False
            if info["result"]["status"] in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True

def resume_all_reactors():
    """বট রিস্টার্ট হলে — মালিক এখনো চ্যানেলে আছে কিনা চেক করে শুধু তাদের বটগুলোই আবার চালু করে"""
    with _lock:
        d = _load()
        count = 0
        for short_id, info in d.get("bots", {}).items():
            if check_user_joined_all_channels(info["owner_id"]):
                start_child_bot(short_id, info["token"], info["emoji"])
                info["status"] = "active"
                count += 1
            else:
                info["status"] = "paused"
        _save(d)
    logger.info(f"{count} টা চাইল্ড বট রিজিউম করা হয়েছে (মোট {len(d.get('bots', {}))} টার মধ্যে)।")

def membership_watcher():
    """
    প্রতি ৫ মিনিটে প্রতিটা যুক্ত করা বটের মালিক এখনো চ্যানেলে আছে কিনা চেক করে।
    কেউ চ্যানেল ছেড়ে দিলে তার বট(গুলো) বন্ধ হয়ে যাবে, আবার জয়েন করলে
    স্বয়ংক্রিয়ভাবে আবার চালু হয়ে যাবে।
    """
    while True:
        time.sleep(300)
        try:
            with _lock:
                d = _load()
                changed = False
                for short_id, info in d.get("bots", {}).items():
                    owner_id = info["owner_id"]
                    is_member = check_user_joined_all_channels(owner_id)
                    currently_active = short_id in ACTIVE_REACTORS
                    if is_member and not currently_active:
                        start_child_bot(short_id, info["token"], info["emoji"])
                        info["status"] = "active"
                        changed = True
                        logger.info(f"ইউজার {owner_id} চ্যানেলে ফিরেছে, বট @{info['bot_username']} আবার চালু হলো।")
                    elif not is_member and currently_active:
                        stop_child_bot(short_id)
                        info["status"] = "paused"
                        changed = True
                        logger.info(f"ইউজার {owner_id} চ্যানেল ছেড়ে গেছে, বট @{info['bot_username']} বন্ধ করা হলো।")
                if changed:
                    _save(d)
        except Exception as e:
            logger.error(f"Membership watcher এরর: {e}")

# ============================================================
# ফোর্স জয়েন চেক
# ============================================================
async def is_user_joined_all(bot, user_id: int) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=f"@{ch}", user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True

def get_force_join_keyboard():
    buttons = []
    for ch in REQUIRED_CHANNELS:
        b = InlineKeyboardButton(f"📢 Join Channel", url=f"https://t.me/{ch}")
        _style(b, 'primary')
        buttons.append([b])
    btn_verify = InlineKeyboardButton("✅ Verify", callback_data="verify_join")
    _style(btn_verify, 'success')
    buttons.append([btn_verify])
    return InlineKeyboardMarkup(buttons)

FORCE_JOIN_MSG = (
    "🔒 বট ব্যবহার করার আগে নিচের চ্যানেলগুলোতে জয়েন করুন, "
    "তারপর ✅ Verify বাটনে চাপুন:"
)

# ============================================================
# মেইন মেনু
# ============================================================
def main_menu_keyboard():
    btn_add = KeyboardButton("➕ Add Bot")
    btn_edit = KeyboardButton("✏️ Edit Bot")
    btn_video = KeyboardButton("🎥 Bot Add Video")
    btn_contact = KeyboardButton("📞 Admin Contact")

    _style(btn_add, 'success')
    _style(btn_edit, 'primary')
    _style(btn_video, 'primary')
    _style(btn_contact, 'primary')

    return ReplyKeyboardMarkup([[btn_add, btn_edit], [btn_video, btn_contact]], resize_keyboard=True)

# ============================================================
# /start
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message:
        return
    user_id = update.effective_user.id

    if not await is_user_joined_all(context.bot, user_id):
        await update.message.reply_text(FORCE_JOIN_MSG, reply_markup=get_force_join_keyboard())
        return

    await update.message.reply_text(
        "👋 স্বাগতম!\n\nএই বট দিয়ে তুমি তোমার নিজের বট যুক্ত করতে পারবে, যেটা তোমার চ্যানেলে (যেখানে সেই বট admin) "
        "নতুন পোস্টে স্বয়ংক্রিয়ভাবে রিয়েক্ট দেবে। নিচের মেনু থেকে শুরু করো 👇",
        reply_markup=main_menu_keyboard()
    )

# ============================================================
# টেক্সট মেসেজ হ্যান্ডলার
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not await is_user_joined_all(context.bot, user_id):
        await update.message.reply_text(FORCE_JOIN_MSG, reply_markup=get_force_join_keyboard())
        return

    state = USER_STATE.get(user_id, {})

    # ---------------- Add Bot ফ্লো: টোকেন গ্রহণ ----------------
    if state.get("step") == "waiting_bot_token":
        token = text.strip()
        USER_STATE.pop(user_id, None)

        await update.message.reply_text("⏳ টোকেন যাচাই করা হচ্ছে...")
        try:
            resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            info = resp.json()
        except Exception:
            info = {"ok": False}

        if not info.get("ok"):
            await update.message.reply_text("❌ ভুল বট টোকেন! আবার সঠিক টোকেন দিন, অথবা /start চেপে আবার চেষ্টা করুন।")
            return

        bot_username = info["result"].get("username", "unknown")
        USER_STATE[user_id] = {"step": "waiting_emoji", "token": token, "bot_username": bot_username}

        buttons = []
        row = []
        for i, emo in enumerate(EMOJI_OPTIONS, start=1):
            b = InlineKeyboardButton(emo, callback_data=f"set_emoji:{emo}")
            _style(b, 'primary')
            row.append(b)
            if i % 4 == 0:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await update.message.reply_text(
            f"✅ বট পাওয়া গেছে: @{bot_username}\n\n👇 এই বট কোন ইমোজি দিয়ে রিয়েক্ট দেবে সিলেক্ট করুন:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ---------------- মেনু বাটনগুলো ----------------
    if text == "➕ Add Bot":
        USER_STATE[user_id] = {"step": "waiting_bot_token"}
        await update.message.reply_text("🤖 আপনার বট টোকেন দিন:\n\n(BotFather থেকে পাওয়া টোকেনটা এখানে পাঠান)")
        return

    if text == "✏️ Edit Bot":
        d = _load()
        my_bots = {sid: info for sid, info in d.get("bots", {}).items() if info.get("owner_id") == user_id}
        if not my_bots:
            await update.message.reply_text("❌ আপনার কোনো বট এখনো যুক্ত করা নেই।")
            return

        lines = ["🤖 আপনার যুক্ত করা বটসমূহ:\n"]
        buttons = []
        for sid, info in my_bots.items():
            status_icon = "🟢 Active" if info.get("status") == "active" else "🔴 Paused (চ্যানেল ছেড়ে গেছেন)"
            lines.append(f"• @{info['bot_username']} — রিয়েকশন: {info['emoji']} — {status_icon}")
            btn_del = InlineKeyboardButton(f"🗑️ Delete @{info['bot_username']}", callback_data=f"del_bot:{sid}")
            _style(btn_del, 'danger')
            buttons.append([btn_del])

        await update.message.reply_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
        return

    if text == "🎥 Bot Add Video":
        await update.message.reply_text(f"🎥 কীভাবে বট যুক্ত করবেন — ভিডিও টিউটোরিয়াল:\n\n{ADD_BOT_TUTORIAL_LINK}")
        return

    if text == "📞 Admin Contact":
        await update.message.reply_text(f"📞 যেকোনো সমস্যায় যোগাযোগ করুন:\n\n@{ADMIN_CONTACT_USERNAME}")
        return

# ============================================================
# বাটন (Inline) হ্যান্ডলার
# ============================================================
async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    if data == "verify_join":
        if await is_user_joined_all(context.bot, user_id):
            try: await query.delete_message()
            except: pass
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ ভেরিফাই সফল হয়েছে! নিচের মেনু থেকে শুরু করো 👇",
                reply_markup=main_menu_keyboard()
            )
        else:
            await query.answer("❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)
        return

    if data.startswith("set_emoji:"):
        emoji = data.split(":", 1)[1]
        state = USER_STATE.get(user_id, {})
        if state.get("step") != "waiting_emoji":
            return

        token = state["token"]
        bot_username = state["bot_username"]
        short_id = uuid.uuid4().hex[:8]

        with _lock:
            d = _load()
            d["bots"][short_id] = {
                "token": token,
                "emoji": emoji,
                "owner_id": user_id,
                "bot_username": bot_username,
                "status": "active"
            }
            _save(d)

        start_child_bot(short_id, token, emoji)
        USER_STATE.pop(user_id, None)

        try: await query.delete_message()
        except: pass
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 আপনার বট @{bot_username} সফলভাবে যুক্ত হয়েছে!\n\n"
                 f"এখন থেকে এই বট যেসব চ্যানেলে admin আছে, সেসব চ্যানেলের নতুন পোস্টে {emoji} রিয়েক্ট দেবে।",
            reply_markup=main_menu_keyboard()
        )
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🆕 নতুন বট যুক্ত হয়েছে\n\n👤 User ID: {user_id}\n🤖 Bot: @{bot_username}\n{emoji} Reaction: {emoji}"
                )
            except Exception:
                pass
        return

    if data.startswith("del_bot:"):
        short_id = data.split(":", 1)[1]
        with _lock:
            d = _load()
            bot_info = d.get("bots", {}).get(short_id)
            if not bot_info or bot_info.get("owner_id") != user_id:
                await query.message.reply_text("❌ বটটি খুঁজে পাওয়া যায়নি।")
                return
            bot_username = bot_info["bot_username"]
            del d["bots"][short_id]
            _save(d)

        stop_child_bot(short_id)
        await query.message.reply_text(f"🗑️ @{bot_username} সফলভাবে ডিলিট করা হয়েছে।")
        try: await query.delete_message()
        except: pass
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🗑️ বট ডিলিট হয়েছে\n\n👤 User ID: {user_id}\n🤖 Bot: @{bot_username}"
                )
            except Exception:
                pass
        return

# ============================================================
# গ্লোবাল এরর হ্যান্ডলার
# ============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, Conflict):
        logger.warning("Conflict: সাময়িক, স্বয়ংক্রিয়ভাবে recover হচ্ছে।")
        return
    logger.error(f"হ্যান্ডলারে সমস্যা হয়েছে: {err}", exc_info=err)

# ============================================================
# DUMMY HEALTH-CHECK সার্ভার (Render Web Service পোর্ট চায়)
# ============================================================
def _run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class _Health(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
        def log_message(self, *args):
            pass
    try:
        HTTPServer(("0.0.0.0", port), _Health).serve_forever()
    except Exception as e:
        logger.error(f"Health-check সার্ভার চালু করা যায়নি: {e}")

# ============================================================
# MAIN
# ============================================================
def main():
    resume_all_reactors()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(callback_query))
    app.add_error_handler(error_handler)
    logger.info("Multi-Bot Reaction Manager চালু হয়েছে।")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=_run_dummy_server, daemon=True).start()
    threading.Thread(target=membership_watcher, daemon=True).start()
    while True:
        try:
            main()
            break
        except Exception as e:
            logger.error(f"বট অপ্রত্যাশিতভাবে বন্ধ হয়ে গেছে, ৫ সেকেন্ড পর আবার চালু হচ্ছে: {e}", exc_info=e)
            time.sleep(5)