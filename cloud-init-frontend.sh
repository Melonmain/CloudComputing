#!/bin/bash
apt-get update -y
apt-get install -y curl

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# TODO: replace with real deployment (git clone or scp + npm run build)
mkdir -p /opt/frontend
cat > /opt/frontend/server.js <<'JSEOF'
const http = require('http');
http.createServer((_, res) => {
  res.end('Frontend placeholder — deploy Next.js build here');
}).listen(3000);
JSEOF

cat > /etc/systemd/system/frontend.service <<'SVCEOF'
[Unit]
Description=Cloud Todo Next.js Frontend
After=network.target

[Service]
WorkingDirectory=/opt/frontend
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable frontend
systemctl start frontend
