import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# تنظیمات لاگ برای دیدن خطاها در کنسول
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app_web = Flask('')
@app_web.route('/')
def home(): return "Robot is ACTIVE!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس ساده و محلی ---
DB_FILE = 'data.json'

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    
    # ساختار اولیه در صورت نبود فایل
    init_db = {
        "users": {}, "brand": "Dragon VPN",
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"ارزان و به صرفه": [{"id": 1, "name": "50GB", "price": "100"}], "قوی": [{"id": 1, "name": "50GB", "price": "120"}]},
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nگزینه مورد نظر را انتخاب کنید:",
            "support": "🆘 پشتیبانی: @Support", "guide": "📚 راهنما: @Help", "test": "🚀 تست شما ارسال شد."
        }
    }
    save_db(init_db)
    return init_db

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data = {}

# --- منوی اصلی ---
def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if str(uid) == str(ADMIN_ID): kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- توابع اصلی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user: return
    uid = str(user.id)
    
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
        save_db(db)
    
    user_data[uid] = {}
    brand = db.get("brand", "Dragon VPN")
    text = db["texts"]["welcome"].format(brand=brand)
    await update.message.reply_text(text, reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = str(update.effective_user.id)
    step = user_data.get(uid, {}).get('step')

    # انصراف
    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- مدیریت ---
    if uid == str(ADMIN_ID):
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("انتخاب بخش:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # ذخیره ویرایش‌ها
        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ برند تغییر کرد.", reply_markup=get_main_menu(uid)); return
        
        if step and step.startswith('et_'):
            key = step.replace('et_', '')
            db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ آپدیت شد.", reply_markup=get_main_menu(uid)); return

        # افزودن پلن
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ap_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'ap_cat':
            user_data[uid].update({'step': 'ap_name', 'cat': text})
            await update.message.reply_text("نام پلن:", reply_markup=ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)); return
        if step == 'ap_name':
            user_data[uid].update({'step': 'ap_price', 'name': text})
            await update.message.reply_text("قیمت (مثلا 100):"); return
        if step == 'ap_price':
            c = user_data[uid]['cat']
            db["categories"][c].append({"id": len(db["categories"][c])+1, "name": user_data[uid]['name'], "price": text})
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ اضافه شد.", reply_markup=get_main_menu(uid)); return

        # حذف پلن
        if text == 'حذف پلن':
            for c, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']} ({c})", callback_data=f"del_{c}_{p['id']}")]]
                    await update.message.reply_text(f"📍 {p['name']}", reply_markup=InlineKeyboardMarkup(btn))
            return

        # فعالسازی ویرایش‌ها
        maps = {'ویرایش متن پشتیبانی':'et_support', 'ویرایش متن راهنما':'et_guide', 'ویرایش متن تست':'et_test', 'ویرایش خوش‌آمدگویی':'et_welcome', 'ویرایش برند':'ed_brand'}
        if text in maps:
            user_data[uid]['step'] = maps[text]
            await update.message.reply_text("متن جدید را بفرستید:", reply_markup=ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)); return

    # --- کاربر ---
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'تست رایگان':
        await update.message.reply_text(db["texts"]["test"].format(brand=db["brand"]), parse_mode='HTML')
        await context.bot.send_message(ADMIN_ID, f"🎁 تست از: {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال", callback_data=f"ok_{uid}")]]))
        return
    
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
    
    if text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text("پلن‌ها:", reply_markup=InlineKeyboardMarkup(btn)); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.data.startswith("del_"):
        _, c, pid = query.data.split("_")
        db["categories"][c] = [p for p in db["categories"][c] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ حذف شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
