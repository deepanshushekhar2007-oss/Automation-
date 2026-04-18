import asyncio
import json
import requests
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
import html

from telethon import TelegramClient
from telethon.sessions import StringSession

# ================= CONFIG =================
BOT_TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "6860983540"))
OWNER_USERNAME = "SPIDYWS"
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "@SPIDY_W_S")

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")

NUMBER_API = os.getenv("NUMBER_API", "https://ayaanmods.site/number.php?key=annonymous&number=")
TG_API     = os.getenv("TG_API",     "https://ayaanmods.site/tg2num.php?key=annonymoustgtonum&id=")
ADHAR_API  = os.getenv("ADHAR_API",  "https://ayaanmods.site/family.php?key=annonymousfamily&term=")

# ================= STATS =================
bot_start_time = datetime.now()
total_users = set()
total_queries = 0

# ================= INIT =================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
user_mode  = {}
admin_mode = {}

tg_client = TelegramClient(
    StringSession(STRING_SESSION), API_ID, API_HASH,
    auto_reconnect=True, connection_retries=None,
    retry_delay=5, request_retries=5, flood_sleep_threshold=60
)

# ================= STYLED BUTTON HELPERS =================
# Telegram new colored buttons (primary=blue, success=green, danger=red)
# via direct Bot API (aiogram doesn't support 'style' field natively yet)

def styled_send(chat_id, text, rows, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {"inline_keyboard": rows}
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("styled_send error:", e)

def styled_edit(chat_id, message_id, text, rows, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": {"inline_keyboard": rows}
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("styled_edit error:", e)

# ================= HELPERS =================
async def check_force_sub(user_id):
    try:
        member = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def is_owner(user_id, username=""):
    if user_id == OWNER_ID:
        return True
    if username and username.lstrip("@").lower() == OWNER_USERNAME.lower():
        return True
    return False

def build_msg(data, header=""):
    msg = f"<b>{html.escape(header)}</b>\n━━━━━━━━━━━━━━━\n<code>"
    def safe_val(val):
        if isinstance(val, (dict, list)):
            return html.escape(json.dumps(val, ensure_ascii=False))
        return html.escape(str(val))
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for k, v in item.items():
                    if v is not None:
                        msg += f"{safe_val(k)} : {safe_val(v)}\n"
            else:
                msg += f"{safe_val(item)}\n"
    elif isinstance(data, dict):
        for k, v in data.items():
            if v is not None:
                msg += f"{safe_val(k)} : {safe_val(v)}\n"
    else:
        msg += safe_val(data) + "\n"
    msg += f"owner : @{OWNER_USERNAME}\n</code>"
    return msg

# ================= REPLY KEYBOARD =================
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Number Lookup"), KeyboardButton(text="🆔 TG to Number")],
        [KeyboardButton(text="📝 Aadhar Info")]
    ],
    resize_keyboard=True
)

# ================= ADMIN PANEL HELPER =================
def _admin_panel_text():
    uptime = datetime.now() - bot_start_time
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    mins = rem // 60
    return (
        "<b>👑 SPIDY ADMIN PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 <b>Bot Status:</b> ✅ Running\n"
        f"⏱️ <b>Uptime:</b> {hours}h {mins}m\n"
        f"👥 <b>Total Users:</b> {len(total_users)}\n"
        f"🔍 <b>Total Queries:</b> {total_queries}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔧 <b>Select an action:</b>"
    )

def _admin_panel_rows():
    return [
        [
            {"text": "📱 Number Lookup", "callback_data": "adm_num",   "style": "primary"},
            {"text": "🆔 TG to Number",  "callback_data": "adm_tg",    "style": "primary"}
        ],
        [
            {"text": "📝 Aadhar Info",   "callback_data": "adm_adhar", "style": "primary"}
        ],
        [
            {"text": "🌐 View APIs",     "callback_data": "adm_apis",      "style": "success"},
            {"text": "📊 Bot Stats",     "callback_data": "adm_stats",     "style": "success"}
        ],
        [
            {"text": "📢 Broadcast",     "callback_data": "adm_broadcast", "style": "danger"}
        ]
    ]

