import os
import json
import re
import threading
import datetime
import uuid
import random
import pyotp
import logging
import asyncio
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton as _TelegramKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton as _TelegramInlineKeyboardButton, Bot as _TelegramBot, MessageEntity as _TelegramMessageEntity
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError, Conflict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# httpx প্রতিটা Telegram API কল-এ একটা INFO লাইন প্রিন্ট করে (getUpdates,
# getMe ইত্যাদি) — এতে console অকারণে ভরে যায়, তাই এটার লেভেল WARNING-এ
# তুলে দেওয়া হলো যাতে শুধু আসল সমস্যা হলেই কিছু দেখায়।
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)


# ============================================================
# TELEGRAM PREMIUM CUSTOM EMOJI DATABASE
# ============================================================
PREMIUM_EMOJI_IDS = {
    "📘": "5334807341109908955", "💬": "5334759662677957452",
    "✈️": "5337010556253543833", "💼": "5336814486701514414",
    "💭": "5337155807752524558", "📸": "5334868205091459431",
    "🍎": "5334637951894722661", "🔍": "5335010201005231986",
    "🪟": "5334880948259427772", "🧑‍🤝‍🧑": "5334590977837403844",
    "🎵": "5339213256001102461", "🏦": "5348469219761626211",
    "🚀": "5346042941196507141", "📈": "5348372939479751825",
    "💱": "5348212415077064131", "🌟": "5337102391244263212",
    "👻": "5359441366554255082", "🚗": "5298715455316303708",
    "💵": "5776103539872896061", "🎬": "5116246243646898866",
    "💜": "5463060437572528782", "🔒": "5399818044866327279",
    "🐦": "5215726959056662534", "👽": "4992421103847604984",
    "📌": "5346103513120258857", "🎮": "5233333563306301418",
    "📹": "5881799193219043268", "💻": "4994972469040251302",
    "☎️": "4992613535562334989", "🎥": "6255738712664050133",
    "🍿": "6104822598493801746", "📦": "5336879280578138635",
    "🐼": "5336879280578138635", "🛵": "5336879280578138635",
    "🛒": "5336879280578138635", "🛍️": "5336879280578138635",
    "💳": "5336879280578138635", "🦉": "5336879280578138635",
    "🤖": "5296516998996445955", "📓": "5336879280578138635",
    "🐙": "5417836094098007862", "🖌️": "5111661409008092227",
    "🎨": "5336879280578138635", "🌐": "5336879280578138635",
    "☁️": "5336879280578138635", "📚": "5336879280578138635",
    "🗣️": "5336879280578138635",
}

GLOBAL_BODY_EMOJIS = {
    "➖": "5870818207383686839", "🚫": "5334807341109908955", "😒": "5334763399299506604",
    "🖥": "6235307467337635626", "🌐": "5334590977837403844", "🌟": "5337102391244263212",
    "🕓": "5336983442125001376", "⌛": "4958503072801228000", "💬": "5337302974806922068",
    "🔐": "5337255927735163754", "🍏": "5337132498965010628", "❔": "5336850036145823599",
    "⚠️": "5336944168944047463", "🔥": "5337267511261960341", "💸": "5348469219761626211",
    "🥚": "5348390922507817684", "👨‍⚖": "5334763399299506604", "🐁": "5348494358205207761",
    "🧻": "5348486915026884464", "⚗": "5346311574221000149", "🛴": "5348075478634766440",
    "📊": "5353032893096567467", "🔢": "5352862640592949843", "👤": "5352861489541714456",
    "📁": "5352721946054268944", "🚀": "5352597830089347330", "💎": "5352838545826420397",
    "📍": "5352922460897452503", "👋": "5353027129250453493", "✅": "5352694861990501856",
    "1️⃣": "5352651766288652742", "2️⃣": "5355186458418257716", "3️⃣": "5352867219028091093",
    "4️⃣": "5352566657216714037", "5️⃣": "5353086880835474989", "6️⃣": "5354859211975071385",
    "7️⃣": "5352859127309707652", "8️⃣": "5352957533600389988", "9️⃣": "5353060913463204207",
    "🔤": "5352727417842606016", "📣": "5352980533150259581", "📤": "5353001161878182134",
    "✨": "5352552689983067014", "🔹": "5352638632278660622", "🎙": "5355102594886833928",
    "💴": "5352985330628730418", "📅": "5352585194295564660", "📴": "5352974971167611327",
    "✏️": "5395444784611480792", "📱": "5337132498965010628", "🔗": "5420517437885943844",
    "❌": "5420130255174145507", "⚙️": "5420155432272438703", "🫂": "5420145051336485498",
    "➕": "5420323438508155202", "🗑": "5422557736330106570", "🎁": "5420396762189831222",
    "➤": "5420618897898381296", "🏢": "5420156334215565595", "💳": "5190899075968441286",
    "📝": "5192739271886282680", "🛡": "5190447043545438788", "🤝": "5192805934073685937",
    "💰": "5190576863226933563", "👀": "5190645917711114179", "🕹": "5193100774988617665",
    "🟢": "5192812028632274956", "🧪": "5190781475468915802", "🎨": "5190751148704833975",
    "📂": "5257969839313526622", "🌍": "5780471598922337683", "📌": "5318986077455795572",
    "📢": "5789428375261023681", "🆔": "5352862640592949843", "📈": "5352877703043258544",
    "🔔": "5352980533150259581", "🏦": "5348469219761626211", "🧾": "5192739271886282680",
    "👨‍⚖️": "5334763399299506604", "🤔": "5370919202796348364", "😮": "5391090636961099009",
    # Common UI/message emojis used elsewhere in this bot.
    # Exact Premium emoji IDs supplied for the Facebook task UI.
    "🔜": "6089104521428997572", "😎": "5235807206770750407",
    "➡️": "6238013326798887112", "⬇️": "5193202823411546657",
    "🚧": "5336944168944047463", "❌": "5949785428843302949",
    "📂": "6206185428702206246", "⭐️": "5127861690641156032",
    "🛡": "6174589325695521740", "💵": "6206155797722830770",
    "📝": "5215672443036772796", "🚀": "6068700050928704109",
    "📱": "5848177124074066676", "⬆️": "5470143839371021696",
    "🕐": "5215484787325676090", "👉": "6158862632926319619",
    "📊": "5353032893096567467", "📥": "6203886371363364022",
    "⌛": "5386367538735104399", "👨‍💼": "5334763399299506604",
    "😀": "5978822208082939495", "💰": "6190336264940559752",
    "📤": "5353001161878182134", "✅": "4956454790012863177",
    "🎉": "5352552689983067014", "⚡": "6082511510406436819", "⚡️": "6082511510406436819", "💙": "5463060437572528782",
    "ℹ️": "5352861489541714456", "🔙": "5420618897898381296", "▶️": "5352694861990501856",
    "🎥": "6255738712664050133", "❓": "5336850036145823599", "👉": "5352922460897452503",
    "🛡️": "5190447043545438788", "⏱️": "5336983442125001376", "🔄": "5352980533150259581",
    "👇": "5352922460897452503", "💼": "5336814486701514414", "📋": "5352721946054268944",
    "📤": "5353001161878182134", "💰": "5190576863226933563", "❗": "5336944168944047463",
    "🔑": "5337255927735163754", "🛠️": "5420155432272438703", "🚧": "5336944168944047463",
    "❤️": "5463060437572528782", "📢": "5789428375261023681", "👨‍💼": "5334763399299506604",
    "🍪": "5336879280578138635", "🎯": "5352922460897452503", "👁️": "5190645917711114179",
    "💥": "5352597830089347330", "📄": "5352721946054268944", "📥": "5353001161878182134",
    "📲": "5337132498965010628", "📷": "5334868205091459431", "🗂️": "5257969839313526622",
    "🗑️": "5422557736330106570", "🟡": "5192812028632274956", "🥹": "5370919202796348364",
}

# Exact IDs supplied for the requested Facebook-task message design.
# These are applied after the general emoji database so they take precedence.
GLOBAL_BODY_EMOJIS.update({
    "🔜": "6089104521428997572",
    "😎": "5235807206770750407",
    "✅": "4956454790012863177",
    "📤": "5353001161878182134",
    "💰": "6190336264940559752",
    "⚡️": "6082511510406436819",
    "⚡": "6082511510406436819",
    "😀": "5978822208082939495",
    "🔥": "6068682402908083940",
    "➡️": "6238013326798887112",
    "⬇️": "5193202823411546657",
    "🚧": "5336944168944047463",
    "❌": "5949785428843302949",
    "📂": "6206185428702206246",
    "⭐️": "5127861690641156032",
    "🛡": "6174589325695521740",
    "🛡️": "6174589325695521740",
    "💵": "6206155797722830770",
    "📝": "5215672443036772796",
    "🚀": "6068700050928704109",
    "📱": "5848177124074066676",
    "⬆️": "5470143839371021696",
    "🕐": "5215484787325676090",
    "👉": "6158862632926319619",
    "📊": "5353032893096567467",
    "📥": "6203886371363364022",
    "⌛": "5386367538735104399",
    "👨‍💼": "5334763399299506604",
})

PREMIUM_SERVICE_IDS = {
    "FACEBOOK": "5334807341109908955",
    "WHATSAPP": "5334759662677957452",
    "TELEGRAM": "5337010556253543833",
    "WHATSAPP BUSINESSES": "5336814486701514414",
    "IMO": "5337155807752524558",
    "INSTAGRAM": "5334868205091459431",
    "APPLE": "5334637951894722661",
    "GOOGLE": "5335010201005231986",
    "MICROSOFT": "5334880948259427772",
    "TEAMS": "5334590977837403844",
    "TIKTOK": "5339213256001102461",
    "BKASH": "5348469219761626211",
    "ROCKET": "5346042941196507141",
    "BYBIT": "5348372939479751825",
    "BINANCE": "5348212415077064131",
    "MELBET": "5337102391244263212",
    "SNAPCHAT": "5359441366554255082",
    "UBER": "5298715455316303708",
    "PAYPAL": "5776103539872896061",
    "DISCORD": "5116246243646898866",
    "AMAZON": "4995019580536524226",
    "VIBER": "5463060437572528782",
    "LINKEDIN": "6224222994265279792",
    "LINE": "5399818044866327279",
    "WECHAT": "5782757599560602950",
    "TWITTER": "5215726959056662534",
    "REDDIT": "4992421103847604984",
    "PINTEREST": "5346103513120258857",
    "TWITCH": "5233333563306301418",
    "ZOOM": "5881799193219043268",
    "SIGNAL": "5293998404404272267",
    "SLACK": "4994972469040251302",
    "SKYPE": "4992613535562334989",
    "NETFLIX": "6255738712664050133",
    "SPOTIFY": "5411392711146095115",
    "AMAZON PRIME": "6111801057061374810",
    "HOICHOI": "6104822598493801746",
    "DARAZ": "5336879280578138635",
    "FOODPANDA": "5336879280578138635",
    "PATHAO": "5336879280578138635",
    "ALIEXPRESS": "5336879280578138635",
    "SHOPEE": "5336879280578138635",
    "PAYONEER": "5336879280578138635",
    "WISE": "5336879280578138635",
    "CHATGPT": "5296516998996445955",
    "NOTION": "5336879280578138635",
    "GITHUB": "5417836094098007862",
    "CANVA": "5111661409008092227",
    "FIGMA": "5336879280578138635",
    "UPWORK": "5336879280578138635",
    "FIVERR": "5336879280578138635",
    "YAHOO": "5336879280578138635",
    "DROPBOX": "5336879280578138635",
    "COURSERA": "5336879280578138635",
    "DUOLINGO": "5336879280578138635",
}

def premium_html(emoji: str) -> str:
    """Return a Telegram HTML custom-emoji span for a known emoji."""
    emoji_id = PREMIUM_EMOJI_IDS.get(emoji)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'
    return emoji

def premiumize_entities(text, existing_entities=None):
    """Attach Premium custom-emoji entities to every mapped emoji in outgoing messages."""
    if not isinstance(text, str):
        return existing_entities
    entities = list(existing_entities or [])
    occupied = []
    # আগে থেকে দেওয়া entity-গুলোর জায়গা "দখল করা" হিসেবে মার্ক করে রাখা হচ্ছে,
    # যাতে অটো-স্ক্যান একই জায়গায় দ্বিতীয়বার (ভিন্ন/ডুপ্লিকেট) entity না বসায়।
    for e in entities:
        try:
            occupied.append((e.offset, e.offset + e.length))
        except Exception:
            pass
    # Longest first prevents overlaps such as 👨‍⚖ and 👨‍⚖️.
    emoji_map = dict(PREMIUM_EMOJI_IDS)
    emoji_map.update(GLOBAL_BODY_EMOJIS)
    for emoji, emoji_id in sorted(emoji_map.items(), key=lambda item: len(item[0]), reverse=True):
        start = 0
        while True:
            pos = text.find(emoji, start)
            if pos < 0:
                break
            end = pos + len(emoji)
            offset16 = len(text[:pos].encode("utf-16-le")) // 2
            length16 = len(emoji.encode("utf-16-le")) // 2
            if not any(offset16 < e and offset16 + length16 > s for s, e in occupied):
                entities.append(_TelegramMessageEntity(
                    type="custom_emoji",
                    offset=offset16,
                    length=length16,
                    custom_emoji_id=emoji_id,
                ))
                occupied.append((offset16, offset16 + length16))
            start = end
    return entities or None


