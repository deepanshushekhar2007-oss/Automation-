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

# TELETHON CLIENT


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

# ================= MODE SELECTION WITH FORCE SUB =================
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
    await message.answer("Send mobile number (10 digits):")

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
    await message.answer("Send Telegram user ID or @username:")

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
    await message.answer("Send Aadhar number:")

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
        # Auto delete owner-block message in groups
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

    # Remove unnecessary keys
    for key in ["API_Developer", "channel_name", "channel_link"]:
        data.pop(key, None)

    # Build message
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

    sent = await message.answer(msg)

    # Auto delete in groups
    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(40)
        try:
            await sent.delete()
        except:
            pass

# ================= ADHAR INFO =================
@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):

    import html, asyncio, requests

    args = (message.get_args() or "").strip()

    if not args:
        await message.answer("Usage: /adhar <adhar_number>")
        return

    # ForceSub
    ok = await check_force_sub(message.from_user.id)
    if not ok:
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
        if rc:
            msg_lines.append(f"State : {html.escape(rc.get('state_name',''))}")
            msg_lines.append(f"District : {html.escape(rc.get('district_name',''))}")
            msg_lines.append(f"Scheme : {html.escape(rc.get('scheme_name',''))}")
            msg_lines.append(f"RC ID : {html.escape(rc.get('ration_card_no',''))}")

        # Members
        members = res.get("members", [])
        if members:
            msg_lines.append("\nMembers:")
            for m in members:
                msg_lines.append(
                    f"{html.escape(m.get('member_name',''))} (UID: {html.escape(m.get('member_id',''))})"
                )

        # Additional Info
        add_info = res.get("additional_info", {})
        if add_info:
            msg_lines.append("\nAdditional Info:")
            for k, v in add_info.items():
                msg_lines.append(f"{html.escape(str(k))} : {html.escape(str(v))}")

    msg_lines.append("\nowner : @SPIDYWS")

    full_msg = "<b>📝 AADHAR INFO</b>\n━━━━━━━━━━━━━━━\n<code>"
    full_msg += "\n".join(msg_lines)
    full_msg += "</code>"

    sent = await message.answer(full_msg)

    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(30)
        try:
            await sent.delete()
        except:
            pass


# ================= PRIVATE BUTTON INPUT HANDLER =================
def build_msg(data, header=""):

    import html, json

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

    msg += "owner : @SPIDYWS\n</code>"
    return msg
