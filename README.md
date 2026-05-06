# 🚀 Smart Self-Healing DevOps Platform

> **CI/CD + AI-Powered Auto-Recovery + Cloud Infrastructure**  
> A production-grade project combining DevOps, AI, and Cloud — built for your resume.

---

## 🏗️ Architecture

```
Developer → GitHub → Jenkins Pipeline → Docker Build → AWS EC2
                                               ↓
                                      Health Check (cron, every 1 min)
                                               ↓
                                          App Down?
                                               ↓
                                    AI Log Analyzer (Python)
                                               ↓
                              Analyze → Suggest Fix → Auto Execute
                                               ↓
                                    Slack / Dashboard Alert
```

---

## 📂 Folder Structure

```
smart-devops-platform/
│
├── app/
│   ├── server.js          # Node.js Express app (health, logs, metrics endpoints)
│   └── package.json
│
├── docker/
│   └── Dockerfile         # Multi-stage, non-root, with Docker HEALTHCHECK
│
├── jenkins/
│   └── Jenkinsfile        # Full CI/CD pipeline (build → test → docker → deploy → verify)
│
├── terraform/
│   ├── main.tf            # EC2 + Security Group + Elastic IP + bootstrap
│   ├── variables.tf       # All configurable values
│   └── outputs.tf         # Prints IP, SSH command, App URL after apply
│
├── ai-engine/
│   ├── log_analyzer.py    # Reads logs → calls OpenAI/Anthropic/rule-based fallback
│   └── fix_suggester.py   # Maps analysis to fix strategies → executes them
│
├── scripts/
│   ├── health_check.sh    # HTTP check with retries → triggers AI on failure
│   └── auto_fix.sh        # 3-strategy recovery (restart → redeploy → clean reset)
│
├── dashboard/
│   └── index.html         # Real-time monitoring dashboard (AI-powered)
│
└── README.md
```

---

## ⚙️ Tech Stack

| Area | Tools |
|------|-------|
| **Source Control** | Git + GitHub |
| **CI/CD** | Jenkins |
| **Containerization** | Docker |
| **Cloud** | AWS EC2 + Elastic IP |
| **Infrastructure as Code** | Terraform |
| **AI Engine** | Python + OpenAI / Anthropic Claude |
| **Monitoring** | Bash scripts + cron + HTML dashboard |
| **Notifications** | Slack Webhooks |

---

## 🛠️ Step-by-Step Setup Guide

### Prerequisites
- AWS Account (Free Tier OK)
- Jenkins server (local or EC2)
- Docker installed
- Terraform v1.5+
- Python 3.8+
- Node.js 18+
- OpenAI or Anthropic API key

---

### STEP 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-devops-platform.git
cd smart-devops-platform
```

---

### STEP 2 — Test the App Locally

```bash
cd app
npm install
npm start
# Open: http://localhost:8080
# Health: http://localhost:8080/health
```

---

### STEP 3 — Build Docker Image

```bash
# From project root
docker build -f docker/Dockerfile -t smart-devops-app:latest .

# Run locally
docker run -d --name smart-devops-container -p 8080:8080 smart-devops-app:latest

# Test
curl http://localhost:8080/health
```

---

### STEP 4 — Provision AWS Infrastructure with Terraform

```bash
cd terraform

# Configure your AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Initialize Terraform
terraform init

# Preview what will be created
terraform plan

# Create EC2 + Security Group + Elastic IP
terraform apply

# Note the outputs:
#   ec2_public_ip = "x.x.x.x"
#   ssh_command   = "ssh -i ~/.ssh/id_rsa ubuntu@x.x.x.x"
#   app_url       = "http://x.x.x.x:8080"
```

---

### STEP 5 — Copy Scripts to EC2

```bash
EC2_IP=$(terraform output -raw ec2_public_ip)

# Copy AI engine and scripts
scp -r ai-engine/  ubuntu@$EC2_IP:/opt/ai-engine/
scp -r scripts/    ubuntu@$EC2_IP:/opt/scripts/
scp -r dashboard/  ubuntu@$EC2_IP:/opt/dashboard/

# Make scripts executable
ssh ubuntu@$EC2_IP "chmod +x /opt/scripts/*.sh"
```

---

### STEP 6 — Set Up AI API Key on EC2

```bash
ssh ubuntu@$EC2_IP

# Add to /etc/environment or ~/.bashrc
echo 'export OPENAI_API_KEY=your_key_here' >> ~/.bashrc