def build_custom_emoji_entities(text, emoji_id_sequence):
    """
    text-এ emoji_id_sequence-এ দেওয়া ক্রম অনুযায়ী custom_emoji entity বসায়।
    emoji_id_sequence: [(emoji_char, emoji_id), ...] — text-এ যে ক্রমে ইমোজিগুলো
    আসে ঠিক সেই ক্রমে দিতে হবে। এটা দরকার কারণ generic dict-ভিত্তিক অটো-ম্যাচিং
    (premiumize_entities) একই ইমোজি ক্যারেক্টারের প্রতিটা occurrence-এ সবসময়
    একই ID বসায় — কিন্তু কিছু মেসেজে একই ইমোজি (যেমন ✅) দুইবার এলেও প্রতিবার
    আলাদা Premium ID লাগবে, তাই সেসব ক্ষেত্রে এই ফাংশন দিয়ে হাতে entity বসাতে হয়।
    """
    entities = []
    cursor = 0
    for emoji_char, emoji_id in emoji_id_sequence:
        pos = text.find(emoji_char, cursor)
        if pos < 0:
            continue
        end = pos + len(emoji_char)
        offset16 = len(text[:pos].encode("utf-16-le")) // 2
        length16 = len(emoji_char.encode("utf-16-le")) // 2
        entities.append(_TelegramMessageEntity(
            type="custom_emoji",
            offset=offset16,
            length=length16,
            custom_emoji_id=emoji_id,
        ))
        cursor = end
    return entities


def build_bold_entity(text, substring, start_from=0):
    """substring-টাকে bold করার জন্য একটা entity বানায় (parse_mode ব্যবহার করা যাচ্ছে না
    যেহেতু একই মেসেজে custom_emoji entity-ও পাঠাতে হচ্ছে — Telegram parse_mode আর
    entities একসাথে গ্রহণ করে না)।"""
    pos = text.find(substring, start_from)
    if pos < 0:
        return None
    offset16 = len(text[:pos].encode("utf-16-le")) // 2
    length16 = len(substring.encode("utf-16-le")) // 2
    return _TelegramMessageEntity(type="bold", offset=offset16, length=length16)


def build_code_entity(text, substring, start_from=0):
    """substring-টাকে monospace/code স্টাইলে দেখানোর জন্য entity বানায় (backtick/parse_mode
    ছাড়াই — একই কারণে যা build_bold_entity-এর docstring-এ বলা আছে)।"""
    pos = text.find(substring, start_from)
    if pos < 0:
        return None
    offset16 = len(text[:pos].encode("utf-16-le")) // 2
    length16 = len(substring.encode("utf-16-le")) // 2
    return _TelegramMessageEntity(type="code", offset=offset16, length=length16)


def _premiumize_button_text(text):
    """বাটনের টেক্সট uppercase করে এবং trim করে, যাতে matching-এর জন্য consistent
    থাকে। এখন আর ইমোজি স্ট্রিপ করা হয় না — সেই স্ট্রিপিং শুধু পুরনো
    icon_custom_emoji_id সিস্টেমের (যেটা Telegram বাটনে আসলে সাপোর্টই করে না)
    জন্য দরকার ছিল, সেটা সরিয়ে দেওয়ার পর ইমোজি বাটনে দেখাতে দেওয়াই ভালো।"""
    if not isinstance(text, str):
        return text
    return text.strip().upper()


# Patch Telegram text-sending methods once so every outgoing message automatically
# receives the Premium custom-emoji entities, including language strings and dynamic messages.
_original_bot_send_message = _TelegramBot.send_message
_original_bot_edit_message_text = _TelegramBot.edit_message_text

async def _premium_send_message(self, *args, **kwargs):
    if len(args) >= 2:
        text = args[1]
        if isinstance(text, str):
            kwargs["entities"] = premiumize_entities(text, kwargs.get("entities"))
    elif isinstance(kwargs.get("text"), str):
        kwargs["entities"] = premiumize_entities(kwargs["text"], kwargs.get("entities"))
    return await _original_bot_send_message(self, *args, **kwargs)

async def _premium_edit_message_text(self, *args, **kwargs):
    if args and isinstance(args[0], str):
        text = args[0]
        kwargs["entities"] = premiumize_entities(text, kwargs.get("entities"))
    elif isinstance(kwargs.get("text"), str):
        kwargs["entities"] = premiumize_entities(kwargs["text"], kwargs.get("entities"))
    return await _original_bot_edit_message_text(self, *args, **kwargs)

_TelegramBot.send_message = _premium_send_message
_TelegramBot.edit_message_text = _premium_edit_message_text

PREMIUM_BUTTON_IDS = {
    "TASK": "5267045723685264285",
    "WITHDRAW": "6190336264940559752",
    "YOUR REPORT": "5429184896637607413",
    "REPORT": "5429184896637607413",
    "SUPPORT": "6129805886383723340",
    "বাংলা": "5291824687096027834",
    "🇧🇩 বাংলা": "5291824687096027834",
    "ENGLISH": "5293993521026453119",
    "🇬🇧 ENGLISH": "5293993521026453119",
}

def _button_key(text):
    if not isinstance(text, str):
        return ""
    value = _premiumize_button_text(text).strip()
    return value.upper()

def _premium_button_emoji(text: str):
    key = _button_key(text)
    if key in PREMIUM_BUTTON_IDS:
        return PREMIUM_BUTTON_IDS[key]
    upper = str(text).upper()
    for name, emoji_id in PREMIUM_SERVICE_IDS.items():
        if name in upper:
            return emoji_id
    for emoji, emoji_id in PREMIUM_EMOJI_IDS.items():
        if emoji in str(text):
            return emoji_id
    return None

def InlineKeyboardButton(text, *args, **kwargs):
    """Create an inline button. icon_custom_emoji_id IS a real Telegram field, but only
    works for bots with a Fragment-purchased username (or Premium owner) — pass it
    explicitly per-button where needed; it is not auto-detected from the emoji in text."""
    text = _premiumize_button_text(text)
    return _TelegramInlineKeyboardButton(text, *args, **kwargs)

def KeyboardButton(text, *args, **kwargs):
    """Create a reply-keyboard button (see note in InlineKeyboardButton above)."""
    text = _premiumize_button_text(text)
    return _TelegramKeyboardButton(text, *args, **kwargs)

# ============================================================
# CONFIG & FILE SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6470499890"))

# বাধ্যতামূলক চ্যানেলগুলোর ইউজারনেম (বটকে অবশ্যই এই চ্যানেলে এডমিন হতে হবে)
REQUIRED_CHANNELS = ["@range_channele", "@insagramth"]

_lock = threading.Lock()

def _style(btn, style_name: str):
    """
    কিছু বাটনে (রঙিন UI hint-এর জন্য) 'style' নামে একটা কাস্টম attribute
    বসানোর চেষ্টা করা হয়। নতুন python-telegram-bot ভার্সনে Keyboard/
    InlineKeyboardButton ক্লাস __slots__ ব্যবহার করে বলে সরাসরি নতুন
    attribute বসানো সবসময় সম্ভব হয় না — এই ফাংশন চেষ্টা করে, ব্যর্থ হলে
    নিঃশব্দে স্কিপ করে (বাটন ঠিকই কাজ করবে, শুধু রঙের hint-টা যোগ হবে না)।
    """
    try:
        object.__setattr__(btn, 'style', style_name)
    except Exception:
        pass

# ============================================================
# FIREBASE REALTIME DATABASE (সব ডেটা এখানেই স্থায়ীভাবে সেভ হবে)
# Render-এ ডিস্ক ephemeral, তাই local JSON file এর বদলে Firebase
# ব্যবহার করা হচ্ছে যাতে redeploy/restart এ ডেটা হারিয়ে না যায়।
# ============================================================
FIREBASE_BASE_URL = "https://realtime-database-7310e-default-rtdb.firebaseio.com"
_DATA_CACHE = None  # in-memory cache, _lock দ্বারা সুরক্ষিত

def _firebase_get(path=""):
    """Firebase থেকে ডেটা রিড করার ফাংশন"""
    try:
        r = requests.get(f"{FIREBASE_BASE_URL}/{path}.json", timeout=10)
        if r.status_code == 200:
            return r.json()
        logger.error(f"Firebase GET failed on '{path}': HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Firebase GET Error on '{path}': {e}")
    return None

def _firebase_patch(data: dict, path=""):
    """Firebase-এ শুধু নির্দিষ্ট top-level key গুলো আপডেট করে (অন্য কোনো ডেটা মোছে না)"""
    try:
        r = requests.patch(f"{FIREBASE_BASE_URL}/{path}.json", json=data, timeout=10)
        if r.status_code == 200:
            return True
        logger.error(f"Firebase PATCH failed on '{path}': HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Firebase PATCH Error on '{path}': {e}")
    return False

def _firebase_put(data, path=""):
    """Firebase-এ একটা নির্দিষ্ট path সম্পূর্ণভাবে overwrite করে (delete সহ ঠিকভাবে reflect হয়)"""
    try:
        r = requests.put(f"{FIREBASE_BASE_URL}/{path}.json", json=data, timeout=10)
        if r.status_code == 200:
            return True
        logger.error(f"Firebase PUT failed on '{path}': HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Firebase PUT Error on '{path}': {e}")
    return False

# ============================================================
# ID DUMP (Facebook/Instagram সাবমিশন এখানে জমা হবে, Admin Panel
# থেকে txt ফাইল হিসেবে ডাউনলোড করলে খালি হয়ে যাবে)
# ============================================================
def add_to_id_dump(category: str, task_type: str, entry: dict):
    """
    একটা সাবমিশনের তথ্য (uid, password, data) Facebook/Instagram এর
    Cookies/2FA — এই ৪ টা আলাদা ডাম্প লিস্টের একটাতে যোগ করে (Firebase-এ
    persist থাকে)। কোনো কারণে ব্যর্থ হলে চুপচাপ log করে, বট থামে না।
    """
    cat_key = "fb" if category == "facebook" else "ig"
    type_key = "2fa" if task_type == "2fa" else "cookies"
    key = f"{cat_key}_{type_key}_dump"
    try:
        with _lock:
            d = _load()
            if key not in d:
                d[key] = []
            d[key].append(entry)
            _save(d)
    except Exception as e:
        logger.error(f"ID ডাম্পে যোগ করা যায়নি ({key}): {e}")

