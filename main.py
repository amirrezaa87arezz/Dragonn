import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

app_web = Flask('')
@app_web.route('/')
def home(): return "Dragon VPN is Running!"
def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data, admin_state = {}, {}

MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("خوش اومدید به ربات Dragon vpn", reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, user_id = update.message.text, update.message.from_user.id

    if user_id == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        target_id = admin_state.get('target')
        info = user_data.get(target_id, {})
        final_msg = (f"<b>نام کاربری سرویس :</b> {info.get('name', 'نامشخص')}\n"
                     f"<b>⏳ مدت زمان:</b> {info.get('time', 'نامشخص')}\n"
                     f"<b>🗜 حجم سرویس:</b> {info.get('vol', 'نامشخص')}\n\n"
                     f"<b>لینک اتصال:</b>\n<code>{text}</code>\n\n"
                     f"🟢 اگر لینک ساب اضافه نشد، از @URLExtractor_Bot کمک بگیرید.")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("آموزش اتصال", url="https://t.me/help_dragon")]])
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=kb, parse_mode='HTML')
            await update.message.reply_text("✅ با موفقیت ارسال شد.")
        except Exception as e: await update.message.reply_text(f"❌ خطا: {str(e)}")
        admin_state.clear(); return

    if text == 'بازگشت به منوی اصلی': await start(update, context)
    elif text == 'خرید اشتراک':
        await update.message.reply_text("نوع سرویس:", reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی'], ['بازگشت به منوی اصلی']], resize_keyboard=True))
    elif text == 'ارزان و به صرفه':
        prices = [[InlineKeyboardButton("20 گیگ - 130ت", callback_data="p_20G_نامحدود_130")]]
        await update.message.reply_text("لیست پلن‌ها:", reply_markup=InlineKeyboardMarkup(prices))
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات:\nhttps://t.me/help_dragon")
    elif user_id in user_data and user_data[user_id].get('step') == 'get_name':
        user_data[user_id].update({'name': text, 'step': 'wait_pay'})
        await update.message.reply_text(f"فاکتور برای {text} آماده است.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data.startswith("p_"):
        _, vol, time, price = query.data.split("_")
        user_data[user_id] = {'vol': vol, 'time': time, 'price': price, 'step': 'get_name'}
        await query.message.reply_text("لطفاً یک نام (مثلاً ali) بفرستید:", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))
    elif query.data == "show_card":
        await query.message.reply_text(f"شماره کارت: <code>6277601368776066</code>\nفیش را بفرستید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش", callback_data="get_receipt")]]), parse_mode='HTML')
    elif query.data == "get_receipt":
        user_data[user_id]['step'] = 'wait_photo'
        await query.message.reply_text("عکس فیش را بفرستید:")
    elif query.data.startswith("adm_to_"):
        admin_state.update({'step': 'wait_cfg', 'target': int(query.data.split("_")[-1])})
        await query.message.reply_text("لینک کانفیگ را پیست کنید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get('step') == 'wait_photo':
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"فیش از {user_id}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفیگ ✅", callback_data=f"adm_to_{user_id}")]]))
        await update.message.reply_text("🚀 فیش ارسال شد.")

if __name__ == '__main__':
    Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
  
