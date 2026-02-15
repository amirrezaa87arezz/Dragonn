import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

app_web = Flask('')
@app_web.route('/')
def home(): return "Dragon VPN Admin Panel is Active!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات دیتابیس ---
DB_PATH = '/app/data'
DB_FILE = os.path.join(DB_PATH, 'data.json')

def load_db():
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH, exist_ok=True)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    # مقادیر اولیه در صورت نبود فایل
    return {
        "users": {},
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {
            "ارزان و به صرفه": [
                {"id": 1, "name": "20 گیگ نامحدود", "price": "130"},
                {"id": 2, "name": "30 گیگ نامحدود", "price": "160"}
            ],
            "قوی": [
                {"id": 3, "name": "50 گیگ یک‌ماهه", "price": "280"}
            ]
        }
    }

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
state = {}

# --- منوها ---
def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"test_used": False, "purchases": []}
        save_db(db)
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid_int = update.message.text, update.message.from_user.id
    uid = str(uid_int)

    # بخش مدیریت ادمین
    if uid_int == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['ویرایش پلن‌ها', 'ویرایش کارت'], ['پیام همگانی', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("پنل مدیریت ادمین:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        elif text == 'ویرایش کارت':
            state[uid] = 'edit_card_num'
            await update.message.reply_text("شماره کارت جدید را بفرستید:")
            return

        elif state.get(uid) == 'edit_card_num':
            db["card"]["number"] = text
            state[uid] = 'edit_card_name'
            await update.message.reply_text("نام صاحب کارت را بفرستید:")
            return

        elif state.get(uid) == 'edit_card_name':
            db["card"]["name"] = text
            save_db(db); state[uid] = None
            await update.message.reply_text("✅ اطلاعات کارت آپدیت شد.")
            return

        # ارسال کانفیگ/پاسخ تمدید
        if state.get(uid, {}).get('step') == 'wait_cfg':
            target = state[uid]['target']
            await context.bot.send_message(chat_id=target, text=f"✅ پیام جدید از ادمین:\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("ارسال شد."); state[uid] = None; return

    # منوی کاربر
    if text == 'بازگشت به منوی اصلی':
        state[uid] = None
        await start(update, context)
    
    elif text == 'خرید اشتراک':
        kb = [[cat] for cat in db["categories"].keys()]
        kb.append(['بازگشت به منوی اصلی'])
        await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == 'تست رایگان':
        if db["users"][uid].get("test_used"):
            await update.message.reply_text("❌ قبلاً استفاده شده.")
        else:
            await update.message.reply_text("🚀 درخواست ثبت شد.")
            btn = [[InlineKeyboardButton("ارسال تست 🎁", callback_data=f"adm_test_{uid}")]]
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"درخواست تست: {uid}", reply_markup=InlineKeyboardMarkup(btn))

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    await query.answer()

    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'plan': plan}
        txt = f"📇 فاکتور:\n🔐 سرویس: {plan['name']}\n💶 قیمت: {plan['price']},000 تومان"
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]))

    elif query.data == "show_card":
        txt = f"💳 شماره کارت:\n<code>{db['card']['number']}</code>\n👤 بنام: {db['card']['name']}"
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش 📸", callback_data="get_photo")]]), parse_mode='HTML')

    elif query.data == "get_photo":
        state[uid] = {'step': 'wait_photo'}
        await query.message.reply_text("عکس فیش را بفرستید:")

    elif query.data.startswith("adm_"):
        _, act, target = query.data.split("_")
        state[str(ADMIN_ID)] = {'step': 'wait_cfg', 'target': int(target)}
        await query.message.reply_text(f"لینک یا پیام را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if state.get(uid, {}).get('step') == 'wait_photo':
        btn = [[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_pay_{uid}")]]
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"فیش از {uid}", reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش برای ادمین ارسال شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