# ============================================================
# MULTI-LANGUAGE DICTIONARY
# ============================================================
LANGUAGES = {
    "en": {
        "welcome": "🔜 Welcome to 𓆩𓆩 FACEBOOK TASK 𓆪𓆪! 😎\n\n✅ Complete tasks with ease.\n📤 Submit your proof.\n💰 Earn rewards instantly.\n\n⚡️ Fast • Secure • Trusted\n\n😀 Happy Earning & Best of Luck! 🔥",
                        "btn_tasks": "TASK",
                "btn_withdraw": "WITHDRAW",
                "btn_report": "YOUR REPORT",
                "btn_support": "SUPPORT",
                "btn_language": "LANGUAGE",
                "btn_admin": "ADMIN PANEL",
                "btn_back": "BACK",
                "btn_cancel": "CANCEL",
                "btn_start": "START",
                "btn_video": "VIDEO",
                "btn_how_to_2fa": "HOW TO GET 2FA?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:",
        "lang_changed": "✅ Language changed to English!",
        "balance_msg": "💳 Wallet Balance: ৳{bal}",
        "report_msg": "📊 All Account Report📥\n\n✅ Success: [{s}]\n⌛ Reviewing: [{r}]\n❌ Rejected: [{rej}]",
        "select_cat": "➡️ Select Your Task Category ⬇️",
        "cat_instagram": "INSTAGRAM TASK",
        "cat_facebook": "FACEBOOK TASK",
        "task_hidden": "❌ This task is currently hidden by Admin.",
        "no_tasks": "🚧 This task is currently closed.❌\n\n💬Please try others. ✅",
        "choose_type": "🎯 Choose Task:",
        "send_2fa_secret": "👉 Please Send Your 2FA Secret Key",
        "send_cookies": "👉 Please Send Your Cookies Data 📂",
        "send_fb_uid": "👉 Please Send Your Facebook UID",
        "invalid_2fa": "❌ Invalid 2FA Secret Key! Please send a valid key again:",
        "withdraw_dash": "💳 Your Balance Dashboard\n\n💰 Balance: ৳{bal}\n💸 Minimum Withdraw: ৳50\n💳 Withdrawal Charge: ৳5\n✅ You Will Receive: ৳{rec}",
        "withdraw_min_err": "❌ Unsuccessful balance: Minimum ৳50 required",
        "select_meth": "💳 Select Your Withdraw Method:",
        "send_num": "📱 Please Send Your {method} Number",
        "enter_amt": "💰 Please Enter Your Withdraw Amount:",
        "insufficient": "❌ Insufficient balance.",
        "min_amt_err": "❌ Minimum withdraw is ৳50",
        "check_info": "📋 Please Check Your Info\n\n📱 Number: {num}\n💳 Method: {method}\n💵 Amount: ৳{amt}\n✅ Receive: ৳{rec}\n\n✅ If All Information Is Correct, Please Tap the Confirm Button. 👇",
                "btn_confirm": "CONFIRM",
        "pay_pending": "⌛ Your Payment Is Pending.\n\n👨‍💼 Please Wait for Admin Approval.",
        "cookies_rec": "👉 Cookies Received. Click below to proceed.",
                "btn_acc_reg": "ACCOUNT REGISTERED",
        "invite_check": "⚠️ Have You Invited 2 Friends?\n\n❌ If You Have Not Invited 2 Friends, Your Report Will Be Rejected.",
        "invite_check_short": "✅ Please confirm below to submit your report.",
                "btn_subbed": "YES | I AM SUBSCRIBED",
        "thanks_msg": "✅ Thanks! Please Do Not Unfollow. Follow the Rules.",
        "report_received": "✅ Your report has been received!\n⌛ Please wait for report",
        "no_usernames_err": "❌ No user available yet!",
        "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
    },
    "bn": {
        "welcome": "🔜 Welcome to 𓆩𓆩 FACEBOOK TASK 𓆪𓆪! 😎\n\n✅ Complete tasks with ease.\n📤 Submit your proof.\n💰 Earn rewards instantly.\n\n⚡️ Fast • Secure • Trusted\n\n😀 Happy Earning & Best of Luck! 🔥",
                        "btn_tasks": "কাজ",
                "btn_withdraw": "উইথড্র",
                "btn_report": "আপনার রিপোর্ট",
                "btn_support": "সাপোর্ট",
                "btn_language": "ভাষা",
                "btn_admin": "এডমিন প্যানেল",
        "btn_back": "পেছনে যান",
        "btn_cancel": "বাতিল করুন",
        "btn_start": "শুরু করুন",
        "btn_video": "ভিডিও দেখুন",
                "btn_how_to_2fa": "2FA কিভাবে পাবো?",
        "select_lang": "🌐 Select Language / ভাষা নির্বাচন করুন:",
        "lang_changed": "✅ ভাষা পরিবর্তন করে বাংলায় সেট করা হয়েছে!",
        "balance_msg": "💳 ওয়ালেট ব্যালেন্স: ৳{bal}",
        "report_msg": "📊 সকল অ্যাকাউন্ট রিপোর্ট\n\n✅ সফল: [{s}]\n⏳ রিভিউতে আছে: [{r}]\n❌ বাতিল হয়েছে: [{rej}]",
        "select_cat": "📋 ক্যাটাগরি নির্বাচন করুন:",
        "cat_instagram": "ইনস্টাগ্রাম টাস্ক",
        "cat_facebook": "ফেসবুক টাস্ক",
        "task_hidden": "❌ এই কাজটি বর্তমানে এডমিন দ্বারা হাইড করা আছে।",
        "no_tasks": "🚧 এই টাস্কে বর্তমানে কাজ বন্ধ আছে।❌\n\n💬অন্যগুলো ট্রাই করেন। ✅",
        "choose_type": "🎯 কাজ বেছে নিন:",
        "send_2fa_secret": "👉 অনুগ্রহ করে আপনার 2FA সিক্রেট কি (Secret Key) পাঠান",
        "send_cookies": "👉 অনুগ্রহ করে আপনার কুকিজ (Cookies) ডাটা পাঠান",
        "send_fb_uid": "👉 অনুগ্রহ করে আপনার ফেসবুক ইউআইডি (Facebook UID) পাঠান",
        "invalid_2fa": "❌ ভুল 2FA সিক্রেট কি! দয়া করে আবার সঠিক কি পাঠান:",
        "withdraw_dash": "💳 আপনার ব্যালেন্স ড্যাশবোর্ড\n\n💰 ব্যালেন্স: ৳{bal}\n💸 সর্বনিম্ন উইথড্র: ৳50\n💳 উইথড্র চার্জ: ৳5\n✅ আপনি পাবেন: ৳{rec}",
        "withdraw_min_err": "❌ ব্যর্থ: সর্বনিম্ন ৳50 ব্যালেন্স থাকা আবশ্যক",
        "select_meth": "💳 আপনার উইথড্র পদ্ধতি নির্বাচন করুন:",
        "send_num": "📱 অনুগ্রহ করে আপনার {method} নম্বরটি পাঠান",
        "enter_amt": "💰 অনুগ্রহ করে আপনার উইথড্র অ্যামাউন্ট লিখুন:",
        "insufficient": "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই।",
        "min_amt_err": "❌ সর্বনিম্ন উইথড্র ৳50",
        "check_info": "📋 দয়া করে আপনার তথ্য যাচাই করুন\n\n📱 নম্বর: {num}\n💳 মাধ্যম: {method}\n💵 পরিমাণ: ৳{amt}\n✅ আপনি পাবেন: ৳{rec}\n\n✅ সব তথ্য ঠিক থাকলে নিচের কন্ডিশন বাটনে চাপুন। 👇",
        "btn_confirm": "কনফার্ম করুন",
        "pay_pending": "⏳ আপনার পেমেন্ট পেন্ডিং অবস্থায় আছে।\n\n👨‍💼 অনুগ্রহ করে এডমিনের অনুমোদনের জন্য অপেক্ষা করুন।",
        "cookies_rec": "👉 কুকিজ পাওয়া গেছে। সামনে এগিয়ে যেতে নিচের বাটনে চাপুন।",
        "btn_acc_reg": "অ্যাকাউন্ট রেজিস্টার্ড",
        "invite_check": "⚠️ আপনি কি ২ জন বন্ধুকে ইনভাইট করেছেন?\n\n❌ যদি আপনি ২ জন বন্ধুকে ইনভাইট না করে থাকেন, তবে আপনার রিপোর্টটি রিজেক্ট করা হবে।",
        "invite_check_short": "✅ নিচে কনফার্ম করে আপনার রিপোর্ট সাবমিট করুন।",
        "btn_subbed": "হ্যাঁ | আমি সাবসক্রাইব করেছি",
        "thanks_msg": "✅ ধন্যবাদ! অনুগ্রহ করে আনফলো করবেন না। নিয়ম মেনে চলুন।",
        "report_received": "✅ আপনার রিপোর্টটি গ্রহণ করা হয়েছে!\n⏳ রিপোর্টের জন্য অপেক্ষা করুন",
        "no_usernames_err": "❌ বর্তমানে কোনো ইউজার খালি নেই!",
        "force_join_msg": "📢 আমাদের বটটি ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
        "not_joined_all": "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে আবার ভেরিফাই করুন।",
        "verify_success": "✅ এখন আমাদের বটটি ব্যবহার করতে পারবেন।\nআমাদের চ্যানেলে জয়েন হওয়ার জন্য ধন্যবাদ! ❤️",
        "support_msg": "⚠️ কোনো সমস্যা হলে অ্যাডমিনকে জানান।"
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
        "used_usernames": [],
        "task_password": "shuvo9",
        "visibility": {"instagram_task": True, "facebook_task": True},
        "fb_cookies_dump": [],
        "fb_2fa_dump": [],
        "ig_cookies_dump": [],
        "ig_2fa_dump": []
    }

def _load():
    """মেমরি ক্যাশ থেকে ডেটা রিটার্ন করে; প্রথমবার Firebase থেকে fetch করে ক্যাশ বানায়"""
    global _DATA_CACHE
    if _DATA_CACHE is not None:
        return _DATA_CACHE
    remote = _firebase_get()
    d = remote if isinstance(remote, dict) else {}
    if "saved_usernames" not in d:
        d["saved_usernames"] = []
    if "used_usernames" not in d:
        d["used_usernames"] = []
    if "dynamic_tasks" not in d:
        d["dynamic_tasks"] = {}
    if "task_password" not in d:
        d["task_password"] = "shuvo9"
    if "visibility" not in d:
        d["visibility"] = {"instagram_task": True, "facebook_task": True}
    if "users" not in d:
        d["users"] = {}
    if "submissions" not in d:
        d["submissions"] = {}
    if "withdrawals" not in d:
        d["withdrawals"] = {}
    if "fb_cookies_dump" not in d:
        d["fb_cookies_dump"] = []
    if "fb_2fa_dump" not in d:
        d["fb_2fa_dump"] = []
    if "ig_cookies_dump" not in d:
        d["ig_cookies_dump"] = []
    if "ig_2fa_dump" not in d:
        d["ig_2fa_dump"] = []
    _DATA_CACHE = d
    return _DATA_CACHE

def _save(data):
    """
    ক্যাশ সাথে সাথে আপডেট করে (তাই বট সবাইকে সঙ্গে সঙ্গে রেসপন্স দিতে পারে), আর
    Firebase-এ পার্সিস্ট করার আসল নেটওয়ার্ক কলটা ব্যাকগ্রাউন্ড থ্রেডে পাঠিয়ে দেয়।

    এর আগে এই ফাংশনটা প্রতিবার সরাসরি (blocking) Firebase-এ রিকোয়েস্ট পাঠাত, যেটা
    বটের asyncio ইভেন্ট লুপকে পুরোপুরি আটকে রাখত (requests লাইব্রেরি sync, আর কোনো
    executor/thread ছাড়াই async ফাংশনের ভেতর থেকে কল হচ্ছিল) — ফলে একজনের একটা
    অ্যাকশন সেভ হওয়ার সময় বাকি সব ইউজারের বট 'স্লো'/আটকে যেত। এখন Firebase কল
    আলাদা থ্রেডে চলে, তাই বট প্রতিটা চাপের সাথে সাথে সাথে সাথে রেসপন্স করে,
    ইউজার সংখ্যা যতই বাড়ুক না কেন।
    """
    global _DATA_CACHE
    _DATA_CACHE = data
    payload = {
        "users": data.get("users", {}),
        "submissions": data.get("submissions", {}),
        "withdrawals": data.get("withdrawals", {}),
        "dynamic_tasks": data.get("dynamic_tasks", {}),
        "saved_usernames": data.get("saved_usernames", []),
        "used_usernames": data.get("used_usernames", []),
        "task_password": data.get("task_password", "shuvo9"),
        "visibility": data.get("visibility", {"instagram_task": True, "facebook_task": True}),
        "fb_cookies_dump": data.get("fb_cookies_dump", []),
        "fb_2fa_dump": data.get("fb_2fa_dump", []),
        "ig_cookies_dump": data.get("ig_cookies_dump", []),
        "ig_2fa_dump": data.get("ig_2fa_dump", []),
    }

    def _background_patch():
        if not _firebase_patch(payload):
            logger.error("⚠️ ডেটা Firebase-এ সেভ করা যায়নি! (network/permission সমস্যা হতে পারে)")

    threading.Thread(target=_background_patch, daemon=True).start()

def get_or_create_user(user_id: int, username: str = ""):
    with _lock:
        data = _load()
        uid = str(user_id)
        if uid not in data["users"]:
            data["users"][uid] = {
                "user_id": user_id,
                "username": username,
                "balance": 0.0,
                "language": "bn", 
                "success_count": 0,
                "review_count": 0,
                "rejected_count": 0,
            }
            _save(data)
        return data["users"][uid]

def generate_unique_instagram_username():
    """একবারও ব্যবহার হয়নি এমন একটা বৈধ-দেখতে ইনস্টাগ্রাম ইউজারনেম জেনারেট করে
    (আগে যেগুলো জেনারেট হয়েছে সেগুলোর হিসাব 'used_usernames'-এ রাখা হয়, যাতে
    রিপিট না হয়)।"""
    adjectives = ["cool", "shadow", "silent", "royal", "urban", "lucky", "golden",
                  "midnight", "crazy", "silver", "dark", "wild", "electric", "vivid"]
    nouns = ["tiger", "wolf", "falcon", "storm", "phoenix", "raven", "panther",
             "dragon", "eagle", "fox", "ninja", "cobra", "hawk", "lion"]
    with _lock:
        d = _load()
        used = set(d.get("used_usernames", []))
        candidate = None
        for _ in range(50):
            attempt = f"{random.choice(adjectives)}_{random.choice(nouns)}{random.randint(10, 9999)}"
            if attempt not in used:
                candidate = attempt
                break
        if candidate is None:
            candidate = f"user_{uuid.uuid4().hex[:10]}"
        used.add(candidate)
        d["used_usernames"] = list(used)
        _save(d)
    return candidate


def generate_profile_or_get_saved(task_category="instagram"):
    """টাস্ক ক্যাটাগরির উপর ভিত্তি করে ডাটা জেনারেট করে"""
    first_names = ["fatima", "wafaa", "ahmed", "youssef", "omar", "nour", "ali"]
    last_names = ["Zayan", "Emad", "Khan", "Ahmed", "Ali", "Hassan"]
    f_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    if task_category == "facebook":
        return f_name, "facebook_no_username"

    login_name = generate_unique_instagram_username()
    return f_name, login_name

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

# ============================================================
# PREMIUM BUTTON TEXT COMPATIBILITY
# ============================================================
def _restore_button_text(text: str) -> str:
    """Restore the old internal button label after Telegram sends the visible
    text without its separate Premium custom-emoji icon."""
    if not isinstance(text, str):
        return text

    candidates = []
    for _lang, _strings in LANGUAGES.items():
        for _key, _value in _strings.items():
            if isinstance(_value, str) and "\n" not in _value and len(_value) < 100:
                candidates.append(_value)

    candidates.extend([
        "🔥𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗧𝗔𝗦𝗞", "📘𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞 𝗧𝗔𝗦𝗞",
        "🔗 𝖱𝖾𝖿𝖾𝗋 & 𝖤𝖺𝗋𝗇", "🔙 Return to main menu", "Withdraw",
        "bKash", "Nagad", "Binance", "Approve", "Reject",
    ])
    # নোট: Admin Panel-এর সাব-বাটনগুলো (Add Task, Delete Task, Task
    # Hide/Show, User Broadcast, Add Money, Username Save, All Report,
    # User Delete, Password Change, Instagram File, Facebook File, Work
    # Video) ইচ্ছাকৃতভাবে এই লিস্টে রাখা হয়নি — নিচের handle_message-এর
    # চেকগুলো এদের জন্য stripped/uppercase ফর্ম (যেমন "ADD TASK") আশা
    # করে, emoji-সহ canonical ফর্ম না। এগুলো লিস্টে থাকলে বাটন চাপলেই
    # কোনো response আসতো না।

    seen = set()
    for canonical in sorted(candidates, key=len, reverse=True):
        if canonical in seen:
            continue
        seen.add(canonical)
        stripped = _premiumize_button_text(canonical)
        if stripped and text == stripped:
            return canonical
    return text

def get_force_join_keyboard(lang: str):
    btn_ch1 = InlineKeyboardButton("Range Channel", url="https://t.me/range_channele")
    btn_ch2 = InlineKeyboardButton("Instagram TH", url="https://t.me/insagramth")
    btn_verify = InlineKeyboardButton("Verify Membership", callback_data="verify_join")
    
    _style(btn_ch1, 'primary')
    _style(btn_ch2, 'primary')
    _style(btn_verify, 'success')
    
    return InlineKeyboardMarkup([[btn_ch1], [btn_ch2], [btn_verify]])

# ============================================================
# KEYBOARDS DEFINITION
# ============================================================

def main_menu_keyboard(user_id: int, lang: str):
    ln = LANGUAGES[lang]
    
    btn_tasks = KeyboardButton(ln["btn_tasks"], icon_custom_emoji_id="5267045723685264285")
    btn_withdraw = KeyboardButton(ln["btn_withdraw"], icon_custom_emoji_id="6190336264940559752")
    btn_report = KeyboardButton(ln["btn_report"], icon_custom_emoji_id="5429184896637607413")
    btn_support = KeyboardButton(ln["btn_support"], icon_custom_emoji_id="6129805886383723340")
    btn_language = KeyboardButton(ln["btn_language"], icon_custom_emoji_id="6260264603171689263")
    
    _style(btn_tasks, 'primary')
    _style(btn_withdraw, 'success')
    _style(btn_report, 'success')
    _style(btn_support, 'success')
    _style(btn_language, 'success')
    
    buttons = [
        [btn_tasks],
        [btn_withdraw, btn_report],
        [btn_support, btn_language],
    ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ============================================================
# USER STATE MANAGEMENT
# ============================================================
USER_STATE = {}

async def send_admin_dashboard(bot, chat_id: int, lang: str):
    """
    Admin Control Dashboard পাঠায় — ইনলাইন বাটন আকারে (মেসেজের নিচে,
    keyboard মেনুতে না)। ADMIN PANEL চাপা (টেক্সট, পুরনো ফলব্যাক) বা
    ইনলাইন বাটন চাপা — দুই জায়গা থেকেই একই ফাংশন ব্যবহার হয়।
    """
    btn_add_t = InlineKeyboardButton("Add Task", callback_data="adm_add_task")
    btn_del_t = InlineKeyboardButton("Delete Task", callback_data="adm_delete_task")
    btn_brd_t = InlineKeyboardButton("User Broadcast", callback_data="adm_broadcast")
    btn_add_m = InlineKeyboardButton("Add Money", callback_data="adm_add_money")
    btn_sav_u = InlineKeyboardButton("Username Save", callback_data="adm_username_save")
    btn_all_r = InlineKeyboardButton("All Report", callback_data="adm_all_report")
    btn_pwd_t = InlineKeyboardButton("Password Change", callback_data="adm_password_change")
    btn_work_vid = InlineKeyboardButton("Work Video", callback_data="adm_work_video")
    btn_all_file = InlineKeyboardButton("Bot All Task File", callback_data="adm_all_task_file")
    btn_pending_uids = InlineKeyboardButton("Pending UID List", callback_data="adm_pending_uids")
    btn_reset_bal = InlineKeyboardButton("Reset All Balances", callback_data="adm_reset_balances")
    btn_back_m = InlineKeyboardButton("BACK", callback_data="adm_back")

    _style(btn_add_t, 'success')
    _style(btn_del_t, 'danger')
    _style(btn_brd_t, 'primary')
    _style(btn_add_m, 'success')
    _style(btn_sav_u, 'success')
    _style(btn_all_r, 'primary')
    _style(btn_pwd_t, 'primary')
    _style(btn_work_vid, 'success')
    _style(btn_all_file, 'primary')
    _style(btn_pending_uids, 'primary')
    _style(btn_reset_bal, 'danger')
    _style(btn_back_m, 'danger')

    kb = InlineKeyboardMarkup([
        [btn_add_t, btn_del_t],
        [btn_brd_t, btn_add_m],
        [btn_sav_u, btn_all_r],
        [btn_pwd_t, btn_work_vid],
        [btn_all_file],
        [btn_pending_uids],
        [btn_reset_bal],
        [btn_back_m]
    ])
    await bot.send_message(chat_id=chat_id, text="🛠️ Admin Control Dashboard", reply_markup=kb)


async def admin_send_file_dump(bot, chat_id: int, category: str, task_type: str):
    """Facebook/Instagram Cookies/2FA — এই ৪টা আলাদা বাটনের জন্য Excel এক্সপোর্ট লজিক।
    ফাইল পাঠানোর সাথে সাথে ডাটা মুছে ফেলা হয় না — ফাইলের নিচে একটা Clear বাটন থাকে,
    সেটা চাপলেই শুধু ডাটা মুছে নতুন করে সেভ হওয়া শুরু হয়। ফাইলে শুধু UID, Password,
    এবং Cookies/2FA — এই তিনটা কলামই থাকে, আর কিছু না।"""
    cat_key = "fb" if category == "facebook" else "ig"
    type_key = "2fa" if task_type == "2fa" else "cookies"
    key = f"{cat_key}_{type_key}_dump"
    cat_label = "Facebook" if category == "facebook" else "Instagram"
    type_label = "2FA" if task_type == "2fa" else "Cookies"
    label = f"{cat_label} {type_label}"

    with _lock:
        d = _load()
        dump_list = list(d.get(key, []))

    if not dump_list:
        await bot.send_message(chat_id=chat_id, text=f"❌ এখনো পর্যন্ত কোনো নতুন {label} সাবমিশন জমা হয়নি।")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = label[:31]

    headers = ["UID", "Password", type_label]
    ws.append(headers)
    header_fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    for col_idx, _ in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    row_fills = [
        PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid"),
        PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"),
    ]
    for i, e in enumerate(dump_list):
        row_num = i + 2
        fill = row_fills[i % 2]
        ws.cell(row=row_num, column=1, value=e.get("uid", "")).fill = fill
        ws.cell(row=row_num, column=2, value=e.get("password", "")).fill = fill
        ws.cell(row=row_num, column=3, value=e.get("data", "")).fill = fill
        for col_idx in range(1, 4):
            ws.cell(row=row_num, column=col_idx).font = Font(name="Arial")

    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 40
    ws.freeze_panes = "A2"

    file_path = f"{key}_{uuid.uuid4().hex[:6]}.xlsx"
    wb.save(file_path)

    btn_clear = InlineKeyboardButton("Clear", callback_data=f"adm_clear_dump:{key}")
    _style(btn_clear, 'danger')
    kb = InlineKeyboardMarkup([[btn_clear]])

    with open(file_path, "rb") as f:
        await bot.send_document(
            chat_id=chat_id,
            document=f,
            filename=f"{cat_label}_{type_label}_Submissions.xlsx",
            caption=f"📄 মোট {len(dump_list)} টি {label} সাবমিশন।\n\n🗑️ নিচের Clear বাটনে চাপলে এই ডাটা বট থেকে মুছে যাবে এবং নতুন করে জমা হওয়া শুরু হবে।",
            reply_markup=kb
        )
    os.remove(file_path)


def build_2fa_code_message(current_code: str, remaining: int):
    """🔑/❤️/⏱ প্রিমিয়াম ইমোজি সহ 2FA কোড মেসেজ বানায় (initial দেখানো ও Refresh — দুই
    জায়গা থেকেই এই একই ফাংশন ব্যবহার হয়)।"""
    text = (
        f"╔══════════╗\n"
        f"🔑 Your 2FA Code\n"
        f"╚══════════╝\n\n"
        f"❤️ Code : {current_code}\n\n"
        f"⏱ Valid : {remaining}s\n"
        f"━━━━━━━━━━"
    )
    entities = build_custom_emoji_entities(text, [
        ("🔑", "5307843983102204243"),
        ("❤️", "5854971972789736369"),
        ("⏱", "6068846225845653889"),
    ])
    code_entity = build_code_entity(text, current_code)
    if code_entity:
        entities.append(code_entity)
    return text, entities


async def admin_process_report_uids(bot, admin_chat_id: int, identifier_list: list, approve: bool):
    """
    এডমিন যা পাঠায় (Facebook UID অথবা Instagram username — যেটাই হোক, একটা
    করে প্রতি লাইনে) তার সাথে pending সাবমিশনগুলোর fb_uid/login মিলিয়ে
    বট নিজেই বের করে এটা কোন Telegram ইউজারের সাবমিশন, তারপর সেটা bulk
    approve/reject করে, ব্যালেন্স/কাউন্ট আপডেট করে, এবং ইউজারকে নোটিফাই করে।
    """
    processed = []      # [(identifier, telegram_user_id, price_credited_or_None), ...]
    not_found = []
    with _lock:
        d = _load()
        subs = d.get("submissions", {})
        for raw_ident in identifier_list:
            ident = raw_ident.strip()
            if not ident:
                continue

            matches = [
                s for s in subs.values()
                if s.get("status") == "pending" and (
                    (s.get("category") == "facebook" and str(s.get("fb_uid", "")).strip() == ident)
                    or (s.get("category") != "facebook" and str(s.get("login", "")).strip().lower() == ident.lower())
                )
            ]
            if not matches:
                not_found.append(ident)
                continue

            # একই UID/Username-এর একাধিক pending সাবমিশন থাকলেও (যেমন টেস্ট করার
            # সময় বারবার একই ডাটা দিয়ে সাবমিট করা হলে) একটা UID দিলে শুধু
            # সবচেয়ে পুরনো একটা সাবমিশনই process হবে — সবগুলো না।
            s_rec = matches[0]
            uid = str(s_rec["user_id"])
            if uid not in d.get("users", {}):
                d.setdefault("users", {})[uid] = {
                    "user_id": s_rec["user_id"], "username": s_rec.get("username", ""), "balance": 0.0,
                    "language": "bn", "success_count": 0, "review_count": 0, "rejected_count": 0,
                }
            p_add = None
            if approve:
                s_rec["status"] = "approved"
                t_info = d.get("dynamic_tasks", {}).get(s_rec.get("task_id"), {})
                p_add = t_info.get("price", 3.5)
                d["users"][uid]["balance"] = round(d["users"][uid].get("balance", 0.0) + p_add, 2)
                d["users"][uid]["success_count"] = d["users"][uid].get("success_count", 0) + 1
            else:
                s_rec["status"] = "rejected"
                d["users"][uid]["rejected_count"] = d["users"][uid].get("rejected_count", 0) + 1
            d["users"][uid]["review_count"] = max(0, d["users"][uid].get("review_count", 0) - 1)
            processed.append((ident, uid, p_add))
        _save(d)
        users_snapshot = d.get("users", {})

    for ident, uid, p_add in processed:
        u_lang = users_snapshot.get(uid, {}).get("language", "bn")
        if approve:
            if u_lang == "bn":
                u_msg = f"✅ রিপোর্ট গৃহীত হয়েছে!\n💰৳{p_add:.2f} ব্যালেন্সে যোগ হয়েছে।"
            else:
                u_msg = f"✅ Your report has been approved!\n💰৳{p_add:.2f} Balance credited."
        else:
            u_msg = "❌ আপনার রিপোর্টটি বাতিল করা হয়েছে 🥹" if u_lang == "bn" else "❌ Your Report Has Been Rejected 🥹"
        try:
            await bot.send_message(chat_id=int(uid), text=u_msg)
        except Exception:
            pass

    status_word = "Approve" if approve else "Reject"
    summary = (
        f"✅ প্রসেস সম্পন্ন!\n\n"
        f"{status_word} হয়েছে: {len(processed)} টি\n"
        f"খুঁজে পাওয়া যায়নি / pending নেই: {len(not_found)} টি"
    )
    if not_found:
        summary += "\n\n❌ Not found: " + ", ".join(not_found[:20])
    await bot.send_message(chat_id=admin_chat_id, text=summary)

# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return

    # /start-এর সময় ব্যবহারকারীর saved language আগে বের করতে হবে।
    # আগে এখানে `lang` define না থাকায় NameError হয়ে start handler কাজ করছিল না।
    user_profile = get_or_create_user(user.id, user.username or "")
    lang = user_profile.get("language", "bn")
    if lang not in LANGUAGES:
        lang = "bn"

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

    # Admin Panel বাটনটা এখন থেকে নিচের keyboard মেনুতে না রেখে, মেসেজের
    # নিচে একটা ইনলাইন বাটন হিসেবে আলাদাভাবে পাঠানো হচ্ছে।
    if user.id == ADMIN_ID:
        btn_admin_inline = InlineKeyboardButton("Admin Panel", callback_data="open_admin_panel")
        _style(btn_admin_inline, 'danger')
        await update.message.reply_text(
            "👨‍💼 Admin Access:",
            reply_markup=InlineKeyboardMarkup([[btn_admin_inline]])
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message or not update.message.text:
        return  # চ্যানেল পোস্ট বা অস্বাভাবিক আপডেট হলে চুপচাপ স্কিপ করো
    user_id = update.effective_user.id
    text = _restore_button_text(update.message.text.strip())
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, update.effective_user.username or "")
    lang = user_profile.get("language", "bn")
    ln = LANGUAGES[lang]

    if not await is_user_joined_all(context.bot, user_id):
        await update.message.reply_text(ln["force_join_msg"], reply_markup=get_force_join_keyboard(lang))
        return
    
    if text == "HOW TO GET 2FA?":
        vid_msg = "📹 2FA সেটআপ করার ভিডিও লিংক:\n\nhttps://t.me/range_channele/955" if lang == "bn" else "📹 How to setup 2FA Video Link:\n\nhttps://t.me/range_channele/955"
        await update.message.reply_text(vid_msg)
        return

    # --------------------------------------------------------
    # ADMIN FLOWS
    # --------------------------------------------------------

    # আগে থেকে কোনো step আটকে থাকলেও (যেমন Add Task/Add Money মাঝপথে
    # ছেড়ে দেওয়া) ADMIN PANEL বাটন চাপলে সবসময় সরাসরি প্যানেলে ফিরিয়ে
    # আনার জন্য এই চেকটা সবার আগে রাখা হলো। আগে এটা অনেক নিচে থাকায়
    # stuck state থাকলে বাটনটা কাজ করতো না।
    if text in ["ADMIN PANEL", "🛠️ ADMIN PANEL", "🛠️ ENDMIN PANEL", "🛠️ এডমিন প্যানেল", "এডমিন প্যানেল"] and user_id == ADMIN_ID:
        USER_STATE.pop(user_id, None)

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_change_password":
        USER_STATE.pop(user_id, None)
        with _lock:
            data = _load()
            data["task_password"] = text
            _save(data)
        await update.message.reply_text(f"🔐 সফলভাবে নতুন পাসওয়ার্ড সেভ করা হয়েছে!\nবর্তমান পাসওয়ার্ড: `{text}`", parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id, lang))
        return
    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "waiting_report_txt":
        state = USER_STATE[user_id]
        if text == ln["btn_cancel"] or text.lower() in ("cancel", "❌ cancel", "🚫 cancel", "বাতিল"):
            USER_STATE.pop(user_id, None)
            await update.message.reply_text("🚫 বাতিল করা হয়েছে।", reply_markup=main_menu_keyboard(user_id, lang))
            return
        identifier_list = [line.strip() for line in text.splitlines() if line.strip()]
        if not identifier_list:
            await update.message.reply_text("❌ কোনো UID/Username পাওয়া যায়নি, আবার পাঠান।")
            return
        approve = state.get("report_mode") == "approve"
        await update.message.reply_text(f"⏳ {len(identifier_list)} টি প্রসেস করা হচ্ছে...")
        await admin_process_report_uids(context.bot, user_id, identifier_list, approve)
        mode_label = "Success" if approve else "Rejected"
        btn_done = InlineKeyboardButton("শেষ (Done)", callback_data="adm_report_cancel")
        _style(btn_done, 'danger')
        await update.message.reply_text(
            f"📤 আরও {mode_label} UID/Username পাঠাতে পারেন, অথবা শেষ হলে নিচের বাটনে চাপুন।",
            reply_markup=InlineKeyboardMarkup([[btn_done]])
        )
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

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "add_task_button_name":
        button_name = text.strip()
        
        if not button_name:
            await update.message.reply_text("❌ বাটনের নাম খালি থাকতে পারে না!")
            return
        
        USER_STATE[user_id]["task_name"] = button_name
        USER_STATE[user_id]["step"] = "select_category_for_task"
        
        btn_ig = InlineKeyboardButton("Instagram", callback_data="adm_cat:instagram:")
        btn_fb = InlineKeyboardButton("Facebook", callback_data="adm_cat:facebook:")
        btn_cancel = InlineKeyboardButton("Cancel", callback_data="cancel_add_task")

        _style(btn_ig, 'primary')
        _style(btn_fb, 'success')
        _style(btn_cancel, 'danger')

        kb = InlineKeyboardMarkup([[btn_ig, btn_fb], [btn_cancel]])
        await update.message.reply_text(f"📌 বাটন নাম: {button_name}\n\nকোন ক্যাটাগরিতে যুক্ত করবেন?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and USER_STATE.get(user_id, {}).get("step") == "admin_task_name":
        if "selected_task_name" in USER_STATE[user_id]:
            try:
                price = float(text)
                USER_STATE[user_id]["task_price"] = price
                USER_STATE[user_id]["step"] = "admin_task_rules"
                await update.message.reply_text("📝 টাস্কের নিয়মাবলী (Rules) লিখুন:")
            except:
                await update.message.reply_text("❌ সঠিক সংখ্যা বা ডেসিমাল অ্যামাউন্ট দিন।")
        else:
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
        
        btn_c_work = InlineKeyboardButton("Cookies Work", callback_data="adm_t_type:cookies")
        btn_2_work = InlineKeyboardButton("2FA Work", callback_data="adm_t_type:2fa")
        
        _style(btn_c_work, 'success')
        _style(btn_2_work, 'primary')
        
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
            method = USER_STATE[user_id]["method"]
            num = USER_STATE[user_id]["number"]

            if amt < 50:
                await update.message.reply_text("❌ সর্বনিম্ন উত্তোলন ৳50" if lang == "bn" else "❌ Minimum withdraw is ৳50")
                USER_STATE.pop(user_id, None)
                return
            if amt > user_profile["balance"]:
                await update.message.reply_text(ln["insufficient"])
                USER_STATE.pop(user_id, None)
                return

            charge = 5
            receive = round(amt - charge, 2)

            USER_STATE[user_id]["amt"] = amt
            USER_STATE[user_id]["receive"] = receive

            icon = "🟡" if method == "Binance" else "📱"
            if lang == "bn":
                label = "Binance UID" if method == "Binance" else "নম্বর"
                confirm_text = (
                    f"📋 দয়া করে আপনার তথ্য যাচাই করুন\n\n"
                    f"{icon} {label}: {num}\n"
                    f"💳 মাধ্যম: {method}\n"
                    f"💵 পরিমাণ: ৳{amt}\n"
                    f"💳 চার্জ: ৳{charge}\n"
                    f"✅ আপনি পাবেন: ৳{receive}\n\n"
                    f"✅ সব তথ্য ঠিক থাকলে নিচের Confirm বাটনে চাপুন। 👇"
                )
            else:
                label = "Binance UID" if method == "Binance" else "Number"
                confirm_text = (
                    f"📋 Please Check Your Info\n\n"
                    f"{icon} {label}: {num}\n"
                    f"💳 Method: {method}\n"
                    f"💵 Amount: ৳{amt}\n"
                    f"💳 Fee: ৳{charge}\n"
                    f"✅ Receive: ৳{receive}\n\n"
                    f"✅ If All Information Is Correct, Please Tap the Confirm Button. 👇"
                )
            
            btn_cnf = KeyboardButton(ln["btn_confirm"])
            btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
            _style(btn_cnf, 'success')
            _style(btn_cnc, 'danger')
            
            kb = ReplyKeyboardMarkup([[btn_cnf, btn_cnc]], resize_keyboard=True)
            USER_STATE[user_id]["step"] = "withdraw_confirm"
            await update.message.reply_text(confirm_text, reply_markup=kb)
        except:
            await update.message.reply_text("❌ ভুল ফরম্যাট।" if lang == "bn" else "❌ Invalid format.")
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
            
            btn_w_ap = InlineKeyboardButton("APPROVE", callback_data=f"w_app:{w_id}")
            btn_w_rj = InlineKeyboardButton("REJECT", callback_data=f"w_rej:{w_id}")
            _style(btn_w_ap, 'success')
            _style(btn_w_rj, 'danger')
            
            admin_kb = InlineKeyboardMarkup([[btn_w_ap, btn_w_rj]])
            label = "Binance UID" if state["method"] == "Binance" else "Number"
            admin_text = (
                f"💸 New Payment Request\n\n"
                f"👤 User: @{user_profile['username']}\n🆔 UID: {user_id}\n"
                f"{'🟡' if state['method'] == 'Binance' else '📱'} {label}: {state['number']}\n"
                f"💳 Method: {state['method']}\n"
                f"💵 Amount: ৳{state['amt']}\n"
                f"✅ Send: ৳{state.get('receive', '')}"
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                reply_markup=admin_kb
            )
        else:
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
        USER_STATE.pop(user_id, None)
        return

    # --- FACEBOOK UID SUBMISSION ---
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_fb_uid":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            USER_STATE.pop(user_id, None)
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            return
        USER_STATE[user_id]["fb_uid"] = text
        state = USER_STATE[user_id]

        if state.get("task_type") == "2fa":
            state["step"] = "waiting_for_2fa"
            btn_2fa = KeyboardButton(ln["btn_how_to_2fa"])
            btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
            _style(btn_2fa, 'primary')
            _style(btn_cnc, 'danger')
            task_2fa_kb = ReplyKeyboardMarkup([[btn_2fa], [btn_cnc]], resize_keyboard=True)
            await update.message.reply_text(ln["send_2fa_secret"], reply_markup=task_2fa_kb)
        else:
            state["step"] = "waiting_for_cookies"
            btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
            _style(btn_cnc, 'danger')
            await update.message.reply_text(ln["send_cookies"], reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
        return

    # --- COOKIES SUBMISSION ---
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_cookies":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            USER_STATE.pop(user_id, None)
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            return
        if len(text.strip()) < 100:
            await update.message.reply_text("❌ কুকি অনেক ছোট (সর্বনিম্ন ১০০ ক্যারেক্টার লাগবে)। সঠিক কুকি ডেটা দিন।" if lang == "bn" else "❌ Cookie is too short (minimum 100 characters). Please provide valid cookie data.")
            return
        USER_STATE[user_id]["cookies_data"] = text
        USER_STATE[user_id]["step"] = "cookies_submitted"
        
        btn_reg = KeyboardButton(ln["btn_acc_reg"], icon_custom_emoji_id="6239913824057563150")
        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
        _style(btn_reg, 'success')
        _style(btn_cnc, 'danger')
        
        kb = ReplyKeyboardMarkup([[btn_reg], [btn_cnc]], resize_keyboard=True)
        await update.message.reply_text(ln["cookies_rec"], reply_markup=kb)
        return

    if text == ln["btn_acc_reg"]:
        state = USER_STATE.get(user_id)
        if state and (state.get("step") == "cookies_submitted" or state.get("step") == "2fa_verify"):
            btn_sub = KeyboardButton(ln["btn_subbed"], icon_custom_emoji_id="5215492745900077682")
            btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
            _style(btn_sub, 'success')
            _style(btn_cnc, 'danger')
            
            kb = ReplyKeyboardMarkup([[btn_sub], [btn_cnc]], resize_keyboard=True)
            if state.get("step") == "cookies_submitted":
                await update.message.reply_text(ln["invite_check"], reply_markup=kb)
                USER_STATE[user_id]["step"] = "cookies_final_confirm"
                cred_msg_id = state.get("cred_msg_id")
                if cred_msg_id:
                    try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=cred_msg_id)
                    except: pass
            else:
                await update.message.reply_text(ln["invite_check_short"], reply_markup=kb)
                USER_STATE[user_id]["step"] = "2fa_final_confirm"
                cred_msg_id = state.get("cred_msg_id")
                if cred_msg_id:
                    try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=cred_msg_id)
                    except: pass
            return

    if text == ln["btn_subbed"]:
        state = USER_STATE.get(user_id)
        if state and state.get("step") == "2fa_final_confirm":
            sub_id = str(uuid.uuid4())[:8]

            with _lock:
                d = _load()
                d["submissions"][sub_id] = {
                    "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                    "task_type": "2fa", "task_id": state.get("task_id"), "login": state['login'], "fb_uid": state.get("fb_uid", ""), "category": state.get("cat"), "status": "pending"
                }
                d["users"][str(user_id)]["review_count"] += 1
                _save(d)

            dump_entry = {
                "uid": state.get("fb_uid", "") if state.get("cat") == "facebook" else state.get("login", ""),
                "password": state.get('pass', ''),
                "data": state.get('secret', '')
            }
            add_to_id_dump(state.get("cat", "instagram"), "2fa", dump_entry)

            await update.message.reply_text(ln["report_received"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

        if state and state.get("step") == "cookies_final_confirm":
            sub_id = str(uuid.uuid4())[:8]

            with _lock:
                data = _load()
                data["submissions"][sub_id] = {
                    "sub_id": sub_id, "user_id": user_id, "username": user_profile["username"],
                    "task_type": "cookies", "task_id": state.get("task_id"), "login": state['login'], "fb_uid": state.get("fb_uid", ""), "category": state.get("cat"), "status": "pending"
                }
                data["users"][str(user_id)]["review_count"] += 1
                _save(data)

            dump_entry = {
                "uid": state.get("fb_uid", "") if state.get("cat") == "facebook" else state.get("login", ""),
                "password": state.get('pass', ''),
                "data": state.get('cookies_data', '')
            }
            add_to_id_dump(state.get("cat", "instagram"), "cookies", dump_entry)

            await update.message.reply_text(ln["report_received"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return

    # --- 2FA SECRET KEY SUBMISSION ---
    if USER_STATE.get(user_id, {}).get("step") == "waiting_for_2fa":
        if text == ln["btn_cancel"] or text.lower() == "cancel":
            await update.message.reply_text(ln["btn_cancel"], reply_markup=main_menu_keyboard(user_id, lang))
            USER_STATE.pop(user_id, None)
            return
        user_secret = text.replace(" ", "").upper()

        # আসল 2FA secret key শুধু A-Z আর 2-7 অক্ষর দিয়ে তৈরি হয় (base32),
        # আর সাধারণত ১৬-৬৪ ক্যারেক্টার লম্বা হয়। এর বাইরে কিছু হলে (0,1,8,9,
        # স্পেশাল ক্যারেক্টার, বা খুব ছোট/এলোমেলো টেক্সট) সেটা আসল secret
        # হতে পারে না — তাই সাথে সাথে বাতিল করে দেওয়া হচ্ছে।
        is_valid_format = (
            16 <= len(user_secret) <= 64
            and re.fullmatch(r"[A-Z2-7]+", user_secret) is not None
        )
        if not is_valid_format:
            await update.message.reply_text(ln["invalid_2fa"])
            return
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
        
        btn_reg = KeyboardButton(ln["btn_acc_reg"], icon_custom_emoji_id="6239913824057563150")
        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
        _style(btn_reg, 'success')
        _style(btn_cnc, 'danger')
        reg_kb = ReplyKeyboardMarkup([[btn_reg], [btn_cnc]], resize_keyboard=True)
        
        vmsg = "👉 2FA কি পাওয়া গেছে। এবার নিচের প্যানেল থেকে ভেরিফাই করে সাবমিট করুন।" if lang == "bn" else "👉 2FA Key Received. Now verify and submit using the panel below."
        await update.message.reply_text(vmsg, reply_markup=reg_kb)

        btn_ref = InlineKeyboardButton("Refresh", callback_data="refresh_2fa_code")
        _style(btn_ref, 'primary')
        inline_kb = InlineKeyboardMarkup([[btn_ref]])

        code_text, code_entities = build_2fa_code_message(current_code, remaining)
        msg = await update.message.reply_text(
            code_text,
            entities=code_entities,
            reply_markup=inline_kb
        )
        state["code_msg_id"] = msg.message_id
        return

    # --- MENU NAVIGATION ---
    if text in [ln["btn_report"], "YOUR REPORT", "📊 YOUR REPORT", "📊 আপনার রিপোর্ট"]:
        await update.message.reply_text(
            ln["report_msg"].format(s=user_profile.get('success_count', 0), r=user_profile.get('review_count', 0), rej=user_profile.get('rejected_count', 0)),
            reply_markup=main_menu_keyboard(user_id, lang)
        )
        return

    if text in [ln["btn_support"], "SUPPORT", "ℹ️ SUPPORT", "ℹ️ সাপোর্ট (SUPPORT)"]:
        btn_adm = InlineKeyboardButton("𓆩𓆩 𝗢𝗿𝗶𝘃𝗲𝘅 𝗔𝗱𝗺𝗶𝗻 𓆪𓆪", url="https://t.me/adim_shuvo")
        _style(btn_adm, 'primary')
        inline_kb = InlineKeyboardMarkup([[btn_adm]])
        support_text = "🛠️ Admin Support\n\n⚠️ Need help?\n💬 Contact Admin for quick support."
        await update.message.reply_text(support_text, reply_markup=inline_kb)
        return

    if text in [ln["btn_language"], "LANGUAGE", "🌐 LANGUAGE", "🌐 ভাষা (LANGUAGE)"]:
        btn_bn = InlineKeyboardButton("বাংলা", callback_data="lang_bn", icon_custom_emoji_id="5291824687096027834")
        btn_en = InlineKeyboardButton("English", callback_data="lang_en", icon_custom_emoji_id="5293993521026453119")
        _style(btn_bn, 'success')
        _style(btn_en, 'primary')
        
        kb = InlineKeyboardMarkup([[btn_bn, btn_en]])
        await update.message.reply_text(ln["select_lang"], reply_markup=kb)
        return

    if text in [ln["btn_tasks"], "TASK", "📋 TASKS", "📋 কাজ (TASKS)"]:
        btn_ig_cat = KeyboardButton(ln["cat_instagram"], icon_custom_emoji_id="6136285626233786941")
        btn_fb_cat = KeyboardButton(ln["cat_facebook"], icon_custom_emoji_id="5195004154170326693")
        btn_back = KeyboardButton(ln["btn_back"])

        _style(btn_ig_cat, 'primary')
        _style(btn_fb_cat, 'success')
        _style(btn_back, 'danger')

        vertical_keyboard = [
            [btn_ig_cat],
            [btn_fb_cat],
            [btn_back]
        ]

        await update.message.reply_text(
            ln["select_cat"],
            reply_markup=ReplyKeyboardMarkup(vertical_keyboard, resize_keyboard=True)
        )
        return

    _CAT_BUTTON_MAP = {
        "INSTAGRAM TASK": "instagram",
        "FACEBOOK TASK": "facebook",
        "ইনস্টাগ্রাম টাস্ক": "instagram",
        "ফেসবুক টাস্ক": "facebook",
        "😎 INSTAGRAM TASK": "instagram",
        "🧩 FACEBOOK TASK": "facebook",
        "😎 ইনস্টাগ্রাম টাস্ক": "instagram",
        "🧩 ফেসবুক টাস্ক": "facebook",
        # পুরনো টেক্সট (backward compatibility)
        "🔥𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗧𝗔𝗦𝗞": "instagram",
        "📘𝗙𝗔𝗖𝗘𝗕𝗢𝗢𝗞 𝗧𝗔𝗦𝗞": "facebook",
    }

    if text in _CAT_BUTTON_MAP:
        cat_key = _CAT_BUTTON_MAP[text]
        if not db_data["visibility"].get(f"{cat_key}_task", True) and user_id != ADMIN_ID:
            await update.message.reply_text(ln["task_hidden"])
            return
            
        active_tasks = [t for t in db_data.get("dynamic_tasks", {}).values() if t.get("category") == cat_key]
        if not active_tasks:
            await update.message.reply_text(ln["no_tasks"])
            return
            
        sub_tasks = []
        for t in active_tasks:
            btn_t = KeyboardButton(f"{t['name']} (৳{t['price']:.4f})")
            _style(btn_t, 'success')
            sub_tasks.append([btn_t])
            
        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
        _style(btn_cnc, 'danger')
        sub_tasks.append([btn_cnc])
        await update.message.reply_text(ln["choose_type"], reply_markup=ReplyKeyboardMarkup(sub_tasks, resize_keyboard=True))
        return

    all_tasks_for_match = db_data.get("dynamic_tasks", {})
    target_task = None
    for tid, t in all_tasks_for_match.items():
        label = f"{t['name']} (৳{t['price']:.4f})"
        if text.casefold() == label.casefold():
            target_task = t
            break

    if target_task:
        tid = target_task["id"]
        session_id = str(uuid.uuid4())
        USER_STATE[user_id] = {"task_id": tid, "task_type": target_task["type"], "cat": target_task.get("category"), "session_id": session_id}
        asyncio.create_task(task_timeout_watcher(context, user_id, update.effective_chat.id, session_id))

        btn_str = KeyboardButton(ln["btn_start"], icon_custom_emoji_id="5983495398788962050")
        btn_vid = KeyboardButton(ln["btn_video"], icon_custom_emoji_id="5217852272083477974")
        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")

        _style(btn_str, 'success')
        _style(btn_vid, 'primary')
        _style(btn_cnc, 'danger')

        kb = ReplyKeyboardMarkup([[btn_str], [btn_vid], [btn_cnc]], resize_keyboard=True)
        if lang == "bn":
            rules_label = "নিয়মাবলি:"
            tap_start_line = "🚀 শুরু করতে START বাটনে চাপুন।"
        else:
            rules_label = "Rules:"
            tap_start_line = "🚀 Tap START to continue."
        rules_msg = f"⭐️🛡  {target_task['name']}\n\n💵 Payout: ৳{target_task['price']:.4f}\n\n📝 {rules_label}\n{target_task['rules']}\n\n{tap_start_line}"
        rules_entities = build_custom_emoji_entities(rules_msg, [
            ("⭐️", "5127861690641156032"),
            ("🛡", "6174589325695521740"),
            ("💵", "6206155797722830770"),
            ("📝", "5215672443036772796"),
            ("🚀", "6068700050928704109"),
        ])
        bold_name = build_bold_entity(rules_msg, target_task['name'])
        bold_rules = build_bold_entity(rules_msg, rules_label)
        for be in (bold_name, bold_rules):
            if be:
                rules_entities.append(be)
        await update.message.reply_text(rules_msg, entities=rules_entities, reply_markup=kb)
        return

    if text == ln["btn_video"] or text == "🎥 ভিডিও দেখুন":
        state = USER_STATE.get(user_id, {})
        task_id = state.get("task_id")
        t_data = db_data.get("dynamic_tasks", {}).get(task_id) if task_id else None
        if t_data and t_data.get("video_file_id"):
            cap = f"🎥 {t_data['name']} — কীভাবে কাজটি করবেন" if lang == "bn" else f"🎥 {t_data['name']} — How to complete this task"
            await update.message.reply_video(video=t_data["video_file_id"], caption=cap)
        else:
            await update.message.reply_text("❌ এই টাস্কের জন্য এখনো কোনো ভিডিও যুক্ত করা হয়নি।" if lang == "bn" else "❌ No video has been assigned to this task yet.")
        return

    if text == ln["btn_start"]:
        state = USER_STATE.get(user_id)
        if state and "task_id" in state:
            t_data = db_data["dynamic_tasks"].get(state["task_id"])
            if t_data:
                task_cat = state.get("cat", "instagram")
                f_name, login_name = generate_profile_or_get_saved(task_category=task_cat)
                
                if login_name is None and task_cat == "instagram":
                    await update.message.reply_text(ln["no_usernames_err"])
                    return
                    
                pass_val = db_data.get("task_password", "shuvo9")
                state["login"] = login_name
                state["pass"] = pass_val
                state["f_name"] = f_name
                state["t_name"] = t_data["name"]
                
                if lang == "bn":
                    lbl_first_name, lbl_login, lbl_password, lbl_use_info = "নামঃ", "লগইনঃ", "পাসওয়ার্ডঃ", "তথ্যগুলো ব্যবহার করুন"
                else:
                    lbl_first_name, lbl_login, lbl_password, lbl_use_info = "First name:", "Login:", "Password:", "Use information"

                if task_cat == "facebook":
                    mono_msg = (
                        f"✅ {lbl_first_name} {f_name}\n\n"
                        f"📱 {lbl_password} {pass_val}\n\n"
                        f"✅ {lbl_use_info} ⬆️"
                    )
                else:
                    mono_msg = (
                        f"✅ {lbl_first_name} {f_name}\n\n"
                        f"📱 {lbl_login} {login_name}\n\n"
                        f"📱 {lbl_password} {pass_val}\n\n"
                        f"✅ {lbl_use_info} ⬆️"
                    )

                cred_entities = build_custom_emoji_entities(mono_msg, (
                    [("✅", "6206185428702206246"), ("📱", "5848177124074066676")]
                    + ([("📱", "5848177124074066676")] if task_cat != "facebook" else [])
                    + [("✅", "6206294254583551886"), ("⬆️", "5470143839371021696")]
                ))
                name_entity = build_code_entity(mono_msg, f_name)
                if name_entity:
                    cred_entities.append(name_entity)
                if task_cat != "facebook":
                    login_entity = build_code_entity(mono_msg, login_name)
                    if login_entity:
                        cred_entities.append(login_entity)
                pass_entity = build_code_entity(mono_msg, pass_val)
                if pass_entity:
                    cred_entities.append(pass_entity)

                cred_msg = await update.message.reply_text(mono_msg, entities=cred_entities)
                state["cred_msg_id"] = cred_msg.message_id
                
                if task_cat == "facebook":
                    state["step"] = "waiting_for_fb_uid"
                    btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
                    _style(btn_cnc, 'danger')
                    await update.message.reply_text(ln["send_fb_uid"], reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
                else:
                    if state["task_type"] == "2fa":
                        state["step"] = "waiting_for_2fa"
                        btn_2fa = KeyboardButton(ln["btn_how_to_2fa"])
                        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
                        _style(btn_2fa, 'primary')
                        _style(btn_cnc, 'danger')
                        task_2fa_kb = ReplyKeyboardMarkup([[btn_2fa], [btn_cnc]], resize_keyboard=True)
                        await update.message.reply_text(ln["send_2fa_secret"], reply_markup=task_2fa_kb)
                    else:
                        state["step"] = "waiting_for_cookies"
                        btn_cnc = KeyboardButton(ln["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
                        _style(btn_cnc, 'danger')
                        await update.message.reply_text(ln["send_cookies"], reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
            return

    if text in [ln["btn_withdraw"], "WITHDRAW", "📤 WITHDRAW", "📤 টাকা তুলুন"]:
        bal = user_profile["balance"]
        btn_wth = InlineKeyboardButton("Withdraw", callback_data="start_withdraw")
        _style(btn_wth, 'success')
        inline_wb = InlineKeyboardMarkup([[btn_wth]])
        await update.message.reply_text(ln["withdraw_dash"].format(bal=bal, rec=max(0.0, bal - 5)), reply_markup=inline_wb)
        return

    # --- ADMIN CONTROL DASHBOARD PANEL ---
    if text in ["ADMIN PANEL", "🛠️ ADMIN PANEL", "🛠️ ENDMIN PANEL", "🛠️ এডমিন প্যানেল", "এডমিন প্যানেল"] and user_id == ADMIN_ID:
        await send_admin_dashboard(context.bot, user_id, lang)
        return

    if user_id == ADMIN_ID and text == "PASSWORD CHANGE":
        USER_STATE[user_id] = {"step": "admin_change_password"}
        current_pwd = db_data.get("task_password", "shuvo9")
        await update.message.reply_text(f"🔐 বর্তমান টাস্ক পাসওয়ার্ড: `{current_pwd}`\n\nনতুন যে পাসওয়ার্ডটি সেট করতে চান তা লিখে পাঠান:", parse_mode="Markdown")
        return

    if user_id == ADMIN_ID and text == "DELETE TASK":
        btn_del_ig = InlineKeyboardButton("Instagram Tasks", callback_data="adm_del_cat:instagram")
        btn_del_fb = InlineKeyboardButton("Facebook Tasks", callback_data="adm_del_cat:facebook")
        _style(btn_del_ig, 'danger')
        _style(btn_del_fb, 'danger')
        kb = InlineKeyboardMarkup([[btn_del_ig, btn_del_fb]])
        await update.message.reply_text("🗑️ কোন ক্যাটাগরির কাজ ডিলিট করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "WORK VIDEO":
        btn_vid_ig = InlineKeyboardButton("Instagram Tasks", callback_data="adm_vid_cat:instagram")
        btn_vid_fb = InlineKeyboardButton("Facebook Tasks", callback_data="adm_vid_cat:facebook")
        _style(btn_vid_ig, 'primary')
        _style(btn_vid_fb, 'primary')

        kb = InlineKeyboardMarkup([[btn_vid_ig, btn_vid_fb]])
        await update.message.reply_text("🎥 কোন ক্যাটাগরির টাস্কের ভিডিও সেট করতে চান?", reply_markup=kb)
        return

    if user_id == ADMIN_ID and text == "USERNAME SAVE":
        USER_STATE[user_id] = {"step": "admin_save_username"}
        await update.message.reply_text("📥 আপনি যে ইউজারনেমগুলো সেভ করে রাখতে চান সেগুলো পাঠান:\n(একাধিক ইউজারনেম স্পেস বা কমা দিয়ে একসাথে পাঠাতে পারেন)")
        return

    if user_id == ADMIN_ID and text == "ADD TASK":
        USER_STATE[user_id] = {"step": "add_task_button_name"}
        btn_cancel_name = InlineKeyboardButton("Cancel", callback_data="cancel_add_task")
        _style(btn_cancel_name, 'danger')
        await update.message.reply_text(
            "📝 বাটনের একটি সুন্দর নাম দিন:\n\nউদাহরণ: Like 50 Posts, Share 5 Posts, Follow Account, ইত্যাদি",
            reply_markup=InlineKeyboardMarkup([[btn_cancel_name]])
        )
        return

    if user_id == ADMIN_ID and text == "USER BROADCAST":
        USER_STATE[user_id] = {"step": "broadcast_msg"}
        await update.message.reply_text("📢 Send the message you wish to broadcast to all users:")
        return

    if user_id == ADMIN_ID and text == "ADD MONEY":
        USER_STATE[user_id] = {"step": "add_money_uid"}
        await update.message.reply_text("👤 Send the target User identification (UID) number:")
        return

    if user_id == ADMIN_ID and text == "ALL REPORT":
        btn_success = InlineKeyboardButton("Success", callback_data="adm_report_success")
        btn_rejected = InlineKeyboardButton("Rejected", callback_data="adm_report_rejected")
        btn_cancel_rep = InlineKeyboardButton("Cancel", callback_data="adm_report_cancel")
        _style(btn_success, 'success')
        _style(btn_rejected, 'danger')
        _style(btn_cancel_rep, 'danger')
        kb = InlineKeyboardMarkup([[btn_success, btn_rejected], [btn_cancel_rep]])
        await update.message.reply_text("🗂️ কোন লিস্ট আপলোড করবেন?", reply_markup=kb)
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

async def task_timeout_watcher(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, session_id: str, delay: int = 600):
    """
    কোনো ইউজার একটা টাস্ক শুরু করার পর নির্দিষ্ট সময়ের (ডিফল্ট ১০ মিনিট)
    মধ্যে সম্পূর্ণ না করলে টাস্কটা স্বয়ংক্রিয়ভাবে বাতিল করে দেয়, আর
    "Return to main menu" বাটন সহ একটা টাইমআউট মেসেজ পাঠায়।
    """
    await asyncio.sleep(delay)
    current_state = USER_STATE.get(user_id, {})
    if current_state.get("session_id") != session_id:
        return  # ইউজার ইতিমধ্যে টাস্ক শেষ করেছে/বাতিল করেছে/অন্য কিছুতে চলে গেছে
    USER_STATE.pop(user_id, None)
    btn_ret = KeyboardButton("Return to main menu")
    kb = ReplyKeyboardMarkup([[btn_ret]], resize_keyboard=True)
    try:
        await context.bot.send_message(chat_id=chat_id, text="🕐 Time's up! Task cancelled.❌", reply_markup=kb)
    except Exception:
        pass

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    user_id = query.from_user.id
    data = query.data
    
    db_data = _load()
    user_profile = get_or_create_user(user_id, query.from_user.username or "")
    lang = user_profile.get("language", "bn")
    ln = LANGUAGES[lang]

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
                
                btn_ref = InlineKeyboardButton("Refresh", callback_data="refresh_2fa_code")
                _style(btn_ref, 'primary')
                inline_kb = InlineKeyboardMarkup([[btn_ref]])

                code_text, code_entities = build_2fa_code_message(current_code, remaining)
                await query.edit_message_text(
                    code_text,
                    entities=code_entities,
                    reply_markup=inline_kb
                )
            except:
                pass
        return

    if data == "cancel_add_task":
        USER_STATE.pop(user_id, None)
        await query.edit_message_text("❌ বাতিল করা হয়েছে। Admin Panel-এ ফিরে গেছেন।")
        return

    if data == "open_admin_panel":
        if user_id != ADMIN_ID:
            return
        await send_admin_dashboard(context.bot, user_id, lang)
        return

    if user_id == ADMIN_ID and data in [
        "adm_add_task", "adm_delete_task", "adm_broadcast", "adm_add_money",
        "adm_username_save", "adm_all_report", "adm_password_change",
        "adm_work_video", "adm_all_task_file", "adm_pending_uids", "adm_reset_balances", "adm_back",
    ]:
        if data == "adm_add_task":
            USER_STATE[user_id] = {"step": "add_task_button_name"}
            btn_cancel_name = InlineKeyboardButton("Cancel", callback_data="cancel_add_task")
            _style(btn_cancel_name, 'danger')
            await query.message.reply_text(
                "📝 বাটনের একটি সুন্দর নাম দিন:\n\nউদাহরণ: Like 50 Posts, Share 5 Posts, Follow Account, ইত্যাদি",
                reply_markup=InlineKeyboardMarkup([[btn_cancel_name]])
            )

        elif data == "adm_delete_task":
            btn_del_ig = InlineKeyboardButton("Instagram Tasks", callback_data="adm_del_cat:instagram")
            btn_del_fb = InlineKeyboardButton("Facebook Tasks", callback_data="adm_del_cat:facebook")
            _style(btn_del_ig, 'danger')
            _style(btn_del_fb, 'danger')
            kb = InlineKeyboardMarkup([[btn_del_ig, btn_del_fb]])
            await query.message.reply_text("🗑️ কোন ক্যাটাগরির কাজ ডিলিট করতে চান?", reply_markup=kb)

        elif data == "adm_broadcast":
            USER_STATE[user_id] = {"step": "broadcast_msg"}
            await query.message.reply_text("📢 Send the message you wish to broadcast to all users:")

        elif data == "adm_add_money":
            USER_STATE[user_id] = {"step": "add_money_uid"}
            await query.message.reply_text("👤 Send the target User identification (UID) number:")

        elif data == "adm_username_save":
            USER_STATE[user_id] = {"step": "admin_save_username"}
            await query.message.reply_text("📥 আপনি যে ইউজারনেমগুলো সেভ করে রাখতে চান সেগুলো পাঠান:\n(একাধিক ইউজারনেম স্পেস বা কমা দিয়ে একসাথে পাঠাতে পারেন)")

        elif data == "adm_all_report":
            btn_success = InlineKeyboardButton("Success", callback_data="adm_report_success")
            btn_rejected = InlineKeyboardButton("Rejected", callback_data="adm_report_rejected")
            btn_cancel_rep = InlineKeyboardButton("Cancel", callback_data="adm_report_cancel")
            _style(btn_success, 'success')
            _style(btn_rejected, 'danger')
            _style(btn_cancel_rep, 'danger')
            kb = InlineKeyboardMarkup([[btn_success, btn_rejected], [btn_cancel_rep]])
            await query.message.reply_text("🗂️ কোন লিস্ট আপলোড করবেন?", reply_markup=kb)

        elif data == "adm_password_change":
            USER_STATE[user_id] = {"step": "admin_change_password"}
            current_pwd = db_data.get("task_password", "shuvo9")
            await query.message.reply_text(f"🔐 বর্তমান টাস্ক পাসওয়ার্ড: `{current_pwd}`\n\nনতুন যে পাসওয়ার্ডটি সেট করতে চান তা লিখে পাঠান:", parse_mode="Markdown")

        elif data == "adm_work_video":
            btn_vid_ig = InlineKeyboardButton("Instagram Tasks", callback_data="adm_vid_cat:instagram")
            btn_vid_fb = InlineKeyboardButton("Facebook Tasks", callback_data="adm_vid_cat:facebook")
            _style(btn_vid_ig, 'primary')
            _style(btn_vid_fb, 'primary')
            kb = InlineKeyboardMarkup([[btn_vid_ig, btn_vid_fb]])
            await query.message.reply_text("🎥 কোন ক্যাটাগরির টাস্কের ভিডিও সেট করতে চান?", reply_markup=kb)

        elif data == "adm_all_task_file":
            fb_c = len(db_data.get("fb_cookies_dump", []))
            fb_2 = len(db_data.get("fb_2fa_dump", []))
            ig_c = len(db_data.get("ig_cookies_dump", []))
            ig_2 = len(db_data.get("ig_2fa_dump", []))
            btn_fb_c = InlineKeyboardButton(f"Facebook Cookies: {fb_c:02d}", callback_data="adm_file:fb:cookies")
            btn_fb_2 = InlineKeyboardButton(f"Facebook 2FA: {fb_2:02d}", callback_data="adm_file:fb:2fa")
            btn_ig_c = InlineKeyboardButton(f"Instagram Cookies: {ig_c:02d}", callback_data="adm_file:ig:cookies")
            btn_ig_2 = InlineKeyboardButton(f"Instagram 2FA: {ig_2:02d}", callback_data="adm_file:ig:2fa")
            for b in (btn_fb_c, btn_fb_2, btn_ig_c, btn_ig_2):
                _style(b, 'primary')
            kb = InlineKeyboardMarkup([[btn_fb_c], [btn_fb_2], [btn_ig_c], [btn_ig_2]])
            await query.message.reply_text("🗃️ কোন ফাইল দেখতে চান?", reply_markup=kb)

        elif data == "adm_pending_uids":
            pending_subs = [s for s in db_data["submissions"].values() if s["status"] == "pending"]
            if not pending_subs:
                await query.message.reply_text("✅ এই মুহূর্তে কোনো pending সাবমিশন নেই।")
            else:
                lines = ["📋 Pending Submissions:\n(Success/Rejected-এ এই UID/Username গুলো ব্যবহার করুন)\n"]
                for s in pending_subs:
                    t_type = "2FA" if s.get("task_type") == "2fa" else "Cookies"
                    if s.get("category") == "facebook":
                        ident = s.get("fb_uid", "N/A")
                        lines.append(f"📘 Facebook UID: {ident}  |  Telegram: {s['user_id']}  |  {t_type}")
                    else:
                        ident = s.get("login", "N/A")
                        lines.append(f"📷 Instagram Username: {ident}  |  Telegram: {s['user_id']}  |  {t_type}")
                text_out = "\n".join(lines)
                # টেলিগ্রাম মেসেজ লিমিটের (৪০৯৬) মধ্যে রাখার জন্য প্রয়োজনে ভাগ করে পাঠানো হচ্ছে
                for i in range(0, len(text_out), 3800):
                    await query.message.reply_text(text_out[i:i + 3800])

        elif data == "adm_reset_balances":
            user_count = len(db_data.get("users", {}))
            btn_confirm_reset = InlineKeyboardButton("হ্যাঁ, সব ব্যালেন্স ০ করে দাও", callback_data="adm_reset_balances_confirm")
            btn_cancel_reset = InlineKeyboardButton("বাতিল", callback_data="adm_report_cancel")
            _style(btn_confirm_reset, 'danger')
            _style(btn_cancel_reset, 'danger')
            kb = InlineKeyboardMarkup([[btn_confirm_reset], [btn_cancel_reset]])
            await query.message.reply_text(
                f"⚠️ এই মুহূর্তে বটে মোট {user_count} জন ইউজার আছে।\n\n"
                f"এই বাটনে চাপলে **সবার ব্যালেন্স 0 করে দেওয়া হবে** (Dollar থেকে Taka-তে পরিবর্তনের জন্য) — এটা আর ফেরত আনা যাবে না। নিশ্চিত?",
                reply_markup=kb
            )

        elif data == "adm_back":
            USER_STATE.pop(user_id, None)
            await query.message.reply_text("🔙 Menu", reply_markup=main_menu_keyboard(user_id, lang))
        return

    if user_id == ADMIN_ID and data.startswith("adm_file:"):
        _, cat, ttype = data.split(":")
        await admin_send_file_dump(context.bot, user_id, "instagram" if cat == "ig" else "facebook", ttype)
        return

    if user_id == ADMIN_ID and data.startswith("adm_clear_dump:"):
        key = data.split(":", 1)[1]
        label_map = {
            "fb_cookies_dump": "Facebook Cookies", "fb_2fa_dump": "Facebook 2FA",
            "ig_cookies_dump": "Instagram Cookies", "ig_2fa_dump": "Instagram 2FA",
        }
        label = label_map.get(key, key)
        with _lock:
            d = _load()
            d[key] = []
            _save(d)
        await query.edit_message_caption(caption=f"✅ {label} সাবমিশন ডাটা মুছে ফেলা হয়েছে। এখন থেকে নতুন করে সেভ হওয়া শুরু হবে।", reply_markup=None)
        return

    if user_id == ADMIN_ID and data == "adm_report_success":
        USER_STATE[user_id] = {"step": "waiting_report_txt", "report_mode": "approve"}
        await query.message.reply_text(
            "📤 Success-এর Facebook UID অথবা Instagram Username পাঠান\n"
            "(প্রতি লাইনে একটা করে — সরাসরি মেসেজে লিখে পাঠাতে পারেন, অথবা .txt ফাইল আপলোড করতে পারেন)"
        )
        return

    if user_id == ADMIN_ID and data == "adm_report_rejected":
        USER_STATE[user_id] = {"step": "waiting_report_txt", "report_mode": "reject"}
        await query.message.reply_text(
            "📤 Rejected-এর Facebook UID অথবা Instagram Username পাঠান\n"
            "(প্রতি লাইনে একটা করে — সরাসরি মেসেজে লিখে পাঠাতে পারেন, অথবা .txt ফাইল আপলোড করতে পারেন)"
        )
        return

    if user_id == ADMIN_ID and data == "adm_report_cancel":
        USER_STATE.pop(user_id, None)
        await query.message.reply_text("🚫 বাতিল করা হয়েছে।")
        return

    if user_id == ADMIN_ID and data == "adm_reset_balances_confirm":
        with _lock:
            d = _load()
            count = 0
            for uid_key in d.get("users", {}):
                d["users"][uid_key]["balance"] = 0.0
                count += 1
            _save(d)
        await query.edit_message_text(f"✅ সব ({count} জন) ইউজারের ব্যালেন্স 0 করে দেওয়া হয়েছে।")
        return

    if data.startswith("adm_cat:"):
        parts = data.split(":")
        cat = parts[1]
        state = USER_STATE.get(user_id, {})
        
        if state.get("step") == "select_category_for_task":
            task_name = state.get("task_name")
            USER_STATE[user_id] = {"category": cat, "step": "admin_task_price", "task_name": task_name}
            await query.message.reply_text(f"📝 বাটন নাম: {task_name}\n📁 Category: {cat}\n\n💵 টাস্কের দাম কত হবে লিখুন (যেমন: 5, 10.5):")
            try: await query.delete_message()
            except: pass
            return
        
        task_name = parts[2] if len(parts) > 2 else None
        if task_name:
            USER_STATE[user_id] = {"category": cat, "step": "admin_task_name", "selected_task_name": task_name}
            await query.message.reply_text(f"📝 Task: {task_name}\n📁 Category: {cat}\n\n💰 টাস্কের মূল্য দিন (Price in ৳):")
            try: await query.delete_message()
            except: pass
        else:
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
            btn_t_del = InlineKeyboardButton(f"Delete: {t['name']} (৳{t['price']})", callback_data=f"adm_do_del:{t['id']}")
            _style(btn_t_del, 'danger')
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

    if data.startswith("adm_vid_cat:"):
        cat = data.split(":")[1]
        active_tasks = [t for t in db_data.get("dynamic_tasks", {}).values() if t.get("category") == cat]
        if not active_tasks:
            await query.message.reply_text("❌ এই ক্যাটাগরিতে কোনো একটিভ টাস্ক পাওয়া যায়নি।")
            return

        buttons = []
        for t in active_tasks:
            has_vid = "[Video]" if t.get("video_file_id") else "[No Video]"
            btn_t_vid = InlineKeyboardButton(f"{has_vid} {t['name']}", callback_data=f"adm_vid_task:{t['id']}")
            _style(btn_t_vid, 'primary')
            buttons.append([btn_t_vid])

        await query.message.reply_text("👇 কোন টাস্কের জন্য ভিডিও সেট করতে চান? (🎥 = আগে থেকেই ভিডিও সেট আছে)", reply_markup=InlineKeyboardMarkup(buttons))
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_vid_task:"):
        task_id = data.split(":")[1]
        t_data = db_data.get("dynamic_tasks", {}).get(task_id)
        if not t_data:
            await query.message.reply_text("❌ দুঃখিত! টাস্কটি খুঁজে পাওয়া যায়নি।")
            return
        USER_STATE[user_id] = {"step": "waiting_for_task_video", "task_id": task_id}
        await query.message.reply_text(f"🎥 '{t_data['name']}' টাস্কের জন্য এখন একটা ভিডিও পাঠান (ফাইল হিসেবে ভিডিও আপলোড করুন):")
        try: await query.delete_message()
        except: pass
        return

    if data.startswith("adm_t_type:"):
        t_type = data.split(":")[1]
        state = USER_STATE.get(user_id)
        if state and "category" in state and (state.get("selected_task_name") or state.get("task_name")):
            t_id = str(uuid.uuid4())[:8]
            new_task = {
                "id": t_id, "category": state["category"], "name": state.get("selected_task_name") or state.get("task_name"),
                "price": state.get("task_price", 0.0), "rules": state.get("task_rules", ""), "type": t_type,
                "video_file_id": None
            }
            with _lock:
                d = _load()
                if "dynamic_tasks" not in d: d["dynamic_tasks"] = {}
                d["dynamic_tasks"][t_id] = new_task
                _save(d)
                
            USER_STATE.pop(user_id, None)
            await query.message.reply_text(f"✅ সফলভাবে নতুন টাস্ক সিস্টেমে সেভ করা হয়েছে!\n\n📌 নাম: {new_task['name']}\n💵 পেমেন্ট: ৳{new_task['price']}\n🎯 টাইপ: {new_task['type'].upper()}")
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
        USER_STATE[user_id] = {"step": "withdraw_method"}
        
        btn_bks = InlineKeyboardButton("bKash", callback_data="w_meth:bKash")
        btn_ngd = InlineKeyboardButton("Nagad", callback_data="w_meth:Nagad")
        btn_bnc = InlineKeyboardButton("Binance", callback_data="w_meth:Binance")
        _style(btn_bks, 'success')
        _style(btn_ngd, 'success')
        _style(btn_bnc, 'primary')
        
        kb = InlineKeyboardMarkup([[btn_bks, btn_ngd], [btn_bnc]])
        await query.edit_message_text(LANGUAGES[lang]["select_meth"], reply_markup=kb)
        return

    if data.startswith("w_meth:"):
        method = data.split(":")[1]
        USER_STATE[user_id]["method"] = method
        USER_STATE[user_id]["step"] = "withdraw_num"
        
        btn_cnc = KeyboardButton(LANGUAGES[lang]["btn_cancel"], icon_custom_emoji_id="5273914604752216432")
        _style(btn_cnc, 'danger')
        
        if method == "Binance":
            prompt = "🟡 আপনার Binance UID দিন:" if lang == "bn" else "🟡 Please send your Binance UID:"
        else:
            prompt = LANGUAGES[lang]["send_num"].format(method=method)
        await context.bot.send_message(chat_id=user_id, text=prompt, reply_markup=ReplyKeyboardMarkup([[btn_cnc]], resize_keyboard=True))
        try: await query.delete_message()
        except: pass
        return

    if user_id != ADMIN_ID:
        return

    if data.startswith("w_app:") or data.startswith("w_rej:"):
        w_id = data.split(":")[1]
        is_approve = data.startswith("w_app:")
        with _lock:
            d = _load()
            w_rec = d["withdrawals"].get(w_id)
            if w_rec and w_rec["status"] == "pending":
                w_lang = d["users"].get(str(w_rec["user_id"]), {}).get("language", "bn")
                if is_approve:
                    w_rec["status"] = "approved"
                    d["users"][str(w_rec["user_id"])]["balance"] = round(d["users"][str(w_rec["user_id"])]["balance"] - w_rec["amount"], 2)
                    msg = f"✅ Approved ৳{w_rec['amount']}"
                    if w_rec["method"] == "Binance":
                        num_label = "Binance UID" 
                    else:
                        num_label = "নম্বর" if w_lang == "bn" else "Number"
                    if w_lang == "bn":
                        u_msg = f"✅ উত্তোলন সফল হয়েছে\n\n{num_label}: {w_rec['number']}\nমাধ্যম: {w_rec['method']}\nপরিমাণ: ৳{w_rec['amount']}"
                    else:
                        u_msg = f"✅ Withdrawal Successful\n\n{num_label}: {w_rec['number']}\nMethod: {w_rec['method']}\nAmount: ৳{w_rec['amount']}"
                else:
                    w_rec["status"] = "rejected"
                    msg = "❌ Rejected"
                    u_msg = "❌ আপনার উত্তোলন অনুরোধটি বাতিল করা হয়েছে।" if w_lang == "bn" else "❌ Your withdrawal request has been rejected."
                _save(d)
                await query.edit_message_text(msg)
                try: await context.bot.send_message(chat_id=w_rec["user_id"], text=u_msg)
                except: pass
        return


# ============================================================
# ADMIN TASK VIDEO UPLOAD HANDLER
# ============================================================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    এডমিন 'Work Video' ফিচার দিয়ে যখন কোনো টাস্কের জন্য ভিডিও আপলোড করেন,
    তখন এটা ধরে সেই টাস্কের সাথে ভিডিওটা যুক্ত করে দেয়।
    """
    if not update.effective_user or not update.message or not update.message.video:
        return
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    state = USER_STATE.get(user_id, {})
    if state.get("step") != "waiting_for_task_video":
        return

    task_id = state.get("task_id")
    video_file_id = update.message.video.file_id

    with _lock:
        d = _load()
        if task_id in d.get("dynamic_tasks", {}):
            d["dynamic_tasks"][task_id]["video_file_id"] = video_file_id
            _save(d)
            task_name = d["dynamic_tasks"][task_id]["name"]
            await update.message.reply_text(f"✅ '{task_name}' টাস্কের জন্য ভিডিও সফলভাবে সেট করা হয়েছে!")
        else:
            await update.message.reply_text("❌ দুঃখিত! টাস্কটি খুঁজে পাওয়া যায়নি (হয়তো ডিলিট হয়ে গেছে)।")
    USER_STATE.pop(user_id, None)

# ============================================================
# ADMIN REPORT UID TXT UPLOAD HANDLER
# ============================================================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    এডমিন 'All Report' ফিচারে Success/Rejected UID লিস্ট (.txt) আপলোড
    করলে সেটা ধরে, ভেতরের UID (প্রতি লাইনে একটা করে) পড়ে bulk
    approve/reject প্রসেস চালায়।
    """
    if not update.effective_user or not update.message or not update.message.document:
        return
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    state = USER_STATE.get(user_id, {})
    if state.get("step") != "waiting_report_txt":
        return

    doc = update.message.document
    if not doc.file_name.lower().endswith(".txt"):
        await update.message.reply_text("❌ শুধু .txt ফাইল আপলোড করুন।")
        return

    tg_file = await doc.get_file()
    file_bytes = await tg_file.download_as_bytearray()
    try:
        text_content = bytes(file_bytes).decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text("❌ ফাইলটা পড়া গেল না, দয়া করে একটা সাধারণ .txt ফাইল পাঠান।")
        return

    uid_list = [line.strip() for line in text_content.splitlines() if line.strip()]
    if not uid_list:
        await update.message.reply_text("❌ ফাইলে কোনো UID পাওয়া যায়নি।")
        return

    approve = state.get("report_mode") == "approve"
    await update.message.reply_text(f"⏳ {len(uid_list)} টি UID প্রসেস করা হচ্ছে...")
    await admin_process_report_uids(context.bot, user_id, uid_list, approve)
    mode_label = "Success" if approve else "Rejected"
    btn_done = InlineKeyboardButton("শেষ (Done)", callback_data="adm_report_cancel")
    _style(btn_done, 'danger')
    await update.message.reply_text(
        f"📤 আরও {mode_label} UID/Username পাঠাতে পারেন, অথবা শেষ হলে নিচের বাটনে চাপুন।",
        reply_markup=InlineKeyboardMarkup([[btn_done]])
    )

# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    বটের যেকোনো হ্যান্ডলারে কোনো এরর হলে এটা ধরে ফেলে এবং শুধু log-এ
    সংক্ষেপে দেখায় (পুরো messy traceback console-এ আসা বন্ধ করে)।
    এটার কারণে বট কখনো ক্র্যাশ করবে না, শুধু ওই একটা রিকোয়েস্ট স্কিপ হবে।
    """
    err = context.error

    # Telegram-এর নিজস্ব Conflict এরর (একই টোকেনের একাধিক instance বা
    # deploy transition-এর সময় সাময়িকভাবে আসে) — এটা harmless, তাই
    # শুধু ছোট্ট একটা info লাইন দেখিয়ে চুপচাপ স্কিপ করা হচ্ছে।
    if isinstance(err, Conflict):
        logger.warning("Conflict: অন্য কোনো bot instance সাময়িকভাবে সক্রিয় ছিল, স্বয়ংক্রিয়ভাবে recover হচ্ছে।")
        return

    logger.error(f"হ্যান্ডলারে সমস্যা হয়েছে: {err}", exc_info=err)

    # ঠিক কোথায় (কোন ফাইলের কোন লাইনে) এররটা হয়েছে সেটা বের করে শুধু
    # Render Logs-এ রাখা হচ্ছে (এডমিনের Telegram ইনবক্সে আর কোনো এরর
    # মেসেজ পাঠানো হবে না, বট নিঃশব্দে সামলে নেবে)।
    location = ""
    try:
        tb = err.__traceback__
        last_frame = tb
        while last_frame.tb_next:
            last_frame = last_frame.tb_next
        fname = os.path.basename(last_frame.tb_frame.f_code.co_filename)
        func_name = last_frame.tb_frame.f_code.co_name
        line_no = last_frame.tb_lineno
        location = f"{fname} → {func_name}() → line {line_no}"
        logger.error(f"📍 এররের অবস্থান: {location}")
    except Exception:
        pass

# ============================================================
# FLASK KEEP-ALIVE SERVER (Render "Web Service" পোর্ট চায় + Uptime
# monitor যেমন UptimeRobot দিয়ে পিং করলে বট কখনো ঘুমাবে না/বন্ধ হবে না)
# ============================================================
from flask import Flask
_flask_app = Flask(__name__)
_START_TIME = datetime.datetime.utcnow()

@_flask_app.route("/")
def _home():
    uptime = datetime.datetime.utcnow() - _START_TIME
    return f"✅ Bot is running | Uptime: {str(uptime).split('.')[0]}"

@_flask_app.route("/health")
def _health():
    return {"status": "ok", "uptime_seconds": int((datetime.datetime.utcnow() - _START_TIME).total_seconds())}

def _run_dummy_server():
    """
    Render "Web Service" একটা খোলা পোর্ট আশা করে, নাহলে সার্ভিসটাকে
    unhealthy ভেবে বারবার restart করে। Flask দিয়ে একটা হালকা সার্ভার
    আলাদা থ্রেডে চালানো হচ্ছে — এটা বটের আসল কাজে কোনো প্রভাব ফেলে না।
    এই "/" URL-টা UptimeRobot বা যেকোনো uptime monitor দিয়ে প্রতি
    কয়েক মিনিটে পিং করলে Render সার্ভিসকে "sleep"/বন্ধ হতে দেবে না।
    """
    port = int(os.environ.get("PORT", 10000))
    try:
        _flask_app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Flask keep-alive সার্ভার চালু করা যায়নি: {e}")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    _load()  # স্টার্টআপেই Firebase থেকে সব ডেটা load করে ক্যাশে বসিয়ে দেয়
    logger.info("Firebase Realtime Database থেকে ডেটা সফলভাবে load হয়েছে।")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(callback_query))
    app.add_error_handler(error_handler)
    logger.info("Bot fully updated with Custom Report Layouts.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    import time
    threading.Thread(target=_run_dummy_server, daemon=True).start()
    # main() কোনো কারণে ক্র্যাশ করলে (যেমন নেটওয়ার্ক সাময়িকভাবে ডাউন
    # থাকলে), পুরো সার্ভিস বন্ধ না হয়ে বট নিজে থেকে কয়েক সেকেন্ড পর
    # আবার চালু হওয়ার চেষ্টা করবে।
    while True:
        try:
            main()
            break  # স্বাভাবিকভাবে থামলে (যেমন Ctrl+C) আর restart হবে না
        except Exception as e:
            logger.error(f"বট অপ্রত্যাশিতভাবে বন্ধ হয়ে গেছে, ৫ সেকেন্ড পর আবার চালু হচ্ছে: {e}", exc_info=e)
            time.sleep(5)
