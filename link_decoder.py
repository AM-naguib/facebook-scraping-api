#!/usr/bin/env python3
"""
Facebook Link Decoder & Validator
=================================
سكربت لفك وتحليل روابط فيسبوك والتحقق من صحتها
"""

import json
import re
import requests
import sys
import urllib.parse
import base64
import binascii


class FacebookLinkDecoder:
    """فئة فك وتحليل روابط فيسبوك"""
    
    def __init__(self, cookies_file="cookies.json"):
        """تهيئة الفئة مع الكوكيز"""
        self.session = requests.Session()
        self.load_cookies(cookies_file)
        
    def load_cookies(self, cookies_file):
        """تحميل الكوكيز من ملف JSON"""
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
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
                print("✅ تم تحميل الكوكيز بنجاح")
                return True
            else:
                print("❌ فورمات ملف الكوكيز غير مدعوم")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في تحميل الكوكيز: {e}")
            return False

    def analyze_link(self, post_url):
        """تحليل رابط فيسبوك وفك مكوناته"""
        print(f"\n🔍 تحليل الرابط:")
        print(f"📎 {post_url}")
        print("-" * 60)
        
        # تنظيف الرابط
        post_url = post_url.strip()
        
        # تحليل URL
        parsed_url = urllib.parse.urlparse(post_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        analysis = {
            "url_type": "unknown",
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "parameters": query_params,
            "post_id": None,
            "user_id": None,
            "pfbid": None,
            "is_valid": False
        }
        
        print(f"🌐 النطاق: {analysis['domain']}")
        print(f"📂 المسار: {analysis['path']}")
        
        # تحديد نوع الرابط
        if "permalink.php" in parsed_url.path:
            analysis["url_type"] = "permalink"
            print("📋 نوع الرابط: Permalink")
            
            # استخراج story_fbid
            if 'story_fbid' in query_params:
                story_fbid = query_params['story_fbid'][0]
                analysis["post_id"] = story_fbid
                
                # فحص إذا كان pfbid
                if story_fbid.startswith('pfbid'):
                    analysis["pfbid"] = story_fbid
                    print(f"🔐 معرف مشفر (pfbid): {story_fbid}")
                    
                    # محاولة فك التشفير
                    decoded_info = self.decode_pfbid(story_fbid)
                    if decoded_info:
                        analysis.update(decoded_info)
                else:
                    print(f"🔢 معرف رقمي: {story_fbid}")
            
            # استخراج معرف المستخدم/الصفحة
            if 'id' in query_params:
                user_id = query_params['id'][0]
                analysis["user_id"] = user_id
                print(f"👤 معرف المستخدم/الصفحة: {user_id}")
        
        elif "/posts/" in parsed_url.path:
            analysis["url_type"] = "direct_post"
            print("📋 نوع الرابط: Direct Post")
            
            # استخراج معرف البوست من المسار
            post_match = re.search(r'/posts/([^/?]+)', parsed_url.path)
            if post_match:
                post_id = post_match.group(1)
                analysis["post_id"] = post_id
                
                if post_id.startswith('pfbid'):
                    analysis["pfbid"] = post_id
                    print(f"🔐 معرف مشفر (pfbid): {post_id}")
                    decoded_info = self.decode_pfbid(post_id)
                    if decoded_info:
                        analysis.update(decoded_info)
                else:
                    print(f"🔢 معرف رقمي: {post_id}")
        
        # تحديد صحة الرابط
        if analysis["post_id"]:
            analysis["is_valid"] = True
            print("✅ الرابط صحيح ويحتوي على معرف بوست")
        else:
            print("❌ لا يمكن استخراج معرف البوست")
        
        return analysis

    def decode_pfbid(self, pfbid):
        """محاولة فك تشفير pfbid"""
        print(f"\n🔓 محاولة فك تشفير pfbid:")
        
        if not pfbid.startswith('pfbid'):
            print("❌ ليس pfbid صحيح")
            return None
        
        # إزالة البادئة
        encoded_part = pfbid[5:]  # إزالة "pfbid"
        
        print(f"📝 الجزء المشفر: {encoded_part}")
        print(f"📏 طول التشفير: {len(encoded_part)} حرف")
        
        # معلومات أساسية
        info = {
            "pfbid_length": len(encoded_part),
            "encoding_type": "base64_variant",
            "estimated_data_size": len(encoded_part) * 3 // 4,
            "decode_attempts": []
        }
        
        # محاولات فك التشفير المختلفة
        decode_methods = [
            ("Standard Base64", self.try_standard_base64),
            ("URL-Safe Base64", self.try_urlsafe_base64),
            ("Base64 with padding", self.try_base64_with_padding),
            ("Custom Facebook encoding", self.try_facebook_encoding)
        ]
        
        for method_name, method_func in decode_methods:
            try:
                result = method_func(encoded_part)
                info["decode_attempts"].append({
                    "method": method_name,
                    "success": result is not None,
                    "result": result
                })
                
                if result:
                    print(f"✅ {method_name}: نجح جزئياً")
                else:
                    print(f"❌ {method_name}: فشل")
                    
            except Exception as e:
                info["decode_attempts"].append({
                    "method": method_name,
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ {method_name}: خطأ - {e}")
        
        return info

    def try_standard_base64(self, encoded):
        """محاولة فك Base64 عادي"""
        try:
            # إضافة padding إذا لزم الأمر
            padding = len(encoded) % 4
            if padding:
                encoded += '=' * (4 - padding)
            
            decoded = base64.b64decode(encoded)
            return {
                "method": "standard_base64",
                "raw_bytes": len(decoded),
                "hex_preview": decoded[:20].hex() if len(decoded) > 0 else None
            }
        except:
            return None

    def try_urlsafe_base64(self, encoded):
        """محاولة فك URL-Safe Base64"""
        try:
            padding = len(encoded) % 4
            if padding:
                encoded += '=' * (4 - padding)
            
            decoded = base64.urlsafe_b64decode(encoded)
            return {
                "method": "urlsafe_base64",
                "raw_bytes": len(decoded),
                "hex_preview": decoded[:20].hex() if len(decoded) > 0 else None
            }
        except:
            return None

    def try_base64_with_padding(self, encoded):
        """محاولة فك Base64 مع padding مختلف"""
        try:
            # محاولة بدون padding
            decoded = base64.b64decode(encoded + '==')
            return {
                "method": "base64_with_padding",
                "raw_bytes": len(decoded),
                "hex_preview": decoded[:20].hex() if len(decoded) > 0 else None
            }
        except:
            return None

    def try_facebook_encoding(self, encoded):
        """محاولة فك تشفير فيسبوك المخصص"""
        try:
            # فيسبوك قد يستخدم تعديلات على Base64
            # استبدال أحرف خاصة
            modified = encoded.replace('-', '+').replace('_', '/')
            
            padding = len(modified) % 4
            if padding:
                modified += '=' * (4 - padding)
            
            decoded = base64.b64decode(modified)
            return {
                "method": "facebook_custom",
                "raw_bytes": len(decoded),
                "hex_preview": decoded[:20].hex() if len(decoded) > 0 else None,
                "char_replacements": "Applied - and _ replacements"
            }
        except:
            return None

    def verify_post_accessibility(self, post_url):
        """التحقق من إمكانية الوصول للبوست"""
        print(f"\n🔍 التحقق من إمكانية الوصول للبوست:")
        
        try:
            # محاولة زيارة الرابط
            response = self.session.get(post_url, timeout=15)
            
            verification = {
                "status_code": response.status_code,
                "accessible": False,
                "requires_login": False,
                "post_exists": False,
                "content_preview": None
            }
            
            print(f"📊 كود الاستجابة: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # فحص محتوى الصفحة
                if "you must log in" in content or "log into facebook" in content:
                    verification["requires_login"] = True
                    print("🔒 البوست يتطلب تسجيل دخول")
                
                elif "this content isn't available" in content or "content not found" in content:
                    verification["post_exists"] = False
                    print("❌ البوست غير موجود أو محذوف")
                
                elif "facebook" in content and len(content) > 1000:
                    verification["accessible"] = True
                    verification["post_exists"] = True
                    print("✅ البوست متاح ويمكن الوصول إليه")
                    
                    # استخراج معاينة المحتوى
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
                    if title_match:
                        verification["content_preview"] = title_match.group(1).strip()
                        print(f"📄 عنوان الصفحة: {verification['content_preview'][:100]}...")
                
            elif response.status_code == 404:
                verification["post_exists"] = False
                print("❌ البوست غير موجود (404)")
                
            elif response.status_code == 403:
                verification["requires_login"] = True
                print("🔒 الوصول مرفوض - قد يتطلب صلاحيات خاصة")
            
            return verification
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الشبكة: {e}")
            return {"error": str(e), "accessible": False}

    def generate_report(self, post_url):
        """إنتاج تقرير شامل عن الرابط"""
        print("=" * 80)
        print("🔍 Facebook Link Analysis Report")
        print("=" * 80)
        
        # تحليل الرابط
        analysis = self.analyze_link(post_url)
        
        # التحقق من الوصول
        verification = self.verify_post_accessibility(post_url)
        
        # تجميع التقرير
        report = {
            "input_url": post_url,
            "analysis": analysis,
            "verification": verification,
            "recommendations": []
        }
        
        # إضافة توصيات
        if analysis["is_valid"] and verification.get("accessible"):
            report["recommendations"].append("✅ الرابط صحيح ويمكن استخدامه")
        
        if verification.get("requires_login"):
            report["recommendations"].append("🔒 تأكد من صحة الكوكيز وصلاحيتها")
        
        if not verification.get("post_exists"):
            report["recommendations"].append("❌ تحقق من صحة الرابط أو أن البوست لم يُحذف")
        
        if analysis.get("pfbid"):
            report["recommendations"].append("🔐 الرابط يستخدم التشفير الجديد (pfbid)")
        
        # طباعة ملخص التقرير
        print(f"\n📋 ملخص التقرير:")
        print("-" * 40)
        print(f"🔗 صحة الرابط: {'✅' if analysis['is_valid'] else '❌'}")
        print(f"🌐 إمكانية الوصول: {'✅' if verification.get('accessible') else '❌'}")
        print(f"🔒 يتطلب تسجيل دخول: {'نعم' if verification.get('requires_login') else 'لا'}")
        print(f"📄 البوست موجود: {'✅' if verification.get('post_exists', True) else '❌'}")
        
        if report["recommendations"]:
            print(f"\n💡 التوصيات:")
            for rec in report["recommendations"]:
                print(f"   {rec}")
        
        return report


def main():
    """الدالة الرئيسية"""
    
    # الرابط المراد تحليله
    test_url = "https://www.facebook.com/permalink.php?story_fbid=pfbid0oHgEXFDkcGqrQfNPr7HnYHyNPpSZ8NrpvJZHEMrjiimXszEiKYhZWAvdanXoFWRfl&id=100063997509036"
    
    print("🔍 Facebook Link Decoder & Validator")
    print("=" * 80)
    
    # إنشاء محلل الروابط
    decoder = FacebookLinkDecoder()
    
    # تحليل الرابط
    report = decoder.generate_report(test_url)
    
    # حفظ التقرير
    try:
        with open("link_analysis_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n💾 تم حفظ التقرير في: link_analysis_report.json")
    except Exception as e:
        print(f"❌ خطأ في حفظ التقرير: {e}")


if __name__ == "__main__":
    main()
