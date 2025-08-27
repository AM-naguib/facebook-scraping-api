#!/usr/bin/env python3
"""
Facebook Reactions Scraper - Final Version
==========================================
سكربت متقدم لسحب التفاعلات من منشورات فيسبوك
يدعم جميع أنواع الروابط والتفاعلات مع pagination ذكي

الاستخدام:
python facebook_reactions_final.py -u "رابط_البوست" -l 50 -d 2.5

المميزات:
- استخراج ذكي لـ feedback_id من أي نوع رابط
- دعم جميع أنواع التفاعلات (Like, Love, Haha, Wow, Sad, Angry, Care)
- pagination تلقائي للحصول على جميع التفاعلات
- تحكم في معدل الطلبات لتجنب الحظر
- حفظ النتائج بتفاصيل كاملة
"""

import json
import re
import requests
import time
import sys
import argparse
import urllib.parse
import base64
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, List, Any


class FacebookReactionsScraper:
    """سكربت متقدم لسحب التفاعلات من فيسبوك"""
    
    def __init__(self, cookies_file: str = "cookies.json"):
        """تهيئة السكربت"""
        self.cookies_file = cookies_file
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
        
    def load_cookies(self) -> bool:
        """تحميل الكوكيز من ملف JSON"""
        try:
            print("📂 جاري تحميل الكوكيز...")
            
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies_data = json.load(f)
            
            for cookie in cookies_data:
                if cookie.get('domain') == '.facebook.com':
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie['domain']
                    )
                    
                    if cookie['name'] == 'c_user':
                        self.user_id = cookie['value']
            
            print("✅ تم تحميل الكوكيز بنجاح")
            if self.user_id:
                print(f"👤 معرف المستخدم: {self.user_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def extract_tokens(self) -> bool:
        """استخراج التوكنز المطلوبة من فيسبوك"""
        try:
            print("🔍 جاري استخراج التوكنز...")
            
            response = self.session.get('https://www.facebook.com/', 
                                      headers=self.browser_headers, timeout=30)
            
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
            
            if not self.fb_dtsg:
                print("❌ فشل في استخراج fb_dtsg")
                return False
                
            print(f"✅ fb_dtsg: {self.fb_dtsg[:30]}...")
            if self.lsd:
                print(f"✅ lsd: {self.lsd}")
            print(f"✅ jazoest: {self.jazoest}")
            return True
            
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
            
            print("❌ لا يمكن استخراج معرف البوست من الرابط")
            return None
            
        except Exception as e:
            print(f"❌ خطأ في استخراج معرف البوست: {e}")
            return None

    def create_feedback_target_id(self, post_id: str) -> str:
        """Create feedback target ID from post ID - الطريقة البسيطة الصحيحة"""
        # The format is base64 encoded "feedback:" + post_id
        feedback_string = f"feedback:{post_id}"
        encoded = base64.b64encode(feedback_string.encode()).decode()
        return encoded

    def smart_feedback_id_extractor(self, post_id: str, post_url: str) -> Optional[str]:
        """استخراج feedback_id بالطريقة البسيطة الصحيحة فقط"""
        try:
            print(f"🎯 إنشاء feedback_id بالطريقة البسيطة...")
            
            # الطريقة البسيطة الصحيحة: "feedback:" + post_id ثم base64
            feedback_target_id = self.create_feedback_target_id(post_id)
            print(f"✅ تم إنشاء feedback_id: {feedback_target_id[:50]}...")
            
            return feedback_target_id
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء feedback_id: {e}")
            return None



    def get_reactions(self, feedback_id: str, limit: int = 0, delay: float = 2.0) -> List[Dict[str, Any]]:
        """جلب التفاعلات من البوست"""
        try:
            print(f"🎭 جاري جلب التفاعلات...")
            if limit == 0:
                print(f"📊 سيتم جلب كل التفاعلات المتاحة")
            else:
                print(f"📊 الحد الأقصى: {limit} تفاعل")
            print(f"⏱️ التأخير بين الطلبات: {delay} ثانية")
            
            all_reactions = []
            cursor = None
            page_count = 0
            
            while True:
                page_count += 1
                print(f"\n📄 جلب الصفحة {page_count}...")
                
                # تحديد عدد التفاعلات لهذا الطلب
                if limit == 0:
                    # جلب كل التفاعلات - استخدم 50 لكل طلب لسرعة أكبر
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
                    print(f"❌ فشل الطلب: {response.status_code}")
                    break
                
                # معالجة الاستجابة
                reactions_data = self.process_response(response)
                if not reactions_data:
                    print("❌ لا توجد بيانات في الاستجابة")
                    # حفظ الاستجابة للتشخيص
                    with open(f"debug_response_page_{page_count}.json", "w", encoding="utf-8") as f:
                        response_text = response.text
                        if response_text.startswith('for (;;);'):
                            response_text = response_text[9:]
                        try:
                            data = json.loads(response_text)
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"💾 تم حفظ استجابة API في debug_response_page_{page_count}.json للفحص")
                        except:
                            f.write(response_text)
                    break
                
                new_reactions = reactions_data.get('reactions', [])
                all_reactions.extend(new_reactions)
                
                print(f"✅ تم جلب {len(new_reactions)} تفاعل")
                print(f"📊 المجموع: {len(all_reactions)} تفاعل")
                
                # التحقق من وجود صفحات أخرى
                page_info = reactions_data.get('page_info', {})
                has_next_page = page_info.get('has_next_page', False)
                cursor = page_info.get('end_cursor')
                

                
                # شروط التوقف
                if not has_next_page or not cursor:
                    print("✅ تم جلب جميع التفاعلات المتاحة")
                    break
                
                if limit > 0 and len(all_reactions) >= limit:
                    print(f"✅ تم الوصول للحد المطلوب: {limit} تفاعل")
                    break
                
                # تأخير قبل الطلب التالي
                print(f"⏳ انتظار {delay} ثانية...")
                time.sleep(delay)
            
            # قطع القائمة للحد المطلوب (فقط إذا كان هناك حد محدد)
            if limit > 0 and len(all_reactions) > limit:
                all_reactions = all_reactions[:limit]
            
            print(f"\n🎉 تم جلب {len(all_reactions)} تفاعل بنجاح")
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
            # الوقت قد يكون في مكان آخر - نحتاج للبحث عنه
            return None
        except Exception:
            return None

    def save_reactions(self, reactions: List[Dict], output_file: str, post_url: str) -> bool:
        """حفظ التفاعلات في ملف JSON داخل مجلد منفصل"""
        try:
            # إنشاء مجلد النتائج
            results_dir = "facebook_reactions_results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
                print(f"📁 تم إنشاء مجلد النتائج: {results_dir}")
            
            # التأكد من أن اسم الملف لا يحتوي على path
            if os.path.dirname(output_file):
                output_file = os.path.basename(output_file)
            
            # المسار الكامل للملف
            full_path = os.path.join(results_dir, output_file)
            
            # حساب إحصائيات التفاعلات
            reaction_stats = {}
            for reaction in reactions:
                reaction_type = reaction.get('reaction_type', 'UNKNOWN')
                reaction_stats[reaction_type] = reaction_stats.get(reaction_type, 0) + 1
            
            output_data = {
                'scraping_info': {
                    'timestamp': datetime.now().isoformat(),
                    'post_url': post_url,
                    'total_reactions': len(reactions),
                    'reaction_stats': reaction_stats,
                    'scraper_version': '2.0'
                },
                'reactions': reactions
            }
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 تم حفظ {len(reactions)} تفاعل في: {full_path}")
            
            # طباعة الإحصائيات
            print("\n📊 إحصائيات التفاعلات:")
            for reaction_type, count in reaction_stats.items():
                print(f"   {reaction_type}: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في حفظ الملف: {e}")
            return False

    def scrape_reactions(self, post_url: str, limit: int = 0, delay: float = 2.0, 
                        output_file: Optional[str] = None) -> List[Dict]:
        """الدالة الرئيسية لسحب التفاعلات"""
        try:
            print("=" * 80)
            print("🎭 Facebook Reactions Scraper - Final Version")
            print("=" * 80)
            print(f"🔗 رابط البوست: {post_url}")
            if limit == 0:
                print(f"📊 سيتم جلب كل التفاعلات المتاحة")
            else:
                print(f"📊 عدد التفاعلات المطلوب: {limit}")
            print(f"⏱️ التأخير بين الطلبات: {delay} ثانية")
            print("=" * 80)
            
            # تحميل الكوكيز
            if not self.load_cookies():
                return []
            
            # استخراج التوكنز
            if not self.extract_tokens():
                return []
            
            # استخراج معرف البوست
            post_id = self.extract_post_id_from_url(post_url)
            if not post_id:
                return []
            
            print(f"✅ معرف البوست: {post_id}")
            
            # الحصول على feedback_id
            feedback_id = self.smart_feedback_id_extractor(post_id, post_url)
            if not feedback_id:
                return []
            
            print(f"✅ feedback_id: {feedback_id}")
            
            # جلب التفاعلات
            reactions = self.get_reactions(feedback_id, limit, delay)
            
            # حفظ النتائج
            if reactions and output_file:
                self.save_reactions(reactions, output_file, post_url)
            
            return reactions
            
        except Exception as e:
            print(f"❌ خطأ عام في السكربت: {e}")
            return []


