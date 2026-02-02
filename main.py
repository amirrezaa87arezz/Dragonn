import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# تنظیمات لاگ برای دیباگ در پنل رندر
logging.basicConfig(level=logging.INFO)

# --- سیستم زنده نگه داشتن (Keep-Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- تنظیمات ربات ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770

user_db = {}
admin_state = {}

# منوها
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_KB = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid = update.message.text, update.message.from_user.id

    # مدیریت پنل ادمین (ارسال کانفیگ برای مشتری)
    if uid == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        tid = admin_state.get('target')
        try:
            await context.bot.send_message(chat_id=tid, text=f"✅ <b>سرویس شما آماده شد:</b>\n\n<code>{text}</code>", parse_mode='HTML')
            await update.message.reply_text("✅ کانفیگ با موفقیت برای کاربر ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال: {e}")
        admin_state.clear(); return

    # منوی اصلی و فرعی
    if text == 'بازگشت به منوی اصلی':
        user_db[uid] = {}; await start(update, context)
    elif text == 'خرید اشتراک':
        await update.message.reply_text("لطفاً نوع سرویس را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی'], ['بازگشت به منوی اصلی']], resize_keyboard=True))
    elif text == 'ارزان و به صرفه':
        plans = [
            [InlineKeyboardButton("20 گیگ - 130,000", callback_data="p_20G_ارزان_130")],
            [InlineKeyboardButton("30 گیگ - 160,000", callback_data="p_30G_ارزان_160")],
            [InlineKeyboardButton("50 گیگ - 250,000", callback_data="p_50G_ارزان_250")],
            [InlineKeyboardButton("100 گیگ - 420,000", callback_data="p_100G_ارزان_420")]
        ]
        await update.message.reply_text("لیست پلن‌های ارزان:", reply_markup=InlineKeyboardMarkup(plans))
    elif text == 'قوی':
        plans = [
            [InlineKeyboardButton("20 گیگ 1 ماهه - 150,000", callback_data="p_20G_قوی_150")],
            [InlineKeyboardButton("50 گیگ 1 ماهه - 280,000", callback_data="p_50G_قوی_280")],
            [InlineKeyboardButton("100 گیگ 1 ماهه - 550,000", callback_data="p_100G_قوی_550")]
        ]
        await update.message.reply_text("لیست پلن‌های قوی:", reply_markup=InlineKeyboardMarkup(plans))
    elif text == 'پشتیبانی':
        await update.message.reply_text("برای پشتیبانی به آیدی زیر پیام دهید:\n@reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_KB, resize_keyboard=True))
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات در کانال زیر موجود است:\nhttps://t.me/help_dragon")

async def handle_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data.startswith("p_"):
        _, vol, type, price = query.data.split("_")
        user_db[uid] = {'vol': vol, 'price': price, 'type': type}
        invoice = (f"📇 پیش فاکتور شما:\n👤 نام کاربری: {uid}\n🔐 سرویس: {vol} | {type}\n💶 قیمت: {price},000 تومان\n\n💰 سفارش شما آماده پرداخت است")
        await query.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="card")]]))
    elif query.data == "card":
        info = user_db.get(uid, {})
        txt = (f"<code>6277601368776066</code>\n\n💰 مبلغ: {info.get('price', '0')},000 تومان\n👤 بنام رضوانی\n\n"
               "⭕ لطفاً مبلغ را دقیق واریز کرده و فیش جعلی ارسال نکنید.")
        await query.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش", callback_data="get_rec")]), parse_mode='HTML')
    elif query.data == "get_rec":
        user_db[uid]['step'] = 'photo'
        await query.message.reply_text("لطفاً عکس فیش واریزی را ارسال فرمایید:")
    elif query.data.startswith("adm_"):
        admin_state.update({'step': 'wait_cfg', 'target': int(query.data.split("_")[1])})
        await query.message.reply_text("لطفاً لینک کانفیگ را اینجا بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if user_db.get(uid, {}).get('step') == 'photo':
        caption = f"🔔 فیش جدید رسید!\n🆔 آیدی کاربر: <code>{uid}</code>\n📦 پلن: {user_db[uid]['vol']}"
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, parse_mode='HTML', 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفینگ ✅", callback_data=f"adm_{uid}")]]))
        await update.message.reply_text("🚀 رسید شما ارسال و پس از بررسی سرویس برای شما ارسال خواهد شد.")

if __name__ == '__main__':
    Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    application.add_handler(CallbackQueryHandler(handle_call))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling(drop_pending_updates=True)
  
