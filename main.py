import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- تنظیمات زنده نگه داشتن ---
app_web = Flask('')
@app_web.route('/')
def home(): return "Dragon VPN is Running!"
def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات اصلی ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770

# حافظه موقت ربات
user_data_storage = {} 
admin_state = {} # حافظه مخصوص برای ادمین

# --- منوها ---
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه"
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # 1. بخش مدیریت (ارسال کانفیگ برای مشتری)
    if user_id == ADMIN_ID and admin_state.get('step') == 'waiting_for_config':
        target_id = admin_state.get('target_user')
        info = user_data_storage.get(target_id, {})
        
        final_msg = (
            f"نام کاربری سرویس : {info.get('chosen_name', 'نامشخص')}\n"
            f"⏳ مدت زمان: {info.get('time', 'نامشخص')}\n"
            f"🗜 حجم سرویس: {info.get('volume', 'نامشخص')}\n\n"
            f"لینک اتصال:\n`{text}`\n\n"
            f"🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه.\n"
            f"🔵 کافیه لینک ساب خودتون رو بهش بدید."
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("آموزش اتصال", url="https://t.me/help_dragon")]])
        
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=keyboard, parse_mode='Markdown')
            await update.message.reply_text(f"✅ کانفیگ با موفقیت برای کاربر {target_id} ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال: {e}")
        
        admin_state.clear() # پاکسازی وضعیت ادمین بعد از ارسال
        return

    # 2. منوهای معمولی
    if text == 'بازگشت به منوی اصلی':
        await start(update, context)

    elif text == 'خرید اشتراک':
        await update.message.reply_text("لطفاً نوع سرویس را انتخاب کنید:", 
            reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی'], ['بازگشت به منوی اصلی']], resize_keyboard=True))

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
            [InlineKeyboardButton("100 گیگ | 1 ماهه - 550,000", callback_data="p_100G_1 ماهه_550")],
            [InlineKeyboardButton("200 گیگ | 3 ماهه - 1,100,000", callback_data="p_200G_3 ماهه_1100")]
        ]
        await update.message.reply_text("لیست پلن‌های قوی:", reply_markup=InlineKeyboardMarkup(prices))

    elif text == 'پشتیبانی':
        await update.message.reply_text("پشتیبانی مستقیم: @reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))

    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات در چنل زیر:\nhttps://t.me/help_dragon")

    # 3. دریافت نام کاربری از مشتری
    elif user_id in user_data_storage and user_data_storage[user_id].get('step') == 'wait_name':
        user_data_storage[user_id]['chosen_name'] = text
        user_data_storage[user_id]['step'] = 'wait_pay'
        price = user_data_storage[user_id]['price']
        invoice = f"📇 پیش فاکتور شما:\n👤 نام انتخابی: {text}\n🔐 سرویس: {user_data_storage[user_id]['volume']}\n💶 قیمت: {price},000 تومان\n💰 آماده پرداخت"
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data="show_card")]]))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data.startswith("p_"):
        _, volume, time, price = query.data.split("_")
        user_data_storage[user_id] = {'volume': volume, 'time': time, 'price': price, 'step': 'wait_name'}
        await query.message.reply_text("لطفاً یک نام کاربری برای کانفیگ خود انتخاب و ارسال کنید (مثلاً: ali):", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))

    elif query.data == "show_card":
        info = user_data_storage.get(user_id, {})
        bank = f"💳 شماره کارت:\n`6277601368776066`\n💰 مبلغ: {info['price']},000 تومان\n👤 رضوانی\n\n⭕ فیش را ارسال کنید."
        await query.message.reply_text(bank, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش", callback_data="get_receipt")]]), parse_mode='Markdown')

    elif query.data == "get_receipt":
        user_data_storage[user_id]['step'] = 'wait_photo'
        await query.message.reply_text("لطفاً عکس فیش واریزی را ارسال فرمایید:")

    elif query.data.startswith("adm_to_"):
        target = int(query.data.split("_")[-1])
        admin_state['step'] = 'waiting_for_config'
        admin_state['target_user'] = target
        await query.message.reply_text(f"لطفاً لینک کانفیگ را برای کاربر {target} در اینجا پیست (Paste) کرده و ارسال کنید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data_storage.get(user_id, {}).get('step') == 'wait_photo':
        info = user_data_storage[user_id]
        caption = f"🔔 فیش جدید!\n🆔 آیدی: `{user_id}`\n👤 نام کاربر: {info['chosen_name']}\n📦 پلن: {info['volume']} | {info['time']}"
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, 
            caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفیگ ✅", callback_data=f"adm_to_{user_id}")]]))
        await update.message.reply_text("🚀 رسید شما ارسال شد. پس از تایید، سرویس برای شما ارسال می‌شود.")

if __name__ == '__main__':
    Thread(target=run_web).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
