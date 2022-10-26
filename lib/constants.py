import re
from operator import itemgetter
from pathlib import Path

import requests
from bs4 import BeautifulSoup, SoupStrainer

from lib import config

# config
CONFIG = config.Config()

# base
ENTITIES_SYNTAX = re.compile(r"[a-zA-Z0-9]+\d*:\d+")

# misc
# DICE_SYNTAX = re.compile(r"\d*?\d*d\d+[-+]?\d*")
DICE_SYNTAX = re.compile(r"\d*?\d*d\d+\s?[-+]?\s?\d*")
SPELL_DICE_SYNTAX = re.compile(r"\d*?\d*d\d+")
SANITIZE_DICE = re.compile(r"[^\d+\-*\/d]")
INITIAL_DICE_SYNTAX = re.compile(r"(\d*d\d+)")


# autocomplete
def generate_spells() -> list:
    spells_url = "https://dnd5e.wikidot.com/spells"
    page = requests.get(spells_url)
    if page.status_code != 200:
        return

    soup = BeautifulSoup(page.text, "html.parser", parse_only=SoupStrainer("a"))
    # all spells except Homebrew and Unearthed Arcana
    spells = [
        (a.contents[0], a.get("href").split(":")[1])
        for a in soup.find_all("a", href=True)[49:-38]
        if not any(spell in a.contents[0] for spell in ["HB", "UA"])
    ]
    spells.sort(key=itemgetter(1))
    return spells


SPELL_LIST = generate_spells()


class CharacterSheets:
    def __init__(self, filename: str):
        if not Path(filename).is_file():
            open(filename, "w+", encoding="utf-8").close()

        self.__file = open(filename, "r", encoding="utf-8")

    def __del__(self):
        self.__file.close()

    def read(self) -> str:
        curr = self.__file.read()
        self.__file.seek(0)
        return curr


SHEETS = CharacterSheets("stats.json")
