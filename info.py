import asyncio
import json
import requests
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
import html

# TELETHON ADD
from telethon import TelegramClient
from telethon.sessions import StringSession

# ================= CONFIG =================
BOT_TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "6860983540"))
OWNER_USERNAME = "SPIDYWS"
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "@SPIDY_W_S")

# TELETHON CONFIG
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")

# APIs
NUMBER_API = os.getenv(
    "NUMBER_API",
    "https://ayaanmods.site/number.php?key=annonymous&number="
)

TG_API = os.getenv(
    "TG_API",
    "https://ayaanmods.site/tg2num.php?key=annonymoustgtonum&id="
)

ADHAR_API = os.getenv(
    "ADHAR_API",
    "https://ayaanmods.site/family.php?key=annonymousfamily&term="
)

# ================= INIT =================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
user_mode = {}

# ================= TELETHON CLIENT =================
tg_client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH,
    auto_reconnect=True,
    connection_retries=None,
    retry_delay=5,
    request_retries=5,
    flood_sleep_threshold=60
)

# ================= FORCE SUB FUNCTION =================


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
    


def join_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔔 Join Channel",
                url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"
            )]
        ]
    )

# ================= KEYBOARD =================
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Number Lookup"), KeyboardButton(text="🆔 TG to Number")],
        [KeyboardButton(text="📝 Aadhar Info")]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    try:
        if message.chat.type == "private":
            ok = await check_force_sub(message.from_user.id)
            if not ok:
                await message.answer(
                    "⚠️ You must join channel to use this bot!",
                    reply_markup=join_button()
                )
                return

            await message.answer(
                "<b>💗 SPIDY MULTI TOOL BOT 💗</b>\n\n"
                "🚀 Welcome to the Advanced Multi Tool Bot\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📞 Number Lookup\n"
                "🆔 TG to Number\n"
                "🪪 Aadhar Info\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚡ Fast • Secure • Accurate\n\n"
                "👇 Please select an option below to continue",
                reply_markup=kb
            )

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

# ================= MODE SELECTION =================
@dp.message(F.text == "📱 Number Lookup")
async def number_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    user_mode[message.from_user.id] = "number"
    await message.answer("📱 Send mobile number (10 digits):")

@dp.message(F.text == "🆔 TG to Number")
async def tg_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    user_mode[message.from_user.id] = "tg"
    await message.answer("🆔 Send Telegram user ID or username:")

@dp.message(F.text == "📝 Aadhar Info")
async def adhar_mode(message: Message):
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    user_mode[message.from_user.id] = "adhar"
    await message.answer("🪪 Send Aadhar number:")

