from configparser import ConfigParser
from typing import Any
import json


def read_config() -> ConfigParser:
    config = ConfigParser()
    config.read("../config.ini")
    return config


def write_json(json_path: str, data: dict[str, Any]) -> None:
    with open(json_path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
