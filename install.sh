#!/bin/bash
set -e

echo "=== Installing dependencies ==="
apt install -y php-fpm php-mysql
pip install pymysql --break-system-packages

echo "=== Setting up database ==="
mysql -u root < setup.sql

echo "=== Installing stats reader ==="
cp fpv_live.py /opt/fpv_live.py
cp fpv-stats.service /etc/systemd/system/fpv-stats.service
systemctl daemon-reload
systemctl enable fpv-stats
systemctl start fpv-stats

echo "=== Installing web interface ==="
cp index.php /var/www/html/index.php
cp index.php /var/www/html/stats.php

echo "=== Done ==="
echo "Open https://your-domain/stats.php"
