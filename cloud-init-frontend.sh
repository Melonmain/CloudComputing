#!/bin/bash
# NEXT_PUBLIC_API_URL and NEXT_PUBLIC_LOGIN_URL are injected by cloud-init.py before this script runs

apt-get update -y
apt-get install -y curl

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Clone the frontend from the integration branch
git clone --branch integration --single-branch \
    https://github.com/Melonmain/CloudComputing.git /opt/repo

# Write .env.local so Next.js embeds the correct API URL at build time
cat > /opt/repo/frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
NEXT_PUBLIC_LOGIN_URL=${NEXT_PUBLIC_LOGIN_URL}
EOF

cd /opt/repo/frontend
npm ci
npm run build

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

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable frontend
systemctl start frontend
