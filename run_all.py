import subprocess
import sys
import os
import time
import threading

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

base_dir = os.path.abspath(os.path.dirname(__file__))
bilimgo_dir = os.path.join(base_dir, "BilimGo")
restart_flag_file = os.path.join(base_dir, "restart.flag")

procs = {
    "web": None,
    "tunnel": None,
    "bot": None,
    "ai_worker": None,
    "engagement_worker": None,
}

running = True


def kill_proc(proc):
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def stop_all():
    print("\n🛑 Barcha xizmatlar to'xtatilmoqda...")
    for name, proc in list(procs.items()):
        if proc and proc.poll() is None:
            print(f" - {name} to'xtatildi")
            kill_proc(proc)
        procs[name] = None
    time.sleep(1)


def start_service(name):
    if name == "web":
        print("1. 🌐 FastAPI Web Server ishga tushmoqda (Port 8000)...")
        return subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=bilimgo_dir,
        )
    elif name == "tunnel":
        print("2. 🚇 Cloudflare Tunnel ishga tushmoqda (bilimgo.smart-tools.uk)...")
        return subprocess.Popen(
            ["cloudflared", "tunnel", "--config", "cloudflared_bilimgo.yml", "run"],
            cwd=bilimgo_dir,
        )
    elif name == "bot":
        print("3. 🤖 Telegram Bot ishga tushmoqda (@BilimGoUz_Bot)...")
        return subprocess.Popen(
            [sys.executable, "-m", "bot.main"],
            cwd=bilimgo_dir,
        )
    elif name == "ai_worker":
        print("4. 🧠 AI Baholash Workeri ishga tushmoqda (ai_evaluation_worker)...")
        return subprocess.Popen(
            [sys.executable, "-m", "workers.ai_evaluation_worker"],
            cwd=bilimgo_dir,
        )
    elif name == "engagement_worker":
        print("5. ⏰ Talabalar Eslatma Workeri ishga tushmoqda (engagement_monitor_worker)...")
        return subprocess.Popen(
            [sys.executable, "-m", "workers.engagement_monitor_worker"],
            cwd=bilimgo_dir,
        )
    return None


def start_all():
    print("\n==================================================")
    print("🚀 BilimGo barcha xizmatlari ishga tushirilmoqda...")
    print("==================================================")
    for name in ("web", "tunnel", "bot", "ai_worker", "engagement_worker"):
        procs[name] = start_service(name)
        time.sleep(1)
    print("\n✅ Barcha xizmatlar muvaffaqiyatli ishga tushirildi!")
    print("==================================================\n")


def restart_all():
    stop_all()
    start_all()


def file_watcher():
    last_mtime = 0
    if os.path.exists(restart_flag_file):
        try:
            last_mtime = os.path.getmtime(restart_flag_file)
        except Exception:
            pass

    while running:
        time.sleep(1)
        if os.path.exists(restart_flag_file):
            try:
                mtime = os.path.getmtime(restart_flag_file)
                if mtime > last_mtime:
                    last_mtime = mtime
                    print("\n🔄 [SIGNAL] 'restart.flag' orqali restart buyrug'i qabul qilindi!")
                    restart_all()
            except Exception:
                pass


def main():
    global running
    start_all()

    # Restart flag watcher thread
    t = threading.Thread(target=file_watcher, daemon=True)
    t.start()

    print("🟢 Tizim barqaror rejimda ishlamoqda. Xizmatlar doimiy nazorat ostida.")

    while running:
        try:
            time.sleep(2)
            for name, proc in list(procs.items()):
                if proc is not None and proc.poll() is not None:
                    exit_code = proc.poll()
                    print(f"⚠️ [{name}] to'xtab qoldi (kod: {exit_code}). Avtomatik qayta yoqilmoqda...")
                    procs[name] = start_service(name)
        except KeyboardInterrupt:
            print("\n🛑 To'xtatilmoqda...")
            break
        except Exception as e:
            print(f"Nazoratda xatolik: {e}")
            time.sleep(2)

    stop_all()


if __name__ == "__main__":
    main()