def main():
    """الدالة الرئيسية لواجهة سطر الأوامر"""
    parser = argparse.ArgumentParser(
        description="سحب التفاعلات من منشورات فيسبوك - الإصدار النهائي",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  %(prog)s -u "https://facebook.com/post/123"                    # جلب كل التفاعلات
  %(prog)s -u "https://facebook.com/post/123" -l 50              # جلب 50 تفاعل
  %(prog)s --url "رابط_البوست" --delay 2.5 --output reactions.json  # جلب كل التفاعلات مع تخصيص
  %(prog)s -u "رابط_البوست" -l 200 -d 1.5 -o my_reactions.json  # جلب عدد محدد
        """
    )
    
    parser.add_argument(
        '-u', '--url',
        required=True,
        help='رابط البوست المراد سحب التفاعلات منه'
    )
    
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=0,
        help='عدد التفاعلات المراد جلبها (افتراضي: 0 = جلب كل التفاعلات)'
    )
    
    parser.add_argument(
        '-d', '--delay',
        type=float,
        default=2.0,
        help='التأخير بين الطلبات بالثواني (افتراضي: 2.0)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='ملف الحفظ (افتراضي: reactions_TIMESTAMP.json)'
    )
    
    parser.add_argument(
        '-c', '--cookies',
        default='cookies.json',
        help='ملف الكوكيز (افتراضي: cookies.json)'
    )
    
    args = parser.parse_args()
    
    # إعداد ملف الإخراج
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"reactions_{timestamp}.json"
    
    # إنشاء السكربت
    scraper = FacebookReactionsScraper(args.cookies)
    
    # سحب التفاعلات
    reactions = scraper.scrape_reactions(
        post_url=args.url,
        limit=args.limit,
        delay=args.delay,
        output_file=args.output
    )
    
    # طباعة النتائج النهائية
    if reactions:
        print("\n" + "=" * 80)
        print("🎉 تم الانتهاء بنجاح!")
        print("=" * 80)
        print(f"✅ تم جلب {len(reactions)} تفاعل")
        print(f"💾 تم الحفظ في: facebook_reactions_results/{args.output}")
        print("=" * 80)
    else:
        print("\n❌ فشل في جلب التفاعلات")
        sys.exit(1)


if __name__ == "__main__":
    main()
