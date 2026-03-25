import os
import asyncio
import subprocess
import re
import ast
import threading
import shutil
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ================= WEB SERVER FOR RENDER =================

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"🔥 Hosting Panel Running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    # 🔥 IMPORTANT: disable log spam (Render fix)
    def log_message(self, format, *args):
        return


def run_web():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 Web running on {port}")
    server.serve_forever()


threading.Thread(target=run_web, daemon=True).start()

# ================= BOT CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found")

OWNER_ID = 6860983540

bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ================= ACCESS SYSTEM (PERSISTENT) =================

ACCESS_FILE = "access.json"

def load_access():
    try:
        if os.path.exists(ACCESS_FILE):
            with open(ACCESS_FILE, "r") as f:
                return set(json.load(f))
    except:
        pass
    return {OWNER_ID}


def save_access():
    try:
        with open(ACCESS_FILE, "w") as f:
            json.dump(list(allowed), f)
    except:
        pass


allowed = load_access()
allowed.add(OWNER_ID)  # 🔥 ensure owner always present

# ================= STORAGE =================

BASE = "user_bots"
os.makedirs(BASE, exist_ok=True)

running = {}
logs = {}
uptime = {}
waiting_input = {}

# ================= DELETE SYSTEM (PERSISTENT) =================

DELETE_FILE = "deleted.json"

def load_deleted():
    try:
        if os.path.exists(DELETE_FILE):
            with open(DELETE_FILE, "r") as f:
                data = json.load(f)
                # 🔥 FIX: convert list → set
                return {k: set(v) for k, v in data.items()}
    except:
        pass
    return {}


def save_deleted():
    try:
        # 🔥 convert set → list for JSON
        data = {k: list(v) for k, v in user_deleted.items()}
        with open(DELETE_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass


user_deleted = load_deleted()

# ================= STORAGE SYSTEM =================

def get_storage():
    total, used, free = shutil.disk_usage(BASE)

    def gb(x): return round(x / (1024**3), 2)

    return {
        "total": gb(total),
        "used": gb(used),
        "free": gb(free)
    }


def get_user_storage(uid):
    folder = f"{BASE}/{uid}"
    total_size = 0

    if os.path.exists(folder):
        for root, _, files in os.walk(folder):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)

    return round(total_size / (1024*1024), 2)

# ================= SERVER UPTIME =================

START_TIME = time.time()

def get_uptime():
    s = int(time.time() - START_TIME)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# ================= AUTO INSTALL LIBRARIES =================

