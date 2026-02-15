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
def home(): return "Dragon VPN Online!", 200

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
    return {"users": {}, "card": {"number": "6277601368776066", "name": "رضوانی"}, "categories": {"ارزان و به صرفه": [], "قوی": []}, "base_price": 50000}

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

RENEW_MENU = ReplyKeyboardMarkup([['🔄 تمدید سرویس فعلی'], ['❌ انصراف و بازگشت']], resize_keyboard=True)

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
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        elif text == '⚙️ تنظیم قیمت واحد':
            state[uid] = 'set_base_price'
            await update.message.reply_text("قیمت هر 10 گیگ (یک ماهه) را به تومان وارد کنید:")
            return
        elif state.get(uid) == 'set_base_price':
            try:
                db["base_price"] = int(text); save_db(db); state[uid] = None
                await update.message.reply_text(f"✅ تنظیم شد: {text} تومان", reply_markup=get_main_menu(uid))
            except: await update.message.reply_text("عدد بفرستید.")
            return

    # --- کاربر ---
    # تمدید سریع سرویس فعلی
    if text == '🔄 تمدید سرویس فعلی' and uid in state and 'current_srv' in state[uid]:
        srv_info = state[uid]['current_srv']
        try:
            # استخراج حجم از متن سرویس: "📦 100G | ..."
            vol_str = srv_info.split('|')[0].replace('📦','').strip().replace('G','')
            vol_val = int(vol_str)
            price = int((vol_val / 10) * db.get("base_price", 50000))
            state[uid].update({'vol': f"{vol_val}G", 'price': price, 'duration': '1 ماه', 'step': 'wait_pay'})
            invoice = f"📇 <b>فاکتور تمدید سرویس فعلی</b>\n\n👤 {srv_info}\n⏳ مدت: 1 ماه\n💶 مبلغ: {price:,} تومان"
            await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')
        except: await update.message.reply_text("خطا در تمدید خودکار. لطفاً دستی وارد کنید.")
        return

    # دریافت حجم دستی
    if uid in state and isinstance(state[uid], dict) and state[uid].get('step') == 'ren_get_vol':
        try:
            vol_val = int(text)
            month = int(state[uid]['duration'].replace('m',''))
            raw_price = (vol_val / 10) * db.get("base_price", 50000) * month
            discount = 0.05 if month == 3 else (0.10 if month == 6 else (0.20 if month >= 12 else 0))
            final_price = int(raw_price * (1 - discount))
            state[uid].update({'vol': f"{vol_val}G", 'price': final_price, 'step': 'wait_pay'})
            await update.message.reply_text(f"📇 <b>فاکتور تمدید</b>\n\n⏳ {month} ماهه\n🚀 {vol_val} گیگ\n💶 {final_price:,} تومان", 
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')
        except: await update.message.reply_text("عدد وارد کنید:")
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 لیست خالی است."); return
        for i, p in enumerate(purchases):
            btn = [[InlineKeyboardButton("🔄 تمدید این سرویس", callback_data=f"renew_{i}")]]
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
    
    if query.data.startswith("renew_"):
        idx = int(query.data.split("_")[1])
        srv_name = db["users"][uid]["purchases"][idx]
        state[uid] = {'current_srv': srv_name}
        kb = [[InlineKeyboardButton(f"{m} ماهه 📅", callback_data=f"rentime_{m}m")] for m in [1, 2, 3, 6, 12]]
        await query.message.reply_text(f"💎 سرویس: {srv_name}\n\nمدت تمدید را انتخاب کنید یا از دکمه پایین استفاده کنید:", 
                                        reply_markup=RENEW_MENU, InlineKeyboardMarkup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rentime_"):
        state[uid].update({'step': 'ren_get_vol', 'duration': query.data.split("_")[1]})
        await query.message.reply_text("🚀 مقدار حجم درخواستی (عدد گیگابایت):", reply_markup=RENEW_MENU)

    elif query.data == "show_card":
        p = state[uid].get('price', 0)
        if 'plan' in state[uid]: p = int(state[uid]['plan']['price']) * 1000
        txt = f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n💰 <b>مبلغ: {p:,} تومان</b>\n👤 <b>بنام {db['card']['name']}</b>"
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]), parse_mode='HTML')

    elif query.data == "get_photo": await query.message.reply_text("📸 فیش را بفرستید:")
    
    elif query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت (انگلیسی):", reply_markup=ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True))

    elif query.data.startswith("adm_pay_"):
        target = query.data.split("_")[2]
        is_new = 'plan' in state[target]
        state[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': int(target), 'is_new': is_new,
                               'vpn_name': state[target].get('vpn_name', 'تمدیدی'),
                               'vol': state[target]['plan']['name'] if is_new else state[target]['vol'],
                               'duration': 'نامحدود' if is_new else state[target]['duration']}
        await query.message.reply_text(f"لینک/پاسخ برای {target}:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid in state and isinstance(state[uid], dict) and state[uid].get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, 
                                     caption=f"فیش جدید از {uid}\nمبلغ: {state[uid].get('price', 0):,}ت",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_pay_{uid}")]]))
        await update.message.reply_text("🚀 ارسال شد. منتظر تایید ادمین باشید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
