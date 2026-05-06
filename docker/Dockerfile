# ─── Stage 1: Builder ─────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files first (Docker layer caching)
COPY app/package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# ─── Stage 2: Production Image ────────────────────────────
FROM node:18-alpine

# Security: run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Create log directory with correct permissions
RUN mkdir -p /var/log/app && chown -R appuser:appgroup /var/log/app

# Copy built dependencies from builder stage
COPY --from=builder /app/node_modules ./node_modules

# Copy app source
COPY app/server.js ./server.js

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose app port
EXPOSE 8080

# Health check built into Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/health || exit 1

# Start app
CMD ["node", "server.js"]