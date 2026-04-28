#!/bin/bash
apt-get update -y
apt-get install -y python3-pip python3-venv git

mkdir -p /opt/backend
python3 -m venv /opt/backend/.venv
/opt/backend/.venv/bin/pip install fastapi uvicorn[standard] pydantic pydantic-settings python-multipart python-jose[cryptography] passlib[bcrypt]

# TODO: replace with real deployment (git clone or scp)
cat > /opt/backend/main.py <<'PYEOF'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
PYEOF

cat > /etc/systemd/system/backend.service <<'SVCEOF'
[Unit]
Description=Cloud Todo FastAPI Backend
After=network.target

[Service]
WorkingDirectory=/opt/backend
ExecStart=/opt/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable backend
systemctl start backend
