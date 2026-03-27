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
AI_API = os.getenv(
    "AI_API",
    "https://ayaanmods.site/aiimage.php?key=annonymousai&prompt="
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
    API_HASH
)

# ================= FORCE SUB FUNCTION =================
async def check_force_sub(user_id):
    try:
        member = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def join_button():
    """Inline button to join the force channel"""
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
        [KeyboardButton(text="📝 Aadhar Info"), KeyboardButton(text="🖼️ AI Image")]
    ],
    resize_keyboard=True
)

# ================= START COMMAND =================
@dp.message(CommandStart())
async def start(message: Message):
    try:
        # Force sub check for private chats
        if message.chat.type == "private":
            ok = await check_force_sub(message.from_user.id)
            if not ok:
                await message.answer(
                    "⚠️ You must join the channel to use this bot!",
                    reply_markup=join_button()
                )
                return

            await message.answer(
                "<b>💗 SPIDY MULTI TOOL BOT 💗</b>\nSelect an option below:",
                reply_markup=kb
            )
        else:
            # Group or channel message
            await message.answer(
                "<b>💗 SPIDY BOT 💗</b>\nUse /num, /tg, /adhar, /ai commands directly"
            )
    except Exception as e:
        print("Start command error:", e)

# ================= MODE SELECTION WITH FORCE SUB =================
@dp.message(F.text == "📱 Number Lookup")
async def number_mode(message: Message):
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join the channel to use this bot!",
            reply_markup=join_button()
        )
        return
    user_mode[message.from_user.id] = "number"
    await message.answer("Send mobile number:")


@dp.message(F.text == "🆔 TG to Number")
async def tg_mode(message: Message):
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join the channel to use this bot!",
            reply_markup=join_button()
        )
        return
    user_mode[message.from_user.id] = "tg"
    await message.answer("Send Telegram user ID or @username:")


@dp.message(F.text == "📝 Aadhar Info")
async def adhar_mode(message: Message):
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join the channel to use this bot!",
            reply_markup=join_button()
        )
        return
    user_mode[message.from_user.id] = "adhar"
    await message.answer("Send Aadhar number:")


@dp.message(F.text == "🖼️ AI Image")
async def ai_mode(message: Message):
    if not await check_force_sub(message.from_user.id):
        await message.answer(
            "⚠️ You must join the channel to use this bot!",
            reply_markup=join_button()
        )
        return
    user_mode[message.from_user.id] = "ai"
    await message.answer("Send AI prompt to generate image:")

# ================= NUMBER LOOKUP =================
@dp.message(F.command("num"))
async def cmd_num(message: Message):
    try:
        if not await check_force_sub(message.from_user.id):
            await message.answer(
                "⚠️ You must join the channel to use this bot!",
                reply_markup=join_button()
            )
            return

        args = message.text.split(maxsplit=1)
        number = args[1].strip() if len(args) > 1 else ""

        if not number:
            await message.answer("Usage: /num <phone_number>")
            return

        try:
            r = requests.get(NUMBER_API + number, timeout=15)
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

        # Auto-delete in groups
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
    try:
        if not await check_force_sub(message.from_user.id):
            await message.answer(
                "⚠️ You must join the channel to use this bot!",
                reply_markup=join_button()
            )
            return

        args = (message.get_args() or "").strip()
        if not args:
            await message.answer("Usage: /tg <user_id | @username>")
            return

        # Resolve username / id
        user_id_to_lookup = None
        if args.isdigit():
            user_id_to_lookup = args
        else:
            try:
                entity = await tg_client.get_entity(args)
                user_id_to_lookup = str(entity.id)
            except Exception as e:
                print("Telethon resolve error:", e)
                await message.answer("❌ Invalid username or user not found!")
                return

        # API call
        try:
            r = requests.get(TG_API + user_id_to_lookup, timeout=15)
            data = r.json()
        except Exception as e:
            print("TG API error:", e)
            await message.answer("❌ API Error! Try again later.")
            return

        # Remove unnecessary keys
        for key in ["API_Developer", "channel_name", "channel_link"]:
            data.pop(key, None)

        msg = "<b>🆔 TG TO NUMBER</b>\n━━━━━━━━━━━━━━━\n<code>"
        result = data.get("result", {})

        if isinstance(result, dict) and result:
            for k, v in result.items():
                if v:
                    msg += f"{html.escape(str(k))} : {html.escape(str(v))}\n"
            msg += "owner : @SPIDYWS\n"
        else:
            msg += "No Data Found\nowner : @SPIDYWS\n"

        msg += "</code>"

        sent = await message.answer(msg)

        # Auto-delete in groups
        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(40)
            try:
                await sent.delete()
            except:
                pass

    except Exception as e:
        print("TG command error:", e)
        await message.answer("❌ Error fetching TG info!")

