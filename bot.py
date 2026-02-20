import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
import random
from datetime import datetime, timedelta

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8587672080:AAHlGubM0ah_c1DTbYyIHh_tmRPvHxiSz68"

# توكن المشرف (حسابك)
ADMIN_ID = "8491314169"  # ضع معرف تليجرام الخاص بك هنا

# ملفات تخزين البيانات
APPS_FILE = "apps_data.json"
USERS_FILE = "users_data.json"

# تحميل البيانات
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# القنوات المطلوب الاشتراك فيها
REQUIRED_CHANNELS = [
    {'username': '@gdch6', 'name': 'قناة gdch6 📢'},
    {'username': '@OfficalDSMods', 'name': 'قناة OfficalDSMods 📢'},
    {'username': '@torki02', 'name': 'قناة torki02 📢'}
]

# قوالب التطبيقات مع التكلفة
APP_TEMPLATES = {
    'business_card': {
        'name': '📇 بطاقة أعمال',
        'description': 'تطبيق بطاقة تعريفية لشخص أو شركة',
        'cost': 10,
        'features': ['صورة شخصية', 'معلومات الاتصال', 'روابط اجتماعية', 'موقع على الخريطة']
    },
    'store': {
        'name': '🛍️ متجر بسيط',
        'description': 'تطبيق متجر إلكتروني بمنتجات محدودة',
        'cost': 25,
        'features': ['عرض المنتجات', 'سلة تسوق', 'واتساب للطلب', 'صور المنتجات']
    },
    'portfolio': {
        'name': '🎨 معرض أعمال',
        'description': 'تطبيق لعرض أعمالك الفنية أو مشاريعك',
        'cost': 15,
        'features': ['معرض صور', 'فيديو تعريفي', 'التواصل', 'شهادة خبرات']
    },
    'menu': {
        'name': '🍽️ قائمة طعام',
        'description': 'تطبيق منيو لمطعم أو مقهى',
        'cost': 20,
        'features': ['قسمة الأصناف', 'أسعار', 'صور الأطباق', 'طلب أونلاين']
    }
}

