import logging
import random
import subprocess
import time
from pathlib import Path

import psutil

from config import bot_settings, configure_logging

# ==== CONFIGURATION ====
CURRENT_DIR = Path(__file__).parent.resolve()
VENV_PATH = CURRENT_DIR / ".venv/Scripts/activate.bat"
BOT_SCRIPT = CURRENT_DIR / "main.py"

# Log setup
configure_logging()
logger = logging.getLogger(__name__)


def is_bot_running() -> bool:
    """Check if bot script is already running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and str(BOT_SCRIPT.name) in ' '.join(cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def run_bot_with_venv():
    """
    Activates virtual environment and runs bot script.
    Executes a command like: cmd /c "activate && python bot_script.py"
    """
    command = f'cmd /c "{VENV_PATH} && python {BOT_SCRIPT}"'
    try:
        logging.info("Running bot via virtual environment...")
        subprocess.run(command, shell=True, check=True)
        logging.info("Bot execution completed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running bot: {e}")

def main():
    logging.info("Bot scheduler started.")

    while True:
        # Random interval 
        wait_minutes = random.randint(*bot_settings.WAIT_TIME)
        logging.info(f"Next run scheduled in {wait_minutes} minutes.")

        # Wait until no instance is running
        while is_bot_running():
            logging.warning("Bot is already running. Checking again in 2 minutes.")
            time.sleep(120)  # wait 2 mins

        # Run the bot
        run_bot_with_venv()

        # Sleep before next run
        logging.info(f"Sleeping for {wait_minutes} minutes...")
        time.sleep(wait_minutes * 60)

if __name__ == "__main__":
    main()
