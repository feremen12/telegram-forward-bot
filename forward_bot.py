# forward_bot.py

from telethon import TelegramClient, events
import asyncio
import os

# ========== تنظیمات ==========
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# کانال مبدا (که می‌خوای از اون بخونی)
SOURCE_CHANNEL =  "@testforwarder83"  # مثلاً @bbcpersian

# کانال مقصد (کانال خودت)
DEST_CHANNEL =  "@Aadmintester83"  # مثلاً @my_channel

# فیلتر کلمات - پیام‌هایی که این کلمات رو دارن فوروارد نمیشن
BLOCKED_WORDS = [
    "تبلیغ",
    "آگهی",
    "خرید",
    "فروش",
    # هر کلمه‌ای که می‌خوای اضافه کن
]

# فقط پیام‌هایی که این کلمات رو دارن فوروارد بشن (خالی = همه)
ALLOWED_WORDS = [
    # "اخبار",
    # "فوری",
]

# ==============================

client = TelegramClient('session', API_ID, API_HASH)

if SESSION_STRING:
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

def should_forward(text):
    if not text:
        return True

    text_lower = text.lower()

    # چک فیلتر کلمات ممنوع
    for word in BLOCKED_WORDS:
        if word.lower() in text_lower:
            print(f"❌ بلاک شد - کلمه ممنوع: {word}")
            return False

    # چک کلمات مجاز (اگه لیست خالی نباشه)
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

async def main():
    print("ربات شروع به کار کرد...")
    await client.start()
    print("متصل شد!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
