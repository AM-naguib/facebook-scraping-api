#!/usr/bin/env python3
"""
Facebook Comments Scraper - Optimized
======================================
نسخة محسنة لجلب الكومنتات من فيسبوك
- فقط author_id في JSON النهائي
- كود محسن وأداء أفضل
- فحص شامل للأخطاء
"""

import json
import re
import requests
import time
import urllib.parse
import base64
from datetime import datetime


class FacebookCommentsScraper:
    """فئة محسنة لجلب كومنتات فيسبوك"""
    
    def __init__(self, cookies_file="cookies.json"):
        """تهيئة الفئة"""
        self.session = requests.Session()
        self.cookies_file = cookies_file
        self.fb_dtsg = None
        self.lsd = None
        self.jazoest = "25515"
        self.user_id = None
        
        # إعداد timeout افتراضي
        self.session.timeout = 30
        
    def load_cookies(self):
        """تحميل الكوكيز من ملف JSON"""
        try:
            print("📂 تحميل الكوكيز...")
            
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            if not isinstance(cookies_data, list):
                print("❌ فورمات ملف الكوكيز غير صحيح")
                return False
            
            # تحميل الكوكيز
            loaded_count = 0
            for cookie in cookies_data:
                if cookie.get('domain') == '.facebook.com':
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
                    loaded_count += 1
                    
                    # استخراج معرف المستخدم
                    if cookie['name'] == 'c_user':
                        self.user_id = cookie['value']
            
            if loaded_count == 0:
                print("❌ لم يتم العثور على كوكيز فيسبوك صالحة")
                return False
                
            if not self.user_id:
                print("❌ لم يتم العثور على معرف المستخدم")
                return False
                
            print(f"✅ تم تحميل {loaded_count} كوكيز - معرف المستخدم: {self.user_id}")
            return True
            
        except FileNotFoundError:
            print(f"❌ ملف الكوكيز غير موجود: {self.cookies_file}")
            return False
        except json.JSONDecodeError:
            print("❌ خطأ في قراءة ملف الكوكيز")
            return False
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def extract_tokens(self):
        """استخراج التوكنز من فيسبوك"""
        try:
            print("🔍 استخراج التوكنز...")
            
            response = self.session.get('https://www.facebook.com/', timeout=30)
            
            if response.status_code != 200:
                print(f"❌ فشل في تحميل فيسبوك: {response.status_code}")
                return False
            
            content = response.text
            
            # استخراج fb_dtsg
            dtsg_patterns = [
                r'"DTSGInitialData",\[\],\{"token":"([^"]+)"',
                r'"dtsg":\{"token":"([^"]+)"',
                r'fb_dtsg":"([^"]+)"',
                r'DTSGInitialData.*?"token":"([^"]+)"'
            ]
            
            for pattern in dtsg_patterns:
                match = re.search(pattern, content)
                if match:
                    self.fb_dtsg = match.group(1)
                    break
            
            # استخراج lsd
            lsd_patterns = [
                r'"LSD",\[\],\{"token":"([^"]+)"',
                r'"token":"([^"]{20,})"'
            ]
            
            for pattern in lsd_patterns:
                match = re.search(pattern, content)
                if match:
                    self.lsd = match.group(1)
                    break
            
            # التحقق من النتائج
            if not self.fb_dtsg:
                print("❌ فشل في استخراج fb_dtsg")
                return False
                
            print(f"✅ fb_dtsg: {self.fb_dtsg[:30]}...")
            
            if self.lsd:
                print(f"✅ lsd: {self.lsd}")
            else:
                print("⚠️ لم يتم العثور على lsd - سيتم المحاولة بدونه")
                
            print(f"✅ jazoest: {self.jazoest}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في استخراج التوكنز: {e}")
            return False

    def extract_post_id(self, post_url):
        """استخراج معرف البوست من الرابط"""
        try:
            print(f"🔍 تحليل رابط البوست...")
            
            parsed_url = urllib.parse.urlparse(post_url.strip())
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            post_id = None
            
            # من نوع permalink
            if "permalink.php" in parsed_url.path and 'story_fbid' in query_params:
                post_id = query_params['story_fbid'][0]
            # من نوع direct post
            elif "/posts/" in parsed_url.path:
                post_match = re.search(r'/posts/([^/?]+)', parsed_url.path)
                if post_match:
                    post_id = post_match.group(1)
            
            if not post_id:
                print("❌ لم يتم العثور على معرف البوست")
                return None
                
            print(f"✅ معرف البوست: {post_id}")
            
            # تحويل pfbid إلى feedback format
            if post_id.startswith('pfbid'):
                try:
                    feedback_data = f"feedback:{post_id}"
                    graphql_id = base64.b64encode(feedback_data.encode()).decode()
                    print(f"✅ تم تحويل pfbid إلى feedback format")
                    return graphql_id
                except Exception as e:
                    print(f"⚠️ فشل تحويل pfbid: {e} - سيتم استخدام المعرف الأصلي")
                    return post_id
            
            return post_id
            
        except Exception as e:
            print(f"❌ خطأ في تحليل الرابط: {e}")
            return None

    def fetch_comments_page(self, post_id, cursor=None):
        """جلب صفحة واحدة من الكومنتات"""
        try:
            # إعداد المتغيرات
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
                "id": post_id,
                "__relay_internal__pv__IsWorkUserrelayprovider": False
            }
            
            # إعداد بيانات الطلب
            data = {
                "av": self.user_id,
                "__aaid": "0",
                "__user": self.user_id,
                "__a": "1",
                "__req": "3n",
                "__hs": "20325.HYP:comet_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "EXCELLENT",
                "__rev": "1026303884",
                "__s": "43pu0c:crpsn8:ehpbtp",
                "__comet_req": "15",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": self.jazoest,
                "lsd": self.lsd or "",
                "__spin_r": "1026303884",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "server_timestamps": "true",
                "fb_api_req_friendly_name": "CommentsListComponentsPaginationQuery",
                "variables": json.dumps(variables),
                "doc_id": "24170828295923210"
            }
            
            # إعداد headers
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.facebook.com',
                'Referer': 'https://www.facebook.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            # إرسال الطلب
            response = self.session.post(
                'https://www.facebook.com/api/graphql/',
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ فشل الطلب: {response.status_code}")
                return None, None
            
            try:
                return self.parse_response(response.json())
            except json.JSONDecodeError:
                print("❌ خطأ في تحليل JSON")
                return None, None
                
        except Exception as e:
            print(f"❌ خطأ في جلب الكومنتات: {e}")
            return None, None

    def parse_response(self, response_data):
        """تحليل استجابة الكومنتات"""
        try:
            # التنقل في بنية البيانات
            data = response_data.get('data', {})
            node = data.get('node')
            
            if not node:
                print("❌ لا يوجد بيانات في الاستجابة")
                return [], None
            
            # البحث عن الكومنتات
            comment_rendering = node.get('comment_rendering_instance_for_feed_location', {})
            comments_data = comment_rendering.get('comments', {})
            
            if not comments_data:
                print("❌ لا توجد كومنتات")
                return [], None
            
            # استخراج pagination
            page_info = comments_data.get('page_info', {})
            next_cursor = None
            if page_info.get('has_next_page'):
                next_cursor = page_info.get('end_cursor')
            
            # استخراج الكومنتات
            edges = comments_data.get('edges', [])
            comments = []
            
            for edge in edges:
                comment_node = edge.get('node', {})
                comment = self.extract_comment_data(comment_node)
                if comment:
                    comments.append(comment)
            
            return comments, next_cursor
            
        except Exception as e:
            print(f"❌ خطأ في تحليل الاستجابة: {e}")
            return [], None

    def extract_comment_data(self, comment_node):
        """استخراج بيانات الكومنت - محسن للحصول على author_id فقط"""
        try:
            # استخراج author_id فقط كما طلبت
            author = comment_node.get('author', {})
            author_id = author.get('id', '')
            
            if not author_id:
                return None  # تجاهل الكومنتات بدون author_id
            
            # النص
            body = comment_node.get('body', {})
            text = body.get('text', '') if body else ''
            
            # التاريخ
            created_time = comment_node.get('created_time', 0)
            
            # معلومات إضافية للعرض فقط (لن تحفظ في JSON)
            author_name = author.get('name', 'Unknown')
            
            return {
                'author_id': author_id,  # فقط author_id في JSON
                'text': text,
                'created_time': created_time,
                # بيانات إضافية للعرض فقط
                '_display_name': author_name,  # للعرض فقط
                '_formatted_time': self.format_timestamp(created_time)  # للعرض فقط
            }
            
        except Exception as e:
            print(f"⚠️ خطأ في استخراج كومنت: {e}")
            return None
    
    def format_timestamp(self, timestamp):
        """تحويل timestamp إلى تاريخ قابل للقراءة"""
        try:
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        return 'Unknown'

    def scrape_all_comments(self, post_url, delay=10, max_pages=None):
        """جلب جميع الكومنتات - نسخة محسنة"""
        print("=" * 70)
        print("🔍 Facebook Comments Scraper - Optimized")
        print("=" * 70)
        
        # التحقق من المتطلبات
        if not self.load_cookies():
            return None
            
        if not self.extract_tokens():
            return None
            
        post_id = self.extract_post_id(post_url)
        if not post_id:
            return None
        
        # جلب الكومنتات
        all_comments = []
        cursor = None
        page_count = 0
        
        print(f"\n💬 بدء جلب الكومنتات...")
        
        while True:
            page_count += 1
            
            if max_pages and page_count > max_pages:
                print(f"🛑 تم الوصول للحد الأقصى: {max_pages} صفحة")
                break
            
            print(f"📄 صفحة {page_count}...", end=" ")
            
            comments, next_cursor = self.fetch_comments_page(post_id, cursor)
            
            if not comments:
                print("❌ لا توجد كومنتات")
                break
            
            print(f"✅ {len(comments)} كومنت")
            all_comments.extend(comments)
            
            if not next_cursor:
                print("📄 لا توجد صفحات إضافية")
                break
            
            cursor = next_cursor
            
            # فارق زمني بين الطلبات
            if next_cursor:
                print(f"⏳ انتظار {delay} ثانية...")
                time.sleep(delay)
        
        # إعداد النتائج النهائية
        result = {
            'post_url': post_url,
            'total_comments': len(all_comments),
            'pages_scraped': page_count,
            'scraped_at': datetime.now().isoformat(),
            'comments': []
        }
        
        # إعداد الكومنتات للحفظ - فقط البيانات المطلوبة
        for comment in all_comments:
            # إزالة البيانات المؤقتة للعرض
            clean_comment = {
                'author_id': comment['author_id'],
                'text': comment['text'],
                'created_time': comment['created_time']
            }
            result['comments'].append(clean_comment)
        
        # عرض الملخص
        self.display_summary(result, all_comments)
        
        return result

    def display_summary(self, result, all_comments_with_display):
        """عرض ملخص النتائج"""
        print(f"\n" + "=" * 70)
        print("📊 ملخص النتائج")
        print("=" * 70)
        
        print(f"💬 إجمالي الكومنتات: {result['total_comments']}")
        print(f"📄 عدد الصفحات: {result['pages_scraped']}")
        print(f"🕐 وقت الجلب: {result['scraped_at']}")
        
        if all_comments_with_display:
            print(f"\n💬 عينة من الكومنتات:")
            print("-" * 50)
            
            for i, comment in enumerate(all_comments_with_display[:5]):
                print(f"{i+1}. {comment.get('_display_name', 'Unknown')}")
                print(f"   🆔 author_id: {comment['author_id']}")
                print(f"   📅 {comment.get('_formatted_time', 'Unknown')}")
                text = comment['text'][:80]
                if len(comment['text']) > 80:
                    text += "..."
                print(f"   💭 {text}")
                print()
            
            if len(all_comments_with_display) > 5:
                print(f"... و {len(all_comments_with_display) - 5} كومنت آخر")
        
        print("=" * 70)

    def save_results(self, results, filename=None):
        """حفظ النتائج في ملف JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"facebook_comments_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 تم حفظ النتائج في: {filename}")
            return filename
        except Exception as e:
            print(f"❌ خطأ في حفظ النتائج: {e}")
            return None


def main():
    """الدالة الرئيسية"""
    
    # رابط البوست للاختبار
    test_url = "https://www.facebook.com/bantalrb.heba/posts/pfbid029Ra2EaMcbGn5miZxq5DHx2cS3NYiYGav7TBMzFWQ8JQ8fvs3T1BGpVKnR4sN44LVl"
    
    # إنشاء مكشطة الكومنتات
    scraper = FacebookCommentsScraper()
    
    # جلب جميع الكومنتات
    results = scraper.scrape_all_comments(
        post_url=test_url,
        delay=10,  # 10 ثوانٍ بين الطلبات
        max_pages=None  # جلب جميع الصفحات
    )
    
    if results:
        # حفظ النتائج
        scraper.save_results(results)
        print(f"\n🎉 تم الانتهاء بنجاح!")
        print(f"📊 تم جلب {results['total_comments']} كومنت من {results['pages_scraped']} صفحة")
    else:
        print("❌ فشل في جلب الكومنتات")


if __name__ == "__main__":
    main()