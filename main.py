import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
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
                
                # اضافه کردن فیلدهای جدید اگر وجود نداشتند
                if "force_join" not in data:
                    data["force_join"] = {"enabled": False, "channel": ""}
                if "channel_link" not in data:
                    data["channel_link"] = ""
                
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
        "force_join": {"enabled": False, "channel": ""},
        "channel_link": "",
        "texts": {
            "welcome": "🔰 به {brand} خوش آمدید\n\nهمه راه‌ها بسته نیست! 😊\nبا سرویس‌های پرسرعت ما، فیلترها رو کنار بزن!\n\n✅ مخصوص تلگرام، اینستاگرام، یوتیوب و...\n✅ نصب آسان روی همه دستگاه‌ها\n✅ پشتیبانی 24 ساعته",
            "support": "🆘 <b>پشتیبانی {brand}</b>\n\nبرای ارتباط با پشتیبانی به آیدی زیر پیام بدید:\n{support_id}",
            "guide": "📚 <b>آموزش اتصال</b>\n\nبرای مشاهده آموزش تصویری و متنی به کانال زیر مراجعه کنید:\n{guide_channel}",
            "test": "🎁 درخواست تست رایگان شما ثبت شد.\n\nپس از بررسی ادمین، اکانت تست 3 ساعته برای شما ارسال می‌شود.",
            "force_join": "🔒 <b>عضویت اجباری</b>\n\nبرای استفاده از ربات باید در کانال زیر عضو شوید:\n{channel_link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید."
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
        ['🔒 عضویت اجباری', '🏷 ویرایش برند'],
        ['📊 آمار ربات', '📨 ارسال همگانی'],
        ['🔙 بازگشت به منوی اصلی']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- بررسی عضویت اجباری ---
def check_force_join(user_id, context):
    """بررسی اینکه کاربر در کانال عضو هست یا نه"""
    if not db["force_join"]["enabled"] or not db["force_join"]["channel"]:
        return True
    
    try:
        channel = db["force_join"]["channel"].replace('@', '').replace('https://t.me/', '')
        member = context.bot.get_chat_member(chat_id=f"@{channel}", user_id=int(user_id))
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- شروع ربات ---
def start(update, context):
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
                "test_count": 0,
                "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username": username,
                "first_name": first_name
            }
            save_db(db)
            logger.info(f"New user joined: {uid} - {first_name}")
        
        user_data[uid] = {}
        
        # بررسی عضویت اجباری
        if db["force_join"]["enabled"] and db["force_join"]["channel"]:
            if not check_force_join(uid, context):
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")
                ]])
                
                force_text = db["texts"]["force_join"].format(channel_link=db["channel_link"])
                update.message.reply_text(force_text, parse_mode='HTML', reply_markup=keyboard)
                return
        
        welcome_text = db["texts"]["welcome"].format(brand=db["brand"])
        update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu(uid),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in start: {e}")
        update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت پیام‌ها ---
