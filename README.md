# Facebook Scraper API - الدليل الشامل

## 📋 نظرة عامة

API متقدم لسحب التفاعلات والكومنتات من فيسبوك باستخدام Threading للمعالجة المتوازية.

## 🚀 المميزات الرئيسية

- **معالجة متوازية**: تشغيل عدة مهام في نفس الوقت (حتى 5 مهام متزامنة)
- **تتبع مباشر**: متابعة تقدم المهام في الوقت الفعلي
- **تنظيف تلقائي**: حذف الملفات المنتهية الصلاحية تلقائياً
- **معالجة أخطاء شاملة**: رسائل خطأ واضحة ومفيدة
- **دعم العربية الكامل**: واجهة وتوثيق باللغة العربية
- **نظام مراقبة متقدم**: أدوات مراقبة متعددة للسيرفر

---

## 📦 التثبيت والتشغيل

### المتطلبات
- Python 3.10+ (الأفضل)
- pip3
- مساحة تخزين كافية للنتائج

### خطوات التثبيت السريع

#### 1. فحص وتحضير البيئة:
```bash
# فحص إصدار Python
python3 --version

# تثبيت pip إذا لم يكن موجود (Linux/Ubuntu)
sudo apt update
sudo apt install python3-pip python3-venv -y

# إنشاء بيئة افتراضية (مستحسن)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt
```

#### 2. التشغيل السريع:
```bash
# تشغيل مباشر
python3 run.py

# أو باستخدام uvicorn مباشرة
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8091
```

#### 3. فحص التشغيل:
```bash
# في terminal آخر
curl http://localhost:8091/health
```

### التشغيل في الخلفية:

#### الطريقة 1: nohup
```bash
nohup python3 run.py > api.log 2>&1 &
```

#### الطريقة 2: screen
```bash
screen -S facebook-api
python3 run.py
# اضغط Ctrl+A ثم D للخروج
```

#### الطريقة 3: كخدمة نظام (الأفضل)
```bash
# نسخ وتحديث ملف الخدمة
sudo cp facebook-api.service /etc/systemd/system/
sudo nano /etc/systemd/system/facebook-api.service

# تحديث المسارات في الملف:
# WorkingDirectory=/path/to/your/project
# ExecStart=/path/to/your/venv/bin/python run.py

# تفعيل وتشغيل الخدمة
sudo systemctl daemon-reload
sudo systemctl enable facebook-api
sudo systemctl start facebook-api
sudo systemctl status facebook-api
```

---

## 🌐 API المتاحة

### نقاط الواجهة الأساسية

#### التفاعلات (Reactions)
- `POST /api/v1/reactions/scrape` - بدء سحب التفاعلات
- `GET /api/v1/reactions/status/{job_id}` - متابعة حالة المهمة
- `GET /api/v1/reactions/download/{job_id}` - تحميل النتائج

#### الكومنتات (Comments)
- `POST /api/v1/comments/scrape` - بدء سحب الكومنتات
- `GET /api/v1/comments/status/{job_id}` - متابعة حالة المهمة
- `GET /api/v1/comments/download/{job_id}` - تحميل النتائج

#### إدارة النظام
- `GET /health` - فحص حالة النظام
- `GET /jobs` - ملخص المهام
- `GET /docs` - التوثيق التفاعلي
- `GET /` - معلومات عامة عن API

## 📝 أمثلة الاستخدام العملية

### 1. سحب التفاعلات مع التوثيق الكامل

```bash
curl -X POST "http://localhost:8091/api/v1/reactions/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "post_url": "https://www.facebook.com/post/123456789",
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
      },
      {
        "domain": ".facebook.com",
        "name": "xs",
        "value": "your_xs_token_here",
        "path": "/",
        "secure": true,
        "httpOnly": true
      }
    ]
  }'
```

**الاستجابة المتوقعة:**
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
curl "http://localhost:8091/api/v1/reactions/status/reactions_20241215_143022_abc123"
```

**الاستجابة التفصيلية:**
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

### 3. تحميل النتائج النهائية

```bash
curl -O "http://localhost:8091/api/v1/reactions/download/reactions_20241215_143022_abc123"
```

---

## ⚙️ إعدادات النظام

### إعدادات التشغيل الرئيسية
```python
# في app/config.py
class Settings:
    # إعدادات الخادم
    HOST: str = "0.0.0.0"
    PORT: int = 8091
    DEBUG: bool = True
    
    # إعدادات Threading
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT_MINUTES: int = 30
    
    # إعدادات التخزين
    RESULTS_DIR: str = "api_results"
    CLEANUP_AFTER_HOURS: int = 24
    
    # إعدادات الأمان
    API_KEY_HEADER: str = "X-API-Key"
    ALLOWED_ORIGINS: list = ["*"]
