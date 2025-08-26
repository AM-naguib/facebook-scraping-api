#!/usr/bin/env python3
"""
اختبار سكربت جلب الكومنتات من فيسبوك
"""

from facebook_comments_scraper import FacebookCommentsScraper

def test_scraper():
    """اختبار السكربت"""
    
    # رابط البوست للاختبار
    test_url = "https://www.facebook.com/bantalrb.heba/posts/pfbid029Ra2EaMcbGn5miZxq5DHx2cS3NYiYGav7TBMzFWQ8JQ8fvs3T1BGpVKnR4sN44LVl"
    
    print("🧪 بدء اختبار سكربت جلب الكومنتات")
    print("=" * 50)
    
    # إنشاء مكشطة الكومنتات
    scraper = FacebookCommentsScraper()
    
    # اختبار تحميل الكوكيز
    print("1️⃣ اختبار تحميل الكوكيز...")
    if scraper.load_cookies():
        print("✅ تم تحميل الكوكيز بنجاح")
    else:
        print("❌ فشل في تحميل الكوكيز")
        return
    
    # اختبار استخراج التوكنز
    print("\n2️⃣ اختبار استخراج التوكنز...")
    if scraper.extract_tokens():
        print("✅ تم استخراج التوكنز بنجاح")
    else:
        print("❌ فشل في استخراج التوكنز")
        return
    
    # اختبار تحليل رابط البوست
    print("\n3️⃣ اختبار تحليل رابط البوست...")
    post_info = scraper.analyze_post_url(test_url)
    if post_info and (post_info.get('pfbid') or post_info.get('post_id')):
        print("✅ تم تحليل رابط البوست بنجاح")
        print(f"   📋 نوع المعرف: {list(post_info.keys())}")
    else:
        print("❌ فشل في تحليل رابط البوست")
        return
    
    # اختبار جلب صفحة واحدة من الكومنتات
    print("\n4️⃣ اختبار جلب كومنتات (صفحة واحدة)...")
    try:
        results = scraper.scrape_all_comments(
            post_url=test_url,
            delay=2,  # تقليل الانتظار للاختبار
            max_pages=1  # صفحة واحدة فقط للاختبار
        )
        
        if results and results.get('comments'):
            print(f"✅ تم جلب {len(results['comments'])} كومنت بنجاح")
            print("\n📋 عينة من النتائج:")
            for i, comment in enumerate(results['comments'][:3]):
                print(f"   {i+1}. {comment.get('author_name', 'Unknown')}")
                text = comment.get('text', '')[:50]
                if len(comment.get('text', '')) > 50:
                    text += "..."
                print(f"      💭 {text}")
        else:
            print("⚠️ لم يتم جلب أي كومنتات (قد يكون البوست خاص أو محذوف)")
    
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 انتهى الاختبار")

if __name__ == "__main__":
    test_scraper()