# ================= ADHAR INFO =================
@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):
    try:
        # ForceSub
        if not await check_force_sub(message.from_user.id):
            await message.answer(
                "⚠️ You must join channel to use this bot!",
                reply_markup=join_button()
            )
            return

        args = (message.get_args() or "").strip()
        if not args:
            await message.answer("Usage: /adhar <adhar_number>")
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

    except Exception as e:
        print("ADHAR command error:", e)
        await message.answer("❌ Error fetching Aadhar info!")


# ================= AI IMAGE =================
@dp.message(F.command("ai"))
async def cmd_ai(message: Message):
    try:
        # Force sub check
        if not await check_force_sub(message.from_user.id):
            await message.answer(
                "⚠️ You must join channel to use this bot!",
                reply_markup=join_button()
            )
            return

        args = message.text.split(maxsplit=1)
        prompt = args[1].strip() if len(args) > 1 else ""

        if not prompt:
            await message.answer("Usage: /ai <prompt>")
            return

        # Processing message
        sent = await message.answer("🤖 Generating AI image...")

        # API request
        try:
            r = requests.get(AI_API + prompt, timeout=30)
            data = r.json()
        except Exception as e:
            print("AI API request error:", e)
            await sent.edit_text("❌ AI API Error! Try again.")
            return

        if not data.get("success") or not data.get("images"):
            await sent.edit_text("❌ No images found for this prompt!")
            return

        # Send all images
        for img_url in data["images"]:
            sent = await message.answer_photo(
                img_url,
                caption=f"🖼 Prompt: {prompt}\nowner: @SPIDYWS"
            )

            # Auto delete in groups after 40s
            if message.chat.type in ["group", "supergroup"]:
                await asyncio.sleep(40)
                try:
                    await sent.delete()
                except:
                    pass

    except Exception as e:
        print("AI command error:", e)
        await message.answer("❌ Error generating AI image!")
        
# ================= PRIVATE & GROUP INPUT HANDLER =================
async def build_msg(data, header=""):
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


