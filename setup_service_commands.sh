#!/bin/bash

# Facebook API Service Setup Commands
# ===================================

echo "🚀 إعداد Facebook API كخدمة نظام..."

# 1. تحديد المسار الحالي
CURRENT_DIR=$(pwd)
echo "📍 المجلد الحالي: $CURRENT_DIR"

# 2. إنشاء نسخة محدثة من ملف الخدمة
cat > facebook-api-updated.service << EOF
[Unit]
Description=Facebook Scraper API
Documentation=file://README_API.md
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python run.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$CURRENT_DIR/api_results
ReadWritePaths=$CURRENT_DIR

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

echo "✅ تم إنشاء ملف الخدمة المحدث: facebook-api-updated.service"

echo ""
echo "🔧 الأوامر التالية لإعداد الخدمة:"
echo "sudo cp facebook-api-updated.service /etc/systemd/system/facebook-api.service"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable facebook-api"
echo "sudo systemctl start facebook-api"
echo "sudo systemctl status facebook-api"

echo ""
echo "📊 أوامر المراقبة:"
echo "sudo systemctl status facebook-api"
echo "sudo journalctl -u facebook-api -f"
echo "curl http://localhost:8091/health"

