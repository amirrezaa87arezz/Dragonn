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
def home(): return "VPN Bot System 20.0 Online!", 200

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
        "brand": "Dragon VPN",
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
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
        save_db(db)
    user_data[uid] = {}
    welcome_txt = db["texts"]["welcome"].format(brand=db["brand"])
    await update.message.reply_text(welcome_txt, reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.message.from_user.id)
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context)
        return

    # --- پاسخ به دکمه‌های اصلی (اگر در مرحله ویرایش نباشد) ---
    if not step:
        if text == 'راهنمای اتصال':
            await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
        if text == 'پشتیبانی':
            await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
        if text == 'تست رایگان':
            if db["users"].get(uid, {}).get("test_used"):
                await update.message.reply_text("⚠️ شما قبلاً تست رایگان دریافت کرده‌اید."); return
            await update.message.reply_text(db["texts"]["test"].format(brand=db["brand"]), parse_mode='HTML')
            await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست از: {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال تست", callback_data=f"adm_ok_{uid}")]]))
            return

    # --- پنل مدیریت ادمین ---
    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("کدام بخش را ویرایش می‌کنید؟", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # منطق ذخیره‌سازی ویرایش‌ها
        edit_steps = {
            'ed_supp': 'support', 'ed_guid': 'guide', 
            'ed_test': 'test', 'ed_welc': 'welcome'
        }
        if step in edit_steps:
            db["texts"][edit_steps[step]] = text
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ تغییرات با موفقیت ذخیره شد.", reply_markup=get_main_menu(uid)); return

        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ نام برند به <b>{text}</b> تغییر یافت.", parse_mode='HTML', reply_markup=get_main_menu(uid)); return

        # فعال‌سازی استپ‌ها
        if text == 'ویرایش متن پشتیبانی': user_data[uid]['step'] = 'ed_supp'; await update.message.reply_text("متن جدید پشتیبانی:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن راهنما': user_data[uid]['step'] = 'ed_guid'; await update.message.reply_text("متن جدید راهنما:", reply_markup=BACK_KB); return
        if text == 'ویرایش متن تست': user_data[uid]['step'] = 'ed_test'; await update.message.reply_text("متن جدید تست:", reply_markup=BACK_KB); return
        if text == 'ویرایش خوش‌آمدگویی': user_data[uid]['step'] = 'ed_welc'; await update.message.reply_text("متن جدید خوش‌آمدگویی:\n(نکته: از عبارت {brand} در متن استفاده کنید)", reply_markup=BACK_KB); return
        if text == 'ویرایش برند': user_data[uid]['step'] = 'ed_brand'; await update.message.reply_text("نام جدید برند را وارد کنید:", reply_markup=BACK_KB); return

        # ویرایش کارت (اصلاح شده)
        if text == 'ویرایش کارت': user_data[uid]['step'] = 'ed_card_n'; await update.message.reply_text("شماره کارت جدید:", reply_markup=BACK_KB); return
        if step == 'ed_card_n': db["card"]["number"] = text; user_data[uid]['step'] = 'ed_card_m'; await update.message.reply_text("نام صاحب کارت:"); return
        if step == 'ed_card_m': db["card"]["name"] = text; save_db(db); user_data[uid] = {}; await update.message.reply_text("✅ کارت آپدیت شد.", reply_markup=get_main_menu(uid)); return

        # افزودن پلن (اصلاح شده)
        if text == 'افزودن پلن':
            kb = [[c] for c in db["categories"].keys()]
            user_data[uid]['step'] = 'add_cat'; await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'add_cat': user_data[uid].update({'step': 'add_n', 'cat': text}); await update.message.reply_text("نام پلن:", reply_markup=BACK_KB); return
        if step == 'add_n': user_data[uid].update({'step': 'add_p', 'p_name': text}); await update.message.reply_text("قیمت (هزار تومان):"); return
        if step == 'add_p':
            new_id = len(db["categories"][user_data[uid]['cat']]) + 1
            db["categories"][user_data[uid]['cat']].append({"id": new_id, "name": user_data[uid]['p_name'], "price": text})
            save_db(db); user_data[uid] = {}; await update.message.reply_text("✅ پلن اضافه شد.", reply_markup=get_main_menu(uid)); return

        # حذف پلن
        if text == 'حذف پلن':
            for cat, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']} ({cat})", callback_data=f"del_{cat}_{p['id']}")]]
                    await update.message.reply_text(f"🗑 {p['name']}", reply_markup=InlineKeyboardMarkup(btn))
            return

        # ارسال کانفیگ
        if step == 'send_cfg':
            target, info = str(user_data[uid]['target']), user_data[uid]
            if info.get('is_new'):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
                save_db(db)
            await context.bot.send_message(target, f"🚀 <b>سرویس {db['brand']} شما آماده شد!</b>\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ ارسال شد."); user_data[uid] = {}
            return

    # --- بخش کاربر ---
    if step == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        invoice = (f"📑 <b>پیش فاکتور {db['brand']}</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 نام اکانت: <code>{text}</code>\n"
                   f"📦 پلن: <b>{plan['name']}</b>\n"
                   f"💰 مبلغ: <b>{price:,} تومان</b>\n"
                   f"━━━━━━━━━━━━━━━")
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و مرحله بعد ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 لیست شما خالی است."); return
        for i, p in enumerate(purchases):
            await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))
        return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 انتخاب دسته بندی:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ پلنی یافت نشد."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan, 'is_new': True}
        await query.message.reply_text("📝 نام اکانت را بفرستید:", reply_markup=BACK_KB)

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        try:
            raw = db["users"][uid]["raw_details"][idx]
            user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price'], 'is_new': False}
            invoice = (f"📑 <b>فاکتور تمدید {db['brand']}</b>\n"
                       f"━━━━━━━━━━━━━━━\n"
                       f"👤 نام: <code>{raw['name']}</code>\n"
                       f"💰 مبلغ: <b>{raw['price']:,} تومان</b>\n"
                       f"━━━━━━━━━━━━━━━")
            await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و مرحله بعد ✅", callback_data="show_card")]]), parse_mode='HTML')
        except: await query.message.reply_text("❌ خطا در بازیابی اطلاعات سرویس.")

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        card_msg = (f"💳 <b>اطلاعات واریز ({db['brand']})</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"💰 مبلغ: <b>{p:,} تومان</b>\n"
                    f"📍 شماره کارت: <code>{db['card']['number']}</code>\n"
                    f"👤 بنام: <b>{db['card']['name']}</b>\n"
                    f"━━━━━━━━━━━━━━━")
        await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]))

    elif query.data == "get_photo": await query.message.reply_text("📸 فیش را بفرستید:", reply_markup=BACK_KB)
    elif query.data.startswith("del_"):
        _, cat, pid = query.data.split("_")
        db["categories"][cat] = [p for p in db["categories"][cat] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ پلن حذف شد.")
    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 'vol': user_data.get(target, {}).get('vol', 'تست'), 'vpn_name': user_data.get(target, {}).get('vpn_name', 'تست'), 'price': user_data.get(target, {}).get('price', 0), 'is_new': user_data.get(target, {}).get('is_new', False)}
        await query.message.reply_text(f"لینک را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"💰 فیش جدید!\nUserID: {uid}\nمبلغ: {user_data[uid].get('price', 0):,}ت", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_ok_{uid}")]]))
        await update.message.reply_text("🚀 فیش ارسال شد. منتظر تایید ادمین باشید.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
