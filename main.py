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
def home(): return "VPN Bot 27.0 - Stable Storage", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- مدیریت دیتابیس (تلاش برای پایداری بیشتر) ---
DB_FILE = 'data.json'
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # اطمینان از وجود بخش‌های ضروری
                if "categories" not in data: data["categories"] = {"ارزان و به صرفه": [], "قوی": []}
                return data
        except: pass
    return {
        "users": {}, "brand": "Dragon VPN",
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"ارزان و به صرفه": [], "قوی": []},
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nلطفا یکی از گزینه‌ها را انتخاب کنید:",
            "support": "🆘 <b>واحد پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>راهنمای اتصال {brand}</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست رایگان شما در {brand} ارسال شد."
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
    if str(uid) == str(ADMIN_ID): kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
        save_db(db)
    user_data[uid] = {}
    txt = db["texts"]["welcome"].format(brand=db["brand"])
    await update.message.reply_text(txt, reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = str(update.effective_user.id)
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- بخش مدیریت ---
    if uid == str(ADMIN_ID):
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # افزودن پلن (حجم -> کاربر -> قیمت)
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ap_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'ap_cat':
            user_data[uid].update({'step': 'ap_vol', 'cat': text})
            await update.message.reply_text("حجم پلن را وارد کنید (مثلا 20 گیگ):", reply_markup=BACK_KB); return
        if step == 'ap_vol':
            user_data[uid].update({'step': 'ap_user', 'vol': text})
            await update.message.reply_text("تعداد کاربر را وارد کنید (مثلا تک یا دو):"); return
        if step == 'ap_user':
            user_data[uid].update({'step': 'ap_price', 'user': text})
            await update.message.reply_text("قیمت را به عدد (هزار تومان) وارد کنید:"); return
        if step == 'ap_price':
            c = user_data[uid]['cat']
            p_name = f"{user_data[uid]['vol']} | {user_data[uid]['user']} کاربره"
            db["categories"][c].append({"id": len(db["categories"][c])+1, "name": p_name, "price": int(text), "only_vol": user_data[uid]['vol']})
            db["categories"][c] = sorted(db["categories"][c], key=lambda x: x['price'])
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن با موفقیت ذخیره شد.", reply_markup=get_main_menu(uid)); return

        # ارسال کانفیگ توسط ادمین (با متن درخواستی شما)
        if step == 'admin_send_config':
            target_id = user_data[uid]['target']
            vpn_name = user_data[uid].get('vpn_name', 'Amir')
            vol_size = user_data[uid].get('vol_only', '20 گیگ')
            
            user_msg = (f"👤 نام کاربری سرویس : {vpn_name}\n"
                        f"⏳ مدت زمان: نامحدود\n"
                        f"🗜 حجم سرویس: {vol_size}\n\n"
                        f"لینک اتصال:\n<code>{text}</code>\n\n"
                        f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید\n\n"
                        f"🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه.\n"
                        f"🔵 کافیه لینک ساب خودتون رو بهش بدید.")
            
            kb_guide = InlineKeyboardMarkup([[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/Guide_Channel")]])
            
            await context.bot.send_message(target_id, user_msg, parse_mode='HTML', reply_markup=kb_guide)
            
            # ذخیره در تاریخچه
            db["users"][target_id]["purchases"].append(f"📦 {vol_size} | {vpn_name}")
            save_db(db)
            await update.message.reply_text("✅ کانفیگ با متن حرفه‌ای برای کاربر ارسال شد.", reply_markup=get_main_menu(uid))
            user_data[uid] = {}; return

    # --- بخش کاربر ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 دسته بندی مورد نظر:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ پلنی یافت نشد."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']},000ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 لیست پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

    if step == 'get_vpn_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol_info': plan['name'], 'vol_only': plan.get('only_vol', 'نامشخص')})
        inv = (f"📑 <b>پیش فاکتور خرید {db['brand']}</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"👤 نام اکانت: <code>{text}</code>\n"
               f"📦 نوع پلن: <b>{plan['name']}</b>\n"
               f"💰 مبلغ: <b>{price:,} تومان</b>\n"
               f"━━━━━━━━━━━━━━━")
        await update.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت کارت 💳", callback_data="show_card")]]), parse_mode='HTML')
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        adm_msg = f"💰 <b>فیش واریزی جدید</b>\n👤 آیدی: {uid}\n📦 پلن: {user_data[uid]['vol_info']}"
        btn = [[InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"adm_send_{uid}_{user_data[uid]['vpn_name']}_{user_data[uid]['vol_only']}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=adm_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش برای ادمین ارسال شد. منتظر بمانید."); user_data[uid]['step'] = None

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید (انگلیسی):", reply_markup=BACK_KB)
    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        msg = f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n👤 <b>بنام:</b> {db['card']['name']}\n💰 <b>مبلغ:</b> {p:,} تومان"
        await query.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))
    elif query.data == "get_photo":
        user_data[uid]['step'] = 'wait_pay'; await query.message.reply_text("📸 فیش را بفرستید:")
    elif query.data.startswith("adm_send_"):
        _, _, target_id, v_name, v_only = query.data.split("_")
        user_data[str(ADMIN_ID)] = {'step': 'admin_send_config', 'target': target_id, 'vpn_name': v_name, 'vol_only': v_only}
        await context.bot.send_message(ADMIN_ID, f"📨 کانفیگ را برای کاربر <code>{target_id}</code> بفرستید:", parse_mode='HTML')

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