# ================= NUMBER LOOKUP =================
@dp.message(F.command("num"))
async def cmd_num(message: Message):

    import html, asyncio, requests

    try:
        ok = await check_force_sub(message.from_user.id)
        if not ok:
            await message.answer(
                "⚠️ You must join channel to use this bot!",
                reply_markup=join_button()
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

        result = data.get("result", [])

        # ---------- UI START ----------
        msg = "💎 <b>SPIDY NUMBER LOOKUP</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"🔎 Search: <code>{html.escape(args)}</code>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        if isinstance(result, list) and result:

            for item in result:
                if isinstance(item, dict):

                    def val(x):
                        return html.escape(str(x)) if x else "Not Found"

                    msg += f"👤 Name - <code>{val(item.get('name'))}</code>\n"
                    msg += f"📱 Mobile - <code>{val(item.get('mobile'))}</code>\n"
                    msg += f"📍 Address - <code>{val(item.get('address'))}</code>\n"
                    msg += f"👨 Father - <code>{val(item.get('father_name'))}</code>\n"
                    msg += f"🌐 Circle - {val(item.get('circle'))}\n"
                    msg += f"📧 Email - {val(item.get('email'))}\n"
                    msg += f"🆔 ID - {val(item.get('id'))}\n"

                    msg += "────────────────────\n"

        else:
            msg += "❌ No Data Found\n"

        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"🤖 Powered by @{OWNER_USERNAME}"

        # ---------- SEND ----------
        sent = await message.answer(msg)

        # auto delete in groups
        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(40)
            try:
                await sent.delete()
            except:
                pass

    except Exception as e:
        print("NUM command error:", e)
        await message.answer("❌ Error fetching number info!")
        
# ================= TG TO NUMBER =================
# ================= TG TO NUMBER =================
@dp.message(F.command("tg"))
async def cmd_tg(message: Message):
    import html, asyncio, requests

    user_input = (message.get_args() or "").strip()

    # -------- ForceSub FIRST --------
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    if not user_input:
        await message.answer("Usage: /tg <user_id | @username>")
        return

    # -------- resolve username / id --------
    try:
        if user_input.isdigit():
            user_id_to_lookup = int(user_input)
            username_to_lookup = ""
        else:
            entity = await tg_client.get_entity(user_input)
            user_id_to_lookup = entity.id
            username_to_lookup = getattr(entity, "username", "")
    except Exception as e:
        print("Telethon resolve error:", e)
        await message.answer("❌ Invalid username or user not found!")
        return

    # -------- STRICT OWNER BLOCK --------
    if user_id_to_lookup == OWNER_ID or username_to_lookup.lstrip("@").lower() == OWNER_USERNAME.lower():
        sent = await message.answer(
            "<b>😂 Arre Bhai!</b>\n\n"
            "👀 Owner ko hi dhoondh rahe ho kya?\n"
            "🚫 Ye user search nahi ho sakta.\n"
            "🔒 Privacy level: Ultra Pro Max\n\n"
            f"👑 Owner ➤ @{OWNER_USERNAME}"
        )

        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(40)
            try:
                await sent.delete()
            except:
                pass
        return

    # -------- API call --------
    try:
        r = requests.get(TG_API + str(user_id_to_lookup), timeout=15)
        data = r.json()
    except Exception as e:
        print("TG API error:", e)
        await message.answer("❌ API Error! Try again later.")
        return

    result = data.get("result", {})

    # -------- COUNTRY FLAG FUNCTION --------
    def get_flag(country):
        flags = {
            "India": "🇮🇳", "Pakistan": "🇵🇰", "Bangladesh": "🇧🇩", "Nepal": "🇳🇵",
            "United States": "🇺🇸", "USA": "🇺🇸", "United Kingdom": "🇬🇧", "Canada": "🇨🇦",
            "Australia": "🇦🇺", "Germany": "🇩🇪", "France": "🇫🇷", "Japan": "🇯🇵",
            "China": "🇨🇳", "Brazil": "🇧🇷", "Russia": "🇷🇺", "Peru": "🇵🇪",
            "Mexico": "🇲🇽", "South Africa": "🇿🇦", "Italy": "🇮🇹", "Spain": "🇪🇸",
            "Saudi Arabia": "🇸🇦", "Turkey": "🇹🇷", "Indonesia": "🇮🇩", "Philippines": "🇵🇭",
            "Thailand": "🇹🇭", "Malaysia": "🇲🇾", "Singapore": "🇸🇬"
        }
        return flags.get(country, "🌍")  # Default globe if not found

    # -------- UI START --------
    msg = "💎 <b>SPIDY TG TO NUMBER</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔎 Search: <code>{html.escape(user_input)}</code>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    def val(x):
        return html.escape(str(x)) if x else "Not Found"

    if isinstance(result, dict) and result:
        country = result.get("country", "")
        country_code = result.get("country_code", "")
        flag = get_flag(country)

        msg += f"👤 Name - {val(result.get('name'))}\n"
        msg += f"📱 Mobile - <code>{val(result.get('mobile'))}</code>\n"
        msg += f"🆔 Telegram ID - {val(result.get('id'))}\n"
        msg += f"🔗 Username - {val(result.get('username'))}\n"
        msg += f"📍 Address - {val(result.get('address'))}\n"
        msg += f"🌐 Circle - {val(result.get('circle'))}\n"
        msg += f"🌎 Country - {val(country)} {flag}\n"
        msg += f"🏷 Country Code - {val(country_code)}\n"

    else:
        msg += "❌ No Data Found\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🤖 Powered by @{OWNER_USERNAME}"

    # -------- SEND --------
    sent = await message.answer(msg)

    # auto delete
    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(40)
        try:
            await sent.delete()
        except:
            pass

# ================= ADHAR INFO =================
# ================= AADHAR INFO =================
@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):

    import html, asyncio, requests

    args = (message.get_args() or "").strip()

    if not args:
        await message.answer("Usage: /adhar <adhar_number>")
        return

    # ForceSub
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    try:
        r = requests.get(ADHAR_API + args, timeout=15)
        data = r.json()
    except Exception as e:
        print("ADHAR API error:", e)
        await message.answer("❌ API Error! Try again later.")
        return

    results_list = data.get("result", {}).get("results", [])

    if not results_list:
        await message.answer("❌ No Data Found")
        return

    msg_lines = []

    for res in results_list:
        # Ration Card Details
        rc = res.get("ration_card_details", {})
        msg_lines.append(f"🏛 State : {html.escape(rc.get('state_name','Not Found'))}")
        msg_lines.append(f"📍 District : {html.escape(rc.get('district_name','Not Found'))}")
        msg_lines.append(f"💳 Scheme : {html.escape(rc.get('scheme_name','Not Found'))}")
        msg_lines.append(f"🆔 RC ID : {html.escape(rc.get('ration_card_no','Not Found'))}")

        # Members
        members = res.get("members", [])
        msg_lines.append("\n👥 Members:")
        if members:
            for m in members:
                name = m.get('member_name','Not Found')
                uid = m.get('member_id','Not Found')
                msg_lines.append(f"{html.escape(name)} (UID: {html.escape(uid)})")
        else:
            msg_lines.append("No Members Found")

        # Additional Info
        add_info = res.get("additional_info", {})
        msg_lines.append("\n📑 Additional Info:")
        if add_info:
            for k, v in add_info.items():
                msg_lines.append(f"{html.escape(str(k))} : {html.escape(str(v) if v else 'Not Found')}")
        else:
            msg_lines.append("No Additional Info Found")

    # Footer
    msg_lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━")
    msg_lines.append("🤖 Powered by @SPIDYWS")

    full_msg = "<b>📝 AADHAR INFO</b>\n━━━━━━━━━━━━━━━\n<code>"
    full_msg += "\n".join(msg_lines)
    full_msg += "</code>"

    sent = await message.answer(full_msg)

    # Auto delete in groups
    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(30)
        try:
            await sent.delete()
        except:
            pass


