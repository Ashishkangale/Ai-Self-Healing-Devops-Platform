FROM node:18-alpine AS builder

WORKDIR /app

COPY app/package*.json ./

RUN npm ci --only=production

FROM node:18-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

RUN mkdir -p /var/log/app && chown -R appuser:appgroup /var/log/app

COPY --from=builder /app/node_modules ./node_modules

COPY app/server.js ./server.js

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["node", "server.js"]