```

### الكوكيز المطلوبة للمصادقة
- `c_user`: معرف المستخدم في فيسبوك
- `xs`: توكن الجلسة (Token)
- `fr`: توكن التحديث (Refresh Token)

### نصائح الأمان الهامة
- استخدم HTTPS في الإنتاج
- احم ملفات الكوكيز بصلاحيات محدودة
- راقب معدل الطلبات لتجنب الحظر
- استخدم معرفات API للمصادقة
- لا تشارك الكوكيز مع أطراف ثالثة

---

## 🔍 نظام المراقبة المتقدم

### فحص حالة النظام السريع

#### الفحص الأساسي:
```bash
# فحص حالة API
curl "http://your-server-ip:8091/health"

# ملخص المهام
curl "http://your-server-ip:8091/jobs"

# معلومات النظام
curl "http://your-server-ip:8091/"
```

### أدوات المراقبة المتاحة

#### 1. سكربت Python للمراقبة:
```bash
# فحص واحد
python monitor_api.py --once

# مراقبة مستمرة (كل 5 دقائق)
python monitor_api.py

# مراقبة مخصصة
python monitor_api.py --url http://your-server:8091 --interval 120
```

#### 2. سكربت Bash (Linux/Mac):
```bash
# فحص واحد
./monitor_api.sh --once

