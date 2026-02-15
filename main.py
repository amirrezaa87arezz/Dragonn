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

# --- دیتابیس ---
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

    if text in ['❌ انصراف و بازگشت', 'بازگشت به منوی اصلی']:
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
        elif state.get(uid) == 'edit_card_num':
            db["card"]["number"] = text; state[uid] = 'edit_card_name'
            await update.message.reply_text("نام صاحب کارت جدید:")
            return
        elif state.get(uid) == 'edit_card_name':
            db["card"]["name"] = text; save_db(db); state[uid] = None
            await update.message.reply_text("✅ اطلاعات کارت بروزرسانی شد.", reply_markup=get_main_menu(uid))
            return
        elif text == 'افزودن پلن':
            state[uid] = 'add_p_cat'
            kb = [[c] for c in db["categories"].keys()]
            await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        elif state.get(uid) == 'add_p_cat':
            state[uid] = {'step': 'add_p_name', 'cat': text}
            await update.message.reply_text("نام پلن (مثلاً 100G):", reply_markup=CANCEL_KB)
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_p_name':
            state[uid].update({'step': 'add_p_price', 'name': text})
            await update.message.reply_text("قیمت (بدون صفر آخر - مثلا 250):")
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_p_price':
            db["categories"][state[uid]['cat']].append({"id": len(db["categories"][state[uid]['cat']])+1, "name": state[uid]['name'], "price": text})
            save_db(db); state[uid] = None
            await update.message.reply_text("✅ پلن اضافه شد.", reply_markup=get_main_menu(uid))
            return

        # ارسال کانفیگ توسط ادمین
        if isinstance(state.get(uid), dict) and state[uid].get('step') == 'send_cfg':
            info = state[uid]
            target = info['target']
            final_msg = (
                f"👤 نام کاربری سرویس : <code>{info['vpn_name']}</code>\n"
                f"⏳ مدت زمان: نامحدود\n"
                f"🗜 حجم سرویس: {info['vol']}\n\n"
                f"لینک اتصال:\n<code>{text}</code>\n\n"
                f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید\n\n"
                f"🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه.\n"
                f"🔵 کافیه لینک ساب خودتون رو بهش بدید."
            )
            btn = [[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/help_dragon")]]
            await context.bot.send_message(target, final_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
            await update.message.reply_text("✅ کانفیگ برای کاربر ارسال شد."); state[uid] = None; return

    # --- پنل کاربر ---
    if text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("دسته مورد نظر:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    elif text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))
    elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'get_vpn_name':
        plan = state[uid]['plan']
        state[uid].update({'step': 'wait_pay', 'vpn_name': text})
        invoice = f"📇 <b>پیش فاکتور</b>\n👤 نام انتخابی: {text}\n🔐 پلن: {plan['name']}\n💶 قیمت: {plan['price']},000 تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]), parse_mode='HTML')
    elif text == 'پشتیبانی':
        await update.message.reply_text("پشتیبانی: @reunite_music")
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزش: https://t.me/help_dragon")

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    if query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام دلخواه اکانت را بفرستید (انگلیسی):", reply_markup=CANCEL_KB)
    elif query.data == "show_card":
        plan = state[uid]['plan']
        txt = (f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n"
               f"💰 <b>مبلغ: {plan['price']},000 تومان</b>\n"
               f"👤 <b>بنام {db['card']['name']}</b>\n\n"
               f"⭕ کاربر گرامی لطفاً مبلغ واریزی را بصورت دقیق واریز کنید\n"
               f"⭕ از ارسال فیش جعلی خودداری فرمایید")
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]), parse_mode='HTML')
    elif query.data == "get_photo":
        await query.message.reply_text("📸 عکس فیش را بفرستید:")
    elif query.data.startswith("adm_pay_"):
        target = query.data.split("_")[2]
        # انتقال اطلاعات پلن به وضعیت ادمین برای پیام نهایی
        state[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': int(target), 
                               'vpn_name': state[target]['vpn_name'], 'vol': state[target]['plan']['name']}
        await query.message.reply_text(f"لطفاً لینک کانفیگ را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'wait_pay':
        cap = f"🔔 فیش جدید!\n🆔 آیدی: {uid}\n👤 نام انتخابی: {state[uid]['vpn_name']}\n📦 پلن: {state[uid]['plan']['name']}"
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=cap, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"adm_pay_{uid}")]]))
        await update.message.reply_text("🚀 فیش شما برای ادمین ارسال شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
