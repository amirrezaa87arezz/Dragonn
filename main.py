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

# --- دیتابیس ---
DB_PATH = '/app/data'
DB_FILE = '/app/data/data.json'

def load_db():
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH, exist_ok=True)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {"users": {}, "card": {"number": "6277601368776066", "name": "رضوانی"}, "categories": {"ارزان و به صرفه": [], "قوی": []}}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data = {}

# --- کیبوردها ---
def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
        save_db(db)
    user_data[uid] = {}
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید\n\nلطفا یکی از گزینه‌های زیر را جهت ادامه انتخاب کنید:", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.message.from_user.id)
    
    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context)
        return

    # --- پاسخ به دکمه‌های اصلی ---
    if text == 'راهنمای اتصال':
        await update.message.reply_text("📚 <b>راهنمای اتصال</b>\n\nبرای دریافت آموزش‌ها به کانال ما بپیوندید:\n🆔 @help_dragon", parse_mode='HTML')
        return

    if text == 'پشتیبانی':
        await update.message.reply_text("🆘 <b>واحد پشتیبانی</b>\n\nارتباط مستقیم با اپراتور:\n🆔 @Dragon_Support", parse_mode='HTML')
        return

    if text == 'تست رایگان':
        if db["users"].get(uid, {}).get("test_used"):
            await update.message.reply_text("⚠️ شما قبلاً تست رایگان دریافت کرده‌اید.")
        else:
            await update.message.reply_text("🚀 درخواست شما برای ادمین ارسال شد.")
            await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست از: {uid}", 
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال تست", callback_data=f"adm_ok_{uid}")]]))
        return

    # --- مدیریت ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        if user_data.get(uid, {}).get('step') == 'send_cfg':
            target = str(user_data[uid]['target'])
            info = user_data[uid]
            if info.get('is_new'):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
                save_db(db)
            await context.bot.send_message(target, f"🚀 سرویس شما آماده شد:\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ با موفقیت ارسال شد."); user_data[uid] = {}
            return

    # --- مراحل خرید ---
    if user_data.get(uid, {}).get('step') == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        
        invoice = (f"📑 <b>پیش فاکتور خرید سرویس</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 نام اکانت: <code>{text}</code>\n"
                   f"📦 نوع پلن: <b>{plan['name']}</b>\n"
                   f"💰 مبلغ قابل پرداخت: <b>{price:,} تومان</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"✅ جهت دریافت شماره کارت بر روی دکمه زیر کلیک کنید:")
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و مرحله بعد ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 شما هنوز اشتراک فعالی ندارید."); return
        for i, p in enumerate(purchases):
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))
        return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 لطفاً دسته بندی مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ پلنی در این دسته وجود ندارد."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 پلن‌های دسته {text}:", reply_markup=InlineKeyboardMarkup(btn))
        return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 لطفا یک نام برای اکانت خود (به انگلیسی) ارسال کنید:", reply_markup=BACK_KB)

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        raw = db["users"][uid]["raw_details"][idx]
        user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price'], 'is_new': False}
        invoice = (f"📑 <b>فاکتور تمدید سرویس</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 سرویس: <code>{raw['name']}</code>\n"
                   f"🚀 حجم: <b>{raw['vol']}</b>\n"
                   f"💰 مبلغ تمدید: <b>{raw['price']:,} تومان</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"تمدید بر اساس خرید قبلی شما انجام می‌شود.")
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و مرحله بعد ✅", callback_data="show_card")]]), parse_mode='HTML')

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        card_msg = (f"💳 <b>اطلاعات واریز</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"💰 مبلغ: <b>{p:,} تومان</b>\n"
                    f"📍 شماره کارت:\n<code>{db['card']['number']}</code>\n"
                    f"👤 بنام: <b>{db['card']['name']}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"⚠️ لطفاً پس از واریز، عکس فیش را ارسال کنید.")
        await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]))

    elif query.data == "get_photo":
        await query.message.reply_text("📸 لطفاً عکس فیش واریزی خود را در همین‌جا ارسال کنید:", reply_markup=BACK_KB)

    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 'vol': user_data.get(target, {}).get('vol', 'تست'), 'vpn_name': user_data.get(target, {}).get('vpn_name', 'تست'), 'price': user_data.get(target, {}).get('price', 0), 'is_new': user_data.get(target, {}).get('is_new', False)}
        await query.message.reply_text(f"لینک را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, 
                                     caption=f"💰 فیش جدید!\nUserID: {uid}\nمبلغ: {user_data[uid].get('price', 0):,}ت",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش شما با موفقیت برای مدیریت ارسال شد.\nلطفاً تا تایید نهایی صبور باشید.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
