#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ========== تنظیمات ==========
REPO_URL_BASE = "https://github.com/sazidehm/linuxsupd.git"   # آدرس ریپو (بدون توکن)
REPO_DIR = "/path/to/local/repo"                   # مسیر محلی
BRANCH = "main"
GIT_USER = "claudetest"
GIT_EMAIL = "sazidehm@email.com"

# 🔑 توکن خود را اینجا وارد کن (با دسترسی repo)
GITHUB_TOKEN = "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"   # <---- توکن را عوض کن

# ساخت آدرس کامل با توکن
REPO_URL = REPO_URL_BASE.replace("https://", f"https://{GITHUB_TOKEN}@")
# ==============================

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def git_init():
    repo_path = Path(REPO_DIR)
    if not repo_path.exists():
        print(f"[*] کلون کردن ریپو با توکن از {REPO_URL_BASE}")
        out, err, code = run_cmd(f"git clone {REPO_URL} {REPO_DIR}")
        if code != 0:
            print(f"❌ خطا در clone: {err}")
            sys.exit(1)
    run_cmd(f"git config user.name '{GIT_USER}'", cwd=REPO_DIR)
    run_cmd(f"git config user.email '{GIT_EMAIL}'", cwd=REPO_DIR)
    run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)

def git_pull():
    print("[*] دریافت آخرین تغییرات...")
    run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)
    out, err, code = run_cmd(f"git pull origin {BRANCH}", cwd=REPO_DIR)
    if code != 0:
        print(f"⚠️ خطا در pull: {err}")
        run_cmd(f"git fetch origin {BRANCH}", cwd=REPO_DIR)
        run_cmd(f"git reset --hard origin/{BRANCH}", cwd=REPO_DIR)

def git_commit_push(message):
    run_cmd("git add .", cwd=REPO_DIR)
    out, err, code = run_cmd(f'git commit -m "{message}"', cwd=REPO_DIR)
    if code != 0 and "nothing to commit" not in err and "nothing to commit" not in out:
        print(f"⚠️ خطا در commit: {err}")
    else:
        run_cmd(f"git remote set-url origin {REPO_URL}", cwd=REPO_DIR)
        out_push, err_push, code_push = run_cmd(f"git push origin {BRANCH}", cwd=REPO_DIR)
        if code_push != 0:
            print(f"❌ خطا در push: {err_push}")
        else:
            print("[✓] تغییرات با موفقیت push شد")

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
    name = "linuxarvin"   # یا از hostname بگیر
    uptime = get_uptime()
    content = f"names={name}\nuptime={uptime}\n"
    with open(online_path, "w") as f:
        f.write(content)
    print(f"[✓] online.txt به‌روز شد: {content.strip()}")

def process_commands():
    term_path = Path(REPO_DIR) / "terminalcomment.txt"
    if not term_path.exists():
        with open(term_path, "w") as f:
            f.write("com = \nansw = \n")
        return

    with open(term_path, "r") as f:
        lines = f.readlines()

    com_line = next((line for line in lines if line.strip().startswith("com =")), None)
    if not com_line:
        return

    com_value = com_line.split("=", 1)[1].strip()
    if not com_value:
        return

    print(f"[*] اجرای دستور: {com_value}")
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

    print(f"[✓] پاسخ در terminalcomment.txt نوشته شد")

def main():
    print(f"[*] شروع اسکریپت در {datetime.now()}")
    git_init()
    git_pull()
    update_online_txt()
    process_commands()
    git_commit_push("Auto update: online status and command result")
    print("[✓] پایان کار\n")

if __name__ == "__main__":
    main()