# ================= PRIVATE BUTTON INPUT HANDLER =================
# ================= GENERIC BUILD MSG =================
def build_msg(data, header=""):

    import html, json

    msg = f"<b>{html.escape(header)}</b>\n━━━━━━━━━━━━━━━\n<code>"

    def safe_val(val):
        if val is None or val == "":
            return "Not Found"
        if isinstance(val, (dict, list)):
            return html.escape(json.dumps(val, ensure_ascii=False))
        return html.escape(str(val))

    if isinstance(data, list):
        if not data:
            msg += "No Data Found\n"
        else:
            for item in data:
                if isinstance(item, dict):
                    for k, v in item.items():
                        msg += f"{safe_val(k)} : {safe_val(v)}\n"
                else:
                    msg += f"{safe_val(item)}\n"

    elif isinstance(data, dict):
        if not data:
            msg += "No Data Found\n"
        else:
            for k, v in data.items():
                msg += f"{safe_val(k)} : {safe_val(v)}\n"

    else:
        msg += safe_val(data) + "\n"

    msg += "owner : @SPIDYWS\n</code>"
    return msg
# ---------------- Message handler ----------------
# ================= UNIVERSAL INPUT HANDLER (NEW UI + COUNTRY INFO) =================
@dp.message()
async def handle_input(message: Message):
    import html, asyncio, requests, json
    from telethon.errors.rpcerrorlist import UsernameNotOccupiedError, PeerIdInvalidError, UserNotMutualContactError

    user_id = message.from_user.id
    chat_type = message.chat.type
    text = (message.text or "").strip()
    if not text:
        return

    # ---------------- SAFE BUILD_MSG FUNCTION ----------------
    def build_msg(data, header=""):
        msg = f"<b>{html.escape(header)}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n<code>"

        def safe_val(val):
            if val is None or val == "":
                return "No Data Found"
            if isinstance(val, (dict, list)):
                return html.escape(json.dumps(val, ensure_ascii=False, indent=2))
            return html.escape(str(val))

        if isinstance(data, list):
            if not data:
                msg += "No Data Found\n"
            else:
                for idx, item in enumerate(data, start=1):
                    if isinstance(item, dict):
                        msg += f"\n--- Item {idx} ---\n"
                        for k, v in item.items():
                            msg += f"{safe_val(k)} : {safe_val(v)}\n"
                    else:
                        msg += f"{safe_val(item)}\n"
        elif isinstance(data, dict):
            if not data:
                msg += "No Data Found\n"
            else:
                # Country info injection
                if "mobile" in data and "country" not in data:
                    # Try to parse country code from mobile
                    mob = str(data.get("mobile", ""))
                    if mob.startswith("+"):
                        data["country"] = f"{mob[:4]} 🌐"
                    else:
                        data["country"] = "Unknown 🌐"

                for k, v in data.items():
                    msg += f"{safe_val(k)} : {safe_val(v)}\n"
        else:
            msg += safe_val(data) + "\n"

        msg += f"\nowner : @{OWNER_USERNAME}\n</code>"
        return msg

    # ---------------- FORCE CHANNEL CHECK ----------------
    async def check_force_sub(uid):
        try:
            member = await bot.get_chat_member(FORCE_CHANNEL, uid)
            return member.status in ["member", "administrator", "creator"]
        except:
            return False

    # ---------------- TELEGRAM USER RESOLVER ----------------
    async def resolve_username(text):
        text = text.strip()
        if text.isdigit():
            return int(text), ""  # numeric ID, no username
        if not text.startswith("@"):
            text = "@" + text
        try:
            entity = await tg_client.get_entity(text)
            return entity.id, getattr(entity, "username", "")
        except (UsernameNotOccupiedError, PeerIdInvalidError, UserNotMutualContactError):
            return None, None
        except Exception as e:
            print("Telegram lookup error:", e)
            return None, None

    # ---------------- OWNER CHECK ----------------
    def is_owner(uid, uname=""):
        if uid == OWNER_ID:
            return True
        if uname and uname.lstrip("@").lower() == OWNER_USERNAME.lower():
            return True
        return False

    # ---------------- UNIVERSAL PROCESS FUNCTION ----------------
    async def process_lookup(mode, query):
        try:
            msg = None

            if mode == "number":
                r = requests.get(os.getenv("NUMBER_API") + query, timeout=15)
                result = r.json().get("result", [])
                # Add country flags automatically
                for item in result:
                    if isinstance(item, dict) and "mobile" in item:
                        mob = str(item.get("mobile", ""))
                        if mob.startswith("+"):
                            item["country"] = f"{mob[:4]} 🌐"
                        else:
                            item["country"] = "Unknown 🌐"
                msg = build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗")

            elif mode == "tg":
                uid, uname = await resolve_username(query)
                if not uid:
                    return "❌ Invalid username or user not found!"
                if is_owner(uid, uname):
                    return (
                        f"<b>😂 Arre Bhai!</b>\n\n"
                        f"👀 Owner ko hi dhoondh rahe ho kya?\n"
                        f"🚫 Ye user search nahi ho sakta.\n"
                        f"🔒 Privacy level: Ultra Pro Max\n\n"
                        f"👑 Owner ➤ @{OWNER_USERNAME}"
                    )
                r = requests.get(os.getenv("TG_API") + str(uid), timeout=15)
                result = r.json().get("result", {})
                # Country flag
                if "mobile" in result:
                    mob = str(result.get("mobile", ""))
                    if mob.startswith("+"):
                        result["country"] = f"{mob[:4]} 🌐"
                    else:
                        result["country"] = "Unknown 🌐"
                msg = build_msg(result, "🆔 TG TO NUMBER")

            elif mode == "adhar":
                r = requests.get(os.getenv("ADHAR_API") + query, timeout=15)
                data = r.json()
                data.pop("credits", None)

                results_list = data.get("result", {}).get("results", [])
                final_list = []
                for res in results_list:
                    rc = res.get("ration_card_details")
                    if isinstance(rc, dict):
                        final_list.append(rc)
                    members = res.get("members", [])
                    for m in members:
                        if isinstance(m, dict):
                            final_list.append(m)
                    add_info = res.get("additional_info")
                    if isinstance(add_info, dict):
                        final_list.append(add_info)
                msg = build_msg(final_list, "📝 AADHAR INFO")

            else:
                return "❌ Invalid mode!"

            return msg or "No Data Found"

        except Exception as e:
            print(f"{mode.upper()} error:", e)
            return "❌ Error processing input!"

    # ---------------- GROUP / SUPERGROUP HANDLER ----------------
    if chat_type in ["group", "supergroup"]:
        if not text.startswith("/"):
            return
        if not await check_force_sub(user_id):
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use commands!")
            return

        cmd_parts = text.split(maxsplit=1)
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""

        mode_map = {
            "/num": "number",
            "/tg": "tg",
            "/adhar": "adhar"
        }

        mode = mode_map.get(cmd)
        if not mode:
            return

        if not args:
            await message.answer(f"Usage: {cmd} <query>")
            return

        reply = await process_lookup(mode, args)
        sent = await message.answer(reply)
        await asyncio.sleep(30)
        try:
            await sent.delete()
        except:
            pass
        return

    # ---------------- PRIVATE HANDLER ----------------
    if user_id not in user_mode:
        return

    mode = user_mode[user_id]

    if chat_type == "private":
        if not await check_force_sub(user_id):
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use the bot!")
            return

    reply = await process_lookup(mode, text)
    await message.answer(reply)
    user_mode.pop(user_id, None)
    
