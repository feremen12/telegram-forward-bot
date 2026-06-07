# forward_bot.py

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
from aiohttp import web

# ========== تنظیمات ==========
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# کانال مبدا (که می‌خوای از اون بخونی)
SOURCE_CHANNEL = "@AdsVipz" # مثلاً @bbcpersian

# کانال مقصد (کانال خودت)
DEST_CHANNEL = "@testmaghsad83"   # مثلاً @my_channel

# فیلتر کلمات - پیام‌هایی که این کلمات رو دارن فوروارد نمیشن
BLOCKED_WORDS = [
    "تبلیغ",
    "آگهی",
    "خرید",
    "فروش",
]

# فقط پیام‌هایی که این کلمات رو دارن فوروارد بشن (خالی = همه)
ALLOWED_WORDS = [
]

# ==============================

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def should_forward(text):
    if not text:
        return True

    text_lower = text.lower()

    for word in BLOCKED_WORDS:
        if word.lower() in text_lower:
            print(f"❌ بلاک شد - کلمه ممنوع: {word}")
            return False

    if ALLOWED_WORDS:
        for word in ALLOWED_WORDS:
            if word.lower() in text_lower:
                return True
        print("❌ بلاک شد - کلمه مجاز پیدا نشد")
        return False

    return True

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    try:
        message = event.message
        text = getattr(message, 'text', '') or getattr(message, 'caption', '') or ""

        if should_forward(text):
            await client.forward_messages(DEST_CHANNEL, message)
            print(f"✅ فوروارد شد: {text[:50]}...")

    except Exception as e:
        print(f"خطا: {e}")

# وب سرور کوچیک برای اینکه Railway نخوابه
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"وب سرور روی پورت {port} شروع شد")

async def main():
    print("ربات شروع به کار کرد...")
    await start_web_server()
    await client.start()
    print("متصل شد!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
