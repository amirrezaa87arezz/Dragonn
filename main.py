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
def home(): return "Dragon VPN is Online!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- دیتابیس ---
DB_PATH = '/app/data'
DB_FILE = '/app/data/data.json'

def load_db():
    if not os.path.exists(DB_PATH): os.makedirs(DB_PATH, exist_ok=True)
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {"users": {}, "card": {"number": "6277601368776066", "name": "رضوانی"}, "categories": {"ارزان و به صرفه": [], "قوی": []}}

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

    # --- ادمین ---
    if uid_int == ADMIN_ID:
        if text == '⚙️ مدیریت ربات':
            kb = [['افزودن پلن', 'حذف/ویرایش پلن'], ['ویرایش کارت', 'پیام همگانی'], ['بازگشت به منوی اصلی']]
            await update.message.reply_text("🛠 مدیریت ربات:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return
        
        elif text == 'پیام همگانی':
            state[uid] = 'broadcasting'
            await update.message.reply_text("پیام همگانی را بفرستید:", reply_markup=CANCEL_KB)
            return

        elif state.get(uid) == 'broadcasting':
            for user_id in db["users"].keys():
                try: await context.bot.copy_message(chat_id=user_id, from_chat_id=uid, message_id=update.message.message_id)
                except: pass
            state[uid] = None
            await update.message.reply_text("✅ ارسال شد.", reply_markup=get_main_menu(uid))
            return

        # ارسال کانفیگ یا پاسخ تمدید
        if isinstance(state.get(uid), dict) and state[uid].get('step') == 'send_cfg':
            info = state[uid]
            target = str(info['target'])
            
            if target in db["users"] and info.get('is_new', True):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                save_db(db)

            final_msg = (
                f"👤 نام کاربری سرویس : <code>{info.get('vpn_name', 'تمدیدی')}</code>\n"
                f"⏳ مدت زمان: {info.get('duration', 'نامحدود')}\n"
                f"🗜 حجم سرویس: {info.get('vol', 'نامشخص')}\n\n"
                f"لینک اتصال:\n<code>{text}</code>\n\n"
                f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید"
            )
            btn = [[InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/help_dragon")]]
            await context.bot.send_message(target, final_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(btn))
            await update.message.reply_text("✅ ارسال شد."); state[uid] = None; return

    # --- کاربر ---
    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases:
            await update.message.reply_text("📭 لیست سرویس‌های شما خالی است.")
        else:
            await update.message.reply_text("📂 لیست سرویس‌های شما:")
            for p in purchases:
                btn = [[InlineKeyboardButton("🔄 تمدید این سرویس", callback_data=f"renew_start_{uid}")]]
                await update.message.reply_text(f"✅ {p}", reply_markup=InlineKeyboardMarkup(btn))

    elif text == 'خرید اشتراک':
        kb = [[c] for c in db["categories"].keys()]
        await update.message.reply_text("انتخاب دسته:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in db["categories"]:
        plans = db["categories"][text]
        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"buy_{text}_{p['id']}")] for p in plans]
        await update.message.reply_text(f"پلن‌های {text}:", reply_markup=InlineKeyboardMarkup(btn))

    elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'get_vpn_name':
        plan = state[uid]['plan']
        state[uid].update({'step': 'wait_pay', 'vpn_name': text})
        invoice = f"📇 <b>پیش فاکتور</b>\n👤 نام انتخابی: {text}\n🔐 پلن: {plan['name']}\n💶 قیمت: {plan['price']},000 تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]), parse_mode='HTML')

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    # شروع روند تمدید
    if query.data.startswith("renew_start_"):
        kb = [
            [InlineKeyboardButton("۱ ماهه 📅", callback_data="rentime_1m"), InlineKeyboardButton("۲ ماهه 📅", callback_data="rentime_2m")],
            [InlineKeyboardButton("۳ ماهه 📅", callback_data="rentime_3m")]
        ]
        await query.message.reply_text("⏳ مدت زمان تمدید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rentime_"):
        duration = query.data.split("_")[1]
        state[uid] = {'step': 'ren_vol', 'duration': duration}
        kb = [
            [InlineKeyboardButton("20 گیگ", callback_data="renvol_20G_130"), InlineKeyboardButton("50 گیگ", callback_data="renvol_50G_230")],
            [InlineKeyboardButton("100 گیگ", callback_data="renvol_100G_350")]
        ]
        await query.message.reply_text("🚀 حجم مورد نظر برای تمدید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("renvol_"):
        _, vol, price = query.data.split("_")
        state[uid].update({'vol': vol, 'price': price, 'step': 'wait_pay'})
        invoice = (f"📇 <b>پیش فاکتور تمدید سرویس</b>\n"
                   f"⏳ مدت: {state[uid]['duration']}\n"
                   f"🚀 حجم: {vol}\n"
                   f"💶 مبلغ تمدید: {price},000 تومان")
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و دریافت شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')

    # ادامه روند خرید معمولی
    elif query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام دلخواه اکانت (انگلیسی):", reply_markup=CANCEL_KB)
    
    elif query.data == "show_card":
        # دریافت قیمت از خرید یا تمدید
        price = state[uid]['plan']['price'] if 'plan' in state[uid] else state[uid]['price']
        txt = (f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n"
               f"💰 <b>مبلغ: {price},000 تومان</b>\n"
               f"👤 <b>بنام {db['card']['name']}</b>\n\n"
               f"⭕ لطفاً مبلغ را دقیق واریز کنید و فیش را بفرستید.")
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]), parse_mode='HTML')
    
    elif query.data == "get_photo":
        await query.message.reply_text("📸 عکس فیش واریزی را بفرستید:")
    
    elif query.data.startswith("adm_pay_"):
        target = query.data.split("_")[2]
        # تنظیم اطلاعات برای پاسخ ادمین
        is_new = 'plan' in state[target]
        state[str(ADMIN_ID)] = {
            'step': 'send_cfg', 
            'target': int(target), 
            'is_new': is_new,
            'vpn_name': state[target].get('vpn_name', 'تمدیدی'),
            'vol': state[target]['plan']['name'] if is_new else state[target]['vol'],
            'duration': 'نامحدود' if is_new else state[target]['duration']
        }
        await query.message.reply_text(f"لینک یا پیام تایید را برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'wait_pay':
        type_req = "خرید جدید" if 'plan' in state[uid] else "تمدید سرویس"
        info = state[uid]
        cap = f"🔔 فیش جدید ({type_req})!\n🆔 آیدی: {uid}\n📦 جزئیات: {info.get('vol', info.get('plan', {}).get('name'))}"
        btn = [[InlineKeyboardButton("✅ تایید و ارسال پاسخ", callback_data=f"adm_pay_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش شما برای ادمین ارسال شد. لطفاً منتظر تایید باشید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
