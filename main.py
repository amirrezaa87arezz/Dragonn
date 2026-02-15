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
def home(): return "Dragon VPN is Online!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس ---
DB_PATH = '/app/data'
DB_FILE = '/app/data/data.json'

def load_db():
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH, exist_ok=True)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {
        "users": {}, 
        "card": {"number": "6277601368776066", "name": "رضوانی"}, 
        "categories": {"ارزان و به صرفه": [], "قوی": []},
        "base_price": 50  # قیمت هر ۱۰ گیگ به تومان (پیش‌فرض ۵۰ هزار تومن)
    }

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
state = {}

def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

CANCEL_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"test_used": False, "purchases": []}
        save_db(db)
    state[uid] = None
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid_int = update.message.text, update.message.from_user.id
    uid = str(uid_int)

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        state[uid] = None
        await start(update, context)
        return

    # --- ادمین ---
    if uid_int == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف/ویرایش پلن'], ['ویرایش کارت', '⚙️ تنظیم قیمت واحد'], ['پیام همگانی', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        elif text == '⚙️ تنظیم قیمت واحد':
            state[uid] = 'set_base_price'
            await update.message.reply_text("لطفاً قیمت هر 10 گیگ (یک ماهه) را به تومان وارد کنید:\n(مثلاً: 50000)")
            return
        
        elif state.get(uid) == 'set_base_price':
            try:
                db["base_price"] = int(text) / 1000 # ذخیره به فرمت k
                save_db(db); state[uid] = None
                await update.message.reply_text(f"✅ قیمت پایه تنظیم شد. هر ۱۰ گیگ = {text} تومان", reply_markup=get_main_menu(uid))
            except: await update.message.reply_text("فقط عدد وارد کنید.")
            return

        # ارسال کانفیگ
        if isinstance(state.get(uid), dict) and state[uid].get('step') == 'send_cfg':
            info = state[uid]; target = str(info['target'])
            if target in db["users"] and info.get('is_new', True):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                save_db(db)
            final_msg = f"👤 سرویس: <code>{info.get('vpn_name', 'تمدیدی')}</code>\n⏳ مدت: {info.get('duration')}\n🗜 حجم: {info.get('vol')}\n\nلینک:\n<code>{text}</code>"
            await context.bot.send_message(target, final_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 آموزش", url="https://t.me/help_dragon")]]))
            await update.message.reply_text("✅ ارسال شد."); state[uid] = None; return

    # --- کاربر ---
    # مرحله دریافت حجم تمدید بصورت دستی (عدد)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'ren_get_vol':
        try:
            vol_val = int(text)
            month = int(state[uid]['duration'].replace('m',''))
            # فرمول محاسبه: (حجم / 10) * قیمت پایه ادمین * تعداد ماه
            total_price = int((vol_val / 10) * db.get("base_price", 50) * month)
            
            state[uid].update({'vol': f"{vol_val}G", 'price': total_price, 'step': 'wait_pay'})
            invoice = (f"📇 <b>پیش فاکتور تمدید هوشمند</b>\n"
                       f"⏳ مدت: {month} ماه\n"
                       f"🚀 حجم درخواستی: {vol_val} گیگ\n"
                       f"💶 مبلغ نهایی: {total_price},000 تومان")
            await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        except:
            await update.message.reply_text("⚠️ لطفاً حجم را فقط به صورت عدد (مثلاً 40) وارد کنید:")
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 خالی است."); return
        for p in purchases:
            btn = [[InlineKeyboardButton("🔄 تمدید این سرویس", callback_data=f"renstart_{uid}")]]
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup(btn))

    elif text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("renstart_"):
        kb = [[InlineKeyboardButton(f"{m} ماهه 📅", callback_data=f"rentime_{m}m")] for m in [1, 2, 3, 6, 12]]
        await query.message.reply_text("⏳ مدت زمان تمدید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rentime_"):
        state[uid] = {'step': 'ren_get_vol', 'duration': query.data.split("_")[1]}
        await query.message.reply_text("🚀 لطفاً مقدار حجم درخواستی خود را به <b>عدد</b> (گیگابایت) وارد کنید:\n(مثلاً: 40)", parse_mode='HTML', reply_markup=CANCEL_KB)

    elif query.data == "show_card":
        price = state[uid]['plan']['price'] if 'plan' in state[uid] else state[uid]['price']
        txt = f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n💰 <b>مبلغ: {price},000 تومان</b>\n👤 <b>بنام {db['card']['name']}</b>"
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]), parse_mode='HTML')
    
    elif query.data == "get_photo": await query.message.reply_text("📸 عکس فیش را بفرستید:")
    
    elif query.data.startswith("adm_pay_"):
        target = query.data.split("_")[2]
        is_new = 'plan' in state[target]
        state[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': int(target), 'is_new': is_new,
                               'vpn_name': state[target].get('vpn_name', 'تمدیدی'),
                               'vol': state[target]['plan']['name'] if is_new else state[target]['vol'],
                               'duration': 'نامحدود' if is_new else state[target]['duration']}
        await query.message.reply_text(f"پاسخ/لینک برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'wait_pay':
        btn = [[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_pay_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"فیش جدید از {uid}", reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش ارسال شد. منتظر تایید ادمین باشید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
