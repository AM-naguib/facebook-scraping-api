#!/usr/bin/env python3
"""
Facebook API Monitor Script
===========================
سكربت بسيط لمراقبة حالة الـ API على السيرفر
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

class APIMonitor:
    """فئة مراقبة الـ API"""
    
    def __init__(self, api_url: str = "http://localhost:8091", log_file: str = "api_monitor.log"):
        """تهيئة المراقب"""
        self.api_url = api_url.rstrip('/')
        self.log_file = log_file
        self.last_status = None
        
        # إعداد Telegram (اختياري)
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
    def log_message(self, message: str, level: str = "INFO"):
        """تسجيل رسالة في ملف اللوج"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)  # طباعة على الشاشة
        
        # كتابة في ملف اللوج
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"❌ خطأ في كتابة اللوج: {e}")
    
    def send_telegram_alert(self, message: str):
        """إرسال تنبيه عبر Telegram (اختياري)"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": f"🤖 Facebook API Monitor\n\n{message}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.log_message("✅ تم إرسال تنبيه Telegram بنجاح")
            else:
                self.log_message(f"❌ فشل إرسال تنبيه Telegram: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"❌ خطأ في إرسال تنبيه Telegram: {e}")
    
    def check_health(self) -> Optional[Dict[str, Any]]:
        """فحص حالة الـ API"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log_message(f"❌ API returned status code: {response.status_code}", "ERROR")
                return None
                
        except requests.exceptions.ConnectionError:
            self.log_message("❌ لا يمكن الاتصال بالـ API - الخدمة متوقفة؟", "ERROR")
            return None
        except requests.exceptions.Timeout:
            self.log_message("❌ انتهت مهلة الاتصال بالـ API", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"❌ خطأ غير متوقع: {e}", "ERROR")
            return None
    
    def get_jobs_summary(self) -> Optional[Dict[str, Any]]:
        """جلب ملخص المهام"""
        try:
            response = requests.get(f"{self.api_url}/jobs", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception:
            return None
    
    def analyze_health_data(self, health_data: Dict[str, Any]) -> str:
        """تحليل بيانات الصحة وإرجاع تقرير"""
        status = health_data.get('status', 'unknown')
        active_jobs = health_data.get('active_jobs', 0)
        system_load = health_data.get('system_load', 'unknown')
        uptime = health_data.get('uptime', 'unknown')
        available_slots = health_data.get('available_slots', 0)
        
        # تحديد مستوى التحذير
        if status != 'healthy':
            level = "🚨 CRITICAL"
        elif system_load == 'heavy':
            level = "⚠️ WARNING"
        elif active_jobs == 0:
            level = "✅ IDLE"
        else:
            level = "✅ HEALTHY"
        
        report = (
            f"{level} - API Status: {status}\n"
            f"📊 Active Jobs: {active_jobs}\n"
            f"🔄 Available Slots: {available_slots}\n"
            f"📈 System Load: {system_load}\n"
            f"⏱️ Uptime: {uptime}"
        )
        
        return report
    
    def check_and_report(self):
        """فحص شامل وإعداد التقرير"""
        self.log_message("🔍 بدء فحص حالة الـ API...")
        
        # فحص الصحة
        health_data = self.check_health()
        
        if health_data is None:
            # API غير متاح
            if self.last_status != "down":
                alert_msg = "🚨 Facebook API is DOWN!\n\nالـ API لا يستجيب أو متوقف."
                self.send_telegram_alert(alert_msg)
                self.last_status = "down"
            
            self.log_message("❌ API غير متاح", "ERROR")
            return
        
        # تحليل البيانات
        report = self.analyze_health_data(health_data)
        self.log_message(report.replace('\n', ' | '))
        
        # فحص إذا تغيرت الحالة من down إلى up
        if self.last_status == "down":
            alert_msg = f"✅ Facebook API is back online!\n\n{report}"
            self.send_telegram_alert(alert_msg)
        
        # فحص التحذيرات
        status = health_data.get('status', 'unknown')
        system_load = health_data.get('system_load', 'unknown')
        active_jobs = health_data.get('active_jobs', 0)
        
        # تنبيهات خاصة
        if status != 'healthy' and self.last_status != "unhealthy":
            alert_msg = f"⚠️ API Status Changed!\n\n{report}"
            self.send_telegram_alert(alert_msg)
            self.last_status = "unhealthy"
        elif system_load == 'heavy' and self.last_status != "heavy":
            alert_msg = f"⚠️ High System Load!\n\n{report}"
            self.send_telegram_alert(alert_msg)
            self.last_status = "heavy"
        elif status == 'healthy' and system_load != 'heavy':
            self.last_status = "healthy"
        
        # جلب ملخص المهام (إضافي)
        jobs_data = self.get_jobs_summary()
        if jobs_data:
            total_jobs = jobs_data.get('total_jobs', 0)
            jobs_by_status = jobs_data.get('jobs_by_status', {})
            
            jobs_summary = f"📋 Total Jobs: {total_jobs}"
            if jobs_by_status:
                jobs_summary += f" | Status: {jobs_by_status}"
            
            self.log_message(jobs_summary)
    
    def run_continuous(self, interval_minutes: int = 5):
        """تشغيل المراقبة المستمرة"""
        self.log_message(f"🚀 بدء مراقبة الـ API على {self.api_url}")
        self.log_message(f"⏰ فحص كل {interval_minutes} دقائق")
        
        if self.telegram_token and self.telegram_chat_id:
            self.log_message("📱 تنبيهات Telegram مفعلة")
        else:
            self.log_message("📱 تنبيهات Telegram غير مفعلة (قم بتعيين TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID)")
        
        try:
            while True:
                self.check_and_report()
                self.log_message(f"😴 انتظار {interval_minutes} دقائق...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            self.log_message("⏹️ تم إيقاف المراقبة بواسطة المستخدم")
        except Exception as e:
            self.log_message(f"❌ خطأ في المراقبة المستمرة: {e}", "ERROR")


def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description="مراقب Facebook API")
    parser.add_argument('--url', '-u', default="http://localhost:8091", 
                       help="رابط الـ API (افتراضي: http://localhost:8091)")
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help="فترة الفحص بالدقائق (افتراضي: 5)")
    parser.add_argument('--log-file', '-l', default="api_monitor.log",
                       help="ملف اللوج (افتراضي: api_monitor.log)")
    parser.add_argument('--once', action='store_true',
                       help="فحص واحد فقط (بدون مراقبة مستمرة)")
    
    args = parser.parse_args()
    
    # إنشاء المراقب
    monitor = APIMonitor(api_url=args.url, log_file=args.log_file)
    
    if args.once:
        # فحص واحد فقط
        monitor.check_and_report()
    else:
        # مراقبة مستمرة
        monitor.run_continuous(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
