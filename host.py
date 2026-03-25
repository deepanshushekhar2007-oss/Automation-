import os
import subprocess
import threading
import time
import psutil
from flask import Flask

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

BASE_DIR = "users"
os.makedirs(BASE_DIR, exist_ok=True)

# ===== STORAGE =====
running_bots = {}
bot_inputs = {}
user_settings = {}
allowed_users = set()
bot_status = {}
user_states = {}

# ===== BOT INIT =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===== RENDER KEEP ALIVE =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot Running ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# ===== UTILS =====
def is_allowed(uid):
    return uid == OWNER_ID or uid in allowed_users

def user_dir(uid):
    path = os.path.join(BASE_DIR, str(uid))
    os.makedirs(path, exist_ok=True)
    return path

# ===== OWNER COMMANDS =====
@dp.message(Command("access"))
async def access(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])
        allowed_users.add(uid)
        await message.answer(f"✅ Access Granted: {uid}")
    except:
        await message.answer("Usage: /access user_id")

@dp.message(Command("ban"))
async def ban(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])
        allowed_users.discard(uid)
        await message.answer(f"🚫 Banned: {uid}")
    except:
        await message.answer("Usage: /ban user_id")

# ===== START MENU =====
@dp.message(Command("start"))
async def start(message: types.Message):
    uid = message.from_user.id

    if not is_allowed(uid):
        await message.answer("❌ Not allowed")
        return

    user_settings.setdefault(uid, {"auto_req": True})

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Upload", callback_data="upload")],
        [InlineKeyboardButton(text="⚙ Requirements", callback_data="req")],
        [InlineKeyboardButton(text="▶ Start Bot", callback_data="startbot")],
        [InlineKeyboardButton(text="🛑 Stop Bot", callback_data="stopbot")],
        [InlineKeyboardButton(text="📊 Status", callback_data="status")]
    ])

    await message.answer(
        "🚀 *Telegram Bot Hosting Panel*\n\n"
        "✨ Upload, manage & run bots like hosting",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
# ===== BUTTON HANDLER (AIROGRAM) =====
@dp.callback_query()
async def buttons(callback: types.CallbackQuery):
    uid = callback.from_user.id
    data = callback.data
    path = user_dir(uid)

    if not is_allowed(uid):
        await callback.answer("Not allowed", show_alert=True)
        return

    try:

        # ===== STATUS =====
        if data == "status":
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            bots = running_bots.get(uid, {})

            await callback.message.edit_text(
                f"📊 STATUS\n\nCPU: {cpu}%\nRAM: {ram}%\nDisk: {disk}%\n\nRunning Bots: {len(bots)}"
            )

        # ===== UPLOAD MENU =====
        elif data == "upload":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Add File", callback_data="addfile")],
                [InlineKeyboardButton(text="🗑 Delete File", callback_data="delfile")],
                [InlineKeyboardButton(text="📁 View Files", callback_data="viewfile")],
                [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
            ])
            await callback.message.edit_text("📂 Upload Menu", reply_markup=keyboard)

        elif data == "viewfile":
            files = os.listdir(path)
            await callback.message.edit_text(
                "📁 Files:\n" + ("\n".join(files) or "Empty")
            )

        elif data == "delfile":
            files = os.listdir(path)

            if not files:
                await callback.answer("No files", show_alert=True)
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f, callback_data=f"del_{f}")]
                    for f in files
                ]
            )

            await callback.message.edit_text("Select file:", reply_markup=keyboard)

        elif data.startswith("del_"):
            fname = data.replace("del_", "")
            file_path = os.path.join(path, fname)

            if not os.path.exists(file_path):
                await callback.message.edit_text("❌ File not found")
                return

            try:
                os.remove(file_path)
                await callback.message.edit_text(f"🗑 Deleted: {fname}")
            except Exception as e:
                await callback.message.edit_text(f"❌ Delete error:\n{e}")

        # ===== REQUIREMENTS =====
        elif data == "req":
            status = "ON" if user_settings[uid]["auto_req"] else "OFF"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Toggle", callback_data="toggle")],
                [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
            ])

            await callback.message.edit_text(
                f"⚙ Requirements (Auto: {status})",
                reply_markup=keyboard
            )

        elif data == "toggle":
            user_settings[uid]["auto_req"] = not user_settings[uid]["auto_req"]
            await callback.answer("✅ Toggled")

        # ===== START BOT =====
        elif data == "startbot":
            files = [f for f in os.listdir(path) if f.endswith(".py")]

            if not files:
                await callback.answer("❌ No .py files found", show_alert=True)
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f, callback_data=f"run_{f}")]
                    for f in files
                ]
            )

            await callback.message.edit_text("Select bot:", reply_markup=keyboard)

        elif data.startswith("run_"):
            fname = data.replace("run_", "")
            file_path = os.path.join(path, fname)

            if not os.path.exists(file_path):
                await callback.message.edit_text("❌ File not found")
                return

            await callback.message.edit_text(
                f"⚙ Starting {fname}...\nInstalling requirements..."
            )

            # ===== INSTALL REQUIREMENTS =====
            req = os.path.join(path, "requirements.txt")

            if user_settings[uid]["auto_req"] and os.path.exists(req):
                result = subprocess.run(
                    ["pip", "install", "-r", req],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    await callback.message.edit_text(
                        f"❌ Requirements failed:\n{result.stderr[:1000]}"
                    )
                    return

            # ===== START PROCESS =====
            proc = subprocess.Popen(
                 ["python", "-u", file_path],  # 🔥 IMPORTANT (-u unbuffered)
                 stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.STDOUT,
                 text=True,
                 bufsize=1
             ) 
            running_bots.setdefault(uid, {})[fname] = proc
            bot_inputs.setdefault(uid, {})[fname] = proc

            threading.Thread(
                target=monitor_bot,
                args=(uid, fname, proc),
                daemon=True
            ).start()

            await callback.message.edit_text(f"🚀 Running: {fname}")

        # ===== STOP BOT =====
        elif data == "stopbot":
            bots = running_bots.get(uid, {})

            if not bots:
                await callback.answer("❌ No running bots", show_alert=True)
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=b, callback_data=f"stop_{b}")]
                    for b in bots
                ]
            )

            await callback.message.edit_text("Select bot:", reply_markup=keyboard)

        elif data.startswith("stop_"):
            name = data.replace("stop_", "")

            if name not in running_bots.get(uid, {}):
                await callback.message.edit_text("❌ Bot already stopped")
                return

            proc = running_bots[uid][name]

            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()

            del running_bots[uid][name]
            bot_inputs.get(uid, {}).pop(name, None)

            await callback.message.edit_text(f"🛑 Stopped: {name}")

        elif data == "back":
            await start(callback.message)

    except Exception as e:
        await callback.message.edit_text(f"❌ Error:\n{str(e)[:1000]}")

