"""统一加载 config/settings.yaml，并定位项目根目录。"""
import os
import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT_DIR, "config", "settings.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_config()


def base_url():
    return CONFIG[CONFIG["env"]]["base_url"]


def web_login_url():
    return CONFIG[CONFIG["env"]]["web_login_url"]
