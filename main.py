import os
from flask import Flask
from threading import Thread
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- تنظیمات لاگ برای عیب‌یابی راحت‌تر ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- بخش زنده نگه داشتن حرفه‌ای ---
app_web = Flask('')

@app_web.route('/')
def home():
    # این پاسخی است که UptimeRobot دریافت می‌کند و متوجه می‌شود ربات زنده است
    return "Dragon VPN is Online and Working!", 200

@app_web.route('/health')
def health():
    return "OK", 200

def run_web():
    # Render پورت را از این طریق به برنامه می‌دهد
    port = int(os.environ.get('PORT', 8080))
    # استفاده از 0.0.0.0 برای دسترسی عمومی در شبکه سرور
    app_web.run(host='0.0.0.0', port=port)

# --- تنظیمات اصلی ربات ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770

user_data = {} 
admin_state = {} 

MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = "🐉 به ربات Dragon VPN خوش آمدید\n🚀 پرسرعت، ارزان و به‌صرفه"
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if user_id == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        target_id = admin_state.get('target')
        info = user_data.get(target_id, {})
        final_msg = (
            f"<b>✅ سرویس شما آماده شد</b>\n\n"
            f"👤 <b>نام کاربری:</b> {info.get('name', 'نامشخص')}\n"
            f"⏳ <b>مدت زمان:</b> {info.get('time', 'نامشخص')}\n"
            f"🗜 <b>حجم سرویس:</b> {info.get('vol', 'نامشخص')}\n\n"
            f"🔗 <b>لینک اتصال (برای کپی لمس کنید):</b>\n<code>{text}</code>\n\n"
            f"🟢 اگر لینک ساب در برنامه اضافه نشد، از ربات @URLExtractor_Bot استفاده کنید."
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎥 آموزش اتصال", url="https://t.me/help_dragon")]])
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=kb, parse_mode='HTML')
            await update.message.reply_text(f"✅ با موفقیت برای کاربر {target_id} ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال: {str(e)}")
        admin_state.clear()
        return

    if text == 'بازگشت به منوی اصلی':
        user_data[user_id] = {}
        await start(update, context)
    elif text == 'خرید اشتراک':
        await update.message.reply_text("لطفاً نوع سرویس مورد نظر را انتخاب کنید:", 
            reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی (VIP)'], ['بازگشت به منوی اصلی']], resize_keyboard=True))
    elif text == 'ارزان و به صرفه':
        prices = [
            [InlineKeyboardButton("20 گیگ | نامحدود - 130,000", callback_data="p_20G_نامحدود_130")],
            [InlineKeyboardButton("30 گیگ | نامحدود - 160,000", callback_data="p_30G_نامحدود_160")],
            [InlineKeyboardButton("50 گیگ | نامحدود - 250,000", callback_data="p_50G_نامحدود_250")]
        ]
        await update.message.reply_text("💎 لیست پلن‌های اقتصادی:", reply_markup=InlineKeyboardMarkup(prices))
    elif text == 'قوی (VIP)':
        prices = [
            [InlineKeyboardButton("50 گیگ | 1 ماهه - 280,000", callback_data="p_50G_1 ماهه_280")],
            [InlineKeyboardButton("100 گیگ | 1 ماهه - 550,000", callback_data="p_100G_1 ماهه_550")]
        ]
        await update.message.reply_text("🚀 لیست پلن‌های VIP:", reply_markup=InlineKeyboardMarkup(prices))
    elif text == 'پشتیبانی':
        await update.message.reply_text("👨‍💻 برای پشتیبانی به آیدی زیر پیام دهید:\n@reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))
    elif text == 'راهنمای اتصال':
        await update.message.reply_text("📚 آموزش اتصال در کانال زیر موجود است:\nhttps://t.me/help_dragon")
    elif user_id in user_data and user_data[user_id].get('step') == 'get_name':
        user_data[user_id]['name'] = text
        user_data[user_id]['step'] = 'wait_pay'
        price = user_data[user_id]['price']
        invoice = (f"📇 <b>پیش فاکتور خرید:</b>\n\n👤 <b>نام انتخابی:</b> {text}\n"
                   f"🔐 <b>سرویس:</b> {user_data[user_id]['vol']} | {user_data[user_id]['time']}\n"
                   f"💶 <b>قیمت:</b> {price},000 تومان\n\n💳 برای دریافت شماره کارت روی دکمه زیر بزنید:")
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("دریافت شماره کارت 💳", callback_data="show_card")]]), parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data.startswith("p_"):
        _, vol, time, price = query.data.split("_")
        user_data[user_id] = {'vol': vol, 'time': time, 'price': price, 'step': 'get_name'}
        await query.message.reply_text("📝 یک نام دلخواه برای کانفیگ خود ارسال کنید (مثلاً: Arash):", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))
    elif query.data == "show_card":
        info = user_data.get(user_id, {})
        bank = (f"💳 <b>شماره کارت جهت واریز:</b>\n<code>6277601368776066</code>\n\n"
                f"💰 <b>مبلغ دقیق:</b> {info['price']},000 تومان\n👤 <b>به نام:</b> رضوانی\n\n"
                f"⚠️ لطفاً پس از واریز، <b>فقط عکس فیش</b> را ارسال کنید.")
        await query.message.reply_text(bank, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال فیش واریزی", callback_data="get_receipt")]]), parse_mode='HTML')
    elif query.data == "get_receipt":
        user_data[user_id]['step'] = 'wait_photo'
        await query.message.reply_text("📸 لطفاً تصویر فیش واریزی خود را بفرستید:")
    elif query.data.startswith("adm_to_"):
        target = int(query.data.split("_")[-1])
        admin_state['step'] = 'wait_cfg'; admin_state['target'] = target
        await query.message.reply_text(f"📤 لینک کانفیگ را برای کاربر {target} بفرستید:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get('step') == 'wait_photo':
        info = user_data[user_id]
        caption = (f"🔔 <b>فیش واریزی جدید!</b>\n\n🆔 <b>آیدی عددی:</b> <code>{user_id}</code>\n"
                   f"👤 <b>نام انتخابی:</b> {info['name']}\n"
                   f"📦 <b>پلن:</b> {info['vol']} | {info['time']}")
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, 
            caption=caption, parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"adm_to_{user_id}")]]))
        await update.message.reply_text("✅ فیش شما دریافت شد. پس از بررسی ادمین، سرویس ارسال می‌گردد.")
        user_data[user_id]['step'] = 'done'

def main():
    # شروع سرور وب در پس‌زمینه
    server_thread = Thread(target=run_web)
    server_thread.daemon = True # باعث می‌شود با بسته شدن برنامه اصلی، این هم بسته شود
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Dragon VPN Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
