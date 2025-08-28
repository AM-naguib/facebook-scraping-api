# 🔍 دليل المراقبة السريع - Facebook Scraper API

## 🚀 البدء السريع

### 1. فحص سريع للـ API:
```bash
curl "http://your-server-ip:8091/health"
```

### 2. استخدام سكربت Python للمراقبة:
```bash
# فحص واحد
python monitor_api.py --once

# مراقبة مستمرة (كل 5 دقائق)
python monitor_api.py

# مراقبة مخصصة
python monitor_api.py --url http://your-server:8091 --interval 2
```

### 3. استخدام سكربت Bash (Linux/Mac):
```bash
# فحص واحد
./monitor_api.sh --once

# مراقبة مستمرة
./monitor_api.sh --url http://your-server:8091 --interval 300
```

## 📱 تفعيل تنبيهات Telegram

### 1. إنشاء بوت Telegram:
- تحدث مع [@BotFather](https://t.me/botfather)
- أرسل `/newbot`
- اتبع التعليمات واحصل على التوكن

### 2. الحصول على Chat ID:
- أرسل رسالة لبوتك
- زر: `https://api.telegram.org/bot<TOKEN>/getUpdates`
- ابحث عن `"chat":{"id":-123456789`

### 3. تعيين متغيرات البيئة:
```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="-123456789"
```

## 🖥️ تشغيل كخدمة على Linux

### 1. نسخ ملفات الخدمة:
```bash
sudo cp facebook-api.service /etc/systemd/system/
sudo cp facebook-api-monitor.service /etc/systemd/system/
```

### 2. تحديث المسارات في الملفات:
```bash
sudo nano /etc/systemd/system/facebook-api.service
# غيّر /path/to/your/ إلى المسار الفعلي
```

### 3. تفعيل وتشغيل الخدمات:
```bash
sudo systemctl daemon-reload
sudo systemctl enable facebook-api
sudo systemctl enable facebook-api-monitor
sudo systemctl start facebook-api
sudo systemctl start facebook-api-monitor
```

### 4. فحص الحالة:
```bash
sudo systemctl status facebook-api
sudo systemctl status facebook-api-monitor
```

## 📊 المؤشرات المهمة للمراقبة

| المؤشر | الوصف | القيم الطبيعية |
|---------|--------|----------------|
| **Status** | حالة الـ API | `healthy` |
| **Active Jobs** | المهام الجارية | 0-5 |
| **System Load** | حمولة النظام | `idle`, `light`, `moderate` |
| **Available Slots** | المساحات المتاحة | > 0 |
| **Uptime** | مدة التشغيل | متزايدة |

## 🚨 علامات التحذير

- ❌ **Status != "healthy"** - مشكلة في الـ API
- ⚠️ **System Load = "heavy"** - حمولة عالية
- 🔄 **Active Jobs عالق** - مهام معلقة
- 💾 **Available Slots = 0** - النظام مشغول بالكامل

## 🛠️ استكشاف الأخطاء

### API لا يستجيب:
```bash
# فحص إذا كان يعمل
ps aux | grep uvicorn

# فحص البورت
netstat -tlnp | grep :8000

# فحص اللوجز
tail -f api_monitor.log
```

### مشاكل الذاكرة:
```bash
# فحص استهلاك الذاكرة
free -h
htop

# فحص مساحة القرص
df -h
du -sh api_results/
```

## 📞 الدعم السريع

### فحص سريع شامل:
```bash
# فحص حالة الخدمة
curl -s http://localhost:8091/health | jq '.'

# فحص ملخص المهام
curl -s http://localhost:8091/jobs | jq '.'

# فحص معلومات النظام
curl -s http://localhost:8091/ | jq '.features'
```

### أوامر مفيدة:
```bash
# إعادة تشغيل الخدمة
sudo systemctl restart facebook-api

# متابعة اللوجز المباشرة
journalctl -u facebook-api -f

# فحص استهلاك الموارد
top -p $(pgrep -f uvicorn)
```

---

💡 **نصيحة**: احتفظ بهذا الدليل في مكان سهل الوصول لمراجعة سريعة عند الحاجة!
