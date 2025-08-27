# Facebook Reactions Scraper - دليل الاستخدام

## المميزات الرئيسية

✅ **سحب التفاعلات الذكي**: يدعم جميع أنواع الروابط والتفاعلات  
✅ **Pagination تلقائي**: يجلب جميع التفاعلات المطلوبة تلقائياً  
✅ **تحكم في المعدل**: تأخير قابل للتخصيص لتجنب الحظر  
✅ **إحصائيات شاملة**: تفصيل كامل لأنواع التفاعلات  
✅ **حفظ منظم**: ملفات JSON مع بيانات مفصلة  

## الاستخدام الأساسي

### 1. سحب 30 تفاعل (افتراضي)
```bash
python facebook_reactions_final.py -u "https://www.facebook.com/post/123"
```

### 2. سحب عدد محدد من التفاعلات
```bash
python facebook_reactions_final.py -u "رابط_البوست" -l 100
```

### 3. تخصيص التأخير بين الطلبات
```bash
python facebook_reactions_final.py -u "رابط_البوست" -l 50 -d 3.5
```

### 4. حفظ في ملف محدد
```bash
python facebook_reactions_final.py -u "رابط_البوست" -l 200 -o my_reactions.json
```

## أمثلة متقدمة

### مثال شامل مع جميع الخيارات
```bash
python facebook_reactions_final.py \
  --url "https://www.facebook.com/Mostafagamaalrock/posts/pfbid123..." \
  --limit 500 \
  --delay 2.5 \
  --output "mostafa_reactions.json" \
  --cookies "my_cookies.json"
```

### سحب تفاعلات من أنواع روابط مختلفة

#### رابط Permalink
```bash
python facebook_reactions_final.py -u "https://www.facebook.com/permalink.php?story_fbid=pfbid123&id=456"
```

#### رابط مباشر للبوست
```bash
python facebook_reactions_final.py -u "https://www.facebook.com/username/posts/pfbid123"
```

## هيكل ملف النتائج

```json
{
  "scraping_info": {
    "timestamp": "2025-01-26T15:30:00",
    "post_url": "https://facebook.com/post/123",
    "total_reactions": 150,
    "reaction_stats": {
      "LIKE": 85,
      "LOVE": 35,
      "HAHA": 15,
      "WOW": 10,
      "SORRY": 3,
      "ANGRY": 2
    },
    "scraper_version": "2.0"
  },
  "reactions": [
    {
      "user": {
        "id": "100012936518130",
        "name": "أسامة البنداري",
        "profile_url": "https://facebook.com/osama.elbindary.2025",
        "profile_picture": "https://scontent.faly8-2.fna.fbcdn.net/..."
      },
      "reaction_type": "LIKE",
      "timestamp": null
    }
  ]
}
```

## أنواع التفاعلات المدعومة

| التفاعل | الاسم الإنجليزي | الوصف |
|---------|----------------|-------|
| 👍 | LIKE | إعجاب |
| ❤️ | LOVE | حب |
| 😂 | HAHA | ضحك |
| 😮 | WOW | تعجب |
| 😢 | SORRY | حزن |
| 😡 | ANGRY | غضب |
| 🤗 | CARE | اهتمام |
| 💪 | SUPPORT | دعم |

## نصائح للاستخدام الأمثل

### 1. معدل الطلبات
- للحسابات العادية: `--delay 2.0` أو أكثر
- للحسابات الجديدة: `--delay 3.0` أو أكثر
- لتجنب الحظر: `--delay 5.0` للكميات الكبيرة

### 2. كمية البيانات
- للاختبار: `--limit 10-50`
- للاستخدام العادي: `--limit 100-500`
- للتحليل الشامل: `--limit 1000+`

### 3. أفضل الممارسات
```bash
# سحب تدريجي للمنشورات الكبيرة
python facebook_reactions_final.py -u "رابط" -l 1000 -d 3.0

# سحب سريع للمنشورات الصغيرة  
python facebook_reactions_final.py -u "رابط" -l 100 -d 1.5

# سحب آمن لتجنب الحظر
python facebook_reactions_final.py -u "رابط" -l 500 -d 5.0
```

## استكشاف الأخطاء

### مشكلة الكوكيز
```bash
❌ خطأ في تحميل الكوكيز
```
**الحل**: تأكد من وجود ملف `cookies.json` وصحة تنسيقه

### مشكلة التوكنز
```bash
❌ فشل في استخراج fb_dtsg
```
**الحل**: تأكد من صحة الكوكيز وعدم انتهاء صلاحيتها

### مشكلة الرابط
```bash
❌ لا يمكن استخراج معرف البوست
```
**الحل**: تأكد من صحة رابط البوست وأنه قابل للوصول

### حد المعدل
```bash
❌ فشل الطلب: 429
```
**الحل**: زيادة قيمة `--delay` أو الانتظار قبل المحاولة مجدداً

## أمثلة للاستخدامات المختلفة

### 1. تحليل تفاعلات منشور فيروسي
```bash
python facebook_reactions_final.py \
  -u "https://facebook.com/viral-post" \
  -l 2000 \
  -d 4.0 \
  -o viral_analysis.json
```

### 2. مراقبة تفاعلات صفحة
```bash
python facebook_reactions_final.py \
  -u "https://facebook.com/page/posts/123" \
  -l 500 \
  -d 2.0 \
  -o page_engagement.json
```

### 3. اختبار سريع
```bash
python facebook_reactions_final.py \
  -u "رابط_البوست" \
  -l 20 \
  -d 1.0
```

---

## ملاحظات مهمة

⚠️ **تنبيه**: استخدم السكربت بمسؤولية واحترم شروط استخدام فيسبوك  
🔒 **الخصوصية**: لا تشارك ملفات الكوكيز مع أحد  
📊 **الاستخدام**: مناسب للأبحاث والتحليلات الشخصية  

للمساعدة أو الأسئلة، راجع الوثائق أو اتصل بالدعم.
