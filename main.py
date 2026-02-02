import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- تنظیمات Flask برای زنده نگه داشتن ربات ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Dragon VPN is Online!"
def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات اصلی ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_data, admin_state = {}, {}

# --- دکمه‌ها ---
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه"
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, user_id = update.message.text, update.message.from_user.id

    # مدیریت ارسال کانفیگ توسط ادمین
    if user_id == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        target_id = admin_state.get('target')
        info = user_data.get(target_id, {})
        final_msg = (
            f"نام کاربری سرویس : {info.get('name', 'نامشخص')}\n"
            f"⏳ مدت زمان: {info.get('time', 'نامشخص')}\n"
            f"🗜 حجم سرویس: {info.get('vol', 'نامشخص')}\n\n"
            f"لینک اتصال:\n<code>{text}</code>\n\n"
            f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید\n\n"
            f"🟢 اگر لینک ساب اضافه نشد، @URLExtractor_Bot به شما کمک می‌کنه."
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("آموزش اتصال", url="https://t.me/help_dragon")]])
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=kb, parse_mode='HTML')
            await update.message.reply_text("✅ با موفقیت برای کاربر ارسال شد.")
        except Exception as e: await update.message.reply_text(f"❌ خطا: {str(e)}")
        admin_state.clear(); return

    # منوهای کاربری
    if text == 'بازگشت به منوی اصلی':
        user_data[user_id] = {}; await start(update, context)
    elif text == 'خرید اشتراک':
        await update.message.reply_text("لطفاً نوع سرویس را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی'], ['بازگشت به منوی اصلی']], resize_keyboard=True))
    elif text == 'ارزان و به صرفه':
        prices = [
            [InlineKeyboardButton("20 گیگ | نامحدود - 130,000", callback_data="p_20G_نامحدود_130")],
            [InlineKeyboardButton("30 گیگ | نامحدود - 160,000", callback_data="p_30G_نامحدود_160")],
            [InlineKeyboardButton("50 گیگ | نامحدود - 250,000", callback_data="p_50G_نامحدود_250")],
            [InlineKeyboardButton("100 گیگ | نامحدود - 420,000", callback_data="p_100G_نامحدود_420")]
        ]
        await update.message.reply_text("لیست پلن‌های ارزان:", reply_markup=InlineKeyboardMarkup(prices))
    elif text == 'قوی':
        prices = [
            [InlineKeyboardButton("20 گیگ | 1 ماهه - 150,000", callback_data="p_20G_1 ماهه_150")],
            [InlineKeyboardButton("50 گیگ | 1 ماهه - 280,000", callback_data="p_50G_1 ماهه_280")],
            [InlineKeyboardButton("100 گیگ | 1 ماهه - 550,000", callback_data="p_100G_1 ماهه_550")]
        ]
        await update.message.reply_text("لیست پلن‌های قوی:", reply_markup=InlineKeyboardMarkup(prices))
    elif text == 'پشتیبانی':
        await update.message.reply_text("پشتیبانی: @reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات در چنل زیر:\nhttps://t.me/help_dragon")

    # دریافت نام کاربری
    elif user_id in user_data and user_data[user_id].get('step') == 'get_name':
        user_data[user_id].update({'name': text, 'step': 'wait_pay'})
        p = user_data[user_id]['price']
        invoice = (f"📇 <b>پیش فاکتور شما:</b>\n👤 نام انتخابی: {text}\n"
                   f"🔐 سرویس: {user_data[user_id]['vol']} | {user_data[user_id]['time']}\n"
                   f"💶 قیمت: {p},000 تومان\n\n💰 سفارش آماده پرداخت است")
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]), parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data.startswith("p_"):
        _, vol, time, price = query.data.split("_")
        user_data[user_id] = {'vol': vol, 'time': time, 'price': price, 'step': 'get_name'}
        await query.message.reply_text("لطفاً یک نام (مثلاً ali) برای کانفیگ بفرستید:", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))
    elif query.data == "show_card":
        info = user_data.get(user_id, {})
        bank = (f"💳 شماره کارت:\n<code>6277601368776066</code>\n💰 مبلغ: {info['price']},000 تومان\n👤 بنام رضوانی\n\n⭕ فیش را ارسال کنید.")
        await query.message.reply_text(bank, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش واریزی", callback_data="get_receipt")]]), parse_mode='HTML')
    elif query.data == "get_receipt":
        user_data[user_id]['step'] = 'wait_photo'
        await query.message.reply_text("لطفاً عکس فیش را بفرستید:")
    elif query.data.startswith("adm_to_"):
        admin_state.update({'step': 'wait_cfg', 'target': int(query.data.split("_")[-1])})
        await query.message.reply_text("لینک کانفیگ را پیست (Paste) کنید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get('step') == 'wait_photo':
        info = user_data[user_id]
        caption = f"🔔 فیش جدید!\n👤 نام: {info['name']}\n📦 پلن: {info['vol']}\n🆔 آیدی: <code>{user_id}</code>"
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفیگ ✅", callback_data=f"adm_to_{user_id}")]]))
        await update.message.reply_text("🚀 فیش شما ارسال شد.")

if __name__ == '__main__':
    Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
                                  
