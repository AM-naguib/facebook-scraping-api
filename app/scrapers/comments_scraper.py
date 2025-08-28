"""
Facebook Comments Scraper - API Version
Modified version of the original scraper for API usage
"""

import json
import re
import requests
import time
import urllib.parse
import base64
from datetime import datetime
from typing import Optional, Dict, List, Any


class FacebookCommentsScraper:
    """فئة محسنة لجلب كومنتات فيسبوك - نسخة API"""
    
    def __init__(self):
        """تهيئة الفئة"""
        self.session = requests.Session()
        self.fb_dtsg = None
        self.lsd = None
        self.jazoest = "25515"
        self.user_id = None
        
        # إعداد timeout افتراضي
        self.session.timeout = 30
        
    def load_cookies_from_array(self, cookies_array: List[Dict]) -> bool:
        """تحميل الكوكيز من array - للاستخدام في API"""
        try:
            if not isinstance(cookies_array, list):
                return False
            
            # تحميل الكوكيز
            loaded_count = 0
            for cookie in cookies_array:
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
                return False
                
            if not self.user_id:
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def extract_tokens(self):
        """استخراج التوكنز من فيسبوك"""
        try:
            response = self.session.get('https://www.facebook.com/', timeout=30)
            
            if response.status_code != 200:
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
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ خطأ في استخراج التوكنز: {e}")
            return False

    def extract_post_id(self, post_url):
        """استخراج معرف البوست من الرابط"""
        try:
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
                return None
            
            # تحويل pfbid إلى feedback format
            if post_id.startswith('pfbid'):
                try:
                    feedback_data = f"feedback:{post_id}"
                    graphql_id = base64.b64encode(feedback_data.encode()).decode()
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
                return None, None
            
            try:
                return self.parse_response(response.json())
            except json.JSONDecodeError:
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
                return [], None
            
            # البحث عن الكومنتات
            comment_rendering = node.get('comment_rendering_instance_for_feed_location', {})
            comments_data = comment_rendering.get('comments', {})
            
            if not comments_data:
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
        """استخراج بيانات الكومنت"""
        try:
            # استخراج author_id
            author = comment_node.get('author', {})
            author_id = author.get('id', '')
            
            if not author_id:
                return None
            
            # النص
            body = comment_node.get('body', {})
            text = body.get('text', '') if body else ''
            
            # التاريخ
            created_time = comment_node.get('created_time', 0)
            
            return {
                'author_id': author_id,
                'text': text,
                'created_time': created_time
            }
            
        except Exception as e:
            print(f"⚠️ خطأ في استخراج كومنت: {e}")
            return None

    def scrape_all_comments_api(self, post_url: str, cookies_array: List[Dict], 
                               delay: int = 10, max_pages: Optional[int] = None) -> Dict:
        """جلب جميع الكومنتات - نسخة API"""
        try:
            # التحقق من المتطلبات
            if not self.load_cookies_from_array(cookies_array):
                return {"error": "فشل في تحميل الكوكيز", "comments": []}
                
            if not self.extract_tokens():
                return {"error": "فشل في استخراج التوكنز", "comments": []}
                
            post_id = self.extract_post_id(post_url)
            if not post_id:
                return {"error": "فشل في استخراج معرف البوست", "comments": []}
            
            # جلب الكومنتات
            all_comments = []
            cursor = None
            page_count = 0
            
            while True:
                page_count += 1
                
                if max_pages and page_count > max_pages:
                    break
                
                comments, next_cursor = self.fetch_comments_page(post_id, cursor)
                
                if not comments:
                    break
                
                all_comments.extend(comments)
                
                if not next_cursor:
                    break
                
                cursor = next_cursor
                
                # فارق زمني بين الطلبات
                if next_cursor:
                    time.sleep(delay)
            
            # إعداد النتائج النهائية
            return {
                "success": True,
                "post_url": post_url,
                "total_comments": len(all_comments),
                "pages_scraped": page_count,
                "scraped_at": datetime.now().isoformat(),
                "comments": all_comments
            }
            
        except Exception as e:
            return {"error": f"خطأ عام في السكربت: {str(e)}", "comments": []}