# ================= OWNER ADMIN PANEL =================
@dp.message(F.command("admin"))
async def cmd_admin(message: Message):
    try:
        if message.from_user.id != OWNER_ID:
            await message.answer("❌ Only owner can view admin panel.")
            return

        msg = "<b>👑 Admin Panel</b>\n\nCommands:\n"
        msg += "/num <number> - Number Lookup\n"
        msg += "/tg <user_id | @username> - TG to Number\n"
        msg += "/adhar <adhar_number> - Aadhar Info\n"
        msg += "\nSupports: username + numeric id"

        await message.answer(msg)
    except Exception as e:
        print("ADMIN command error:", e)
        await message.answer("❌ Error opening admin panel!")


# ================= RUN BOT (RENDER PORT FIX) =================
import os
import asyncio
from aiohttp import web

async def handle(request):
    return web.Response(text="SPIDY Bot Running")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    try:
        print("💗 SPIDY Bot Running...")

        # ---------- TELETHON AUTO CONNECT ----------
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

        # ---------- KEEP TELETHON ALIVE ----------
        async def keep_telethon_alive():
            while True:
                try:
                    await tg_client.get_me()
                except Exception as e:
                    print("Telethon keepalive error:", e)
                    await start_telethon()

                await asyncio.sleep(60)

        asyncio.create_task(keep_telethon_alive())

        # ---------- SELF PING (prevent sleep) ----------
        async def self_ping():
            while True:
                try:
                    await bot.get_me()
                except:
                    pass
                await asyncio.sleep(300)

        asyncio.create_task(self_ping())

        # ---------- RUN TELETHON BACKGROUND (FIXED) ----------
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

        # ---------- START WEB ----------
        await start_web()

        # ---------- START BOT ----------
        await dp.start_polling(bot)

    except Exception as e:
        print("Bot polling error:", e)


if __name__ == "__main__":
    asyncio.run(main())