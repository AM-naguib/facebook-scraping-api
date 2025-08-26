#!/usr/bin/env python3
"""
Facebook Token Extractor
========================
سكربت بسيط لاستخراج التوكنز من فيسبوك: fb_dtsg, lsd, jazoest
"""

import json
import re
import requests
import sys


def load_cookies(cookies_file):
    """تحميل الكوكيز من ملف JSON"""
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = requests.Session()
        
        # تحميل الكوكيز في الجلسة
        if isinstance(data, list):
            # فورمات تصدير المتصفح
            for cookie in data:
                if cookie.get('domain') == '.facebook.com':
                    session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
        elif isinstance(data, dict) and 'cookies' in data:
            # فورمات مخصص
            for cookie in data['cookies']:
                session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie['domain']
                )
        else:
            print("❌ فورمات ملف الكوكيز غير مدعوم")
            return None
            
        print("✅ تم تحميل الكوكيز بنجاح")
        return session
        
    except FileNotFoundError:
        print(f"❌ خطأ: ملف الكوكيز غير موجود: {cookies_file}")
        return None
    except json.JSONDecodeError:
        print(f"❌ خطأ: ملف الكوكيز غير صحيح")
        return None
    except Exception as e:
        print(f"❌ خطأ في تحميل الكوكيز: {e}")
        return None


def extract_tokens(session):
    """استخراج التوكنز من فيسبوك"""
    try:
        print("🔍 جاري زيارة فيسبوك لاستخراج التوكنز...")
        
        # زيارة صفحة فيسبوك الرئيسية
        response = session.get('https://www.facebook.com/', timeout=30)
        
        if response.status_code != 200:
            print(f"❌ فشل في تحميل صفحة فيسبوك: {response.status_code}")
            return None, None, None
        
        page_content = response.text
        
        # استخراج fb_dtsg
        fb_dtsg = None
        dtsg_patterns = [
            r'"DTSGInitialData",\[\],\{"token":"([^"]+)"',
            r'"dtsg":\{"token":"([^"]+)"',
            r'fb_dtsg":"([^"]+)"',
            r'DTSGInitialData.*?"token":"([^"]+)"'
        ]
        
        for pattern in dtsg_patterns:
            dtsg_match = re.search(pattern, page_content)
            if dtsg_match:
                fb_dtsg = dtsg_match.group(1)
                break
        
        # استخراج lsd
        lsd = None
        lsd_patterns = [
            r'"LSD",\[\],\{"token":"([^"]+)"',
            r'"token":"([^"]{20,})"'
        ]
        
        for pattern in lsd_patterns:
            lsd_match = re.search(pattern, page_content)
            if lsd_match:
                lsd = lsd_match.group(1)
                break
        
        # jazoest هو قيمة ثابتة
        jazoest = "25515"
        
        return fb_dtsg, lsd, jazoest
        
    except Exception as e:
        print(f"❌ خطأ في استخراج التوكنز: {e}")
        return None, None, None


def main():
    """الدالة الرئيسية"""
    
    # اسم ملف الكوكيز
    cookies_file = "cookies.json"
    
    print("=" * 50)
    print("🔍 Facebook Token Extractor")
    print("=" * 50)
    
    # تحميل الكوكيز
    session = load_cookies(cookies_file)
    if not session:
        print("❌ فشل في تحميل الكوكيز")
        sys.exit(1)
    
    # استخراج التوكنز
    fb_dtsg, lsd, jazoest = extract_tokens(session)
    
    # طباعة النتائج
    print("\n" + "=" * 50)
    print("📊 النتائج:")
    print("=" * 50)
    
    if fb_dtsg:
        print(f"✅ fb_dtsg: {fb_dtsg}")
    else:
        print("❌ لم يتم العثور على fb_dtsg")
    
    if lsd:
        print(f"✅ lsd: {lsd}")
    else:
        print("❌ لم يتم العثور على lsd")
    
    print(f"✅ jazoest: {jazoest}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
