from pathlib import Path
import yaml
from dotenv import load_dotenv
from .Logger import get_logger

BASE = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE / "config.yaml"
ENVIRN_FILE = BASE / ".env"

log = get_logger("Config")


def load_config():
    config = {}
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        log.info(f"加载配置文件 {CONFIG_FILE} 成功")
    except FileNotFoundError:
        log.warning(f"配置文件 {CONFIG_FILE} 不存在")
    except Exception as e:
        log.error(f"加载配置文件 {CONFIG_FILE} 失败: {e}")

    try:
        load_dotenv(ENVIRN_FILE)
        log.info(f"加载环境变量 {ENVIRN_FILE} 成功")
    except FileNotFoundError:
        log.warning(f"环境变量 {ENVIRN_FILE} 不存在")
    except Exception as e:
        log.error(f"加载环境变量 {ENVIRN_FILE} 失败: {e}")

    return config
