#!/usr/bin/env python3
"""
استخراج يدوي لـ feedback_id من أي بوست فيسبوك
"""

import requests
import json
import re
from facebook_reactions_final import FacebookReactionsScraper

def extract_feedback_manually(post_url):
    """استخراج feedback_id يدوياً من رابط البوست"""
    
    print("🔍 استخراج feedback_id يدوياً...")
    print(f"📎 الرابط: {post_url}")
    
    scraper = FacebookReactionsScraper()
    
    # تحميل الكوكيز
    if not scraper.load_cookies():
        return None
    
    try:
        # زيارة الصفحة مباشرة
        response = scraper.session.get(post_url, headers=scraper.browser_headers, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            print(f"✅ تم تحميل الصفحة - الحجم: {len(content)} حرف")
            
            # حفظ المحتوى للفحص
            with open("page_content_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("💾 تم حفظ محتوى الصفحة في page_content_debug.html")
            
            # البحث عن جميع أنماط feedback ممكنة
            patterns = [
                r'"feedback_id":"([^"]+)"',
                r'"feedbackTargetID":"([^"]+)"',
                r'"feedbackID":"([^"]+)"',
                r'"target_id":"([^"]+)"',
                r'feedback:(\d+)',
                r'"id":"(feedback:\d+)"',
                r'"feedback"[^}]*"id"[^"]*"([^"]+)"',
                r'ZmVlZGJhY2s[A-Za-z0-9+/=]+',
                r'"ufi_target_id":"([^"]+)"',
                r'"content_id":"([^"]+)"',
                r'"object_id":"([^"]+)"',
                r'"story_id":"([^"]+)"',
                r'"post_id":"([^"]+)"'
            ]
            
            found_ids = []
            
            print(f"\n🔍 البحث عن feedback patterns...")
            for i, pattern in enumerate(patterns, 1):
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"✅ Pattern {i}: وجد {len(matches)} مطابقة")
                    for match in matches[:3]:  # أول 3 مطابقات
                        print(f"   {match}")
                        if match not in found_ids:
                            found_ids.append(match)
                else:
                    print(f"❌ Pattern {i}: لا توجد مطابقات")
            
            # طباعة جميع المعرفات الموجودة
            print(f"\n📋 جميع المعرفات المحتملة ({len(found_ids)}):")
            for i, fid in enumerate(found_ids, 1):
                print(f"{i:2d}. {fid}")
            
            return found_ids
            
        else:
            print(f"❌ فشل تحميل الصفحة: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return None

def test_feedback_id(feedback_id, limit=5):
    """اختبار feedback_id ليرى هل يعطي نتائج"""
    
    print(f"\n🧪 اختبار feedback_id: {feedback_id}")
    
    scraper = FacebookReactionsScraper()
    
    # تحميل الكوكيز واستخراج التوكنز
    if not scraper.load_cookies() or not scraper.extract_tokens():
        return False
    
    try:
        # محاولة جلب تفاعلات
        variables = {
            "count": limit,
            "cursor": None,
            "feedbackTargetID": feedback_id,
            "reactionID": None,
            "scale": 1,
            "id": feedback_id
        }
        
        payload = scraper.build_request_payload(variables, 1)
        headers = scraper.api_headers.copy()
        headers['x-fb-lsd'] = scraper.lsd
        
        response = scraper.session.post(
            'https://www.facebook.com/api/graphql/',
            data=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            reactions_data = scraper.process_response(response)
            if reactions_data and reactions_data.get('reactions'):
                reactions_count = len(reactions_data['reactions'])
                print(f"✅ نجح! وجد {reactions_count} تفاعل")
                return True
            else:
                print(f"❌ لا توجد تفاعلات")
                return False
        else:
            print(f"❌ فشل الطلب: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    
    # رابط بوست مع الذهب
    post_url = "https://www.facebook.com/maa.althahab.sy/posts/pfbid027aesuQ7MZCiDFthVZ9nuEpz2RdapbkG88zm2SGCzyj5xBYsHYz5RL5GJFWkwxCjSl"
    
    print("=" * 80)
    print("🔍 استخراج feedback_id يدوياً")
    print("=" * 80)
    
    # استخراج المعرفات المحتملة
    found_ids = extract_feedback_manually(post_url)
    
    if found_ids:
        print(f"\n🧪 اختبار المعرفات...")
        
        for i, fid in enumerate(found_ids, 1):
            print(f"\n--- اختبار {i}/{len(found_ids)} ---")
            if test_feedback_id(fid):
                print(f"🎉 المعرف الصحيح هو: {fid}")
                print(f"يمكنك استخدامه مع السكربت الرئيسي")
                break
        else:
            print("❌ لم يتم العثور على معرف يعمل")
    else:
        print("❌ لم يتم العثور على أي معرفات")

if __name__ == "__main__":
    main()