import asyncio

# ===== FILE UPLOAD + SMART INPUT =====
@dp.message()
async def handle_msg(message: types.Message):
    uid = message.from_user.id
    path = user_dir(uid)

    if not is_allowed(uid):
        return

    # ===== FILE UPLOAD =====
    if message.document:
        file = message.document
        name = file.file_name

        try:
            file_path = os.path.join(path, name)
            await bot.download(file, destination=file_path)

            if name == "requirements.txt":
                await message.answer("✅ requirements.txt uploaded")
            else:
                await message.answer(f"✅ Uploaded: {name}")

        except Exception as e:
            await message.answer(f"❌ Upload failed:\n{e}")

        return

    # ===== SMART INPUT SYSTEM =====
    if uid in user_states:
        state = user_states[uid]
        bot_name = state["bot"]

        proc = bot_inputs.get(uid, {}).get(bot_name)

        if proc:
            try:
                proc.stdin.write(message.text + "\n")
                proc.stdin.flush()

                await message.answer("✅ Input received")

            except Exception as e:
                await message.answer(f"❌ Input error:\n{e}")

        return


# ===== MONITOR BOT (THREAD SAFE) =====
def monitor_bot(uid, name, proc):
    loop = asyncio.get_event_loop()

    try:
        for line in proc.stdout:
            text = line.strip()
            print(text)

            lower = text.lower()

            # ===== TELETHON LOGIN DETECT =====
            if any(x in lower for x in ["phone", "enter your phone"]):
                user_states[uid] = {"bot": name, "step": "phone"}
                send("📱 Enter Phone Number")

            elif any(x in lower for x in ["code", "login code"]):
                user_states[uid] = {"bot": name, "step": "code"}
                send("🔢 Enter OTP")

            elif any(x in lower for x in ["password", "2fa"]):
                user_states[uid] = {"bot": name, "step": "password"}
                send("🔐 Enter 2FA Password")

            else:
                if len(text) > 5 and not any(x in lower for x in ["debug", "info"]):
                    asyncio.run_coroutine_threadsafe(
                        bot.send_message(uid, f"📜 {text[:150]}"),
                        loop
                    )

        proc.wait()

        user_states.pop(uid, None)

        if proc.returncode != 0:
            asyncio.run_coroutine_threadsafe(
                bot.send_message(uid, f"❌ Bot Crashed: {name}"),
                loop
            )
        else:
            asyncio.run_coroutine_threadsafe(
                bot.send_message(uid, f"⚠️ Bot Stopped: {name}"),
                loop
            )

    except Exception as e:
        asyncio.run_coroutine_threadsafe(
            bot.send_message(uid, f"❌ Monitor error:\n{e}"),
            loop
        )
        
# ===== RUN =====
async def main():
    print("🔥 Aiogram Bot Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())