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

# --- دیتابیس هوشمند ---
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
        "texts": {
            "support": "🆘 <b>واحد پشتیبانی</b>\n🆔 @Dragon_Support",
            "guide": "📚 <b>راهنمای اتصال</b>\n🆔 @help_dragon",
            "test": "🚀 درخواست تست رایگان شما ارسال شد."
        }
    }

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
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.message.from_user.id)
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context)
        return

    # --- پاسخ به دکمه‌های اصلی کاربر ---
    if text == 'راهنمای اتصال':
        await update.message.reply_text(db["texts"]["guide"], parse_mode='HTML')
        return
    if text == 'پشتیبانی':
        await update.message.reply_text(db["texts"]["support"], parse_mode='HTML')
        return
    if text == 'تست رایگان':
        if db["users"].get(uid, {}).get("test_used"):
            await update.message.reply_text("⚠️ شما قبلاً تست رایگان دریافت کرده‌اید.")
        else:
            await update.message.reply_text(db["texts"]["test"], parse_mode='HTML')
            await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست از: {uid}", 
                                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال تست", callback_data=f"adm_ok_{uid}")]]))
        return

    # --- پنل مدیریت ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', '❌ انصراف و بازگشت']]
            await update.message.reply_text("کدام متن را ویرایش می‌کنید؟", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        # ذخیره متن‌های جدید
        if step == 'edit_support':
            db["texts"]["support"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ متن پشتیبانی آپدیت شد.", reply_markup=get_main_menu(uid)); return
        if step == 'edit_guide':
            db["texts"]["guide"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ متن راهنما آپدیت شد.", reply_markup=get_main_menu(uid)); return
        if step == 'edit_test_txt':
            db["texts"]["test"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ متن تست آپدیت شد.", reply_markup=get_main_menu(uid)); return

        if text == 'ویرایش متن پشتیبانی': user_data[uid]['step'] = 'edit_support'; await update.message.reply_text("متن جدید پشتیبانی را بفرستید:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن راهنما': user_data[uid]['step'] = 'edit_guide'; await update.message.reply_text("متن جدید راهنما را بفرستید:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن تست': user_data[uid]['step'] = 'edit_test_txt'; await update.message.reply_text("متن جدید بخش تست را بفرستید:", reply_markup=BACK_KB); return

        # ویرایش کارت
        if text == 'ویرایش کارت':
            user_data[uid]['step'] = 'edit_card_num'
            await update.message.reply_text("شماره کارت جدید را بفرستید:", reply_markup=BACK_KB); return
        if step == 'edit_card_num':
            db["card"]["number"] = text; user_data[uid]['step'] = 'edit_card_name'
            await update.message.reply_text("حالا نام صاحب کارت را بفرستید:"); return
        if step == 'edit_card_name':
            db["card"]["name"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ مشخصات کارت ذخیره شد.", reply_markup=get_main_menu(uid)); return

        # افزودن پلن
        if text == 'افزودن پلن':
            kb = [[c] for c in db["categories"].keys()]
            user_data[uid]['step'] = 'add_p_cat'
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'add_p_cat':
            user_data[uid].update({'step': 'add_p_name', 'cat': text})
            await update.message.reply_text("نام پلن (مثلا 50G):", reply_markup=BACK_KB); return
        if step == 'add_p_name':
            user_data[uid].update({'step': 'add_p_price', 'name': text})
            await update.message.reply_text("قیمت به هزار تومان (مثلا 150):"); return
        if step == 'add_p_price':
            new_id = len(db["categories"][user_data[uid]['cat']]) + 1
            db["categories"][user_data[uid]['cat']].append({"id": new_id, "name": user_data[uid]['name'], "price": text})
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن اضافه شد.", reply_markup=get_main_menu(uid)); return

        # حذف پلن
        if text == 'حذف پلن':
            for cat, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']} ({cat})", callback_data=f"del_{cat}_{p['id']}")]]
                    await update.message.reply_text(f"🗑 پلن: {p['name']}", reply_markup=InlineKeyboardMarkup(btn))
            return

        # ارسال کانفیگ
        if step == 'send_cfg':
            target = str(user_data[uid]['target'])
            info = user_data[uid]
            if info.get('is_new'):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
                save_db(db)
            await context.bot.send_message(target, f"🚀 سرویس شما آماده شد:\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ ارسال شد."); user_data[uid] = {}
            return

    # --- خرید و تمدید کاربر ---
    if step == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        invoice = f"📑 <b>پیش فاکتور</b>\n👤 نام: {text}\n📦 پلن: {plan['name']}\n💰 مبلغ: {price:,} تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 لیست خالی است."); return
        for i, p in enumerate(purchases):
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))
        return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ خالی است."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))
        return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("del_"):
        _, cat, pid = query.data.split("_")
        db["categories"][cat] = [p for p in db["categories"][cat] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ پلن حذف شد.")

    elif query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 نام اکانت را بفرستید:", reply_markup=BACK_KB)

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        raw = db["users"][uid]["raw_details"][idx]
        user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price'], 'is_new': False}
        invoice = f"📑 <b>فاکتور تمدید</b>\n👤 سرویس: {raw['name']}\n💰 مبلغ: {raw['price']:,} تومان"
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        card_msg = f"💳 <b>اطلاعات واریز</b>\n💰 مبلغ: {p:,} تومان\n📍 شماره کارت: <code>{db['card']['number']}</code>\n👤 بنام: {db['card']['name']}"
        await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))

    elif query.data == "get_photo": await query.message.reply_text("📸 فیش را بفرستید:", reply_markup=BACK_KB)

    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 'vol': user_data.get(target, {}).get('vol', 'تست'), 'vpn_name': user_data.get(target, {}).get('vpn_name', 'تست'), 'price': user_data.get(target, {}).get('price', 0), 'is_new': user_data.get(target, {}).get('is_new', False)}
        await query.message.reply_text(f"لینک را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, 
                                     caption=f"💰 فیش جدید از {uid}\nمبلغ: {user_data[uid].get('price', 0):,}ت",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش شما ارسال شد. منتظر تایید باشید.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