@dp.message()
async def handle_input(message: Message):
    import requests, asyncio

    user_id = message.from_user.id
    chat_type = message.chat.type
    text = (message.text or "").strip()
    if not text:
        return

    # ---------------- FORCE SUB CHECK ----------------
    async def is_member(uid):
        try:
            member = await bot.get_chat_member(FORCE_CHANNEL, uid)
            return member.status in ["member", "administrator", "creator"]
        except:
            return False

    # ---------------- GROUP COMMANDS ----------------
    if chat_type in ["group", "supergroup"]:
        if not text.startswith("/"):
            return

        if not await is_member(user_id):
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use commands!")
            return

        args = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
        sent = None

        try:
            if text.startswith("/num"):
                if not args:
                    sent = await message.answer("Usage: /num <phone_number>")
                else:
                    try:
                        r = requests.get(NUMBER_API + args, timeout=15)
                        result = r.json().get("result", [])
                    except:
                        await message.answer("❌ API Error!")
                        return

                    sent = await message.answer(build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗") if result else "No Data Found")

            elif text.startswith("/tg"):
                if not args:
                    sent = await message.answer("Usage: /tg <id | @username>")
                else:
                    user_id_to_lookup = args if args.isdigit() else None
                    if not user_id_to_lookup:
                        try:
                            entity = await tg_client.get_entity(args)
                            user_id_to_lookup = str(entity.id)
                        except:
                            await message.answer("❌ Invalid username or user not found!")
                            return

                    try:
                        r = requests.get(TG_API + user_id_to_lookup, timeout=15)
                        result = r.json().get("result", {})
                    except:
                        await message.answer("❌ API Error!")
                        return

                    sent = await message.answer(build_msg(result, "🆔 TG TO NUMBER") if result else "No Data Found")

            elif text.startswith("/adhar"):
                if not args:
                    sent = await message.answer("Usage: /adhar <adhar_number>")
                else:
                    try:
                        r = requests.get(ADHAR_API + args, timeout=15)
                        data = r.json()
                    except:
                        await message.answer("❌ API Error!")
                        return

                    results_list = data.get("result", {}).get("results", [])
                    final_list = []
                    for res in results_list:
                        for key in ["ration_card_details", "members", "additional_info"]:
                            val = res.get(key)
                            if val:
                                if isinstance(val, list):
                                    final_list.extend(val)
                                elif isinstance(val, dict):
                                    final_list.append(val)
                    sent = await message.answer(build_msg(final_list, "📝 AADHAR INFO") if final_list else "No Data Found")

            elif text.startswith("/ai"):
                if not args:
                    sent = await message.answer("Usage: /ai <prompt>")
                else:
                    prompt = args
                    sent = await message.answer("🤖 Generating AI image...")
                    try:
                        r = requests.get(AI_API + prompt, timeout=30)
                        data = r.json()
                        images = data.get("images", [])
                    except:
                        await sent.edit_text("❌ AI API Error!")
                        return

                    if not images:
                        await sent.edit_text("❌ No images found!")
                        return

                    for img_url in images:
                        img_msg = await message.answer_photo(img_url, caption=f"🖼 Prompt: {prompt}\nowner: @SPIDYWS")
                        await asyncio.sleep(40)
                        try:
                            await img_msg.delete()
                        except:
                            pass

        except Exception as e:
            print("GROUP error:", e)
            await message.answer("❌ Error processing request!")
        return

    # ---------------- PRIVATE COMMANDS ----------------
    if user_id not in user_mode:
        return

    mode = user_mode[user_id]

    if not await is_member(user_id):
        await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use the bot!")
        user_mode.pop(user_id, None)
        return

    try:
        msg = None

        if mode == "number":
            r = requests.get(NUMBER_API + text, timeout=15)
            result = r.json().get("result", [])
            msg = build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗") if result else "No Data Found"

        elif mode == "tg":
            user_id_to_lookup = text if text.isdigit() else None
            if not user_id_to_lookup:
                try:
                    entity = await tg_client.get_entity(text)
                    user_id_to_lookup = str(entity.id)
                except:
                    await message.answer("❌ Invalid username or user not found!")
                    user_mode.pop(user_id, None)
                    return

            r = requests.get(TG_API + user_id_to_lookup, timeout=15)
            result = r.json().get("result", {})
            msg = build_msg(result, "🆔 TG TO NUMBER") if result else "No Data Found"

        elif mode == "adhar":
            r = requests.get(ADHAR_API + text, timeout=15)
            data = r.json()
            results_list = data.get("result", {}).get("results", [])
            final_list = []
            for res in results_list:
                for key in ["ration_card_details", "members", "additional_info"]:
                    val = res.get(key)
                    if val:
                        if isinstance(val, list):
                            final_list.extend(val)
                        elif isinstance(val, dict):
                            final_list.append(val)
            msg = build_msg(final_list, "📝 AADHAR INFO") if final_list else "No Data Found"

        elif mode == "ai":
            if not text:
                await message.answer("Usage: /ai <prompt>")
                user_mode.pop(user_id, None)
                return
            sent = await message.answer("🤖 Generating AI image...")
            try:
                r = requests.get(AI_API + text, timeout=30)
                data = r.json()
                images = data.get("images", [])
            except:
                await sent.edit_text("❌ AI API Error!")
                user_mode.pop(user_id, None)
                return

            if not images:
                await sent.edit_text("❌ No images found!")
                user_mode.pop(user_id, None)
                return

            for img_url in images:
                await message.answer_photo(img_url, caption=f"🖼 Prompt: {text}\nowner: @SPIDYWS")

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

# ================== WEB SERVER ==================
async def handle(request):
    return web.Response(text="🌐 SPIDY Bot Running")


async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server running on port {port}")


# ================== TELETHON ==================
async def start_telethon():
    """Auto connect Telethon client with retry"""
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


async def keep_telethon_alive():
    """Keep Telethon alive and auto reconnect if disconnected"""
    while True:
        try:
            if not tg_client.is_connected() or not await tg_client.is_user_authorized():
                print("⚠️ Telethon disconnected, reconnecting...")
                await start_telethon()
            else:
                await tg_client.get_me()  # simple ping
        except Exception as e:
            print("Telethon keepalive error:", e)
            await asyncio.sleep(5)
        await asyncio.sleep(60)


# ================== TELETHON PING ==================
async def keep_alive():
    """Ping Telethon periodically"""
    while True:
        try:
            await tg_client.get_me()
        except Exception as e:
            print("Ping failed:", e)
        await asyncio.sleep(60)


# ================== SELF-PING ==================
async def self_ping():
    """Prevent host sleep"""
    while True:
        try:
            await bot.get_me()
        except Exception as e:
            print("Self-ping error:", e)
        await asyncio.sleep(300)


# ================== MAIN ==================
async def main():
    print("💗 SPIDY Bot Starting...")

    # Start Telethon first
    await start_telethon()

    # Start all background tasks
    asyncio.create_task(keep_telethon_alive())
    asyncio.create_task(keep_alive())
    asyncio.create_task(self_ping())
    asyncio.create_task(tg_client.run_until_disconnected())

    # Start web server
    await start_web()

    # Start Aiogram polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())