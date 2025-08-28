#!/bin/bash

# Facebook API Monitor Script
# ===========================
# سكربت bash بسيط لمراقبة الـ API

# إعدادات
API_URL="${API_URL:-http://localhost:8091}"
LOG_FILE="${LOG_FILE:-api_monitor.log}"
CHECK_INTERVAL="${CHECK_INTERVAL:-300}"  # 5 دقائق
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# ألوان للعرض
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دالة تسجيل الرسائل
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""
    
    case $level in
        "ERROR") color=$RED ;;
        "WARN") color=$YELLOW ;;
        "INFO") color=$GREEN ;;
        "DEBUG") color=$BLUE ;;
    esac
    
    local log_entry="[$timestamp] [$level] $message"
    
    # طباعة ملونة
    echo -e "${color}${log_entry}${NC}"
    
    # كتابة في ملف اللوج
    echo "$log_entry" >> "$LOG_FILE"
}

# دالة إرسال تنبيه Telegram
send_telegram_alert() {
    local message="$1"
    
    if [[ -n "$TELEGRAM_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHAT_ID" \
            -d "text=🤖 Facebook API Monitor%0A%0A$message" \
            -d "parse_mode=HTML" > /dev/null
        
        if [[ $? -eq 0 ]]; then
            log_message "INFO" "✅ تم إرسال تنبيه Telegram"
        else
            log_message "ERROR" "❌ فشل إرسال تنبيه Telegram"
        fi
    fi
}

# دالة فحص صحة الـ API
check_api_health() {
    local response
    local status_code
    
    # فحص الـ health endpoint
    response=$(curl -s -w "%{http_code}" "$API_URL/health" --connect-timeout 10 --max-time 30)
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [[ "$status_code" == "200" ]]; then
        # استخراج المعلومات من JSON
        local api_status=$(echo "$response_body" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
        local active_jobs=$(echo "$response_body" | grep -o '"active_jobs":[0-9]*' | cut -d':' -f2)
        local system_load=$(echo "$response_body" | grep -o '"system_load":"[^"]*' | cut -d'"' -f4)
        local uptime=$(echo "$response_body" | grep -o '"uptime":"[^"]*' | cut -d'"' -f4)
        local available_slots=$(echo "$response_body" | grep -o '"available_slots":[0-9]*' | cut -d':' -f2)
        
        # تحديد مستوى الحالة
        local level="INFO"
        local emoji="✅"
        
        if [[ "$api_status" != "healthy" ]]; then
            level="ERROR"
            emoji="🚨"
        elif [[ "$system_load" == "heavy" ]]; then
            level="WARN"
            emoji="⚠️"
        elif [[ "$active_jobs" == "0" ]]; then
            emoji="😴"
        fi
        
        local status_msg="$emoji API Status: $api_status | Jobs: $active_jobs | Load: $system_load | Uptime: $uptime | Slots: $available_slots"
        log_message "$level" "$status_msg"
        
        # إرجاع الحالة للمقارنة
        echo "$api_status:$system_load:$active_jobs"
        return 0
    else
        log_message "ERROR" "❌ API لا يستجيب - Status Code: $status_code"
        send_telegram_alert "🚨 Facebook API is DOWN!%0A%0AStatus Code: $status_code"
        echo "down:unknown:0"
        return 1
    fi
}

# دالة فحص ملخص المهام
check_jobs_summary() {
    local response
    local status_code
    
    response=$(curl -s -w "%{http_code}" "$API_URL/jobs" --connect-timeout 10 --max-time 30)
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [[ "$status_code" == "200" ]]; then
        local total_jobs=$(echo "$response_body" | grep -o '"total_jobs":[0-9]*' | cut -d':' -f2)
        log_message "INFO" "📋 Total Jobs Processed: $total_jobs"
    fi
}

# دالة المراقبة الرئيسية
monitor_api() {
    local last_status=""
    local consecutive_failures=0
    local max_failures=3
    
    log_message "INFO" "🚀 بدء مراقبة Facebook API على $API_URL"
    log_message "INFO" "⏰ فحص كل $(($CHECK_INTERVAL / 60)) دقائق"
    
    if [[ -n "$TELEGRAM_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        log_message "INFO" "📱 تنبيهات Telegram مفعلة"
    else
        log_message "INFO" "📱 تنبيهات Telegram غير مفعلة"
    fi
    
    while true; do
        log_message "INFO" "🔍 فحص حالة الـ API..."
        
        current_status=$(check_api_health)
        api_health=$(echo "$current_status" | cut -d':' -f1)
        system_load=$(echo "$current_status" | cut -d':' -f2)
        active_jobs=$(echo "$current_status" | cut -d':' -f3)
        
        if [[ $? -eq 0 ]]; then
            # API يعمل
            consecutive_failures=0
            
            # فحص إذا عاد من حالة down
            if [[ "$last_status" == "down" ]]; then
                send_telegram_alert "✅ Facebook API is back online!%0A%0AStatus: $api_health%0ALoad: $system_load%0AActive Jobs: $active_jobs"
            fi
            
            # تحذيرات خاصة
            if [[ "$api_health" != "healthy" && "$last_status" != "unhealthy" ]]; then
                send_telegram_alert "⚠️ API Status Changed!%0A%0ANew Status: $api_health%0ALoad: $system_load%0AActive Jobs: $active_jobs"
                last_status="unhealthy"
            elif [[ "$system_load" == "heavy" && "$last_status" != "heavy" ]]; then
                send_telegram_alert "⚠️ High System Load!%0A%0ALoad: $system_load%0AActive Jobs: $active_jobs"
                last_status="heavy"
            elif [[ "$api_health" == "healthy" && "$system_load" != "heavy" ]]; then
                last_status="healthy"
            fi
            
            # فحص ملخص المهام
            check_jobs_summary
            
        else
            # API لا يعمل
            consecutive_failures=$((consecutive_failures + 1))
            
            if [[ "$consecutive_failures" -ge "$max_failures" && "$last_status" != "down" ]]; then
                send_telegram_alert "🚨 Facebook API has been DOWN for $(($consecutive_failures * $CHECK_INTERVAL / 60)) minutes!"
                last_status="down"
            fi
        fi
        
        log_message "INFO" "😴 انتظار $(($CHECK_INTERVAL / 60)) دقائق..."
        sleep "$CHECK_INTERVAL"
    done
}

# دالة فحص واحد فقط
single_check() {
    log_message "INFO" "🔍 فحص واحد لحالة الـ API..."
    check_api_health > /dev/null
    check_jobs_summary
    log_message "INFO" "✅ انتهى الفحص"
}

# دالة المساعدة
show_help() {
    echo "استخدام: $0 [OPTIONS]"
    echo ""
    echo "خيارات:"
    echo "  -u, --url URL          رابط الـ API (افتراضي: http://localhost:8000)"
    echo "  -i, --interval SEC     فترة الفحص بالثواني (افتراضي: 300)"
    echo "  -l, --log FILE         ملف اللوج (افتراضي: api_monitor.log)"
    echo "  -o, --once             فحص واحد فقط"
    echo "  -h, --help             عرض هذه المساعدة"
    echo ""
    echo "متغيرات البيئة:"
    echo "  TELEGRAM_TOKEN         توكن بوت Telegram للتنبيهات"
    echo "  TELEGRAM_CHAT_ID       معرف المحادثة في Telegram"
    echo ""
    echo "أمثلة:"
    echo "  $0                                    # مراقبة مستمرة"
    echo "  $0 -u http://server:8000 -i 60       # مراقبة كل دقيقة"
    echo "  $0 --once                             # فحص واحد فقط"
}

# معالجة المعاملات
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -i|--interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -l|--log)
            LOG_FILE="$2"
            shift 2
            ;;
        -o|--once)
            single_check
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "معامل غير معروف: $1"
            show_help
            exit 1
            ;;
    esac
done

# التحقق من وجود curl
if ! command -v curl &> /dev/null; then
    echo "❌ خطأ: curl غير مثبت"
    exit 1
fi

# بدء المراقبة
monitor_api
