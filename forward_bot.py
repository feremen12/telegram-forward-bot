# forward_bot.py

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
from aiohttp import web
from datetime import datetime, timezone

# ========== تنظیمات ==========
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# کانال مبدا (که می‌خوای از اون بخونی)
SOURCE_CHANNEL = "@FO_RK"   # مثلاً @bbcpersian یا ID عددی

# کانال مقصد (کانال خودت)
DEST_CHANNEL = -1003792554304   # مثلاً @my_channel

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

# هر چند ثانیه کانال رو چک کنه (60 = یک دقیقه)
CHECK_INTERVAL = 60

# ==============================

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH,
    device_model="Server",
    system_version="Linux",
    app_version="1.0"
)

# آخرین ID پیامی که فوروارد شده
last_message_id = 0

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

async def check_new_messages():
    global last_message_id
    try:
        messages = await client.get_messages(SOURCE_CHANNEL, limit=10)
        
        if not messages:
            return
            
        # اولین بار که اجرا میشه، آخرین ID رو ذخیره کن
        if last_message_id == 0:
            last_message_id = messages[0].id
            print(f"✅ شروع از پیام ID: {last_message_id}")
            return
        
        # پیام‌های جدید رو پیدا کن
        new_messages = [m for m in messages if m.id > last_message_id]
        
        if new_messages:
            # از قدیمی به جدید فوروارد کن
            for message in reversed(new_messages):
                text = getattr(message, 'text', '') or getattr(message, 'caption', '') or ""
                if should_forward(text):
                    await client.forward_messages(DEST_CHANNEL, message)
                    print(f"✅ فوروارد شد: {text[:50]}...")
                last_message_id = message.id
                
    except Exception as e:
        print(f"خطا در چک کردن پیام‌ها: {e}")

async def polling_loop():
    print("حلقه چک کردن پیام‌ها شروع شد...")
    while True:
        await check_new_messages()
        await asyncio.sleep(CHECK_INTERVAL)

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
    
    # هم listener و هم polling
    asyncio.create_task(polling_loop())
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
