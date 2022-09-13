import json
import os
import random
import re

import aiofiles
import interactions
import pyfiglet
import requests
from interactions import CommandContext, Embed, EmbedImageStruct, Member

stats = [
    "Acrobatics",
    "Animal Handling",
    "Arcana",
    "Athletics",
    "Deception",
    "History",
    "Insight",
    "Intimidation",
    "Investigation",
    "Medicine",
    "Nature",
    "Perception",
    "Performance",
    "Persuasion",
    "Religion",
    "Sleight Of Hand",
    "Stealth",
    "Survival",
]


class CharRepr:
    def __init__(self, author: Member):
        self.character = {
            str(author.id): {
                "name": author.user.username,
                "stats": {},
                "weapons": {},
                "spells": {},
                "custom": {},
                "features": {},
                "initiative": "",
            }
        }

    def character(self) -> dict:
        return self.character


def quick_embed(title: str, desc: str, ty: str):
    match ty:
        case "info":
            ty = 0x95E9FE
        case "warn":
            ty = 0xFEEC95
        case "error":
            ty = 0xFF7373
        case "ok":
            ty = 0xAEFF73
        case _:
            ty = 0xD8D8D8

    return Embed(
        title=title,
        description=desc,
        color=ty,
    )


def roll_dice(
    rolls: int,
    sides: int,
    implication: str = "",
    mod: int = 0,
):
    if implication and rolls < 2:
        rolls = 2

    random_nums = [random.randint(1, sides) for _ in range(0, rolls)]
    match implication:
        case "adv":
            final_num = max(random_nums)
        case "dis":
            final_num = min(random_nums)
        case _:
            final_num = sum(random_nums)

    return final_num + mod, random_nums


dice_syntax = re.compile(r"\d*?\d*d\d+[-+]?\d*")


def find_dice(string: str):
    return sorted(
        [*set(dice_syntax.findall(string))], key=lambda x: (int(x.split("d")[0]))
    )


def decipher_dice(roll: str) -> tuple[int, int, int]:
    if not dice_syntax.match(roll):
        raise TypeError(f"Invalid Syntax for roll: {roll}")

    rolls = 0
    sides = 0
    mod = 0
    splits = list(roll.split("d"))

    if not splits[0]:
        rolls = 1

    values = [int(value) for value in re.findall(r"-?\d+", roll)]

    if len(values) == 1:
        rolls, sides, mod = 1, values[0], 0
    elif len(values) == 2:
        if rolls:
            sides, mod = values[0], values[1]
        else:
            rolls, sides = values[0], values[1]
    else:
        rolls, sides, mod = values[0], values[1], values[2]

    return rolls, sides, mod


class CharacterSheets:
    def __init__(self, filename: str):
        from pathlib import Path

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


async def open_stats(author: Member):
    char = CharRepr(author)
    try:
        content = sheets.read()
        content: dict = json.loads(content)
    except json.JSONDecodeError:
        content: dict = json.loads("{}")

    if content.get(str(author.id)) is None or content == {}:
        async with aiofiles.open("stats.json", "w") as save:
            content.update(char.character())
            await save.write(json.dumps(content, indent=4))

    return content


def roll_embed(
    author: Member,
    rolls: int,
    sides: int,
    final_num: int,
    random_nums: list[int],
    implication: str = "",
    mod: int = 0,
):
    roll_syn = f"{rolls}d{sides}"
    if mod > 0:
        roll_syn += "+"
    if mod != 0:
        roll_syn += str(mod)

    try:
        base_url = "https://cdn.discordapp.com/avatars"
        user_avatar = f"{base_url}/{author.id}/{author.avatar}.webp"
        title = author.name + "'s Roll"
    except AttributeError:
        user_avatar = ""
        title = "Your Roll"

    embed = Embed(
        title=title,
        thumbnail=EmbedImageStruct(url=user_avatar, height=100, width=100),
        color=0xE2E0DD,
    )
    embed.add_field(name="**Roll**", value=f"**{roll_syn}**", inline=True)

    if implication == "adv":
        embed.add_field(name="Implication", value="Rolling with Advantage")
    elif implication == "dis":
        embed.add_field(name="Implication", value="Rolling with Disadvantage")
    else:
        pass

    figlet = pyfiglet.figlet_format(str(final_num), "fraktur")

    # discord uses three backticks for code formatting.
    # adding a zero width character allows for good looking ascii art
    # since a "\`" does not work in code formatting.
    figlet = figlet.replace("`", "\u200B`")

    embed.add_field(name="Generated Numbers", value=f"{random_nums}", inline=False)
    if len(figlet) < 1024:
        # this might fail because discord does not allow for
        # more than 1024 characters in a field value
        embed.add_field(name="Final Roll", value=f"```{figlet}```", inline=False)
    else:
        embed.add_field(name="Result", value=f"**{final_num}**")
        # logging.exception("Failed to add figlet field.")

    embed.set_footer(final_num)

    return embed


