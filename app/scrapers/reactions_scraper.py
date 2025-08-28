"""
Facebook Reactions Scraper - API Version
Modified version of the original scraper for API usage
"""

import json
import re
import requests
import time
import urllib.parse
import base64
import gzip
import io
from datetime import datetime
from typing import Optional, Dict, List, Any


class FacebookReactionsScraper:
    """سكربت متقدم لسحب التفاعلات من فيسبوك - نسخة API"""
    
    def __init__(self):
        """تهيئة السكربت"""
        self.session = requests.Session()
        self.fb_dtsg = None
        self.lsd = None
        self.jazoest = "25729"
        self.user_id = None
        
        # إعدادات headers لـ GraphQL API
        self.api_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'x-fb-friendly-name': 'CometUFIReactionsDialogTabContentRefetchQuery',
            'priority': 'u=1, i'
        }
        
        # headers للتصفح العادي - مع User-Agents متعددة للتوافق
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'identity',  # إزالة الضغط لتجنب مشاكل decoding
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache'
        }
        
        # معرفات التفاعلات
        self.reaction_types = {
            '115940658764963': 'LIKE',
            '115940695431625': 'LOVE', 
            '115940658764959': 'HAHA',
            '115940658764965': 'WOW',
            '115940695431634': 'SORRY',
            '115940658764962': 'ANGRY',
            '478547315650144': 'CARE',
            '1635855486666999': 'SUPPORT'
        }
        
    def load_cookies_from_array(self, cookies_array: List[Dict]) -> bool:
        """تحميل الكوكيز من array - للاستخدام في API"""
        try:
            print(f"🔍 [DEBUG] بدء تحميل الكوكيز...")
            print(f"🔍 [DEBUG] عدد الكوكيز المستلمة: {len(cookies_array)}")
            
            facebook_cookies_count = 0
            for cookie in cookies_array:
                if cookie.get('domain') == '.facebook.com':
                    facebook_cookies_count += 1
                    print(f"🔍 [DEBUG] تحميل كوكي: {cookie['name']}")
                    
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
                    
                    if cookie['name'] == 'c_user':
                        self.user_id = cookie['value']
                        print(f"🔍 [DEBUG] تم العثور على user_id: {self.user_id}")
            
            print(f"🔍 [DEBUG] تم تحميل {facebook_cookies_count} كوكي من فيسبوك")
            
            if not self.user_id:
                print(f"❌ [DEBUG] لم يتم العثور على c_user في الكوكيز")
                return False
            
            print(f"✅ [DEBUG] تم تحميل الكوكيز بنجاح")
            return True
            
        except Exception as e:
            print(f"❌ [DEBUG] خطأ في تحميل الكوكيز: {e}")
            import traceback
            print(f"❌ [DEBUG] تفاصيل الخطأ:")
            traceback.print_exc()
            return False
            
    def check_cookies_validity(self) -> bool:
        """التحقق من صحة الكوكيز بسرعة"""
        try:
            print(f"🔍 [DEBUG] التحقق من صحة الكوكيز...")
            
            # طلب سريع لاختبار الكوكيز
            test_response = self.session.head('https://www.facebook.com/', timeout=10)
            print(f"🔍 [DEBUG] حالة اختبار الكوكيز: {test_response.status_code}")
            
            # التحقق من وجود كوكيز أساسية
            important_cookies = ['c_user', 'xs', 'datr']
            for cookie_name in important_cookies:
                if cookie_name in [cookie.name for cookie in self.session.cookies]:
                    print(f"✅ [DEBUG] الكوكي {cookie_name} موجود")
                else:
                    print(f"❌ [DEBUG] الكوكي {cookie_name} مفقود")
                    
            return test_response.status_code in [200, 302]
            
        except Exception as e:
            print(f"❌ [DEBUG] خطأ في التحقق من الكوكيز: {e}")
            return True  # نتابع حتى لو فشل الاختبار
    
    def decompress_content(self, response) -> str:
        """إلغاء ضغط المحتوى يدوياً إذا لزم الأمر"""
        try:
            content_encoding = response.headers.get('content-encoding', '').lower()
            
            if content_encoding == 'gzip':
                print(f"🔍 [DEBUG] إلغاء ضغط gzip يدوياً...")
                return gzip.decompress(response.content).decode('utf-8')
            elif content_encoding == 'deflate':
                print(f"🔍 [DEBUG] إلغاء ضغط deflate يدوياً...")
                import zlib
                return zlib.decompress(response.content).decode('utf-8')
            else:
                # المحتوى غير مضغوط أو requests تعامل معه
                return response.text
                
        except Exception as e:
            print(f"❌ [DEBUG] خطأ في إلغاء الضغط: {e}")
            # كبديل، جرب response.text العادي
            try:
                return response.text
            except:
                return response.content.decode('utf-8', errors='ignore')

    def extract_tokens(self) -> bool:
        """استخراج التوكنز المطلوبة من فيسبوك"""
        try:
            print(f"🔍 [DEBUG] بدء استخراج التوكنز...")
            print(f"🔍 [DEBUG] إرسال طلب GET إلى https://www.facebook.com/")
            
            # محاولة أولى مع User-Agent الحالي
            response = self.session.get('https://www.facebook.com/', 
                                      headers=self.browser_headers, timeout=30)
            
            # إذا فشلت المحاولة الأولى، جرب user-agent آخر
            if response.status_code != 200:
                print(f"🔍 [DEBUG] المحاولة الأولى فشلت ({response.status_code})، جاري المحاولة مع User-Agent مختلف...")
                alternative_headers = self.browser_headers.copy()
                alternative_headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                response = self.session.get('https://www.facebook.com/', 
                                          headers=alternative_headers, timeout=30)
            
            print(f"🔍 [DEBUG] حالة الاستجابة: {response.status_code}")
            print(f"🔍 [DEBUG] حجم المحتوى الخام: {len(response.content)} بايت")
            print(f"🔍 [DEBUG] Content-Type: {response.headers.get('content-type', 'غير محدد')}")
            print(f"🔍 [DEBUG] Content-Encoding: {response.headers.get('content-encoding', 'غير محدد')}")
            
            if response.status_code != 200:
                print(f"❌ [DEBUG] فشل الطلب مع حالة: {response.status_code}")
                return False
            
            # التأكد من إلغاء ضغط المحتوى باستخدام الدالة المخصصة
            try:
                content = self.decompress_content(response)
                print(f"🔍 [DEBUG] حجم المحتوى بعد إلغاء الضغط: {len(content)} حرف")
                
                # التحقق من أن المحتوى نص صالح
                if len(content) == 0:
                    print(f"❌ [DEBUG] المحتوى فارغ")
                    return False
                
                # التحقق من وجود HTML tags أساسية
                if '<html' not in content.lower() and '<div' not in content.lower() and '<script' not in content.lower():
                    print(f"❌ [DEBUG] المحتوى لا يبدو كـ HTML صحيح")
                    print(f"🔍 [DEBUG] أول 200 حرف: {repr(content[:200])}")
                    
                    # محاولة إضافية مع headers مختلفة
                    print(f"🔍 [DEBUG] محاولة مع headers مبسطة...")
                    simple_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'identity',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    response = self.session.get('https://www.facebook.com/', 
                                              headers=simple_headers, timeout=30)
                    content = self.decompress_content(response)
                    print(f"🔍 [DEBUG] حجم المحتوى الجديد: {len(content)} حرف")
                    
            except Exception as e:
                print(f"❌ [DEBUG] خطأ في معالجة المحتوى: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # حفظ محتوى الصفحة للديباجنج إذا لزم الأمر
            try:
                with open('debug_facebook_page.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"🔍 [DEBUG] تم حفظ محتوى الصفحة في debug_facebook_page.html")
            except:
                pass
            
            # طباعة أول 500 حرف من المحتوى للديباجنج
            print(f"🔍 [DEBUG] أول 500 حرف من المحتوى:")
            print(f"{'='*50}")
            print(content[:500])
            print(f"{'='*50}")
            
            # التحقق من تسجيل الدخول والأخطاء أولاً
            content_lower = content.lower()
            
            if any(keyword in content_lower for keyword in ['login', 'sign in', 'تسجيل الدخول']):
                print(f"❌ [DEBUG] يبدو أن فيسبوك يطلب تسجيل الدخول - الكوكيز قد تكون منتهية الصلاحية")
                return False
            
            if any(keyword in content_lower for keyword in ['error', 'not found', '404', 'خطأ']):
                print(f"❌ [DEBUG] فيسبوك يعرض صفحة خطأ")
                return False
            
            if 'checkpoint' in content_lower or 'security' in content_lower:
                print(f"❌ [DEBUG] فيسبوك يطلب تأكيد الأمان - قد تحتاج لتسجيل دخول جديد")
                return False
            
            # استخراج fb_dtsg
            print(f"🔍 [DEBUG] البحث عن fb_dtsg...")
            dtsg_patterns = [
                r'"DTSGInitialData",\[\],\{"token":"([^"]+)"',
                r'"dtsg":\{"token":"([^"]+)"',
                r'fb_dtsg":"([^"]+)"',
                r'DTSGInitialData.*?"token":"([^"]+)"',
                r'"fb_dtsg":"([^"]+)"',
                r'fb_dtsg["\']?\s*:\s*["\']([^"\']+)["\']',
                r'name="fb_dtsg"\s+value="([^"]+)"',
                r'fb_dtsg.*?value="([^"]+)"',
                r'"token":"([a-zA-Z0-9_-]{20,})"',
                # أنماط إضافية للمحتوى المضغوط
                r'dtsg[^a-zA-Z0-9]+([a-zA-Z0-9_-]{20,})',
                r'token[^a-zA-Z0-9]+([a-zA-Z0-9_-]{20,})'
            ]
            
            for i, pattern in enumerate(dtsg_patterns):
                print(f"🔍 [DEBUG] تجريب نمط fb_dtsg #{i+1}: {pattern}")
                match = re.search(pattern, content)
                if match:
                    self.fb_dtsg = match.group(1)
                    print(f"✅ [DEBUG] تم العثور على fb_dtsg: {self.fb_dtsg[:20]}...")
                    break
                else:
                    print(f"❌ [DEBUG] لم يتم العثور على fb_dtsg بالنمط #{i+1}")
            
            if not self.fb_dtsg:
                print(f"❌ [DEBUG] فشل في العثور على fb_dtsg بأي نمط")
                # البحث عن أي نصوص تحتوي على dtsg أو token
                print(f"🔍 [DEBUG] البحث عن أي نصوص تحتوي على 'dtsg':")
                dtsg_matches = re.findall(r'.{0,50}dtsg.{0,50}', content, re.IGNORECASE)
                for match in dtsg_matches[:5]:  # عرض أول 5 نتائج
                    print(f"  - {match}")
                
                print(f"🔍 [DEBUG] البحث عن أي نصوص تحتوي على 'token':")
                token_matches = re.findall(r'.{0,30}token.{0,30}', content, re.IGNORECASE)
                for match in token_matches[:5]:  # عرض أول 5 نتائج
                    print(f"  - {match}")
            
            # استخراج lsd
            print(f"🔍 [DEBUG] البحث عن lsd...")
            lsd_patterns = [
                r'"LSD",\[\],\{"token":"([^"]+)"',
                r'"token":"([^"]{20,})"',
                r'"lsd":"([^"]+)"',
                r'lsd["\']?\s*:\s*["\']([^"\']+)["\']',
                r'name="lsd"\s+value="([^"]+)"',
                r'lsd.*?value="([^"]+)"',
                r'"LSD".*?"token":"([^"]+)"',
                # أنماط إضافية للمحتوى المضغوط
                r'lsd[^a-zA-Z0-9]+([a-zA-Z0-9_-]{15,})',
                r'LSD[^a-zA-Z0-9]+([a-zA-Z0-9_-]{15,})'
            ]
            
            for i, pattern in enumerate(lsd_patterns):
                print(f"🔍 [DEBUG] تجريب نمط lsd #{i+1}: {pattern}")
                match = re.search(pattern, content)
                if match:
                    self.lsd = match.group(1)
                    print(f"✅ [DEBUG] تم العثور على lsd: {self.lsd[:20]}...")
                    break
                else:
                    print(f"❌ [DEBUG] لم يتم العثور على lsd بالنمط #{i+1}")
            
            if not self.lsd:
                print(f"❌ [DEBUG] فشل في العثور على lsd بأي نمط")
                # البحث عن أي نصوص تحتوي على LSD
                print(f"🔍 [DEBUG] البحث عن أي نصوص تحتوي على 'LSD':")
                lsd_matches = re.findall(r'.{0,50}LSD.{0,50}', content, re.IGNORECASE)
                for match in lsd_matches[:5]:  # عرض أول 5 نتائج
                    print(f"  - {match}")
            
            result = bool(self.fb_dtsg)
            print(f"🔍 [DEBUG] نتيجة استخراج التوكنز: {result}")
            print(f"🔍 [DEBUG] fb_dtsg: {'موجود' if self.fb_dtsg else 'غير موجود'}")
            print(f"🔍 [DEBUG] lsd: {'موجود' if self.lsd else 'غير موجود'}")
            
            return result
            
        except Exception as e:
            print(f"❌ [DEBUG] خطأ في استخراج التوكنز: {e}")
            import traceback
            print(f"❌ [DEBUG] تفاصيل الخطأ:")
            traceback.print_exc()
            return False
    
    def extract_tokens_alternative(self) -> bool:
        """طريقة بديلة لاستخراج التوكنز من صفحة مختلفة"""
        try:
            print(f"🔍 [DEBUG] محاولة استخراج التوكنز من طريقة بديلة...")
            
            # جرب صفحة mobile facebook
            mobile_headers = self.browser_headers.copy()
            mobile_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
            
            response = self.session.get('https://m.facebook.com/', 
                                      headers=mobile_headers, timeout=30)
            
            if response.status_code == 200:
                content = self.decompress_content(response)
                print(f"🔍 [DEBUG] حجم محتوى الموبايل: {len(content)} حرف")
                
                # البحث في محتوى الموبايل
                dtsg_patterns = [
                    r'name="fb_dtsg"\s+value="([^"]+)"',
                    r'fb_dtsg.*?value="([^"]+)"',
                    r'"dtsg":"([^"]+)"',
                    r'dtsg[^a-zA-Z0-9]+([a-zA-Z0-9_-]{20,})'
                ]
                
                for pattern in dtsg_patterns:
                    match = re.search(pattern, content)
                    if match:
                        self.fb_dtsg = match.group(1)
                        print(f"✅ [DEBUG] تم العثور على fb_dtsg من الموبايل: {self.fb_dtsg[:20]}...")
                        break
                
                # البحث عن lsd
                lsd_patterns = [
                    r'name="lsd"\s+value="([^"]+)"',
                    r'lsd.*?value="([^"]+)"',
                    r'"lsd":"([^"]+)"'
                ]
                
                for pattern in lsd_patterns:
                    match = re.search(pattern, content)
                    if match:
                        self.lsd = match.group(1)
                        print(f"✅ [DEBUG] تم العثور على lsd من الموبايل: {self.lsd[:20]}...")
                        break
            
            return bool(self.fb_dtsg)
            
        except Exception as e:
            print(f"❌ [DEBUG] خطأ في الطريقة البديلة: {e}")
            return False

    def extract_post_id_from_url(self, post_url: str) -> Optional[str]:
        """استخراج معرف البوست من الرابط"""
        try:
            post_url = post_url.strip()
            parsed_url = urllib.parse.urlparse(post_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # استخراج من permalink
            if "permalink.php" in parsed_url.path and 'story_fbid' in query_params:
                return query_params['story_fbid'][0]
            
            # استخراج من direct post
            post_match = re.search(r'/posts/([^/?]+)', parsed_url.path)
            if post_match:
                return post_match.group(1)
            
            # محاولة أخرى من الرابط المباشر
            if '/posts/' in post_url:
                parts = post_url.split('/posts/')
                if len(parts) > 1:
                    post_id = parts[1].split('?')[0].split('/')[0]
                    return post_id
            
            return None
            
        except Exception as e:
            print(f"❌ خطأ في استخراج معرف البوست: {e}")
            return None

    def create_feedback_target_id(self, post_id: str) -> str:
        """Create feedback target ID from post ID"""
        feedback_string = f"feedback:{post_id}"
        encoded = base64.b64encode(feedback_string.encode()).decode()
        return encoded

    def smart_feedback_id_extractor(self, post_id: str, post_url: str) -> Optional[str]:
        """استخراج feedback_id بالطريقة البسيطة الصحيحة فقط"""
        try:
            feedback_target_id = self.create_feedback_target_id(post_id)
            return feedback_target_id
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء feedback_id: {e}")
            return None

    def get_reactions(self, feedback_id: str, limit: int = 0, delay: float = 2.0) -> List[Dict[str, Any]]:
        """جلب التفاعلات من البوست"""
        try:
            all_reactions = []
            cursor = None
            page_count = 0
            
            while True:
                page_count += 1
                
                # تحديد عدد التفاعلات لهذا الطلب
                if limit == 0:
                    count_per_request = 50
                else:
                    remaining = limit - len(all_reactions)
                    count_per_request = min(10, remaining)
                
                # إعداد variables للطلب
                variables = {
                    "count": count_per_request,
                    "cursor": cursor,
                    "feedbackTargetID": feedback_id,
                    "reactionID": None,
                    "scale": 1,
                    "id": feedback_id
                }
                
                # إعداد payload
                payload = self.build_request_payload(variables, page_count)
                
                # إعداد headers
                headers = self.api_headers.copy()
                headers['x-fb-lsd'] = self.lsd
                
                # إرسال الطلب
                response = self.session.post(
                    'https://www.facebook.com/api/graphql/',
                    data=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    break
                
                # معالجة الاستجابة
                reactions_data = self.process_response(response)
                if not reactions_data:
                    break
                
                new_reactions = reactions_data.get('reactions', [])
                all_reactions.extend(new_reactions)
                
                # التحقق من وجود صفحات أخرى
                page_info = reactions_data.get('page_info', {})
                has_next_page = page_info.get('has_next_page', False)
                cursor = page_info.get('end_cursor')
                
                # شروط التوقف
                if not has_next_page or not cursor:
                    break
                
                if limit > 0 and len(all_reactions) >= limit:
                    break
                
                # تأخير قبل الطلب التالي
                time.sleep(delay)
            
            # قطع القائمة للحد المطلوب (فقط إذا كان هناك حد محدد)
            if limit > 0 and len(all_reactions) > limit:
                all_reactions = all_reactions[:limit]
            
            return all_reactions
            
        except Exception as e:
            print(f"❌ خطأ في جلب التفاعلات: {e}")
            return []

    def build_request_payload(self, variables: Dict, page_count: int) -> Dict:
        """بناء payload للطلب"""
        return {
            'av': self.user_id,
            '__aaid': '0',
            '__user': self.user_id,
            '__a': '1',
            '__req': f'{page_count:02x}',
            '__hs': '20326.HYP:comet_pkg.2.1...0',
            'dpr': '1',
            '__ccg': 'EXCELLENT',
            '__rev': '1026326043',
            '__s': 'deup5g:m4uo1p:p0pyqa',
            '__hsi': '7542830019330714267',
            '__comet_req': '15',
            'fb_dtsg': self.fb_dtsg,
            'jazoest': self.jazoest,
            'lsd': self.lsd,
            '__spin_r': '1026326043',
            '__spin_b': 'trunk',
            '__spin_t': str(int(time.time())),
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CometUFIReactionsDialogTabContentRefetchQuery',
            'variables': json.dumps(variables),
            'server_timestamps': 'true',
            'doc_id': '31470716059194219'
        }

    def process_response(self, response) -> Optional[Dict]:
        """معالجة استجابة API"""
        try:
            response_text = response.text
            if response_text.startswith('for (;;);'):
                response_text = response_text[9:]
            
            data = json.loads(response_text)
            
            # استخراج التفاعلات
            if 'data' in data and 'node' in data['data']:
                node = data['data']['node']
                
                if 'reactors' in node and 'edges' in node['reactors']:
                    reactions = []
                    
                    for edge in node['reactors']['edges']:
                        reaction_info = {
                            'user': self.extract_user_info(edge),
                            'reaction_type': self.extract_reaction_type(edge),
                            'timestamp': self.extract_timestamp(edge)
                        }
                        reactions.append(reaction_info)
                    
                    page_info = node['reactors'].get('page_info', {})
                    
                    return {
                        'reactions': reactions,
                        'page_info': page_info
                    }
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"❌ خطأ في معالجة JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ خطأ في معالجة الاستجابة: {e}")
            return None

    def extract_user_info(self, edge: Dict) -> Dict:
        """استخراج معلومات المستخدم"""
        try:
            user_info = {
                'id': None,
                'name': None,
                'profile_url': None,
                'profile_picture': None
            }
            
            if 'node' in edge:
                user = edge['node']
                user_info['id'] = user.get('id')
                user_info['name'] = user.get('name')
                user_info['profile_url'] = user.get('url') or user.get('profile_url')
                
                if 'profile_picture' in user and user['profile_picture']:
                    user_info['profile_picture'] = user['profile_picture'].get('uri')
            
            return user_info
            
        except Exception:
            return {'id': None, 'name': None, 'profile_url': None, 'profile_picture': None}

    def extract_reaction_type(self, edge: Dict) -> str:
        """استخراج نوع التفاعل"""
        try:
            if 'feedback_reaction_info' in edge:
                reaction_info = edge['feedback_reaction_info']
                reaction_id = reaction_info.get('id', '')
                return self.reaction_types.get(reaction_id, 'LIKE')
            
            return 'LIKE'
        except Exception:
            return 'UNKNOWN'

    def extract_timestamp(self, edge: Dict) -> Optional[str]:
        """استخراج وقت التفاعل"""
        try:
            return None
        except Exception:
            return None

    def scrape_reactions_api(self, post_url: str, cookies_array: List[Dict], 
                           limit: int = 0, delay: float = 2.0) -> Dict:
        """الدالة الرئيسية لسحب التفاعلات - نسخة API"""
        try:
            print(f"🔍 [DEBUG] بدء سحب التفاعلات من: {post_url}")
            print(f"🔍 [DEBUG] المعاملات: limit={limit}, delay={delay}")
            
            # تحميل الكوكيز
            print(f"🔍 [DEBUG] خطوة 1: تحميل الكوكيز...")
            if not self.load_cookies_from_array(cookies_array):
                print(f"❌ [DEBUG] فشل في تحميل الكوكيز")
                return {"error": "فشل في تحميل الكوكيز", "reactions": []}
            
            # التحقق من صحة الكوكيز
            print(f"🔍 [DEBUG] خطوة 1.5: التحقق من صحة الكوكيز...")
            self.check_cookies_validity()
            
            # استخراج التوكنز
            print(f"🔍 [DEBUG] خطوة 2: استخراج التوكنز...")
            if not self.extract_tokens():
                print(f"❌ [DEBUG] فشل في استخراج التوكنز من الطريقة الأساسية")
                print(f"🔍 [DEBUG] جاري المحاولة بالطريقة البديلة...")
                if not self.extract_tokens_alternative():
                    print(f"❌ [DEBUG] فشل في استخراج التوكنز من جميع الطرق")
                    return {"error": "فشل في استخراج التوكنز", "reactions": []}
            
            # استخراج معرف البوست
            print(f"🔍 [DEBUG] خطوة 3: استخراج معرف البوست...")
            post_id = self.extract_post_id_from_url(post_url)
            if not post_id:
                print(f"❌ [DEBUG] فشل في استخراج معرف البوست")
                return {"error": "فشل في استخراج معرف البوست", "reactions": []}
            print(f"✅ [DEBUG] معرف البوست: {post_id}")
            
            # الحصول على feedback_id
            print(f"🔍 [DEBUG] خطوة 4: إنشاء feedback_id...")
            feedback_id = self.smart_feedback_id_extractor(post_id, post_url)
            if not feedback_id:
                print(f"❌ [DEBUG] فشل في إنشاء feedback_id")
                return {"error": "فشل في إنشاء feedback_id", "reactions": []}
            print(f"✅ [DEBUG] feedback_id: {feedback_id[:50]}...")
            
            # جلب التفاعلات
            print(f"🔍 [DEBUG] خطوة 5: جلب التفاعلات...")
            reactions = self.get_reactions(feedback_id, limit, delay)
            print(f"✅ [DEBUG] تم جلب {len(reactions)} تفاعل")
            
            # حساب إحصائيات التفاعلات
            reaction_stats = {}
            for reaction in reactions:
                reaction_type = reaction.get('reaction_type', 'UNKNOWN')
                reaction_stats[reaction_type] = reaction_stats.get(reaction_type, 0) + 1
            
            print(f"✅ [DEBUG] إحصائيات التفاعلات: {reaction_stats}")
            
            result = {
                "success": True,
                "post_url": post_url,
                "post_id": post_id,
                "total_reactions": len(reactions),
                "reaction_stats": reaction_stats,
                "reactions": reactions,
                "scraped_at": datetime.now().isoformat()
            }
            
            print(f"✅ [DEBUG] تم الانتهاء بنجاح من سحب التفاعلات")
            return result
            
        except Exception as e:
            print(f"❌ [DEBUG] خطأ عام في السكربت: {str(e)}")
            import traceback
            print(f"❌ [DEBUG] تفاصيل الخطأ:")
            traceback.print_exc()
            return {"error": f"خطأ عام في السكربت: {str(e)}", "reactions": []}


