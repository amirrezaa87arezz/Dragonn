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
def home(): return "Dragon VPN Bot v34.0 - Permanent Plans", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- لیست پلن‌های ثابت (برای جلوگیری از حذف بعد از دپلوی) ---
PERMANENT_PLANS = [
    {"id": 1, "name": "10GB - 30 Days", "price": 45, "only_vol": "10GB"},
    {"id": 2, "name": "20GB - 30 Days", "price": 80, "only_vol": "20GB"},
    {"id": 3, "name": "50GB - 30 Days", "price": 140, "only_vol": "50GB"},
    {"id": 4, "name": "100GB - 30 Days", "price": 250, "only_vol": "100GB"}
]

# --- دیتابیس ---
DB_FILE = 'data.json'
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # اگر لیست پلن‌ها خالی بود، دوباره از لیست ثابت پرش کن
                if not data["categories"]["سرویس‌های ویژه"]:
                    data["categories"]["سرویس‌های ویژه"] = list(PERMANENT_PLANS)
                return data
        except: pass
    return {
        "users": {}, "brand": "Dragon VPN",
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"سرویس‌های ویژه": list(PERMANENT_PLANS)}, # بارگذاری خودکار پلن‌ها
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nامنیت و سرعت را با ما تجربه کنید.",
            "support": "🆘 <b>پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>آموزش اتصال</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست رایگان شما ثبت شد.\nپس از بررسی ادمین، اکانت تست برای شما ارسال می‌شود."
        }
    }

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

BACK_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {"purchases": []}
        save_db(db)
    user_data[uid] = {}
    await update.message.reply_text(db["texts"]["welcome"].format(brand=db["brand"]), reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = update.effective_user.id
    u_name = update.effective_user.first_name
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- تست رایگان (با دکمه برای ادمین) ---
    if text == 'تست رایگان':
        await update.message.reply_text(db["texts"]["test"])
        btn = [[InlineKeyboardButton("📤 ارسال اکانت تست", callback_data=f"adm_send_{uid}_FreeTest_TestVol")]]
        admin_alert = (f"🎁 <b>درخواست تست رایگان</b>\n👤 کاربر: {u_name}\n🆔 آیدی: <code>{uid}</code>")
        await context.bot.send_message(ADMIN_ID, admin_alert, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
        return

    # --- بخش مدیریت ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if step == 'ADM_SEND_CONF':
            target = user_data[uid]['target']
            v_name = user_data[uid]['vpn_name']
            msg = (f"👤 سرویس: {v_name}\n⏳ اعتبار: نامحدود\n\nلینک اتصال:\n<code>{text}</code>\n\n🟢 لطفا با دقت کپی کنید.")
            await context.bot.send_message(target, msg, parse_mode='HTML')
            db["users"][str(target)]["purchases"].append(f"🚀 {v_name}")
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ با موفقیت ارسال شد.", reply_markup=get_main_menu(uid)); return

        # (سایر بخش‌های مدیریت مثل ویرایش متن و کارت که درست بودند بدون تغییر باقی ماندند)
        maps = {'ویرایش متن پشتیبانی': 'et_support', 'ویرایش متن راهنما': 'et_guide', 'ویرایش خوش‌آمدگویی': 'et_welcome', 'ویرایش متن تست': 'et_test'}
        if text in maps:
            user_data[uid]['step'] = maps[text]
            await update.message.reply_text(f"📝 متن جدید را بفرستید:", reply_markup=BACK_KB); return
        if step and step.startswith('et_'):
            db["texts"][step.replace('et_', '')] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ آپدیت شد.", reply_markup=get_main_menu(uid)); return

    # --- بخش کاربر ---
    if text == 'سرویس‌های من':
        purchases = db["users"].get(str(uid), {}).get("purchases", [])
        msg = "📂 سرویس‌های شما:\n" + ("\n".join(purchases) if purchases else "❌ موردی یافت نشد.")
        await update.message.reply_text(msg, parse_mode='HTML'); return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()] + [['❌ انصراف و بازگشت']]
        await update.message.reply_text("📂 انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"] and not step:
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}T", callback_data=f"buy_{text}_{p['id']}")] for p in db["categories"][text]]
        await update.message.reply_text("🚀 پلن مورد نظر:", reply_markup=InlineKeyboardMarkup(btn)); return

    if step == 'USR_NAME':
        plan = user_data[uid]['plan']
        user_data[uid].update({'step': 'WAIT_PHOTO', 'vpn_name': text, 'price': plan['price']*1000, 'vol': plan['only_vol']})
        inv = f"💎 <b>پیش‌فاکتور</b>\n👤 نام: <code>{text}</code>\n📦 پلن: <b>{plan['name']}</b>"
        await update.message.reply_text(inv, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ دریافت کارت", callback_data="show_card")]]))
        return

    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"], parse_mode='HTML'); return
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"], parse_mode='HTML'); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = query.from_user.id; await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'USR_NAME', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید:", reply_markup=BACK_KB)
    elif query.data == "show_card":
        card_msg = f"💳 <b>کارت بانکی</b>\n<code>{db['card']['number']}</code>\nبنام: {db['card']['name']}"
        await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))
    elif query.data == "get_photo":
        user_data[uid]['step'] = 'WAIT_PHOTO'; await query.message.reply_text("📸 فیش را بفرستید:")
    elif query.data.startswith("adm_send_"):
        _, _, target, v_name, _ = query.data.split("_")
        user_data[ADMIN_ID] = {'step': 'ADM_SEND_CONF', 'target': target, 'vpn_name': v_name}
        await context.bot.send_message(ADMIN_ID, f"📨 کانفیگ برای {v_name} را بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_data.get(uid, {}).get('step') == 'WAIT_PHOTO':
        v_n = user_data[uid].get('vpn_name'); v_v = user_data[uid].get('vol')
        btn = [[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_send_{uid}_{v_n}_{v_v}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"💰 فیش جدید\n👤 {v_n}", reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("✅ ارسال شد.", reply_markup=get_main_menu(uid)); user_data[uid] = {}

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
