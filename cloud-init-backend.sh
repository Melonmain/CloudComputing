#!/bin/bash
# DATABASE_URL is injected by cloud-init.py before this script runs
# e.g. postgresql://postgres:postgres@<db-ip>:5432/appdb

apt-get update -y
apt-get install -y python3-pip python3-venv git

# Clone the backend from the integration branch
git clone --branch integration --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo

python3 -m venv /opt/backend/.venv
/opt/backend/.venv/bin/pip install -r /opt/repo/backend/requirements.txt

# Write .env so FastAPI picks up DATABASE_URL via pydantic-settings
cat > /opt/repo/backend/.env <<EOF
DATABASE_URL=${DATABASE_URL}
EOF

cat > /etc/systemd/system/backend.service <<SVCEOF
[Unit]
Description=Cloud Todo FastAPI Backend
After=network.target

[Service]
WorkingDirectory=/opt/repo/backend
Environment="DATABASE_URL=${DATABASE_URL}"
ExecStart=/opt/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable backend
systemctl start backend
