import os
import asyncio
import subprocess
import re
import psutil
import shutil
import time
import ast
import threading

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from flask import Flask


# ================= WEB SERVER FOR RENDER =================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Spidy Hosting Bot Running 🚀"


def run_web():
    port = int(os.getenv("PORT", 10000))
    print(f"🌐 Web server running on {port}")
    flask_app.run(host="0.0.0.0", port=port)


# ================= BOT CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

OWNER_ID = 6860983540

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

allowed = {OWNER_ID}


# ================= STORAGE =================

BASE = "user_bots"
os.makedirs(BASE, exist_ok=True)

running = {}          # running processes
logs = {}             # bot logs
uptime = {}           # uptime tracker
waiting_input = {}    # runtime input (phone / otp / password)


# ================= AUTO INSTALL LIBS =================

async def auto_install_libs(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    modules = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for name in node.names:
                modules.add(name.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])

    for module in modules:

        try:
            __import__(module)

        except ImportError:

            print(f"📦 Installing {module}")

            subprocess.run(
                ["python", "-m", "pip", "install", module],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )


# ================= PANEL =================

def panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Upload Bot", callback_data="upload_bot")],
            [InlineKeyboardButton(text="🚀 Start Bot", callback_data="start_menu")],
            [InlineKeyboardButton(text="🛑 Stop Bot", callback_data="stop_menu")],
            [InlineKeyboardButton(text="🗑 Delete Bot", callback_data="delete_menu")],
            [InlineKeyboardButton(text="📊 Status", callback_data="status_bot")],
            [InlineKeyboardButton(text="📜 Logs", callback_data="logs_menu")]
        ]
    )


# ================= ACCESS CONTROL =================

banned = set()


# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):

    if message.from_user.id in banned:
        return await message.answer("🚫 You are banned from using this bot")

    if message.from_user.id not in allowed:
        return await message.answer(
            "❌ Access Denied\n\n"
            "You are not authorized to use this hosting panel.\n\n"
            "👑 Owner: @SPIDYWS"
        )

    text = f"""
╔════════════════════╗
   🕷️ SPIDY HOSTING BOT
╚════════════════════╝

👤 User: {message.from_user.first_name}
🆔 User ID: {message.from_user.id}

⚡ Welcome to Spidy Bot Hosting Server

With this panel you can:

📂 Upload your Python bots  
🚀 Start or Stop hosted bots  
📊 Monitor uptime & status  
📜 Check error logs  

🔧 Manage everything directly from Telegram.

👇 Use the buttons below to control your bots
"""

    await message.answer(text, reply_markup=panel())


# ================= ACCESS COMMAND =================

@dp.message(Command("access"))
async def access(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])

        if uid in allowed:
            return await message.answer("⚠️ User already has access")

        allowed.add(uid)

        if uid in banned:
            banned.remove(uid)

        await message.answer(f"✅ Access Granted to `{uid}`", parse_mode="Markdown")

    except:
        await message.answer("Usage:\n/access USER_ID")


# ================= BAN COMMAND =================

@dp.message(Command("ban"))
async def ban_user(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])

        if uid == OWNER_ID:
            return await message.answer("❌ You cannot ban yourself")

        banned.add(uid)

        if uid in allowed:
            allowed.remove(uid)

        await message.answer(f"🚫 User `{uid}` banned successfully", parse_mode="Markdown")

    except:
        await message.answer("Usage:\n/ban USER_ID")


# ================= USERS LIST =================

@dp.message(Command("users"))
async def users_list(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    text = "👥 Allowed Users\n\n"

    for uid in allowed:
        text += f"• `{uid}`\n"

    text += "\n🚫 Banned Users\n\n"

    for uid in banned:
        text += f"• `{uid}`\n"

    await message.answer(text, parse_mode="Markdown")


# ================= UPLOAD BUTTON =================

@dp.callback_query(F.data == "upload_bot")
async def upload_button(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    back_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Back", callback_data="back")]
        ]
    )

    await call.message.edit_text(
        "📂 Please upload your .py bot file",
        reply_markup=back_btn
    )

    await call.answer()


