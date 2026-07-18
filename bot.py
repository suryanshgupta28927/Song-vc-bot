"""
Telegram Voice Chat Music Bot
------------------------------
Plays music in a Telegram group's Voice Chat (VC) using Pyrogram + py-tgcalls.

Supports:
    - YouTube search / links   -> streamed via yt-dlp
    - Spotify track links      -> track name resolved (no audio API), then searched on YouTube

Requirements:
    pip install -r requirements.txt
    (also needs ffmpeg installed on the host)

Env vars needed (set these on Render / locally):
    API_ID          - from https://my.telegram.org
    API_HASH        - from https://my.telegram.org
    SESSION_STRING  - a Pyrogram user-session string (bot account can't join VC, must be a user account)
    BOT_TOKEN       - from @BotFather (for the command-handling bot identity)
"""

import os
import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict

import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class _HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass


def _run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
    server.serve_forever()


API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

if not (API_ID and API_HASH and SESSION_STRING and BOT_TOKEN):
    raise RuntimeError("Set API_ID, API_HASH, SESSION_STRING, BOT_TOKEN env vars first.")

# Bot account -> handles commands
bot = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User account (assistant) -> actually joins the VC and streams audio
user = Client("vc_assistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

call = PyTgCalls(user)

# Per-chat song queue: {chat_id: [ (title, stream_url), ... ]}
queues: dict[int, list] = defaultdict(list)

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch1",
}


def resolve_spotify_title(url: str) -> str | None:
    """Get a track's title/artist from Spotify's public oEmbed endpoint (no API key needed)."""
    import urllib.request
    import json

    try:
        oembed = f"https://open.spotify.com/oembed?url={url}"
        with urllib.request.urlopen(oembed, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("title")
    except Exception as e:
        logger.warning("Spotify resolve failed: %s", e)
        return None


def get_stream(query: str) -> tuple[str, str]:
    """Return (title, direct_audio_url) for a YouTube link/search query or Spotify link."""
    if "open.spotify.com" in query:
        title = resolve_spotify_title(query)
        query = title if title else query

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:  # search result list
            info = info["entries"][0]
        return info["title"], info["url"]


async def play_next(chat_id: int):
    if not queues[chat_id]:
        await call.leave_call(chat_id)
        return
    title, url = queues[chat_id].pop(0)
    await call.play(chat_id, MediaStream(url))
    logger.info("Now playing in %s: %s", chat_id, title)


@bot.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    await message.reply_text(
        "🎵 *VC Music Bot active!*\n\n"
        "Commands:\n"
        "• /play <song name or YouTube/Spotify link>\n"
        "• /skip — skip current song\n"
        "• /stop — stop and leave VC\n"
        "• /queue — show queue",
        parse_mode="Markdown",
    )


@bot.on_message(filters.command("play"))
async def play_cmd(_, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /play <song name or link>")
        return

    query = message.text.split(None, 1)[1]
    chat_id = message.chat.id
    status = await message.reply_text("🔎 Searching...")

    try:
        title, url = await asyncio.to_thread(get_stream, query)
    except Exception as e:
        await status.edit_text(f"❌ Couldn't find that: {e}")
        return

    queues[chat_id].append((title, url))
    await status.edit_text(f"✅ Queued: *{title}*", parse_mode="Markdown")

    try:
        # Not yet in a call in this chat -> join and start playing
        await call.play(chat_id, MediaStream(url))
        queues[chat_id].pop()  # already being played, remove the duplicate we just queued
    except Exception:
        pass  # already in a call -> stays queued, play_next() will pick it up


@bot.on_message(filters.command("skip"))
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id
    await play_next(chat_id)
    await message.reply_text("⏭ Skipped.")


@bot.on_message(filters.command("stop"))
async def stop_cmd(_, message: Message):
    chat_id = message.chat.id
    queues[chat_id].clear()
    try:
        await call.leave_call(chat_id)
    except Exception:
        pass
    await message.reply_text("⏹ Stopped and left VC.")


@bot.on_message(filters.command("queue"))
async def queue_cmd(_, message: Message):
    chat_id = message.chat.id
    q = queues[chat_id]
    if not q:
        await message.reply_text("Queue is empty.")
        return
    text = "\n".join(f"{i+1}. {t}" for i, (t, _) in enumerate(q))
    await message.reply_text(f"🎶 *Queue:*\n{text}", parse_mode="Markdown")


@call.on_stream_end()
async def stream_end_handler(_, update):
    await play_next(update.chat_id)


async def main():
    threading.Thread(target=_run_health_server, daemon=True).start()
    await user.start()
    await call.start()
    await bot.start()
    logger.info("VC Music Bot running.")
    await asyncio.Event().wait()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
