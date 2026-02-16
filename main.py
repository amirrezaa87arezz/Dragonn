import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
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
    return "✅ VPN Bot is Running!", 200

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
                logger.info("✅ Database loaded")
                return data
    except Exception as e:
        logger.error(f"❌ Error loading: {e}")
    
    # دیتابیس پیش‌فرض
    logger.info("📁 Creating default database")
    return {
        "users": {},
        "brand": "تک نت وی‌پی‌ان",
        "card": {
            "number": "6277601368776066",
            "name": "محمد رضوانی"
        },
        "support": "@Support_Admin",
        "guide": "@Guide_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "force_join": {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""},
        "texts": {
            "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته\n✅ نصب آسان",
            "support": "🆘 پشتیبانی: {support}",
            "guide": "📚 آموزش: {guide}",
            "test": "🎁 درخواست تست شما ثبت شد",
            "force": "🔒 برای استفاده از ربات باید در کانال زیر عضو شوید:\n{link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید."
        }
    }

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

db = load_db()
user_data = {}

# --- منوها ---
def main_menu(uid):
    kb = [
        ['💰 خرید', '🎁 تست'],
        ['📂 سرویس‌ها'],
        ['👤 پشتیبانی', '📚 آموزش'],
        ['🤝 دعوت دوستان']
    ]
    if str(uid) == str(ADMIN_ID):
        kb.append(['⚙️ مدیریت'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    return ReplyKeyboardMarkup([['🔙 برگشت']], resize_keyboard=True)

def admin_menu():
    kb = [
        ['➕ پلن جدید', '➖ حذف پلن'],
        ['💳 کارت', '📝 متن‌ها'],
        ['👤 پشتیبان', '📢 کانال'],
        ['🔒 عضویت', '🏷 برند'],
        ['📊 آمار', '📨 همگانی'],
        ['🔙 برگشت']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- بررسی عضویت (اصلاح شده) ---
def check_join(user_id, context):
    """بررسی عضویت کاربر در کانال"""
    if not db["force_join"]["enabled"]:
        return True
        
    channel_id = db["force_join"].get("channel_id", "")
    channel_username = db["force_join"].get("channel_username", "")
    
    if not channel_id and not channel_username:
        return True
    
    try:
        # اول با آیدی عددی تلاش کن
        if channel_id:
            try:
                member = context.bot.get_chat_member(
                    chat_id=int(channel_id),
                    user_id=int(user_id)
                )
                return member.status in ['member', 'administrator', 'creator']
            except:
                pass
        
        # بعد با یوزرنیم تلاش کن
        if channel_username:
            member = context.bot.get_chat_member(
                chat_id=channel_username,
                user_id=int(user_id)
            )
            return member.status in ['member', 'administrator', 'creator']
            
    except Exception as e:
        logger.error(f"❌ Error checking join: {e}")
        # اگر خطای 400 یعنی کاربر اصلاً عضو نیست
        if "400" in str(e):
            return False
    
    return False

# --- استارت ---
def start(update, context):
    uid = str(update.effective_user.id)
    
    # ثبت کاربر
    if uid not in db["users"]:
        db["users"][uid] = {
            "purchases": [],
            "tests": [],
            "test_count": 0,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        save_db(db)
    
    user_data[uid] = {}
    
    # بررسی عضویت اجباری
    if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
        if not check_join(uid, context):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
            ]])
            msg = db["texts"]["force"].format(link=db["force_join"]["channel_link"])
            update.message.reply_text(msg, reply_markup=btn)
            return
    
    # خوش‌آمد
    welcome = db["texts"]["welcome"].format(brand=db["brand"])
    update.message.reply_text(welcome, reply_markup=main_menu(uid))

# --- پیام‌ها ---
def handle_msg(update, context):
    try:
        text = update.message.text
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')

        # بررسی عضویت
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
            if not check_join(uid, context) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                update.message.reply_text(
                    db["texts"]["force"].format(link=db["force_join"]["channel_link"]),
                    reply_markup=btn
                )
                return

        # برگشت
        if text == '🔙 برگشت':
            user_data[uid] = {}
            start(update, context)
            return

        # تست رایگان
        if text == '🎁 تست':
            if db["users"][uid]["test_count"] >= 1:
                update.message.reply_text("❌ شما قبلاً تست گرفته‌اید")
                return
            
            db["users"][uid]["test_count"] += 1
            db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
            save_db(db)
            
            update.message.reply_text(db["texts"]["test"])
            
            # به ادمین
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال تست", callback_data=f"test_{uid}_{name}")
            ]])
            context.bot.send_message(
                ADMIN_ID,
                f"🎁 درخواست تست\n👤 {name}\n🆔 {uid}",
                reply_markup=btn
            )
            return

        # سرویس‌ها
        if text == '📂 سرویس‌ها':
            pur = db["users"][uid].get("purchases", [])
            msg = "📂 سرویس‌های شما:\n"
            if pur:
                for i, p in enumerate(pur[-10:], 1):
                    msg += f"{i}. {p}\n"
            else:
                msg += "❌ سرویسی ندارید"
            update.message.reply_text(msg)
            return

        # پشتیبانی
        if text == '👤 پشتیبانی':
            update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
            return

        # آموزش
        if text == '📚 آموزش':
            update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
            return

        # دعوت
        if text == '🤝 دعوت دوستان':
            bot = context.bot.get_me().username
            update.message.reply_text(
                f"🤝 لینک دعوت شما:\n"
                f"https://t.me/{bot}?start={uid}\n\n"
                "به ازای هر دعوت 1 روز هدیه"
            )
            return

        # خرید
        if text == '💰 خرید':
            cats = list(db["categories"].keys())
            kb = [[c] for c in cats] + [['🔙 برگشت']]
            update.message.reply_text(
                "دسته را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
            )
            return

        # نمایش پلن‌ها
        if text in db["categories"] and not step:
            plans = db["categories"][text]
            keyboard = []
            for p in plans:
                btn = InlineKeyboardButton(
                    f"{p['name']} - {p['price']} هزار تومان",
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
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=admin_menu())
                return

            # کارت
            if text == '💳 کارت':
                keyboard = [
                    ['شماره کارت', 'نام صاحب'],
                    ['🔙 برگشت']
                ]
                current = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(
                    current,
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == 'شماره کارت':
                user_data[uid] = {'step': 'card_num'}
                update.message.reply_text("شماره کارت 16 رقمی را بفرستید:", reply_markup=back_btn())
                return

            if text == 'نام صاحب':
                user_data[uid] = {'step': 'card_name'}
                update.message.reply_text("نام صاحب کارت را بفرستید:", reply_markup=back_btn())
                return

            # پشتیبان
            if text == '👤 پشتیبان':
                user_data[uid] = {'step': 'support'}
                update.message.reply_text("آیدی پشتیبان را بفرستید:", reply_markup=back_btn())
                return

            # کانال
            if text == '📢 کانال':
                user_data[uid] = {'step': 'guide'}
                update.message.reply_text("آیدی کانال آموزش را بفرستید:", reply_markup=back_btn())
                return

            # برند
            if text == '🏷 برند':
                user_data[uid] = {'step': 'brand'}
                update.message.reply_text("نام برند را بفرستید:", reply_markup=back_btn())
                return

            # عضویت اجباری (اصلاح شده)
            if text == '🔒 عضویت':
                keyboard = [
                    ['✅ فعال کردن', '❌ غیرفعال کردن'],
                    ['🔗 تنظیم لینک کانال'],
                    ['🔙 برگشت']
                ]
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                channel = db["force_join"]["channel_username"] or "تنظیم نشده"
                update.message.reply_text(
                    f"🔒 وضعیت عضویت اجباری:\n"
                    f"وضعیت: {status}\n"
                    f"کانال: {channel}\n\n"
                    "برای تنظیم، ابتدا لینک کانال را وارد کنید.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            if text == '✅ فعال کردن':
                if db["force_join"]["channel_link"] and db["force_join"]["channel_username"]:
                    db["force_join"]["enabled"] = True
                    save_db(db)
                    update.message.reply_text("✅ عضویت اجباری فعال شد", reply_markup=admin_menu())
                else:
                    update.message.reply_text("❌ ابتدا لینک کانال را تنظیم کنید")
                return

            if text == '❌ غیرفعال کردن':
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ عضویت اجباری غیرفعال شد", reply_markup=admin_menu())
                return

            if text == '🔗 تنظیم لینک کانال':
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text(
                    "🔗 لینک کانال را بفرستید (مثال: https://t.me/mychannel):\n\n"
                    "⚠️ نکته: ربات باید در کانال ادمین باشد!",
                    reply_markup=back_btn()
                )
                return

            # متن‌ها
            if text == '📝 متن‌ها':
                keyboard = [
                    ['خوش‌آمد', 'پشتیبانی', 'آموزش'],
                    ['تست', 'عضویت'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text(
                    "کدام متن را ویرایش کنیم؟",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            text_map = {
                'خوش‌آمد': 'welcome',
                'پشتیبانی': 'support',
                'آموزش': 'guide',
                'تست': 'test',
                'عضویت': 'force'
            }
            
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                update.message.reply_text("متن جدید را بفرستید:", reply_markup=back_btn())
                return

            # آمار
            if text == '📊 آمار':
                total = len(db["users"])
                pur = sum(len(u.get("purchases", [])) for u in db["users"].values())
                tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                update.message.reply_text(
                    f"📊 آمار ربات\n"
                    f"👥 کاربران: {total}\n"
                    f"💰 خریدها: {pur}\n"
                    f"🎁 تست‌ها: {tests}"
                )
                return

            # همگانی
            if text == '📨 همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text("پیام همگانی را بفرستید:", reply_markup=back_btn())
                return

            # پلن جدید
            if text == '➕ پلن جدید':
                cats = list(db["categories"].keys())
                kb = [[c] for c in cats] + [['🔙 برگشت']]
                user_data[uid] = {'step': 'new_cat'}
                update.message.reply_text(
                    "دسته را انتخاب کنید:",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
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
                    update.message.reply_text("❌ پلنی نیست")
                return

            # --- مراحل ویرایش ---
            if step == 'card_num':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ شماره کارت ذخیره شد", reply_markup=admin_menu())
                else:
                    update.message.reply_text("❌ شماره کارت نامعتبر")
                user_data[uid] = {}
                return

            if step == 'card_name':
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ نام صاحب کارت ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step == 'support':
                db["support"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step == 'guide':
                db["guide"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step == 'brand':
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step == 'set_link':
                # ذخیره لینک
                db["force_join"]["channel_link"] = text
                
                # استخراج یوزرنیم کانال از لینک
                if 't.me/' in text:
                    username = text.split('t.me/')[-1].split('/')[0].replace('@', '')
                    db["force_join"]["channel_username"] = f"@{username}"
                    
                    # تلاش برای گرفتن آیدی عددی
                    try:
                        chat = context.bot.get_chat(f"@{username}")
                        db["force_join"]["channel_id"] = str(chat.id)
                        update.message.reply_text(f"✅ کانال شناسایی شد: {chat.title}")
                    except Exception as e:
                        logger.error(f"Error getting chat: {e}")
                        update.message.reply_text(
                            f"⚠️ لینک ذخیره شد اما ربات در کانال ادمین نیست!\n"
                            f"لطفاً ربات را به کانال اضافه کنید و ادمینش کنید."
                        )
                
                save_db(db)
                update.message.reply_text("✅ لینک کانال ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step and step.startswith('edit_'):
                key = step.replace('edit_', '')
                db["texts"][key] = text
                save_db(db)
                update.message.reply_text("✅ متن ذخیره شد", reply_markup=admin_menu())
                user_data[uid] = {}
                return

            if step == 'broadcast':
                suc, fail = 0, 0
                for uid2 in db["users"]:
                    try:
                        context.bot.send_message(int(uid2), text)
                        suc += 1
                    except:
                        fail += 1
                update.message.reply_text(f"✅ ارسال شد\nموفق: {suc}\nناموفق: {fail}")
                user_data[uid] = {}
                return

            # --- مراحل پلن جدید ---
            if step == 'new_cat' and text in db["categories"]:
                user_data[uid]['cat'] = text
                user_data[uid]['step'] = 'new_name'
                update.message.reply_text("نام پلن:", reply_markup=back_btn())
                return

            if step == 'new_name':
                user_data[uid]['name'] = text
                user_data[uid]['step'] = 'new_vol'
                update.message.reply_text("حجم (مثال: 50GB):")
                return

            if step == 'new_vol':
                user_data[uid]['vol'] = text
                user_data[uid]['step'] = 'new_users'
                update.message.reply_text("تعداد کاربران:")
                return

            if step == 'new_users':
                try:
                    user_data[uid]['users'] = int(text)
                    user_data[uid]['step'] = 'new_days'
                    update.message.reply_text("مدت (روز):")
                except:
                    update.message.reply_text("❌ عدد وارد کنید")
                return

            if step == 'new_days':
                try:
                    user_data[uid]['days'] = int(text)
                    user_data[uid]['step'] = 'new_price'
                    update.message.reply_text("قیمت (هزار تومان):")
                except:
                    update.message.reply_text("❌ عدد وارد کنید")
                return

            if step == 'new_price':
                try:
                    price = int(text)
                    # پیدا کردن id
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
                    
                    update.message.reply_text("✅ پلن اضافه شد", reply_markup=admin_menu())
                    user_data[uid] = {}
                except:
                    update.message.reply_text("❌ خطا")
                return

            # دریافت کانفیگ
            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                
                msg = (
                    f"🎉 سرویس شما آماده است\n"
                    f"👤 {name}\n"
                    f"🔗 {update.message.text}\n"
                    f"📚 {db['guide']}"
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
                f"💳 اطلاعات پرداخت\n"
                f"👤 نام: {text}\n"
                f"📦 {p['name']}\n"
                f"💰 {p['price']*1000:,} تومان\n\n"
                f"💳 شماره کارت:\n{db['card']['number']}\n"
                f"👤 {db['card']['name']}\n\n"
                "پس از واریز، عکس فیش را بفرستید"
            )
            
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="receipt")
            ]])
            
            update.message.reply_text(msg, reply_markup=btn)

    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ خطا، دوباره تلاش کنید")

# --- کالبک (اصلاح شده) ---
def handle_cb(update, context):
    query = update.callback_query
    uid = str(query.from_user.id)
    query.answer()

    # بررسی عضویت (اصلاح شده)
    if query.data == "join_check":
        if check_join(uid, context):
            query.message.delete()
            # ارسال پیام خوش‌آمدگویی
            welcome = db["texts"]["welcome"].format(brand=db["brand"])
            context.bot.send_message(uid, welcome, reply_markup=main_menu(uid))
        else:
            query.message.reply_text(
                "❌ شما هنوز عضو کانال نشده‌اید!\n"
                "لطفاً ابتدا عضو شوید سپس دکمه تایید را بزنید."
            )
        return

    # خرید
    if query.data.startswith("buy_"):
        pid = int(query.data.split("_")[1])
        for cat in db["categories"].values():
            for p in cat:
                if p["id"] == pid:
                    user_data[uid] = {'step': 'wait_name', 'plan': p}
                    query.message.reply_text("📝 نام اکانت را وارد کنید:")
                    return
        query.message.reply_text("❌ پلن یافت نشد")

    # ارسال فیش
    elif query.data == "receipt":
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
                        query.message.reply_text("✅ پلن حذف شد")
                        return
            query.message.reply_text("❌ یافت نشد")

    # ارسال تست
    elif query.data.startswith("test_"):
        if str(uid) == str(ADMIN_ID):
            parts = query.data.split("_")
            target, name = parts[1], parts[2]
            user_data[uid] = {'step': 'send_config', 'target': target, 'name': f"تست {name}"}
            context.bot.send_message(ADMIN_ID, "📨 کانفیگ تست را بفرستید:")
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
            f"👤 اکانت: {acc}\n"
            f"💰 {p['price']*1000:,} تومان"
        )
        
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"send_{uid}")
        ]])
        
        context.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=cap,
            reply_markup=btn
        )
        
        update.message.reply_text("✅ فیش ارسال شد")
        del user_data[uid]

# --- اجرا ---
def main():
    try:
        logger.info("🚀 Starting bot...")
        
        # وب سرور
        Thread(target=run_web, daemon=True).start()
        
        # ربات
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(CallbackQueryHandler(handle_cb))
        
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == '__main__':
    main()