import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [
    "mhasaninejad",
    "hamedkamalpour",
]

# اگر User ID عددی داری اینجا اضافه کن (امن‌تره)
ADMIN_IDS = []  # مثال: [123456789, 987654321]

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.up.railway.app")  # بعد از دیپلوی تغییر بده
DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/stationery_products.db")

# تعداد نتایج در هر صفحه استعلام متنی
PAGE_SIZE = 10