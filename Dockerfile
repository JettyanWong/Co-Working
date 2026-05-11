FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    nginx curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
RUN mkdir -p backend/uploads

RUN rm -f /etc/nginx/sites-enabled/default && \
    printf 'server {\n\
    listen 8109;\n\
    client_max_body_size 100M;\n\
    location / {\n\
        root /app/frontend;\n\
        index login.html index.html;\n\
    }\n\
    location /auth {\n\
        proxy_pass http://127.0.0.1:5001;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
    location /api {\n\
        proxy_pass http://127.0.0.1:5001;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
    location /socket.io {\n\
        proxy_pass http://127.0.0.1:5001;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
    location /static {\n\
        root /app/frontend;\n\
    }\n\
}\n' > /etc/nginx/sites-available/default && \
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

EXPOSE 8109

CMD ["sh", "-c", "cd /app/backend && python run.py & nginx -g 'daemon off;'"]
