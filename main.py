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
def home(): return "VPN Bot 28.0 - FULL ACTIVE", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس با قابلیت بازیابی ---
DB_FILE = 'data.json'
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
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
        db["users"][uid] = {"purchases": [], "test_used": False}
    save_db(db)
    user_data[uid] = {}
    await update.message.reply_text(db["texts"]["welcome"].format(brand=db["brand"]), reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = str(update.effective_user.id)
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- فرآیند خرید (برای کاربر) ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ فعلاً پلنی در این دسته نیست."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']},000ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 لیست پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

    if step == 'get_vpn_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol_only': plan.get('only_vol', '20GB')})
        inv = f"📑 <b>پیش‌فاکتور خرید</b>\n━━━━━━━━━━━━━━━\n👤 نام اکانت: <code>{text}</code>\n📦 پلن: <b>{plan['name']}</b>\n💰 مبلغ: <b>{price:,} تومان</b>\n━━━━━━━━━━━━━━━"
        await update.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت 💳", callback_data="show_card")]]), parse_mode='HTML')
        return

    # --- بخش مدیریت (فقط ادمین) ---
    if str(uid) == str(ADMIN_ID):
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 منوی مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("انتخاب بخش:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # فرآیند افزودن پلن
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ap_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'ap_cat':
            user_data[uid].update({'step': 'ap_vol', 'cat': text})
            await update.message.reply_text("حجم پلن (مثلاً 20 گیگ):", reply_markup=BACK_KB); return
        if step == 'ap_vol':
            user_data[uid].update({'step': 'ap_user', 'vol': text})
            await update.message.reply_text("تعداد کاربر (مثلاً تک کاربره):"); return
        if step == 'ap_user':
            user_data[uid].update({'step': 'ap_price', 'user': text})
            await update.message.reply_text("قیمت به عدد (هزار تومان):"); return
        if step == 'ap_price':
            c = user_data[uid]['cat']
            p_name = f"{user_data[uid]['vol']} | {user_data[uid]['user']}"
            db["categories"][c].append({"id": len(db["categories"][c])+1, "name": p_name, "price": int(text), "only_vol": user_data[uid]['vol']})
            db["categories"][c] = sorted(db["categories"][c], key=lambda x: x['price'])
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن ذخیره و مرتب شد.", reply_markup=get_main_menu(uid)); return

        if text == 'حذف پلن':
            for c, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']}", callback_data=f"del_{c}_{p['id']}")]]
                    await update.message.reply_text(f"📍 {p['name']} - {p['price']}ت", reply_markup=InlineKeyboardMarkup(btn))
            return

        if text == 'ویرایش کارت':
            user_data[uid]['step'] = 'ed_card_n'
            await update.message.reply_text("شماره کارت جدید را بفرستید:", reply_markup=BACK_KB); return
        if step == 'ed_card_n':
            db["card"]["number"] = text; user_data[uid]['step'] = 'ed_card_m'
            await update.message.reply_text("نام صاحب کارت:"); return
        if step == 'ed_card_m':
            db["card"]["name"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ کارت ویرایش شد.", reply_markup=get_main_menu(uid)); return

        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ برند ویرایش شد.", reply_markup=get_main_menu(uid)); return

        if step and step.startswith('et_'):
            key = step.replace('et_', ''); db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ متن ویرایش شد.", reply_markup=get_main_menu(uid)); return

        maps = {'ویرایش متن پشتیبانی':'et_support', 'ویرایش متن راهنما':'et_guide', 'ویرایش متن تست':'et_test', 'ویرایش خوش‌آمدگویی':'et_welcome', 'ویرایش برند':'ed_brand'}
        if text in maps:
            user_data[uid]['step'] = maps[text]
            await update.message.reply_text("متن جدید را وارد کنید:", reply_markup=BACK_KB); return

    # سایر دکمه‌های کاربر
    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'تست رایگان':
        await update.message.reply_text(db["texts"]["test"]); await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست از: {uid}"); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید (مثلاً Amir):", reply_markup=BACK_KB)
    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        card_text = (f"💳 <b>اطلاعات پرداخت {db['brand']}</b>\n"
                     f"━━━━━━━━━━━━━━━\n"
                     f"💰 مبلغ قابل واریز: <b>{p:,} تومان</b>\n\n"
                     f"📍 شماره کارت (لمس کنید کپی شود):\n<code>{db['card']['number']}</code>\n\n"
                     f"👤 بنام: <b>{db['card']['name']}</b>\n"
                     f"━━━━━━━━━━━━━━━\n"
                     f"⚠️ لطفاً پس از واریز، تصویر فیش را ارسال کنید.")
        await query.message.reply_text(card_text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]))
    elif query.data == "get_photo":
        user_data[uid]['step'] = 'wait_pay'; await query.message.reply_text("📸 لطفاً عکس فیش را بفرستید:")
    elif query.data.startswith("del_"):
        _, c, pid = query.data.split("_")
        db["categories"][c] = [p for p in db["categories"][c] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ پلن حذف شد.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"💰 فیش جدید از: {uid}\nاکانت: {user_data[uid]['vpn_name']}")
        await update.message.reply_text("✅ فیش برای ادمین ارسال شد.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
