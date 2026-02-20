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

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8587672080:AAHlGubM0ah_c1DTbYyIHh_tmRPvHxiSz68"
ADMIN_ID = "8491314169"

# ملفات التخزين
APPS_FILE = "apps_data.json"
USERS_FILE = "users_data.json"
TEMPLATES_FILE = "templates_data.json"

# إعدادات Thunkable
THUNKABLE_API_URL = "https://api.thunkable.com/v1"
THUNKABLE_API_KEY = "YOUR_THUNKABLE_API_KEY"  # استبدل هذا
THUNKABLE_PROJECT_ID = "YOUR_PROJECT_ID"      # استبدل هذا

# تحميل البيانات
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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

# باقي الكود (جلسات المستخدمين والدوال) هي كما كانت...