def handle_message(update, context):
    """هندلر پیام‌های متنی"""
    try:
        if not update.message or not update.message.text:
            return
        
        text = update.message.text
        uid = str(update.effective_user.id)
        first_name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')

        # بررسی عضویت اجباری (برای همه پیام‌ها به جز start)
        if db["force_join"]["enabled"] and db["force_join"]["channel"]:
            if not check_force_join(uid, context) and text != '/start':
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="check_join")
                ]])
                
                force_text = db["texts"]["force_join"].format(channel_link=db["channel_link"])
                update.message.reply_text(force_text, parse_mode='HTML', reply_markup=keyboard)
                return

        # بازگشت به منوی اصلی
        if text == '🔙 بازگشت به منوی اصلی':
            user_data[uid] = {}
            start(update, context)
            return

        # --- تست رایگان ---
        if text == '🎁 تست رایگان':
            # بررسی تعداد تست‌های قبلی
            test_count = db["users"][uid].get("test_count", 0)
            
            if test_count >= 1:
                await_msg = "❌ شما قبلاً یک بار اکانت تست دریافت کرده‌اید و امکان دریافت تست مجدد وجود ندارد."
                update.message.reply_text(await_msg)
                return
            
            # ثبت درخواست تست
            db["users"][uid]["test_count"] = test_count + 1
            db["users"][uid]["tests"].append(f"تست {datetime.now().strftime('%Y-%m-%d')}")
            save_db(db)
            
            update.message.reply_text(db["texts"]["test"])
            
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
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"━━━━━━━━━━━━━━━"
            )
            
            context.bot.send_message(
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
            
            update.message.reply_text(msg, parse_mode='HTML')
            return

        # --- تمدید سرویس ---
        if text == '⏳ تمدید سرویس':
            purchases = db["users"].get(uid, {}).get("purchases", [])
            if not purchases:
                update.message.reply_text("❌ شما سرویسی برای تمدید ندارید.")
                return
            
            keyboard = []
            for i, purchase in enumerate(purchases[-5:]):
                parts = purchase.split('|')
                if len(parts) >= 2:
                    service_name = parts[0].strip()
                    volume = parts[1].strip() if len(parts) > 1 else "نامشخص"
                    btn_text = f"🔄 {service_name} - {volume}"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"renew_{i}")])
            
            if keyboard:
                update.message.reply_text(
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
            update.message.reply_text(support_text, parse_mode='HTML')
            return

        if text == '📚 آموزش استفاده':
            guide_text = db["texts"]["guide"].format(
                brand=db["brand"],
                guide_channel=db["guide_channel"]
            )
            update.message.reply_text(guide_text, parse_mode='HTML')
            return

        # --- معرفی به دوستان ---
        if text == '🤝 معرفی به دوستان':
            bot_username = context.bot.get_me().username
            referral_link = f"https://t.me/{bot_username}?start={uid}"
            msg = (
                "🤝 <b>برنامه معرفی به دوستان</b>\n\n"
                "از لینک زیر برای دعوت دوستانت استفاده کن:\n"
                f"<code>{referral_link}</code>\n\n"
                "✨ مزایای معرفی:\n"
                "• به ازای هر دوست، 1 روز به سرویس شما اضافه می‌شود\n"
                "• پس از خرید دوستتان، به شما اعلام می‌شود"
            )
            update.message.reply_text(msg, parse_mode='HTML')
            return

        # --- خرید اشتراک ---
        if text == '💰 خرید اشتراک':
            categories = list(db["categories"].keys())
            keyboard = []
            for cat in categories:
                keyboard.append([cat])
            keyboard.append(['🔙 بازگشت به منوی اصلی'])
            
            update.message.reply_text(
                "📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

        # --- نمایش پلن‌های یک دسته ---
        if text in db["categories"] and not step:
            plans = db["categories"][text]
            if not plans:
                update.message.reply_text("❌ این دسته‌بندی پلنی ندارد.")
                return
            
            keyboard = []
            for plan in plans:
                users_text = f"👥 {plan['users']} کاربره - " if plan['users'] > 1 else ""
                btn_text = f"{plan['name']} - {users_text}{plan['volume']} - {plan['price']}K تومان"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{plan['id']}")])
            
            update.message.reply_text(
                f"📦 <b>{text}</b>\nلطفاً پلن مورد نظر را انتخاب کنید:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- بخش مدیریت ---
        if str(uid) == str(ADMIN_ID):
            
            # منوی مدیریت
            if text == '⚙️ مدیریت ربات':
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu())
                return

            # ویرایش متن‌ها
            if text == '📝 ویرایش متن‌ها':
                keyboard = [
                    ['ویرایش متن خوش‌آمدگویی', 'ویرایش متن پشتیبانی'],
                    ['ویرایش متن آموزش', 'ویرایش متن تست'],
                    ['ویرایش متن عضویت', '🔙 بازگشت به منوی اصلی']
                ]
                update.message.reply_text(
                    "📝 کدام متن را می‌خواهید ویرایش کنید؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # عضویت اجباری
            if text == '🔒 عضویت اجباری':
                keyboard = [
                    ['✅ فعال کردن', '❌ غیرفعال کردن'],
                    ['🔗 تنظیم لینک کانال'],
                    ['🔙 بازگشت به منوی اصلی']
                ]
                update.message.reply_text(
                    f"🔒 وضعیت فعلی: {'فعال' if db['force_join']['enabled'] else 'غیرفعال'}\n"
                    f"📢 کانال: {db['force_join']['channel'] or 'تنظیم نشده'}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ فعال کردن':
                db["force_join"]["enabled"] = True
                save_db(db)
                update.message.reply_text("✅ عضویت اجباری فعال شد.", reply_markup=get_admin_menu())
                return

            if text == '❌ غیرفعال کردن':
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ عضویت اجباری غیرفعال شد.", reply_markup=get_admin_menu())
                return

            if text == '🔗 تنظیم لینک کانال':
                user_data[uid] = {'step': 'set_channel_link'}
                update.message.reply_text(
                    "🔗 لینک کانال را ارسال کنید (مثال: https://t.me/mychannel):",
                    reply_markup=get_back_keyboard()
                )
                return

            # ویرایش پشتیبان
            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'edit_support'}
                update.message.reply_text(
                    "👤 آیدی جدید پشتیبانی را وارد کنید (مثال: @Support_Admin):",
                    reply_markup=get_back_keyboard()
                )
                return

            # ویرایش کانال آموزش
            if text == '📢 ویرایش کانال آموزش':
                user_data[uid] = {'step': 'edit_guide'}
                update.message.reply_text(
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
                update.message.reply_text(
                    "💳 چه اطلاعاتی را ویرایش می‌کنید؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # ویرایش برند
            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'edit_brand'}
                update.message.reply_text(
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
                update.message.reply_text(stats, parse_mode='HTML')
                return

            # ارسال همگانی
            if text == '📨 ارسال همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text(
                    "📨 پیام مورد نظر برای ارسال همگانی را ارسال کنید:",
                    reply_markup=get_back_keyboard()
                )
                return

            # افزودن پلن
            if text == '➕ افزودن پلن':
                categories = list(db["categories"].keys())
                keyboard = []
                for cat in categories:
                    keyboard.append([cat])
                keyboard.append(['🔙 بازگشت به منوی اصلی'])
                
                user_data[uid] = {'step': 'add_plan_category'}
                update.message.reply_text(
                    "📂 لطفاً دسته‌بندی مورد نظر برای افزودن پلن را انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # حذف پلن
            if text == '➖ حذف پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for plan in plans:
                        btn_text = f"❌ {cat} - {plan['name']}"
                        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"delplan_{plan['id']}")])
                
                if keyboard:
                    update.message.reply_text(
                        "🗑 پلن مورد نظر برای حذف را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("❌ هیچ پلنی برای حذف وجود ندارد.")
                return

            # مراحل ویرایش متن
            text_map = {
                'ویرایش متن خوش‌آمدگویی': 'welcome',
                'ویرایش متن پشتیبانی': 'support',
                'ویرایش متن آموزش': 'guide',
                'ویرایش متن تست': 'test',
                'ویرایش متن عضویت': 'force_join'
            }
            
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                update.message.reply_text(
                    f"📝 متن جدید را ارسال کنید:",
                    reply_markup=get_back_keyboard()
                )
                return

            if step and step.startswith('edit_'):
                key = step.replace('edit_', '')
                db["texts"][key] = text
                save_db(db)
                update.message.reply_text("✅ متن با موفقیت ویرایش شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            # مراحل تنظیمات
            if step == 'set_channel_link':
                db["channel_link"] = text
                # استخراج آیدی کانال از لینک
                if 't.me/' in text:
                    channel = text.split('t.me/')[-1].split('/')[0]
                    db["force_join"]["channel"] = f"@{channel}"
                save_db(db)
                update.message.reply_text("✅ لینک کانال ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_support':
                db["support_id"] = text
                save_db(db)
                update.message.reply_text("✅ آیدی پشتیبانی ویرایش شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_guide':
                db["guide_channel"] = text
                save_db(db)
                update.message.reply_text("✅ کانال آموزش ویرایش شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_brand':
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ نام برند ویرایش شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_card_number':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ شماره کارت ویرایش شد.", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ شماره کارت نامعتبر!")
                user_data[uid] = {}
                return

            if step == 'edit_card_name':
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ نام صاحب کارت ویرایش شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'broadcast':
                success = 0
                failed = 0
                for user_id in db["users"].keys():
                    try:
                        context.bot.send_message(int(user_id), text)
                        success += 1
                    except:
                        failed += 1
                
                update.message.reply_text(
                    f"✅ ارسال همگانی انجام شد.\n✓ موفق: {success}\n✗ ناموفق: {failed}",
                    reply_markup=get_admin_menu()
                )
                user_data[uid] = {}
                return

            # مراحل افزودن پلن
            if step == 'add_plan_category' and text in db["categories"]:
                user_data[uid]['category'] = text
                user_data[uid]['step'] = 'add_plan_name'
                update.message.reply_text(
                    "📝 نام پلن را وارد کنید (مثال: ⚡️ پلن ویژه 50GB):",
                    reply_markup=get_back_keyboard()
                )
                return

            if step == 'add_plan_name':
                user_data[uid]['plan_name'] = text
                user_data[uid]['step'] = 'add_plan_volume'
                update.message.reply_text("📦 حجم پلن را وارد کنید (مثال: 50GB):")
                return

            if step == 'add_plan_volume':
                user_data[uid]['volume'] = text
                user_data[uid]['step'] = 'add_plan_users'
                update.message.reply_text("👥 تعداد کاربران را وارد کنید (عدد):")
                return

            if step == 'add_plan_users':
                try:
                    users = int(text)
                    user_data[uid]['users'] = users
                    user_data[uid]['step'] = 'add_plan_days'
                    update.message.reply_text("⏳ مدت اعتبار را به روز وارد کنید (عدد):")
                except ValueError:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'add_plan_days':
                try:
                    days = int(text)
                    user_data[uid]['days'] = days
                    user_data[uid]['step'] = 'add_plan_price'
                    update.message.reply_text("💰 قیمت را به هزار تومان وارد کنید (عدد):")
                except ValueError:
                    update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
                return

            if step == 'add_plan_price':
                try:
                    price = int(text)
                    
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
                    
                    update.message.reply_text(
                        f"✅ پلن با موفقیت به دسته {category} اضافه شد!",
                        reply_markup=get_admin_menu()
                    )
                    user_data[uid] = {}
                    
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
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
                    context.bot.send_message(int(target), config_msg, parse_mode='HTML', reply_markup=keyboard)
                    
                    service_record = f"🚀 {name} | {vol} | {datetime.now().strftime('%Y-%m-%d')}"
                    if str(target) not in db["users"]:
                        db["users"][str(target)] = {"purchases": []}
                    
                    if "purchases" not in db["users"][str(target)]:
                        db["users"][str(target)]["purchases"] = []
                    
                    db["users"][str(target)]["purchases"].append(service_record)
                    save_db(db)
                    
                    update.message.reply_text("✅ کانفیگ با موفقیت ارسال شد.", reply_markup=get_main_menu(uid))
                except Exception as e:
                    update.message.reply_text(f"❌ خطا در ارسال: {str(e)}")
                
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
                f"💰 <b>مبلغ:</b> {plan['price'] * 1000:,} تومان\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ تایید و دریافت کارت", callback_data="show_card")
            ]])
            
            update.message.reply_text(invoice, parse_mode='HTML', reply_markup=keyboard)
            return

    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        logger.error(traceback.format_exc())
        update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت کالبک‌ها ---
def handle_callback(update, context):
    """هندلر کالبک‌های دکمه‌های شیشه‌ای"""
    try:
        query = update.callback_query
        uid = str(query.from_user.id)
        query.answer()

        # بررسی عضویت
        if query.data == "check_join":
            if check_force_join(uid, context):
                query.message.delete()
                start(update, context)
            else:
                query.message.reply_text("❌ شما هنوز عضو کانال نشده‌اید. لطفاً ابتدا عضو شوید.")
            return

        # خرید پلن
        if query.data.startswith("buy_"):
            plan_id = int(query.data.split("_")[1])
            
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
                query.message.reply_text(
                    "📝 لطفاً نام دلخواه برای اکانت خود وارد کنید:",
                    reply_markup=get_back_keyboard()
                )
            else:
                query.message.reply_text("❌ پلن مورد نظر یافت نشد.")

        # نمایش کارت
        elif query.data == "show_card":
            if uid not in user_data or 'plan' not in user_data[uid]:
                query.message.reply_text("❌ خطا در اطلاعات خرید. دوباره تلاش کنید.")
                return
            
            plan = user_data[uid]['plan']
            price = plan['price'] * 1000
            
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
            
            query.message.reply_text(card_msg, parse_mode='HTML', reply_markup=keyboard)

        # ارسال فیش
        elif query.data == "send_receipt":
            if 'plan' in user_data[uid]:
                user_data[uid]['step'] = 'wait_photo'
                query.message.reply_text(
                    "📸 لطفاً عکس فیش واریزی را ارسال کنید:",
                    reply_markup=get_back_keyboard()
                )
            else:
                query.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")

        # تمدید سرویس
        elif query.data.startswith("renew_"):
            index = int(query.data.split("_")[1])
            purchases = db["users"][uid].get("purchases", [])
            
            if index < len(purchases):
                service = purchases[index]
                
                similar_plan = None
                for cat, plans in db["categories"].items():
                    for plan in plans:
                        if plan['volume'] in service or any(word in service for word in plan['name'].split()):
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
                        f"💰 <b>مبلغ تمدید:</b> {similar_plan['price'] * 1000:,} تومان\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📝 لطفاً نام اکانت را وارد کنید:"
                    )
                    
                    query.message.reply_text(renew_msg, parse_mode='HTML')
                else:
                    query.message.reply_text("❌ پلن مشابه برای تمدید یافت نشد. لطفاً از خرید جدید استفاده کنید.")
            else:
                query.message.reply_text("❌ سرویس مورد نظر یافت نشد.")

        # حذف پلن توسط ادمین
        elif query.data.startswith("delplan_"):
            if str(uid) == str(ADMIN_ID):
                plan_id = int(query.data.split("_")[1])
                
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
                    query.message.reply_text("✅ پلن با موفقیت حذف شد.", reply_markup=get_admin_menu())
                else:
                    query.message.reply_text("❌ پلن یافت نشد.")

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
                    
                    context.bot.send_message(
                        ADMIN_ID,
                        f"📨 لطفاً کانفیگ تست برای کاربر {name} را ارسال کنید:"
                    )
                    
                    query.message.edit_reply_markup(reply_markup=None)

        # ارسال کانفیگ خرید توسط ادمین
        elif query.data.startswith("send_config_"):
            if str(uid) == str(ADMIN_ID):
                parts = query.data.split("_", 2)
                if len(parts) >= 3:
                    target = parts[2]
                    
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
                    
                    context.bot.send_message(
                        ADMIN_ID,
                        f"📨 لطفاً کانفیگ سرویس {name} را ارسال کنید:"
                    )
                    
                    query.message.edit_reply_markup(reply_markup=None)

    except Exception as e:
        logger.error(f"Error in handle_callback: {e}")
        logger.error(traceback.format_exc())
        query.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- مدیریت دریافت عکس (فیش واریزی) ---
def handle_photo(update, context):
    """هندلر دریافت عکس"""
    try:
        uid = str(update.effective_user.id)
        
        if user_data.get(uid, {}).get('step') == 'wait_photo':
            if 'plan' not in user_data[uid] or 'account_name' not in user_data[uid]:
                update.message.reply_text("❌ اطلاعات خرید یافت نشد. دوباره از ابتدا شروع کنید.")
                return
            
            account_name = user_data[uid]['account_name']
            plan = user_data[uid]['plan']
            category = user_data[uid].get('category', 'نامشخص')
            
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
                f"💰 <b>مبلغ:</b> {plan['price'] * 1000:,} تومان\n"
                f"👤 <b>نام اکانت:</b> {account_name}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            
            btn = [[InlineKeyboardButton(
                "✅ تایید و ارسال کانفیگ",
                callback_data=f"send_config_{uid}"
            )]]
            
            context.bot.send_photo(
                ADMIN_ID,
                update.message.photo[-1].file_id,
                caption=caption,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(btn)
            )
            
            update.message.reply_text(
                "✅ فیش شما با موفقیت ارسال شد.\n"
                "به زودی پس از تایید، سرویس برای شما ارسال می‌شود.",
                reply_markup=get_main_menu(uid)
            )
            
            if uid in user_data:
                del user_data[uid]

    except Exception as e:
        logger.error(f"Error in handle_photo: {e}")
        update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- اجرای اصلی ---
def main():
    """تابع اصلی"""
    try:
        logger.info("Starting bot...")
        
        # اجرای وب سرور در ترد جداگانه
        web_thread = Thread(target=run_web, daemon=True)
        web_thread.start()
        logger.info("Web server started")
        
        # ساخت ربات با Updater (نسخه پایدار)
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        # اضافه کردن هندلرها
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        logger.info("Bot started successfully!")
        
        # شروع ربات
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()