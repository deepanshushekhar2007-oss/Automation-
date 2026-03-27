import asyncio
import json
import requests
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

AI_IMG_API = os.getenv(
    "AI_IMG_API",
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Join Channel",
                    url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ I Joined",
                    callback_data="recheck_join"
                )
            ]
        ]
    )

# ================= RECHECK BUTTON =================
@dp.callback_query(F.data == "recheck_join")
async def recheck_join(callback: CallbackQuery):

    ok = await check_force_sub(callback.from_user.id)

    if ok:
        await callback.message.edit_text(
            "✅ Access Granted!\nNow send command again."
        )
    else:
        await callback.answer(
            "❌ Still not joined!",
            show_alert=True
        )

# ================= KEYBOARD =================
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Number Lookup"), KeyboardButton(text="🆔 TG to Number")],
        [KeyboardButton(text="📝 Aadhar Info"), KeyboardButton(text="🎨 AI Image")]
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
                "<b>💗 SPIDY MULTI TOOL BOT 💗</b>\nSelect option below:",
                reply_markup=kb
            )
        else:
            await message.answer(
                "<b>💗 SPIDY BOT 💗</b>\nUse /num, /tg, /adhar commands directly"
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
    await message.answer("Send mobile number:")


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


@dp.message(F.text == "🎨 AI Image")
async def ai_mode(message: Message):

    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    user_mode[message.from_user.id] = "ai"
    await message.answer("Send prompt for AI image:")

# ================= NUMBER LOOKUP =================
@dp.message(F.command("num"))
async def cmd_num(message: Message):

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
            await asyncio.sleep(30)
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

    args = (message.get_args() or "").strip()

    if not args:
        await message.answer("Usage: /tg <user_id | @username>")
        return

    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    # resolve username
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

    try:
        r = requests.get(TG_API + user_id_to_lookup, timeout=15)
        data = r.json()
    except Exception as e:
        print("TG API error:", e)
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
        msg += "owner : @SPIDYWS\n"
    else:
        msg += "No Data Found\nowner : @SPIDYWS\n"

    msg += "</code>"

    sent = await message.answer(msg)

    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(30)
        try:
            await sent.delete()
        except:
            pass


# ================= ADHAR INFO =================
@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):

    args = (message.get_args() or "").strip()

    if not args:
        await message.answer("Usage: /adhar <adhar_number>")
        return

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

    result = data.get("result", {})
    pd = result.get("pd", {})

    if not pd:
        await message.answer("❌ No Data Found")
        return

    msg_lines = []

    msg_lines.append(f"State : {html.escape(str(pd.get('homeStateName', '')))}")
    msg_lines.append(f"District : {html.escape(str(pd.get('homeDistName', '')))}")
    msg_lines.append(f"Scheme : {html.escape(str(pd.get('schemeName', '')))}")
    msg_lines.append(f"RC ID : {html.escape(str(pd.get('rcId', '')))}")
    msg_lines.append(f"FPS ID : {html.escape(str(pd.get('fpsId', '')))}")
    msg_lines.append(f"Address : {html.escape(str(pd.get('address', '')))}")

    members = pd.get("memberDetailsList", [])
    if members:
        msg_lines.append("\nMembers:")
        for m in members:
            msg_lines.append(
                f"{html.escape(str(m.get('memberName','')))} "
                f"({html.escape(str(m.get('releationship_name','')))}), "
                f"UID : {html.escape(str(m.get('uid','')))}"
            )

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


# ================= AI IMAGE HANDLER =================
# ================= AI IMAGE =================
@dp.message(F.command("ai"))
async def cmd_ai(message: Message):

    args = (message.get_args() or "").strip()

    if not args:
        await message.answer("Usage: /ai <prompt>")
        return

    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    wait = await message.answer("🎨 Generating AI Images...")

    try:
        r = requests.get(AI_IMG_API + args, timeout=60)
        data = r.json()
    except Exception as e:
        print("AI API error:", e)
        await wait.edit_text("❌ API Error")
        return

    images = data.get("images", [])

    if not images:
        await wait.edit_text("❌ No images generated")
        return

    await wait.edit_text(
        f"<b>🎨 AI Images Generated</b>\n"
        f"Prompt : <code>{html.escape(args)}</code>\n"
        f"Owner : @SPIDYWS"
    )

    for img in images:
        try:
            await message.answer_photo(img)
        except:
            try:
                await message.answer(img)
            except:
                pass

    if message.chat.type in ["group", "supergroup"]:
        await asyncio.sleep(30)
        try:
            await wait.delete()
        except:
            pass
            
