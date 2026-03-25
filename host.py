import os
import subprocess
import threading
import time
import psutil
from flask import Flask
from telethon import TelegramClient, events, Button

# ===== CONFIG =====
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
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

# ===== TELEGRAM =====
bot = TelegramClient("manager", api_id, api_hash).start(bot_token=bot_token)

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
@bot.on(events.NewMessage(pattern="/access"))
async def access(event):
    if event.sender_id != OWNER_ID:
        return
    try:
        uid = int(event.raw_text.split()[1])
        allowed_users.add(uid)
        await event.reply(f"✅ Access Granted: {uid}")
    except:
        await event.reply("Usage: /access user_id")

@bot.on(events.NewMessage(pattern="/ban"))
async def ban(event):
    if event.sender_id != OWNER_ID:
        return
    try:
        uid = int(event.raw_text.split()[1])
        allowed_users.discard(uid)
        await event.reply(f"🚫 Banned: {uid}")
    except:
        await event.reply("Usage: /ban user_id")

# ===== START MENU =====
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    uid = event.sender_id

    if not is_allowed(uid):
        await event.reply("❌ Not allowed")
        return

    user_settings.setdefault(uid, {"auto_req": True})

    await event.respond(
        "🚀 **Telegram Bot Hosting Panel**\n\n"
        "✨ Upload, manage & run bots like hosting\n",
        buttons=[
            [Button.inline("📂 Upload", b"upload")],
            [Button.inline("⚙ Requirements", b"req")],
            [Button.inline("▶ Start Bot", b"startbot")],
            [Button.inline("🛑 Stop Bot", b"stopbot")],
            [Button.inline("📊 Status", b"status")]
        ]
    )
    
