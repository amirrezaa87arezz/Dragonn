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
def home(): return "Dragon VPN Bot v30.0 - Ultra Stable", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس هوشمند با پلن‌های پیش‌فرض ثابت ---
DB_FILE = 'data.json'
DEFAULT_PLANS = [
    {"id": 1, "name": "10GB - یک ماهه", "price": 40, "only_vol": "10GB"},
    {"id": 2, "name": "20GB - یک ماهه", "price": 70, "only_vol": "20GB"},
    {"id": 3, "name": "50GB - یک ماهه", "price": 130, "only_vol": "50GB"},
    {"id": 4, "name": "100GB - یک ماهه", "price": 220, "only_vol": "100GB"}
]

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    
    # ساختار اولیه با پلن‌های پیش‌فرض که خواسته بودی
    init_db = {
        "users": {}, "brand": "Dragon VPN",
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {
            "ارزان و به صرفه": list(DEFAULT_PLANS),
            "قوی": list(DEFAULT_PLANS)
        },
        "texts": {
            "welcome": "🐉 به ربات {brand} خوش آمدید\nلطفا یکی از گزینه‌ها را انتخاب کنید:",
            "support": "🆘 <b>واحد پشتیبانی {brand}</b>\n🆔 @Support_Admin",
            "guide": "📚 <b>راهنمای اتصال {brand}</b>\n🆔 @Guide_Channel",
            "test": "🚀 درخواست تست رایگان شما در {brand} ارسال شد."
        }
    }
    save_db(init_db)
    return init_db

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
    uid = update.effective_user.id
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {"purchases": [], "test_used": False}
        save_db(db)
    user_data[uid] = {}
    await update.message.reply_text(db["texts"]["welcome"].format(brand=db["brand"]), reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    uid = update.effective_user.id
    is_admin = (int(uid) == ADMIN_ID)
    step = user_data.get(uid, {}).get('step')

    # دستور لغو عملیات
    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
        user_data[uid] = {}
        await start(update, context); return

    # --- لایه مدیریت (ADMIN ONLY) ---
    if is_admin:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف پلن'], ['ویرایش کارت', 'ویرایش متن‌ها'], ['ویرایش برند', 'بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 پنل مدیریت فعال شد:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        if text == 'ویرایش متن‌ها':
            kb = [['ویرایش متن پشتیبانی', 'ویرایش متن راهنما'], ['ویرایش متن تست', 'ویرایش خوش‌آمدگویی'], ['❌ انصراف و بازگشت']]
            await update.message.reply_text("بخش مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

        # --- فرآیند افزودن پلن (دقیق و مرحله‌ای) ---
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ADM_ADD_CAT'
            kb = [[c] for c in db["categories"].keys()]
            kb.append(['❌ انصراف و بازگشت'])
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        
        if step == 'ADM_ADD_CAT' and text in db["categories"]:
            user_data[uid].update({'step': 'ADM_ADD_VOL', 'target_cat': text})
            await update.message.reply_text("حجم (مثلاً 50GB):", reply_markup=BACK_KB); return
        
        if step == 'ADM_ADD_VOL':
            user_data[uid].update({'step': 'ADM_ADD_USER', 'vol': text})
            await update.message.reply_text("تعداد کاربر (مثلاً ۲ کاربره):"); return
        
        if step == 'ADM_ADD_USER':
            user_data[uid].update({'step': 'ADM_ADD_PRICE', 'user': text})
            await update.message.reply_text("قیمت (فقط عدد به هزار تومان):"); return
        
        if step == 'ADM_ADD_PRICE':
            cat = user_data[uid]['target_cat']
            new_p = {"id": len(db["categories"][cat])+1, "name": f"{user_data[uid]['vol']} | {user_data[uid]['user']}", "price": int(text), "only_vol": user_data[uid]['vol']}
            db["categories"][cat].append(new_p)
            db["categories"][cat] = sorted(db["categories"][cat], key=lambda x: x['price'])
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن با موفقیت اضافه شد.", reply_markup=get_main_menu(uid)); return

        # --- ویرایش کارت ---
        if text == 'ویرایش کارت':
            user_data[uid]['step'] = 'ADM_ED_CARD_N'
            await update.message.reply_text("شماره کارت جدید را بفرستید:", reply_markup=BACK_KB); return
        if step == 'ADM_ED_CARD_N':
            db["card"]["number"] = text; user_data[uid]['step'] = 'ADM_ED_CARD_M'
            await update.message.reply_text("نام صاحب کارت:"); return
        if step == 'ADM_ED_CARD_M':
            db["card"]["name"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ کارت بانکی بروزرسانی شد.", reply_markup=get_main_menu(uid)); return

        # --- ویرایش متن‌ها و برند ---
        maps = {
            'ویرایش متن پشتیبانی': 'ADM_TXT_support', 'ویرایش متن راهنما': 'ADM_TXT_guide',
            'ویرایش متن تست': 'ADM_TXT_test', 'ویرایش خوش‌آمدگویی': 'ADM_TXT_welcome',
            'ویرایش برند': 'ADM_BRAND'
        }
        if text in maps:
            user_data[uid]['step'] = maps[text]
            await update.message.reply_text("متن جدید را وارد کنید:", reply_markup=BACK_KB); return
        
        if step == 'ADM_BRAND':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ نام برند تغییر کرد.", reply_markup=get_main_menu(uid)); return
        
        if step and step.startswith('ADM_TXT_'):
            key = step.split('_')[2]
            db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ متن با موفقیت تغییر کرد.", reply_markup=get_main_menu(uid)); return

        if text == 'حذف پلن':
            for c, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"حذف {p['name']}", callback_data=f"del_{c}_{p['id']}")]]
                    await update.message.reply_text(f"📍 {p['name']} ({c})", reply_markup=InlineKeyboardMarkup(btn))
            return

    # --- لایه کاربری ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        kb.append(['❌ انصراف و بازگشت'])
        await update.message.reply_text("📂 دسته‌بندی مورد نظر:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return

    if text in db["categories"] and not step:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("❌ فعلاً پلنی موجود نیست."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"🚀 لیست پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn)); return

    if step == 'USR_GET_NAME':
        plan = user_data[uid]['plan']
        price = plan['price'] * 1000
        user_data[uid].update({'step': 'WAIT_PAY', 'vpn_name': text, 'price': price, 'vol_only': plan['only_vol']})
        inv = f"📑 <b>پیش‌فاکتور</b>\n━━━━━━━━━━━━━━━\n👤 نام: <code>{text}</code>\n📦 پلن: <b>{plan['name']}</b>\n💰 مبلغ: <b>{price:,} تومان</b>\n━━━━━━━━━━━━━━━"
        await update.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت 💳", callback_data="show_card")]]), parse_mode='HTML')
        return

    if text == 'پشتیبانی': await update.message.reply_text(db["texts"]["support"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'راهنمای اتصال': await update.message.reply_text(db["texts"]["guide"].format(brand=db["brand"]), parse_mode='HTML'); return
    if text == 'تست رایگان': await update.message.reply_text(db["texts"]["test"]); return

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = query.from_user.id; await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'USR_GET_NAME', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید:", reply_markup=BACK_KB)
    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        msg = (f"💳 <b>اطلاعات پرداخت</b>\n━━━━━━━━━━━━━━━\n💰 مبلغ: <b>{p:,} تومان</b>\n\n📍 شماره کارت:\n<code>{db['card']['number']}</code>\n\n👤 بنام: <b>{db['card']['name']}</b>\n━━━━━━━━━━━━━━━")
        await query.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]))
    elif query.data == "get_photo":
        user_data[uid]['step'] = 'WAIT_PAY'; await query.message.reply_text("📸 فیش را بفرستید:")
    elif query.data.startswith("del_"):
        _, c, pid = query.data.split("_")
        db["categories"][c] = [p for p in db["categories"][c] if str(p['id']) != pid]
        save_db(db); await query.message.edit_text("✅ پلن حذف شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
