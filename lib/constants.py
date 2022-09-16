import re
from pathlib import Path

from lib import config

# config
config = config.Config()

# misc
dice_syntax = re.compile(r"\d*?\d*d\d+[-+]?\d*")


class CharacterSheets:
    def __init__(self, filename: str):
        if not Path(filename).is_file():
            open(filename, "w+", encoding="utf-8").close()

        self.__file = open(filename, "r", encoding="utf-8")

    def __del__(self):
        self.__file.close()

    async def ready(self):
        self.__file = self.__file

    def read(self) -> str:
        curr = self.__file.read()
        self.__file.seek(0)
        return curr


sheets = CharacterSheets("stats.json")