# ================= FILE UPLOAD =================

@dp.message(F.document)
async def upload_file(message: types.Message):

    if message.from_user.id not in allowed:
        return

    if message.from_user.id in banned:
        return

    file = message.document

    if not file.file_name.endswith(".py"):
        return await message.answer("❌ Only .py files allowed")

    uid = str(message.from_user.id)

    folder = f"{BASE}/{uid}"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{file.file_name}"

    try:
        await message.delete()
    except:
        pass

    msg = await message.answer("📦 Uploading bot...")

    # fake progress bar
    for percent in [20, 40, 60, 80]:
        await asyncio.sleep(1)
        bars = "■" * (percent // 10) + "□" * (10 - percent // 10)
        await msg.edit_text(f"📦 Uploading bot...\n\n[{bars}] {percent}%")

    await bot.download(file, path)

    await msg.edit_text("📦 Uploading bot...\n\n[■■■■■■■■■■] 100%")

    await asyncio.sleep(1)
    await msg.edit_text("⚙️ Processing bot files...")

    await asyncio.sleep(2)

    start_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Start Bot", callback_data="start_menu")]
        ]
    )

    await msg.edit_text(
        f"""
✅ Bot Uploaded Successfully

🤖 Bot File: {file.file_name}

🚀 Your bot is ready to deploy.
""",
        reply_markup=start_btn
    )

# ================= START MENU =================