# ===== BUTTON HANDLER (CRASH PROOF) =====
@bot.on(events.CallbackQuery)
async def buttons(event):
    uid = event.sender_id
    data = event.data.decode()
    path = user_dir(uid)

    if not is_allowed(uid):
        await event.answer("Not allowed", alert=True)
        return

    try:

        # ===== STATUS =====
        if data == "status":
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            bots = running_bots.get(uid, {})

            await event.edit(
                f"📊 STATUS\n\nCPU: {cpu}%\nRAM: {ram}%\nDisk: {disk}%\n\nRunning Bots: {len(bots)}"
            )

        # ===== UPLOAD MENU =====
        elif data == "upload":
            await event.edit("📂 Upload Menu", buttons=[
                [Button.inline("➕ Add File", b"addfile")],
                [Button.inline("🗑 Delete File", b"delfile")],
                [Button.inline("📁 View Files", b"viewfile")],
                [Button.inline("🔙 Back", b"back")]
            ])

        elif data == "viewfile":
            files = os.listdir(path)
            await event.edit("📁 Files:\n" + ("\n".join(files) or "Empty"))

        elif data == "delfile":
            files = os.listdir(path)
            if not files:
                await event.answer("No files", alert=True)
                return

            btns = [[Button.inline(f, f"del_{f}".encode())] for f in files]
            await event.edit("Select file:", buttons=btns)

        elif data.startswith("del_"):
            fname = data.replace("del_", "")
            file_path = os.path.join(path, fname)

            if not os.path.exists(file_path):
                await event.edit("❌ File not found")
                return

            try:
                os.remove(file_path)
                await event.edit(f"🗑 Deleted: {fname}")
            except Exception as e:
                await event.edit(f"❌ Delete error:\n{e}")

        # ===== REQUIREMENTS =====
        elif data == "req":
            status = "ON" if user_settings[uid]["auto_req"] else "OFF"
            await event.edit(
                f"⚙ Requirements (Auto: {status})",
                buttons=[
                    [Button.inline("🔁 Toggle", b"toggle")],
                    [Button.inline("🔙 Back", b"back")]
                ]
            )

        elif data == "toggle":
            user_settings[uid]["auto_req"] = not user_settings[uid]["auto_req"]
            await event.answer("✅ Toggled")

        # ===== START BOT =====
        elif data == "startbot":
            files = [f for f in os.listdir(path) if f.endswith(".py")]

            if not files:
                await event.answer("❌ No .py files found", alert=True)
                return

            btns = [[Button.inline(f, f"run_{f}".encode())] for f in files]
            await event.edit("Select bot:", buttons=btns)

        elif data.startswith("run_"):
            fname = data.replace("run_", "")
            file_path = os.path.join(path, fname)

            if not os.path.exists(file_path):
                await event.edit("❌ File not found")
                return

            await event.edit(f"⚙ Starting {fname}...\nInstalling requirements...")

            # ===== INSTALL REQUIREMENTS SAFE =====
            req = os.path.join(path, "requirements.txt")
            if user_settings[uid]["auto_req"] and os.path.exists(req):
                result = subprocess.run(
                    ["pip", "install", "-r", req],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    await event.edit(f"❌ Requirements failed:\n{result.stderr[:1000]}")
                    return

            # ===== START PROCESS =====
            proc = subprocess.Popen(
                ["python", file_path],
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

            await event.edit(f"🚀 Running: {fname}")

        # ===== STOP BOT =====
        elif data == "stopbot":
            bots = running_bots.get(uid, {})

            if not bots:
                await event.answer("❌ No running bots", alert=True)
                return

            btns = [[Button.inline(b, f"stop_{b}".encode())] for b in bots]
            await event.edit("Select bot:", buttons=btns)

        elif data.startswith("stop_"):
            name = data.replace("stop_", "")

            if name not in running_bots.get(uid, {}):
                await event.edit("❌ Bot already stopped")
                return

            proc = running_bots[uid][name]

            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()

            del running_bots[uid][name]
            bot_inputs.get(uid, {}).pop(name, None)

            await event.edit(f"🛑 Stopped: {name}")

        elif data == "back":
            await start(event)

    except Exception as e:
        await event.edit(f"❌ Error:\n{str(e)[:1000]}")
        


# ===== FILE UPLOAD + SMART INPUT =====
@bot.on(events.NewMessage)
async def handle_msg(event):
    uid = event.sender_id
    path = user_dir(uid)

    if not is_allowed(uid):
        return

    # ===== FILE UPLOAD =====
    if event.file:
        name = event.file.name

        try:
            if name == "requirements.txt":
                await event.download_media(file=os.path.join(path, name))
                await event.reply("✅ requirements.txt uploaded")
            else:
                await event.download_media(file=path)
                await event.reply(f"✅ Uploaded: {name}")
        except Exception as e:
            await event.reply(f"❌ Upload failed:\n{e}")
        return

    # ===== SMART INPUT SYSTEM =====
    if uid in user_states:
        state = user_states[uid]
        bot_name = state["bot"]

        proc = bot_inputs.get(uid, {}).get(bot_name)

        if proc:
            try:
                proc.stdin.write(event.raw_text + "\n")
                proc.stdin.flush()

                await event.reply("✅ Input received")

            except Exception as e:
                await event.reply(f"❌ Input error:\n{e}")
        return


# ===== MONITOR + PROFESSIONAL TELETHON FLOW =====
def monitor_bot(uid, name, proc):
    try:
        for line in proc.stdout:
            text = line.strip()
            print(text)

            lower = text.lower()

            # ===== TELETHON LOGIN DETECTION =====
            if "phone" in lower:
                user_states[uid] = {"bot": name, "step": "phone"}

                bot.send_message(
                    uid,
                    f"📱 **Login Required ({name})**\n\n"
                    "Enter your Telegram phone number\n"
                    "Example: +91XXXXXXXXXX"
                )

            elif "code" in lower:
                user_states[uid] = {"bot": name, "step": "code"}

                bot.send_message(
                    uid,
                    f"🔢 **OTP Verification ({name})**\n\n"
                    "Enter the OTP you received"
                )

            elif "password" in lower:
                user_states[uid] = {"bot": name, "step": "password"}

                bot.send_message(
                    uid,
                    f"🔐 **2FA Enabled ({name})**\n\n"
                    "Enter your 2FA password"
                )

            else:
                # ===== CLEAN LOG SYSTEM =====
                if len(text) > 5 and not any(x in lower for x in ["debug", "info"]):
                    bot.send_message(uid, f"📜 {text[:150]}")

        # ===== PROCESS END =====
        proc.wait()

        # remove state after finish
        user_states.pop(uid, None)

        if proc.returncode != 0:
            bot.send_message(
                uid,
                f"❌ **Bot Crashed: {name}**\n\n"
                "Check your code / requirements / API keys."
            )
        else:
            bot.send_message(uid, f"⚠️ **Bot Stopped: {name}**")

    except Exception as e:
        bot.send_message(uid, f"❌ Monitor error:\n{e}")


# ===== RUN =====
print("🔥 Ultra Bot Running...")
bot.run_until_disconnected()