# جلسات المستخدمين
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users_data = load_data(USERS_FILE)
    
    # تسجيل المستخدم جديد إذا لم يكن موجوداً
    if user_id not in users_data:
        # المشرف (حسابك) يحصل على 99999 عملة
        if user_id == ADMIN_ID:
            users_data[user_id] = {
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'coins': 99999,
                'apps_created': 0,
                'joined_channels': [],
                'last_daily': None,
                'referrals': [],
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            users_data[user_id] = {
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'coins': 0,
                'apps_created': 0,
                'joined_channels': [],
                'last_daily': None,
                'referrals': [],
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        save_data(users_data, USERS_FILE)
    
    # التحقق من الاشتراك في القنوات
    if not await check_channels_subscription(update, context):
        return
    
    coins = users_data[user_id]['coins']
    
    welcome = f"""
🎯 **مرحباً بك في بوت صانع التطبيقات!**

💰 **رصيدك الحالي:** {coins} عملة

**ما يمكنك فعله:**
📱 إنشاء تطبيقات احترافية بدون برمجة
✨ اختر من القوالب المتاحة
💎 اربح عملات مجانية بالاشتراك في القنوات

**طريقة الحصول على العملات:**
✅ الاشتراك في القنوات: +10 عملات لكل قناة
✅ الدعوة للأصدقاء: +20 عملة لكل صديق
✅ المكافأة اليومية: +5 عملات كل يوم
    """
    
    keyboard = [
        [InlineKeyboardButton("🚀 إنشاء تطبيق", callback_data="create_app")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="show_balance")],
        [InlineKeyboardButton("📋 تطبيقاتي", callback_data="my_apps")],
        [InlineKeyboardButton("💎 ربح عملات", callback_data="earn_coins")],
        [InlineKeyboardButton("🎁 المكافأة اليومية", callback_data="daily_reward")],
        [InlineKeyboardButton("👥 دعوة الأصدقاء", callback_data="referral")]
    ]
    
    # إضافة زر للمشرف فقط
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚡ لوحة المشرف", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)

async def check_channels_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من اشتراك المستخدم في القنوات المطلوبة"""
    user_id = str(update.effective_user.id)
    users_data = load_data(USERS_FILE)
    
    # المشرف (حسابك) لا يحتاج للتحقق
    if user_id == ADMIN_ID:
        return True
    
    not_joined = []
    
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['username'], user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    
    if not_joined:
        message = "🔒 **للاستمرار في استخدام البوت، يجب الاشتراك في هذه القنوات أولاً:**\n\n"
        keyboard = []
        
        for channel in not_joined:
            message += f"• {channel['name']}\n"
            keyboard.append([InlineKeyboardButton(f"✅ اشترك في {channel['name']}", url=f"https://t.me/{channel['username'][1:]}")])
        
        keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        return False
    
    return True

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = str(update.effective_user.id)
    
    # التحقق من الاشتراك في القنوات
    if not await check_channels_subscription(update, context):
        return
    
    if data == "show_balance":
        await show_balance(query, user_id)
    
    elif data == "earn_coins":
        await earn_coins_menu(query)
    
    elif data == "daily_reward":
        await daily_reward(query, user_id)
    
    elif data == "referral":
        await referral_menu(query, user_id)
    
    elif data == "create_app":
        await show_app_templates(query, user_id)
    
    elif data == "my_apps":
        await list_user_apps(query, user_id)
    
    elif data == "check_subscription":
        await check_subscription_after_join(query, context, user_id)
    
    elif data.startswith("select_template_"):
        template = data.replace("select_template_", "")
        await check_and_start_creation(query, user_id, template)
    
    elif data == "admin_panel" and user_id == ADMIN_ID:
        await admin_panel(query)
    
    elif data == "add_coins" and user_id == ADMIN_ID:
        await add_coins_menu(query)
    
    elif data == "stats" and user_id == ADMIN_ID:
        await show_stats(query)

async def show_balance(query, user_id):
    users_data = load_data(USERS_FILE)
    coins = users_data.get(user_id, {}).get('coins', 0)
    apps = users_data.get(user_id, {}).get('apps_created', 0)
    
    message = f"""
💰 **محفظة العملات**

**رصيدك الحالي:** {coins} عملة
**التطبيقات المنشأة:** {apps} تطبيق

**طرق زيادة الرصيد:**
• الاشتراك في القنوات: +10 عملات لكل قناة
• دعوة الأصدقاء: +20 عملة لكل صديق
• المكافأة اليومية: +5 عملات يومياً
    """
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def earn_coins_menu(query):
    message = "💎 **اختر طريقة للحصول على العملات:**\n\n"
    
    keyboard = [
        [InlineKeyboardButton("📢 الاشتراك في القنوات", callback_data="subscribe_channels")],
        [InlineKeyboardButton("👥 دعوة الأصدقاء", callback_data="referral")],
        [InlineKeyboardButton("🎁 المكافأة اليومية", callback_data="daily_reward")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def subscribe_channels(query):
    message = "📢 **اشترك في هذه القنوات لتحصل على عملات مجانية:**\n\n"
    keyboard = []
    
    for channel in REQUIRED_CHANNELS:
        message += f"• {channel['name']}\n"
        keyboard.append([InlineKeyboardButton(f"✅ اشترك في {channel['name']}", url=f"https://t.me/{channel['username'][1:]}")])
    
    keyboard.append([InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_subscription_reward")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="earn_coins")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def check_subscription_after_join(query, context, user_id):
    users_data = load_data(USERS_FILE)
    joined_channels = users_data[user_id].get('joined_channels', [])
    
    new_channels = []
    for channel in REQUIRED_CHANNELS:
        if channel['username'] not in joined_channels:
            try:
                member = await context.bot.get_chat_member(chat_id=channel['username'], user_id=user_id)
                if member.status not in ['left', 'kicked']:
                    new_channels.append(channel)
            except:
                pass
    
    if new_channels:
        coins_added = len(new_channels) * 10
        users_data[user_id]['coins'] += coins_added
        for channel in new_channels:
            users_data[user_id]['joined_channels'].append(channel['username'])
        save_data(users_data, USERS_FILE)
        
        await query.message.edit_text(
            f"✅ تم إضافة {coins_added} عملة إلى رصيدك!\n"
            f"رصيدك الحالي: {users_data[user_id]['coins']} عملة"
        )
    else:
        await query.message.edit_text(
            "❌ لم يتم العثور على اشتراكات جديدة.\n"
            "تأكد من الاشتراك في القنوات ثم حاول مرة أخرى."
        )
    
    # عرض خيارات إضافية
    keyboard = [
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_reply_markup(reply_markup)

async def daily_reward(query, user_id):
    users_data = load_data(USERS_FILE)
    last_daily = users_data[user_id].get('last_daily')
    
    if last_daily:
        last_date = datetime.strptime(last_daily, '%Y-%m-%d')
        if datetime.now().date() == last_date.date():
            await query.message.edit_text(
                "❌ لقد حصلت على مكافأتك اليومية بالفعل!\n"
                "عد غداً للحصول على مكافأة جديدة."
            )
            return
    
    # إضافة المكافأة
    users_data[user_id]['coins'] += 5
    users_data[user_id]['last_daily'] = datetime.now().strftime('%Y-%m-%d')
    save_data(users_data, USERS_FILE)
    
    await query.message.edit_text(
        f"🎁 تم إضافة 5 عملات إلى رصيدك!\n"
        f"رصيدك الحالي: {users_data[user_id]['coins']} عملة\n\n"
        f"عد غداً للحصول على مكافأة جديدة!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_reply_markup(reply_markup)

async def referral_menu(query, user_id):
    referral_link = f"https://t.me/{(await query.message.bot.get_me()).username}?start={user_id}"
    
    message = f"""
👥 **دعوة الأصدقاء**

لكل صديق تدعوه وينضم للبوت عبر رابطك، تحصل على **20 عملة**!

**رابط الدعوة الخاص بك:**
`{referral_link}`

**كيف تعمل الدعوة؟**
1. شارك الرابط مع أصدقائك
2. عندما ينضم صديق عبر الرابط، تحصل على 20 عملة
3. كلما زاد عدد أصدقائك، زاد رصيدك!
    """
    
    keyboard = [
        [InlineKeyboardButton("📤 مشاركة الرابط", switch_inline_query=f"انضم لبوت صناعة التطبيقات الرائع! {referral_link}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def show_app_templates(query, user_id):
    users_data = load_data(USERS_FILE)
    coins = users_data[user_id]['coins']
    
    message = f"💰 **رصيدك:** {coins} عملة\n\n"
    message += "**اختر نوع التطبيق الذي تريد إنشاءه:**\n\n"
    
    keyboard = []
    for key, template in APP_TEMPLATES.items():
        can_afford = "✅" if coins >= template['cost'] else "❌"
        message += f"{template['name']} - {template['cost']} عملة {can_afford}\n"
        message += f"📝 {template['description']}\n"
        message += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        
        button_text = f"{template['name']} ({template['cost']} عملة)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_template_{key}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def check_and_start_creation(query, user_id, template):
    users_data = load_data(USERS_FILE)
    coins = users_data[user_id]['coins']
    cost = APP_TEMPLATES[template]['cost']
    
    if coins < cost:
        await query.message.edit_text(
            f"❌ **رصيدك غير كافٍ!**\n\n"
            f"تحتاج: {cost} عملة\n"
            f"رصيدك: {coins} عملة\n\n"
            f"احصل على عملات إضافية من خلال:\n"
            f"• الاشتراك في القنوات\n"
            f"• دعوة الأصدقاء\n"
            f"• المكافأة اليومية",
            parse_mode='Markdown'
        )
        
        keyboard = [
            [InlineKeyboardButton("💎 احصل على عملات", callback_data="earn_coins")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="create_app")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_reply_markup(reply_markup)
        return
    
    # خصم العملات
    users_data[user_id]['coins'] -= cost
    save_data(users_data, USERS_FILE)
    
    # بدء عملية إنشاء التطبيق
    user_sessions[user_id] = {
        'step': 'app_name',
        'template': template,
        'data': {}
    }
    
    await query.message.edit_text(
        f"✅ تم خصم {cost} عملة\n"
        f"رصيدك المتبقي: {users_data[user_id]['coins']} عملة\n\n"
        f"الخطوة 1/3: **أدخل اسم التطبيق**",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # التحقق من الاشتراك في القنوات
    if not await check_channels_subscription(update, context):
        return
    
    if user_id not in user_sessions:
        return
    
    step = user_sessions[user_id].get('step')
    text = update.message.text
    
    if step == 'app_name':
        user_sessions[user_id]['data']['app_name'] = text
        user_sessions[user_id]['step'] = 'app_content'
        await update.message.reply_text(
            f"✅ تم حفظ اسم التطبيق\n\n"
            f"الخطوة 2/3: **أدخل محتوى التطبيق**\n"
            f"أدخل المعلومات التي تريد ظهورها في التطبيق\n"
            f"(كل معلومة في سطر منفصل)"
        )
    
    elif step == 'app_content':
        user_sessions[user_id]['data']['content'] = text.split('\n')
        user_sessions[user_id]['step'] = 'confirm'
        
        template = user_sessions[user_id]['template']
        template_info = APP_TEMPLATES[template]
        
        summary = f"""
📱 **ملخص التطبيق:**

**النوع:** {template_info['name']}
**الاسم:** {user_sessions[user_id]['data']['app_name']}
**المحتوى:** {len(user_sessions[user_id]['data']['content'])} عناصر

✅ تم إنشاء تطبيقك بنجاح!
سيتم تحضير ملف التطبيق...
        """
        
        # محاكاة إنشاء التطبيق
        import asyncio
        await update.message.reply_text(summary)
        await asyncio.sleep(2)
        
        # تحديث عدد التطبيقات
        users_data = load_data(USERS_FILE)
        users_data[user_id]['apps_created'] = users_data[user_id].get('apps_created', 0) + 1
        save_data(users_data, USERS_FILE)
        
        # رسالة النجاح مع رابط تحميل وهمي
        success = f"""
🎉 **تم إنشاء تطبيقك بنجاح!**

**اسم التطبيق:** {user_sessions[user_id]['data']['app_name']}
**نوع التطبيق:** {template_info['name']}

📥 **رابط التحميل:** [اضغط هنا](https://example.com/download)

⚠️ ملاحظة: هذا مجرد مثال، في النسخة الحقيقية سيتم إنشاء ملف APK حقيقي
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 إنشاء تطبيق آخر", callback_data="create_app")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="show_balance")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(success, parse_mode='Markdown', reply_markup=reply_markup)
        
        # تنظيف الجلسة
        del user_sessions[user_id]

async def admin_panel(query):
    message = """
⚡ **لوحة تحكم المشرف**

**الإجراءات المتاحة:**
• إضافة عملات لأي مستخدم
• عرض إحصائيات البوت
• إدارة القنوات
• عرض جميع المستخدمين
    """
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة عملات", callback_data="add_coins")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 إدارة القنوات", callback_data="manage_channels")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def add_coins_menu(query):
    await query.message.edit_text(
        "➕ **إضافة عملات لمستخدم**\n\n"
        "أرسل معرف المستخدم وعدد العملات:\n"
        "مثال: `@username 100`\n"
        "أو: `123456789 50`",
        parse_mode='Markdown'
    )

async def show_stats(query):
    users_data = load_data(USERS_FILE)
    apps_data = load_data(APPS_FILE)
    
    total_users = len(users_data)
    total_apps = sum(user.get('apps_created', 0) for user in users_data.values())
    total_coins = sum(user.get('coins', 0) for user in users_data.values())
    
    message = f"""
📊 **إحصائيات البوت**

👥 **المستخدمين:** {total_users}
📱 **التطبيقات المنشأة:** {total_apps}
💰 **إجمالي العملات:** {total_coins}

**أكثر المستخدمين نشاطاً:**
    """
    
    # ترتيب المستخدمين حسب عدد التطبيقات
    top_users = sorted(users_data.items(), key=lambda x: x[1].get('apps_created', 0), reverse=True)[:5]
    
    for user_id, data in top_users:
        name = data.get('first_name', 'مستخدم')
        apps = data.get('apps_created', 0)
        coins = data.get('coins', 0)
        message += f"\n• {name}: {apps} تطبيق | {coins} عملة"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # إعادة عرض القائمة الرئيسية
    await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 بوت صانع التطبيقات مع نظام العملات يعمل...")
    print(f"👑 المشرف (حسابك) لديه 99999 عملة")
    app.run_polling()

if __name__ == '__main__':
    main()