# مراقبة مستمرة
./monitor_api.sh --url http://your-server:8091 --interval 300
```

### تفعيل تنبيهات Telegram

#### إنشاء بوت Telegram:
1. تحدث مع [@BotFather](https://t.me/botfather)
2. أرسل `/newbot`
3. اتبع التعليمات واحصل على التوكن

#### الحصول على Chat ID:
1. أرسل رسالة لبوتك
2. زر: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. ابحث عن `"chat":{"id":-123456789`

#### تعيين متغيرات البيئة:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="-123456789"
```

### المؤشرات المهمة للمراقبة

| المؤشر | الوصف | القيم الطبيعية | علامات التحذير |
|---------|--------|----------------|------------------|
| **Status** | حالة الـ API | `healthy` | `unhealthy`, `error` |
| **Active Jobs** | المهام الجارية | 0-5 | > 5 أو عالق |
| **System Load** | حمولة النظام | `idle`, `light`, `moderate` | `heavy` |
| **Available Slots** | المساحات المتاحة | > 0 | = 0 |
| **Uptime** | مدة التشغيل | متزايدة | انقطاع متكرر |

---

## 🛠️ استكشاف الأخطاء والحلول

### الأخطاء الشائعة والحلول

#### 1. `429 Too Many Requests`
**السبب:** تجاوز الحد الأقصى للمهام المتزامنة  
**الحل:** انتظر انتهاء بعض المهام أو زيادة `MAX_CONCURRENT_JOBS`

#### 2. `400 Invalid URL`
**السبب:** رابط فيسبوك غير صحيح أو غير مدعوم  
**الحل:** تأكد من صحة الرابط وأنه من فيسبوك

#### 3. `401 Invalid Cookies`
**السبب:** كوكيز منتهية الصلاحية أو غير صحيحة  
**الحل:** حدث الكوكيز من المتصفح

#### 4. `500 Internal Server Error`
**السبب:** خطأ في النظام أو في كود السكرابر  
**الحل:** فحص logs الخادم للتفاصيل

### فحص النظام عند المشاكل

#### فحص إذا كان API يعمل:
```bash
# فحص العملية
ps aux | grep uvicorn

# فحص البورت
netstat -tlnp | grep :8091

# فحص اللوجز
tail -f api_monitor.log
```

#### فحص استهلاك الموارد:
```bash
# فحص الذاكرة
free -h
htop

# فحص مساحة القرص
df -h
du -sh api_results/
```

#### أوامر إدارة الخدمة:
```bash
# إعادة تشغيل
sudo systemctl restart facebook-api

# متابعة اللوجز
journalctl -u facebook-api -f

# فحص الحالة التفصيلية
sudo systemctl status facebook-api
```

---

## 🏗️ هيكل المشروع التفصيلي

```
facebook-scraper-api/
├── app/                     # التطبيق الرئيسي
│   ├── api/                # API endpoints
│   │   ├── comments.py     # واجهة الكومنتات
│   │   └── reactions.py    # واجهة التفاعلات
│   ├── core/               # المنطق الأساسي
│   │   └── job_manager.py  # إدارة المهام والـ Threading
│   ├── models/             # نماذج البيانات
│   │   ├── requests.py     # نماذج الطلبات
│   │   └── responses.py    # نماذج الاستجابات
│   ├── scrapers/           # محركات السحب
│   │   ├── comments_scraper.py   # سحب الكومنتات
│   │   └── reactions_scraper.py  # سحب التفاعلات
│   ├── config.py           # إعدادات النظام
│   └── main.py             # تطبيق FastAPI الرئيسي
├── api_results/            # مجلد النتائج
├── monitor_api.py          # مراقب Python
├── monitor_api.sh          # مراقب Bash
├── facebook-api.service    # ملف خدمة systemd
├── requirements.txt        # المتطلبات
├── run.py                  # مشغل التطبيق
└── README.md              # هذا الملف
```

---

## 🔄 تطوير وإضافة ميزات جديدة

### إضافة endpoint جديد:

#### 1. إنشاء ملف API جديد:
```python
# في app/api/new_feature.py
from fastapi import APIRouter
from app.models.requests import NewFeatureRequest
from app.models.responses import JobResponse

router = APIRouter()

@router.post("/scrape")
async def scrape_new_feature(request: NewFeatureRequest):
    # منطق الميزة الجديدة
    pass
```

#### 2. إنشاء Scraper جديد:
```python
# في app/scrapers/new_feature_scraper.py
class NewFeatureScraper:
    def __init__(self, cookies):
        self.cookies = cookies
    
    def scrape(self, params):
        # منطق السحب
        pass
```

#### 3. تحديث main.py:
```python
# في app/main.py
from app.api import new_feature

app.include_router(
    new_feature.router, 
    prefix="/api/v1/new-feature", 
    tags=["new-feature"]
)
```

### اختبار الأداء:
```bash
# اختبار الحمولة
ab -n 100 -c 10 http://localhost:8091/health

# مراقبة الذاكرة
htop

# اختبار API محدد
curl -X POST "http://localhost:8091/api/v1/reactions/scrape" \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

---

## 📊 معلومات التوافق والأداء

### متطلبات النظام الموصى بها:
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB للاستخدام المكثف)
- **Storage**: 10GB+ مساحة فارغة
- **Network**: اتصال إنترنت مستقر

### Python والمكتبات المدعومة:

| التقنية | الإصدار المستخدم | دعم Python 3.10 | الحالة |
|---------|------------------|------------------|---------|
| **Python** | 3.10+ | ✅ الأفضل | ممتاز |
| **FastAPI** | 0.104.1 | ✅ مدعوم كاملاً | ممتاز |
| **Uvicorn** | 0.24.0 | ✅ مدعوم كاملاً | ممتاز |
| **Pydantic** | 2.5.0 | ✅ مدعوم كاملاً | ممتاز |
| **Requests** | 2.31.0 | ✅ مدعوم كاملاً | ممتاز |

### الأداء المتوقع:
- **التفاعلات**: 50-100 تفاعل/دقيقة
- **الكومنتات**: 30-60 كومنت/دقيقة
- **المهام المتزامنة**: حتى 5 مهام
- **استجابة API**: < 2 ثانية

---

## 📞 الدعم وحل المشاكل

### نصائح الصيانة الدورية:

#### تنظيف النتائج القديمة:
```bash
# حذف الملفات أقدم من 7 أيام
find api_results/ -name "*.json" -mtime +7 -delete

# فحص مساحة التخزين
du -sh api_results/
```

#### تحديث المتطلبات:
```bash
# تحديث المكتبات
pip install -r requirements.txt --upgrade

# فحص المكتبات القديمة
pip list --outdated
```

#### النسخ الاحتياطي:
```bash
# نسخ إعدادات مهمة
cp cookies.json cookies_backup.json
cp app/config.py config_backup.py

# نسخ النتائج المهمة
tar -czf api_results_backup.tar.gz api_results/
```

### الحصول على المساعدة:

1. **فحص `/docs`** للتوثيق التفاعلي
2. **مراجعة logs** الخادم للتفاصيل
3. **استخدام `/health`** لفحص حالة النظام
4. **فحص هذا الملف** للحلول الشائعة

### معلومات الاتصال والدعم الفني:
- **التوثيق التفاعلي**: `http://your-server:8091/docs`
- **حالة النظام**: `http://your-server:8091/health`
- **ملخص المهام**: `http://your-server:8091/jobs`

---

## 🎯 الخلاصة والتوصيات

### ما يجعل هذا المشروع مميز:
- ✅ **Python 3.10 مثالي** - لا يحتاج تغيير
- ✅ **جميع المكتبات متوافقة 100%**
- ✅ **نظام مراقبة شامل ومتقدم**
- ✅ **توثيق عربي كامل ومفصل**
- ✅ **دعم Threading للأداء العالي**
- ✅ **معالجة أخطاء ذكية وشاملة**

### التوصيات للاستخدام الأمثل:
1. **استخدم Python 3.10** - الأفضل للمشروع
2. **فعّل المراقبة** للحصول على أداء مستقر
3. **نظّف النتائج** دورياً لتوفير المساحة
4. **استخدم HTTPS** في الإنتاج
5. **اعمل نسخ احتياطية** للإعدادات المهمة

**المشروع جاهز للاستخدام بدون أي تغييرات إضافية! 🚀**

---

*آخر تحديث: ديسمبر 2024*
