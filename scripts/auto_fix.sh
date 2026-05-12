#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#   auto_fix.sh — Smart Self-Healing DevOps Platform
#   Attempts automated recovery of the failed application
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# CONFIGURATION
CONTAINER_NAME="smart-devops-container"
APP_IMAGE="smart-devops-app:latest"
APP_PORT="8080"
HEALTH_URL="http://localhost:${APP_PORT}/health"
LOG_FILE="/var/log/app/autofix.log"
MAX_WAIT=60     # seconds to wait for recovery
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

# LOGGING
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log()  { echo "[$(timestamp)] [FIX]   $*" | tee -a "$LOG_FILE"; }
ok()   { echo "[$(timestamp)] [OK]    ✅ $*" | tee -a "$LOG_FILE"; }
err()  { echo "[$(timestamp)] [ERROR] ❌ $*" | tee -a "$LOG_FILE"; }

mkdir -p "$(dirname "$LOG_FILE")"

# SLACK NOTIFICATION
notify_slack() {
    local message="$1"
    local color="${2:-warning}"
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"🤖 AutoFix: $message\"}]}" \
            > /dev/null 2>&1 || true
    fi
}

# WAIT FOR APP HEALTHY
wait_for_health() {
    local elapsed=0
    log "Waiting up to ${MAX_WAIT}s for app to become healthy..."

    while [ $elapsed -lt $MAX_WAIT ]; do
        HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" \
            --connect-timeout 3 --max-time 5 "$HEALTH_URL" || echo "000")

        if [ "$HTTP_CODE" = "200" ]; then
            ok "App is healthy! (HTTP 200)"
            return 0
        fi

        sleep 5
        elapsed=$((elapsed + 5))
        log "Still waiting... (${elapsed}s elapsed, HTTP ${HTTP_CODE})"
    done

    return 1
}

# STRATEGY 1 : RESTART CONTAINER
fix_restart_container() {
    log "Strategy 1: Restarting container..."

    if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        docker restart "$CONTAINER_NAME"
        ok "Container restarted"
    else
        log "Container not found — starting fresh..."
        docker run -d \
            --name "$CONTAINER_NAME" \
            --restart unless-stopped \
            -p "${APP_PORT}:${APP_PORT}" \
            "$APP_IMAGE"
        ok "Fresh container started"
    fi
}

# # STRATEGY 1 : PULL LATEST IMAGE AND REDEPLOY
fix_redeploy() {
    log "Strategy 2: Pulling latest image and redeploying..."

    docker stop  "$CONTAINER_NAME" 2>/dev/null || true
    docker rm    "$CONTAINER_NAME" 2>/dev/null || true
    docker pull  "$APP_IMAGE"      2>/dev/null || true

    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        --memory=512m \
        -p "${APP_PORT}:${APP_PORT}" \
        "$APP_IMAGE"

    ok "Redeployed with latest image"
}

# # STRATEGY 1 : CLEAN UP AND RESET
fix_clean_reset() {
    log "Strategy 3: Full cleanup and reset..."

    docker stop  "$CONTAINER_NAME"   2>/dev/null || true
    docker rm -f "$CONTAINER_NAME"   2>/dev/null || true
    docker system prune -f           2>/dev/null || true

    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p "${APP_PORT}:${APP_PORT}" \
        "$APP_IMAGE"

    ok "Clean reset complete"
}

# RECOVERY FLOW
main() {
    log "═══════════════════════════════════════════"
    log "  AUTO-FIX STARTED"
    log "═══════════════════════════════════════════"

    notify_slack "Auto-fix triggered. Attempting recovery..." "warning"

# ATTEMPT 1 : RESTART
    fix_restart_container
    if wait_for_health; then
        ok "Recovery successful after Strategy 1 (Restart)"
        notify_slack "App recovered after container restart ✅" "good"
        exit 0
    fi

# ATTEMPT 1 : REDEPLOY
    log "Strategy 1 failed. Trying redeploy..."
    fix_redeploy
    if wait_for_health; then
        ok "Recovery successful after Strategy 2 (Redeploy)"
        notify_slack "App recovered after redeploy ✅" "good"
        exit 0
    fi

# ATTEMPT 1 : CLEAN RESET
    log "Strategy 2 failed. Trying clean reset..."
    fix_clean_reset
    if wait_for_health; then
        ok "Recovery successful after Strategy 3 (Clean Reset)"
        notify_slack "App recovered after clean reset ✅" "good"
        exit 0
    fi

# ALL STRATEGIES FAILED 
    err "ALL AUTO-FIX STRATEGIES FAILED. Manual intervention required!"
    notify_slack "⚠️ ALL auto-fix strategies FAILED. Manual intervention required!" "danger"
    exit 1
}

main "$@"
