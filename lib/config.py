import logging
from pathlib import Path

import toml


class Config:
    # {
    #     'owner': {'id': 1},
    #     'tokens': {   'discord': ''},
    #     'log': {'file': 'bot.log'},
    #     'barred': {'users': [1] }
    # }
    def __init__(self):
        filename = "Config.toml"
        if not Path(filename).is_file():
            raise SystemExit("Config.toml not found.")

        with open(filename, "r") as config_file:
            config_file = config_file.read()

        self.__config: dict = toml.loads(config_file)
        self.owner: dict = self.__config.get("owner", "")
        self.tokens: dict = self.__config.get("tokens", {})
        self.log: str = self.__config.get("log", "").get("file", "")
        self.barred: dict = self.__config.get("barred", "")

    def barred_users(self) -> list[int]:
        return self.barred.get("users", [])

    def set_logs(self):
        level = logging.INFO
        format = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%d/%m/%Y %I:%M:%S %p"
        filename = "bot.log" if self.log else None

        logging.basicConfig(
            level=level, format=format, datefmt=datefmt, filename=filename
        )
