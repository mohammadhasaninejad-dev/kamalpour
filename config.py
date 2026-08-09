import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [
    "mhasaninejad",
    "hamedkamalpour",
]

# ⚠️ مهم: یوزرنیم تلگرام قابل تغییره؛ تا وقتی این لیست خالیه، اگر یکی از ادمین‌ها
# یوزرنیمش رو عوض کنه، هر کس دیگه‌ای همون یوزرنیم رو بگیره دسترسی ادمین پیدا می‌کنه.
# برای گرفتن آیدی عددی: بعد از دیپلوی، از داخل خود بات دستور /myid یا دکمه «🆔 آیدی من» را بزنید.
ADMIN_IDS = []  # مثال: [123456789, 987654321]

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.up.railway.app")  # بعد از دیپلوی تغییر بده

# ⚠️ مهم: روی Railway (و اکثر هاست‌های ابری) مسیر /tmp بین ری‌استارت‌ها و دیپلوی‌های
# جدید پاک می‌شود و کل اطلاعات کالاها از بین می‌رود. حتماً یک Volume دائمی روی Railway
# بسازید و DATABASE_PATH را به مسیر همان Volume (مثلاً /data/products.db) تنظیم کنید.
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/products.db")

# تعداد نتایج در هر صفحه استعلام متنی
PAGE_SIZE = 10