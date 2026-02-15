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
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data = {} 

def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "test_used": False, "raw_details": []}
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

    # --- بخش ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'پیام همگانی'], ['بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        # لاجیک حذف پلن
        if text == 'حذف پلن':
            for cat, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']} ({cat})", callback_data=f"del_{cat}_{p['id']}")]]
                    await update.message.reply_text(f"پلن: {p['name']}", reply_markup=InlineKeyboardMarkup(btn))
            return

        # ارسال کانفیگ
        if user_data.get(uid, {}).get('step') == 'send_cfg':
            info = user_data[uid]
            target = str(info['target'])
            # ذخیره اطلاعات برای تمدیدهای بعدی
            db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
            db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
            save_db(db)
            await context.bot.send_message(target, f"🚀 سرویس شما آماده شد:\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ ارسال شد."); user_data[uid] = {}
            return

    # --- بخش کاربر ---
    if user_data.get(uid, {}).get('step') == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        invoice = f"📇 <b>پیش فاکتور خرید</b>\n\n👤 نام: {text}\n🔐 پلن: {plan['name']}\n💶 مبلغ: {price:,} تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 لیست خالی است."); return
        for i, p in enumerate(purchases):
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))

    elif text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == 'پشتیبانی':
        await update.message.reply_text("🆘 پشتیبانی: @Dragon_Support")
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("📚 کانال آموزش: @help_dragon")

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    # تمدید هوشمند (بدون سوال اضافه)
    if query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        raw = db["users"][uid]["raw_details"][idx]
        user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price'], 'is_new': False}
        invoice = f"📇 <b>پیش فاکتور تمدید سرویس</b>\n\n👤 سرویس: {raw['name']}\n🚀 حجم: {raw['vol']}\n💶 مبلغ تمدید: {raw['price']:,} تومان\n\n(تمدید بر اساس خرید قبلی شما)"
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')

    elif query.data.startswith("del_"):
        _, cat, pid = query.data.split("_")
        db["categories"][cat] = [p for p in db["categories"][cat] if str(p['id']) != pid]
        save_db(db)
        await query.message.edit_text("✅ پلن با موفقیت حذف شد.")

    elif query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 نام اکانت را بفرستید (انگلیسی):")

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        txt = f"💳 کارت: <code>{db['card']['number']}</code>\n💰 مبلغ: {p:,} تومان\n👤 بنام: {db['card']['name']}"
        await query.message.reply_text(txt, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))

    elif query.data == "get_photo": await query.message.reply_text("📸 فیش را بفرستید:")

    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 
                                   'vol': user_data[target].get('vol'), 
                                   'vpn_name': user_data[target].get('vpn_name'), 
                                   'price': user_data[target].get('price'),
                                   'is_new': user_data[target].get('is_new', False)}
        await query.message.reply_text(f"لینک را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, 
                                     caption=f"فیش از {uid}\nمبلغ: {user_data[uid].get('price', 0):,}ت",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش ارسال شد. منتظر تایید ادمین باشید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
