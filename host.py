import os
import asyncio
import subprocess
import re
import ast
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command


# ================= WEB SERVER FOR RENDER =================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Spidy Hosting Bot Running")


def run_web():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


threading.Thread(target=run_web, daemon=True).start()

# ================= BOT CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # token from Render env
OWNER_ID = 6860983540

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

allowed = {OWNER_ID}

# ================= STORAGE =================

BASE = "user_bots"
os.makedirs(BASE, exist_ok=True)

running = {}
logs = {}
uptime = {}
waiting_input = {}   # ADD THIS

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
                ["python3", "-m", "pip", "install", module],
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

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):

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

⚡ Welcome to **Spidy Bot Hosting Server**

With this panel you can:

📂 Upload your Python bots  
🚀 Start or Stop hosted bots  
📊 Monitor uptime & status  
📜 Check error logs  

🔧 Manage everything directly from Telegram.

👇 Use the buttons below to control your bots
"""

    await message.answer(text, reply_markup=panel())
# ================= ACCESS =================

@dp.message(Command("access"))
async def access(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])
        allowed.add(uid)

        await message.answer("✅ Access Granted")

    except:
        await message.answer("Usage:\n/access USER_ID")

# ================= UPLOAD BUTTON =================
@dp.callback_query(F.data == "upload_bot")
async def upload_button(call: types.CallbackQuery):

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

    file = message.document

    if not file.file_name.endswith(".py"):
        return await message.answer("❌ Only .py files allowed")

    uid = str(message.from_user.id)

    folder = f"{BASE}/{uid}"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{file.file_name}"

    # delete user upload message
    try:
        await message.delete()
    except:
        pass

    msg = await message.answer("📦 Uploading bot...")

    await asyncio.sleep(1)

    await msg.edit_text("📦 Uploading bot...\n\n[■■□□□□□□□] 20%")

    await asyncio.sleep(1)

    await msg.edit_text("📦 Uploading bot...\n\n[■■■■□□□□□□] 40%")

    await asyncio.sleep(1)

    await msg.edit_text("📦 Uploading bot...\n\n[■■■■■■□□□□] 60%")

    await asyncio.sleep(1)

    await msg.edit_text("📦 Uploading bot...\n\n[■■■■■■■■□□] 80%")

    await asyncio.sleep(1)

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

    
    
    
@dp.message()
async def send_input(message: types.Message):

    uid = str(message.from_user.id)

    for key, process in running.items():

        if key.startswith(uid) and key in waiting_input:

            process.stdin.write((message.text + "\n").encode())
            await process.stdin.drain()

            del waiting_input[key]

            await message.reply("✅ Input sent to bot")

            return

# ================= START MENU =================

@dp.callback_query(F.data == "start_menu")
async def start_menu(call: types.CallbackQuery):

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text("❌ No bots uploaded", reply_markup=panel())

    files = [f for f in os.listdir(folder) if f.endswith(".py")]

    buttons = []

    for f in files:
        buttons.append([InlineKeyboardButton(text=f, callback_data=f"run_{f}")])

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "🚀 Select bot to start",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ================= RUN BOT =================

@dp.callback_query(F.data.startswith("run_"))
async def run_bot(call: types.CallbackQuery):

    uid = str(call.from_user.id)
    file = call.data.replace("run_", "")
    key = f"{uid}_{file}"

    path = f"{BASE}/{uid}/{file}"

    if key in running:
        return await call.answer("⚠️ Bot already running", show_alert=True)

    msg = await call.message.edit_text(
        "⏳ Initializing hosting environment..."
    )

    await asyncio.sleep(1.2)

    await msg.edit_text(
        "⚙️ Preparing runtime environment..."
    )

    await asyncio.sleep(1.2)

    await msg.edit_text(
        "📦 Checking required libraries..."
    )

    # 🔽 YAHI ADD KARNA HAI
    await auto_install_libs(path)

    await asyncio.sleep(1)

    await msg.edit_text(
        "🔍 Verifying bot file..."
    )

    if not os.path.exists(path):
        return await msg.edit_text(
            "❌ Bot file not found",
            reply_markup=panel()
        )

    await asyncio.sleep(1)

    await msg.edit_text(
        "🚀 Launching bot process..."
    )

    try:

        process = await asyncio.create_subprocess_exec(
            "python3",
            path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        running[key] = process
        logs[key] = ""
        uptime[key] = asyncio.get_event_loop().time()

        asyncio.create_task(read_stream(key, process.stdout))
        asyncio.create_task(read_stream(key, process.stderr))

        await asyncio.sleep(1)

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
{e}
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

        text = line.decode()

        logs[key] += text
        
        if (
            "phone" in text.lower()
            or "enter code" in text.lower()
            or "password" in text.lower()
            or "token" in text.lower()
        ):

            waiting_input[key] = True

            uid = key.split("_")[0]

            try:
                await bot.send_message(
                    uid,
                    f"📟 Bot asking input:\n\n{text}"
                )
            except:
                pass

        # Detect missing module
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

    uid = str(call.from_user.id)

    bots = [k for k in running if k.startswith(uid)]

    if not bots:
        return await call.message.edit_text("❌ No running bots", reply_markup=panel())

    buttons = []

    for b in bots:
        name = b.split("_",1)[1]
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"stop_{name}")])

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
        except:
            pass

        del running[key]

        # remove uptime
        if key in uptime:
            del uptime[key]

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

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    files = [f for f in os.listdir(folder) if f.endswith(".py")]

    buttons = []

    for f in files:
        buttons.append([InlineKeyboardButton(text=f"🗑 {f}", callback_data=f"del_{f}")])

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

    # stop bot if running
    if key in running:

        running[key].terminate()
        del running[key]

    # delete file from server
    if os.path.exists(path):
        os.remove(path)

    # delete logs
    if key in logs:
        del logs[key]

    await call.message.edit_text(
        f"🗑 {file} deleted from server",
        reply_markup=panel()
    )

    await call.answer()
# ================= STATUS =================

@dp.callback_query(F.data == "status_bot")
async def status_bot(call: types.CallbackQuery):

    uid = str(call.from_user.id)

    text = "📊 Running Bots\n\n"

    for key in running:

        if key.startswith(uid):

            name = key.split("_",1)[1]

            start = uptime.get(key,0)

            seconds = int(asyncio.get_event_loop().time() - start)

            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60

            text += f"""🤖 {name}
⏱ Uptime: {hours}h {minutes}m {secs}s

"""

    if text == "📊 Running Bots\n\n":
        text += "No bots running"

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

    uid = str(call.from_user.id)

    bots = [k for k in logs if k.startswith(uid)]

    if not bots:
        return await call.message.edit_text("❌ No logs available", reply_markup=panel())

    buttons = []

    for b in bots:
        name = b.split("_",1)[1]
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"log_{name}")])

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

    text = logs.get(key, "No logs")

    await call.message.edit_text(
        f"📜 Logs\n\n{text[-3500:]}",
        reply_markup=panel()
    )

# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):

    await call.message.edit_text(
        "🚀 Bot Hosting Panel",
        reply_markup=panel()
    )

# ================= RUN =================

async def main():
    await dp.start_polling(bot)

asyncio.run(main())