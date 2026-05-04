#!/bin/bash
# DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS are injected by cloud-init.py

apt-get update -y
apt-get install -y python3-pip python3-venv git

git clone --branch Develop --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo

python3 -m venv /opt/login/.venv
/opt/login/.venv/bin/pip install -r /opt/repo/login/requirements.txt

cat > /opt/repo/login/.env <<EOF
DATABASE_URL=${DATABASE_URL}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
CORS_ORIGINS=${CORS_ORIGINS}
EOF

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
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable login
systemctl start login
