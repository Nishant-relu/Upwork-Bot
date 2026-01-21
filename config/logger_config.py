import logging
import logging.config
from datetime import datetime
from zoneinfo import ZoneInfo

from .paths import paths


INDIA_TZ = ZoneInfo("Asia/Kolkata")

def ist_time_converter(seconds: float):
    return datetime.fromtimestamp(seconds, tz=INDIA_TZ).timetuple()

def configure_logging() -> None:
    """
    Configure the root logger with file and stream handlers.
    """

    if getattr(configure_logging, "_configured", False):
        return

    now = datetime.now(INDIA_TZ)
    log_dir = paths.LOGS_DIR / now.strftime("%Y-%m-%d")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filename = log_dir / f"{now.strftime('%Y-%m-%d-%H-%M-%S')}.log"
    
    config: dict[str, any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "converter": ist_time_converter
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_filename.as_posix(),
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 3,
                "formatter": "standard",
                "encoding": "utf-8"
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard"
            }
        },
        "root": {
            "handlers": ["file", "console"],
            "level": logging.INFO
        }
    }
    

    logging.config.dictConfig(config)
    logging.captureWarnings(True)
    configure_logging._configured = True
