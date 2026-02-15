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
def home(): return "VPN Bot 23.0 - Stable", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- مدیریت دیتابیس ---
DB_FILE = 'data.json'

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    
    # پلن‌های پیش‌فرض که خواسته بودی
    default_plans = [
        {"id": 1, "name": "10GB - یک ماهه", "price": "40"},
        {"id": 2, "name": "20GB - یک ماهه", "price": "70"},
        {"id": 3, "name": "50GB - یک ماهه", "price": "130"},
        {"id": 4, "name": "100GB - یک ماهه", "price": "220"}
    ]
    
    db_init = {
        "users": {},
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {
            "ارزان و به صرفه": list(default_plans),
            "قوی": list(default_plans)
        },
        "brand": "Dragon VPN",
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nلطفا یکی از گزینه‌ها را انتخاب کنید:",
            "support": "🆘 <b>واحد پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>راهنمای اتصال {brand}</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست رایگان شما در {brand} ارسال شد."
        }
    }
    save_db(db_init)
    return db_init

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPy?2hAcJxJpwhrxc0DxxBMGN8RY' # توکن خودت را اصلاح کن
ADMIN_ID = 5993860770
user_data = {}

def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"purchases": [], "raw_details": [], "test_used": False}
        save_db(db)
    user_data[uid] = {}
    msg = db["texts"]["welcome"].format(brand=db["brand"])
    await update.message.reply_text(msg, reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    step = user_data.get(uid, {}).get('step')

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    if int(uid) == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # منطق ویرایش متن‌ها و برند
        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ برند به {text} تغییر کرد.", reply_markup=get_main_menu(uid)); return
        if step and step.startswith('ed_txt_'):
            key = step.split('_')[2]
            db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ آپدیت شد.", reply_markup=get_main_menu(uid)); return

        map_btns = {'ویرایش متن پشتیبانی':'ed_txt_support', 'ویرایش متن راهنما':'ed_txt_guide', 'ویرایش متن تست':'ed_txt_test', 'ویرایش خوش‌آمدگویی':'ed_txt_welcome', 'ویرایش برند':'ed_brand'}
        if text in map_btns:
            user_data[uid]['step'] = map_btns[text]
            await update.message.reply_text("متن جدید را بفرستید:", reply_markup=BACK_KB); return

        # --- افزودن پلن (اصلاح شده) ---
        if text == 'افزودن پلن':
            kb = [[c] for c in db["categories"].keys()]
            user_data[uid]['step'] = 'add_p_cat'
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'add_p_cat':
            user_data[uid].update({'step': 'add_p_name', 'cat_target': text})
            await update.message.reply_text(f"نام پلن برای دسته {text} (مثلا 50 گیگ):", reply_markup=BACK_KB); return
        if step == 'add_p_name':
            user_data[uid].update({'step': 'add_p_price', 'plan_name': text})
            await update.message.reply_text("قیمت (فقط عدد به هزار تومان - مثلا 100):"); return
        if step == 'add_p_price':
            cat = user_data[uid]['cat_target']
            new_plan = {"id": len(db["categories"][cat]) + 1, "name": user_data[uid]['plan_name'], "price": text}
            db["categories"][cat].append(new_plan)
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن با موفقیت اضافه شد.", reply_markup=get_main_menu(uid)); return

        # --- حذف پلن (اصلاح شده) ---
        if text == 'حذف پلن':
            found = False
            for cat, plans in db["categories"].items():
                for p in plans:
                    found = True
                    btn = [[InlineKeyboardButton(f"حذف {p['name']} از {cat}", callback_data=f"del_{cat}_{p['id']}")]]
                    await update.message.reply_text(f"📍 پلن: {p['name']} | قیمت: {p['price']}ت", reply_markup=InlineKeyboardMarkup(btn))
            if not found: await update.message.reply_text("❌ هیچ پلنی برای حذف وجود ندارد."); return

        if text == 'ویرایش کارت':
            user_data[uid]['step'] = 'ed_c_n'; await update.message.reply_text("شماره کارت:", reply_markup=BACK_KB); return
        if step == 'ed_c_n': db["card"]["number"] = text; user_data[uid]['step'] = 'ed_c_m'; await update.message.reply_text("نام صاحب کارت:"); return
        if step == 'ed_c_m': db["card"]["name"] = text; save_db(db); user_data[uid] = {}; await update.message.reply_text("✅ ذخیره شد.", reply_markup=get_main_menu(uid)); return

        if step == 'send_cfg':
            target = str(user_data[uid]['target'])
            info = user_data[uid]
            db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
            db["users"][target]["raw_details"].append({"vol": info['vol'], "price": info['price'], "name": info['vpn_name']})
            save_db(db)
            await context.bot.send_message(target, f"🚀 سرویس شما آماده شد:\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ ارسال شد."); user_data[uid] = {}; return

    # --- بخش کاربر ---
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'تست رایگان':
        if db["users"].get(uid, {}).get("test_used"): await update.message.reply_text("⚠️ قبلا استفاده شده."); return
        await update.message.reply_text(db["texts"]["test"].format(brand=db["brand"]), parse_mode='HTML')
        await context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست: {uid}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"adm_ok_{uid}")]]))
        return

    if text == 'سرویس‌های من':
        p = db["users"].get(uid, {}).get("purchases", [])
        if not p: await update.message.reply_text("📭 خالی است."); return
        for i, item in enumerate(p):
            await update.message.reply_text(f"✅ {item}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 تمدید همین سرویس", callback_data=f"ren_{i}")]]))
        return

    if step == 'get_name':
        plan = user_data[uid]['plan']
        price = int(plan['price']) * 1000
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol': plan['name']})
        inv = f"📑 <b>پیش فاکتور {db['brand']}</b>\n━━━━━━━━━━━━━━━\n👤 نام: <code>{text}</code>\n📦 پلن: <b>{plan['name']}</b>\n💰 مبلغ: <b>{price:,} تومان</b>\n━━━━━━━━━━━━━━━"
        await update.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("📂 انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ این دسته خالی است."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید:", reply_markup=BACK_KB)

    elif query.data.startswith("del_"):
        _, cat, pid = query.data.split("_")
        db["categories"][cat] = [p for p in db["categories"][cat] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ پلن با موفقیت حذف شد.")

    elif query.data.startswith("ren_"):
        idx = int(query.data.split("_")[1])
        details = db["users"][uid].get("raw_details", [])
        if idx < len(details):
            raw = details[idx]
            user_data[uid] = {'step': 'wait_pay', 'vpn_name': raw['name'], 'vol': raw['vol'], 'price': raw['price']}
            inv = f"📑 <b>فاکتور تمدید {db['brand']}</b>\n━━━━━━━━━━━━━━━\n👤 سرویس: <code>{raw['name']}</code>\n💰 مبلغ: <b>{raw['price']:,} تومان</b>\n━━━━━━━━━━━━━━━"
            await query.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و پرداخت ✅", callback_data="show_card")]]), parse_mode='HTML')

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        msg = f"💳 <b>واریز به کارت</b>\n━━━━━━━━━━━━━━━\n💰 مبلغ: <b>{p:,} تومان</b>\n📍 کارت: <code>{db['card']['number']}</code>\n👤 بنام: <b>{db['card']['name']}</b>\n━━━━━━━━━━━━━━━"
        await query.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))

    elif query.data == "get_photo": await query.message.reply_text("📸 عکس فیش را بفرستید:", reply_markup=BACK_KB)
    elif query.data.startswith("adm_ok_"):
        target = query.data.split("_")[2]
        user_data[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': target, 'vol': user_data.get(target, {}).get('vol', 'تست'), 'vpn_name': user_data.get(target, {}).get('vpn_name', 'تست'), 'price': user_data.get(target, {}).get('price', 0)}
        await query.message.reply_text(f"لینک را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"💰 فیش جدید از {uid}")
        await update.message.reply_text("🚀 فیش ارسال شد. منتظر بمانید.", reply_markup=get_main_menu(uid))

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
