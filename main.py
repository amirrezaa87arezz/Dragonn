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
user_data, admin_state = {}, {}

# --- منوها ---
MAIN_MENU = [['خرید اشتراک'], ['پشتیبانی', 'راهنمای اتصال']]
BACK_MENU = [['بازگشت به منوی اصلی']]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = "خوش اومدید به ربات Dragon vpn\nپرسرعت ارزان و به صرفه"
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, user_id = update.message.text, update.message.from_user.id

    # 1. پنل مدیریت: ارسال کانفیگ برای مشتری
    if user_id == ADMIN_ID and admin_state.get('step') == 'wait_cfg':
        target_id = admin_state.get('target')
        info = user_data.get(target_id, {})
        final_msg = (
            f"<b>نام کاربری سرویس :</b> {info.get('name', 'نامشخص')}\n"
            f"<b>⏳ مدت زمان:</b> {info.get('time', 'نامشخص')}\n"
            f"<b>🗜 حجم سرویس:</b> {info.get('vol', 'نامشخص')}\n\n"
            f"<b>لینک اتصال:</b>\n<code>{text}</code>\n\n"
            f"🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر دریافت کنید\n\n"
            f"🟢 اگر لینک ساب اضافه نشد، از @URLExtractor_Bot کمک بگیرید."
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("آموزش اتصال", url="https://t.me/help_dragon")]])
        try:
            await context.bot.send_message(chat_id=target_id, text=final_msg, reply_markup=kb, parse_mode='HTML')
            await update.message.reply_text(f"✅ با موفقیت برای کاربر {target_id} ارسال شد.")
        except Exception as e: await update.message.reply_text(f"❌ خطا: {str(e)}")
        admin_state.clear(); return

    # 2. مدیریت منوهای اصلی
    if text == 'بازگشت به منوی اصلی':
        user_data[user_id] = {}; await start(update, context)

    elif text == 'خرید اشتراک':
        await update.message.reply_text("لطفاً نوع سرویس را انتخاب کنید:", 
            reply_markup=ReplyKeyboardMarkup([['ارزان و به صرفه'], ['قوی'], ['بازگشت به منوی اصلی']], resize_keyboard=True))

    elif text == 'ارزان و به صرفه':
        prices = [
            [InlineKeyboardButton("20 گیگ | نامحدود - 130,000", callback_data="p_20G_نامحدود_130")],
            [InlineKeyboardButton("30 گیگ | نامحدود - 160,000", callback_data="p_30G_نامحدود_160")],
            [InlineKeyboardButton("40 گیگ | نامحدود - 190,000", callback_data="p_40G_نامحدود_190")],
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
        await update.message.reply_text("پشتیبانی: @reunite_music", reply_markup=ReplyKeyboardMarkup(BACK_MENU, resize_keyboard=True))

    elif text == 'راهنمای اتصال':
        await update.message.reply_text("آموزشات در چنل زیر:\nhttps://t.me/help_dragon")

    # 3. دریافت نام کاربری انتخابی
    elif user_id in user_data and user_data[user_id].get('step') == 'get_name':
        user_data[user_id].update({'name': text, 'step': 'wait_pay'})
        info = user_data[user_id]
        invoice = (
            f"📇 <b>پیش فاکتور شما:</b>\n"
            f"👤 <b>نام انتخابی:</b> {text}\n"
            f"🔐 <b>سرویس:</b> {info['vol']} | {info['time']}\n"
            f"💶 <b>قیمت:</b> {info['price']},000 تومان\n\n"
            f"💰 سفارش شما آماده پرداخت است"
        )
        await update.message.reply_text(invoice, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ادامه و دریافت شماره کارت ✅", callback_data="show_card")]), [InlineKeyboardButton("انصراف و بازگشت", callback_data="cancel")]]), parse_mode='HTML')

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
        bank = (
            f"💳 <b>شماره کارت:</b>\n<code>6277601368776066</code>\n"
            f"💰 <b>مبلغ:</b> {info['price']},000 تومان\n"
            f"👤 <b>بنام رضوانی</b>\n\n"
            f"⭕ کاربر گرامی لطفاً مبلغ واریزی را بصورت دقیق واریز کنید\n"
            f"⭕ از ارسال فیش جعلی خودداری فرمایید"
        )
        await query.message.reply_text(bank, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ارسال فیش واریزی", callback_data="
