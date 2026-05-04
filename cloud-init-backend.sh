#!/bin/bash
# DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS are injected by cloud-init.py before this script runs

LOG=/var/log/cloud-init-backend.log
exec > >(tee -a "$LOG") 2>&1
set -euo pipefail
trap 'echo "[ERROR] backend setup failed at line $LINENO — check $LOG"' ERR

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== Backend setup start ==="
log "DATABASE_URL host: $(echo "${DATABASE_URL}" | sed 's|.*@||')"

log "[1/6] apt-get update + install"
apt-get update -y
apt-get install -y python3-pip python3-venv git netcat-openbsd

log "[2/6] git clone (branch: Develop)"
git clone --branch Develop --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo
log "Repo cloned. Contents of /opt/repo: $(ls /opt/repo)"

log "[3/6] create venv + pip install"
python3 -m venv /opt/backend/.venv
/opt/backend/.venv/bin/pip install --quiet -r /opt/repo/backend/requirements.txt
log "pip install done"

log "[4/6] write .env"
cat > /opt/repo/backend/.env <<EOF
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
cat > /etc/systemd/system/backend.service <<SVCEOF
[Unit]
Description=Cloud Todo FastAPI Backend
After=network.target

[Service]
WorkingDirectory=/opt/repo/backend
Environment="DATABASE_URL=${DATABASE_URL}"
Environment="JWT_SECRET_KEY=${JWT_SECRET_KEY}"
Environment="CORS_ORIGINS=${CORS_ORIGINS}"
ExecStart=/opt/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StartLimitIntervalSec=0
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

log "[6/6] enable + start backend service"
systemctl daemon-reload
systemctl enable backend
systemctl start backend

sleep 3
if systemctl is-active --quiet backend; then
    log "=== Backend service is RUNNING ==="
else
    log "[ERROR] Backend service FAILED to start"
    journalctl -u backend --no-pager -n 50
    exit 1
fi
