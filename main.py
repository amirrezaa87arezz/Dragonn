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
def home(): return "Dragon VPN Bot v31.0 - FINAL PRO", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس ---
DB_FILE = 'data.json'
DEFAULT_PLANS = [
    {"id": 1, "name": "10GB - 30 Days", "price": 45, "only_vol": "10GB"},
    {"id": 2, "name": "20GB - 30 Days", "price": 80, "only_vol": "20GB"},
    {"id": 3, "name": "50GB - 30 Days", "price": 140, "only_vol": "50GB"},
    {"id": 4, "name": "100GB - 30 Days", "price": 250, "only_vol": "100GB"}
]

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {
        "users": {}, "brand": "Dragon VPN",
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"سرویس‌های ویژه": list(DEFAULT_PLANS)},
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nامنیت و سرعت را با ما تجربه کنید.",
            "support": "🆘 <b>پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>آموزش اتصال</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست شما ثبت شد. به زودی ارسال می‌شود."
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
    user_data[uid] = {}
    await update.message.reply_text(db["texts"]["welcome"].format(brand=db["brand"]), reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = update.effective_user.id
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- مدیریت ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("انتخاب بخش:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # فرآیند افزودن پلن
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ADM_CAT'
            kb = [[c] for c in db["categories"].keys()] + [['❌ انصراف و بازگشت']]
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'ADM_CAT':
            user_data[uid].update({'step': 'ADM_VOL', 'cat': text})
            await update.message.reply_text("حجم (مثلاً 50GB):", reply_markup=BACK_KB); return
        if step == 'ADM_VOL':
            user_data[uid].update({'step': 'ADM_PRICE', 'vol': text})
            await update.message.reply_text("قیمت (عدد به هزار تومان):"); return
        if step == 'ADM_PRICE':
            db["categories"][user_data[uid]['cat']].append({"id": 99, "name": user_data[uid]['vol'], "price": int(text), "only_vol": user_data[uid]['vol']})
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ انجام شد.", reply_markup=get_main_menu(uid)); return

        # ویرایش کارت
        if text == 'ویرایش کارت':
            user_data[uid]['step'] = 'ED_CARD'
            await update.message.reply_text("شماره کارت و نام صاحب را بفرستید:", reply_markup=BACK_KB); return
        if step == 'ED_CARD':
            db["card"]["number"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ ثبت شد.", reply_markup=get_main_menu(uid)); return

        # ارسال کانفیگ توسط ادمین
        if step == 'ADM_SEND_CONF':
            target = user_data[uid]['target']
            vpn_name = user_data[uid]['vpn_name']
            vol = user_data[uid]['vol']
            msg = (f"👤 نام کاربری سرویس : {vpn_name}\n⏳ مدت زمان: نامحدود\n🗜 حجم سرویس: {vol}\n\n"
                   f"لینک اتصال:\n<code>{text}</code>\n\n"
                   f"🟢 اگر لینک اضافه نشد از ربات @URLExtractor_Bot استفاده کنید.")
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/Guide_Channel")]])
            await context.bot.send_message(target, msg, parse_mode='HTML', reply_markup=kb)
            await update.message.reply_text("✅ برای کاربر ارسال شد.", reply_markup=get_main_menu(uid))
            user_data[uid] = {}; return

    # --- کاربر ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()] + [['❌ انصراف و بازگشت']]
        await update.message.reply_text("📂 انتخاب دسته بندی:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"] and not step:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}T", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text("🚀 پلن مورد نظر:", reply_markup=InlineKeyboardMarkup(btn)); return

    if step == 'USR_NAME':
        plan = user_data[uid]['plan']
        price = plan['price'] * 1000
        user_data[uid].update({'step': 'WAIT_PHOTO', 'vpn_name': text, 'price': price, 'vol': plan['only_vol']})
        inv = (f"💎 <b>پیش‌فاکتور خرید سرویس</b>\n"
               f"➖➖➖➖➖➖➖➖➖➖\n"
               f"👤 نام اکانت: <code>{text}</code>\n"
               f"📦 نوع پلن: <b>{plan['name']}</b>\n"
               f"💰 مبلغ نهایی: <b>{price:,} تومان</b>\n"
               f"➖➖➖➖➖➖➖➖➖➖\n"
               f"👇 جهت تایید و دریافت کارت کلیک کنید:")
        await update.message.reply_text(inv, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و مرحله بعد", callback_data="show_card")]]))
        return

    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"], parse_mode='HTML'); return
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"], parse_mode='HTML'); return
    if text == 'تست رایگان': await update.message.reply_text(db["texts"]["test"]); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = query.from_user.id; await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'USR_NAME', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت (انگلیسی) را بفرستید:", reply_markup=BACK_KB)
    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        card_msg = (f"💳 <b>اطلاعات واریز وجه</b>\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n"
                    f"💰 مبلغ قابل پرداخت: <b>{p:,} تومان</b>\n\n"
                    f"📍 شماره کارت (لمس کنید کپی شود):\n<code>{db['card']['number']}</code>\n\n"
                    f"👤 بنام: <b>{db['card']['name']}</b>\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n"
                    f"📸 لطفاً پس از واریز، عکس فیش را ارسال کنید.")
        await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]))
    elif query.data == "get_photo":
        user_data[uid]['step'] = 'WAIT_PHOTO'
        await query.message.reply_text("📸 اکنون عکس فیش واریزی را ارسال کنید:")
    elif query.data.startswith("adm_send_"):
        _, _, target, v_name, v_vol = query.data.split("_")
        user_data[ADMIN_ID] = {'step': 'ADM_SEND_CONF', 'target': target, 'vpn_name': v_name, 'vol': v_vol}
        await context.bot.send_message(ADMIN_ID, "📨 لطفاً کانفیگ را ارسال کنید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if user_data.get(uid, {}).get('step') == 'WAIT_PHOTO':
        v_name = user_data[uid].get('vpn_name', 'Amir')
        v_vol = user_data[uid].get('vol', '20GB')
        # ارسال به ادمین
        caption = f"💰 <b>فیش واریزی جدید</b>\n👤 آیدی: {uid}\n📝 نام اکانت: {v_name}\n📦 پلن: {v_vol}"
        btn = [[InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"adm_send_{uid}_{v_name}_{v_vol}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=caption, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("✅ فیش شما با موفقیت برای ادمین ارسال شد.\nبزودی سرویس شما ارسال می‌گردد.", reply_markup=get_main_menu(uid))
        user_data[uid] = {}

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo)) # هندلر عکس اضافه شد
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
