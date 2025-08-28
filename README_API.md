# Facebook Scraper API

## 📋 نظرة عامة

API متقدم لسحب التفاعلات والكومنتات من فيسبوك باستخدام Threading للمعالجة المتوازية.

## 🚀 المميزات

- **معالجة متوازية**: تشغيل عدة مهام في نفس الوقت
- **تتبع مباشر**: متابعة تقدم المهام في الوقت الفعلي
- **تنظيف تلقائي**: حذف الملفات المنتهية الصلاحية تلقائياً
- **معالجة أخطاء شاملة**: رسائل خطأ واضحة ومفيدة
- **دعم العربية**: واجهة وتوثيق باللغة العربية

## 📦 التثبيت

```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# تشغيل الخادم
python run.py
```

## 🌐 الواجهات المتاحة

### التفاعلات (Reactions)
- `POST /api/v1/reactions/scrape` - بدء سحب التفاعلات
- `GET /api/v1/reactions/status/{job_id}` - متابعة حالة المهمة
- `GET /api/v1/reactions/download/{job_id}` - تحميل النتائج

### الكومنتات (Comments)
- `POST /api/v1/comments/scrape` - بدء سحب الكومنتات
- `GET /api/v1/comments/status/{job_id}` - متابعة حالة المهمة
- `GET /api/v1/comments/download/{job_id}` - تحميل النتائج

### النظام
- `GET /health` - فحص حالة النظام
- `GET /jobs` - ملخص المهام
- `GET /docs` - التوثيق التفاعلي

## 📝 أمثلة الاستخدام

### 1. سحب التفاعلات

```bash
curl -X POST "http://localhost:8000/api/v1/reactions/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "post_url": "https://www.facebook.com/post/123",
    "limit": 100,
    "delay": 2.5,
    "cookies": [
      {
        "domain": ".facebook.com",
        "name": "c_user",
        "value": "100076386722911",
        "path": "/",
        "secure": true,
        "httpOnly": false
      }
    ]
  }'
```

**الاستجابة:**
```json
{
  "job_id": "reactions_20241215_143022_abc123",
  "status": "running",
  "message": "تم بدء سحب التفاعلات بنجاح",
  "estimated_time": "2-5 دقائق",
  "created_at": "2024-12-15T14:30:22Z"
}
```

### 2. متابعة حالة المهمة

```bash
curl "http://localhost:8000/api/v1/reactions/status/reactions_20241215_143022_abc123"
```

**الاستجابة:**
```json
{
  "job_id": "reactions_20241215_143022_abc123",
  "status": "running",
  "progress": {
    "percentage": 45,
    "message": "جاري جلب الصفحة 3...",
    "current_page": 3,
    "items_scraped": 150,
    "updated_at": "2024-12-15T14:32:15Z"
  },
  "started_at": "2024-12-15T14:30:25Z"
}
```

### 3. تحميل النتائج

```bash
curl -O "http://localhost:8000/api/v1/reactions/download/reactions_20241215_143022_abc123"
```

## ⚙️ الإعدادات

يمكن تخصيص الإعدادات في `app/config.py`:

```python
class Settings:
    # إعدادات الخادم
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # إعدادات Threading
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_MINUTES: int = 30
    
    # إعدادات التخزين
    RESULTS_DIR: str = "api_results"
    CLEANUP_AFTER_HOURS: int = 24
```

## 🔒 الأمان

### الكوكيز المطلوبة
- `c_user`: معرف المستخدم
- `xs`: توكن الجلسة
- `fr`: توكن التحديث

### نصائح الأمان
- استخدم HTTPS في الإنتاج
- احم ملفات الكوكيز
- راقب معدل الطلبات
- استخدم معرفات API للمصادقة

## 📊 مراقبة الأداء

### فحص حالة النظام
```bash
curl "http://localhost:8000/health"
```

### ملخص المهام
```bash
curl "http://localhost:8000/jobs"
```

## 🛠️ استكشاف الأخطاء

### أخطاء شائعة

1. **429 Too Many Requests**
   - السبب: تجاوز الحد الأقصى للمهام المتزامنة
   - الحل: انتظر انتهاء بعض المهام

2. **400 Invalid URL**
   - السبب: رابط فيسبوك غير صحيح
   - الحل: تأكد من صحة الرابط

3. **401 Invalid Cookies**
   - السبب: كوكيز منتهية الصلاحية أو غير صحيحة
   - الحل: حدث الكوكيز من المتصفح

## 📁 هيكل المشروع

```
facebook-scraper-api/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core logic (job manager)
│   ├── models/       # Pydantic models
│   ├── scrapers/     # Scraper classes
│   ├── config.py     # Configuration
│   └── main.py       # FastAPI application
├── api_results/      # Results storage
├── requirements.txt  # Dependencies
├── run.py           # Runner script
└── README_API.md    # Documentation
```

## 🔄 تطوير المشروع

### إضافة ميزة جديدة
1. أنشئ endpoint في `app/api/`
2. أضف models في `app/models/`
3. حدث `app/main.py` لتضمين الـ router

### اختبار الأداء
```bash
# اختبار الحمولة
ab -n 100 -c 10 http://localhost:8000/health

# مراقبة الذاكرة
htop
```

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- تحقق من `/docs` للتوثيق التفاعلي
- راجع logs الخادم للتفاصيل
- استخدم `/health` لفحص حالة النظام

