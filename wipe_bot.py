import discord
import re
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
 
# ============================================================
#  KONFIGURATION
# ============================================================
 
BOT_TOKEN = os.environ.get("BOT_TOKEN")
 
WATCH_CHANNEL_ID = 1496309289701085304
ALERT_CHANNEL_ID = 1502007942365446224
PING_ROLE_NAME = "DevWipe"
ALERT_MESSAGE = "⚠️ **DEV WIPE** erkannt auf `{server}`!"
 
# ============================================================
#  KEEP-ALIVE SERVER (damit Render den Bot nicht beendet)
# ============================================================
 
class KeepAlive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
 
    def log_message(self, format, *args):
        pass
 
def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAlive)
    server.serve_forever()
 
# ============================================================
#  BOT-LOGIK
# ============================================================
 
intents = discord.Intents.default()
intents.message_content = True
 
client = discord.Client(intents=intents)
 
 
def parse_wipe_message(content: str):
    if not re.search(r"dev\s*wipe", content, re.IGNORECASE):
        return None
 
    # Code-Block Formatierung entfernen (```ansi, ```fix, ``` etc.)
    clean = re.sub(r"```[a-z]*\n?", "", content)
    clean = clean.replace("```", "")
 
    lines = clean.strip().splitlines()
    server_name = "Unbekannt"
    for i, line in enumerate(lines):
        if re.search(r"dev\s*wipe", line, re.IGNORECASE):
            for next_line in lines[i + 1:]:
                stripped = next_line.strip()
                # Leerzeilen, "Tamed"-Zeilen und ANSI-Escape-Codes überspringen
                stripped_clean = re.sub(r"\x1b\[[0-9;]*m", "", stripped)
                if stripped_clean and not stripped_clean.lower().startswith("tamed"):
                    server_name = stripped_clean
                    break
            break
 
    return server_name
 
 
@client.event
async def on_ready():
    print(f"✅ Bot eingeloggt als: {client.user}")
    print(f"   Überwache Channel-ID : {WATCH_CHANNEL_ID}")
    print(f"   Alert Channel-ID     : {ALERT_CHANNEL_ID}")
    print(f"   Ping-Rolle           : {PING_ROLE_NAME or 'keine'}")
 
 
@client.event
async def on_message(message: discord.Message):
    if message.channel.id != WATCH_CHANNEL_ID:
        return
 
    if message.author == client.user:
        return
 
    full_text = message.content or ""
    for embed in message.embeds:
        if embed.title:
            full_text += "\n" + embed.title
        if embed.description:
            full_text += "\n" + embed.description
        for field in embed.fields:
            full_text += "\n" + field.value
 
    server_name = parse_wipe_message(full_text)
    if server_name is None:
        return
 
    print(f"🚨 Wipe erkannt! Server: {server_name}")
 
    alert_channel = client.get_channel(ALERT_CHANNEL_ID)
    if alert_channel is None:
        print("❌ Alert-Channel nicht gefunden.")
        return
 
    ping_text = ""
    if PING_ROLE_NAME:
        role = discord.utils.get(message.guild.roles, name=PING_ROLE_NAME)
        if role:
            ping_text = role.mention + " "
 
    alert_text = ping_text + ALERT_MESSAGE.format(server=server_name)
    await alert_channel.send(alert_text)
    print(f"✅ Alert gesendet: {alert_text}")
 
 
# Keep-Alive Server starten
threading.Thread(target=run_server, daemon=True).start()
print("🌐 Keep-Alive Server gestartet")
 
client.run(BOT_TOKEN)
