import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
import requests
from datetime import datetime
import random
import string
import io
import sys
import traceback

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# معالجة الأخطاء غير المتوقعة
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("❌ خطأ غير متوقع:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    logger.error("خطأ غير متوقع", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

TOKEN = "8587672080:AAHlGubM0ah_c1DTbYyIHh_tmRPvHxiSz68"
ADMIN_ID = "8491314169"

# ملفات التخزين
APPS_FILE = "apps_data.json"
USERS_FILE = "users_data.json"
TEMPLATES_FILE = "templates_data.json"

# إعدادات Thunkable
THUNKABLE_API_URL = "https://api.thunkable.com/v1"
THUNKABLE_API_KEY = "YOUR_THUNKABLE_API_KEY"
THUNKABLE_PROJECT_ID = "YOUR_PROJECT_ID"

# تحميل البيانات
def load_data(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في تحميل {filename}: {e}")
    return {}

def save_data(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"خطأ في حفظ {filename}: {e}")

# القنوات المطلوبة
REQUIRED_CHANNELS = [
    {'username': '@gdch6', 'name': 'قناة gdch6 📢'},
    {'username': '@OfficalDSMods', 'name': 'قناة OfficalDSMods 📢'},
    {'username': '@torki02', 'name': 'قناة torki02 📢'}
]

# قوالب التطبيقات المتقدمة
APP_TEMPLATES = {
    'business_card': {
        'name': '📇 بطاقة أعمال احترافية',
        'description': 'تطبيق بطاقة تعريفية متكاملة مع صور ومعلومات التواصل',
        'cost': 10,
        'icon': '📇',
        'category': 'أعمال',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'required': True},
            {'name': 'الاسم الكامل', 'type': 'text', 'required': True},
            {'name': 'المسمى الوظيفي', 'type': 'text', 'required': True},
            {'name': 'رقم الهاتف', 'type': 'phone', 'required': True},
            {'name': 'البريد الإلكتروني', 'type': 'email', 'required': True},
            {'name': 'رابط واتساب', 'type': 'url', 'required': False},
            {'name': 'رابط تليجرام', 'type': 'url', 'required': False},
            {'name': 'رابط انستغرام', 'type': 'url', 'required': False},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'صورة شخصية', 'type': 'image', 'required': False}
        ]
    },
    'store': {
        'name': '🛍️ متجر إلكتروني متكامل',
        'description': 'تطبيق متجر بمنتجات وسلة تسوق وواتساب للطلب',
        'cost': 25,
        'icon': '🛍️',
        'category': 'تسوق',
        'fields': [
            {'name': 'اسم المتجر', 'type': 'text', 'required': True},
            {'name': 'وصف المتجر', 'type': 'textarea', 'required': True},
            {'name': 'المنتجات', 'type': 'products', 'required': True},
            {'name': 'رقم واتساب للطلبات', 'type': 'phone', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#27ae60'},
            {'name': 'شعار المتجر', 'type': 'image', 'required': False},
            {'name': 'صورة خلفية', 'type': 'image', 'required': False}
        ]
    },
    'gallery': {
        'name': '🎨 معرض صور فني',
        'description': 'تطبيق لعرض الصور مع إعجاب وتعليقات',
        'cost': 15,
        'icon': '🎨',
        'category': 'فني',
        'fields': [
            {'name': 'اسم المعرض', 'type': 'text', 'required': True},
            {'name': 'وصف المعرض', 'type': 'textarea', 'required': True},
            {'name': 'الصور', 'type': 'images', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#9b59b6'},
            {'name': 'شاشة عرض', 'type': 'select', 'options': ['شبكي', 'قائمة', 'مربعات'], 'default': 'شبكي'}
        ]
    },
    'menu': {
        'name': '🍽️ قائمة طعام ذكية',
        'description': 'تطبيق منيو مطعم مع أصناف وأسعار وطلبات',
        'cost': 20,
        'icon': '🍽️',
        'category': 'مطاعم',
        'fields': [
            {'name': 'اسم المطعم', 'type': 'text', 'required': True},
            {'name': 'عنوان المطعم', 'type': 'text', 'required': True},
            {'name': 'رقم الهاتف', 'type': 'phone', 'required': True},
            {'name': 'الأصناف', 'type': 'menu_items', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#e67e22'},
            {'name': 'شعار المطعم', 'type': 'image', 'required': False},
            {'name': 'وقت التوصيل', 'type': 'text', 'default': '30-45 دقيقة'}
        ]
    },
    'booking': {
        'name': '📅 نظام حجوزات متقدم',
        'description': 'تطبيق لحجز المواعيد مع تقويم وإشعارات',
        'cost': 30,
        'icon': '📅',
        'category': 'خدمات',
        'fields': [
            {'name': 'اسم المنشأة', 'type': 'text', 'required': True},
            {'name': 'نوع الخدمة', 'type': 'text', 'required': True},
            {'name': 'الخدمات المقدمة', 'type': 'services', 'required': True},
            {'name': 'ساعات العمل', 'type': 'text', 'required': True},
            {'name': 'رقم الهاتف', 'type': 'phone', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'مدة الحجز', 'type': 'number', 'default': '30'}
        ]
    },
    'quran': {
        'name': '📖 تطبيق قرآن كريم',
        'description': 'تطبيق قرآن مع تلاوات وتفسير',
        'cost': 15,
        'icon': '📖',
        'category': 'ديني',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'القرآن الكريم'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#2ecc71'},
            {'name': 'نوع الخط', 'type': 'select', 'options': ['عادي', 'عثماني', 'مزخرف']},
            {'name': 'تلاوات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'تفسير', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'weather': {
        'name': '🌤️ تطبيق الطقس',
        'description': 'تطبيق لمعرفة حالة الطقس في مدينتك',
        'cost': 12,
        'icon': '🌤️',
        'category': 'أدوات',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'الطقس الآن'},
            {'name': 'المدينة الافتراضية', 'type': 'text', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'وحدة القياس', 'type': 'select', 'options': ['مئوي', 'فهرنهايت']},
            {'name': 'تحديث تلقائي', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'calculator': {
        'name': '🧮 آلة حاسبة متطورة',
        'description': 'تطبيق آلة حاسبة علمية',
        'cost': 8,
        'icon': '🧮',
        'category': 'أدوات',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'آلة حاسبة'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#34495e'},
            {'name': 'نوع الآلة', 'type': 'select', 'options': ['بسيطة', 'علمية', 'مالية']},
            {'name': 'الذاكرة', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'notes': {
        'name': '📝 مفكرة ملاحظات',
        'description': 'تطبيق لتدوين الملاحظات مع حفظ تلقائي',
        'cost': 10,
        'icon': '📝',
        'category': 'إنتاجية',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'مفكرتي'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#f1c40f'},
            {'name': 'حفظ تلقائي', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'مشاركة', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'نسخ احتياطي', 'type': 'checkbox', 'default': 'لا'}
        ]
    },
    'prayer': {
        'name': '🕌 أوقات الصلاة',
        'description': 'تطبيق أوقات الصلاة مع القبلة والأذكار',
        'cost': 18,
        'icon': '🕌',
        'category': 'ديني',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'مواقيت الصلاة'},
            {'name': 'المدينة', 'type': 'text', 'required': True},
            {'name': 'الدولة', 'type': 'text', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#27ae60'},
            {'name': 'طريقة الحساب', 'type': 'select', 'options': ['رابطة العالم الإسلامي', 'مصر', 'أم القرى']},
            {'name': 'أذكار', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'قبلة', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'fitness': {
        'name': '💪 تطبيق رياضي',
        'description': 'تطبيق تمارين رياضية مع جدول ومتابعة',
        'cost': 22,
        'icon': '💪',
        'category': 'صحة',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'رياضتي'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#e74c3c'},
            {'name': 'مستوى اللياقة', 'type': 'select', 'options': ['مبتدئ', 'متوسط', 'متقدم']},
            {'name': 'تمارين مقترحة', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'مؤقت', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'متابعة تقدم', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'scanner': {
        'name': '📱 ماسح QR كود',
        'description': 'تطبيق لمسح QR codes وباركود',
        'cost': 12,
        'icon': '📱',
        'category': 'أدوات',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'ماسح QR'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#2c3e50'},
            {'name': 'مسح باركود', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'إنشاء QR', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'حفظ المسح', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'translator': {
        'name': '🌐 مترجم فوري',
        'description': 'تطبيق ترجمة فورية بين اللغات',
        'cost': 20,
        'icon': '🌐',
        'category': 'أدوات',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'المترجم الفوري'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'اللغات', 'type': 'select', 'options': ['عربي-إنجليزي', 'عربي-فرنسي', 'كل اللغات']},
            {'name': 'ترجمة صوتية', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'ترجمة صور', 'type': 'checkbox', 'default': 'لا'}
        ]
    },
    'wallet': {
        'name': '💰 محفظة مالية',
        'description': 'تطبيق لإدارة المصروفات والميزانية',
        'cost': 25,
        'icon': '💰',
        'category': 'مالية',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'محفظتي'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#f39c12'},
            {'name': 'العملة', 'type': 'text', 'default': 'دينار'},
            {'name': 'إيرادات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'مصروفات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'تقارير', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'رسوم بيانية', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'social': {
        'name': '👥 تطبيق تواصل',
        'description': 'تطبيق تواصل اجتماعي بسيط',
        'cost': 30,
        'icon': '👥',
        'category': 'تواصل',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'default': 'تواصل'},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'منشورات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'تعليقات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'إعجابات', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'مشاركة', 'type': 'checkbox', 'default': 'نعم'},
            {'name': 'محادثات', 'type': 'checkbox', 'default': 'نعم'}
        ]
    },
    'custom': {
        'name': '⚡ تطبيق مخصص',
        'description': 'قم بتخصيص تطبيقك بنفسك مع خيارات متقدمة',
        'cost': 35,
        'icon': '⚡',
        'category': 'مخصص',
        'fields': [
            {'name': 'اسم التطبيق', 'type': 'text', 'required': True},
            {'name': 'وصف التطبيق', 'type': 'textarea', 'required': True},
            {'name': 'اللون الرئيسي', 'type': 'color', 'default': '#3498db'},
            {'name': 'عدد الصفحات', 'type': 'number', 'default': '3'},
            {'name': 'نوع التطبيق', 'type': 'select', 'options': ['أعمال', 'تسوق', 'تعليمي', 'ترفيهي', 'خدمات']},
            {'name': 'أذونات خاصة', 'type': 'permissions', 'required': False},
            {'name': 'قاعدة بيانات', 'type': 'checkbox', 'default': 'لا'},
            {'name': 'إشعارات', 'type': 'checkbox', 'default': 'لا'},
            {'name': 'وضع مظلم', 'type': 'checkbox', 'default': 'نعم'}
        ]
    }
}

# جلسات المستخدمين
user_sessions = {}

# دالة إنشاء APK وهمي للتجربة
def generate_fake_apk(app_data):
    """توليد ملف APK وهمي للتجربة"""
    fake_apk_content = f"""
    هذا ملف APK وهمي للتطبيق: {app_data.get('app_name', 'تطبيق')}
    تم إنشاؤه في: {datetime.now()}
    البيانات: {json.dumps(app_data, ensure_ascii=False)}
    """
    return io.BytesIO(fake_apk_content.encode('utf-8'))

# دالة إنشاء تطبيق حقيقي في Thunkable
def create_app_on_thunkable(template, data):
    try:
        app_data = {
            "name": data.get('app_name', 'تطبيق جديد'),
            "template": template,
            "settings": {
                "primaryColor": data.get('اللون الرئيسي', '#3498db'),
                "fields": data
            },
            "user_id": data.get('user_id'),
            "timestamp": datetime.now().isoformat()
        }
        
        # للتجربة: نرجع نجاح وهمي
        return {
            "success": True,
            "download_url": f"https://thunkable.com/download/{template}_{random.randint(1000,9999)}.apk",
            "file_data": generate_fake_apk(app_data)
        }
    except Exception as e:
        logger.error(f"خطأ في إنشاء التطبيق: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# دالة البدء
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        users_data = load_data(USERS_FILE)
        
        if user_id not in users_data:
            if user_id == ADMIN_ID:
                users_data[user_id] = {
                    'username': update.effective_user.username,
                    'first_name': update.effective_user.first_name,
                    'coins': 99999,
                    'apps_created': 0,
                    'joined_channels': [],
                    'last_daily': None,
                    'created_apps': [],
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
                    'created_apps': [],
                    'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            save_data(users_data, USERS_FILE)
        
        coins = users_data[user_id]['coins']
        
        welcome = f"""
🎯 **مرحباً بك في بوت صناعة التطبيقات!**

👤 **المستخدم:** {update.effective_user.first_name}
💰 **رصيدك:** {coins} عملة

**📋 الأقسام المتاحة:**
/create - إنشاء تطبيق جديد
/balance - رصيدي
/help - تعليمات
        """
        
        keyboard = [
            [InlineKeyboardButton("📱 إنشاء تطبيق", callback_data="create_app")],
            [InlineKeyboardButton("💰 رصيدي", callback_data="show_balance")],
        ]
        
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚡ لوحة التحكم", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"خطأ في دالة start: {e}")
        await update.message.reply_text("❌ حدث خطأ. الرجاء المحاولة لاحقاً.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = str(update.effective_user.id)
        
        if data == "create_app":
            await query.message.edit_text(
                "📱 **اختر نوع التطبيق:**\n\n"
                "سيتم إضافة القوالب قريباً...",
                parse_mode='Markdown'
            )
        
        elif data == "show_balance":
            users_data = load_data(USERS_FILE)
            coins = users_data.get(user_id, {}).get('coins', 0)
            await query.message.edit_text(
                f"💰 **رصيدك:** {coins} عملة",
                parse_mode='Markdown'
            )
        
        elif data == "admin_panel" and user_id == ADMIN_ID:
            await query.message.edit_text(
                "⚡ **لوحة تحكم المشرف**\n\n"
                "عدد المستخدمين: قيد التطوير",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"خطأ في button_handler: {e}")

def main():
    try:
        print("🚀 جاري تشغيل البوت...")
        
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        
        print("✅ البوت جاهز للتشغيل")
        print(f"👤 المشرف: {ADMIN_ID}")
        print("📡 بدء استقبال الرسائل...")
        
        app.run_polling()
        
    except Exception as e:
        print(f"❌ خطأ فادح: {e}")
        traceback.print_exc()
        logger.error("خطأ فادح في main", exc_info=True)

if __name__ == '__main__':
    main()