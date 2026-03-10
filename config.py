"""
Configuration management for OpenClaw Telegram Bridge.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.resolve()
STORAGE_DIR = BASE_DIR / "storage"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
STORAGE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
AUTHORIZED_CHAT_ID = int(TELEGRAM_CHAT_ID) if TELEGRAM_CHAT_ID else None

# Queue settings
QUEUE_FILE = STORAGE_DIR / "queue.json"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Message timeout (seconds)
MESSAGE_TIMEOUT = int(os.getenv("MESSAGE_TIMEOUT", "300"))

# Bot metadata
BOT_NAME = "OpenClaw Bridge"
BOT_VERSION = "1.0"


def validate_config() -> list[str]:
    """
    Validate configuration and return list of errors.
    """
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set in .env file")
    
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is not set in .env file")
    else:
        try:
            int(TELEGRAM_CHAT_ID)
        except ValueError:
            errors.append("TELEGRAM_CHAT_ID must be a valid integer")
    
    return errors


def is_authorized(chat_id: int) -> bool:
    """
    Check if the chat ID is authorized to use the bot.
    Only the configured TELEGRAM_CHAT_ID is allowed.
    """
    return chat_id == AUTHORIZED_CHAT_ID