# OR use Anthropic
echo 'export ANTHROPIC_API_KEY=your_key_here' >> ~/.bashrc

source ~/.bashrc

# Install Python deps
pip3 install openai requests
```

---

### STEP 7 — Set Up Jenkins Pipeline

1. Install Jenkins (if not already):
   ```bash
   # On Ubuntu
   sudo apt install openjdk-17-jdk -y
   wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
   sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
   sudo apt update && sudo apt install jenkins -y
   sudo systemctl start jenkins
   ```

2. Open `http://YOUR_JENKINS_IP:8080`

3. Install plugins: **Git**, **Docker Pipeline**, **SSH Agent**

4. Add credentials in Jenkins → Manage Jenkins → Credentials:
   - `EC2_HOST` → your EC2 Elastic IP
   - `EC2_SSH_KEY` → your private key (id_rsa content)
   - `SLACK_WEBHOOK_URL` → your Slack webhook URL

5. Create Pipeline job → point to `jenkins/Jenkinsfile`

6. **Trigger**: push to GitHub → Jenkins auto-runs

---

### STEP 8 — Enable Auto Health Check (cron)

```bash
ssh ubuntu@$EC2_IP

# Edit crontab
crontab -e

# Add this line (runs health check every minute)
* * * * * /opt/scripts/health_check.sh >> /var/log/app/health.log 2>&1
```

---

### STEP 9 — Test the Self-Healing

```bash
# Simulate failure — stop the container manually
ssh ubuntu@$EC2_IP "docker stop smart-devops-container"

# Within 1 minute, cron triggers health_check.sh
# health_check.sh detects failure
# log_analyzer.py reads logs and calls AI
# auto_fix.sh restarts the container automatically
# ✅ App recovers without manual intervention

# Watch it happen
ssh ubuntu@$EC2_IP "tail -f /var/log/app/health.log"
```

---

### STEP 10 — Open the Dashboard

```bash
# Option 1: Open directly in browser
open http://YOUR_EC2_IP:8080  # Needs nginx or serve

# Option 2: Serve with Python
ssh ubuntu@$EC2_IP "cd /opt/dashboard && python3 -m http.server 3000"
# Open: http://YOUR_EC2_IP:3000
```

---

## 🔐 Environment Variables Reference

| Variable | Where | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | EC2 + `.env` | OpenAI API key for AI analysis |
| `ANTHROPIC_API_KEY` | EC2 + `.env` | Alternative: Anthropic Claude API key |
| `SLACK_WEBHOOK_URL` | EC2 + Jenkins | Slack incoming webhook URL |
| `CONTAINER_NAME` | scripts | Docker container name (default: `smart-devops-container`) |
| `APP_PORT` | scripts | App port (default: `8080`) |

---

## 🎯 Interview Questions & Answers

**Q: How does the CI/CD pipeline work?**  
A: Developer pushes code to GitHub → Jenkins detects change via polling → runs build/test/docker stages → SSH deploys to EC2 → verifies health.

**Q: How does Docker help deployment?**  
A: Docker packages the app with all dependencies into an image. Any machine with Docker can run it identically, eliminating "works on my machine" issues.

**Q: What happens when the app fails?**  
A: Cron runs health_check.sh every minute. On failure, log_analyzer.py reads error logs and sends them to AI. The AI identifies root cause and recommends a fix. auto_fix.sh tries 3 recovery strategies.

**Q: How is AI integrated?**  
A: Python script reads app logs, builds a structured prompt, calls OpenAI/Anthropic API, and parses the response to extract root cause, severity, and fix commands.

**Q: How does the system recover automatically?**  
A: fix_suggester.py matches AI analysis keywords to fix strategies (restart / redeploy / clean-reset) and executes them via subprocess. If all fail, a Slack alert is sent for manual intervention.

---

## 💼 Resume Description

**Smart Self-Healing DevOps Platform** *(AI + CI/CD + Cloud)*
- Built automated CI/CD pipeline using Jenkins & Docker with multi-stage builds
- Provisioned AWS EC2 infrastructure using Terraform (Infrastructure as Code)
- Developed AI-powered log analyzer integrating OpenAI/Anthropic API for failure detection
- Implemented 3-strategy self-healing system achieving automatic recovery without manual intervention
- Created real-time monitoring dashboard with live log streaming and AI analysis

---

## 📄 License

MIT — free to use, modify, and include in your portfolio.