def decipher_all(syntax: list[str]):
    rollable = []
    for dice_syn in syntax:
        try:
            rolls, sides, mod = decipher_dice(dice_syn)
            rollable.append((rolls, sides, mod))
        except TypeError:
            pass

    return rollable


def create_choice(choice: str, value: str = ""):
    if not value:
        value = choice

    return interactions.Choice(name=choice, value=value)


class Choices:
    def from_list(self, lst: list[str]):
        return [create_choice(choice) for choice in lst]


def author_url(author: Member, guild_id: interactions.Snowflake):
    icon = author.get_avatar_url(guild_id)
    if requests.get(icon).status_code == 404:
        try:
            base_url = "https://cdn.discordapp.com/avatars"
            icon = f"{base_url}/{author.id}/{author.avatar}.webp"
        except Exception:
            icon = ""

    return icon


def disable(buttons: list[interactions.Button]):
    for button in buttons:
        button.disabled = True


def to_button(label: str, style):
    return interactions.Button(style=style, label=label, custom_id=label)


# ttps://stackoverflow.com/a/65038809
# hope the person who wrote this is doing amazing rn. actual lifesaver
def wrap_spell(source_text, separator_chars=["."], width=1024, keep_separators=True):
    current_length = 0
    latest_separator = -1
    current_chunk_start = 0
    output = ""
    char_index = 0
    while char_index < len(source_text):
        if source_text[char_index] in separator_chars:
            latest_separator = char_index
        output += source_text[char_index]
        current_length += 1
        if current_length == width:
            if latest_separator >= current_chunk_start:
                # Valid earlier separator, cut there
                cutting_length = char_index - latest_separator
                if not keep_separators:
                    cutting_length += 1
                if cutting_length:
                    output = output[:-cutting_length]
                output += "<linebreak>"
                current_chunk_start = latest_separator + 1
                char_index = current_chunk_start
            else:
                # No separator found, hard cut
                output += "<linebreak>"
                current_chunk_start = char_index + 1
                latest_separator = current_chunk_start - 1
                char_index += 1
            current_length = 0
        else:
            char_index += 1
    return output


def create_spell_embed_unstable(ctx: CommandContext, spell: str, spell_json: dict):
    level_school = spell_json.get("School")
    casting_time = spell_json.get("Casting Time")
    spell_range = spell_json.get("Range")
    components = spell_json.get("Components")
    duration = spell_json.get("Duration")
    description = spell_json.get("Description")
    at_higher_levels = spell_json.get("At Higher Levels")
    source = spell_json.get("Source")

    author = ctx.author
    title = spell
    school: str = level_school.split(" ")[1].replace(".", "")

    match school:
        case "abjuration":
            spell_icon = "https://i.stack.imgur.com/uzFcs.png"
        case "conjuration":
            spell_icon = "https://i.stack.imgur.com/8DWrI.png"
        case "divination":
            spell_icon = "https://i.stack.imgur.com/VfeKS.png"
        case "enchantment":
            spell_icon = "https://i.stack.imgur.com/0YuqE.png"
        case "evocation":
            spell_icon = "https://i.stack.imgur.com/lwSxi.png"
        case "illusion":
            spell_icon = "https://i.stack.imgur.com/bHkjS.png"
        case "necromancy":
            spell_icon = "https://i.stack.imgur.com/b9tgW.png"
        case "transmutation":
            spell_icon = "https://i.stack.imgur.com/wPeGf.png"
        case _:
            spell_icon = ""

    embed_initial = interactions.Embed(
        title=title,
        description=f"*{level_school}*",
        thumbnail=interactions.EmbedImageStruct(url=spell_icon, height=200, width=200),
        color=0xE2E0DD,
    )
    embed_initial.set_author(author.name, icon_url=author_url(author, ctx.guild_id))
    meta = f"**Casting Time**: {casting_time}\n"
    meta += f"**Range**: {spell_range}\n"
    meta += f"**Components**: {components}\n"
    meta += f"**Duration**: {duration}\n"
    embed_initial.add_field(
        name="Meta",
        value=meta,
    )

    if len(description) > 1024:  # embed limit
        split_descriptions = wrap_spell(description).split("<linebreak>")
    else:
        split_descriptions = [description]

    first_desc = split_descriptions.pop(0)
    embed_initial.add_field(name="Description", value=first_desc)
    embeds = (
        [
            interactions.Embed(description=desc, color=0xE2E0DD)
            for desc in split_descriptions
        ]
        if len(split_descriptions) > 0
        else []
    )
    embeds.insert(0, embed_initial)
    if at_higher_levels:
        embeds[-1].add_field(name="At Higher Levels", value=at_higher_levels)

    embeds[-1].set_footer(source)
    return embeds


banned = os.getenv("BARRED")


async def user_check(ctx, barred=[banned]):
    if str(ctx.author.id) in barred or str(ctx.user.id) in barred:
        await ctx.send(
            embeds=quick_embed("Nah", "I'm not playing. Use your sheet.", "error"),
            ephemeral=True,
        )
        return True
    return False
