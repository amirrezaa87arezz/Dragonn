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
def home(): return "Dragon VPN System is Online!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- مدیریت دیتابیس ---
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
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: logging.error("Error saving DB")

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data = {} # ذخیره موقت وضعیت کاربر

def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

RENEW_MENU = ReplyKeyboardMarkup([['🔄 تمدید سرویس فعلی'], ['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": []}
        save_db(db)
    user_data[uid] = {}
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.message.from_user.id)
    
    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context)
        return

    # --- پنل ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف/ویرایش پلن'], ['ویرایش کارت', '⚙️ تنظیم قیمت واحد'], ['پیام همگانی', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        # تنظیم قیمت واحد توسط ادمین
        if user_data.get(uid, {}).get('step') == 'set_base_price':
            try:
                db["base_price"] = int(text)
                save_db(db); user_data[uid] = {}
                await update.message.reply_text(f"✅ قیمت پایه تنظیم شد: {text} تومان", reply_markup=get_main_menu(uid))
            except: await update.message.reply_text("لطفا فقط عدد وارد کنید.")
            return

        # ارسال کانفیگ توسط ادمین
        if user_data.get(uid, {}).get('step') == 'send_cfg':
            info = user_data[uid]
            target = str(info['target'])
            if info.get('is_new'):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                save_db(db)
            
            msg = f"✅ سرویس شما آماده شد:\n👤 نام: {info['vpn_name']}\n🗜 حجم: {info['vol']}\n\nلینک اتصال:\n<code>{text}</code>"
            await context.bot.send_message(target, msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/help_dragon")]]))
            await update.message.reply_text("✅ با موفقیت برای کاربر ارسال شد."); user_data[uid] = {}
            return

    # --- پنل کاربر ---
    # مرحله وارد کردن اسم در خرید جدید
    if user_data.get(uid, {}).get('step') == 'get_name':
        plan = user_data[uid]['plan']
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': int(plan['price']) * 1000})
        invoice = f"📇 <b>پیش فاکتور خرید</b>\n\n👤 نام انتخابی: {text}\n🔐 پلن: {plan['name']}\n💶 مبلغ: {int(plan['price'])*1000:,} تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    # مرحله وارد کردن حجم در تمدید
    if user_data.get(uid, {}).get('step') == 'ren_get_vol':
        try:
            vol_val = int(text)
            month = int(user_data[uid]['duration'].replace('m',''))
            raw_price = (vol_val / 10) * db.get("base_price", 50000) * month
            # تخفیف
            disc = 0.05 if month == 3 else (0.10 if month == 6 else (0.20 if month >= 12 else 0))
            final_p = int(raw_price * (1 - disc))
            
            user_data[uid].update({'step': 'wait_pay', 'vol': f"{vol_val}G", 'price': final_p})
            invoice = f"📇 <b>پیش فاکتور تمدید</b>\n\n⏳ مدت: {month} ماه\n🚀 حجم: {vol_val} گیگ\n💶 مبلغ: {final_p:,} تومان"
            await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        except: await update.message.reply_text("⚠️ لطفا حجم را به عدد وارد کنید (مثلا 50):")
        return

    if text == '🔄 تمدید سرویس فعلی' and 'current_srv' in user_data.get(uid, {}):
        srv = user_data[uid]['current_srv']
        try:
            vol = int(srv.split('|')[0].replace('📦','').strip().replace('G',''))
            price = int((vol / 10) * db.get("base_price", 50000))
            user_data[uid].update({'step': 'wait_pay', 'vol': f"{vol}G", 'price': price, 'duration': '1 ماه', 'vpn_name': srv.split('|')[1].strip()})
            invoice = f"📇 <b>فاکتور تمدید سریع</b>\n\n👤 سرویس: {srv}\n💶 مبلغ تمدید (1 ماه): {price:,} تومان"
            await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        except: await update.message.reply_text("خطا در خواندن اطلاعات سرویس.")
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 شما هنوز سرویسی خریداری نکرده‌اید."); return
        for i, p in enumerate(purchases):
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید این سرویس", callback_data=f"ren_{i}")]]))

    elif text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("لطفا دسته بندی مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("پلنی در این دسته موجود نیست."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های دسته {text}:", reply_markup=InlineKeyboardMarkup(btn))

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 لطفا یک نام برای اکانت خود بفرستید (انگلیسی):", reply_markup=ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True))

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        srv = db["users"][uid]["purchases"][idx]
        user_data[uid] = {'current_srv': srv, 'is_new': False}
        kb = [[InlineKeyboardButton(f"{m} ماهه 📅", callback_data=f"rt_{m}m")] for m in [1, 2, 3, 6, 12]]
        await query.message.reply_text(f"💎 سرویس انتخاب شده: {srv}\n\nمدت زمان تمدید را انتخاب کنید:", reply_markup=RENEW_MENU, InlineKeyboardMarkup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rt_"):
        user_data[uid]['step'] = 'ren_get_vol'
        user_data[uid]['duration'] = query.data.split("_")[1]
        await query.message.reply_text("🚀 چه حجمی می‌خواهید؟ (عدد به گیگ وارد کنید):", reply_markup=RENEW_MENU)

    elif query.data == "show_card":
        price = user_data[uid].get('price', 0)
        txt = f"💳 <b>شماره کارت جهت واریز:</b>\n<code>{db['card']['number']}</code>\n\n💰 <b>مبلغ قابل پرداخت: {price:,} تومان</b>\n👤 بنام: {db['card']['name']}\n\n⚠️ پس از واریز، حتما عکس فیش را ارسال کنید."
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]), parse_mode='HTML')

    elif query.data == "get_photo":
        await query.message.reply_text("📸 لطفا عکس فیش واریزی خود را ارسال کنید:")

    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 
                                   'vol': user_data[target].get('vol', user_data[target].get('plan', {}).get('name')),
                                   'vpn_name': user_data[target].get('vpn_name', 'تمدیدی'),
                                   'is_new': user_data[target].get('is_new', False)}
        await query.message.reply_text(f"لطفا لینک کانفیگ را برای کاربر {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        price = user_data[uid].get('price', 0)
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, 
                                     caption=f"💰 فیش جدید رسید!\n🆔 آیدی کاربر: {uid}\n💵 مبلغ: {price:,} تومان",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال سرویس", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش شما دریافت شد و برای ادمین ارسال گردید. منتظر تایید بمانید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
