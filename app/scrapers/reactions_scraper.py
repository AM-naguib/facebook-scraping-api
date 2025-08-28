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
        
        # headers للتصفح العادي
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
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
            for cookie in cookies_array:
                if cookie.get('domain') == '.facebook.com':
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
                    
                    if cookie['name'] == 'c_user':
                        self.user_id = cookie['value']
            
            if not self.user_id:
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def extract_tokens(self) -> bool:
        """استخراج التوكنز المطلوبة من فيسبوك"""
        try:
            response = self.session.get('https://www.facebook.com/', 
                                      headers=self.browser_headers, timeout=30)
            
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
            
            return bool(self.fb_dtsg)
            
        except Exception as e:
            print(f"❌ خطأ في استخراج التوكنز: {e}")
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
            # تحميل الكوكيز
            if not self.load_cookies_from_array(cookies_array):
                return {"error": "فشل في تحميل الكوكيز", "reactions": []}
            
            # استخراج التوكنز
            if not self.extract_tokens():
                return {"error": "فشل في استخراج التوكنز", "reactions": []}
            
            # استخراج معرف البوست
            post_id = self.extract_post_id_from_url(post_url)
            if not post_id:
                return {"error": "فشل في استخراج معرف البوست", "reactions": []}
            
            # الحصول على feedback_id
            feedback_id = self.smart_feedback_id_extractor(post_id, post_url)
            if not feedback_id:
                return {"error": "فشل في إنشاء feedback_id", "reactions": []}
            
            # جلب التفاعلات
            reactions = self.get_reactions(feedback_id, limit, delay)
            
            # حساب إحصائيات التفاعلات
            reaction_stats = {}
            for reaction in reactions:
                reaction_type = reaction.get('reaction_type', 'UNKNOWN')
                reaction_stats[reaction_type] = reaction_stats.get(reaction_type, 0) + 1
            
            return {
                "success": True,
                "post_url": post_url,
                "post_id": post_id,
                "total_reactions": len(reactions),
                "reaction_stats": reaction_stats,
                "reactions": reactions,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"خطأ عام في السكربت: {str(e)}", "reactions": []}