# ---------------- Message handler ----------------
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

        # Show owner username but don't leak private info
        msg += f"owner : @{OWNER_USERNAME}\n</code>"
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
        """
        Returns Telegram user ID from username or numeric ID.
        """
        text = text.strip()
        if text.isdigit():
            return int(text), ""  # numeric ID, no username

        if not text.startswith("@"):
            text = "@" + text

        try:
            entity = await tg_client.get_entity(text)
            uid = entity.id
            uname = getattr(entity, "username", "")
            return uid, uname
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

    # ---------------- GROUP HANDLER ----------------
    if chat_type in ["group", "supergroup"]:
        if not text.startswith("/"):
            return

        if not await check_force_sub(user_id):
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use commands!")
            return

        args = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
        sent = None

        try:
            # -------- /num --------
            if text.startswith("/num"):
                if not args:
                    sent = await message.answer("Usage: /num <phone_number>")
                else:
                    try:
                        r = requests.get(os.getenv("NUMBER_API") + args, timeout=15)
                        result = r.json().get("result", [])
                    except:
                        sent = await message.answer("❌ API Error!")
                        return

                    if not result:
                        sent = await message.answer("No Data Found")
                    else:
                        sent = await message.answer(build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗"))

            # -------- /tg --------
            elif text.startswith("/tg"):
                if not args:
                    sent = await message.answer("Usage: /tg <id | @username>")
                else:
                    uid, uname = await resolve_username(args)
                    if not uid:
                        sent = await message.answer("❌ Invalid username or user not found!")
                        return

                    if is_owner(uid, uname):
                        sent = await message.answer(
                            f"<b>😂 Arre Bhai!</b>\n\n"
                            f"👀 Owner ko hi dhoondh rahe ho kya?\n"
                            f"🚫 Ye user search nahi ho sakta.\n"
                            f"🔒 Privacy level: Ultra Pro Max\n\n"
                            f"👑 Owner ➤ @{OWNER_USERNAME}"
                        )
                        return

                    try:
                        r = requests.get(os.getenv("TG_API") + str(uid), timeout=15)
                        result = r.json().get("result", {})
                    except:
                        sent = await message.answer("❌ API Error!")
                        return

                    if not result:
                        sent = await message.answer("No Data Found")
                    else:
                        sent = await message.answer(build_msg(result, "🆔 TG TO NUMBER"))

            # -------- /adhar --------
            elif text.startswith("/adhar"):
                if not args:
                    sent = await message.answer("Usage: /adhar <adhar_number>")
                else:
                    try:
                        r = requests.get(os.getenv("ADHAR_API") + args, timeout=15)
                        data = r.json()
                    except:
                        sent = await message.answer("❌ API Error!")
                        return

                    data.pop("credits", None)
                    results_list = data.get("result", {}).get("results", [])
                    if not results_list:
                        sent = await message.answer("No Data Found")
                        return

                    final_list = []
                    for res in results_list:
                        rc = res.get("ration_card_details")
                        if rc and isinstance(rc, dict):
                            final_list.append(rc)

                        members = res.get("members", [])
                        if members and isinstance(members, list):
                            for m in members:
                                if isinstance(m, dict):
                                    final_list.append(m)

                        add_info = res.get("additional_info")
                        if add_info and isinstance(add_info, dict):
                            final_list.append(add_info)

                    if not final_list:
                        sent = await message.answer("No Data Found")
                        return

                    sent = await message.answer(build_msg(final_list, "📝 AADHAR INFO"))

            else:
                return

            if sent:
                await asyncio.sleep(30)
                try:
                    await sent.delete()
                except:
                    pass

        except Exception as e:
            print("GROUP error:", e)
            await message.answer("❌ Error processing request!")

        return

    # ---------------- PRIVATE HANDLER ----------------
    if user_id not in user_mode:
        return

    mode = user_mode[user_id]

    if chat_type == "private":
        if not await check_force_sub(user_id):
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use the bot!")
            return

    try:
        msg = None
        # -------- number --------
        if mode == "number":
            r = requests.get(os.getenv("NUMBER_API") + text, timeout=15)
            result = r.json().get("result", [])
            if not result:
                await message.answer("No Data Found")
                user_mode.pop(user_id, None)
                return
            msg = build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗")

        # -------- tg --------
        elif mode == "tg":
            uid, uname = await resolve_username(text)
            if not uid:
                await message.answer("❌ Invalid username or user not found!")
                user_mode.pop(user_id, None)
                return

            if is_owner(uid, uname):
                await message.answer(
                    f"<b>😂 Arre Bhai!</b>\n\n"
                    f"👀 Owner ko hi dhoondh rahe ho kya?\n"
                    f"🚫 Ye user search nahi ho sakta.\n"
                    f"🔒 Privacy level: Ultra Pro Max\n\n"
                    f"👑 Owner ➤ @{OWNER_USERNAME}"
                )
                user_mode.pop(user_id, None)
                return

            r = requests.get(os.getenv("TG_API") + str(uid), timeout=15)
            result = r.json().get("result", {})
            if not result:
                await message.answer("No Data Found")
                user_mode.pop(user_id, None)
                return
            msg = build_msg(result, "🆔 TG TO NUMBER")

        # -------- adhar --------
        elif mode == "adhar":
            r = requests.get(os.getenv("ADHAR_API") + text, timeout=15)
            data = r.json()
            data.pop("credits", None)

            results_list = data.get("result", {}).get("results", [])
            if not results_list:
                await message.answer("No Data Found")
                user_mode.pop(user_id, None)
                return

            final_list = []
            for res in results_list:
                rc = res.get("ration_card_details")
                if rc and isinstance(rc, dict):
                    final_list.append(rc)

                members = res.get("members", [])
                if members and isinstance(members, list):
                    for m in members:
                        if isinstance(m, dict):
                            final_list.append(m)

                add_info = res.get("additional_info")
                if add_info and isinstance(add_info, dict):
                    final_list.append(add_info)

            if not final_list:
                await message.answer("No Data Found")
                user_mode.pop(user_id, None)
                return

            msg = build_msg(final_list, "📝 AADHAR INFO")

        else:
            await message.answer("❌ Invalid mode!")
            user_mode.pop(user_id, None)
            return

        if msg:
            await message.answer(msg)

    except Exception as e:
        print(f"PRIVATE {mode} error:", e)
        await message.answer("❌ Error processing input!")

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