async def auto_install_libs(file_path):

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

            # 🔥 basic security filter
            blocked = ["os.system", "subprocess.call", "shutil.rmtree"]
            for b in blocked:
                if b in code:
                    print(f"⚠️ Blocked dangerous code: {b}")
                    return

            tree = ast.parse(code)

    except:
        return

    modules = set()

    ignore = {
        "os", "sys", "re", "time", "math", "json",
        "asyncio", "threading", "subprocess",
        "collections", "itertools", "random"
    }

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for name in node.names:
                mod = name.name.split(".")[0]
                if mod not in ignore:
                    modules.add(mod)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                if mod not in ignore:
                    modules.add(mod)

    for module in modules:

        try:
            __import__(module)

        except ImportError:

            print(f"📦 Installing: {module}")

            try:
                process = await asyncio.create_subprocess_exec(
                    "python3", "-m", "pip", "install", module,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()   # 🔥 IMPORTANT FIX
            except:
                pass

# ================= PANEL =================

def panel(uid=None):

    buttons = [
        [InlineKeyboardButton(text="📂 Upload", callback_data="upload_bot")],
        [InlineKeyboardButton(text="🚀 Start", callback_data="start_menu")],
        [InlineKeyboardButton(text="🛑 Stop", callback_data="stop_menu")],
        [InlineKeyboardButton(text="🗑 Delete", callback_data="delete_menu")],
        [InlineKeyboardButton(text="📊 Status", callback_data="status_bot")],
        [InlineKeyboardButton(text="📜 Logs", callback_data="logs_menu")],
        [InlineKeyboardButton(text="⚡ Live", callback_data="live_status")]
    ]

    if uid == OWNER_ID:
        buttons.append(
            [InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):

    if message.from_user.is_bot:
        return

    if message.from_user.id not in allowed:
        return await message.answer(
            "❌ <b>Access Denied</b>\n\n"
            "You are not authorized.\n\n"
            "👑 Owner: @SPIDYWS"
        )

    uid = message.from_user.id
    storage = get_user_storage(uid)
    server = get_storage()

    text = f"""
<b>╭━━━〔 🕷️ HOST PANEL 〕━━━╮</b>

👤 <b>User:</b> {message.from_user.first_name}
🆔 <b>ID:</b> {uid}

💾 <b>Your Storage:</b> {storage} MB
🖥 <b>Server Free:</b> {server['free']} GB
⏱ <b>Uptime:</b> {get_uptime()}

━━━━━━━━━━━━━━━━━━━
🚀 Deploy & Manage Bots  
📜 Live Logs System  
🔄 Auto Restart Enabled  
━━━━━━━━━━━━━━━━━━━

⚡ <b>Status:</b> ONLINE
"""

    await message.answer(text, reply_markup=panel(uid))
    
# ================= ACCESS =================

@dp.message(Command("access"))
async def access(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])

        if uid in allowed:
            return await message.answer("⚠️ User already has access")

        allowed.add(uid)
        save_access()

        await message.answer(f"✅ Access Granted → {uid}")

    except:
        await message.answer("Usage:\n/access USER_ID")


# ================= BAN =================

@dp.message(Command("ban"))
async def ban_user(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        uid = int(message.text.split()[1])

        if uid not in allowed:
            return await message.answer("⚠️ User not found")

        allowed.remove(uid)
        save_access()

        # 🔥 stop all running bots of user
        uid_str = str(uid)
        for key in list(running.keys()):
            if key.startswith(uid_str):
                try:
                    running[key].terminate()
                except:
                    pass
                running.pop(key, None)
                uptime.pop(key, None)
                waiting_input.pop(key, None)

        await message.answer(f"🚫 Access Removed + Bots Stopped → {uid}")

    except:
        await message.answer("Usage:\n/ban USER_ID")


# ================= UPLOAD BUTTON =================

@dp.callback_query(F.data == "upload_bot")
async def upload_button(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"
    os.makedirs(folder, exist_ok=True)

    files = os.listdir(folder)

    total_size = sum(
        os.path.getsize(os.path.join(folder, f))
        for f in files if os.path.isfile(os.path.join(folder, f))
    )

    mb = round(total_size / (1024 * 1024), 2)

    text = f"""
╭━━━〔 📂 UPLOAD PANEL 〕━━━╮

👤 User: {uid}

━━━━━━━━━━━━━━━━━━━
📦 Files: {len(files)}
💾 Storage: {mb} MB
━━━━━━━━━━━━━━━━━━━

📁 Supported:
.py | .txt | .json | .env | .js | .yaml

━━━━━━━━━━━━━━━━━━━

⚡ Upload files one by one
🚀 Then deploy from Start menu

💡 Tip:
Use requirements.txt for auto install

╰━━━━━━━━━━━━━━━━━━━
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("📦 My Files", callback_data="my_files"),
                InlineKeyboardButton("🗑 Deleted", callback_data="deleted_files")
            ],
            [
                InlineKeyboardButton("🚀 Deploy", callback_data="start_menu")
            ],
            [
                InlineKeyboardButton("⬅ Back", callback_data="back")
            ]
        ]
    )

    await call.message.edit_text(text, reply_markup=keyboard)


# ================= MY FILES =================

@dp.callback_query(F.data == "my_files")
async def my_files(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text(
            "❌ No files uploaded",
            reply_markup=panel(call.from_user.id)
        )

    files = os.listdir(folder)

    if not files:
        return await call.message.edit_text(
            "❌ No files uploaded",
            reply_markup=panel(call.from_user.id)
        )

    text = f"📂 Your Files ({len(files)})\n\n"
    text += "\n".join([f"📄 {f}" for f in files])

    await call.message.edit_text(text, reply_markup=panel(call.from_user.id))


# ================= DELETED FILES =================

@dp.callback_query(F.data == "deleted_files")
async def deleted_files(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    deleted = list(user_deleted.get(uid, []))

    if not deleted:
        return await call.message.edit_text(
            "❌ No deleted files",
            reply_markup=panel(call.from_user.id)
        )

    text = f"🗑 Hidden Files ({len(deleted)})\n\n"
    text += "\n".join([f"❌ {f}" for f in deleted])

    await call.message.edit_text(text, reply_markup=panel(call.from_user.id))


# ================= FILE UPLOAD =================

@dp.message(F.document)
async def upload_file(message: types.Message):

    if message.from_user.id not in allowed:
        return

    document = message.document

    allowed_ext = (".py", ".txt", ".json", ".env", ".js", ".yaml", ".yml")

    if not document.file_name or not document.file_name.endswith(allowed_ext):
        return await message.answer("❌ Unsupported file type")

    if document.file_size > 20 * 1024 * 1024:
        return await message.answer("❌ File too large (Max 20MB)")

    uid = str(message.from_user.id)
    folder = f"{BASE}/{uid}"
    os.makedirs(folder, exist_ok=True)

    file_name = document.file_name
    path = os.path.join(folder, file_name)

    if os.path.exists(path):
        file_name = f"{int(asyncio.get_event_loop().time())}_{file_name}"
        path = os.path.join(folder, file_name)

    try:
        await message.delete()
    except:
        pass

    msg = await message.answer("📦 Initializing upload...")

    try:
        file = await bot.get_file(document.file_id)

        downloaded = 0
        total = document.file_size
        last_percent = -1

        chunk_size = 1024 * 64

        with open(path, "wb") as f:
            stream = await bot.download_file(file.file_path)

            while True:
                chunk = await stream.read(chunk_size)
                if not chunk:
                    break

                f.write(chunk)
                downloaded += len(chunk)

                percent = int((downloaded / total) * 100)

                if percent // 10 != last_percent:
                    last_percent = percent // 10

                    try:
                        await msg.edit_text(
                            f"📦 Uploading...\n\n⚡ {percent}% completed"
                        )
                    except:
                        pass

    except Exception as e:
        return await msg.edit_text(f"❌ Upload failed\n{str(e)[:100]}")

    await msg.edit_text("📦 Upload Complete ✅")

    # ================= DETECTION =================
    detected = []

    if file_name.endswith(".py"):
        detected.append("🐍 Python Bot")
    if file_name == "requirements.txt":
        detected.append("📦 Requirements")
    if file_name.endswith(".json"):
        detected.append("⚙️ Config")
    if file_name.endswith(".env"):
        detected.append("🔐 Environment")
    if file_name.endswith(".js"):
        detected.append("🌐 JS File")

    user_deleted.setdefault(uid, set()).discard(file_name)
    save_deleted()

    # ================= STORAGE =================
    total_size = sum(
        os.path.getsize(os.path.join(folder, f))
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    )

    mb = round(total_size / (1024 * 1024), 2)

    # ================= FINAL =================
    await msg.edit_text(
        f"""
╭━━━〔 ✅ UPLOAD SUCCESS 〕━━━╮

📂 File: {file_name}
📦 Size: {round(document.file_size / (1024*1024),2)} MB

━━━━━━━━━━━━━━━━━━━
🧠 Detected: {", ".join(detected) if detected else "Unknown"}
💾 Storage: {mb} MB
━━━━━━━━━━━━━━━━━━━

💡 Ready for deployment 🚀
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("🚀 Start Bot", callback_data="start_menu"),
                    InlineKeyboardButton("📜 Logs", callback_data="logs_menu")
                ],
                [
                    InlineKeyboardButton("⬅ Back", callback_data="back")
                ]
            ]
        )
    )
    
