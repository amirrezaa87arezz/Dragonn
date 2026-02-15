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
def home(): return "VPN Bot 26.0 - Professional", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس ---
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

        # فرآیند افزودن پلن (حجم -> کاربر -> قیمت)
        if text == 'افزودن پلن':
            user_data[uid]['step'] = 'ap_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)); return
        if step == 'ap_cat':
            user_data[uid].update({'step': 'ap_vol', 'cat': text})
            await update.message.reply_text("حجم پلن را وارد کنید (مثلا 50 گیگ):", reply_markup=BACK_KB); return
        if step == 'ap_vol':
            user_data[uid].update({'step': 'ap_user', 'vol': text})
            await update.message.reply_text("تعداد کاربر را وارد کنید (مثلا 2):"); return
        if step == 'ap_user':
            user_data[uid].update({'step': 'ap_price', 'user': text})
            await update.message.reply_text("قیمت را به عدد (هزار تومان) وارد کنید:"); return
        if step == 'ap_price':
            c = user_data[uid]['cat']
            p_name = f"{user_data[uid]['vol']} | {user_data[uid]['user']} کاربره"
            db["categories"][c].append({"id": len(db["categories"][c])+1, "name": p_name, "price": int(text)})
            db["categories"][c] = sorted(db["categories"][c], key=lambda x: x['price'])
            save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ پلن با جزئیات کامل اضافه و لیست مرتب شد.", reply_markup=get_main_menu(uid)); return

        # ارسال کانفیگ توسط ادمین
        if step == 'admin_send_config':
            target_id = user_data[uid]['target']
            config_data = text
            brand = db.get('brand', 'Dragon VPN')
            user_msg = (f"🚀 <b>سرویس جدید شما آماده شد!</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🛡 برند: <b>{brand}</b>\n"
                        f"👤 اشتراک: <code>{user_data[uid].get('vpn_name', 'نامشخص')}</code>\n"
                        f"📦 جزئیات: <b>{user_data[uid].get('vol_info', 'پلن خریداری شده')}</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📥 <b>کانفیگ اختصاصی:</b>\n\n<code>{config_data}</code>\n\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🆘 در صورت بروز مشکل با پشتیبانی در ارتباط باشید.")
            await context.bot.send_message(target_id, user_msg, parse_mode='HTML')
            # ذخیره در تاریخچه کاربر
            db["users"][target_id]["purchases"].append(f"📦 {user_data[uid].get('vol_info')} | {user_data[uid].get('vpn_name')}")
            save_db(db)
            await update.message.reply_text("✅ کانفیگ با موفقیت برای کاربر ارسال شد.", reply_markup=get_main_menu(uid))
            user_data[uid] = {}; return

        # بقیه بخش‌های مدیریت (برند و متن‌ها)
        if step == 'ed_brand':
            db["brand"] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text(f"✅ برند تغییر کرد.", reply_markup=get_main_menu(uid)); return
        if step and step.startswith('et_'):
            key = step.replace('et_', ''); db["texts"][key] = text; save_db(db); user_data[uid] = {}
            await update.message.reply_text("✅ آپدیت شد.", reply_markup=get_main_menu(uid)); return
        
        maps = {'ویرایش متن پشتیبانی':'et_support', 'ویرایش متن راهنما':'et_guide', 'ویرایش متن تست':'et_test', 'ویرایش خوش‌آمدگویی':'et_welcome', 'ویرایش برند':'ed_brand', 'ویرایش کارت':'ed_card_n'}
        if text in maps:
            user_data[uid]['step'] = maps[text]
            await update.message.reply_text("متن جدید را بفرستید:", reply_markup=BACK_KB); return

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
        user_data[uid].update({'step': 'wait_pay', 'vpn_name': text, 'price': price, 'vol_info': plan['name']})
        inv = (f"📑 <b>پیش فاکتور خرید {db['brand']}</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"👤 نام اکانت: <code>{text}</code>\n"
               f"📦 نوع پلن: <b>{plan['name']}</b>\n"
               f"💰 مبلغ: <b>{price:,} تومان</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"✅ جهت تایید و دریافت کارت کلیک کنید:")
        await update.message.reply_text(inv, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت کارت 💳", callback_data="show_card")]]), parse_mode='HTML')
        return

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if user_data.get(uid, {}).get('step') == 'wait_pay':
        price = user_data[uid].get('price', 0)
        vpn_name = user_data[uid].get('vpn_name', 'نامشخص')
        vol_info = user_data[uid].get('vol_info', 'نامشخص')
        
        # ارسال برای ادمین
        adm_msg = (f"💰 <b>فیش واریزی جدید!</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 از کاربر: <code>{uid}</code>\n"
                   f"📝 نام اکانت: <b>{vpn_name}</b>\n"
                   f"📦 پلن: <b>{vol_info}</b>\n"
                   f"💵 مبلغ: <b>{price:,} تومان</b>\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👇 جهت ارسال کانفیگ دکمه زیر را بزنید:")
        btn = [[InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"adm_send_{uid}_{vpn_name}_{vol_info}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=adm_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
        
        # پیام تایید برای کاربر
        await update.message.reply_text("🚀 فیش شما با موفقیت برای ادمین ارسال شد.\nپس از تایید، کانفیگ همین‌جا برایتان ارسال می‌شود.", reply_markup=get_main_menu(uid))
        user_data[uid]['step'] = None

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        user_data[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت را بفرستید (مثلاً Ali):", reply_markup=BACK_KB)

    elif query.data == "show_card":
        p = user_data[uid].get('price', 0)
        msg = (f"💳 <b>اطلاعات واریز ({db['brand']})</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"💰 مبلغ: <b>{p:,} تومان</b>\n"
               f"📍 شماره کارت:\n<code>{db['card']['number']}</code>\n"
               f"👤 بنام: <b>{db['card']['name']}</b>\n"
               f"━━━━━━━━━━━━━━━\n"
               f"👇 پس از واریز، دکمه ارسال فیش را بزنید:")
        await query.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]))

    elif query.data == "get_photo":
        user_data[uid]['step'] = 'wait_pay'
        await query.message.reply_text("📸 لطفاً عکس فیش را ارسال کنید:")

    elif query.data.startswith("adm_send_"):
        _, _, target_id, v_name, v_info = query.data.split("_")
        user_data[str(ADMIN_ID)] = {'step': 'admin_send_config', 'target': target_id, 'vpn_name': v_name, 'vol_info': v_info}
        await context.bot.send_message(ADMIN_ID, f"📨 لطفاً کانفیگ را برای کاربر <code>{target_id}</code> بفرستید:", parse_mode='HTML', reply_markup=BACK_KB)

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.run_polling()
