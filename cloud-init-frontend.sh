#!/bin/bash
# NEXT_PUBLIC_API_URL and NEXT_PUBLIC_LOGIN_URL are injected by cloud-init.py before this script runs

LOG=/var/log/cloud-init-frontend.log
exec > >(tee -a "$LOG") 2>&1
set -euo pipefail
trap 'echo "[ERROR] frontend setup failed at line $LINENO — check $LOG"' ERR

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== Frontend setup start ==="
log "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"
log "NEXT_PUBLIC_LOGIN_URL=${NEXT_PUBLIC_LOGIN_URL}"

log "[1/7] apt-get update + install curl + git"
apt-get update -y
apt-get install -y curl git

log "[2/7] install Node.js 20 LTS"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
log "Node version: $(node --version) | npm version: $(npm --version)"

log "[3/7] git clone (branch: main)"
git clone --branch main --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo
log "Repo cloned. Contents of /opt/repo: $(ls /opt/repo)"
log "Contents of /opt/repo/frontend: $(ls /opt/repo/frontend)"

log "[4/7] write .env.local"
cat > /opt/repo/frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
NEXT_PUBLIC_LOGIN_URL=${NEXT_PUBLIC_LOGIN_URL}
EOF
log ".env.local written:"
cat /opt/repo/frontend/.env.local

log "[5/7] npm ci"
cd /opt/repo/frontend
npm ci

log "[6/7] npm run build"
npm run build
log "Build complete"

log "[7/7] write systemd unit + start"
cat > /etc/systemd/system/frontend.service <<SVCEOF
[Unit]
Description=Cloud Todo Next.js Frontend
After=network.target

[Service]
WorkingDirectory=/opt/repo/frontend
Environment="PORT=80"
Environment="NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"
Environment="NEXT_PUBLIC_LOGIN_URL=${NEXT_PUBLIC_LOGIN_URL}"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable frontend
systemctl start frontend

sleep 5
if systemctl is-active --quiet frontend; then
    log "=== Frontend service is RUNNING on port 80 ==="
else
    log "[ERROR] Frontend service FAILED to start"
    journalctl -u frontend --no-pager -n 50
    exit 1
fi
