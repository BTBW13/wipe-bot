import discord
import re
import os

# ============================================================
#  KONFIGURATION – hier anpassen
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Channel-ID, der auf Wipe-Nachrichten überwacht wird (Pegasus Eye Channel)
WATCH_CHANNEL_ID = 1496309289701085304     # <-- ersetzen

# Channel-ID, in den die Alert-Nachricht gesendet wird (kann derselbe sein)
ALERT_CHANNEL_ID = 1502007942365446224       # <-- ersetzen

# Rolle, die gepingt werden soll (z. B. "DevWipe"). None = kein Ping
PING_ROLE_NAME = "DevWipe"                  # oder None für keinen Ping

# Nachricht die gesendet wird (wird unten dynamisch zusammengebaut)
ALERT_MESSAGE = "⚠️ **DEV WIPE** erkannt auf `{server}`!"

# ============================================================
#  BOT-LOGIK – nichts ändern nötig
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def parse_wipe_message(content: str):
    """
    Erkennt Pegasus Eye Wipe-Nachrichten.
    Erwartet Muster wie:
      Possible Dev wipe
      EU-PVP-SmallTribes-Aberration9367
      Tamed Dino Count: 324/2283 | -1959
    Gibt den Servernamen zurück oder None wenn kein Match.
    """
    # Prüfe ob "dev wipe" (case-insensitive) im Text steht
    if not re.search(r"dev\s*wipe", content, re.IGNORECASE):
        return None

    # Versuche Servernamen zu extrahieren (Zeile nach "wipe")
    lines = content.strip().splitlines()
    server_name = "Unbekannt"
    for i, line in enumerate(lines):
        if re.search(r"dev\s*wipe", line, re.IGNORECASE):
            # Nächste nicht-leere Zeile ist wahrscheinlich der Servername
            for next_line in lines[i + 1:]:
                stripped = next_line.strip()
                if stripped and not stripped.lower().startswith("tamed"):
                    server_name = stripped
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
    # Nur Nachrichten im überwachten Channel beachten
    if message.channel.id != WATCH_CHANNEL_ID:
        return

    # Eigene Nachrichten ignorieren
    if message.author == client.user:
        return

    # Embed-Text auch prüfen (Pegasus Eye sendet oft Embeds)
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
        return  # Keine Wipe-Nachricht

    print(f"🚨 Wipe erkannt! Server: {server_name}")

    # Alert-Channel holen
    alert_channel = client.get_channel(ALERT_CHANNEL_ID)
    if alert_channel is None:
        print("❌ Alert-Channel nicht gefunden. Channel-ID prüfen.")
        return

    # Rolle suchen
    ping_text = ""
    if PING_ROLE_NAME:
        role = discord.utils.get(message.guild.roles, name=PING_ROLE_NAME)
        if role:
            ping_text = role.mention + " "
        else:
            print(f"⚠️  Rolle '{PING_ROLE_NAME}' nicht gefunden.")

    # Nachricht senden
    alert_text = ping_text + ALERT_MESSAGE.format(server=server_name)
    await alert_channel.send(alert_text)
    print(f"✅ Alert gesendet: {alert_text}")


client.run(BOT_TOKEN)
