import psutil
import logging
from pathlib import Path
from datetime import datetime

# ===== Configuration =====
LOG_DIR = Path(__file__).parent / "bot_scheduler_logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"stop_bot_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Scripts to target
TARGET_SCRIPTS = ["main.py", "bot_scheduler.py"]

def terminate_process(proc: psutil.Process):
    try:
        cmdline = ' '.join(proc.cmdline())
        logging.info(f"Attempting to terminate process {proc.pid}: {cmdline}")
        proc.terminate()
        proc.wait(timeout=10)  # Wait for graceful termination
        logging.info(f"Successfully terminated process {proc.pid}")
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
        logging.error(f"Failed to terminate process {proc.pid}: {e}")
        return False

def stop_related_processes():
    logging.info("Stop script started.")
    found = False

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
        try:
            cmdline_list = proc.info.get('cmdline', [])
            if not cmdline_list:
                continue
            cmdline_str = ' '.join(cmdline_list)

            if any(script in cmdline_str for script in TARGET_SCRIPTS):
                found = True
                terminate_process(proc)

                # Optionally terminate parent cmd.exe if it's the parent
                parent_pid = proc.ppid()
                try:
                    parent_proc = psutil.Process(parent_pid)
                    if "cmd.exe" in parent_proc.name().lower():
                        logging.info(f"Also terminating parent cmd.exe: {parent_pid}")
                        terminate_process(parent_proc)
                except psutil.NoSuchProcess:
                    logging.warning(f"Parent process {parent_pid} no longer exists.")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not found:
        logging.info("No related bot processes were found.")
    logging.info("Stop script completed.")

if __name__ == "__main__":
    stop_related_processes()
