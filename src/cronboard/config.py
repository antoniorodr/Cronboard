from pathlib import Path

CONFIG_REL_PATH: str = ".config/cronboard"
CRONBOARD_CONFIG_FILE: str = f"{CONFIG_REL_PATH}/config.toml"
CRONBOARD_NOTIFICATIONS_FILE: str = f"{CONFIG_REL_PATH}/notifications.toml"
WRAPPER_DIST: str = "cron-wrapper.sh"
LOG_REL_PATH: str = f"{CONFIG_REL_PATH}/logs"
CONFIG_DIR: Path = Path.home() / CONFIG_REL_PATH
CONFIG_FILE: Path = CONFIG_DIR / "servers.toml"
KEY_FILE: Path = CONFIG_DIR / "secret.key"
LOG_DIR: Path = CONFIG_DIR / "logs"
WRAPPER_SOURCE: Path = Path(__file__).parent / "logging" / "cron-wrapper.sh"