def send_admin_panel(chat_id):
    styled_send(chat_id, _admin_panel_text(), _admin_panel_rows())

def edit_admin_panel(chat_id, message_id):
    styled_edit(chat_id, message_id, _admin_panel_text(), _admin_panel_rows())

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    try:
        total_users.add(message.from_user.id)

        if message.chat.type == "private":
            ok = await check_force_sub(message.from_user.id)
            if not ok:
                styled_send(
                    message.chat.id,
                    "⚠️ <b>Access Required!</b>\n\n"
                    "You must join our channel to use this bot.\n"
                    "Tap the button below to join 👇",
                    [
                        [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                        [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
                    ]
                )
                return

            styled_send(
                message.chat.id,
                "<b>💗 SPIDY MULTI TOOL BOT 💗</b>\n\n"
                "🚀 Welcome to the Advanced Multi Tool Bot\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📞 Number Lookup\n"
                "🆔 TG to Number\n"
                "🪪 Aadhar Info\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚡ Fast • Secure • Accurate\n\n"
                "👇 Select an option below:",
                [
                    [
                        {"text": "📱 Number Lookup", "callback_data": "mode_num",   "style": "primary"},
                        {"text": "🆔 TG to Number",  "callback_data": "mode_tg",    "style": "primary"}
                    ],
                    [
                        {"text": "📝 Aadhar Info",   "callback_data": "mode_adhar", "style": "primary"}
                    ]
                ]
            )
            await message.answer("Or use the keyboard below 👇", reply_markup=kb)

        else:
            await message.answer(
                "<b>💗 SPIDY BOT 💗</b>\n\n"
                "🚀 Advanced Lookup Services Available\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📞 /num  ➤ Number Lookup\n"
                "🆔 /tg   ➤ TG to Number\n"
                "🪪 /adhar ➤ Aadhar Info\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚡ Use commands directly to get started\n\n"
                "👑 Owner ➤ @SPIDYWS"
            )
    except Exception as e:
        print("Start command error:", e)

# ================= FORCE SUB CALLBACK =================
@dp.callback_query(F.data == "check_join")
async def cb_check_join(callback: CallbackQuery):
    ok = await check_force_sub(callback.from_user.id)
    if ok:
        total_users.add(callback.from_user.id)
        styled_edit(
            callback.message.chat.id,
            callback.message.message_id,
            "<b>💗 SPIDY MULTI TOOL BOT 💗</b>\n\n"
            "✅ Successfully joined! Welcome aboard!\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "👇 Select an option below:",
            [
                [
                    {"text": "📱 Number Lookup", "callback_data": "mode_num",   "style": "primary"},
                    {"text": "🆔 TG to Number",  "callback_data": "mode_tg",    "style": "primary"}
                ],
                [
                    {"text": "📝 Aadhar Info",   "callback_data": "mode_adhar", "style": "primary"}
                ]
            ]
        )
        await callback.answer("✅ Access granted! Welcome!")
    else:
        await callback.answer("❌ You haven't joined yet! Please join first.", show_alert=True)

# ================= MODE SELECTION CALLBACKS =================
@dp.callback_query(F.data == "mode_num")
async def cb_mode_num(callback: CallbackQuery):
    ok = await check_force_sub(callback.from_user.id)
    if not ok:
        await callback.answer("❌ Join the channel first!", show_alert=True)
        return
    user_mode[callback.from_user.id] = "number"
    await callback.message.answer("📱 Send mobile number (10 digits):")
    await callback.answer()

@dp.callback_query(F.data == "mode_tg")
async def cb_mode_tg(callback: CallbackQuery):
    ok = await check_force_sub(callback.from_user.id)
    if not ok:
        await callback.answer("❌ Join the channel first!", show_alert=True)
        return
    user_mode[callback.from_user.id] = "tg"
    await callback.message.answer("🆔 Send Telegram user ID or @username:")
    await callback.answer()

@dp.callback_query(F.data == "mode_adhar")
async def cb_mode_adhar(callback: CallbackQuery):
    ok = await check_force_sub(callback.from_user.id)
    if not ok:
        await callback.answer("❌ Join the channel first!", show_alert=True)
        return
    user_mode[callback.from_user.id] = "adhar"
    await callback.message.answer("📝 Send Aadhar number:")
    await callback.answer()

# ================= REPLY KEYBOARD HANDLERS =================
@dp.message(F.text == "📱 Number Lookup")
async def number_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        styled_send(
            message.chat.id,
            "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
            [
                [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
            ]
        )
        return
    user_mode[message.from_user.id] = "number"
    await message.answer("📱 Send mobile number (10 digits):")

@dp.message(F.text == "🆔 TG to Number")
async def tg_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        styled_send(
            message.chat.id,
            "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
            [
                [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
            ]
        )
        return
    user_mode[message.from_user.id] = "tg"
    await message.answer("🆔 Send Telegram user ID or @username:")

@dp.message(F.text == "📝 Aadhar Info")
async def adhar_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        styled_send(
            message.chat.id,
            "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
            [
                [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
            ]
        )
        return
    user_mode[message.from_user.id] = "adhar"
    await message.answer("📝 Send Aadhar number:")

# ================= COMMAND HANDLERS =================
@dp.message(F.command("num"))
async def cmd_num(message: Message):
    global total_queries
    try:
        ok = await check_force_sub(message.from_user.id)
        if not ok:
            styled_send(
                message.chat.id,
                "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
                [
                    [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                    [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
                ]
            )
            return
        args = message.text.split(maxsplit=1)
        args = args[1].strip() if len(args) > 1 else ""
        if not args:
            await message.answer("Usage: /num <phone_number>")
            return
        try:
            r = requests.get(NUMBER_API + args, timeout=15)
            data = r.json()
        except:
            await message.answer("❌ API Error! Try again.")
            return
        msg = "<code>"
        result = data.get("result", [])
        if isinstance(result, list) and result:
            for item in result:
                if isinstance(item, dict):
                    for k, v in item.items():
                        if v:
                            msg += f"{html.escape(str(k))} : {html.escape(str(v))}\n"
            msg += "owner : @SPIDYWS\n"
        else:
            msg += "No Data Found\nowner : @SPIDYWS\n"
        msg += "</code>"
        total_queries += 1
        sent = await message.answer(msg)
        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(40)
            try:
                await sent.delete()
            except:
                pass
    except Exception as e:
        print("NUM command error:", e)
        await message.answer("❌ Error fetching number info!")

@dp.message(F.command("tg"))
async def cmd_tg(message: Message):
    global total_queries
    from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError, PeerIdInvalidError
    user_input = (message.get_args() or "").strip()
    if not await check_force_sub(message.from_user.id):
        styled_send(
            message.chat.id,
            "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
            [
                [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
            ]
        )
        return
    if not user_input:
        await message.answer("Usage: /tg <user_id | @username>")
        return
    if not user_input.isdigit():
        if not user_input.startswith("@"):
            user_input = "@" + user_input
    try:
        if not tg_client.is_connected():
            await tg_client.connect()
    except Exception as e:
        print("Telethon connect error:", e)
    try:
        if user_input.isdigit():
            user_id_to_lookup = int(user_input)
            username_to_lookup = ""
        else:
            entity = await tg_client.get_entity(user_input)
            user_id_to_lookup = entity.id
            username_to_lookup = getattr(entity, "username", "") or ""
    except (UsernameNotOccupiedError, UsernameInvalidError):
        await message.answer("❌ Username does not exist!")
        return
    except PeerIdInvalidError:
        await message.answer("❌ Invalid user or bot cannot access this user!")
        return
    except Exception as e:
        print("Telethon resolve error:", e)
        await message.answer("❌ Telethon error! Try again later.")
        return
    if user_id_to_lookup == OWNER_ID or username_to_lookup.lstrip("@").lower() == OWNER_USERNAME.lower():
        sent = await message.answer(
            "<b>😂 Arre Bhai!</b>\n\n"
            "👀 Owner ko hi dhoondh rahe ho kya?\n"
            "🚫 Ye user search nahi ho sakta.\n"
            f"👑 Owner ➤ @{OWNER_USERNAME}"
        )
        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(40)
            try:
                await sent.delete()
            except:
                pass
        return
    try:
        r = requests.get(TG_API + str(user_id_to_lookup), timeout=15)
        data = r.json()
    except Exception as e:
        await message.answer("❌ API Error! Try again later.")
        return
    for key in ["API_Developer", "channel_name", "channel_link"]:
        data.pop(key, None)
    msg = "<b>🆔 TG TO NUMBER</b>\n━━━━━━━━━━━━━━━\n<code>"
    result = data.get("result", {})
    if isinstance(result, dict) and result:
        for k, v in result.items():
            if v:
                msg += f"{html.escape(str(k))} : {html.escape(str(v))}\n"
        msg += f"owner : @{OWNER_USERNAME}\n"
    else:
        msg += f"No Data Found\nowner : @{OWNER_USERNAME}\n"
    msg += "</code>"
    total_queries += 1
    sent = await message.answer(msg)
    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(40)
        try:
            await sent.delete()
        except:
            pass

@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):
    global total_queries
    args = (message.get_args() or "").strip()
    if not args:
        await message.answer("Usage: /adhar <adhar_number>")
        return
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        styled_send(
            message.chat.id,
            "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
            [
                [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
            ]
        )
        return
    try:
        r = requests.get(ADHAR_API + args, timeout=15)
        data = r.json()
    except Exception as e:
        await message.answer("❌ API Error! Try again later.")
        return
    results_list = data.get("result", {}).get("results", [])
    if not results_list:
        await message.answer("❌ No Data Found")
        return
    msg_lines = []
    for res in results_list:
        rc = res.get("ration_card_details", {})
        if rc:
            msg_lines.append(f"State : {html.escape(rc.get('state_name',''))}")
            msg_lines.append(f"District : {html.escape(rc.get('district_name',''))}")
            msg_lines.append(f"Scheme : {html.escape(rc.get('scheme_name',''))}")
            msg_lines.append(f"RC ID : {html.escape(rc.get('ration_card_no',''))}")
        members = res.get("members", [])
        if members:
            msg_lines.append("\nMembers:")
            for m in members:
                msg_lines.append(f"{html.escape(m.get('member_name',''))} (UID: {html.escape(m.get('member_id',''))})")
        add_info = res.get("additional_info", {})
        if add_info:
            msg_lines.append("\nAdditional Info:")
            for k, v in add_info.items():
                msg_lines.append(f"{html.escape(str(k))} : {html.escape(str(v))}")
    msg_lines.append("\nowner : @SPIDYWS")
    full_msg = "<b>📝 AADHAR INFO</b>\n━━━━━━━━━━━━━━━\n<code>"
    full_msg += "\n".join(msg_lines)
    full_msg += "</code>"
    total_queries += 1
    sent = await message.answer(full_msg)
    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(30)
        try:
            await sent.delete()
        except:
            pass

# ================= ADMIN COMMAND =================
@dp.message(F.command("admin"))
async def cmd_admin(message: Message):
    try:
        if message.from_user.id != OWNER_ID:
            await message.answer("❌ Only owner can access admin panel.")
            return
        send_admin_panel(message.chat.id)
    except Exception as e:
        print("ADMIN command error:", e)

# ================= ADMIN CALLBACKS =================
@dp.callback_query(F.data == "adm_back")
async def cb_adm_back(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    admin_mode.pop(callback.from_user.id, None)
    edit_admin_panel(callback.message.chat.id, callback.message.message_id)
    await callback.answer()

@dp.callback_query(F.data == "adm_num")
async def cb_adm_num(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    admin_mode[callback.from_user.id] = "adm_number"
    styled_edit(
        callback.message.chat.id, callback.message.message_id,
        "📱 <b>Number Lookup — Admin Mode</b>\n\n"
        "Send any mobile number to look up:",
        [[{"text": "⬅️ Back to Panel", "callback_data": "adm_back", "style": "danger"}]]
    )
    await callback.answer()

@dp.callback_query(F.data == "adm_tg")
async def cb_adm_tg(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    admin_mode[callback.from_user.id] = "adm_tg"
    styled_edit(
        callback.message.chat.id, callback.message.message_id,
        "🆔 <b>TG to Number — Admin Mode</b>\n\n"
        "Send Telegram user ID or @username:",
        [[{"text": "⬅️ Back to Panel", "callback_data": "adm_back", "style": "danger"}]]
    )
    await callback.answer()

@dp.callback_query(F.data == "adm_adhar")
async def cb_adm_adhar(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    admin_mode[callback.from_user.id] = "adm_adhar"
    styled_edit(
        callback.message.chat.id, callback.message.message_id,
        "📝 <b>Aadhar Info — Admin Mode</b>\n\n"
        "Send Aadhar number:",
        [[{"text": "⬅️ Back to Panel", "callback_data": "adm_back", "style": "danger"}]]
    )
    await callback.answer()

@dp.callback_query(F.data == "adm_apis")
async def cb_adm_apis(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    text = (
        "<b>🌐 Current API Configuration</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 <b>Number API:</b>\n<code>{NUMBER_API}</code>\n\n"
        f"🆔 <b>TG API:</b>\n<code>{TG_API}</code>\n\n"
        f"📝 <b>Aadhar API:</b>\n<code>{ADHAR_API}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 To change APIs, update env vars:\n"
        "<code>NUMBER_API</code>, <code>TG_API</code>, <code>ADHAR_API</code>"
    )
    styled_edit(
        callback.message.chat.id, callback.message.message_id, text,
        [
            [
                {"text": "🔄 Test Number API",  "callback_data": "adm_test_num",   "style": "primary"},
                {"text": "🔄 Test TG API",      "callback_data": "adm_test_tg",    "style": "primary"}
            ],
            [
                {"text": "🔄 Test Aadhar API",  "callback_data": "adm_test_adhar", "style": "primary"}
            ],
            [{"text": "⬅️ Back to Panel", "callback_data": "adm_back", "style": "danger"}]
        ]
    )
    await callback.answer()

@dp.callback_query(F.data == "adm_stats")
async def cb_adm_stats(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    uptime = datetime.now() - bot_start_time
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    mins, secs = divmod(rem, 60)
    text = (
        "<b>📊 Bot Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 <b>Status:</b> ✅ Online\n"
        f"⏱️ <b>Uptime:</b> {hours}h {mins}m {secs}s\n"
        f"👥 <b>Unique Users:</b> {len(total_users)}\n"
        f"🔍 <b>Total Queries:</b> {total_queries}\n"
        f"📅 <b>Started:</b> {bot_start_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"🌐 <b>APIs Active:</b> 3\n"
        f"👑 <b>Owner:</b> @{OWNER_USERNAME}"
    )
    styled_edit(
        callback.message.chat.id, callback.message.message_id, text,
        [[{"text": "⬅️ Back to Panel", "callback_data": "adm_back", "style": "danger"}]]
    )
    await callback.answer()

@dp.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    admin_mode[callback.from_user.id] = "adm_broadcast"
    styled_edit(
        callback.message.chat.id, callback.message.message_id,
        "📢 <b>Broadcast Message</b>\n\n"
        f"Total users to receive: <b>{len(total_users)}</b>\n\n"
        "Send the message you want to broadcast:",
        [[{"text": "❌ Cancel", "callback_data": "adm_back", "style": "danger"}]]
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_test_"))
async def cb_adm_test(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Not authorized!", show_alert=True)
        return
    api_type = callback.data.replace("adm_test_", "")
    try:
        if api_type == "num":
            r = requests.get(NUMBER_API + "9876543210", timeout=10)
        elif api_type == "tg":
            r = requests.get(TG_API + "123456789", timeout=10)
        elif api_type == "adhar":
            r = requests.get(ADHAR_API + "123456789012", timeout=10)
        else:
            await callback.answer("❓ Unknown API", show_alert=True)
            return
        status = f"✅ Online (HTTP {r.status_code})" if r.status_code == 200 else f"❌ Error {r.status_code}"
    except Exception as e:
        status = f"❌ Offline / Timeout"
    await callback.answer(f"API Status: {status}", show_alert=True)

# ================= MAIN MESSAGE HANDLER =================
@dp.message()
async def handle_input(message: Message):
    global total_queries

    user_id  = message.from_user.id
    text     = (message.text or "").strip()
    if not text or text.startswith("/"):
        return

    total_users.add(user_id)

    # -------- ADMIN MODE CHECK (runs first for owner) --------
    adm_mode = admin_mode.get(user_id)
    if adm_mode and user_id == OWNER_ID:
        try:
            if adm_mode == "adm_number":
                r = requests.get(NUMBER_API + text, timeout=15)
                result = r.json().get("result", [])
                msg = build_msg(result, "👑 ADMIN — NUMBER LOOKUP") if result else "❌ No Data Found"
                await message.answer(msg)
                total_queries += 1

            elif adm_mode == "adm_tg":
                inp = text.strip()
                if not inp.isdigit():
                    if not inp.startswith("@"):
                        inp = "@" + inp
                    try:
                        if not tg_client.is_connected():
                            await tg_client.connect()
                        entity = await tg_client.get_entity(inp)
                        uid_lookup = entity.id
                    except Exception:
                        await message.answer("❌ Could not resolve username!")
                        admin_mode.pop(user_id, None)
                        return
                else:
                    uid_lookup = int(inp)
                r = requests.get(TG_API + str(uid_lookup), timeout=15)
                result = r.json().get("result", {})
                msg = build_msg(result, "👑 ADMIN — TG TO NUMBER") if result else "❌ No Data Found"
                await message.answer(msg)
                total_queries += 1

            elif adm_mode == "adm_adhar":
                r = requests.get(ADHAR_API + text, timeout=15)
                data_res = r.json()
                results_list = data_res.get("result", {}).get("results", [])
                if results_list:
                    final_list = []
                    for res in results_list:
                        for key in ["ration_card_details", "members", "additional_info"]:
                            v = res.get(key)
                            if v:
                                if isinstance(v, list):
                                    final_list.extend(v)
                                else:
                                    final_list.append(v)
                    msg = build_msg(final_list, "👑 ADMIN — AADHAR INFO")
                else:
                    msg = "❌ No Data Found"
                await message.answer(msg)
                total_queries += 1

            elif adm_mode == "adm_broadcast":
                count, failed = 0, 0
                for uid_bc in list(total_users):
                    try:
                        await bot.send_message(uid_bc, f"📢 <b>Broadcast:</b>\n\n{text}")
                        count += 1
                        await asyncio.sleep(0.05)
                    except:
                        failed += 1
                await message.answer(f"📢 <b>Broadcast Done!</b>\n✅ Sent: {count}\n❌ Failed: {failed}")

            admin_mode.pop(user_id, None)
            await asyncio.sleep(0.3)
            styled_send(
                message.chat.id,
                "✅ Done! Go back to panel?",
                [[{"text": "👑 Admin Panel", "callback_data": "adm_back", "style": "success"}]]
            )
        except Exception as e:
            print(f"Admin mode error ({adm_mode}):", e)
            await message.answer("❌ Error! Try again.")
            admin_mode.pop(user_id, None)
        return

    # -------- FORCE SUB CHECK --------
    if message.chat.type == "private":
        ok = await check_force_sub(user_id)
        if not ok:
            styled_send(
                message.chat.id,
                "⚠️ <b>Access Required!</b>\n\nJoin the channel first.",
                [
                    [{"text": "🔔 Join Channel", "url": f"https://t.me/{FORCE_CHANNEL.replace('@','')}"}],
                    [{"text": "✅ I Joined", "callback_data": "check_join", "style": "success"}]
                ]
            )
            return

    mode = user_mode.get(user_id)
    if not mode:
        return

    # -------- USERNAME RESOLVER --------
    async def resolve_username(inp):
        inp = inp.strip()
        if inp.isdigit():
            return int(inp), ""
        if not inp.startswith("@"):
            inp = "@" + inp
        try:
            if not tg_client.is_connected():
                await tg_client.connect()
            entity = await tg_client.get_entity(inp)
            return entity.id, getattr(entity, "username", "") or ""
        except Exception as e:
            print("Resolve error:", e)
            return None, ""

    try:
        msg = None

        if mode == "number":
            r = requests.get(NUMBER_API + text, timeout=15)
            result = r.json().get("result", [])
            if not result:
                await message.answer("❌ No Data Found")
                user_mode.pop(user_id, None)
                return
            msg = build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗")

        elif mode == "tg":
            uid_r, uname_r = await resolve_username(text)
            if not uid_r:
                await message.answer("❌ Invalid username or user not found!")
                user_mode.pop(user_id, None)
                return
            if is_owner(uid_r, uname_r):
                await message.answer(
                    f"<b>😂 Arre Bhai!</b>\n\n"
                    f"👀 Owner ko hi dhoondh rahe ho kya?\n"
                    f"🚫 Ye user search nahi ho sakta.\n"
                    f"👑 Owner ➤ @{OWNER_USERNAME}"
                )
                user_mode.pop(user_id, None)
                return
            r = requests.get(TG_API + str(uid_r), timeout=15)
            result = r.json().get("result", {})
            if not result:
                await message.answer("❌ No Data Found")
                user_mode.pop(user_id, None)
                return
            msg = build_msg(result, "🆔 TG TO NUMBER")

        elif mode == "adhar":
            r = requests.get(ADHAR_API + text, timeout=15)
            data_res = r.json()
            data_res.pop("credits", None)
            results_list = data_res.get("result", {}).get("results", [])
            if not results_list:
                await message.answer("❌ No Data Found")
                user_mode.pop(user_id, None)
                return
            final_list = []
            for res in results_list:
                for key in ["ration_card_details", "members", "additional_info"]:
                    v = res.get(key)
                    if v:
                        if isinstance(v, list):
                            final_list.extend(v)
                        else:
                            final_list.append(v)
            if not final_list:
                await message.answer("❌ No Data Found")
                user_mode.pop(user_id, None)
                return
            msg = build_msg(final_list, "📝 AADHAR INFO")

        if msg:
            total_queries += 1
            await message.answer(msg)

    except Exception as e:
        print(f"PRIVATE {mode} error:", e)
        await message.answer("❌ Error processing input!")

    user_mode.pop(user_id, None)

# ================= RUN BOT =================
import os
import asyncio
from aiohttp import web

async def handle_web(request):
    return web.Response(text="SPIDY Bot Running")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle_web)
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    try:
        print("💗 SPIDY Bot Running...")

        async def start_telethon():
            while True:
                try:
                    if not tg_client.is_connected():
                        await tg_client.connect()
                    if not await tg_client.is_user_authorized():
                        await tg_client.start()
                    print("✅ Telethon Connected")
                    break
                except Exception as e:
                    print("Telethon reconnect error:", e)
                    await asyncio.sleep(5)

        await start_telethon()

        async def keep_telethon_alive():
            while True:
                try:
                    await tg_client.get_me()
                except Exception as e:
                    print("Telethon keepalive error:", e)
                    await start_telethon()
                await asyncio.sleep(60)

        asyncio.create_task(keep_telethon_alive())

        async def self_ping():
            while True:
                try:
                    await bot.get_me()
                except:
                    pass
                await asyncio.sleep(300)

        asyncio.create_task(self_ping())

        async def telethon_runner():
            while True:
                try:
                    if not tg_client.is_connected():
                        await start_telethon()
                    print("🚀 Telethon loop started")
                    await tg_client.run_until_disconnected()
                except Exception as e:
                    print("Telethon crashed:", e)
                    await asyncio.sleep(5)

        asyncio.create_task(telethon_runner())
        await start_web()
        await dp.start_polling(bot)

    except Exception as e:
        print("Bot polling error:", e)

if __name__ == "__main__":
    asyncio.run(main())
