from pathlib import Path

CONFIG_REL_PATH = ".config/cronboard"
WRAPPER_DIST = "cron-wrapper.sh"
LOG_REL_PATH = f"{CONFIG_REL_PATH}/logs"
CONFIG_DIR = Path.home() / CONFIG_REL_PATH
CONFIG_FILE = CONFIG_DIR / "servers.toml"
KEY_FILE = CONFIG_DIR / "secret.key"
LOG_DIR = CONFIG_DIR / "logs"
WRAPPER_SOURCE = Path(__file__).parent / "logging" / "cron-wrapper.sh"
