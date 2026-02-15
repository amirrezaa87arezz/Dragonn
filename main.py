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

# --- دیتابیس حرفه‌ای ---
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
        
        # لاجیک افزودن پلن توسط ادمین
        if state.get(uid) == 'add_p_cat':
            state[uid] = {'step': 'add_p_name', 'cat': text}
            await update.message.reply_text("نام پلن (مثلاً 200G):", reply_markup=CANCEL_KB)
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_p_name':
            state[uid].update({'step': 'add_p_price', 'name': text})
            await update.message.reply_text("قیمت (مثلاً 450):")
            return
        elif isinstance(state.get(uid), dict) and state[uid].get('step') == 'add_p_price':
            db["categories"][state[uid]['cat']].append({"id": len(db["categories"][state[uid]['cat']])+1, "name": state[uid]['name'], "price": text})
            save_db(db); state[uid] = None
            await update.message.reply_text("✅ پلن با موفقیت اضافه شد.", reply_markup=get_main_menu(uid))
            return

        # ارسال کانفیگ
        if isinstance(state.get(uid), dict) and state[uid].get('step') == 'send_cfg':
            info = state[uid]
            target = str(info['target'])
            if target in db["users"] and info.get('is_new', True):
                db["users"][target]["purchases"].append(f"📦 {info['vol']} | 👤 {info['vpn_name']}")
                save_db(db)
            
            final_msg = f"👤 سرویس: <code>{info.get('vpn_name', 'تمدیدی')}</code>\n⏳ مدت: {info.get('duration', 'نامحدود')}\n🗜 حجم: {info.get('vol', 'نامشخص')}\n\nلینک:\n<code>{text}</code>"
            await context.bot.send_message(target, final_msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 آموزش", url="https://t.me/help_dragon")]]))
            await update.message.reply_text("✅ ارسال شد."); state[uid] = None; return

    # --- کاربر ---
    if text == 'سرویس‌های من':
        purchases = db["users"].get(uid, {}).get("purchases", [])
        if not purchases: await update.message.reply_text("📭 خالی است."); return
        for p in purchases:
            btn = [[InlineKeyboardButton("🔄 تمدید هوشمند این سرویس", callback_data=f"renstart_{uid}")]]
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
        invoice = f"📇 <b>پیش فاکتور</b>\n👤 نام: {text}\n🔐 پلن: {plan['name']}\n💶 قیمت: {plan['price']},000 تومان"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]), parse_mode='HTML')

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; uid = str(query.from_user.id); await query.answer()
    
    # شروع تمدید هوشمند
    if query.data.startswith("renstart_"):
        kb = [[InlineKeyboardButton(f"{m} ماهه 📅", callback_data=f"rentime_{m}m")] for m in [1, 2, 3, 6]]
        await query.message.reply_text("⏳ مدت زمان تمدید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith("rentime_"):
        state[uid] = {'step': 'ren_vol_auto', 'duration': query.data.split("_")[1]}
        # استخراج تمام پلن‌ها از همه دسته‌ها برای نمایش در تمدید
        all_plans = []
        for cat in db["categories"]:
            for p in db["categories"][cat]:
                all_plans.append(p)
        
        if not all_plans:
            await query.message.reply_text("❌ ابتدا باید پلن‌ها را در مدیریت تعریف کنید.")
            return

        btn = [[InlineKeyboardButton(f"{p['name']} - {p['price']}ت", callback_data=f"renfinal_{p['name']}_{p['price']}")] for p in all_plans]
        await query.message.reply_text("🚀 حجم مورد نظر (بر اساس پلن‌های موجود):", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("renfinal_"):
        _, vol, price = query.data.split("_")
        state[uid].update({'vol': vol, 'price': price, 'step': 'wait_pay'})
        invoice = (f"📇 <b>پیش فاکتور تمدید حرفه‌ای</b>\n"
                   f"⏳ مدت تمدید: {state[uid]['duration']}\n"
                   f"🚀 حجم انتخابی: {vol}\n"
                   f"💶 مبلغ: {price},000 تومان")
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید و شماره کارت ✅", callback_data="show_card")]]), parse_mode='HTML')

    elif query.data.startswith("buy_"):
        _, cat, pid = query.data.split("_")
        plan = next(p for p in db["categories"][cat] if str(p['id']) == pid)
        state[uid] = {'step': 'get_vpn_name', 'plan': plan}
        await query.message.reply_text("📝 نام اکانت (انگلیسی):", reply_markup=CANCEL_KB)
    
    elif query.data == "show_card":
        price = state[uid]['plan']['price'] if 'plan' in state[uid] else state[uid]['price']
        txt = f"💳 <b>شماره کارت:</b>\n<code>{db['card']['number']}</code>\n💰 <b>مبلغ: {price},000 تومان</b>\n👤 <b>بنام {db['card']['name']}</b>"
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش", callback_data="get_photo")]]), parse_mode='HTML')
    
    elif query.data == "get_photo": await query.message.reply_text("📸 عکس فیش را بفرستید:")
    
    elif query.data.startswith("adm_pay_"):
        target = query.data.split("_")[2]
        is_new = 'plan' in state[target]
        state[str(ADMIN_ID)] = {'step': 'send_cfg', 'target': int(target), 'is_new': is_new,
                               'vpn_name': state[target].get('vpn_name', 'تمدیدی'),
                               'vol': state[target]['plan']['name'] if is_new else state[target]['vol'],
                               'duration': 'نامحدود' if is_new else state[target]['duration']}
        await query.message.reply_text(f"پاسخ/لینک برای {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if isinstance(state.get(uid), dict) and state[uid].get('step') == 'wait_pay':
        btn = [[InlineKeyboardButton("✅ تایید و ارسال", callback_data=f"adm_pay_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"فیش جدید از {uid}", reply_markup=InlineKeyboardMarkup(btn))
        await update.message.reply_text("🚀 فیش ارسال شد. منتظر تایید ادمین باشید.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(handle_call))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)
