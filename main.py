import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from datetime import datetime
import traceback
import time
import signal

# --- تنظیمات لاگینگ ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وب سرور ساده ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("✅ VPN Bot is Running!".encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def run_web():
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Web server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Web server error: {e}")

# --- توکن و آیدی ادمین ---
TOKEN = '8305364438:AAGAT39wGQey9tzxMVafEiRRXz1eGNvpfhY'
ADMIN_ID = 1374345602

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

DEFAULT_MENU_BUTTONS = [
    {"text": "💰 خرید اشتراک", "action": "buy"},
    {"text": "🎁 تست رایگان", "action": "test"},
    {"text": "📂 سرویس‌ها", "action": "services"},
    {"text": "⏳ تمدید", "action": "renew"},
    {"text": "👤 مشخصات من", "action": "profile"},
    {"text": "👤 پشتیبانی", "action": "support"},
    {"text": "📚 آموزش", "action": "guide"},
    {"text": "🤝 دعوت دوستان", "action": "invite"}
]

DEFAULT_TEXTS = {
    "welcome": "🔰 به {brand} خوش آمدید\n\n✅ فروش ویژه فیلترشکن\n✅ پشتیبانی 24 ساعته\n✅ نصب آسان",
    "support": "🆘 پشتیبانی: {support}",
    "guide": "📚 آموزش: {guide}",
    "test": "🎁 درخواست تست شما ثبت شد",
    "force": "🔒 برای استفاده از ربات باید در کانال زیر عضو شوید:\n{link}\n\nپس از عضویت، دکمه ✅ تایید را بزنید.",
    "invite": "🤝 لینک دعوت شما:\n{link}\n\nبه ازای هر دعوت 1 روز هدیه",
    "payment_info": "💳 اطلاعات پرداخت\n━━━━━━━━━━━━━━\n👤 نام اکانت: {account}\n📦 پلن: {plan_name}\n📊 حجم: {volume}\n👥 {users_text}\n⏳ مدت: {days} روز\n💰 مبلغ: {price:,} تومان\n━━━━━━━━━━━━━━\n💳 شماره کارت:\n<code>{card_number}</code>\n👤 {card_name}\n━━━━━━━━━━━━━━\nپس از واریز، عکس فیش را بفرستید",
    "maintenance": "🔧 ربات در حال تعمیرات است. لطفاً بعداً مراجعه کنید.",
    "config_sent": "🎉 سرویس شما آماده است!\n━━━━━━━━━━━━━━━━━━━━\n👤 نام کاربری سرویس : {name}\n⏳ مدت زمان: {days} روز\n🗜 حجم سرویس: {volume}\n━━━━━━━━━━━━━━━━━━━━\nلینک اتصال:\n<code>{config}</code>\n━━━━━━━━━━━━━━━━━━━━\n🧑‍🦯 شما میتوانید شیوه اتصال را با فشردن دکمه زیر و انتخاب سیستم عامل خود را دریافت کنید\n\n🟢 اگر لینک ساب شما داخل برنامه اضافه نشد، ربات @URLExtractor_Bot به شما کمک می‌کنه لینک‌ها رو استخراج کنید.\n\n🔵 کافیه لینک ساب خودتون رو بهش بدید تا تمامی کانفیگ‌هاش رو براتون خروجی بگیره.",
    "admin_panel": "🛠 پنل مدیریت",
    "back_button": "🔙 برگشت",
    "cancel": "❌ انصراف"
}

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info("✅ Database loaded")
                
                if "force_join" not in data:
                    data["force_join"] = {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""}
                if "bot_status" not in data:
                    data["bot_status"] = {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]}
                if "categories" not in data or not data["categories"]:
                    data["categories"] = DEFAULT_PLANS.copy()
                if "menu_buttons" not in data:
                    data["menu_buttons"] = DEFAULT_MENU_BUTTONS.copy()
                if "texts" not in data:
                    data["texts"] = DEFAULT_TEXTS.copy()
                else:
                    for key, value in DEFAULT_TEXTS.items():
                        if key not in data["texts"]:
                            data["texts"][key] = value
                return data
    except Exception as e:
        logger.error(f"❌ Error loading: {e}")
    
    logger.info("📁 Creating default database")
    return {
        "users": {},
        "brand": "تک نت وی‌پی‌ان",
        "card": {"number": "6277601368776066", "name": "محمد رضوانی"},
        "support": "@Support_Admin",
        "guide": "@Guide_Channel",
        "categories": DEFAULT_PLANS.copy(),
        "menu_buttons": DEFAULT_MENU_BUTTONS.copy(),
        "force_join": {"enabled": False, "channel_id": "", "channel_link": "", "channel_username": ""},
        "bot_status": {"enabled": True, "message": DEFAULT_TEXTS["maintenance"]},
        "texts": DEFAULT_TEXTS.copy()
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

def get_main_menu(uid):
    buttons = db["menu_buttons"]
    kb = []
    row = []
    for i, btn in enumerate(buttons):
        row.append(btn["text"])
        if (i + 1) % 2 == 0 or i == len(buttons) - 1:
            kb.append(row)
            row = []
    if str(uid) == str(ADMIN_ID):
        kb.append(["⚙️ مدیریت"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def back_btn():
    return ReplyKeyboardMarkup([["🔙 برگشت"]], resize_keyboard=True)

def get_admin_menu():
    kb = [
        ['📋 مدیریت منو', '📦 مدیریت دسته‌ها'],
        ['➕ پلن جدید', '➖ حذف پلن', '✏️ ویرایش پلن'],
        ['💳 ویرایش کارت', '📝 ویرایش متن‌ها'],
        ['👤 ویرایش پشتیبان', '📢 ویرایش کانال'],
        ['🔒 عضویت اجباری', '🏷 ویرایش برند'],
        ['🔛 وضعیت ربات', '📊 آمار'],
        ['📦 بکاپ‌گیری', '🔄 بازیابی بکاپ'],
        ['📨 ارسال همگانی', '🔙 برگشت']
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def check_join(user_id, context):
    if not db["force_join"]["enabled"]:
        return True
    channel_id = db["force_join"].get("channel_id", "")
    channel_username = db["force_join"].get("channel_username", "")
    if not channel_id and not channel_username:
        return True
    if channel_id:
        try:
            member = context.bot.get_chat_member(chat_id=int(channel_id), user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    if channel_username:
        try:
            member = context.bot.get_chat_member(chat_id=channel_username, user_id=int(user_id))
            if member.status in ['member', 'administrator', 'creator']:
                return True
        except:
            pass
    return False

def start(update, context):
    try:
        uid = str(update.effective_user.id)
        args = context.args
        if args and args[0].isdigit() and args[0] != uid:
            inviter_id = args[0]
            if inviter_id in db["users"] and uid not in db["users"]:
                if "invited_users" not in db["users"][inviter_id]:
                    db["users"][inviter_id]["invited_users"] = []
                if uid not in db["users"][inviter_id]["invited_users"]:
                    db["users"][inviter_id]["invited_users"].append(uid)
        
        if uid not in db["users"]:
            db["users"][uid] = {
                "purchases": [], "tests": [], "test_count": 0,
                "invited_by": args[0] if args and args[0].isdigit() and args[0] != uid else None,
                "invited_users": [], "date": datetime.now().strftime("%Y-%m-%d")
            }
            save_db(db)
        
        user_data[uid] = {}
        
        if not db["bot_status"]["enabled"]:
            update.message.reply_text(db["bot_status"]["message"])
            return
        
        if db["force_join"]["enabled"] and db["force_join"]["channel_link"]:
            if not check_join(uid, context):
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                msg = db["texts"]["force"].format(link=db["force_join"]["channel_link"])
                update.message.reply_text(msg, reply_markup=btn)
                return
        
        welcome = db["texts"]["welcome"].format(brand=db["brand"])
        update.message.reply_text(welcome, reply_markup=get_main_menu(uid))
    except Exception as e:
        logger.error(f"Error: {e}")

def handle_msg(update, context):
    try:
        text = update.message.text
        uid = str(update.effective_user.id)
        name = update.effective_user.first_name or "کاربر"
        step = user_data.get(uid, {}).get('step')
        texts = db["texts"]

        if not db["bot_status"]["enabled"] and str(uid) != str(ADMIN_ID):
            update.message.reply_text(db["bot_status"]["message"])
            return

        if db["force_join"]["enabled"] and db["force_join"]["channel_link"] and str(uid) != str(ADMIN_ID):
            if not check_join(uid, context) and text != '/start':
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 عضویت در کانال", url=db["force_join"]["channel_link"]),
                    InlineKeyboardButton("✅ تایید عضویت", callback_data="join_check")
                ]])
                update.message.reply_text(db["texts"]["force"].format(link=db["force_join"]["channel_link"]), reply_markup=btn)
                return

        if text == "🔙 برگشت":
            user_data[uid] = {}
            start(update, context)
            return

        if text == '/start':
            start(update, context)
            return
        
        # بررسی دکمه‌های منو
        for btn in db["menu_buttons"]:
            if text == btn["text"]:
                action = btn["action"]
                if action == "buy":
                    cats = list(db["categories"].keys())
                    keyboard = []
                    for cat in cats:
                        keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
                    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
                    update.message.reply_text("📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                elif action == "test":
                    if db["users"][uid]["test_count"] >= 1:
                        update.message.reply_text("❌ شما قبلاً تست دریافت کرده‌اید.")
                        return
                    db["users"][uid]["test_count"] += 1
                    db["users"][uid]["tests"].append(datetime.now().strftime("%Y-%m-%d"))
                    save_db(db)
                    update.message.reply_text(db["texts"]["test"])
                    btn = InlineKeyboardMarkup([[InlineKeyboardButton("📤 ارسال تست", callback_data=f"test_{uid}_{name}")]])
                    context.bot.send_message(ADMIN_ID, f"🎁 درخواست تست جدید\n👤 {name}\n🆔 {uid}", reply_markup=btn)
                    return
                elif action == "services":
                    pur = db["users"][uid].get("purchases", [])
                    tests = db["users"][uid].get("tests", [])
                    msg = "📂 سرویس‌های شما:\n━━━━━━━━━━\n"
                    if pur:
                        msg += "✅ خریدها:\n"
                        for i, p in enumerate(pur[-10:], 1):
                            msg += f"{i}. {p}\n"
                    else:
                        msg += "❌ خریدی ندارید\n"
                    if tests:
                        msg += "\n🎁 تست‌ها:\n"
                        for i, t in enumerate(tests[-5:], 1):
                            msg += f"{i}. {t}\n"
                    update.message.reply_text(msg)
                    return
                elif action == "renew":
                    pur = db["users"][uid].get("purchases", [])
                    if not pur:
                        update.message.reply_text("❌ سرویسی برای تمدید ندارید.")
                        return
                    keyboard = []
                    for i, p in enumerate(pur[-5:]):
                        keyboard.append([InlineKeyboardButton(f"🔄 {p[:30]}...", callback_data=f"renew_{i}")])
                    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
                    update.message.reply_text("🔁 سرویس مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                elif action == "profile":
                    user = db["users"][uid]
                    pur_cnt = len(user.get("purchases", []))
                    test_cnt = len(user.get("tests", []))
                    inv_cnt = len(user.get("invited_users", []))
                    bot_user = context.bot.get_me().username
                    link = f"https://t.me/{bot_user}?start={uid}"
                    profile = (
                        f"👤 <b>مشخصات کاربر</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"نام: {update.effective_user.first_name}\n"
                        f"🆔 آیدی: <code>{uid}</code>\n"
                        f"👤 یوزرنیم: @{update.effective_user.username or 'ندارد'}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 خریدها: {pur_cnt}\n"
                        f"🎁 تست‌ها: {test_cnt}\n"
                        f"👥 زیرمجموعه: {inv_cnt}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔗 لینک دعوت:\n<code>{link}</code>"
                    )
                    update.message.reply_text(profile, parse_mode='HTML')
                    return
                elif action == "support":
                    update.message.reply_text(db["texts"]["support"].format(support=db["support"]))
                    return
                elif action == "guide":
                    update.message.reply_text(db["texts"]["guide"].format(guide=db["guide"]))
                    return
                elif action == "invite":
                    bot_user = context.bot.get_me().username
                    link = f"https://t.me/{bot_user}?start={uid}"
                    msg = db["texts"]["invite"].format(link=link)
                    update.message.reply_text(msg)
                    return

        # پنل مدیریت
        if str(uid) == str(ADMIN_ID):
            if text == "⚙️ مدیریت":
                update.message.reply_text("🛠 پنل مدیریت:", reply_markup=get_admin_menu())
                return

            if text == '📋 مدیریت منو':
                menu = "📋 دکمه‌های فعلی:\n"
                for i, btn in enumerate(db["menu_buttons"], 1):
                    menu += f"{i}. {btn['text']} ({btn['action']})\n"
                kb = [['➕ دکمه جدید', '➖ حذف دکمه'], ['🔙 برگشت']]
                update.message.reply_text(menu, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if text == '➕ دکمه جدید':
                user_data[uid] = {'step': 'new_menu_text'}
                update.message.reply_text("📝 متن دکمه جدید را بفرستید:", reply_markup=back_btn())
                return

            if step == 'new_menu_text':
                user_data[uid]['btn_text'] = text
                user_data[uid]['step'] = 'new_menu_action'
                actions = [['buy', 'test', 'services'], ['renew', 'profile', 'support'], ['guide', 'invite'], ['🔙 برگشت']]
                update.message.reply_text("🔧 عملکرد دکمه را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(actions, resize_keyboard=True))
                return

            if step == 'new_menu_action':
                valid = ['buy', 'test', 'services', 'renew', 'profile', 'support', 'guide', 'invite']
                if text in valid:
                    db["menu_buttons"].append({"text": user_data[uid]['btn_text'], "action": text})
                    save_db(db)
                    update.message.reply_text("✅ دکمه اضافه شد.", reply_markup=get_admin_menu())
                    user_data[uid] = {}
                return

            if text == '➖ حذف دکمه':
                kb = []
                for i, btn in enumerate(db["menu_buttons"]):
                    kb.append([InlineKeyboardButton(f"❌ {btn['text']}", callback_data=f"delmenu_{i}")])
                kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("🗑 دکمه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
                return

            if text == '📦 مدیریت دسته‌ها':
                cats = "📦 دسته‌بندی‌ها:\n"
                for i, cat in enumerate(db["categories"].keys(), 1):
                    cats += f"{i}. {cat}\n"
                kb = [['➕ دسته جدید', '➖ حذف دسته'], ['✏️ ویرایش دسته'], ['🔙 برگشت']]
                update.message.reply_text(cats, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if text == '➕ دسته جدید':
                user_data[uid] = {'step': 'new_cat'}
                update.message.reply_text("📝 نام دسته‌بندی جدید را بفرستید:", reply_markup=back_btn())
                return

            if step == 'new_cat':
                if text not in db["categories"]:
                    db["categories"][text] = []
                    save_db(db)
                    update.message.reply_text(f"✅ دسته {text} اضافه شد.", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ این دسته وجود دارد!")
                user_data[uid] = {}
                return

            if text == '➖ حذف دسته':
                kb = []
                for cat in db["categories"].keys():
                    kb.append([InlineKeyboardButton(f"❌ {cat}", callback_data=f"delcat_{cat}")])
                kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("🗑 دسته را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
                return

            if text == '✏️ ویرایش دسته':
                kb = []
                for cat in db["categories"].keys():
                    kb.append([InlineKeyboardButton(f"✏️ {cat}", callback_data=f"editcat_{cat}")])
                kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("✏️ دسته را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
                return

            if text == '➕ پلن جدید':
                cats = list(db["categories"].keys())
                kb = [[c] for c in cats] + [['🔙 برگشت']]
                user_data[uid] = {'step': 'new_plan_cat'}
                update.message.reply_text("📂 دسته را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if step == 'new_plan_cat' and text in db["categories"]:
                user_data[uid] = {'cat': text, 'step': 'new_plan_name'}
                update.message.reply_text("📝 نام پلن:", reply_markup=back_btn())
                return

            if step == 'new_plan_name':
                user_data[uid]['name'] = text
                user_data[uid]['step'] = 'new_plan_vol'
                update.message.reply_text("📦 حجم (مثال: 50GB):")
                return

            if step == 'new_plan_vol':
                user_data[uid]['vol'] = text
                user_data[uid]['step'] = 'new_plan_users'
                update.message.reply_text("👥 تعداد کاربران (عدد یا 'نامحدود'):")
                return

            if step == 'new_plan_users':
                if text.isdigit() or text == "نامحدود":
                    user_data[uid]['users'] = text if text == "نامحدود" else int(text)
                    user_data[uid]['step'] = 'new_plan_days'
                    update.message.reply_text("⏳ مدت (روز):")
                else:
                    update.message.reply_text("❌ عدد یا 'نامحدود' وارد کنید!")
                return

            if step == 'new_plan_days':
                try:
                    user_data[uid]['days'] = int(text)
                    user_data[uid]['step'] = 'new_plan_price'
                    update.message.reply_text("💰 قیمت (هزار تومان):")
                except:
                    update.message.reply_text("❌ عدد وارد کنید!")
                return

            if step == 'new_plan_price':
                try:
                    price = int(text)
                    max_id = 0
                    for p in db["categories"].values():
                        for plan in p:
                            if plan["id"] > max_id:
                                max_id = plan["id"]
                    new = {
                        "id": max_id + 1, "name": user_data[uid]['name'], "price": price,
                        "volume": user_data[uid]['vol'], "days": user_data[uid]['days'],
                        "users": user_data[uid]['users']
                    }
                    db["categories"][user_data[uid]['cat']].append(new)
                    save_db(db)
                    update.message.reply_text("✅ پلن اضافه شد.", reply_markup=get_admin_menu())
                    user_data[uid] = {}
                except:
                    update.message.reply_text("❌ خطا!")
                return

            if text == '➖ حذف پلن':
                kb = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        kb.append([InlineKeyboardButton(f"❌ {cat} - {p['name']}", callback_data=f"delplan_{p['id']}")])
                kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("🗑 پلن را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
                return

            if text == '✏️ ویرایش پلن':
                kb = []
                for cat, plans in db["categories"].items():
                    for p in plans:
                        kb.append([InlineKeyboardButton(f"✏️ {cat} - {p['name']}", callback_data=f"editplan_{p['id']}")])
                kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin")])
                update.message.reply_text("✏️ پلن را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
                return

            if text == '💳 ویرایش کارت':
                kb = [['شماره کارت', 'نام صاحب کارت'], ['🔙 برگشت']]
                cur = f"شماره: {db['card']['number']}\nنام: {db['card']['name']}"
                update.message.reply_text(cur, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if text == 'شماره کارت':
                user_data[uid] = {'step': 'card_num'}
                update.message.reply_text("💳 شماره کارت 16 رقمی:", reply_markup=back_btn())
                return

            if step == 'card_num':
                if text.isdigit() and len(text) == 16:
                    db["card"]["number"] = text
                    save_db(db)
                    update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ نامعتبر!")
                user_data[uid] = {}
                return

            if text == 'نام صاحب کارت':
                user_data[uid] = {'step': 'card_name'}
                update.message.reply_text("👤 نام صاحب کارت:", reply_markup=back_btn())
                return

            if step == 'card_name':
                db["card"]["name"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '👤 ویرایش پشتیبان':
                user_data[uid] = {'step': 'support'}
                update.message.reply_text("👤 آیدی پشتیبان:", reply_markup=back_btn())
                return

            if step == 'support':
                db["support"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '📢 ویرایش کانال':
                user_data[uid] = {'step': 'guide'}
                update.message.reply_text("📢 آیدی کانال آموزش:", reply_markup=back_btn())
                return

            if step == 'guide':
                db["guide"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '🏷 ویرایش برند':
                user_data[uid] = {'step': 'brand'}
                update.message.reply_text("🏷 نام برند:", reply_markup=back_btn())
                return

            if step == 'brand':
                db["brand"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '📝 ویرایش متن‌ها':
                kb = [
                    ['خوش‌آمدگویی', 'پشتیبانی', 'آموزش'],
                    ['تست', 'عضویت', 'دعوت'],
                    ['پرداخت', 'تعمیرات', 'کانفیگ'],
                    ['🔙 برگشت']
                ]
                update.message.reply_text("📝 کدام متن؟", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            text_map = {
                'خوش‌آمدگویی': 'welcome', 'پشتیبانی': 'support', 'آموزش': 'guide',
                'تست': 'test', 'عضویت': 'force', 'دعوت': 'invite',
                'پرداخت': 'payment_info', 'تعمیرات': 'maintenance', 'کانفیگ': 'config_sent'
            }
            if text in text_map:
                user_data[uid] = {'step': f'edit_{text_map[text]}'}
                cur = db["texts"][text_map[text]]
                update.message.reply_text(f"📝 متن فعلی:\n{cur}\n\nمتن جدید:", reply_markup=back_btn())
                return

            if step and step.startswith('edit_'):
                key = step.replace('edit_', '')
                db["texts"][key] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '🔒 عضویت اجباری':
                kb = [['✅ فعال', '❌ غیرفعال'], ['🔗 تنظیم لینک'], ['🔙 برگشت']]
                status = "✅ فعال" if db["force_join"]["enabled"] else "❌ غیرفعال"
                channel = db["force_join"]["channel_username"] or "ندارد"
                update.message.reply_text(f"🔒 وضعیت: {status}\nکانال: {channel}", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if text == '✅ فعال':
                if db["force_join"]["channel_link"]:
                    db["force_join"]["enabled"] = True
                    save_db(db)
                    update.message.reply_text("✅ فعال شد.", reply_markup=get_admin_menu())
                else:
                    update.message.reply_text("❌ ابتدا لینک را تنظیم کنید.")
                return

            if text == '❌ غیرفعال':
                db["force_join"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ غیرفعال شد.", reply_markup=get_admin_menu())
                return

            if text == '🔗 تنظیم لینک':
                user_data[uid] = {'step': 'set_link'}
                update.message.reply_text("🔗 لینک کانال:", reply_markup=back_btn())
                return

            if step == 'set_link':
                db["force_join"]["channel_link"] = text
                if 't.me/' in text:
                    username = text.split('t.me/')[-1].split('/')[0].replace('@', '')
                    db["force_join"]["channel_username"] = f"@{username}"
                    try:
                        chat = context.bot.get_chat(f"@{username}")
                        db["force_join"]["channel_id"] = str(chat.id)
                    except:
                        pass
                save_db(db)
                update.message.reply_text("✅ لینک ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '🔛 وضعیت ربات':
                kb = [['✅ روشن', '❌ خاموش'], ['✏️ متن تعمیرات'], ['🔙 برگشت']]
                status = "✅ روشن" if db["bot_status"]["enabled"] else "❌ خاموش"
                update.message.reply_text(f"🔛 وضعیت: {status}", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                return

            if text == '✅ روشن':
                db["bot_status"]["enabled"] = True
                save_db(db)
                update.message.reply_text("✅ روشن شد.", reply_markup=get_admin_menu())
                return

            if text == '❌ خاموش':
                db["bot_status"]["enabled"] = False
                save_db(db)
                update.message.reply_text("✅ خاموش شد.", reply_markup=get_admin_menu())
                return

            if text == '✏️ متن تعمیرات':
                user_data[uid] = {'step': 'edit_maintenance'}
                cur = db["bot_status"]["message"]
                update.message.reply_text(f"📝 متن فعلی:\n{cur}\n\nمتن جدید:", reply_markup=back_btn())
                return

            if step == 'edit_maintenance':
                db["bot_status"]["message"] = text
                save_db(db)
                update.message.reply_text("✅ ذخیره شد.", reply_markup=get_admin_menu())
                user_data[uid] = {}
                return

            if text == '📊 آمار':
                total = len(db["users"])
                pur = sum(len(u.get("purchases", [])) for u in db["users"].values())
                tests = sum(len(u.get("tests", [])) for u in db["users"].values())
                today = datetime.now().strftime("%Y-%m-%d")
                today_users = sum(1 for u in db["users"].values() if u.get("date", "").startswith(today))
                stats = f"📊 آمار\n━━━━━━━━━━\n👥 کل: {total}\n🆕 امروز: {today_users}\n💰 خرید: {pur}\n🎁 تست: {tests}"
                update.message.reply_text(stats)
                return

            if text == '📦 بکاپ‌گیری':
                try:
                    files = []
                    # Users
                    with open('users_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"users": db["users"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    files.append(('users_backup.json', '👤 کاربران'))
                    # Plans
                    with open('plans_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"categories": db["categories"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    files.append(('plans_backup.json', '📦 پلن‌ها'))
                    # Card
                    with open('card_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"card": db["card"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    files.append(('card_backup.json', '💳 کارت'))
                    # Texts
                    with open('texts_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"texts": db["texts"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    files.append(('texts_backup.json', '📝 متن‌ها'))
                    # Menu
                    with open('menu_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({"menu": db["menu_buttons"], "date": str(datetime.now())}, f, ensure_ascii=False, indent=4)
                    files.append(('menu_backup.json', '📋 منو'))
                    # Settings
                    with open('settings_backup.json', 'w', encoding='utf-8') as f:
                        json.dump({
                            "brand": db["brand"], "support": db["support"], "guide": db["guide"],
                            "force_join": db["force_join"], "bot_status": db["bot_status"], "date": str(datetime.now())
                        }, f, ensure_ascii=False, indent=4)
                    files.append(('settings_backup.json', '⚙️ تنظیمات'))

                    update.message.reply_text("📦 آماده‌سازی بکاپ...")
                    for fname, desc in files:
                        with open(fname, 'rb') as f:
                            context.bot.send_document(uid, f, filename=fname, caption=f"📁 {desc}")
                        os.remove(fname)
                    update.message.reply_text("✅ بکاپ ارسال شد.")
                except Exception as e:
                    update.message.reply_text(f"❌ خطا: {e}")
                return

            if text == '🔄 بازیابی بکاپ':
                user_data[uid] = {'step': 'restore', 'files': {}, 'next': 'users_backup.json'}
                msg = (
                    "🔄 بازیابی بکاپ\n━━━━━━━━━━\n"
                    "ترتیب ارسال:\n"
                    "1️⃣ users_backup.json (کاربران)\n"
                    "2️⃣ plans_backup.json (پلن‌ها)\n"
                    "3️⃣ card_backup.json (کارت)\n"
                    "4️⃣ texts_backup.json (متن‌ها)\n"
                    "5️⃣ menu_backup.json (منو)\n"
                    "6️⃣ settings_backup.json (تنظیمات)"
                )
                update.message.reply_text(msg)
                return

            if text == '📨 ارسال همگانی':
                user_data[uid] = {'step': 'broadcast'}
                update.message.reply_text("📨 پیام همگانی را بفرستید:", reply_markup=back_btn())
                return

            if step == 'broadcast':
                suc, fail = 0, 0
                for uid2 in db["users"]:
                    try:
                        context.bot.send_message(int(uid2), text)
                        suc += 1
                    except:
                        fail += 1
                update.message.reply_text(f"✅ ارسال شد.\n✓ موفق: {suc}\n✗ ناموفق: {fail}")
                user_data[uid] = {}
                return

            if step == 'send_config':
                target = user_data[uid]['target']
                name = user_data[uid]['name']
                vol = user_data[uid].get('vol', 'نامحدود')
                days = user_data[uid].get('days', '۳۰')
                
                record = f"🚀 {name} | {vol} | {datetime.now().strftime('%Y-%m-%d')}"
                if str(target) not in db["users"]:
                    db["users"][str(target)] = {"purchases": []}
                if "purchases" not in db["users"][str(target)]:
                    db["users"][str(target)]["purchases"] = []
                db["users"][str(target)]["purchases"].append(record)
                save_db(db)
                
                msg = db["texts"]["config_sent"].format(name=name, days=days, volume=vol, config=update.message.text)
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("📚 آموزش", url=f"https://t.me/{db['guide'].replace('@', '')}")
                ]])
                context.bot.send_message(int(target), msg, parse_mode='HTML', reply_markup=btn)
                update.message.reply_text("✅ کانفیگ ارسال شد.")
                user_data[uid] = {}
                return

        if step == 'wait_name':
            user_data[uid]['account'] = text
            p = user_data[uid]['plan']
            price = p['price'] * 1000
            users_text = f"👥 {p['users']} کاربره" if p['users'] != "نامحدود" and p['users'] > 1 else "👤 تک کاربره"
            if p['users'] == "نامحدود":
                users_text = "👥 نامحدود"
            msg = db["texts"]["payment_info"].format(
                account=text, plan_name=p['name'], volume=p['volume'],
                users_text=users_text, days=p['days'], price=price,
                card_number=db['card']['number'], card_name=db['card']['name']
            )
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 ارسال فیش", callback_data="receipt"),
                InlineKeyboardButton("🔙 برگشت", callback_data="back_to_cats")
            ]])
            update.message.reply_text(msg, parse_mode='HTML', reply_markup=btn)

    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ خطا!")

def handle_cb(update, context):
    try:
        q = update.callback_query
        uid = str(q.from_user.id)
        q.answer()

        if q.data == "join_check":
            if check_join(uid, context):
                q.message.delete()
                start(update, context)
            else:
                q.message.reply_text("❌ هنوز عضو نشده‌اید.")
            return

        if q.data == "back_to_main":
            q.message.delete()
            start(update, context)
            return

        if q.data == "back_to_admin":
            q.message.delete()
            context.bot.send_message(uid, "🛠 پنل مدیریت:", reply_markup=get_admin_menu())
            return

        if q.data == "back_to_cats":
            q.message.delete()
            cats = list(db["categories"].keys())
            kb = []
            for cat in cats:
                kb.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
            kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
            context.bot.send_message(uid, "📂 دسته را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))
            return

        if q.data.startswith("cat_"):
            cat = q.data[4:]
            plans = db["categories"].get(cat, [])
            if not plans:
                q.message.reply_text("❌ پلنی نیست.")
                return
            kb = []
            for p in plans:
                price = p['price'] * 1000
                kb.append([InlineKeyboardButton(f"{p['name']} - {price:,} تومان", callback_data=f"buy_{p['id']}")])
            kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_cats")])
            q.message.edit_text(f"📦 {cat}", reply_markup=InlineKeyboardMarkup(kb))
            return

        if q.data.startswith("buy_"):
            pid = int(q.data.split("_")[1])
            plan = None
            for cat, plans in db["categories"].items():
                for p in plans:
                    if p["id"] == pid:
                        plan = p
                        break
                if plan:
                    break
            if plan:
                user_data[uid] = {'step': 'wait_name', 'plan': plan}
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_cats")]])
                q.message.edit_text("📝 نام اکانت را وارد کنید:", reply_markup=kb)
            else:
                q.message.reply_text("❌ پلن یافت نشد.")
            return

        if q.data == "receipt":
            if uid in user_data and 'plan' in user_data[uid] and 'account' in user_data[uid]:
                user_data[uid]['step'] = 'wait_photo'
                q.message.reply_text("📸 عکس فیش را بفرستید:", reply_markup=back_btn())
            else:
                q.message.reply_text("❌ اطلاعات ناقص.")
            return

        if q.data.startswith("renew_"):
            try:
                idx = int(q.data.split("_")[1])
                pur = db["users"][uid].get("purchases", [])
                if idx < len(pur):
                    service = pur[idx]
                    vol = None
                    for v in ["10GB","20GB","30GB","40GB","50GB","60GB","100GB"]:
                        if v in service:
                            vol = v
                            break
                    plan = None
                    for cat, plans in db["categories"].items():
                        for p in plans:
                            if p['volume'] == vol:
                                plan = p
                                break
                        if plan:
                            break
                    if plan:
                        user_data[uid] = {'step': 'wait_name', 'plan': plan}
                        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_cats")]])
                        q.message.edit_text(f"🔄 تمدید\n💰 {plan['price']*1000:,} تومان\n📝 نام اکانت:", reply_markup=kb)
                    else:
                        q.message.reply_text("❌ پلن مشابه یافت نشد.")
                else:
                    q.message.reply_text("❌ سرویس یافت نشد.")
            except:
                q.message.reply_text("❌ خطا.")
            return

        # مدیریت
        if q.data.startswith("delmenu_"):
            if str(uid) == str(ADMIN_ID):
                idx = int(q.data.split("_")[1])
                if 0 <= idx < len(db["menu_buttons"]):
                    del db["menu_buttons"][idx]
                    save_db(db)
                    q.message.edit_text("✅ حذف شد.")
            return

        if q.data.startswith("delcat_"):
            if str(uid) == str(ADMIN_ID):
                cat = q.data[7:]
                if cat in db["categories"] and len(db["categories"][cat]) == 0:
                    del db["categories"][cat]
                    save_db(db)
                    q.message.edit_text(f"✅ {cat} حذف شد.")
                else:
                    q.message.edit_text("❌ دسته خالی نیست.")
            return

        if q.data.startswith("editcat_"):
            if str(uid) == str(ADMIN_ID):
                cat = q.data[8:]
                user_data[uid] = {'step': 'edit_cat', 'old_cat': cat}
                q.message.edit_text(f"📝 نام جدید برای {cat}:")
            return

        if q.data.startswith("delplan_"):
            if str(uid) == str(ADMIN_ID):
                pid = int(q.data.split("_")[1])
                for cat, plans in db["categories"].items():
                    for i, p in enumerate(plans):
                        if p["id"] == pid:
                            del plans[i]
                            save_db(db)
                            q.message.edit_text("✅ حذف شد.")
                            return
                q.message.edit_text("❌ یافت نشد.")
            return

        if q.data.startswith("test_"):
            if str(uid) == str(ADMIN_ID):
                parts = q.data.split("_")
                if len(parts) >= 3:
                    target, name = parts[1], parts[2]
                    user_data[uid] = {'step': 'send_config', 'target': target, 'name': f"تست {name}", 'vol': '۳ ساعت', 'days': '۳'}
                    context.bot.send_message(uid, f"📨 کانفیگ تست برای {name}:")
                    q.message.edit_reply_markup()
            return

        if q.data.startswith("send_"):
            if str(uid) == str(ADMIN_ID):
                target = q.data.split("_")[1]
                cap = q.message.caption or ""
                name, vol = "کاربر", "نامحدود"
                for line in cap.split('\n'):
                    if "اکانت" in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            name = parts[1].strip()
                    elif "📦" in line:
                        vol = line.split('📦')[-1].strip()
                user_data[uid] = {'step': 'send_config', 'target': target, 'name': name, 'vol': vol, 'days': '۳۰'}
                context.bot.send_message(uid, f"📨 کانفیگ {name}:")
                q.message.edit_reply_markup()
            return

    except Exception as e:
        logger.error(f"CB Error: {e}")

def handle_photo(update, context):
    try:
        uid = str(update.effective_user.id)
        if user_data.get(uid, {}).get('step') == 'wait_photo':
            if 'plan' not in user_data[uid] or 'account' not in user_data[uid]:
                update.message.reply_text("❌ اطلاعات ناقص.")
                return
            p = user_data[uid]['plan']
            acc = user_data[uid]['account']
            price = p['price'] * 1000
            cap = (
                f"💰 فیش جدید\n━━━━━━━━━━━━━━\n"
                f"👤 {update.effective_user.first_name}\n🆔 {uid}\n"
                f"👤 @{update.effective_user.username or 'ندارد'}\n"
                f"━━━━━━━━━━━━━━\n📦 {p['name']}\n📊 {p['volume']}\n"
                f"💰 {price:,} تومان\n👤 اکانت: {acc}\n━━━━━━━━━━━━━━"
            )
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"send_{uid}")]])
            context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=cap, parse_mode='HTML', reply_markup=btn)
            update.message.reply_text("✅ فیش ارسال شد.", reply_markup=get_main_menu(uid))
            del user_data[uid]
    except Exception as e:
        logger.error(f"Photo Error: {e}")

def handle_doc(update, context):
    try:
        uid = str(update.effective_user.id)
        if uid != str(ADMIN_ID):
            return
        step = user_data.get(uid, {})
        if step.get('step') != 'restore':
            return
        doc = update.message.document
        if not doc.file_name.endswith('.json'):
            update.message.reply_text("❌ فایل JSON بفرست.")
            return
        expected = step.get('next')
        if doc.file_name != expected:
            update.message.reply_text(f"❌ باید {expected} بفرستی.")
            return
        file = context.bot.get_file(doc.file_id)
        file.download(doc.file_name)
        with open(doc.file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if doc.file_name == 'users_backup.json':
            db["users"] = data["users"]
            step['next'] = 'plans_backup.json'
            msg = "✅ کاربران بازیابی شد. حالا plans_backup.json رو بفرست."
        elif doc.file_name == 'plans_backup.json':
            db["categories"] = data["categories"]
            step['next'] = 'card_backup.json'
            msg = "✅ پلن‌ها بازیابی شد. حالا card_backup.json رو بفرست."
        elif doc.file_name == 'card_backup.json':
            db["card"] = data["card"]
            step['next'] = 'texts_backup.json'
            msg = "✅ کارت بازیابی شد. حالا texts_backup.json رو بفرست."
        elif doc.file_name == 'texts_backup.json':
            db["texts"] = data["texts"]
            step['next'] = 'menu_backup.json'
            msg = "✅ متن‌ها بازیابی شد. حالا menu_backup.json رو بفرست."
        elif doc.file_name == 'menu_backup.json':
            db["menu_buttons"] = data["menu"]
            step['next'] = 'settings_backup.json'
            msg = "✅ منو بازیابی شد. حالا settings_backup.json رو بفرست."
        elif doc.file_name == 'settings_backup.json':
            db["brand"] = data["brand"]
            db["support"] = data["support"]
            db["guide"] = data["guide"]
            db["force_join"] = data["force_join"]
            db["bot_status"] = data["bot_status"]
            save_db(db)
            update.message.reply_text("✅ همه چیز بازیابی شد. ری‌استارت...")
            user_data[uid] = {}
            os._exit(0)
            return
        os.remove(doc.file_name)
        update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Doc Error: {e}")
        update.message.reply_text(f"❌ خطا: {e}")

def main():
    try:
        logger.info("🚀 Starting bot...")
        Thread(target=run_web, daemon=True).start()
        
        # Signal handling
        def handler(sig, frame):
            logger.info("🛑 Stopping...")
            os._exit(0)
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
        
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(MessageHandler(Filters.photo, handle_photo))
        dp.add_handler(MessageHandler(Filters.document, handle_doc))
        dp.add_handler(CallbackQueryHandler(handle_cb))
        
        # Clear old updates
        try:
            updates = updater.bot.get_updates(offset=-1)
            if updates:
                last = updates[-1].update_id
                updater.bot.get_updates(offset=last + 1)
        except:
            pass
        
        updater.start_polling(timeout=30, clean=True)
        logger.info("✅ Bot is running!")
        updater.idle()
    except Exception as e:
        logger.error(f"Fatal: {e}")

if __name__ == '__main__':
    main()