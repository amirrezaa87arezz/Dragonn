import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
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

# --- پلن‌های پیش‌فرض ---
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
        "force_join": {"enabled": False, "channel": "", "link": ""},
        "texts": {
            "welcome": "🔰 به {brand} خوش آمدید\n\n✅ مخصوص تلگرام، اینستاگرام، یوتیوب\n✅ نصب آسان روی همه دستگاه‌ها\n✅ پشتیبانی 24 ساعته",
            "support": "🆘 پشتیبانی: {support_id}",
            "guide": "📚 کانال آموزش: {guide_channel}",
            "test": "🎁 درخواست تست شما ثبت شد. پس از تایید ادمین ارسال می‌شود.",
            "force_join": "🔒 برای استفاده از ربات باید عضو کانال زیر شوید:\n{link}\n\nپس از عضویت، دکمه ✅ را بزنید."
        }
    }

def save_db(data):
    """ذخیره دیتابیس"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving database: {e}")
        return False

db = load_db()
user_data = {}

# --- منوها ---
def get_main_menu(uid):
    kb = [
        ['💰 خرید اشتراک', '🎁 تست رایگان'],
        ['📂 سرویس‌های من'],
        ['👤 پشتیبانی', '📚 آموزش'],
        ['🤝 معرفی به دوستان']
    ]
    if str(uid) == str(ADMIN_ID):
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_back_keyboard():
    return ReplyKeyboardMarkup([['🔙 بازگشت']], resize_keyboard=True)

def get_admin_menu():
    kb = [
        ['➕ افزودن پلن', '➖ حذف پلن'],
        ['💳 ویرایش کارت', '📝 ویرایش متن'],
        ['👤 ویرایش پشتیبان', '📢 ویرایش کانال'],
        ['🔒 عضویت اجباری', '🏷 ویرایش برند'],
        ['📊 آمار', '📨 همگانی'],
        ['🔙 بازگشت']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- بررسی عضویت ---
def check_join(user_id, context):
    if not db["force_join"]["enabled"] or not db["force_join"]["channel"]:
        return True
    try:
        member = context.bot.get_chat_member(
            chat_id=db["force_join"]["channel"],
            user_id=int(user_id)
        )
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- شروع ---
def start(update, context):
    uid = str(update.effective_user.id)
    
    # ثبت کاربر
    if uid not in db["users"]:
        db["users"][uid] = {
            "purchases": [], "tests": [], "test_count": 0,
            "joined": datetime.now().strftime("%Y-%m-%d")
        }
        save_db(db)
    
    user_data[uid] = {}
    
    # بررسی عضویت اجباری
    if db["force_join"]["enabled"] and db["force_join"]["channel"]:
        if not check_join(uid, context):
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 عضویت", url=db["force_join"]["link"]),
                InlineKeyboardButton("✅ تایید", callback_data="check_join")
            ]])
            text = db["texts"]["force_join"].format(link=db["force_join"]["link"])
            update.message.reply_text(text, reply_markup=keyboard)
            return
    
    welcome = db["texts"]["welcome"].format(brand=db["brand"])
    update.message.reply_text(welcome, reply_markup=get_main_menu(uid))

# --- پیام‌ها ---
def handle_message(update, context):
    try:
        text = update.message.text
        uid = str(update.effective_user.id)
        first = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')

        # بررسی عضویت
        if db["force_join"]["enabled"] and db["force_join"]["channel"]:
            if not check_join(uid, context) and text != '/start':
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت", url=db["force_join"]["link"]),
                    InlineKeyboardButton("✅ تایید", callback_data="check_join")
                ]])
                update.message.reply_text(
                    db["texts"]["force_join"].format(link=db["force_join"]["link"]),
                    reply_markup=keyboard
                )
                return

        # بازگشت
        if text == '🔙 بازگشت':
            user_data[uid] = {}
            start(update, context)
            return

        # تست رایگان
        if text == '🎁 تست رایگان':
            if db["users"][uid]["test_count"] >= 1:
                update.message.reply_text("❌ شما قبلاً تست دریافت کرده‌اید.")
                return
            
            db["users"][uid]["test_count"] += 1
            db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
            save_db(db)
            
            update.message.reply_text(db["texts"]["test"])
            
            # به ادمین
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال تست", callback_data=f"test_{uid}_{first}")
            ]])
            context.bot.send_message(
                ADMIN_ID,
                f"🎁 تست از {first}\nآیدی: {uid}",
                reply_markup=keyboard
            )
            return

        # سرویس‌های من
        if text == '📂 سرویس‌های من':
            purchases = db["users"][uid].get("purchases", [])
            msg = "📂 سرویس‌های شما:\n"
            if purchases:
                for i, p in enumerate(purchases[-10:], 1):
                    msg += f"{i}. {p}\n"
            else:
                msg += "❌ سرویسی ندارید"
            update.message.reply_text(msg)
            return

        # پشتیبانی
        if text == '👤 پشتیبانی':
            update.message.reply_text(db["texts"]["support"].format(support_id=db["support_id"]))
            return

        # آموزش
        if text == '📚 آموزش':
            update.message.reply_text(db["texts"]["guide"].format(guide_channel=db["guide_channel"]))
            return

        # معرفی
        if text == '🤝 معرفی به دوستان':
            bot = context.bot.get_me().username
            update.message.reply_text(
                f"🤝 لینک دعوت شما:\nhttps://t.me/{bot}?start={uid}\n\n"
                "به ازای هر دعوت، 1 روز به سرویس اضافه می‌شود."
            )
            return

        # خرید
        if text == '💰 خرید اشتراک':
            keyboard = [[cat] for cat in db["categories"].keys()] + [['🔙 بازگشت']]
            update.message.reply_text(
                "دسته را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

        # نمایش پلن‌ها
        if text in db["categories"] and not step:
            plans = db["categories"][text]
            keyboard = []
            for p in plans:
                btn = InlineKeyboardButton(
                    f"{p['name']} - {p['price']}K تومان",
                    callback_data=f"buy_{p['id']}"
                )
                keyboard.append([btn])
            update.message.reply_text(
                f"📦 {text}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # --- مدیریت ---
        if str(uid) == str(ADMIN_ID):
            
            if text == '⚙️ مدیریت':
                update.message.reply_text("مدیریت:", reply_markup=get_admin_menu())
                return

            # عضویت اجباری
            if text == '🔒 عضویت اجباری':
                keyboard = [
                    ['✅ فعال', '❌ غیرفعال'],
                    ['🔗 تنظیم لینک'],
                    ['🔙 بازگشت']
                ]
                status = "فعال" if db["force_join"]["enabled"] else "غیرفعال"
                channel = db["force_join"]["channel"] or "ندارد"
                update.message.reply_text(
                    f"وضعیت: {status}\nکانال: {channel}",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ فعال':
                db["force_join"]["enabled"] = True
                save_db(db)
                update.message.reply_text("✅ فعال شد", reply_markup=get_admin_menu())
                return

            if text == '❌ غیرفعال':
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ غیرفعال شد", reply_markup=get_admin_menu())
                return

            if text == '🔗 تنظیم لینک':
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text("لینک کانال را بفرستید:", reply_markup=get_back_keyboard())
                return

            # ویرایش پشتیبان
            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'edit_support'}
                update.message.reply_text("آیدی جدید پشتیبانی:", reply_markup=get_back_keyboard())
                return

            # ویرایش کانال
            if text == '📢 ویرایش کانال':
                user_data[uid] = {'step': 'edit_guide'}
                update.message.reply_text("آیدی جدید کانال آموزش:", reply_markup=get_back_keyboard())
                return

            # ویرایش برند
            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'edit_brand'}
                update.message.reply_text("نام جدید برند:", reply_markup=get_back_keyboard())
                return

            # ویرایش کارت
            if text == '💳 ویرایش کارت':
                keyboard = [['شماره کارت', 'نام صاحب'], ['🔙 بازگشت']]
                update.message.reply_text(
                    "چه چیزی را ویرایش می‌کنید؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == 'شماره کارت':
                user_data[uid] = {'step': 'edit_card_num'}
                update.message.reply_text("شماره کارت 16 رقمی:", reply_markup=get_back_keyboard())
                return

            if text == 'نام صاحب':
                user_data[uid] = {'step': 'edit_card_name'}
                update.message.reply_text("نام صاحب کارت:", reply_markup=get_back_keyboard())
                return

            # ویرایش متن
            if text == '📝 ویرایش متن':
                keyboard = [
                    ['خوش‌آمدگویی', 'پشتیبانی'],
                    ['آموزش', 'تست', 'عضویت'],
                    ['🔙 بازگشت']
                ]
                update.message.reply_text(
                    "کدام متن؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            text_map = {
                'خوش‌آمدگویی': 'welcome',
                'پشتیبانی': 'support',
                'آموزش': 'guide',
                'تست': 'test',
                'عضویت': 'force_join'
            }
            
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                update.message.reply_text("متن جدید را بفرستید:", reply_markup=get_back_keyboard())
                return

            # افزودن پلن
            if text == '➕ افزودن پلن':
                cats = list(db["categories"].keys())
                keyboard = [[c] for c in cats] + [['🔙 بازگشت']]
                user_data[uid] = {'step': 'add_cat'}
                update.message.reply_text(
                    "دسته را انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            # حذف پلن
            if text == '➖ حذف پلن':
                keyboard = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        btn = InlineKeyboardButton(
                            f"❌ {cat} - {p['name']}",
                            callback_data=f"del_{p['id']}"
                        )
                        keyboard.append([btn])
                if keyboard:
                    update.message.reply_text(
                        "پلن را انتخاب کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    update.message.reply_text("پلنی نیست")
                return

            # آمار
            if text == '📊 آمار':
                total = len(db["users"])
                purchases = sum(len(u.get("purchases", [])) for u in db["users"].values())
                tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                update.message.reply_text(
                    f"👥 کاربران: {total}\n"
                    f"💰 خرید: {purchases}\n"
                    f"🎁 تست: {tests}"
                )
                return

            # همگانی
            if text == '📨 همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text("پیام همگانی را بفرستید:", reply_markup=get_back_keyboard())
                return

            # مراحل
            if step == 'set_link':
                db["force_join"]["link"] = text
                if 't.me/' in text:
                    ch = text.split('t.me/')[-1].split('/')[0]
                    db["force_join"]["channel"] = f"@{ch}"
                save_db(db)
                update.message.reply_text("✅ لینک ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_support':
                db["support_id"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_guide':
                db["guide_channel"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_brand':
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'edit_card_num':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ نامعتبر")
                user_data[uid] = {}
                return

            if step == 'edit_card_name':
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step and step.startswith('edit_'):
                key = step.replace('edit_', '')
                db["texts"][key] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if step == 'add_cat' and text in db["categories"]:
                user_data[uid]['cat'] = text
                user_data[uid]['step'] = 'add_name'
                update.message.reply_text("نام پلن:", reply_markup=get_back_keyboard())
                return

            if step == 'add_name':
                user_data[uid]['name'] = text
                user_data[uid]['step'] = 'add_vol'
                update.message.reply_text("حجم (مثال: 50GB):")
                return

            if step == 'add_vol':
                user_data[uid]['vol'] = text
                user_data[uid]['step'] = 'add_users'
                update.message.reply_text("تعداد کاربران (عدد):")
                return

            if step == 'add_users':
                try:
                    user_data[uid]['users'] = int(text)
                    user_data[uid]['step'] = 'add_days'
                    update.message.reply_text("مدت (روز):")
                except:
                    update.message.reply_text("❌ عدد وارد کن")
                return

            if step == 'add_days':
                try:
                    user_data[uid]['days'] = int(text)
                    user_data[uid]['step'] = 'add_price'
                    update.message.reply_text("قیمت (هزار تومان):")
                except:
                    update.message.reply_text("❌ عدد وارد کن")
                return

            if step == 'add_price':
                try:
                    price = int(text)
                    max_id = 0
                    for p in db["categories"].values():
                        for plan in p:
                            if plan["id"] > max_id:
                                max_id = plan["id"]
                    
                    new = {
                        "id": max_id + 1,
                        "name": user_data[uid]['name'],
                        "price": price,
                        "volume": user_data[uid]['vol'],
                        "days": user_data[uid]['days'],
                        "users": user_data[uid]['users']
                    }
                    
                    cat = user_data[uid]['cat']
                    db["categories"][cat].append(new)
                    save_db(db)
                    
                    update.message.reply_text("✅ پلن اضافه شد", reply_markup=get_admin_menu())
                    user_data[uid] = {}
                except:
                    update.message.reply_text("❌ خطا")
                return

            if step == 'broadcast':
                suc, fail = 0, 0
                for uid2 in db["users"]:
                    try:
                        context.bot.send_message(int(uid2), text)
                        suc += 1
                    except:
                        fail += 1
                update.message.reply_text(f"✅ موفق: {suc}\n❌ ناموفق: {fail}")
                user_data[uid] = {}
                return

            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                
                msg = (
                    f"🎉 سرویس شما آماده است!\n"
                    f"👤 {name}\n"
                    f"🔗 {update.message.text}\n"
                    f"📚 @{db['guide_channel'].replace('@', '')}"
                )
                
                try:
                    context.bot.send_message(int(target), msg)
                    db["users"][str(target)]["purchases"].append(f"{name} | {datetime.now()}")
                    save_db(db)
                    update.message.reply_text("✅ ارسال شد")
                except:
                    update.message.reply_text("❌ خطا")
                
                user_data[uid] = {}
                return

        # دریافت نام برای خرید
        if step == 'wait_name':
            user_data[uid]['account'] = text
            p = user_data[uid]['plan']
            
            msg = (
                f"💎 پیش‌فاکتور\n"
                f"👤 نام: {text}\n"
                f"📦 {p['name']}\n"
                f"💰 {p['price']*1000:,} تومان\n\n"
                f"💳 {db['card']['number']}\n"
                f"👤 {db['card']['name']}"
            )
            
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="send_receipt")
            ]])
            
            update.message.reply_text(msg, reply_markup=kb)

    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("خطا! دوباره تلاش کنید.")

# --- کالبک ---
def handle_callback(update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    query.answer()

    # بررسی عضویت
    if query.data == "check_join":
        if check_join(uid, context):
            query.message.delete()
            start(update, context)
        else:
            query.message.reply_text("❌ هنوز عضو نشده‌اید")
        return

    # خرید
    if query.data.startswith("buy_"):
        pid = int(query.data.split("_")[1])
        for cat in db["categories"].values():
            for p in cat:
                if p["id"] == pid:
                    user_data[uid] = {'step': 'wait_name', 'plan': p}
                    query.message.reply_text("نام اکانت را وارد کنید:")
                    return
        query.message.reply_text("❌ پلن یافت نشد")

    # ارسال فیش
    elif query.data == "send_receipt":
        if uid in user_data and 'plan' in user_data[uid]:
            user_data[uid]['step'] = 'wait_photo'
            query.message.reply_text("📸 عکس فیش را بفرستید:")
        else:
            query.message.reply_text("❌ خطا")

    # حذف پلن
    elif query.data.startswith("del_"):
        if str(uid) == str(ADMIN_ID):
            pid = int(query.data.split("_")[1])
            for cat in db["categories"].values():
                for i, p in enumerate(cat):
                    if p["id"] == pid:
                        del cat[i]
                        save_db(db)
                        query.message.reply_text("✅ حذف شد")
                        return
            query.message.reply_text("❌ یافت نشد")

    # ارسال تست
    elif query.data.startswith("test_"):
        if str(uid) == str(ADMIN_ID):
            parts = query.data.split("_")
            target, name = parts[1], parts[2]
            user_data[uid] = {'step': 'send_config', 'target': target, 'name': f"تست {name}"}
            context.bot.send_message(ADMIN_ID, "کانفیگ تست را بفرستید:")
            query.message.edit_reply_markup()

# --- عکس ---
def handle_photo(update, context):
    uid = str(update.effective_user.id)
    
    if user_data.get(uid, {}).get('step') == 'wait_photo':
        p = user_data[uid]['plan']
        acc = user_data[uid]['account']
        
        cap = (
            f"💰 فیش جدید\n"
            f"👤 {update.effective_user.first_name}\n"
            f"🆔 {uid}\n"
            f"📦 {p['name']}\n"
            f"👤 {acc}\n"
            f"💰 {p['price']*1000:,} تومان"
        )
        
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"send_{uid}")
        ]])
        
        context.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=cap,
            reply_markup=kb
        )
        
        update.message.reply_text("✅ فیش ارسال شد")
        del user_data[uid]

# --- اجرا ---
def main():
    try:
        logger.info("Starting...")
        Thread(target=run_web, daemon=True).start()
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text, handle_message))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        updater.start_polling()
        logger.info("Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"Fatal: {e}")

if __name__ == '__main__':
    main()