# ================= PRIVATE BUTTON INPUT HANDLER =================
@dp.message()
async def private_button_input(message: Message):

    mode = user_mode.get(message.from_user.id)
    if not mode:
        return

    # -------- Force Sub --------
    ok = await check_force_sub(message.from_user.id)
    if not ok:
        await message.answer(
            "⚠️ You must join channel to use this bot!",
            reply_markup=join_button()
        )
        return

    text = message.text.strip()

    # ================= NUMBER =================
    if mode == "number":
        try:
            r = requests.get(NUMBER_API + text, timeout=15)
            data = r.json()
        except:
            await message.answer("❌ API Error")
            return

        result = data.get("result", [])
        msg = build_msg(result, "📱 NUMBER LOOKUP")

        await message.answer(msg)
        user_mode.pop(message.from_user.id, None)


    # ================= TG =================
    elif mode == "tg":
        if text.isdigit():
            uid = text
        else:
            try:
                entity = await tg_client.get_entity(text)
                uid = str(entity.id)
            except:
                await message.answer("❌ Invalid username")
                return

        try:
            r = requests.get(TG_API + uid, timeout=15)
            data = r.json()
        except:
            await message.answer("❌ API Error")
            return

        result = data.get("result", {})
        msg = build_msg(result, "🆔 TG TO NUMBER")

        await message.answer(msg)
        user_mode.pop(message.from_user.id, None)


    # ================= ADHAR =================
    elif mode == "adhar":
        try:
            r = requests.get(ADHAR_API + text, timeout=15)
            data = r.json()
        except:
            await message.answer("❌ API Error")
            return

        result = data.get("result", {}).get("pd", {})
        msg = build_msg(result, "📝 AADHAR INFO")

        await message.answer(msg)
        user_mode.pop(message.from_user.id, None)


    # ================= AI IMAGE =================
    elif mode == "ai":

        wait = await message.answer("🎨 Generating AI Images...")

        try:
            r = requests.get(AI_IMG_API + text, timeout=60)
            data = r.json()
        except:
            await wait.edit_text("❌ API Error")
            return

        images = data.get("images", [])

        if not images:
            await wait.edit_text("❌ No Images Generated")
            return

        await wait.edit_text(
            f"<b>🎨 AI Images Generated</b>\n"
            f"Prompt : <code>{html.escape(text)}</code>\n"
            f"Owner : @SPIDYWS"
        )

        for img in images:
            try:
                await message.answer_photo(img)
            except:
                await message.answer(img)

        user_mode.pop(message.from_user.id, None)
        
        
