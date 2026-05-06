#!/usr/bin/env python3
import os
import json
import subprocess
from datetime import datetime

LOG_FILE     = "/var/log/app/health.log"
ANALYSIS_LOG = "/var/log/app/ai_analysis.log"
DECISION_LOG = "/var/log/app/ai_decision.log"

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_logs(lines=50):
    try:
        with open(LOG_FILE, "r") as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        return ["No log file found at " + LOG_FILE]

def get_container_status():
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format={{.State.Status}}", "smart-devops-container"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return "not_found"

def get_port_status():
    try:
        result = subprocess.run(
            ["sudo", "lsof", "-i", ":8080", "-t"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""

def detect_anomaly(logs):
    error_count   = sum(1 for l in logs if "ERROR"       in l or "error"       in l)
    crash_count   = sum(1 for l in logs if "EACCES"      in l or "FATAL"       in l or "crash" in l.lower())
    restart_count = sum(1 for l in logs if "restart"     in l or "Restart"     in l)
    down_count    = sum(1 for l in logs if "DOWN"        in l or "not running" in l)
    port_count    = sum(1 for l in logs if "EADDRINUSE"  in l or "address already in use" in l.lower())
    score = (error_count*2) + (crash_count*3) + (restart_count*1) + (down_count*2) + (port_count*3)
    return {
        "anomaly_detected": score > 3,
        "score":          score,
        "error_count":    error_count,
        "crash_count":    crash_count,
        "restart_count":  restart_count,
        "down_count":     down_count,
        "port_count":     port_count
    }

def ask_claude_for_decision(logs, anomaly, container_status, port_pids):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        prompt = f"""You are a Senior DevOps Engineer AI. A production app is failing.

SYSTEM STATE:
- Container status: {container_status}
- Port 8080 conflicting PIDs: "{port_pids}"
- Anomaly score: {anomaly['score']}
- Error count: {anomaly['error_count']}
- Crash count: {anomaly['crash_count']}
- Restart count: {anomaly['restart_count']}
- Down events: {anomaly['down_count']}
- Port conflict events: {anomaly['port_count']}

LAST 50 LOG LINES:
{''.join(logs)}

You must respond with ONLY a JSON object. No explanation. No markdown. Just raw JSON.

Choose the action field from EXACTLY one of these values:
- "restart"   → container is stopped, no crash, just needs to be started
- "rebuild"   → app is crashing repeatedly, code or image issue, needs fresh build
- "port_fix"  → port 8080 is blocked by another process
- "redeploy"  → persistent unknown failure, needs full stop + remove + fresh deploy

{{
  "action": "restart or rebuild or port_fix or redeploy",
  "problem": "one sentence root cause",
  "severity": "LOW or MEDIUM or HIGH or CRITICAL",
  "reason": "why you chose this action",
  "prevention": "how to prevent this next time"
}}"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"Claude API error: {e}")
        return None

def rule_based_decision(logs, anomaly, container_status, port_pids):
    log_text = ''.join(logs)
    if port_pids or anomaly["port_count"] > 0:
        return {
            "action":     "port_fix",
            "problem":    "Port 8080 is occupied by another process",
            "severity":   "HIGH",
            "reason":     "Port conflict detected in logs or active PIDs found",
            "prevention": "Always stop old containers before starting new ones"
        }
    elif container_status in ("exited", "not_found", "dead"):
        return {
            "action":     "restart",
            "problem":    "Container is stopped or does not exist",
            "severity":   "HIGH",
            "reason":     f"Container status is '{container_status}'",
            "prevention": "Use --restart unless-stopped flag in docker run"
        }
    elif anomaly["crash_count"] > 2 or anomaly["restart_count"] > 3:
        return {
            "action":     "rebuild",
            "problem":    "App is crashing repeatedly — possible code or config issue",
            "severity":   "CRITICAL",
            "reason":     f"crash_count={anomaly['crash_count']}, restart_count={anomaly['restart_count']}",
            "prevention": "Add health checks and crash reporting to application"
        }
    else:
        return {
            "action":     "redeploy",
            "problem":    "Persistent unknown failure",
            "severity":   "HIGH",
            "reason":     "No specific pattern matched — doing full redeploy",
            "prevention": "Enable detailed application error logging"
        }

def execute_decision(action, port_pids):
    container = "smart-devops-container"
    image     = "smart-devops-app:latest"
    port      = "8080"

    run_cmd = [
        "docker", "run", "-d",
        "--name", container,
        "--restart", "unless-stopped",
        "-p", f"{port}:{port}",
        image
    ]

    print(f"\n>>> EXECUTING ACTION: {action.upper()}")

    if action == "restart":
        print("Action: Starting stopped container...")
        subprocess.run(["docker", "start", container], check=False)

    elif action == "port_fix":
        print("Action: Killing processes on port 8080...")
        if port_pids:
            for pid in port_pids.split("\n"):
                pid = pid.strip()
                if pid:
                    subprocess.run(["sudo", "kill", "-9", pid], check=False)
                    print(f"  Killed PID {pid}")
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm",   container], check=False)
        subprocess.run(run_cmd, check=False)

    elif action == "rebuild":
        print("Action: Rebuilding Docker image and redeploying...")
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm",   container], check=False)
        build = subprocess.run(
            ["docker", "build", "-t", image, "/opt"],
            capture_output=True, text=True
        )
        if build.returncode != 0:
            print(f"Build failed:\n{build.stderr}")
        else:
            print("Build succeeded — starting fresh container...")
            subprocess.run(run_cmd, check=False)

    elif action == "redeploy":
        print("Action: Full redeploy — stop, remove, fresh start...")
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm",   container], check=False)
        subprocess.run(run_cmd, check=False)

    else:
        print(f"Unknown action '{action}' — defaulting to redeploy...")
        subprocess.run(["docker", "stop", container], check=False)
        subprocess.run(["docker", "rm",   container], check=False)
        subprocess.run(run_cmd, check=False)

def save_decision(decision, source):
    os.makedirs("/var/log/app", exist_ok=True)
    with open(DECISION_LOG, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"AI DECISION — {timestamp()}\n")
        f.write(f"Source        : {source}\n")
        f.write(f"{'='*60}\n")
        f.write(f"ACTION        : {decision['action']}\n")
        f.write(f"PROBLEM       : {decision['problem']}\n")
        f.write(f"SEVERITY      : {decision['severity']}\n")
        f.write(f"REASON        : {decision['reason']}\n")
        f.write(f"PREVENTION    : {decision['prevention']}\n")
        f.write(f"{'='*60}\n")
    with open(ANALYSIS_LOG, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"AI ANALYSIS — {timestamp()} | Source: {source}\n")
        f.write(f"ACTION: {decision['action']} | SEVERITY: {decision['severity']}\n")
        f.write(f"PROBLEM: {decision['problem']}\n")
        f.write(f"{'='*60}\n")

def print_decision(decision, source):
    print(f"\n{'='*60}")
    print(f"AI DECISION ENGINE — {timestamp()}")
    print(f"Source    : {source}")
    print(f"{'='*60}")
    print(f"ACTION    : {decision['action'].upper()}")
    print(f"PROBLEM   : {decision['problem']}")
    print(f"SEVERITY  : {decision['severity']}")
    print(f"REASON    : {decision['reason']}")
    print(f"PREVENTION: {decision['prevention']}")
    print(f"{'='*60}\n")

def analyze_logs():
    print(f"\n{'='*60}")
    print(f"AI Decision Engine started — {timestamp()}")
    print(f"{'='*60}")

    logs             = read_logs()
    anomaly          = detect_anomaly(logs)
    container_status = get_container_status()
    port_pids        = get_port_status()

    print(f"Container status : {container_status}")
    print(f"Port 8080 PIDs   : '{port_pids}'")
    print(f"Anomaly score    : {anomaly['score']}")

    decision = None
    source   = "rule-based"

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("Consulting Anthropic Claude for decision...")
        decision = ask_claude_for_decision(logs, anomaly, container_status, port_pids)
        if decision:
            source = "Anthropic Claude (claude-haiku)"

    if decision is None:
        print("Falling back to rule-based decision...")
        decision = rule_based_decision(logs, anomaly, container_status, port_pids)

    print_decision(decision, source)
    save_decision(decision, source)

    execute_decision(decision["action"], port_pids)

    import time
    time.sleep(8)

    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8080/health", timeout=10)
        print(f"\n✅ Recovery verified — app is responding on port 8080")
    except Exception:
        print(f"\n⚠️  App not yet responding — check: docker logs smart-devops-container")

if __name__ == "__main__":
    analyze_logs()