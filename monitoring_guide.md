# دليل مراقبة Facebook Scraper API على السيرفر

## 🔍 طرق المراقبة المتاحة

### 1. Health Check Endpoints (مدمجة)

#### أ) فحص حالة النظام:
```bash
curl "http://your-server-ip:8000/health"
```

**الاستجابة:**
```json
{
  "status": "healthy",
  "active_jobs": 2,
  "available_slots": 3,
  "system_load": "light",
  "uptime": "5h 23m"
}
```

#### ب) ملخص المهام:
```bash
curl "http://your-server-ip:8000/jobs"
```

**الاستجابة:**
```json
{
  "total_jobs": 15,
  "active_jobs": 2,
  "available_slots": 3,
  "jobs_by_status": {
    "running": 2,
    "completed": 10,
    "failed": 2,
    "cancelled": 1
  }
}
```

#### ج) معلومات API:
```bash
curl "http://your-server-ip:8000/"
```

### 2. مراقبة تلقائية باستخدام Script

#### إنشاء سكربت مراقبة:
```bash
#!/bin/bash
# monitor_api.sh

API_URL="http://your-server-ip:8000"
LOG_FILE="/var/log/facebook-api-monitor.log"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # فحص Health
    health_response=$(curl -s "$API_URL/health")
    health_status=$(echo $health_response | jq -r '.status // "error"')
    
    if [ "$health_status" = "healthy" ]; then
        echo "[$timestamp] ✅ API is healthy" >> $LOG_FILE
        
        # استخراج معلومات إضافية
        active_jobs=$(echo $health_response | jq -r '.active_jobs // 0')
        system_load=$(echo $health_response | jq -r '.system_load // "unknown"')
        uptime=$(echo $health_response | jq -r '.uptime // "unknown"')
        
        echo "[$timestamp] 📊 Active jobs: $active_jobs, Load: $system_load, Uptime: $uptime" >> $LOG_FILE
    else
        echo "[$timestamp] ❌ API is DOWN or unhealthy!" >> $LOG_FILE
        
        # إرسال تنبيه (اختياري)
        # curl -X POST "https://hooks.slack.com/your-webhook" \
        #   -d '{"text":"🚨 Facebook API is DOWN!"}'
    fi
    
    # انتظار 5 دقائق
    sleep 300
done
```

### 3. مراقبة السيرفر نفسه

#### أ) استخدام htop/top:
```bash
# مراقبة استهلاك الذاكرة والمعالج
htop

# أو
top -p $(pgrep -f "uvicorn.*facebook")
```

#### ب) مراقبة Logs:
```bash
# متابعة logs المشروع
tail -f /path/to/your/app/logs/*.log

# أو logs النظام
journalctl -u your-api-service -f
```

#### ج) مراقبة المساحة:
```bash
# فحص مساحة مجلد النتائج
du -sh /path/to/api_results/

# فحص مساحة القرص
df -h
```

### 4. إعداد Systemd Service للمراقبة

#### إنشاء service file:
```ini
# /etc/systemd/system/facebook-api.service
[Unit]
Description=Facebook Scraper API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# تفعيل الخدمة
sudo systemctl enable facebook-api
sudo systemctl start facebook-api

# فحص الحالة
sudo systemctl status facebook-api
```

### 5. مراقبة خارجية

#### أ) UptimeRobot (مجاني):
- إضافة Monitor جديد
- نوع: HTTP(s)
- URL: `http://your-server:8000/health`
- Interval: كل 5 دقائق

#### ب) Pingdom:
- إعداد Uptime Check
- URL للفحص: `/health`
- تنبيهات عبر Email/SMS

#### ج) StatusCake:
- إعداد Website Monitor
- Response Code: 200
- Test String: `"status":"healthy"`

### 6. Dashboard بسيط

#### إنشاء صفحة مراقبة HTML:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Facebook API Monitor</title>
    <meta http-equiv="refresh" content="30">
</head>
<body>
    <h1>Facebook Scraper API Status</h1>
    <div id="status"></div>
    
    <script>
        async function checkStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                document.getElementById('status').innerHTML = `
                    <h2>Status: ${data.status}</h2>
                    <p>Active Jobs: ${data.active_jobs}</p>
                    <p>System Load: ${data.system_load}</p>
                    <p>Uptime: ${data.uptime}</p>
                `;
            } catch (error) {
                document.getElementById('status').innerHTML = 
                    '<h2 style="color:red">API is DOWN!</h2>';
            }
        }
        
        checkStatus();
        setInterval(checkStatus, 30000); // كل 30 ثانية
    </script>
</body>
</html>
```

### 7. تنبيهات Telegram Bot

#### سكربت Python للتنبيهات:
```python
import requests
import time
import json

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
API_URL = "http://your-server:8000"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                return True, data
        return False, None
    except:
        return False, None

# المراقبة المستمرة
while True:
    is_healthy, data = check_api_health()
    
    if not is_healthy:
        send_telegram_message("🚨 Facebook API is DOWN!")
    else:
        # تنبيه إذا كان الحمل عالي
        if data.get("system_load") == "heavy":
            send_telegram_message(f"⚠️ High system load: {data['active_jobs']} active jobs")
    
    time.sleep(300)  # كل 5 دقائق
```

## 📊 أهم المؤشرات للمراقبة:

1. **API Health**: هل الـ API يستجيب؟
2. **Active Jobs**: عدد المهام الجارية
3. **System Load**: حمولة النظام (idle/light/moderate/heavy)
4. **Uptime**: مدة تشغيل الخدمة
5. **Memory Usage**: استهلاك الذاكرة
6. **Disk Space**: مساحة التخزين (خاصة مجلد api_results)
7. **Response Time**: سرعة استجابة الـ API

## 🚨 علامات التحذير:

- **Status != "healthy"**
- **System Load = "heavy" لفترة طويلة**
- **Active Jobs عالق على نفس الرقم**
- **Response Time > 5 ثواني**
- **Disk Space < 10%**

هذا الدليل يوفر لك مراقبة شاملة للمشروع على السيرفر! 🎯