# ---------------- Message handler ----------------
@dp.message()
async def handle_input(message: Message):

    import html, asyncio, requests, os, json

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

        msg += "owner : @SPIDYWS\n</code>"
        return msg

    # ---------------- GROUP HANDLER ----------------
    if chat_type in ["group", "supergroup"]:

        if not text.startswith("/"):
            return

        args = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""

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
                        sent = await message.answer(
                            build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗")
                        )

            # -------- /tg --------
            elif text.startswith("/tg"):

                if not args:
                    sent = await message.answer("Usage: /tg <id | @username>")

                else:

                    user_id_to_lookup = None

                    if args.isdigit():
                        user_id_to_lookup = args

                    else:
                        try:
                            entity = await tg_client.get_entity(args)
                            user_id_to_lookup = str(entity.id)
                        except:
                            sent = await message.answer(
                                "❌ Invalid username or user not found!"
                            )
                            return

                    try:
                        r = requests.get(
                            os.getenv("TG_API") + user_id_to_lookup,
                            timeout=15
                        )
                        result = r.json().get("result", {})
                    except:
                        sent = await message.answer("❌ API Error!")
                        return

                    if not result:
                        sent = await message.answer("No Data Found")
                    else:
                        sent = await message.answer(
                            build_msg(result, "🆔 TG TO NUMBER")
                        )

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

                        rc = res.get("ration_card_details", {})
                        if rc:
                            final_list.append(rc)

                        members = res.get("members", [])
                        if members:
                            final_list.extend(members)

                        add_info = res.get("additional_info", {})
                        if add_info:
                            final_list.append(add_info)

                    sent = await message.answer(
                        build_msg(final_list, "📝 AADHAR INFO")
                    )

            else:
                return

            if 'sent' in locals():

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

        try:
            await bot.get_chat_member(FORCE_CHANNEL, user_id)
        except:
            await message.answer(
                f"⚠️ You must join {FORCE_CHANNEL} to use the bot!"
            )
            return

    try:

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

            user_id_to_lookup = None

            if text.isdigit():
                user_id_to_lookup = text

            else:
                try:
                    entity = await tg_client.get_entity(text)
                    user_id_to_lookup = str(entity.id)
                except:
                    await message.answer(
                        "❌ Invalid username or user not found!"
                    )
                    user_mode.pop(user_id, None)
                    return

            try:
                r = requests.get(
                    os.getenv("TG_API") + user_id_to_lookup,
                    timeout=15
                )
                result = r.json().get("result", {})
            except:
                await message.answer("❌ API Error!")
                user_mode.pop(user_id, None)
                return

            if not result:
                await message.answer("No Data Found")
                user_mode.pop(user_id, None)
                return

            msg = build_msg(result, "🆔 TG TO NUMBER")

        # -------- adhar --------
        elif mode == "adhar":

            try:
                r = requests.get(os.getenv("ADHAR_API") + text, timeout=15)
                data = r.json()
            except Exception as e:
                print("ADHAR request error:", e)
                await message.answer("❌ API Error!")
                user_mode.pop(user_id, None)
                return

            try:
                final_list = []

                results_list = data.get("result", {}).get("results", [])
                if results_list:
                    for res in results_list:

                        rc = res.get("ration_card_details", {})
                        if rc:
                            final_list.append(rc)

                        members = res.get("members", [])
                        if members:
                            final_list.extend(members)

                        add_info = res.get("additional_info", {})
                        if add_info:
                            final_list.append(add_info)

                elif data.get("result", {}).get("pd"):
                    pd = data["result"]["pd"]

                    main_info = {
                        "State": pd.get("homeStateName"),
                        "District": pd.get("homeDistName"),
                        "Scheme": pd.get("schemeName"),
                        "RC ID": pd.get("rcId"),
                        "FPS ID": pd.get("fpsId"),
                        "Address": pd.get("address")
                    }

                    final_list.append(main_info)

                    members = pd.get("memberDetailsList", [])
                    for m in members:
                        final_list.append({
                            "Name": m.get("memberName"),
                            "Relation": m.get("releationship_name"),
                            "UID": m.get("uid")
                        })

                if not final_list:
                    await message.answer("No Data Found")
                    user_mode.pop(user_id, None)
                    return

                msg = build_msg(final_list, "📝 AADHAR INFO")

            except Exception as e:
                print("ADHAR parse error:", e)
                await message.answer("❌ No Data Found")
                user_mode.pop(user_id, None)
                return

        # -------- AI IMAGE --------
        elif mode == "ai":

            try:
                r = requests.get(os.getenv("AI_IMAGE_API") + text, timeout=60)
                data = r.json()

                img_url = data.get("image") or data.get("url")

                if not img_url:
                    await message.answer("❌ Image generate failed")
                    user_mode.pop(user_id, None)
                    return

                caption = (
                    "🎨 AI Generated Image\n"
                    "━━━━━━━━━━━━━━━\n"
                    "owner : @SPIDYWS"
                )

                await message.answer_photo(img_url, caption=caption)

                user_mode.pop(user_id, None)
                return

            except Exception as e:
                print("AI IMAGE error:", e)
                await message.answer("❌ AI Error!")
                user_mode.pop(user_id, None)
                return

        await message.answer(msg)
        user_mode.pop(user_id, None)

    except Exception as e:
        print("PRIVATE error:", e)
        await message.answer("❌ Error processing request!")
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
        msg += "/ai <prompt> - AI Image Generate\n"
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

        # ---------- RUN TELETHON BACKGROUND ----------
        asyncio.create_task(tg_client.run_until_disconnected())

        # ---------- START WEB ----------
        await start_web()

        # ---------- START BOT ----------
        await dp.start_polling(bot)

    except Exception as e:
        print("Bot polling error:", e)


if __name__ == "__main__":
    asyncio.run(main())