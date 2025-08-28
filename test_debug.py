#!/usr/bin/env python3
"""
سكربت اختبار للديباجنج على السيرفر
"""

import json
import sys
import os
from datetime import datetime

# إضافة مسار المشروع
sys.path.append('.')

from app.scrapers.reactions_scraper import FacebookReactionsScraper

def test_token_extraction():
    """اختبار استخراج التوكنز فقط"""
    print("="*60)
    print("🧪 بدء اختبار استخراج التوكنز")
    print("="*60)
    
    # تحميل الكوكيز من الملف
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        print(f"✅ تم تحميل {len(cookies_data)} كوكي من الملف")
        
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الكوكيز: {e}")
        return False
    
    # إنشاء مثيل السكربت
    scraper = FacebookReactionsScraper()
    
    # تحميل الكوكيز
    if not scraper.load_cookies_from_array(cookies_data):
        print("❌ فشل في تحميل الكوكيز")
        return False
    
    # التحقق من صحة الكوكيز
    scraper.check_cookies_validity()
    
    # محاولة استخراج التوكنز
    result = scraper.extract_tokens()
    
    print("="*60)
    print(f"🔍 نتيجة الاختبار: {'نجح' if result else 'فشل'}")
    if result:
        print(f"✅ fb_dtsg: {scraper.fb_dtsg}")
        print(f"✅ lsd: {scraper.lsd}")
    print("="*60)
    
    return result

def test_full_scraping():
    """اختبار كامل لسحب التفاعلات"""
    print("="*60)
    print("🧪 بدء الاختبار الكامل لسحب التفاعلات")
    print("="*60)
    
    # تحميل الكوكيز
    try:
        with open('cookies.json', 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
    except Exception as e:
        print(f"❌ خطأ في تحميل ملف الكوكيز: {e}")
        return False
    
    # إنشاء مثيل السكربت
    scraper = FacebookReactionsScraper()
    
    # رابط تجريبي (استبدل بالرابط الذي تريد اختباره)
    test_post_url = input("أدخل رابط البوست للاختبار: ").strip()
    if not test_post_url:
        print("❌ لم يتم إدخال رابط البوست")
        return False
    
    # سحب التفاعلات (حد أقصى 10 للاختبار)
    result = scraper.scrape_reactions_api(
        post_url=test_post_url,
        cookies_array=cookies_data,
        limit=10,
        delay=1.0
    )
    
    print("="*60)
    print("🔍 نتيجة الاختبار الكامل:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("="*60)
    
    return not result.get("error")

def main():
    """الدالة الرئيسية"""
    print(f"🕐 بدء الاختبار في: {datetime.now()}")
    print(f"🖥️ نظام التشغيل: {os.name}")
    print(f"🐍 إصدار Python: {sys.version}")
    
    # اختبار استخراج التوكنز فقط
    token_test_result = test_token_extraction()
    
    if token_test_result:
        print("\n✅ اختبار التوكنز نجح! هل تريد متابعة الاختبار الكامل؟")
        continue_test = input("اكتب 'y' للمتابعة أو أي شيء آخر للتوقف: ").strip().lower()
        
        if continue_test == 'y':
            test_full_scraping()
    else:
        print("\n❌ اختبار التوكنز فشل. تحقق من الإعدادات والكوكيز.")
    
    # تنظيف ملف الديباجنج إن وجد
    if os.path.exists('debug_facebook_page.html'):
        print("\n🔍 تم إنشاء ملف debug_facebook_page.html للفحص")
        print("يمكنك فتح هذا الملف لرؤية محتوى صفحة فيسبوك المستلمة")

if __name__ == "__main__":
    main()
