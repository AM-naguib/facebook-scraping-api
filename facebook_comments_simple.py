#!/usr/bin/env python3
"""
Facebook Comments Scraper - Simplified Version
===============================================
إصدار مبسط لجلب الكومنتات من فيسبوك مع شرح المفهوم
"""

import json
import re
import requests
import time
import urllib.parse
import base64
from datetime import datetime


def load_cookies_from_file(cookies_file="cookies.json"):
    """تحميل الكوكيز من ملف JSON"""
    try:
        print("📂 جاري تحميل الكوكيز...")
        
        session = requests.Session()
        
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        # تحميل الكوكيز في الجلسة
        user_id = None
        for cookie in cookies_data:
            if cookie.get('domain') == '.facebook.com':
                session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie['domain']
                )
                
                # استخراج معرف المستخدم
                if cookie['name'] == 'c_user':
                    user_id = cookie['value']
        
        print("✅ تم تحميل الكوكيز بنجاح")
        if user_id:
            print(f"👤 معرف المستخدم: {user_id}")
        
        return session, user_id
        
    except Exception as e:
        print(f"❌ خطأ في تحميل الكوكيز: {e}")
        return None, None


def extract_post_id_from_url(post_url):
    """استخراج معرف البوست من الرابط"""
    print(f"\n🔍 تحليل رابط البوست:")
    print(f"📎 {post_url}")
    
    try:
        parsed_url = urllib.parse.urlparse(post_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        post_id = None
        
        # من نوع permalink
        if "permalink.php" in parsed_url.path and 'story_fbid' in query_params:
            post_id = query_params['story_fbid'][0]
            print(f"📋 معرف البوست (من permalink): {post_id}")
        
        # من نوع direct post
        elif "/posts/" in parsed_url.path:
            post_match = re.search(r'/posts/([^/?]+)', parsed_url.path)
            if post_match:
                post_id = post_match.group(1)
                print(f"📋 معرف البوست (من مسار مباشر): {post_id}")
        
        if post_id:
            if post_id.startswith('pfbid'):
                print("🔐 نوع المعرف: pfbid (مشفر)")
            else:
                print("🔢 نوع المعرف: رقمي")
            
            return post_id
        else:
            print("❌ لم يتم العثور على معرف البوست")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في تحليل الرابط: {e}")
        return None


def get_facebook_tokens(session):
    """استخراج التوكنز من فيسبوك - نفس طريقة extract_tokens.py"""
    print("\n🔍 جاري زيارة فيسبوك لاستخراج التوكنز...")
    
    try:
        # زيارة صفحة فيسبوك الرئيسية
        response = session.get('https://www.facebook.com/', timeout=30)
        
        if response.status_code != 200:
            print(f"❌ فشل في تحميل صفحة فيسبوك: {response.status_code}")
            return None, None, None
        
        page_content = response.text
        
        # استخراج fb_dtsg - نفس الطريقة من extract_tokens.py
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
        
        # استخراج lsd - نفس الطريقة من extract_tokens.py
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
        
        # jazoest هو قيمة ثابتة - نفس extract_tokens.py
        jazoest = "25515"
        
        # طباعة النتائج
        if fb_dtsg:
            print(f"✅ fb_dtsg: {fb_dtsg}")
        else:
            print("❌ لم يتم العثور على fb_dtsg")
            
        if lsd:
            print(f"✅ lsd: {lsd}")
        else:
            print("❌ لم يتم العثور على lsd")
            
        print(f"✅ jazoest: {jazoest}")
        
        return fb_dtsg, lsd, jazoest
        
    except Exception as e:
        print(f"❌ خطأ في استخراج التوكنز: {e}")
        return None, None, None


def create_graphql_payload(post_id, fb_dtsg, lsd, jazoest, user_id, cursor=None):
    """إنشاء payload لطلب GraphQL"""
    
    # تحويل pfbid إلى format صحيح إذا لزم الأمر
    graphql_id = post_id
    if post_id.startswith('pfbid'):
        # محاولة تحويل pfbid إلى feedback format
        try:
            feedback_data = f"feedback:{post_id}"
            graphql_id = base64.b64encode(feedback_data.encode()).decode()
            print(f"🔄 تم تحويل pfbid إلى: {graphql_id}")
        except:
            # إذا فشل التحويل، استخدم pfbid كما هو
            graphql_id = post_id
            print(f"⚠️ استخدام pfbid مباشرة: {graphql_id}")
    
    # المتغيرات الأساسية للطلب
    variables = {
        "commentsAfterCount": -1,
        "commentsAfterCursor": cursor,
        "commentsBeforeCount": None,
        "commentsBeforeCursor": None,
        "commentsIntentToken": "RANKED_FILTERED_INTENT_V1",
        "feedLocation": "POST_PERMALINK_DIALOG",
        "focusCommentID": None,
        "scale": 2,
        "useDefaultActor": False,
        "id": graphql_id,  # المعرف المحول
        "__relay_internal__pv__IsWorkUserrelayprovider": False
    }
    
    # بيانات الطلب
    payload = {
        "av": user_id,
        "__aaid": "0",
        "__user": user_id,
        "__a": "1",
        "__req": "3n",
        "__hs": "20325.HYP:comet_pkg.2.1...0",
        "dpr": "1",
        "__ccg": "EXCELLENT",
        "__rev": "1026303884",
        "__s": "43pu0c:crpsn8:ehpbtp",
        "__comet_req": "15",
        "fb_dtsg": fb_dtsg or "dummy_token",
        "jazoest": jazoest or "25515",
        "lsd": lsd or "dummy_lsd",
        "__spin_r": "1026303884",
        "__spin_b": "trunk",
        "__spin_t": str(int(time.time())),
        "fb_api_caller_class": "RelayModern",
        "server_timestamps": "true",
        "fb_api_req_friendly_name": "CommentsListComponentsPaginationQuery",
        "variables": json.dumps(variables),
        "doc_id": "24170828295923210"
    }
    
    return payload


def fetch_comments_page(session, post_id, fb_dtsg, lsd, jazoest, user_id, cursor=None):
    """جلب صفحة واحدة من الكومنتات"""
    
    print(f"💬 جاري جلب الكومنتات...")
    if cursor:
        print(f"📄 من الصفحة: {cursor[:20]}...")
    
    try:
        # إعداد headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Referer': f'https://www.facebook.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        # إعداد payload
        payload = create_graphql_payload(post_id, fb_dtsg, lsd, jazoest, user_id, cursor)
        
        # إرسال الطلب
        response = session.post(
            'https://www.facebook.com/api/graphql/',
            data=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 كود الاستجابة: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # حفظ الاستجابة للفحص
                timestamp = datetime.now().strftime("%H%M%S")
                debug_file = f"graphql_response_{timestamp}.json"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"💾 تم حفظ الاستجابة في: {debug_file}")
                
                return data
                
            except json.JSONDecodeError:
                print("❌ خطأ في تحليل JSON")
                # حفظ النص للفحص
                with open(f"response_text_{datetime.now().strftime('%H%M%S')}.txt", 'w', encoding='utf-8') as f:
                    f.write(response.text[:1000])
                return None
        else:
            print(f"❌ فشل الطلب: {response.status_code}")
            print(f"📄 نص الخطأ: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ خطأ في جلب الكومنتات: {e}")
        return None


def parse_comments_from_response(response_data):
    """تحليل الكومنتات من الاستجابة"""
    
    if not response_data:
        return [], None
    
    comments = []
    next_cursor = None
    
    try:
        print("🔍 تحليل بنية الاستجابة...")
        
        # التنقل في بنية البيانات
        data = response_data.get('data', {})
        node = data.get('node', {})
        
        if not node:
            print("❌ لا يوجد node في البيانات")
            return [], None
        
        # البحث عن الكومنتات
        comment_rendering = node.get('comment_rendering_instance_for_feed_location', {})
        comments_data = comment_rendering.get('comments', {})
        
        if not comments_data:
            print("❌ لا توجد بيانات كومنتات")
            return [], None
        
        # استخراج pagination info
        page_info = comments_data.get('page_info', {})
        if page_info:
            has_next_page = page_info.get('has_next_page', False)
            if has_next_page:
                next_cursor = page_info.get('end_cursor')
                print(f"📄 يوجد صفحات إضافية: {bool(next_cursor)}")
        
        # استخراج الكومنتات
        edges = comments_data.get('edges', [])
        print(f"💬 تم العثور على {len(edges)} كومنت")
        
        for edge in edges:
            comment_node = edge.get('node', {})
            comment = extract_comment_info(comment_node)
            if comment:
                comments.append(comment)
        
        print(f"✅ تم تحليل {len(comments)} كومنت بنجاح")
        return comments, next_cursor
        
    except Exception as e:
        print(f"❌ خطأ في تحليل الكومنتات: {e}")
        return [], None


def extract_comment_info(comment_node):
    """استخراج معلومات الكومنت من node"""
    try:
        comment = {}
        
        # المعلومات الأساسية
        comment['id'] = comment_node.get('id', '')
        comment['created_time'] = comment_node.get('created_time', 0)
        
        # النص
        body = comment_node.get('body', {})
        comment['text'] = body.get('text', '') if body else ''
        
        # معلومات المؤلف
        author = comment_node.get('author', {})
        if author:
            comment['author_name'] = author.get('name', 'Unknown')
            comment['author_id'] = author.get('id', '')
            comment['author_url'] = author.get('url', '')
        
        # عدد الإعجابات والردود
        feedback = comment_node.get('feedback', {})
        if feedback:
            # الإعجابات
            reaction_count = feedback.get('reaction_count', {})
            comment['likes_count'] = reaction_count.get('count', 0) if reaction_count else 0
            
            # الردود
            replies_fields = feedback.get('replies_fields', {})
            comment['replies_count'] = replies_fields.get('total_count', 0) if replies_fields else 0
        else:
            comment['likes_count'] = 0
            comment['replies_count'] = 0
        
        # تنسيق الوقت
        if comment['created_time']:
            try:
                from datetime import datetime
                dt = datetime.fromtimestamp(comment['created_time'])
                comment['created_time_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                comment['created_time_formatted'] = 'Unknown'
        else:
            comment['created_time_formatted'] = 'Unknown'
        
        return comment
        
    except Exception as e:
        print(f"⚠️ خطأ في استخراج معلومات كومنت: {e}")
        return None


def main():
    """الدالة الرئيسية - مثال للاستخدام"""
    
    print("🔍 Facebook Comments Scraper - Simplified Version")
    print("=" * 60)
    
    # رابط البوست للاختبار
    test_url = "https://www.facebook.com/bantalrb.heba/posts/pfbid029Ra2EaMcbGn5miZxq5DHx2cS3NYiYGav7TBMzFWQ8JQ8fvs3T1BGpVKnR4sN44LVl"
    
    # الخطوة 1: تحميل الكوكيز
    session, user_id = load_cookies_from_file()
    if not session:
        print("❌ فشل في تحميل الكوكيز")
        return
    
    # الخطوة 2: استخراج معرف البوست
    post_id = extract_post_id_from_url(test_url)
    if not post_id:
        print("❌ فشل في استخراج معرف البوست")
        return
    
    # الخطوة 3: استخراج التوكنز
    fb_dtsg, lsd, jazoest = get_facebook_tokens(session)
    
    # الخطوة 4: محاولة جلب الكومنتات
    print(f"\n🚀 محاولة جلب الكومنتات من البوست...")
    
    response_data = fetch_comments_page(session, post_id, fb_dtsg, lsd, jazoest, user_id)
    
    if response_data:
        print("✅ تم الحصول على استجابة من فيسبوك")
        comments, next_cursor = parse_comments_from_response(response_data)
        
        if comments:
            print(f"🎉 تم جلب {len(comments)} كومنت!")
            
            # عرض عينة من الكومنتات
            print(f"\n💬 عينة من الكومنتات:")
            print("-" * 60)
            
            for i, comment in enumerate(comments[:3]):  # أول 3 كومنتات فقط
                print(f"\n{i+1}. {comment.get('author_name', 'Unknown')}")
                print(f"   📅 {comment.get('created_time_formatted', 'Unknown')}")
                print(f"   ❤️ {comment.get('likes_count', 0)} إعجاب | 💬 {comment.get('replies_count', 0)} رد")
                text = comment.get('text', '')[:100]
                if len(comment.get('text', '')) > 100:
                    text += "..."
                print(f"   💭 {text}")
            
            if len(comments) > 3:
                print(f"\n   ... و {len(comments) - 3} كومنت آخر")
                
            # معلومات عن الصفحات الإضافية
            if next_cursor:
                print(f"\n📄 يوجد المزيد من الكومنتات في الصفحات التالية")
                print(f"🔄 يمكن استخدام cursor: {next_cursor[:30]}...")
        else:
            print("⚠️ لم يتم العثور على كومنتات في الاستجابة")
            print("💡 قد تحتاج لتحليل بنية الاستجابة المحفوظة وتعديل الكود")
    else:
        print("❌ فشل في الحصول على استجابة صحيحة")
    
    print(f"\n📋 ملخص:")
    print(f"   🔗 رابط البوست: {test_url}")
    print(f"   📋 معرف البوست: {post_id}")
    print(f"   👤 معرف المستخدم: {user_id}")
    print(f"   🔑 fb_dtsg: {'موجود' if fb_dtsg else 'غير موجود'}")
    print(f"   🔑 lsd: {'موجود' if lsd else 'غير موجود'}")
    
    print(f"\n💡 للمتابعة:")
    print(f"   1. فحص ملفات الاستجابة المحفوظة")
    print(f"   2. تحليل بنية البيانات")
    print(f"   3. تعديل دالة parse_comments_from_response")
    print(f"   4. إضافة المزيد من patterns للتوكنز إذا لزم الأمر")


if __name__ == "__main__":
    main()