@dp.callback_query(F.data == "start_menu")
async def start_menu(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text("❌ No bots uploaded", reply_markup=panel())

    files = [f for f in os.listdir(folder) if f.endswith(".py")]

    if not files:
        return await call.message.edit_text("❌ No bots found", reply_markup=panel())

    buttons = [
        [InlineKeyboardButton(text=f, callback_data=f"run_{f}")]
        for f in files
    ]

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "🚀 Select bot to start",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= RUN BOT =================

@dp.callback_query(F.data.startswith("run_"))
async def run_bot(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)
    file = call.data.replace("run_", "")
    key = f"{uid}_{file}"
    path = f"{BASE}/{uid}/{file}"

    if not os.path.exists(path):
        return await call.answer("❌ File not found", show_alert=True)

    if key in running:
        return await call.answer("⚠️ Bot already running", show_alert=True)

    msg = await call.message.edit_text("⏳ Initializing hosting environment...")

    await asyncio.sleep(1)
    await msg.edit_text("⚙️ Preparing runtime environment...")

    await asyncio.sleep(1)
    await msg.edit_text("📦 Checking required libraries...")

    await auto_install_libs(path)

    await asyncio.sleep(1)
    await msg.edit_text("🚀 Launching bot process...")

    try:

        process = await asyncio.create_subprocess_exec(
            "python3",
            path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

        running[key] = process
        logs[key] = ""
        uptime[key] = time.time()

        asyncio.create_task(read_stream(key, process.stdout))
        asyncio.create_task(read_stream(key, process.stderr))

        await msg.edit_text(
            f"""✅ Bot Started Successfully

🤖 Bot: {file}
🟢 Status: Running
⏱ Uptime: Just started
""",
            reply_markup=panel()
        )

    except Exception as e:

        await msg.edit_text(
            f"""❌ Failed to start bot

Error:
{str(e)}
""",
            reply_markup=panel()
        )

    await call.answer()


# ================= READ LOGS =================

async def read_stream(key, stream):

    while True:

        line = await stream.readline()

        if not line:
            break

        text = line.decode(errors="ignore")

        # limit logs size (2k lines)
        logs[key] += text
        if len(logs[key]) > 20000:
            logs[key] = logs[key][-20000:]

        # ================= TELETHON INPUT DETECT =================

        if "Please enter your phone" in text:
            waiting_input[key] = "phone"

        elif "Please enter the code" in text:
            waiting_input[key] = "code"

        elif "Please enter your password" in text:
            waiting_input[key] = "password"

        # ================= AUTO INSTALL LIB =================

        match = re.search(r"No module named '(.*?)'", text)

        if match:

            module = match.group(1)

            logs[key] += f"\n📦 Installing missing library: {module}\n"

            try:
                subprocess.run(
                    ["python3", "-m", "pip", "install", module],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                logs[key] += f"✅ Installed: {module}\n"

            except Exception as e:
                logs[key] += f"❌ Failed installing {module}\n{e}\n"


# ================= STOP MENU =================

@dp.callback_query(F.data == "stop_menu")
async def stop_menu(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)

    bots = [k for k in running if k.startswith(uid)]

    if not bots:
        return await call.message.edit_text("❌ No running bots", reply_markup=panel())

    buttons = []

    for b in bots:
        name = b.split("_", 1)[1]
        buttons.append(
            [InlineKeyboardButton(text=name, callback_data=f"stop_{name}")]
        )

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "🛑 Select bot to stop",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ================= STOP BOT =================

@dp.callback_query(F.data.startswith("stop_"))
async def stop_bot(call: types.CallbackQuery):

    uid = str(call.from_user.id)
    file = call.data.replace("stop_", "")
    key = f"{uid}_{file}"

    if key in running:

        process = running[key]

        try:
            process.terminate()
            await asyncio.sleep(0.5)

            if process.returncode is None:
                process.kill()

        except:
            pass

        running.pop(key, None)
        logs.pop(key, None)
        uptime.pop(key, None)
        waiting_input.pop(key, None)

        await call.message.edit_text(
            f"🛑 {file} stopped successfully",
            reply_markup=panel()
        )

    else:
        await call.message.edit_text(
            "❌ Bot is not running",
            reply_markup=panel()
        )

    await call.answer()


# ================= DELETE MENU =================

@dp.callback_query(F.data == "delete_menu")
async def delete_menu(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text("❌ No bots found", reply_markup=panel())

    files = [f for f in os.listdir(folder) if f.endswith(".py")]

    if not files:
        return await call.message.edit_text("❌ No bots available", reply_markup=panel())

    buttons = [
        [InlineKeyboardButton(text=f"🗑 {f}", callback_data=f"del_{f}")]
        for f in files
    ]

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "🗑 Select bot to delete",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= DELETE BOT =================

@dp.callback_query(F.data.startswith("del_"))
async def delete_bot(call: types.CallbackQuery):

    uid = str(call.from_user.id)
    file = call.data.replace("del_", "")

    key = f"{uid}_{file}"
    path = f"{BASE}/{uid}/{file}"

    # stop if running
    if key in running:
        try:
            running[key].terminate()
            await asyncio.sleep(0.5)

            if running[key].returncode is None:
                running[key].kill()

        except:
            pass

        running.pop(key, None)

    # delete file
    if os.path.exists(path):
        os.remove(path)

    logs.pop(key, None)
    uptime.pop(key, None)
    waiting_input.pop(key, None)

    await call.message.edit_text(
        f"🗑 {file} deleted from server",
        reply_markup=panel()
    )

    await call.answer()


# ================= STATUS =================

@dp.callback_query(F.data == "status_bot")
async def status_bot(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)

    text = "📊 Running Bots\n\n"
    count = 0

    for key in running:

        if key.startswith(uid):

            count += 1
            name = key.split("_", 1)[1]
            start = uptime.get(key, 0)

            seconds = int(time.time() - start)

            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60

            text += f"""🤖 {name}
🟢 Running
⏱ {hours}h {minutes}m {secs}s

"""

    if count == 0:
        text += "❌ No bots running"

    back_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅ Back", callback_data="back")]
        ]
    )

    await call.message.edit_text(text, reply_markup=back_btn)
    await call.answer()


# ================= LOG MENU =================

@dp.callback_query(F.data == "logs_menu")
async def logs_menu(call: types.CallbackQuery):

    if call.from_user.id in banned:
        return await call.answer("🚫 You are banned", show_alert=True)

    uid = str(call.from_user.id)

    bots = [k for k in logs if k.startswith(uid)]

    if not bots:
        return await call.message.edit_text("❌ No logs available", reply_markup=panel())

    buttons = []

    for b in bots:
        name = b.split("_", 1)[1]
        buttons.append(
            [InlineKeyboardButton(text=name, callback_data=f"log_{name}")]
        )

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "📜 Select bot logs",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ================= SHOW LOG =================

@dp.callback_query(F.data.startswith("log_"))
async def show_logs(call: types.CallbackQuery):

    uid = str(call.from_user.id)
    file = call.data.replace("log_", "")
    key = f"{uid}_{file}"

    text = logs.get(key, "No logs available")

    # limit log size
    text = text[-3500:]

    await call.message.edit_text(
        f"📜 Logs - {file}\n\n{text}",
        reply_markup=panel()
    )


# ================= ADVANCED ADMIN STATUS =================

def get_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def format_size(size):
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024


START_TIME = time.time()


@dp.message(Command("status"))
async def admin_status(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    total_users = len(os.listdir(BASE)) if os.path.exists(BASE) else 0
    total_bots = 0
    running_bots = len(running)

    total_storage = get_size(BASE) if os.path.exists(BASE) else 0

    # Disk info
    total_disk, used_disk, free_disk = shutil.disk_usage("/")

    # RAM info
    ram = psutil.virtual_memory()

    # CPU
    cpu = psutil.cpu_percent(interval=0.5)

    # uptime
    bot_uptime = int(time.time() - START_TIME)
    hours = bot_uptime // 3600
    minutes = (bot_uptime % 3600) // 60

    text = f"""
🛠 ADVANCED HOSTING STATUS

👥 Users: {total_users}
🤖 Bots: calculating...
🟢 Running: {running_bots}

━━━━━━━━━━━━━━━━━━

💾 Disk Used: {format_size(used_disk)}
📦 Bot Storage: {format_size(total_storage)}
💾 Disk Free: {format_size(free_disk)}

🧠 RAM Used: {ram.percent}%
⚡ CPU Usage: {cpu}%

⏱ Uptime: {hours}h {minutes}m

━━━━━━━━━━━━━━━━━━
"""

    biggest_user = None
    biggest_size = 0

    if os.path.exists(BASE):

        for user in os.listdir(BASE):

            user_folder = os.path.join(BASE, user)

            if not os.path.isdir(user_folder):
                continue

            user_size = get_size(user_folder)

            if user_size > biggest_size:
                biggest_size = user_size
                biggest_user = user

            for bot_file in os.listdir(user_folder):

                if not bot_file.endswith(".py"):
                    continue

                total_bots += 1

                path = os.path.join(user_folder, bot_file)
                size = os.path.getsize(path)

                key = f"{user}_{bot_file}"

                status = "🟢 Running" if key in running else "🔴 Stopped"
                warn = "⚠️" if size > 5*1024*1024 else ""

                text += f"""
👤 User: {user}
🤖 Bot: {bot_file}
📦 Size: {format_size(size)} {warn}
📊 Status: {status}

"""

    text = text.replace("calculating...", str(total_bots))

    text += f"""

━━━━━━━━━━━━━━━━━━
🏆 Top Storage User: {biggest_user if biggest_user else 'None'}
📦 Size: {format_size(biggest_size)}
"""

    await message.answer(text[:4000])


# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):

    await call.message.edit_text(
        "🚀 Bot Hosting Panel",
        reply_markup=panel()
    )


# ================= RUNTIME INPUT HANDLER =================
# (Telethon login / input() support)

@dp.message()
async def runtime_input_handler(message: types.Message):

    uid = str(message.from_user.id)

    for key in list(waiting_input.keys()):

        if key.startswith(uid) and key in running:

            process = running[key]

            try:
                if process.stdin is None:
                    await message.answer("❌ Bot input not available")
                    return

                process.stdin.write((message.text + "\n").encode())
                await process.stdin.drain()

                waiting_input.pop(key, None)

                await message.answer("✅ Input sent to bot")
                return

            except Exception as e:
                await message.answer(f"❌ Failed to send input\n{e}")
                return


# ================= RUN =================

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Web server running on {port}")
    flask_app.run(host="0.0.0.0", port=port)


async def main_wrapper():
    # start web server thread FIRST
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # then start telegram bot
    await main()


if __name__ == "__main__":
    asyncio.run(main_wrapper())