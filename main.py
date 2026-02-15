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
def home(): return "VPN Bot 21.0 - Stable", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- مدیریت دیتابیس ---
DB_FILE = '/app/data/data.json'
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {
        "users": {}, "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"ارزان و به صرفه": [], "قوی": []}, "brand": "Dragon VPN",
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nلطفا گزینه مورد نظر را انتخاب کنید:",
            "support": "🆘 <b>واحد پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>راهنمای اتصال {brand}</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست شما در {brand} ارسال شد."
        }
    }

def save_db(data):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
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
    uid = str(update.message.from_user.id)
    if uid not in db["users"]: db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
    save_db(db); user_data[uid] = {}
    txt = db["texts"].get("welcome", "خوش آمدید").format(brand=db["brand"])
    await update.message.reply_text(txt, reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.message.from_user.id)
    step = user_data.get(uid, {}).get('step')

    # خروج از هر مرحله
    if text == '❌ انصراف و بازگشت' or text == 'بازگشت به منوی اصلی':
        user_data[uid] = {}
        await start(update, context); return

    # --- بخش مدیریت (بررسی استپ‌ها قبل از دکمه‌های منو) ---
    if int(uid) == ADMIN_ID and step:
        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ برند به {text} تغییر یافت.", reply_markup=get_main_menu(uid)); return
        
        elif step.startswith('ed_txt_'):
            key = step.replace('ed_txt_', '')
            db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ متن {key} بروزرسانی شد.", reply_markup=get_main_menu(uid)); return

        elif step == 'ed_card_n':
            db["card"]["number"] = text; user_data[uid]['step'] = 'ed_card_m'
            await update.message.reply_text("حالا نام صاحب کارت را وارد کنید:"); return
        
        elif step == 'ed_card_m':
            db["card"]["name"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ مشخصات کارت ذخیره شد.", reply_markup=get_main_menu(uid)); return

        elif step == 'send_cfg':
            target = str(user_data[uid]['target'])
            info = user_data[uid]
            db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
            db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
            save_db(db)
            await context.bot.send_message(target, f"🚀 <b>سرویس {db['brand']} شما آماده شد</b>\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ ارسال شد."); user_data[uid] = {}; return

    # --- دکمه‌های اصلی ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 پنل مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        
        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("بخش مورد نظر:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن پشتیبانی': user_data[uid]['step'] = 'ed_txt_support'; await update.message.reply_text("متن جدید را بفرستید:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن راهنما': user_data[uid]['step'] = 'ed_txt_guide'; await update.message.reply_text("متن جدید را بفرستید:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن تست': user_data[uid]['step'] = 'ed_txt_test'; await update.message.reply_text("متن جدید را بفرستید:", reply_markup=BACK_KB); return
        if text == 'ویرایش خوش‌آمدگویی': user_data[uid]['step'] = 'ed_txt_welcome'; await update.message.reply_text("متن جدید را بفرستید (از {brand} در متن استفاده کنید):", reply_markup=BACK_KB); return
        if text == 'ویرایش برند': user_data[uid]['step'] = 'ed_brand'; await update.message.reply_text("نام جدید برند را وارد کنید:", reply_markup=BACK_KB); return
        if text == 'ویرایش کارت': user_data[uid]['step'] = 'ed_card_n'; await update.message.reply_text("شماره کارت جدید:", reply_markup=BACK_KB); return

    # --- دکمه‌های کاربر ---
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'تست رایگان':
        if db["users"].get(uid, {}).get("test_used"): await update.message.reply_text("⚠️ تست قبلا استفاده شده."); return
        await update.message.reply_text(db["texts"]["test"].format(brand=db["brand"]), parse_mode='HTML')
        await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست: {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"adm_ok_{uid}")]]))
        return

    # مرحله خرید - دریافت اسم
    if step == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        invoice = f"📑 <b>پیش فاکتور {db['brand']}</b>\n━━━━━━━━━━━━━━━\n👤 نام: <code>{text}</code>\n📦 پلن: <b>{plan['name']}</b>\n💰 مبلغ: <b>{price:,} تومان</b>\n━━━━━━━━━━━━━━━"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'سرویس‌های من':
        p = db["users"].get(uid, {}).get("purchases", [])
        if not p: await update.message.reply_text("📭 خالی است."); return
        for i, item in enumerate(p):
            await update.message.reply_text(f"✅ {item}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))
        return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 نام اکانت را انگلیسی وارد کنید:", reply_markup=BACK_KB)

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        details = db["users"][uid].get("raw_details", [])
        if idx < len(details):
            raw = details[idx]
            user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price'], 'is_new': False}
            invoice = f"📑 <b>فاکتور تمدید {db['brand']}</b>\n━━━━━━━━━━━━━━━\n👤 سرویس: <code>{raw['name']}</code>\n💰 مبلغ: <b>{raw['price']:,} تومان</b>\n━━━━━━━━━━━━━━━"
            await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')
        else:
            await query.message.reply_text("❌ خطا: اطلاعات خرید قبلی یافت نشد. لطفا پلن جدید بخرید.")

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        msg = f"💳 <b>اطلاعات واریز</b>\n━━━━━━━━━━━━━━━\n💰 مبلغ: <b>{p:,} تومان</b>\n📍 شماره کارت: <code>{db['card']['number']}</code>\n👤 بنام: <b>{db['card']['name']}</b>\n━━━━━━━━━━━━━━━\n⚠️ لطفا فیش را بفرستید."
        await query.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))

    elif query.data == "get_photo": await query.message.reply_text("📸 عکس فیش را بفرستید:", reply_markup=BACK_KB)
    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 'vol': user_data.get(target, {}).get('vol', 'تست'), 'vpn_name': user_data.get(target, {}).get('vpn_name', 'تست'), 'price': user_data.get(target, {}).get('price', 0), 'is_new': user_data.get(target, {}).get('is_new', False)}
        await query.message.reply_text(f"لینک کانفیگ برای {target}:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"💰 فیش جدید از {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش شما ارسال شد. منتظر بمانید.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
