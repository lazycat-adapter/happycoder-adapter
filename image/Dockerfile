# The upstream repository has separate Web and Server Dockerfiles. LazyCat's
# shared executor delivers one prepared image for one service, so this image
# builds both components and serves them behind one nginx process.

FROM node:20 AS deps

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 make g++ build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN corepack enable && corepack prepare pnpm@10.11.0 --activate

WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY scripts ./scripts
COPY patches ./patches

RUN mkdir -p packages/happy-app packages/happy-app-logs packages/happy-agent \
    packages/happy-cli packages/happy-server packages/happy-wire
COPY packages/happy-app/package.json packages/happy-app/
COPY packages/happy-app-logs/package.json packages/happy-app-logs/
COPY packages/happy-agent/package.json packages/happy-agent/
COPY packages/happy-cli/package.json packages/happy-cli/
COPY packages/happy-server/package.json packages/happy-server/
COPY packages/happy-wire/package.json packages/happy-wire/
COPY packages/happy-app/patches packages/happy-app/patches
COPY packages/happy-server/prisma packages/happy-server/prisma
COPY packages/happy-cli/scripts packages/happy-cli/scripts
COPY packages/happy-cli/tools packages/happy-cli/tools

RUN SKIP_HAPPY_WIRE_BUILD=1 pnpm install --frozen-lockfile

FROM deps AS builder

COPY packages/happy-app ./packages/happy-app
COPY packages/happy-app-logs ./packages/happy-app-logs
COPY packages/happy-agent ./packages/happy-agent
COPY packages/happy-server ./packages/happy-server
COPY packages/happy-wire ./packages/happy-wire

RUN pnpm --filter @slopus/happy-wire build
RUN pnpm --filter happy-server build

# Expo embeds this URL in the generated web bundle. The runtime entrypoint
# replaces the sentinel with the installed microserver's secondary domain.
RUN EXPO_PUBLIC_HAPPY_SERVER_URL=https://happyserver.__LAZYCAT_BOX_DOMAIN__ \
    pnpm --filter happy-app exec expo export --platform web --output-dir dist

FROM node:20-slim AS runner

WORKDIR /repo
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/conf.d/default.conf /etc/nginx/sites-enabled/default

ENV NODE_ENV=production
ENV DATA_DIR=/data
ENV PGLITE_DIR=/data/pglite
ENV PORT=3005
ENV TSX_TSCONFIG_PATH=/repo/packages/happy-server/tsconfig.json

COPY --from=builder /repo/node_modules /repo/node_modules
COPY --from=builder /repo/packages/happy-server /repo/packages/happy-server
COPY --from=builder /repo/packages/happy-wire /repo/packages/happy-wire
COPY --from=builder /repo/packages/happy-app/dist /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/happy.conf <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80 default_server;
    server_name happyserver.*;

    location / {
        proxy_pass http://127.0.0.1:3005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}

server {
    listen 80;
    server_name _;

    location /v1/ {
        proxy_pass http://127.0.0.1:3005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /health {
        proxy_pass http://127.0.0.1:3005;
        proxy_set_header Host $host;
    }

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri.html $uri/index.html /index.html =404;
    }
}
EOF

RUN cat > /usr/local/bin/happy-entrypoint <<'EOF'
#!/bin/sh
set -eu

: "${HANDY_MASTER_SECRET:?HANDY_MASTER_SECRET is required}"

if [ -n "${LAZYCAT_BOX_DOMAIN:-}" ]; then
    find /usr/share/nginx/html -type f -exec sed -i \
        "s|https://happyserver.__LAZYCAT_BOX_DOMAIN__|https://happyserver.${LAZYCAT_BOX_DOMAIN}|g" {} +
fi

node_modules/.bin/tsx packages/happy-server/sources/standalone.ts migrate
node_modules/.bin/tsx packages/happy-server/sources/standalone.ts serve &
server_pid=$!
nginx -g 'daemon off;' &
nginx_pid=$!

cleanup() {
    kill -TERM "$server_pid" "$nginx_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    wait "$nginx_pid" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

while kill -0 "$server_pid" 2>/dev/null && kill -0 "$nginx_pid" 2>/dev/null; do
    sleep 1
done

exit 1
EOF
RUN chmod 0755 /usr/local/bin/happy-entrypoint

VOLUME /data
EXPOSE 80
ENTRYPOINT ["/usr/local/bin/happy-entrypoint"]
