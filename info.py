import asyncio
import json
import requests
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
import html

# ================= CONFIG =================
BOT_TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "6860983540"))
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "@SPIDY_W_S")

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
            try:
                await bot.get_chat_member(FORCE_CHANNEL, message.from_user.id)
            except:
                await message.answer(
                    f"⚠️ You must join {FORCE_CHANNEL} to use this bot!"
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
    user_mode[message.from_user.id] = "number"
    await message.answer("Send mobile number:")

@dp.message(F.text == "🆔 TG to Number")
async def tg_mode(message: Message):
    user_mode[message.from_user.id] = "tg"
    await message.answer("Send numeric Telegram user ID:")

@dp.message(F.text == "📝 Aadhar Info")
async def adhar_mode(message: Message):
    user_mode[message.from_user.id] = "adhar"
    await message.answer("Send Aadhar number:")

# ================= NUMBER LOOKUP =================
@dp.message(F.command("num"))
async def cmd_num(message: Message):
    try:
        if message.chat.type == "private":
            try:
                await bot.get_chat_member(FORCE_CHANNEL, message.from_user.id)
            except:
                await message.answer(
                    f"⚠️ You must join {FORCE_CHANNEL} to use this bot!"
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
            await message.answer("❌ Failed to fetch data! Try again.")
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
            await sent.delete()

    except Exception as e:
        print("NUM command error:", e)
        await message.answer("❌ Error fetching number info!")

# ================= TG TO NUMBER =================
@dp.message(F.command("tg"))
async def cmd_tg(message: Message):
    args = (message.get_args() or "").strip()

    if not args.isdigit():
        await message.answer("❌ Only numeric user ID allowed!")
        return

    if message.chat.type == "private":
        try:
            await bot.get_chat_member(FORCE_CHANNEL, message.from_user.id)
        except:
            await message.answer(
                f"⚠️ You must join {FORCE_CHANNEL} to use this bot!"
            )
            return

    try:
        r = requests.get(TG_API + args, timeout=15)
        data = r.json()
    except:
        await message.answer("❌ Failed to fetch data! Try again.")
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
        await sent.delete()

# ================= ADHAR INFO =================
@dp.message(F.command("adhar"))
async def cmd_adhar(message: Message):
    import html, asyncio, requests

    args = (message.get_args() or "").strip()
    if not args:
        await message.answer("Usage: /adhar <adhar_number>")
        return

    # Force join check only for private
    if message.chat.type == "private":
        try:
            await bot.get_chat_member(FORCE_CHANNEL, message.from_user.id)
        except:
            await message.answer(f"⚠️ You must join {FORCE_CHANNEL} to use this bot!")
            return

    try:
        r = requests.get(ADHAR_API + args, timeout=15)
        data = r.json()
        data.pop("credits", None)

        results_list = data.get("result", {}).get("results", [])
        if not results_list:
            await message.answer("❌ No data found for this Aadhar number!")
            return

        msg_lines = []
        for res in results_list:
            # Ration card details
            rc = res.get("ration_card_details", {})
            for key in ["ration_card_no", "state_name", "district_name", "scheme_name"]:
                if key in rc and rc[key]:
                    msg_lines.append(f"{html.escape(str(key))} : {html.escape(str(rc[key]))}")

            # Members
            members = res.get("members", [])
            if members:
                msg_lines.append("\nMembers:")
                for m in members:
                    m_info = []
                    for k in ["s_no", "member_id", "member_name", "remark"]:
                        if k in m and m[k]:
                            m_info.append(f"{html.escape(str(k))} : {html.escape(str(m[k]))}")
                    if m_info:
                        msg_lines.append(", ".join(m_info))

            # Additional info
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

        # Auto-delete in groups after 30 seconds
        if message.chat.type in ["group", "supergroup"]:
            await asyncio.sleep(30)
            try:
                await sent.delete()
            except:
                pass

    except Exception as e:
        print("ADHAR command error:", e)
        await message.answer(
            "❌ Error fetching Aadhar info!\nCorrect usage:\n/adhar 92828xxxxxx"
        )


# ================= PRIVATE BUTTON INPUT HANDLER =================
# (Using build_msg helper for safe HTML messages)
def build_msg(data, header=""):
    """
    Safely build Telegram HTML message.
    Escapes everything to prevent unsupported tags like <phone_number>.
    """
    import html
    import json

    msg = f"<b>{html.escape(header)}</b>\n━━━━━━━━━━━━━━━\n<code>"

    def safe_val(val):
        if isinstance(val, (dict, list)):
            return html.escape(json.dumps(val, ensure_ascii=False))
        return html.escape(str(val)).replace('<', '&lt;').replace('>', '&gt;')

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
    import html, asyncio, requests, os

    user_id = message.from_user.id
    chat_type = message.chat.type
    text = (message.text or "").strip()
    if not text:
        return  # ignore non-text messages

    # ---------------- SAFE BUILD_MSG FUNCTION ----------------
    def build_msg(data, header=""):
        """
        Safely build Telegram HTML message from dict/list
        """
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

    # ---------------- GROUP HANDLER ----------------
    if chat_type in ["group", "supergroup"]:
        if not text.startswith("/"):
            return  # ignore non-command messages

        args = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""

        try:
            # /num command
            if text.startswith("/num"):
                if not args:
                    sent = await message.answer(
                        "Usage: /num <phone_number>", parse_mode="HTML"
                    )
                else:
                    r = requests.get(os.getenv("NUMBER_API") + args, timeout=15)
                    result = r.json().get("result", [])
                    sent = await message.answer(
                        build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗"), parse_mode="HTML"
                    )

            # /tg command
            elif text.startswith("/tg"):
                if not args.isdigit():
                    sent = await message.answer(
                        "❌ Only numeric user ID allowed!", parse_mode="HTML"
                    )
                else:
                    r = requests.get(os.getenv("TG_API") + args, timeout=15)
                    result = r.json().get("result", {})
                    sent = await message.answer(
                        build_msg(result, "🆔 TG TO NUMBER"), parse_mode="HTML"
                    )

            # /adhar command
            elif text.startswith("/adhar"):
                if not args:
                    sent = await message.answer(
                        "Usage: /adhar <adhar_number>", parse_mode="HTML"
                    )
                else:
                    r = requests.get(os.getenv("ADHAR_API") + args, timeout=15)
                    data = r.json()
                    data.pop("credits", None)

                    results_list = data.get("result", {}).get("results", [])
                    if not results_list:
                        sent = await message.answer("❌ No data found!", parse_mode="HTML")
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
                        build_msg(final_list, "📝 AADHAR INFO"), parse_mode="HTML"
                    )

            else:
                return

            # Auto-delete in groups after 30 sec
            if 'sent' in locals():
                await asyncio.sleep(30)
                try:
                    await sent.delete()
                except:
                    pass

        except Exception as e:
            print("GROUP error:", e)
            await message.answer(
                "❌ Error processing request!\n\n"
                "Correct usage:\n"
                "/num 9932xxxxxxx\n"
                "/tg 191xxxxxx\n"
                "/adhar 92828xxxxxx",
                parse_mode="HTML"
            )
        return

    # ---------------- PRIVATE HANDLER ----------------
    if user_id not in user_mode:
        return

    mode = user_mode[user_id]

    # Force join check
    if chat_type == "private":
        try:
            await bot.get_chat_member(FORCE_CHANNEL, user_id)
        except:
            await message.answer(
                f"⚠️ You must join {FORCE_CHANNEL} to use the bot!", parse_mode="HTML"
            )
            return

    try:
        if mode == "number":
            r = requests.get(os.getenv("NUMBER_API") + text, timeout=15)
            result = r.json().get("result", [])
            msg = build_msg(result, "💗 SPIDY NUMBER LOOKUP 💗")

        elif mode == "tg":
            if not text.isdigit():
                await message.answer(
                    "❌ Only numeric user ID allowed!", parse_mode="HTML"
                )
                user_mode.pop(user_id, None)
                return
            r = requests.get(os.getenv("TG_API") + text, timeout=15)
            result = r.json().get("result", {})
            msg = build_msg(result, "🆔 TG TO NUMBER")

        elif mode == "adhar":
            r = requests.get(os.getenv("ADHAR_API") + text, timeout=15)
            data = r.json()
            data.pop("credits", None)

            results_list = data.get("result", {}).get("results", [])
            if not results_list:
                await message.answer("❌ No data found!", parse_mode="HTML")
                user_mode.pop(user_id, None)
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

            msg = build_msg(final_list, "📝 AADHAR INFO")

        else:
            await message.answer("❌ Invalid mode!", parse_mode="HTML")
            user_mode.pop(user_id, None)
            return

        await message.answer(msg, parse_mode="HTML")

    except Exception as e:
        print(f"PRIVATE {mode} error:", e)
        await message.answer("❌ Error processing input!", parse_mode="HTML")


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
        msg += "/tg <user_id> - TG to Number\n"
        msg += "/adhar <adhar_number> - Aadhar Info\n"
        msg += "\nNote: All groups can use the bot freely. No /access required."

        await message.answer(msg)
    except Exception as e:
        print("ADMIN command error:", e)
        await message.answer("❌ Error opening admin panel!")


# ================= RUN BOT (RENDER PORT FIX) =================
import os
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
        await start_web()   # start web server
        await dp.start_polling(bot)  # start bot polling
    except Exception as e:
        print("Bot polling error:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())