import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- بخش زنده نگه داشتن برای Render (Flask) ---
app_web = Flask('')

@app_web.route('/')
def home():
    return "Dragon VPN is Running!"

def run_web():
    # Render معمولاً از پورت 10000 استفاده می‌کند
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات اصلی ربات ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770

# حافظه موقت برای ذخیره وضعیت کاربران و ادمین
user_data = {} 
admin_state = {} 

# --- منوها ---
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه"
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    # 1. بخش مدیریت (ارسال کانفیگ برای مشتری توسط ادمین)
    if user_id == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        target_id = admin_state.get('target')
        info = user_data.get(target_id, {})
        
        # قالب HTML برای جلوگیری از ارور کاراکترهای خاص در لینک کانفیگ
        final_msg = (
            f"<b>نام کاربری سرویس :</b> {info.get('name', 'نامشخص')}\n"
            f"<b>⏳ مدت زمان:</b> {info.get('time', 'نامشخص')}\n"
            f"<b>🗜 حجم سرویس:</b> {info.get('vol', 'نامشخص')}\n\n"
            f"<b>لینک اتصال:</b>\n<code>{text}</code>\n\n"
            f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید\n\n"
            f"🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه.\n"
            f"🔵 کافیه لینک ساب خودتون رو بهش بدید."
        )
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("آموزش اتصال", url="https://t.me/help_dragon")]])
        
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=kb, parse_mode='HTML')
            await update.message.reply_text(f"✅ کانفیگ با موفقیت برای کاربر {target_id} ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال نهایی: {str(e)}")
            
        admin_state.clear()
        return

    # 2. مدیریت دکمه‌های منو
    if text == 'بازگشت به منوی اصلی':
        user_data[user_id] = {}
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
        await update.message.reply_text("لیست پلن‌های ارزان و به صرفه:", reply_markup=InlineKeyboardMarkup(prices))

    elif text == 'قوی':
        prices = [
            [InlineKeyboardButton("20 گیگ | 1 ماهه - 150,000", callback_data="p_20G_1 ماهه_150")],
            [InlineKeyboardButton("50 گیگ | 1 ماهه - 280,000", callback_data="p_50G_1 ماهه_280")],
            [InlineKeyboardButton("100 گیگ | 1 ماهه - 550,000", callback_data="p_100G_1 ماهه_550")],
            [InlineKeyboardButton("200 گیگ | 3 ماهه - 1,100,000", callback_data="p_200G_3 ماهه_1100")]
        ]
        await update.message.reply_text("لیست پلن‌های قوی (VIP):", reply_markup=InlineKeyboardMarkup(prices))

    elif text == 'پشتیبانی':
        await update.message.reply_text("برای پشتیبانی به آیدی زیر پیام دهید:\n@reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))

    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات در چنل زیر:\nhttps://t.me/help_dragon")

    # 3. دریافت نام کاربری انتخابی از کاربر
    elif user_id in user_data and user_data[user_id].get('step') == 'get_name':
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 'wait_pay'
        price = user_data[user_id]['price']
        
        invoice = (f"📇 پیش فاکتور شما:\n👤 نام انتخابی: {text}\n"
                   f"🔐 سرویس: {user_data[user_id]['vol']} | {user_data[user_id]['time']}\n"
                   f"💶 قیمت: {price},000 تومان\n💰 سفارش شما آماده پرداخت است")
        
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه و دریافت شماره کارت ✅", callback_data="show_card")]]))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data.startswith("p_"):
        _, vol, time, price = query.data.split("_")
        user_data[user_id] = {'vol': vol, 'time': time, 'price': price, 'step': 'get_name'}
        await query.message.reply_text("لطفاً یک نام کاربری برای کانفیگ خود انتخاب و ارسال کنید (مثلاً: ali):", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))

    elif query.data == "show_card":
        info = user_data.get(user_id, {})
        bank = (f"💳 شماره کارت:\n<code>6277601368776066</code>\n"
                f"💰 مبلغ: {info['price']},000 تومان\n👤 بنام رضوانی\n\n"
                f"⭕ کاربر گرامی لطفاً مبلغ واریزی را بصورت دقیق واریز کنید\n"
                f"⭕ از ارسال فیش جعلی خودداری فرمایید")
        await query.message.reply_text(bank, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش واریزی", callback_data="get_receipt")]]), parse_mode='HTML')

    elif query.data == "get_receipt":
        user_data[user_id]['step'] = 'wait_photo'
        await query.message.reply_text("لطفاً عکس فیش واریزی را ارسال فرمایید:")

    elif query.data.startswith("adm_to_"):
        target = int(query.data.split("_")[-1])
        admin_state['step'] = 'wait_cfg'
        admin_state['target'] = target
        await query.message.reply_text(f"لطفاً لینک کانفیگ را برای کاربر {target} در اینجا پیست کرده و ارسال کنید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get('step') == 'wait_photo':
        info = user_data[user_id]
        caption = (f"🔔 فیش جدید رسید!\n🆔 آیدی عددی: <code>{user_id}</code>\n👤 نام انتخابی: {info['name']}\n"
                   f"📦 پلن: {info['vol']} | {info['time']}")
        
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, 
            caption=caption, parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفیگ ✅", callback_data=f"adm_to_{user_id}")]]))
        
        await update.message.reply_text("🚀 رسید شما ارسال شد. پس از بررسی توسط ادمین، سرویس برای شما ارسال خواهد شد.")
        user_data[user_id]['step'] = 'done'

# --- اجرای ربات ---
def main():
    # شروع ترد Flask برای زنده نگه داشتن در Render
    Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Dragon VPN is Online...")
    app.run_polling()

if __name__ == '__main__':
    main()
