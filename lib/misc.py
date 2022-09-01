import json
import logging
import random
import re
import aiofiles

import pyfiglet
from interactions import Embed, EmbedImageStruct, Member

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


def decipher_dice(roll: str) -> tuple[int, int, int]:
    values = [int(value) for value in re.findall(r"-?\d+", roll)]
    try:
        assert len(values) >= 2 and len(values) < 4
    except:
        raise ValueError(
            f"Dice Roll has an invalid amount of values. {roll}:{values}(len:{len(values)})"
        )

    if len(values) == 2:
        mod = 0
    else:
        mod = values[2]

    rolls, sides = values[0], values[1]

    return rolls, sides, mod

async def open_stats(author: Member):
    repr = {
        str(author.id): {
            "name": author.user.username,
            "stats": {},
            "weapon": {},
            "custom": {},
            "initiative": "",
        }
    }
    async with aiofiles.open("stats.json", "r") as save:
        try:
            content = await save.read()
            content: dict = json.loads(content)
            if content.get(str(author.id)) is None:
                async with aiofiles.open("stats.json", "w") as save:
                    content.update(repr)
                    await save.write(json.dumps(content, indent=4))
        except:
            content = json.loads("{}")
            async with aiofiles.open("stats.json", "w") as save:
                content.update(repr)
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
    base_url = "https://cdn.discordapp.com/avatars"
    user_avatar = f"{base_url}/{author.id}/{author.avatar}.webp"

    embed = Embed(
        title=f"{author.name}'s Roll",
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
    figlet = figlet.replace("`", "​`")

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
        except:
            pass

    return rollable
