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
def home(): return "Dragon VPN System is Live!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات دیتابیس در Volume ---
DB_PATH = '/app/data'
DB_FILE = os.path.join(DB_PATH, 'data.json')

def load_db():
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH, exist_ok=True)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {
        "users": {},
        "card": {"number": "6277601368776066", "name": "رضوانی"},
        "categories": {"ارزان و به صرفه": [], "قوی": []}
    }

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
state = {}

# --- منوها ---
def get_main_menu(uid):
    kb = [['خرید اشتراک', 'تست رایگان'], ['سرویس‌های من'], ['پشتیبانی', 'راهنمای اتصال']]
    if int(uid) == ADMIN_ID: kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

CANCEL_KB = ReplyKeyboardMarkup([['❌ انصراف و بازگشت']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"test_used": False, "purchases": []}
        save_db(db)
    state[uid] = None
    await update.message.reply_text("🐉 به ربات Dragon VPN خوش آمدید", reply_markup=get_main_menu(uid))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid_int = update.message.text, update.message.from_user.id
    uid = str(uid_int)

    if text == '❌ انصراف و بازگشت' or text == 'بازگشت به منوی اصلی':
        state[uid] = None
        await start(update, context)
        return

    # --- پنل مدیریت ادمین ---
    if uid_int == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف/ویرایش پلن'], ['ویرایش کارت', 'پیام همگانی'], ['بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 پنل مدیریت ادمین:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        elif text == 'ویرایش کارت':
            state[uid] = 'edit_card_num'
            await update.message.reply_text("شماره کارت جدید را بفرستید:", reply_markup=CANCEL_KB)
            return

        elif text == 'پیام همگانی':
            state[uid] = 'broadcasting'
            await update.message.reply_text("پیام خود را بفرستید:", reply_markup=CANCEL_KB)
            return

        elif text == 'افزودن پلن':
            state[uid] = 'add_plan_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("دسته پلن را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return

        elif text == 'حذف/ویرایش پلن':
            for cat, plans in db["categories"].items():
                for p in plans:
                    btn = [[InlineKeyboardButton(f"✏️ ویرایش", callback_data=f"editp_{cat}_{p['id']}"), 
                            InlineKeyboardButton(f"❌ حذف", callback_data=f"delp_{cat}_{p['id']}")]]
                    await update.message.reply_text(f"📦 پلن: {p['name']}\n💰 قیمت: {p['price']}ت\n📁 دسته: {cat}", reply_markup=InlineKeyboardMarkup(btn))
            return

        # لاجیک وضعیت‌های ادمین
        if state.get(uid) == 'edit_card_num':
            db["card"]["number"] = text; state[uid] = 'edit_card_name'
            await update.message.reply_text("نام صاحب کارت:")
            return
        elif state.get(uid) == 'edit_card_name':
            db["card"]["name"] = text; save_db(db); state[uid] = None
            await update.message.reply_text("✅ کارت آپدیت شد.", reply_markup=get_main_menu(uid))
            return
        elif state.get(uid) == 'add_plan_cat':
            state[uid] = {'step': 'add_name', 'cat': text}
            await update.message.reply_text("نام پلن (مثلا 20 گیگ):", reply_markup=CANCEL_KB)
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_name':
            state[uid].update({'step': 'add_price', 'name': text})
            await update.message.reply_text("قیمت را به عدد بفرستید (مثلا 130):")
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_price':
            new_id = len(db["categories"][state[uid]['cat']]) + 1
            db["categories"][state[uid]['cat']].append({"id": new_id, "name": state[uid]['name'], "price": text})
            save_db(db); state[uid] = None
            await update.message.reply_text("✅ پلن اضافه شد.", reply_markup=get_main_menu(uid))
            return
        elif state.get(uid) == 'broadcasting':
            for u in db["users"]:
                try: await context.bot.copy_message(u, uid, update.message.message_id)
                except: pass
            await update.message.reply_text("✅ ارسال شد."); state[uid] = None; return

    # --- لاجیک کاربران ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("دسته مورد نظر:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    
    elif text in db["categories"]:
        plans = db["categories"][text]
        if not plans: await update.message.reply_text("خالی است."); return
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))

    elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'get_vpn_name':
        plan = state[uid]['plan']
        state[uid].update({'step': 'wait_photo', 'vpn_name': text})
        invoice = (f"📇 <b>پیش فاکتور شما:</b>\n👤 نام کاربری: <code>{text}</code>\n"
                   f"🔐 سرویس: {plan['name']}\n💶 قیمت: {plan['price']},000 تومان\n\n💰 سفارش آماده پرداخت است.")
        btn = [[InlineKeyboardButton("ادامه و دریافت شماره کارت ✅", callback_data="show_card")]]
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup(btn), parse_mode='HTML')

    elif text == 'تست رایگان':
        if db["users"][uid].get("test_used"): await update.message.reply_text("❌ قبلاً استفاده شده."); return
        await update.message.reply_text("🚀 درخواست ثبت شد.")
        btn = [[InlineKeyboardButton("ارسال تست 🎁", callback_data=f"adm_test_{uid}")]]
        await context.bot.send_message(ADMIN_ID, f"تست رایگان: {uid}", reply_markup=InlineKeyboardMarkup(btn))

    # ادمین در حال ارسال کانفیگ نهایی
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'send_final_cfg':
        target = state[uid]['target']
        msg = (f"<b>✅ سرویس شما آماده شد</b>\n\n"
               f"🔗 لینک اتصال:\n<code>{text}</code>\n\n"
               f"🚀 برای آموزش اتصال دکمه زیر را لمس کنید:")
        btn = [[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/help_dragon")]]
        await context.bot.send_message(target, msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("✅ برای کاربر ارسال شد."); state[uid] = None

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()

    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 یک نام دلخواه برای اکانت بفرستید (مثلا arash):", reply_markup=CANCEL_KB)

    elif query.data == "show_card":
        txt = f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n👤 بنام: {db['card']['name']}\n\nلطفاً فیش را ارسال کنید:"
        btn = [[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_photo")]]
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(btn), parse_mode='HTML')

    elif query.data == "get_photo":
        await query.message.reply_text("📸 عکس فیش را بفرستید:")

    elif query.data.startswith("adm_"):
        _, act, target = query.data.split("_")
        state[str(ADMIN_ID)] = {'step': 'send_final_cfg', 'target': int(target)}
        await query.message.reply_text(f"لینک کانفیگ را برای {target} بفرستید:")

    elif query.data.startswith("delp_"):
        _, cat, pid = query.data.split("_")
        db["categories"][cat] = [p for p in db["categories"][cat] if str(p['id']) != pid]
        save_db(db); await query.message.delete()
        await query.message.reply_text("✅ حذف شد.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'wait_photo':
        info = state[uid]
        cap = f"🔔 فیش جدید!\n🆔 آیدی: {uid}\n👤 نام انتخابی: {info['vpn_name']}\n📦 پلن: {info['plan']['name']}"
        btn = [[InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"adm_pay_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش شما برای ادمین ارسال شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
