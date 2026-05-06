#!/bin/bash

CONTAINER_NAME="smart-devops-container"
APP_PORT="8080"
HEALTH_URL="http://localhost:${APP_PORT}/health"
LOG_FILE="/var/log/app/health.log"
MAX_RETRIES=3
RETRY_DELAY=5

mkdir -p /var/log/app

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log()  { echo "[$(timestamp)] [INFO]  $*" | tee -a "$LOG_FILE"; }
ok()   { echo "[$(timestamp)] [OK]    ✅ $*" | tee -a "$LOG_FILE"; }
err()  { echo "[$(timestamp)] [ERROR] ❌ $*" | tee -a "$LOG_FILE"; }

log "─── Health Check Started ───────────────────"

attempt=1
while [ $attempt -le $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" \
        --connect-timeout 5 --max-time 10 "$HEALTH_URL" || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        ok "App is healthy (HTTP 200)"
        log "─── Health Check Complete: HEALTHY ─────────"
        exit 0
    fi

    log "Attempt $attempt/$MAX_RETRIES — HTTP $HTTP_CODE"
    sleep $RETRY_DELAY
    attempt=$((attempt + 1))
done

err "App is DOWN after $MAX_RETRIES retries — calling AI Decision Engine..."
log "Launching log_analyzer.py..."
python3 /opt/ai-engine/log_analyzer.py >> "$LOG_FILE" 2>&1

log "─── Health Check Complete: RECOVERY ATTEMPTED ───"