import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- بخش زنده نگه داشتن برای Render (Flask) ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Dragon VPN Bot is Running!"

def run_web():
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- تنظیمات اصلی ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770
user_steps = {}

# --- منوها ---
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]

# --- توابع ربات ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه"
    await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id

    if text == 'خرید اشتراک':
        buttons = [['ارزان و به صرفه'], ['قوی']]
        await update.message.reply_text("لطفاً نوع سرویس را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

    elif text == 'ارزان و به صرفه':
        prices = [
            [InlineKeyboardButton("20 گیگ | نامحدود - 130ت", callback_data="p_20G_130")],
            [InlineKeyboardButton("30 گیگ | نامحدود - 160ت", callback_data="p_30G_160")],
            [InlineKeyboardButton("40 گیگ | نامحدود - 190ت", callback_data="p_40G_190")],
            [InlineKeyboardButton("50 گیگ | نامحدود - 250ت", callback_data="p_50G_250")],
            [InlineKeyboardButton("100 گیگ | نامحدود - 420ت", callback_data="p_100G_420")],
        ]
        await update.message.reply_text("لیست پلن‌های ارزان و به صرفه:", reply_markup=InlineKeyboardMarkup(prices))

    elif text == 'قوی':
        prices = [
            [InlineKeyboardButton("20 گیگ 1 ماهه - 150ت", callback_data="p_20GP_150")],
            [InlineKeyboardButton("50 گیگ 1 ماهه - 280ت", callback_data="p_50GP_280")],
            [InlineKeyboardButton("100 گیگ 1 ماهه - 550ت", callback_data="p_100GP_550")],
            [InlineKeyboardButton("200 گیگ 3 ماهه - 1,100ت", callback_data="p_200GP_1100")],
        ]
        await update.message.reply_text("لیست پلن‌های قوی (VIP):", reply_markup=InlineKeyboardMarkup(prices))

    elif text == 'پشتیبانی':
        await update.message.reply_text("برای پشتیبانی به آیدی زیر پیام دهید:\n@reunite_music")

    elif text == 'راهنمای اتصال':
        await update.message.reply_text("🎥 بخش راهنمای اتصال:\nدر حال حاضر ویدیویی تنظیم نشده است.")

    # مدیریت ارسال کانفیگ توسط ادمین
    elif user_id == ADMIN_ID and user_steps.get(user_id, "").startswith("wait_cfg_"):
        customer_id = user_steps[user_id].split("_")[-1]
        await context.bot.send_message(chat_id=customer_id, text=f"🚀 کانفیگ شما آماده شد:\n\n`{text}`", parse_mode='Markdown')
        await update.message.reply_text(f"✅ با موفقیت برای کاربر {customer_id} ارسال شد.")
        user_steps[user_id] = None

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("p_"):
        _, name, price = query.data.split("_")
        invoice = (
            f"📇 پیش فاکتور شما:\n"
            f"👤 نام کاربری: {query.from_user.username or 'نامشخص'}\n"
            f"🔐 نام سرویس: {name} | زمان و کاربر نامحدود\n"
            f"💶 قیمت: {price},000 تومان\n"
            f"💵 موجودی کیف پول شما : 0\n\n"
            f"💰 سفارش شما آماده پرداخت است"
        )
        await query.edit_message_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه ✅", callback_data=f"pay_{price}")]]))

    elif query.data.startswith("pay_"):
        price = query.data.split("_")[1]
        pay_msg = (
            f"`6277601368776066`\n\n"
            f"مبلغ: {price},000 تومان\n"
            f"بنام رضوانی\n\n"
            f"⭕ کاربر گرامی لطفاً مبلغ واریزی را بصورت دقیق واریز کنید\n"
            f"⭕ از ارسال فیش جعلی خودداری فرمایید"
        )
        await query.edit_message_text(pay_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش", callback_data="ask_photo")]]), parse_mode='Markdown')

    elif query.data == "ask_photo":
        user_steps[query.from_user.id] = "wait_photo"
        await query.message.reply_text("لطفاً عکس فیش واریزی را ارسال فرمایید:")

    elif query.data.startswith("adm_send_"):
        target_id = query.data.split("_")[-1]
        user_steps[ADMIN_ID] = f"wait_cfg_{target_id}"
        await query.message.reply_text(f"لطفاً کانفیگ را برای کاربر {target_id} بفرستید (متن را اینجا پیام کنید):")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_steps.get(user_id) == "wait_photo":
        # ارسال برای شما (ادمین)
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"🔔 فیش جدید رسید!\n👤 کاربر: `{user_id}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال کانفیگ", callback_data=f"adm_send_{user_id}")]])
        )
        await update.message.reply_text("🚀 رسید شما ارسال و پس از بررسی اطلاعات سرویس برای شما ارسال خواهد شد")
        user_steps[user_id] = None

# --- اجرای برنامه ---
def main():
    # شروع ترد Flask برای زنده نگه داشتن در Render
    Thread(target=run_web).start()

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Dragon VPN is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
      
