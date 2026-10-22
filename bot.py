import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---- Set these in Render > Environment (NOT in this file) ----
BOT_TOKEN = os.environ["BOT_TOKEN"]        # from @BotFather
API_KEY = os.environ["API_KEY"]            # your router API key
BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.environ.get("MODEL", "openai/gpt-4o-mini")
# --------------------------------------------------------------


async def ask_ai(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me a message and I'll reply.")


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = await ask_ai(update.message.text)
    except Exception as e:
        text = f"Error: {e}"
    await update.message.reply_text(text[:4000])


# Tiny web server so Render's free Web Service sees an open port
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()


def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.run_polling()


if __name__ == "__main__":
    main()
