import logging
from pathlib import Path

import toml


class Config:
    def __init__(self):
        filename = "Config.toml"
        if not Path(filename).is_file():
            raise SystemExit("Config.toml not found.")

        with open(filename, "r") as config_file:
            config_file = config_file.read()

        self.__config: dict = toml.loads(config_file)
        self.owner: dict = self.__config.get("owner", "")
        self.tokens: dict = self.__config.get("tokens", {})
        self.log_file: str = self.__config.get("log", "").get("file", "")
        self.log_level: str = self.__config.get("log", "").get("level", "WARN")
        self.barred: dict = self.__config.get("barred", "")

    @property
    def scope(self) -> list:
        return self.owner.get("servers", [])

    @property
    def owner_id(self) -> int:
        return int(self.owner.get("id", 0))

    @property
    def barred_users(self) -> list:
        return self.barred.get("users", [])

    def set_logs(self):
        match self.log_level:
            case "DEBUG":
                level = logging.DEBUG
            case "INFO":
                level = logging.INFO
            case "WARN" | "WARNING":
                level = logging.WARN
            case "ERROR" | "CRITICAL" | "FATAL":
                level = logging.ERROR
            case _:
                level = "WARN"

        format = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%d/%m/%Y %I:%M:%S %p"
        filename = "bot.log" if self.log_file else None

        logging.basicConfig(
            level=level, format=format, datefmt=datefmt, filename=filename
        )