# ================= BOT INPUT =================

@dp.message()
async def send_input(message: types.Message):

    uid = str(message.from_user.id)

    for key, process in running.items():

        if key.startswith(uid) and key in waiting_input:

            try:
                if process.stdin and not process.stdin.is_closing():

                    process.stdin.write((message.text + "\n").encode())
                    await process.stdin.drain()

                    waiting_input.pop(key, None)

                    return await message.reply("✅ Input sent to bot")

            except Exception as e:
                return await message.reply(f"❌ Failed: {str(e)[:50]}")

    # ignore other messages silently


# ================= START MENU =================

@dp.callback_query(F.data == "start_menu")
async def start_menu(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text(
            "❌ No files uploaded",
            reply_markup=panel(call.from_user.id)
        )

    files = [
        f for f in os.listdir(folder)
        if f.endswith(".py") and f not in user_deleted.get(uid, set())
    ]

    if not files:
        return await call.message.edit_text(
            "❌ No runnable bots found",
            reply_markup=panel(call.from_user.id)
        )

    # 🔥 priority sort
    priority = ["main.py", "bot.py", "app.py", "run.py"]
    files = sorted(files, key=lambda x: (x not in priority, x.lower()))

    text = f"""
╭━━━〔 🚀 DEPLOY PANEL 〕━━━╮

👤 User: {uid}

━━━━━━━━━━━━━━━━━━━
📦 Bots: {len(files)}
⚡ Ready to Deploy
━━━━━━━━━━━━━━━━━━━

💡 Select file to start

🔝 Recommended:
main.py / bot.py

╰━━━━━━━━━━━━━━━━━━━
"""

    buttons = [
        [InlineKeyboardButton(
            text=("🚀 " if f in priority else "📄 ") + f,
            callback_data=f"run_{f}"
        )] for f in files
    ]

    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= AUTO RESTART =================

crash_count = {}

async def auto_restart(key, path):

    while True:

        await asyncio.sleep(3)

        if key not in running:
            break

        process = running[key]

        # 🔥 crashed
        if process.returncode is not None:

            uid = key.split("_")[0]
            crash_count[key] = crash_count.get(key, 0) + 1
            count = crash_count[key]

            if count >= 5:
                running.pop(key, None)

                try:
                    await bot.send_message(
                        int(uid),
                        f"""🚫 Bot stopped

🤖 {key.split("_",1)[1]}
💥 Crashes: {count}

💡 Fix code and restart"""
                    )
                except:
                    pass

                break

            delay = min(5 * count, 20)

            try:
                await bot.send_message(
                    int(uid),
                    f"⚠️ Crashed! Restarting in {delay}s (Attempt {count}/5)"
                )
            except:
                pass

            await asyncio.sleep(delay)

            try:
                new = await asyncio.create_subprocess_exec(
                    "python3", "-u", path,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )

                running[key] = new
                uptime[key] = asyncio.get_event_loop().time()

                asyncio.create_task(read_stream(key, new.stdout))

            except Exception as e:
                try:
                    await bot.send_message(
                        int(uid),
                        f"❌ Restart failed:\n{str(e)[:100]}"
                    )
                except:
                    pass
                break


# ================= RUN BOT =================

@dp.callback_query(F.data.startswith("run_"))
async def run_bot(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    file = call.data.replace("run_", "")
    key = f"{uid}_{file}"
    path = f"{BASE}/{uid}/{file}"

    if key in running:
        return await call.answer("⚠️ Already running", show_alert=True)

    msg = await call.message.edit_text("⏳ Starting deployment...")

    if not os.path.exists(path):
        return await msg.edit_text(
            "❌ File not found",
            reply_markup=panel(call.from_user.id)
        )

    # 🔥 steps
    steps = [
        "🔍 Checking file...",
        "⚙️ Preparing environment...",
        "📦 Installing requirements...",
        "🧠 Checking imports...",
        "🚀 Launching bot..."
    ]

    for step in steps:
        await msg.edit_text(f"⏳ {step}")
        await asyncio.sleep(0.5)

    # requirements
    req = f"{BASE}/{uid}/requirements.txt"
    if os.path.exists(req):
        try:
            subprocess.run(
                ["python3", "-m", "pip", "install", "-r", req],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            pass

    # imports
    await auto_install_libs(path)

    try:
        process = await asyncio.create_subprocess_exec(
            "python3", "-u", path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        running[key] = process
        logs[key] = ""
        uptime[key] = asyncio.get_event_loop().time()
        crash_count[key] = 0  # reset

        asyncio.create_task(read_stream(key, process.stdout))
        asyncio.create_task(auto_restart(key, path))

        controls = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("📜 Logs", callback_data=f"log_{file}"),
                    InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{file}")
                ],
                [
                    InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{file}")
                ],
                [
                    InlineKeyboardButton("⬅ Back", callback_data="back")
                ]
            ]
        )

        await msg.edit_text(
            f"""
╭━━━〔 ✅ DEPLOY SUCCESS 〕━━━╮

🤖 {file}
🟢 Running
⚡ Production Mode

━━━━━━━━━━━━━━━━━━━
📡 Logs: Active
🔄 Auto Restart: ON
━━━━━━━━━━━━━━━━━━━
""",
            reply_markup=controls
        )

    except Exception as e:

        await msg.edit_text(
            f"""
╭━━━〔 ❌ DEPLOY FAILED 〕━━━╮

⚠️ Error:
{str(e)[:500]}

💡 Fix code & retry
""",
            reply_markup=panel(call.from_user.id)
        )
        
        
# ================= RESTART BOT =================

@dp.callback_query(F.data.startswith("restart_"))
async def restart_bot(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    file = call.data.replace("restart_", "")
    key = f"{uid}_{file}"
    path = f"{BASE}/{uid}/{file}"

    if key in running:
        try:
            running[key].terminate()
            await asyncio.sleep(1)

            if running[key].returncode is None:
                running[key].kill()

        except:
            pass

        running.pop(key, None)
        uptime.pop(key, None)
        waiting_input.pop(key, None)

    # 🔥 clean restart (no recursion bug)
    call.data = f"run_{file}"
    await run_bot(call)


# ================= READ LOGS =================

async def read_stream(key, stream):

    trigger_words = ["phone", "code", "password", "otp", "token"]

    buffer = ""
    last_sent = ""
    last_install = set()

    while True:

        chunk = await stream.read(128)   # 🔥 faster + efficient
        if not chunk:
            break

        text = chunk.decode(errors="ignore")

        # 🔥 safe log memory
        logs[key] = (logs.get(key, "") + text)[-5000:]
        buffer += text

        lower = buffer.lower()

        # ================= INPUT DETECTION =================
        if any(word in lower for word in trigger_words):

            if key not in waiting_input:

                waiting_input[key] = True
                uid = key.split("_")[0]

                msg_preview = buffer[-200:]

                if msg_preview != last_sent:
                    last_sent = msg_preview

                    try:
                        await bot.send_message(
                            int(uid),
                            f"📟 Input required:\n\n{msg_preview}"
                        )
                    except:
                        pass

        # ================= AUTO INSTALL =================
        match = re.search(r"No module named '(.*?)'", buffer)

        if match:
            module = match.group(1)

            # 🔥 avoid duplicate install
            if module not in last_install:
                last_install.add(module)

                logs[key] += f"\n📦 Installing: {module}\n"

                try:
                    subprocess.run(
                        ["python3", "-m", "pip", "install", module],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                    logs[key] += f"✅ Installed: {module}\n"

                except Exception as e:
                    logs[key] += f"❌ Failed: {e}\n"

        # 🔥 buffer control
        if len(buffer) > 400:
            buffer = buffer[-200:]

        await asyncio.sleep(0.01)  # 🔥 CPU safe


# ================= STOP MENU =================

@dp.callback_query(F.data == "stop_menu")
async def stop_menu(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    user_bots = [k for k in running if k.startswith(uid)]

    if not user_bots:
        return await call.message.edit_text(
            "❌ No running bots",
            reply_markup=panel(call.from_user.id)
        )

    text = "╭━━━〔 🛑 STOP PANEL 〕━━━╮\n\n"
    buttons = []

    for key in user_bots:

        name = key.split("_", 1)[1]

        start = uptime.get(key, 0)
        seconds = int(asyncio.get_event_loop().time() - start)

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60

        text += f"🟢 {name}\n⏱ {h}h {m}m {s}s\n\n"

        buttons.append([
            InlineKeyboardButton(
                text=f"🛑 {name}",
                callback_data=f"stop_{name}"
            )
        ])

    text += "━━━━━━━━━━━━━━━━━━━\nSelect a bot to stop"

    buttons.append([
        InlineKeyboardButton("⬅ Back", callback_data="back")
    ])

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= STOP BOT =================

@dp.callback_query(F.data.startswith("stop_"))
async def stop_bot(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    file = call.data.replace("stop_", "")
    key = f"{uid}_{file}"

    if key not in running:
        return await call.message.edit_text(
            "❌ Bot not running",
            reply_markup=panel(call.from_user.id)
        )

    process = running[key]

    try:
        process.terminate()
        await asyncio.sleep(1)

        if process.returncode is None:
            process.kill()

    except:
        pass

    # 🔥 cleanup
    running.pop(key, None)
    uptime.pop(key, None)
    waiting_input.pop(key, None)

    await call.message.edit_text(
        f"""
╭━━━〔 🛑 BOT STOPPED 〕━━━╮

🤖 {file}
🔴 Status: Offline

💡 Bot stopped successfully
""",
        reply_markup=panel(call.from_user.id)
    )

# ================= DELETE MENU =================

@dp.callback_query(F.data == "delete_menu")
async def delete_menu(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    folder = f"{BASE}/{uid}"

    if not os.path.exists(folder):
        return await call.message.edit_text(
            "❌ No bots uploaded",
            reply_markup=panel(call.from_user.id)
        )

    files = [
        f for f in os.listdir(folder)
        if f.endswith(".py") and f not in user_deleted.get(uid, set())
    ]

    if not files:
        return await call.message.edit_text(
            "❌ No bots available",
            reply_markup=panel(call.from_user.id)
        )

    buttons = [
        [InlineKeyboardButton(text=f"🗑 {f}", callback_data=f"del_{f}")]
        for f in files
    ]

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "🗑 Select bot to remove",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= DELETE BOT (SAFE) =================

@dp.callback_query(F.data.startswith("del_"))
async def delete_bot(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    file = call.data.replace("del_", "")
    key = f"{uid}_{file}"

    # stop bot if running
    if key in running:
        try:
            running[key].terminate()
        except:
            pass

    # 🔥 cleanup
    running.pop(key, None)
    logs.pop(key, None)
    uptime.pop(key, None)
    waiting_input.pop(key, None)

    # 🔥 SAVE deleted state (IMPORTANT FIX)
    user_deleted.setdefault(uid, set()).add(file)
    save_deleted()

    await call.message.edit_text(
        f"🗑 {file} removed (safe mode)",
        reply_markup=panel(call.from_user.id)
    )


# ================= STATUS =================

@dp.callback_query(F.data == "status_bot")
async def status_bot(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)

    text = "📊 RUNNING BOTS\n\n"
    found = False

    for key in running:

        if key.startswith(uid):

            found = True
            name = key.split("_", 1)[1]

            start = uptime.get(key, 0)
            seconds = int(asyncio.get_event_loop().time() - start)

            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60

            text += f"🟢 {name}\n⏱ {h}h {m}m {s}s\n\n"

    if not found:
        text += "❌ No bots running"

    await call.message.edit_text(
        text,
        reply_markup=panel(call.from_user.id)
    )


# ================= LOG MENU =================

@dp.callback_query(F.data == "logs_menu")
async def logs_menu(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)

    bots = [
        k for k in logs
        if k.startswith(uid)
        and k.split("_", 1)[1] not in user_deleted.get(uid, set())
    ]

    if not bots:
        return await call.message.edit_text(
            "❌ No logs available",
            reply_markup=panel(call.from_user.id)
        )

    buttons = [
        [InlineKeyboardButton(text=b.split("_",1)[1], callback_data=f"log_{b.split('_',1)[1]}")]
        for b in bots
    ]

    buttons.append([InlineKeyboardButton(text="⬅ Back", callback_data="back")])

    await call.message.edit_text(
        "📜 Select bot logs",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= SHOW LOG =================

@dp.callback_query(F.data.startswith("log_"))
async def show_logs(call: types.CallbackQuery):

    await call.answer()

    uid = str(call.from_user.id)
    file = call.data.replace("log_", "")
    key = f"{uid}_{file}"

    text = logs.get(key, "No logs available")[-3500:]

    await call.message.edit_text(
        f"📜 LOGS ({file})\n\n{text}",
        reply_markup=panel(call.from_user.id)
    )


# ================= LIVE STATUS =================

@dp.callback_query(F.data == "live_status")
async def live_status(call: types.CallbackQuery):

    await call.answer()

    if not running:
        text = "⚡ LIVE STATUS\n\n❌ No bots running"
    else:
        text = "⚡ LIVE STATUS\n\n"
        for key in running:
            name = key.split("_", 1)[1]
            text += f"🟢 {name}\n"

    await call.message.edit_text(
        text,
        reply_markup=panel(call.from_user.id)
    )


# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):

    await call.answer()

    await call.message.edit_text(
        "🚀 HOSTING PANEL",
        reply_markup=panel(call.from_user.id)
    )


# ================= AUTO CLEAN LOGS =================

async def clean_logs():
    while True:
        await asyncio.sleep(60)

        for key in list(logs.keys()):
            logs[key] = logs[key][-3000:]


# ================= RUN =================

async def main():
    asyncio.create_task(clean_logs())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())