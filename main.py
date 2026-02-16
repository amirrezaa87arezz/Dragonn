import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime
import traceback

# --- تنظیمات لاگینگ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وب سرور ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "TAKNET VPN Bot is running!", 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- توکن و آیدی ادمین ---
TOKEN = '8578186075:AAFevjClPyq2hAcJxJpwhrxc0DxxBMGN8RY'
ADMIN_ID = 5993860770

# --- مسیر دیتابیس ---
DB_FILE = 'data.json'

logger.info(f"Database file path: {DB_FILE}")

# --- پلن‌های پیش‌فرض برای هر دسته ---
DEFAULT_PLANS = {
    "🚀 قوی": [
        {"id": 1, "name": "⚡️ پلن قوی 20GB", "price": 80, "volume": "20GB", "days": 30, "users": 1},
        {"id": 2, "name": "🔥 پلن قوی 50GB", "price": 140, "volume": "50GB", "days": 30, "users": 1}
    ],
    "💎 ارزان": [
        {"id": 3, "name": "💎 پلن اقتصادی 10GB", "price": 45, "volume": "10GB", "days": 30, "users": 1},
        {"id": 4, "name": "💎 پلن اقتصادی 20GB", "price": 75, "volume": "20GB", "days": 30, "users": 1}
    ],
    "🎯 به صرفه": [
        {"id": 5, "name": "🎯 پلن ویژه 30GB", "price": 110, "volume": "30GB", "days": 30, "users": 1},
        {"id": 6, "name": "🎯 پلن ویژه 60GB", "price": 190, "volume": "60GB", "days": 30, "users": 1}
    ],
    "👥 چند کاربره": [
        {"id": 7, "name": "👥 2 کاربره 40GB", "price": 150, "volume": "40GB", "days": 30, "users": 2},
        {"id": 8, "name": "👥 3 کاربره 60GB", "price": 210, "volume": "60GB", "days": 30, "users": 3}
    ]
}

def load_db():
    """بارگذاری دیتابیس"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info("Database loaded successfully")
                return data
    except Exception as e:
        logger.error(f"Error loading database: {e}")
    
    # دیتابیس پیش‌فرض
    logger.info("Creating default database")
    return {
        "users": {},
        "brand": "TAKNET VPN",
        "card": {
            "number": "6277601368776066",
            "name": "رضوانی"
        },
        "support_id": "@Support_Admin",
        "guide_channel": "@Guide_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "texts": {
            "welcome": "🔰 به {brand} خوش آمدید\n\nهمه راه‌ها بسته نیست! 😊\nبا سرویس‌های پرسرعت ما، فیلترها رو کنار بزن!\n\n✅ مخصوص تلگرام، اینستاگرام، یوتیوب و...\n✅ نصب آسان روی همه دستگاه‌ها\n✅ پشتیبانی 24 ساعته",
            "support": "🆘 <b>پشتیبانی {brand}</b>\n\nبرای ارتباط با پشتیبانی به آیدی زیر پیام بدید:\n{support_id}",
            "guide": "📚 <b>آموزش اتصال</b>\n\nبرای مشاهده آموزش تصویری و متنی به کانال زیر مراجعه کنید:\n{guide_channel}",
            "test": "🎁 درخواست تست رایگان شما ثبت شد.\n\nپس از بررسی ادمین، اکانت تست 3 ساعته برای شما ارسال می‌شود."
        }
    }

def save_db(data):
    """ذخیره دیتابیس"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("Database saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        return False

# بارگذاری دیتابیس
db = load_db()
user_data = {}

