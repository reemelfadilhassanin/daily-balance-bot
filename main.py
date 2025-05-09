from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3, datetime
from dotenv import load_dotenv
import os

# تحميل المتغيرات من ملف .env
load_dotenv()

# جلب التوكن من ملف .env
TOKEN = os.getenv("TOKEN")

# إنشاء قاعدة البيانات (إن لم تكن موجودة)
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, balance INTEGER, last_claimed TEXT)''')
    conn.commit()
    conn.close()

# دالة البدء عند التفاعل مع البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (user_id, balance, last_claimed) VALUES (?, ?, ?)", (user_id, 0, "1970-01-01"))
        conn.commit()
        await update.message.reply_text("👋 أهلاً بك! تم تسجيلك.\nاستخدم /daily للحصول على رصيدك اليومي.")
    else:
        await update.message.reply_text("👋 أنت مسجل مسبقاً.")
    conn.close()

# دالة عرض الرصيد
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        await update.message.reply_text(f"💰 رصيدك الحالي: {row[0]} د.ع")
    else:
        await update.message.reply_text("❗ لم يتم تسجيلك. استخدم /start.")
    conn.close()

# دالة إضافة الرصيد اليومي
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.datetime.now()
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT balance, last_claimed FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        last_claimed = datetime.datetime.fromisoformat(row[1])
        if (now - last_claimed).total_seconds() >= 86400:
            new_balance = row[0] + 250
            c.execute("UPDATE users SET balance = ?, last_claimed = ? WHERE user_id = ?", (new_balance, now.isoformat(), user_id))
            conn.commit()
            await update.message.reply_text("🎁 تم إضافة 250 د.ع إلى رصيدك اليومي!")
        else:
            remaining = 86400 - (now - last_claimed).total_seconds()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await update.message.reply_text(f"⏳ يمكنك المطالبة مجددًا بعد: {hours} ساعة و {minutes} دقيقة.")
    else:
        await update.message.reply_text("❗ لم يتم تسجيلك. استخدم /start.")
    conn.close()

# تشغيل البوت
if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily))
    print("Bot is running...")
    app.run_polling()
