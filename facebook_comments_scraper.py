#!/usr/bin/env python3
"""
Facebook Comments Scraper
==========================
سكربت لجلب جميع الكومنتات من بوست فيسبوك باستخدام GraphQL API
"""

import json
import re
import requests
import sys
import time
import urllib.parse
import base64
from datetime import datetime


class FacebookCommentsScraper:
    """فئة جلب كومنتات فيسبوك"""
    
    def __init__(self, cookies_file="cookies.json"):
        """تهيئة الفئة مع الكوكيز"""
        self.session = requests.Session()
        self.cookies_file = cookies_file
        self.fb_dtsg = None
        self.lsd = None
        self.jazoest = "25515"  # نفس القيمة من السكربت المبسط
        self.user_id = None
        
    def load_cookies(self):
        """تحميل الكوكيز من ملف JSON"""
        try:
            print("📂 جاري تحميل الكوكيز...")
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # تحميل الكوكيز في الجلسة
            if isinstance(data, list):
                for cookie in data:
                    if cookie.get('domain') == '.facebook.com':
                        self.session.cookies.set(
                            cookie['name'], 
                            cookie['value'], 
                            domain=cookie['domain']
                        )
                        
                        # استخراج معرف المستخدم من c_user
                        if cookie['name'] == 'c_user':
                            self.user_id = cookie['value']
                            
                print("✅ تم تحميل الكوكيز بنجاح")
                if self.user_id:
                    print(f"👤 معرف المستخدم: {self.user_id}")
                return True
            else:
                print("❌ فورمات ملف الكوكيز غير مدعوم")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def extract_tokens(self):
        """استخراج التوكنز من فيسبوك - نفس طريقة extract_tokens.py"""
        try:
            print("🔍 جاري زيارة فيسبوك لاستخراج التوكنز...")
            
            # زيارة صفحة فيسبوك الرئيسية
            response = self.session.get('https://www.facebook.com/', timeout=30)
            
            if response.status_code != 200:
                print(f"❌ فشل في تحميل صفحة فيسبوك: {response.status_code}")
                return False
            
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
            
            # حفظ التوكنز في الكلاس
            self.fb_dtsg = fb_dtsg
            self.lsd = lsd
            self.jazoest = jazoest
            
            # طباعة النتائج
            if self.fb_dtsg:
                print(f"✅ fb_dtsg: {self.fb_dtsg}")
            else:
                print("❌ لم يتم العثور على fb_dtsg")
                
            if self.lsd:
                print(f"✅ lsd: {self.lsd}")
            else:
                print("❌ لم يتم العثور على lsd")
                
            print(f"✅ jazoest: {self.jazoest}")
            
            # دعه يكمل حتى لو لم يجد lsd - كما فعلنا في السكربت المبسط
            if self.fb_dtsg:
                print("✅ تم استخراج التوكنز الأساسية - سيتم المحاولة")
                return True
            else:
                print("❌ فشل في استخراج fb_dtsg - لا يمكن المتابعة")
                return False
            
        except Exception as e:
            print(f"❌ خطأ في استخراج التوكنز: {e}")
            return False

    def analyze_post_url(self, post_url):
        """تحليل رابط البوست واستخراج معرف البوست"""
        print(f"\n🔍 تحليل رابط البوست:")
        print(f"📎 {post_url}")
        
        # تنظيف الرابط
        post_url = post_url.strip()
        
        # تحليل URL
        parsed_url = urllib.parse.urlparse(post_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        post_info = {
            "post_id": None,
            "user_id": None,
            "pfbid": None,
            "feedback_id": None
        }
        
        # استخراج معرف البوست
        if "permalink.php" in parsed_url.path:
            # من نوع permalink
            if 'story_fbid' in query_params:
                story_fbid = query_params['story_fbid'][0]
                post_info["post_id"] = story_fbid
                
                if story_fbid.startswith('pfbid'):
                    post_info["pfbid"] = story_fbid
                    print(f"🔐 معرف مشفر (pfbid): {story_fbid}")
                else:
                    print(f"🔢 معرف رقمي: {story_fbid}")
            
            if 'id' in query_params:
                post_info["user_id"] = query_params['id'][0]
                print(f"👤 معرف المستخدم/الصفحة: {post_info['user_id']}")
        
        elif "/posts/" in parsed_url.path:
            # من نوع direct post
            post_match = re.search(r'/posts/([^/?]+)', parsed_url.path)
            if post_match:
                post_id = post_match.group(1)
                post_info["post_id"] = post_id
                
                if post_id.startswith('pfbid'):
                    post_info["pfbid"] = post_id
                    print(f"🔐 معرف مشفر (pfbid): {post_id}")
                else:
                    print(f"🔢 معرف رقمي: {post_id}")
        
        # تحويل pfbid إلى feedback_id إذا أمكن
        if post_info["pfbid"]:
            feedback_id = self.convert_pfbid_to_feedback_id(post_info["pfbid"])
            if feedback_id:
                post_info["feedback_id"] = feedback_id
                print(f"🎯 Feedback ID: {feedback_id}")
        
        return post_info

    def convert_pfbid_to_feedback_id(self, pfbid):
        """تحويل pfbid إلى feedback_id باستخدام Base64"""
        try:
            # إزالة البادئة pfbid
            encoded_part = pfbid[5:]
            
            # طرق مختلفة للتحويل
            methods = [
                # طريقة 1: استخدام pfbid مباشرة كـ feedback_id
                lambda x: base64.b64encode(f"feedback:{pfbid}".encode()).decode(),
                
                # طريقة 2: محاولة فك pfbid ثم إعادة تشفيره
                lambda x: self._try_decode_pfbid(x),
                
                # طريقة 3: استخدام hash من pfbid
                lambda x: self._hash_pfbid_to_feedback(pfbid)
            ]
            
            for i, method in enumerate(methods):
                try:
                    result = method(encoded_part)
                    if result:
                        print(f"✅ تم التحويل بالطريقة {i+1}")
                        return result
                except Exception as e:
                    print(f"⚠️ فشلت الطريقة {i+1}: {e}")
                    continue
            
            # إذا فشلت جميع الطرق، استخدم pfbid كما هو
            print("⚠️ استخدام pfbid كما هو")
            return pfbid
            
        except Exception as e:
            print(f"⚠️ فشل في تحويل pfbid: {e}")
            return pfbid

    def _try_decode_pfbid(self, encoded_part):
        """محاولة فك pfbid"""
        try:
            # استبدال أحرف URL-safe
            modified = encoded_part.replace('-', '+').replace('_', '/')
            
            # إضافة padding
            padding = len(modified) % 4
            if padding:
                modified += '=' * (4 - padding)
            
            decoded = base64.b64decode(modified)
            
            # تحويل إلى feedback format
            feedback_data = f"feedback:{decoded.hex()[:16]}"
            return base64.b64encode(feedback_data.encode()).decode()
            
        except:
            return None

    def _hash_pfbid_to_feedback(self, pfbid):
        """تحويل pfbid إلى feedback_id باستخدام hash"""
        try:
            import hashlib
            
            # إنشاء hash من pfbid
            hash_obj = hashlib.sha256(pfbid.encode())
            hash_hex = hash_obj.hexdigest()[:20]
            
            # تحويل إلى feedback format
            feedback_data = f"feedback:{hash_hex}"
            return base64.b64encode(feedback_data.encode()).decode()
            
        except:
            return None

    def get_comments(self, feedback_id, cursor=None, max_pages=None):
        """جلب الكومنتات من البوست"""
        try:
            print(f"\n💬 جاري جلب الكومنتات...")
            if cursor:
                print(f"📄 من الصفحة: {cursor[:20]}...")
            
            # تحويل pfbid إلى format صحيح إذا لزم الأمر
            graphql_id = feedback_id
            if feedback_id.startswith('pfbid'):
                # محاولة تحويل pfbid إلى feedback format
                try:
                    feedback_data = f"feedback:{feedback_id}"
                    graphql_id = base64.b64encode(feedback_data.encode()).decode()
                    print(f"🔄 تم تحويل pfbid إلى: {graphql_id[:50]}...")
                except:
                    # إذا فشل التحويل، استخدم pfbid كما هو
                    graphql_id = feedback_id
                    print(f"⚠️ استخدام pfbid مباشرة: {graphql_id}")
            
            # إعداد المتغيرات للطلب
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
                "id": graphql_id,
                "__relay_internal__pv__IsWorkUserrelayprovider": False
            }
            
            # بيانات الطلب
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
                "__hsi": "7542672544110411392",
                "__dyn": "7xeUjGU5a5Q1ryaxG4Vp41twWwIxu13wFwhUKbgS3q2ibwNw9G2Saw8i2S1DwUx60GE5O0BU2_CxS320qa321Rwwwqo462mcwfG12wOx62G5Usw9m1YwBgK7o6C0Mo4G17yovwRwlE-U2exi4UaEW2G1jwUBwJK14xm3y11xfxmu3W3jU8o4Wm7-2K0-obUG2-azqwaW223908O3216xi4UK2K2WEjxK2B08-269wkopg6C13xecwBwWwjHDzUiBG2OUqwjVqwLwHwa211wo83KwHwOyUqxG",
                "__csr": "g4X1gAxq2AeigL3YbOiOiNQ_dNcAhv9sl5OEIKOhadqRYLjW4RH69isRqZGriO-zTC4WAqOqHKhrXJkACJnBHh9a_syt6Fyk8Ju-BOaJOJGpelbBWRy9lQaECt9pP9ainJeumqqF9Uyb8DByrK4aF34V2p9bz95XzaBJyAVAbLK5GV97l95zbLDWQO12VGGHKeJdHx6uiiEGmmlpEG8G48-qnx54G8WQHJ-QK4F-ehaKCdxd1N3qxFeF8Caz4GJ9qKcBUHK8VUy49pUpDzFUSKayUCWxbhpAbAzFrBz8-FFpXCCABG6pEW8JyppUWlFeewDzoCEGVoK3DyEmwFx91WVE9bKEKbAwg48yUgDx92oyazayUC7oOu9xObiwBwkEqwBzUc8c8Op38WEO48gHyoCfGezobEa98y484mcG2S14wGy4ewCxG9DwmGw_AwmoG3bGi7Q0YEfoa84a0GoW0AFU9k9xuFolK0BGy6Hg7qWwGweK1bwzCwVzHxi3C5o2PwuEWu8ADwg86q6o7a1OwdyENajw0Mtw1-R0dmu0bfxS8wuo0Aq7o1RF81NU1gE4p01mubxS1_w0ajK1Cw0Ysyu0gW1OBwaYM2Vwee3y0s1wcu9waZw7oxC0AA0kIw8E0Xi1ko2ZgG1gz8y3i582Fwe2780Gh03BEDa0f-w1lW09DysElw3oU4p015W0hmE09TEcy02OEOt04tgozF2wEw1OC1Fw4Rw7Lw5GxO3e1ew2_80pnwuE1uU13tw7gyE27F05Ow2Kyw98E",
                "__comet_req": "15",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": self.jazoest,
                "lsd": self.lsd,
                "__spin_r": "1026303884",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "server_timestamps": "true",
                "fb_api_req_friendly_name": "CommentsListComponentsPaginationQuery",
                "variables": json.dumps(variables),
                "doc_id": "24170828295923210"
            }
            
            # إعداد headers للطلب
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
                print(f"❌ فشل في الطلب: {response.status_code}")
                return None, None
            
            # تحليل الاستجابة
            try:
                response_data = response.json()
                return self.parse_comments_response(response_data)
            except json.JSONDecodeError:
                print("❌ خطأ في تحليل JSON response")
                return None, None
                
        except Exception as e:
            print(f"❌ خطأ في جلب الكومنتات: {e}")
            return None, None

    def parse_comments_response(self, response_data):
        """تحليل استجابة الكومنتات"""
        try:
            comments = []
            next_cursor = None
            
            # التنقل في بنية البيانات - نفس الطريقة المجربة
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
            
            # استخراج الكومنتات
            edges = comments_data.get('edges', [])
            
            for edge in edges:
                comment_node = edge.get('node', {})
                comment_data = self.extract_comment_data(comment_node)
                if comment_data:
                    comments.append(comment_data)
            
            print(f"✅ تم جلب {len(comments)} كومنت")
            if next_cursor:
                print(f"📄 يوجد صفحات إضافية")
            
            return comments, next_cursor
            
        except Exception as e:
            print(f"❌ خطأ في تحليل الاستجابة: {e}")
            return [], None

    def extract_comment_data(self, comment_node):
        """استخراج بيانات الكومنت"""
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
                    dt = datetime.fromtimestamp(comment['created_time'])
                    comment['created_time_formatted'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    comment['created_time_formatted'] = 'Unknown'
            else:
                comment['created_time_formatted'] = 'Unknown'
            
            return comment
            
        except Exception as e:
            print(f"⚠️ خطأ في استخراج بيانات كومنت: {e}")
            return None

    def scrape_all_comments(self, post_url, delay=10, max_pages=None):
        """جلب جميع الكومنتات من البوست"""
        print("=" * 80)
        print("🔍 Facebook Comments Scraper")
        print("=" * 80)
        
        # تحميل الكوكيز
        if not self.load_cookies():
            return None
        
        # استخراج التوكنز
        if not self.extract_tokens():
            return None
        
        # تحليل رابط البوست
        post_info = self.analyze_post_url(post_url)
        
        # تحديد معرف البوست للاستخدام في GraphQL
        post_identifier = None
        if post_info.get('feedback_id'):
            post_identifier = post_info['feedback_id']
            print(f"📋 استخدام feedback_id: {post_identifier[:30]}...")
        elif post_info.get('pfbid'):
            post_identifier = post_info['pfbid']
            print(f"📋 استخدام pfbid مباشرة: {post_identifier}")
        elif post_info.get('post_id'):
            post_identifier = post_info['post_id']
            print(f"📋 استخدام post_id: {post_identifier}")
        else:
            print("❌ فشل في استخراج معرف البوست")
            return None
        
        # جلب الكومنتات
        all_comments = []
        cursor = None
        page_count = 0
        
        while True:
            page_count += 1
            print(f"\n📄 صفحة {page_count}:")
            
            comments, next_cursor = self.get_comments(post_identifier, cursor, max_pages)
            
            if not comments:
                print("❌ لم يتم جلب أي كومنتات")
                break
            
            all_comments.extend(comments)
            
            if not next_cursor or (max_pages and page_count >= max_pages):
                break
            
            cursor = next_cursor
            
            # انتظار قبل الطلب التالي
            print(f"⏳ انتظار {delay} ثانية قبل الطلب التالي...")
            time.sleep(delay)
        
        return {
            'post_url': post_url,
            'post_info': post_info,
            'total_comments': len(all_comments),
            'pages_scraped': page_count,
            'comments': all_comments,
            'scraped_at': datetime.now().isoformat()
        }

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

    def display_summary(self, results):
        """عرض ملخص النتائج"""
        if not results:
            return
        
        print("\n" + "=" * 80)
        print("📊 ملخص النتائج")
        print("=" * 80)
        
        print(f"🔗 رابط البوست: {results['post_url']}")
        print(f"💬 إجمالي الكومنتات: {results['total_comments']}")
        print(f"📄 عدد الصفحات: {results['pages_scraped']}")
        print(f"🕐 وقت الجلب: {results['scraped_at']}")
        
        if results['comments']:
            print(f"\n💬 عينة من الكومنتات:")
            print("-" * 40)
            
            for i, comment in enumerate(results['comments'][:5]):
                print(f"\n{i+1}. {comment.get('author_name', 'Unknown')}")
                print(f"   📅 {comment.get('created_time_formatted', 'Unknown')}")
                print(f"   ❤️ {comment.get('likes_count', 0)} إعجاب")
                text = comment.get('text', '')[:100]
                if len(comment.get('text', '')) > 100:
                    text += "..."
                print(f"   💭 {text}")
        
        print("=" * 80)


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
        # عرض الملخص
        scraper.display_summary(results)
        
        # حفظ النتائج
        scraper.save_results(results)
    else:
        print("❌ فشل في جلب الكومنتات")


if __name__ == "__main__":
    main()