# --- منوهای اصلی ---
def get_main_menu(uid):
    """منوی اصلی کاربر"""
    kb = [
        ['💰 خرید اشتراک', '🎁 تست رایگان'],
        ['📂 سرویس‌های من', '⏳ تمدید سرویس'],
        ['👤 پشتیبانی', '📚 آموزش استفاده'],
        ['🤝 معرفی به دوستان']
    ]
    if str(uid) == str(ADMIN_ID):
        kb.append(['⚙️ مدیریت ربات'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_back_keyboard():
    """کیبورد بازگشت"""
    return ReplyKeyboardMarkup([['🔙 بازگشت به منوی اصلی']], resize_keyboard=True)

def get_admin_menu():
    """منوی مدیریت"""
    kb = [
        ['➕ افزودن پلن', '➖ حذف پلن'],
        ['💳 ویرایش کارت', '📝 ویرایش متن‌ها'],
        ['👤 ویرایش پشتیبان', '📢 ویرایش کانال آموزش'],
        ['🏷 ویرایش برند', '📊 آمار ربات'],
        ['📨 ارسال همگانی', '🔙 بازگشت به منوی اصلی']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- شروع ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start"""
    try:
        uid = str(update.effective_user.id)
        username = update.effective_user.username or "ندارد"
        first_name = update.effective_user.first_name or "کاربر"
        
        # ثبت کاربر جدید
        if uid not in db["users"]:
            db["users"][uid] = {
                "purchases": [],
                "tests": [],
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username": username,
                "first_name": first_name
            }
            save_db(db)
            logger.info(f"New user joined: {uid} - {first_name}")
        
        user_data[uid] = {}
        
        welcome_text = db["texts"]["welcome"].format(brand=db["brand"])
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(uid),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت پیام‌ها ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر پیام‌های متنی"""
    try:
        if not update.message or not update.message.text:
            return
        
        text = update.message.text
        uid = str(update.effective_user.id)
        first_name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')

        # بازگشت به منوی اصلی
        if text == '🔙 بازگشت به منوی اصلی':
            user_data[uid] = {}
            await start(update, context)
            return

        # --- تست رایگان ---
        if text == '🎁 تست رایگان':
            today = datetime.now().strftime("%Y-%m-%d")
            
            # بررسی درخواست تکراری
            if uid in db["users"] and db["users"][uid].get("last_test") == today:
                await update.message.reply_text("❌ شما امروز قبلاً درخواست تست داده‌اید. لطفاً فردا مجدداً تلاش کنید.")
                return
            
            # ثبت درخواست تست
            if uid not in db["users"]:
                db["users"][uid] = {"purchases": [], "tests": []}
            
            db["users"][uid]["last_test"] = today
            db["users"][uid]["tests"].append(f"تست {today}")
            save_db(db)
            
            await update.message.reply_text(db["texts"]["test"])
            
            # اطلاع به ادمین با دکمه ارسال تست
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "📤 ارسال اکانت تست", 
                    callback_data=f"send_test_{uid}_{first_name}"
                )
            ]])
            
            admin_msg = (
                f"🎁 <b>درخواست تست رایگان جدید</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 نام: {first_name}\n"
                f"🆔 آیدی: <code>{uid}</code>\n"
                f"👤 یوزرنیم: @{update.effective_user.username}\n"
                f"📅 تاریخ: {today}\n"
                f"━━━━━━━━━━━━━━━"
            )
            
            await context.bot.send_message(
                ADMIN_ID,
                admin_msg,
                parse_mode='HTML',
                reply_markup=btn
            )
            return

        # --- سرویس‌های من ---
        if text == '📂 سرویس‌های من':
            purchases = db["users"].get(uid, {}).get("purchases", [])
            tests = db["users"].get(uid, {}).get("tests", [])
            
            msg = "📂 <b>سرویس‌های شما</b>\n━━━━━━━━━━━━━━━\n"
            
            if purchases:
                msg += "✅ <b>سرویس‌های خریداری شده:</b>\n"
                for i, p in enumerate(purchases[-10:], 1):
                    msg += f"{i}. {p}\n"
            else:
                msg += "❌ سرویس خریدی ندارید\n"
            
            if tests:
                msg += "\n🎁 <b>تست‌های دریافتی:</b>\n"
                for i, t in enumerate(tests[-5:], 1):
                    msg += f"{i}. {t}\n"
            
            await update.message.reply_text(msg, parse_mode='HTML')
            return

        # --- تمدید سرویس ---
        if text == '⏳ تمدید سرویس':
            purchases = db["users"].get(uid, {}).get("purchases", [])
            if not purchases:
                await update.message.reply_text("❌ شما سرویسی برای تمدید ندارید.")
                return
            
            keyboard = []
            for i, purchase in enumerate(purchases[-5:]):
                # استخراج اطلاعات از سرویس
                parts = purchase.split('|')
                if len(parts) >= 2:
                    service_name = parts[0].strip()
                    volume = parts[1].strip() if len(parts) > 1 else "نامشخص"
                    btn_text = f"🔄 {service_name} - {volume}"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"renew_{i}")])
            
            if keyboard:
                await update.message.reply_text(
                    "🔁 لطفاً سرویس مورد نظر برای تمدید را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return

        # --- پشتیبانی و آموزش ---
        if text == '👤 پشتیبانی':
            support_text = db["texts"]["support"].format(
                brand=db["brand"],
                support_id=db["support_id"]
            )
            await update.message.reply_text(support_text, parse_mode='HTML')
            return

        if text == '📚 آموزش استفاده':
            guide_text = db["texts"]["guide"].format(
                brand=db["brand"],
                guide_channel=db["guide_channel"]
            )
            await update.message.reply_text(guide_text, parse_mode='HTML')
            return

        # --- معرفی به دوستان ---
        if text == '🤝 معرفی به دوستان':
            bot_username = (await context.bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start={uid}"
            msg = (
                "🤝 <b>برنامه معرفی به دوستان</b>\n\n"
                "از لینک زیر برای دعوت دوستانت استفاده کن:\n"
                f"<code>{referral_link}</code>\n\n"
                "✨ مزایای معرفی:\n"
                "• به ازای هر دوست، 1 روز به سرویس شما اضافه می‌شود\n"
                "• پس از خرید دوستتان، به شما اعلام می‌شود"
            )
            await update.message.reply_text(msg, parse_mode='HTML')
            return

        # --- خرید اشتراک ---
        if text == '💰 خرید اشتراک':
            # نمایش دسته‌بندی‌ها
            categories = list(db["categories"].keys())
            keyboard = []
            for cat in categories:
                keyboard.append([cat])
            keyboard.append(['🔙 بازگشت به منوی اصلی'])
            
            await update.message.reply_text(
                "📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

        # --- نمایش پلن‌های یک دسته ---
        if text in db["categories"] and not step:
            plans = db["categories"][text]
            if not plans:
                await update.message.reply_text("❌ این دسته‌بندی پلنی ندارد.")
                return
            
            keyboard = []
            for plan in plans:
                users_text = f"👥 {plan['users']} کاربره - " if plan['users'] > 1 else ""
                btn_text = f"{plan['name']} - {users_text}{plan['volume']} - {plan['price']:,} تومان"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{plan['id']}")])
            
            await update.message.reply_text(
                f"📦 <b>{text}</b>\nلطفاً پلن مورد نظر را انتخاب کنید:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- بخش مدیریت ---
        if str(uid) == str(ADMIN_ID):
            
            # منوی مدیریت
            if text == '⚙️ مدیریت ربات':
                await update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu())
                return

            # ویرایش متن‌ها
            if text == '📝 ویرایش متن‌ها':
                keyboard = [
                    ['ویرایش متن خوش‌آمدگویی', 'ویرایش متن پشتیبانی'],
                    ['ویرایش متن آموزش', 'ویرایش متن تست'],
                    ['🔙 بازگشت به منوی اصلی']
                ]
                await update.message.reply_text(
                    "📝 کدام متن را می‌خواهید ویرایش کنید؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # ویرایش پشتیبان
            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'edit_support'}
                await update.message.reply_text(
                    "👤 آیدی جدید پشتیبانی را وارد کنید (مثال: @Support_Admin):",
                    reply_markup=get_back_keyboard()
                )
                return

            # ویرایش کانال آموزش
            if text == '📢 ویرایش کانال آموزش':
                user_data[uid] = {'step': 'edit_guide'}
                await update.message.reply_text(
                    "📢 آیدی جدید کانال آموزش را وارد کنید (مثال: @Guide_Channel):",
                    reply_markup=get_back_keyboard()
                )
                return

            # ویرایش کارت
            if text == '💳 ویرایش کارت':
                keyboard = [
                    ['ویرایش شماره کارت', 'ویرایش نام صاحب کارت'],
                    ['🔙 بازگشت به منوی اصلی']
                ]
                await update.message.reply_text(
                    "💳 چه اطلاعاتی را ویرایش می‌کنید؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # ویرایش برند
            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'edit_brand'}
                await update.message.reply_text(
                    "🏷 نام جدید برند را وارد کنید:",
                    reply_markup=get_back_keyboard()
                )
                return

            # آمار ربات
            if text == '📊 آمار ربات':
                total_users = len(db["users"])
                total_purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                total_tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                today = datetime.now().strftime("%Y-%m-%d")
                today_users = sum(1 for u in db["users"].values() if u.get("joined_date", "").startswith(today))
                
                # آمار دسته‌بندی‌ها
                categories_stats = ""
                for cat, plans in db["categories"].items():
                    categories_stats += f"• {cat}: {len(plans)} پلن\n"
                
                stats = (
                    f"📊 <b>آمار ربات {db['brand']}</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"👥 کل کاربران: {total_users}\n"
                    f"🆕 کاربران جدید امروز: {today_users}\n"
                    f"💰 تعداد خریدها: {total_purchases}\n"
                    f"🎁 تعداد تست‌ها: {total_tests}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📦 <b>دسته‌بندی‌ها:</b>\n{categories_stats}"
                )
                await update.message.reply_text(stats, parse_mode='HTML')
                return

            # ارسال همگانی
            if text == '📨 ارسال همگانی':
                user_data[uid] = {'step': 'broadcast'}
                await update.message.reply_text(
                    "📨 پیام مورد نظر برای ارسال همگانی را ارسال کنید:",
                    reply_markup=get_back_keyboard()
                )
                return

            # افزودن پلن - مرحله انتخاب دسته
            if text == '➕ افزودن پلن':
                categories = list(db["categories"].keys())
                keyboard = []
                for cat in categories:
                    keyboard.append([cat])
                keyboard.append(['🔙 بازگشت به منوی اصلی'])
                
                user_data[uid] = {'step': 'add_plan_category'}
                await update.message.reply_text(
                    "📂 لطفاً دسته‌بندی مورد نظر برای افزودن پلن را انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # حذف پلن - نمایش لیست پلن‌ها
            if text == '➖ حذف پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for plan in plans:
                        btn_text = f"❌ {cat} - {plan['name']}"
                        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"delplan_{plan['id']}")])
                
                if keyboard:
                    await update.message.reply_text(
                        "🗑 پلن مورد نظر برای حذف را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await update.message.reply_text("❌ هیچ پلنی برای حذف وجود ندارد.")
                return

            # مراحل ویرایش
            if step == 'edit_support':
                db["support_id"] = text
                save_db(db)
                user_data[uid] = {}
                await update.message.reply_text("✅ آیدی پشتیبانی ویرایش شد.", reply_markup=get_admin_menu())
                return

            if step == 'edit_guide':
                db["guide_channel"] = text
                save_db(db)
                user_data[uid] = {}
                await update.message.reply_text("✅ کانال آموزش ویرایش شد.", reply_markup=get_admin_menu())
                return

            if step == 'edit_brand':
                db["brand"] = text
                save_db(db)
                user_data[uid] = {}
                await update.message.reply_text("✅ نام برند ویرایش شد.", reply_markup=get_admin_menu())
                return

            if step == 'edit_card_number':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    await update.message.reply_text("✅ شماره کارت ویرایش شد.", reply_markup=get_admin_menu())
                else:
                    await update.message.reply_text("❌ شماره کارت نامعتبر!")
                user_data[uid] = {}
                return

            if step == 'edit_card_name':
                db["card"]["name"] = text
                save_db(db)
                user_data[uid] = {}
                await update.message.reply_text("✅ نام صاحب کارت ویرایش شد.", reply_markup=get_admin_menu())
                return

            if step == 'broadcast':
                success = 0
                failed = 0
                for user_id in db["users"].keys():
                    try:
                        await context.bot.send_message(int(user_id), text)
                        success += 1
                    except:
                        failed += 1
                
                await update.message.reply_text(
                    f"✅ ارسال همگانی انجام شد.\n✓ موفق: {success}\n✗ ناموفق: {failed}",
                    reply_markup=get_admin_menu()
                )
                user_data[uid] = {}
                return

            # مراحل افزودن پلن
            if step == 'add_plan_category' and text in db["categories"]:
                user_data[uid]['category'] = text
                user_data[uid]['step'] = 'add_plan_name'
                await update.message.reply_text(
                    "📝 نام پلن را وارد کنید (مثال: ⚡️ پلن ویژه 50GB):",
                    reply_markup=get_back_keyboard()
                )
                return

            if step == 'add_plan_name':
                user_data[uid]['plan_name'] = text
                user_data[uid]['step'] = 'add_plan_volume'
                await update.message.reply_text("📦 حجم پلن را وارد کنید (مثال: 50GB):")
                return

            if step == 'add_plan_volume':
                user_data[uid]['volume'] = text
                user_data[uid]['step'] = 'add_plan_users'
                await update.message.reply_text("👥 تعداد کاربران را وارد کنید (عدد):")
                return

            if step == 'add_plan_users':
                try:
                    users = int(text)
                    user_data[uid]['users'] = users
                    user_data[uid]['step'] = 'add_plan_days'
                    await update.message.reply_text("⏳ مدت اعتبار را به روز وارد کنید (عدد):")
                except ValueError:
                    await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'add_plan_days':
                try:
                    days = int(text)
                    user_data[uid]['days'] = days
                    user_data[uid]['step'] = 'add_plan_price'
                    await update.message.reply_text("💰 قیمت را به تومان وارد کنید (عدد):")
                except ValueError:
                    await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'add_plan_price':
                try:
                    price = int(text)
                    
                    # پیدا کردن بزرگترین id
                    max_id = 0
                    for plans in db["categories"].values():
                        for p in plans:
                            if p["id"] > max_id:
                                max_id = p["id"]
                    
                    new_plan = {
                        "id": max_id + 1,
                        "name": user_data[uid]['plan_name'],
                        "price": price,
                        "volume": user_data[uid]['volume'],
                        "days": user_data[uid]['days'],
                        "users": user_data[uid]['users']
                    }
                    
                    category = user_data[uid]['category']
                    db["categories"][category].append(new_plan)
                    save_db(db)
                    
                    await update.message.reply_text(
                        f"✅ پلن با موفقیت به دسته {category} اضافه شد!",
                        reply_markup=get_admin_menu()
                    )
                    user_data[uid] = {}
                    
                except Exception as e:
                    await update.message.reply_text(f"❌ خطا: {e}")
                return

            # دریافت کانفیگ برای ارسال
            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                vol = user_data[uid].get('vol', 'نامحدود')
                
                config_msg = (
                    f"🎉 <b>سرویس شما آماده است!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 <b>نام کاربری:</b> {name}\n"
                    f"📦 <b>حجم:</b> {vol}\n"
                    f"⏳ <b>مدت زمان:</b> نامحدود\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔗 <b>لینک اتصال:</b>\n"
                    f"<code>{update.message.text}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📱 اگر لینک باز نشد، از ربات @URLExtractor_Bot استفاده کنید."
                )
                
                channel = db['guide_channel'].replace('@', '')
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📚 آموزش اتصال", url=f"https://t.me/{channel}")
                ]])
                
                try:
                    await context.bot.send_message(int(target), config_msg, parse_mode='HTML', reply_markup=keyboard)
                    
                    # ثبت در سرویس‌های من
                    service_record = f"🚀 {name} | {vol} | {datetime.now().strftime('%Y-%m-%d')}"
                    if str(target) not in db["users"]:
                        db["users"][str(target)] = {"purchases": []}
                    
                    if "purchases" not in db["users"][str(target)]:
                        db["users"][str(target)]["purchases"] = []
                    
                    db["users"][str(target)]["purchases"].append(service_record)
                    save_db(db)
                    
                    await update.message.reply_text("✅ کانفیگ با موفقیت ارسال شد.", reply_markup=get_main_menu(uid))
                except Exception as e:
                    await update.message.reply_text(f"❌ خطا در ارسال: {str(e)}")
                
                user_data[uid] = {}
                return

        # --- دریافت نام برای خرید جدید ---
        if step == 'wait_name':
            user_data[uid]['account_name'] = text
            plan = user_data[uid]['plan']
            
            users_text = f"👥 {plan['users']} کاربره" if plan['users'] > 1 else "👤 تک کاربره"
            
            invoice = (
                f"💎 <b>پیش‌فاکتور خرید</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>نام اکانت:</b> {text}\n"
                f"📦 <b>پلن:</b> {plan['name']}\n"
                f"📊 <b>حجم:</b> {plan['volume']}\n"
                f"{users_text}\n"
                f"⏳ <b>مدت:</b> {plan['days']} روز\n"
                f"💰 <b>مبلغ:</b> {plan['price']:,} تومان\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تایید و دریافت کارت", callback_data="show_card")
            ]])
            
            await update.message.reply_text(invoice, parse_mode='HTML', reply_markup=keyboard)
            return

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت کالبک‌ها ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر کالبک‌های دکمه‌های شیشه‌ای"""
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        await query.answer()

        # خرید پلن
        if query.data.startswith("buy_"):
            plan_id = int(query.data.split("_")[1])
            
            # پیدا کردن پلن در همه دسته‌ها
            plan = None
            plan_category = None
            for cat, plans in db["categories"].items():
                for p in plans:
                    if p["id"] == plan_id:
                        plan = p
                        plan_category = cat
                        break
                if plan:
                    break
            
            if plan:
                user_data[uid] = {'step': 'wait_name', 'plan': plan, 'category': plan_category}
                await query.message.reply_text(
                    "📝 لطفاً نام دلخواه برای اکانت خود وارد کنید:",
                    reply_markup=get_back_keyboard()
                )
            else:
                await query.message.reply_text("❌ پلن مورد نظر یافت نشد.")

        # نمایش کارت
        elif query.data == "show_card":
            if uid not in user_data or 'plan' not in user_data[uid]:
                await query.message.reply_text("❌ خطا در اطلاعات خرید. دوباره تلاش کنید.")
                return
            
            plan = user_data[uid]['plan']
            price = plan['price'] * 1000  # تبدیل به تومان
            
            card_msg = (
                f"💳 <b>اطلاعات واریز</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>مبلغ قابل پرداخت:</b> {price:,} تومان\n\n"
                f"📍 <b>شماره کارت (کپی کنید):</b>\n"
                f"<code>{db['card']['number']}</code>\n\n"
                f"👤 <b>بنام:</b> {db['card']['name']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 پس از واریز، عکس فیش را ارسال کنید."
            )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")
            ]])
            
            await query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=keyboard)

        # ارسال فیش
        elif query.data == "send_receipt":
            if 'plan' in user_data[uid]:
                user_data[uid]['step'] = 'wait_photo'
                await query.message.reply_text(
                    "📸 لطفاً عکس فیش واریزی را ارسال کنید:",
                    reply_markup=get_back_keyboard()
                )
            else:
                await query.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")

        # تمدید سرویس
        elif query.data.startswith("renew_"):
            index = int(query.data.split("_")[1])
            purchases = db["users"][uid].get("purchases", [])
            
            if index < len(purchases):
                service = purchases[index]
                
                # پیدا کردن پلن مشابه
                similar_plan = None
                for cat, plans in db["categories"].items():
                    for plan in plans:
                        if plan['volume'] in service or plan['name'].split()[-1] in service:
                            similar_plan = plan
                            break
                    if similar_plan:
                        break
                
                if similar_plan:
                    user_data[uid] = {'step': 'wait_name', 'plan': similar_plan, 'is_renew': True}
                    
                    renew_msg = (
                        f"🔄 <b>تمدید سرویس</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 <b>پلن:</b> {similar_plan['name']}\n"
                        f"💰 <b>مبلغ تمدید:</b> {similar_plan['price']:,} تومان\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📝 لطفاً نام اکانت را وارد کنید:"
                    )
                    
                    await query.message.reply_text(renew_msg, parse_mode='HTML')
                else:
                    await query.message.reply_text("❌ پلن مشابه برای تمدید یافت نشد. لطفاً از خرید جدید استفاده کنید.")
            else:
                await query.message.reply_text("❌ سرویس مورد نظر یافت نشد.")

        # حذف پلن توسط ادمین
        elif query.data.startswith("delplan_"):
            if str(uid) == str(ADMIN_ID):
                plan_id = int(query.data.split("_")[1])
                
                # پیدا کردن و حذف پلن
                deleted = False
                for cat, plans in db["categories"].items():
                    for i, plan in enumerate(plans):
                        if plan["id"] == plan_id:
                            del db["categories"][cat][i]
                            deleted = True
                            break
                    if deleted:
                        break
                
                if deleted:
                    save_db(db)
                    await query.message.reply_text("✅ پلن با موفقیت حذف شد.", reply_markup=get_admin_menu())
                else:
                    await query.message.reply_text("❌ پلن یافت نشد.")

        # ارسال تست توسط ادمین
        elif query.data.startswith("send_test_"):
            if str(uid) == str(ADMIN_ID):
                parts = query.data.split("_")
                if len(parts) >= 4:
                    target = parts[2]
                    name = parts[3]
                    
                    user_data[uid] = {
                        'step': 'send_config',
                        'target': target,
                        'name': f"تست {name}",
                        'vol': "3 ساعت"
                    }
                    
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"📨 لطفاً کانفیگ تست برای کاربر {name} را ارسال کنید:"
                    )
                    
                    await query.message.edit_reply_markup(reply_markup=None)  # حذف دکمه

        # ارسال کانفیگ خرید توسط ادمین
        elif query.data.startswith("send_config_"):
            if str(uid) == str(ADMIN_ID):
                parts = query.data.split("_", 2)
                if len(parts) >= 3:
                    target = parts[2]
                    
                    # پیدا کردن اطلاعات از پیام
                    if query.message.caption:
                        lines = query.message.caption.split('\n')
                        name = "کاربر"
                        vol = "نامحدود"
                        
                        for line in lines:
                            if "نام اکانت" in line:
                                name = line.split(':')[-1].strip()
                            elif "حجم" in line:
                                vol = line.split(':')[-1].strip()
                    
                    user_data[uid] = {
                        'step': 'send_config',
                        'target': target,
                        'name': name,
                        'vol': vol
                    }
                    
                    await context.bot.send_message(
                        ADMIN_ID,
                        f"📨 لطفاً کانفیگ سرویس {name} را ارسال کنید:"
                    )
                    
                    await query.message.edit_reply_markup(reply_markup=None)

    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        logger.error(traceback.format_exc())
        await query.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت دریافت عکس (فیش واریزی) ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دریافت عکس"""
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get('step') == 'wait_photo':
            if 'plan' not in user_data[uid] or 'account_name' not in user_data[uid]:
                await update.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")
                return
            
            account_name = user_data[uid]['account_name']
            plan = user_data[uid]['plan']
            category = user_data[uid].get('category', 'نامشخص')
            
            # ارسال به ادمین
            caption = (
                f"💰 <b>فیش واریزی جدید</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>کاربر:</b> {update.effective_user.first_name}\n"
                f"🆔 <b>آیدی:</b> <code>{uid}</code>\n"
                f"👤 <b>یوزرنیم:</b> @{update.effective_user.username}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📂 <b>دسته:</b> {category}\n"
                f"📦 <b>پلن:</b> {plan['name']}\n"
                f"📊 <b>حجم:</b> {plan['volume']}\n"
                f"👥 <b>تعداد کاربران:</b> {plan['users']}\n"
                f"💰 <b>مبلغ:</b> {plan['price']:,} تومان\n"
                f"👤 <b>نام اکانت:</b> {account_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            btn = [[InlineKeyboardButton(
                "✅ تایید و ارسال کانفیگ",
                callback_data=f"send_config_{uid}"
            )]]
            
            await context.bot.send_photo(
                ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            await update.message.reply_text(
                "✅ فیش شما با موفقیت ارسال شد.\n"
                "به زودی پس از تایید، سرویس برای شما ارسال می‌شود.",
                reply_markup=get_main_menu(uid)
            )
            
            # پاک کردن اطلاعات موقت
            if uid in user_data:
                del user_data[uid]

    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        await update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- اجرای اصلی ---
async def main():
    """تابع اصلی"""
    try:
        logger.info("Starting bot...")
        
        # اجرای وب سرور در ترد جداگانه
        web_thread = Thread(target=run_web, daemon=True)
        web_thread.start()
        logger.info("Web server started")
        
        # ساخت ربات
        app = Application.builder().token(TOKEN).build()
        
        # اضافه کردن هندلرها
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(CallbackQueryHandler(handle_callback))
        
        logger.info("Bot started successfully!")
        
        # شروع ربات
        await app.run_polling()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())