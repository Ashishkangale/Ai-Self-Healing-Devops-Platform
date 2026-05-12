#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║       Fix Suggester — Smart DevOps Platform AI Engine        ║
║  Takes analysis output → generates executable fix commands   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
import subprocess
import datetime
from pathlib import Path

CONTAINER_NAME  = os.getenv("CONTAINER_NAME", "smart-devops-container")
APP_IMAGE       = os.getenv("APP_IMAGE", "smart-devops-app:latest")
APP_PORT        = os.getenv("APP_PORT", "8080")
FIX_LOG         = "/var/log/app/fix_history.log"


# FIXING STRATEGIES
class FixStrategy:
    """Defines a fix action with a name, condition keywords, and shell command."""

    def __init__(self, name: str, keywords: list, command: str, description: str):
        self.name        = name
        self.keywords    = keywords
        self.command     = command
        self.description = description

    def matches(self, analysis_text: str) -> bool:
        text_lower = analysis_text.lower()
        return any(k.lower() in text_lower for k in self.keywords)

    def execute(self) -> dict:
        print(f"\n🔧 Executing fix: {self.name}")
        print(f"   ℹ️  {self.description}")
        print(f"   $ {self.command}")

        result = subprocess.run(
            self.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        success = result.returncode == 0
        output  = result.stdout.strip() or result.stderr.strip()

        status = "✅ Success" if success else "❌ Failed"
        print(f"   {status}: {output[:200]}")

        return {
            "fix_name":   self.name,
            "command":    self.command,
            "success":    success,
            "output":     output,
            "timestamp":  datetime.datetime.now().isoformat()
        }


# AVALIABLE FIX STRATEGIES
FIX_STRATEGIES = [
    FixStrategy(
        name        = "Restart Container",
        keywords    = ["restart", "crashed", "exit", "stopped", "not running"],
        command     = f"docker restart {CONTAINER_NAME} 2>/dev/null || "
                      f"docker run -d --name {CONTAINER_NAME} --restart unless-stopped "
                      f"-p {APP_PORT}:{APP_PORT} {APP_IMAGE}",
        description = "Restarts the application Docker container"
    ),
    FixStrategy(
        name        = "Clear Disk Space",
        keywords    = ["disk", "no space", "storage", "volume full"],
        command     = "docker system prune -f && journalctl --vacuum-size=100M",
        description = "Frees up disk space by removing unused Docker resources"
    ),
    FixStrategy(
        name        = "Fix Permissions",
        keywords    = ["permission denied", "access denied", "unauthorized file"],
        command     = f"docker exec {CONTAINER_NAME} chown -R appuser:appgroup /app /var/log/app 2>/dev/null || true",
        description = "Fixes file permission issues inside the container"
    ),
    FixStrategy(
        name        = "Redeploy Fresh Container",
        keywords    = ["out of memory", "oom", "heap space", "memory leak"],
        command     = f"docker stop {CONTAINER_NAME} && docker rm {CONTAINER_NAME} && "
                      f"docker run -d --name {CONTAINER_NAME} --restart unless-stopped "
                      f"--memory=512m --memory-swap=512m "
                      f"-p {APP_PORT}:{APP_PORT} {APP_IMAGE}",
        description = "Redeploys container with memory limits to prevent OOM"
    ),
    FixStrategy(
        name        = "Rotate Logs",
        keywords    = ["log", "log file", "disk full", "log size"],
        command     = "find /var/log/app -name '*.log' -size +100M -exec truncate -s 0 {} \\;",
        description = "Truncates oversized log files"
    ),
]

# DEFAULT FALLBACK
DEFAULT_FIX = FixStrategy(
    name        = "Default: Restart Container",
    keywords    = [],
    command     = f"docker restart {CONTAINER_NAME} 2>/dev/null || true",
    description = "Default recovery: restart the application container"
)


# SUGGEST AND EXECUTE
def suggest_and_fix(analysis_text: str) -> list:
    """Match analysis to fix strategies and execute them."""
    matched = [s for s in FIX_STRATEGIES if s.matches(analysis_text)]

    if not matched:
        print("⚠️  No specific fix matched — applying default restart fix")
        matched = [DEFAULT_FIX]

    results = []
    for strategy in matched:
        result = strategy.execute()
        results.append(result)

    # Log fix history
    _save_fix_history(results)
    return results


# SAVE FIX HISTORY
def _save_fix_history(results: list):
    Path(FIX_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(FIX_LOG, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\n📁 Fix history saved to {FIX_LOG}")


# ENTRY POINT
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        analysis = " ".join(sys.argv[1:])
    else:
        analysis = sys.stdin.read() if not sys.stdin.isatty() else "restart crashed"

    print("🤖 Fix Suggester running...")
    results = suggest_and_fix(analysis)

    success_count = sum(1 for r in results if r["success"])
    print(f"\n📊 Fix Summary: {success_count}/{len(results)} fixes succeeded")
