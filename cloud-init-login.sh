#!/bin/bash
# DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS are injected by cloud-init.py

LOG=/var/log/cloud-init-login.log
exec > >(tee -a "$LOG") 2>&1
set -euo pipefail
trap 'echo "[ERROR] login setup failed at line $LINENO — check $LOG"' ERR

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== Login service setup start ==="
log "DATABASE_URL host: $(echo "${DATABASE_URL}" | sed 's|.*@||')"

log "[1/6] apt-get update + install"
apt-get update -y
apt-get install -y python3-pip python3-venv git netcat-openbsd

log "[2/6] git clone (branch: feature/loadBalancer2)"
git clone --branch feature/loadBalancer2 --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo
log "Repo cloned. Contents of /opt/repo: $(ls /opt/repo)"
log "Contents of /opt/repo/login: $(ls /opt/repo/login)"

log "[3/6] create venv + pip install"
python3 -m venv /opt/login/.venv
/opt/login/.venv/bin/pip install --quiet -r /opt/repo/login/requirements.txt
log "pip install done"

log "[4/6] write .env"
cat > /opt/repo/login/.env <<EOF
DATABASE_URL=${DATABASE_URL}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
CORS_ORIGINS=${CORS_ORIGINS}
EOF
log ".env written"

log "[4b/6] wait for database to accept connections"
DB_HOST=$(echo "${DATABASE_URL}" | sed 's|.*@\(.*\):.*|\1|')
DB_PORT=5432
log "Polling ${DB_HOST}:${DB_PORT} (max 5 min)..."
for i in $(seq 1 60); do
    if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        log "Database reachable after ${i} attempts"
        break
    fi
    if [ "$i" -eq 60 ]; then
        log "[ERROR] Database not reachable after 5 minutes"
        exit 1
    fi
    log "  attempt ${i}/60 — not ready, retrying in 5s..."
    sleep 5
done

log "[5/6] write systemd unit"
cat > /etc/systemd/system/login.service <<SVCEOF
[Unit]
Description=Cloud Login Service
After=network.target

[Service]
WorkingDirectory=/opt/repo/login
Environment="DATABASE_URL=${DATABASE_URL}"
Environment="JWT_SECRET_KEY=${JWT_SECRET_KEY}"
Environment="CORS_ORIGINS=${CORS_ORIGINS}"
ExecStart=/opt/login/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10
StartLimitIntervalSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

log "[6/6] enable + start login service"
systemctl daemon-reload
systemctl enable login
systemctl start login

sleep 3
if systemctl is-active --quiet login; then
    log "=== Login service is RUNNING ==="
else
    log "[ERROR] Login service FAILED to start"
    journalctl -u login --no-pager -n 50
    exit 1
fi
