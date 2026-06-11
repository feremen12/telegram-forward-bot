# forward_bot.py

from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import os
from aiohttp import web

# ========== تنظیمات ==========
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# کانال مبدا (که می‌خوای از اون بخونی)
SOURCE_CHANNEL = "@alonews"   # مثلاً @bbcpersian یا ID عددی

# کانال مقصد (کانال خودت)
DEST_CHANNEL = -1003792554304      # مثلاً @my_channel

# حداکثر حجم ویدیو برای فوروارد (بر اساس مگابایت)
MAX_VIDEO_SIZE_MB = 5

# فیلتر کلمات - پیام‌هایی که این کلمات رو دارن فوروارد نمیشن
BLOCKED_WORDS = [
    "تبلیغ", "vpn" , "bet" ,
    "آگهی" , "بت"  , "کانال" ,
    "خرید" , 
    "کانفیگ" ,
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

def is_video_allowed(message):
    if not message.video and not message.document:
        return True

    media = message.video or message.document
    if media:
        size_mb = media.size / (1024 * 1024)
        if size_mb > MAX_VIDEO_SIZE_MB:
            print(f"❌ ویدیو بلاک شد - حجم: {size_mb:.1f} MB")
            return False
        else:
            print(f"✅ ویدیو مجاز - حجم: {size_mb:.1f} MB")

    return True

async def check_new_messages():
    global last_message_id
    try:
        messages = await client.get_messages(SOURCE_CHANNEL, limit=20)

        if not messages:
            return

        if last_message_id == 0:
            last_message_id = messages[0].id
            print(f"✅ شروع از پیام ID: {last_message_id}")
            return

        new_messages = [m for m in messages if m.id > last_message_id]

        if not new_messages:
            return

        new_messages = list(reversed(new_messages))

        # گروه‌بندی آلبوم‌ها
        grouped = {}
        singles = []

        for message in new_messages:
            if message.grouped_id:
                if message.grouped_id not in grouped:
                    grouped[message.grouped_id] = []
                grouped[message.grouped_id].append(message)
            else:
                singles.append(message)

        # فوروارد پیام‌های تکی
        for message in singles:
            text = getattr(message, 'text', '') or getattr(message, 'caption', '') or ""

            if not should_forward(text):
                last_message_id = message.id
                continue

            if not is_video_allowed(message):
                last_message_id = message.id
                continue

            await client.forward_messages(DEST_CHANNEL, message)
            print(f"✅ فوروارد شد: {text[:50]}...")
            last_message_id = message.id

        # فوروارد آلبوم‌ها بصورت دسته‌ای
        for group_id, group_messages in grouped.items():
            # چک فیلتر روی کپشن اولین پیام آلبوم
            first = group_messages[0]
            text = getattr(first, 'text', '') or getattr(first, 'caption', '') or ""

            if not should_forward(text):
                last_message_id = group_messages[-1].id
                continue

            # چک حجم ویدیوها
            skip = False
            for msg in group_messages:
                if not is_video_allowed(msg):
                    skip = True
                    break

            if skip:
                last_message_id = group_messages[-1].id
                continue

            # فوروارد کل آلبوم یکجا
            msg_ids = [m.id for m in group_messages]
            await client.forward_messages(DEST_CHANNEL, msg_ids, from_peer=SOURCE_CHANNEL)
            print(f"✅ آلبوم فوروارد شد ({len(group_messages)} فایل)")
            last_message_id = group_messages[-1].id

    except Exception as e:
        print(f"خطا: {e}")

async def polling_loop():
    print("حلقه چک کردن پیام‌ها شروع شد...")
    while True:
        await check_new_messages()
        await asyncio.sleep(CHECK_INTERVAL)

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
    asyncio.create_task(polling_loop())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
