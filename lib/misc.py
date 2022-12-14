import json
import random
import re

import aiofiles
import interactions
import pyfiglet
from interactions import CommandContext, Embed, Member, User

from lib import constants

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
    def __init__(self, author: Member | User):
        self.character = {
            str(author.id): {
                "name": author_name(author),
                "stats": {},
                "weapons": {},
                "custom": {},
                "features": {},
                "initiative": "",
            }
        }


def quick_embed(title: str, desc: str, ty: str):
    match ty:
        case "info":
            color = 0x95E9FE
        case "warn":
            color = 0xFEEC95
        case "error":
            color = 0xFF7373
        case "ok":
            color = 0xAEFF73
        case _:
            color = 0xD8D8D8

    return Embed(
        title=title,
        description=desc,
        color=color,
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


async def open_stats(author: Member):
    char = CharRepr(author)
    try:
        content = constants.SHEETS.read()
        content: dict = json.loads(content)
    except json.JSONDecodeError:
        content: dict = json.loads("{}")

    if content.get(str(author.id)) is None or content == {}:
        async with aiofiles.open("stats.json", "w") as save:
            content.update(char.character)
            await save.write(json.dumps(content, indent=4))

    return content


def create_choice(choice: str, value: str = ""):
    if not value:
        value = choice

    return interactions.Choice(name=choice, value=value)


def author_url(author: Member | User):
    base_url = "https://cdn.discordapp.com/avatars"
    try:
        icon = f"{base_url}/{author.id}/{author.avatar}.webp"
    except AttributeError:
        icon = ""

    return icon


def to_button(
    label: str,
    id: str = "",
    style: interactions.ButtonStyle = interactions.ButtonStyle.SECONDARY,
):
    if not id:
        id = label
    return interactions.Button(style=style, label=label, custom_id=id)


# ttps://stackoverflow.com/a/65038809
def wrap_spell(source_text, separator_chars, width=1024, keep_separators=True):
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


def spell_embed(ctx: CommandContext, spell: str, spell_json: dict):
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
    idx = 0 if 'cantrip' in level_school else 1
    school: str = level_school.split(" ")[idx].replace(".", "")

    match school:
        case "abjuration":
            spell_icon = "https://i.imgur.com/H8cB8mv.png"
        case "conjuration":
            spell_icon = "https://i.imgur.com/jjtwfqF.png"
        case "divination":
            spell_icon = "https://i.imgur.com/6kQkFHa.png"
        case "enchantment":
            spell_icon = "https://i.imgur.com/rfeTLTh.png"
        case "evocation":
            spell_icon = "https://i.imgur.com/pTpQUGV.png"
        case "illusion":
            spell_icon = "https://i.imgur.com/uEWl5eS.png"
        case "necromancy":
            spell_icon = "https://i.imgur.com/Aw5eUkK.png"
        case "transmutation":
            spell_icon = "https://i.imgur.com/r7ucT57.png"
        case _:
            spell_icon = ""

    embed_initial = interactions.Embed(
        title=title,
        description=f"*{level_school}*",
        thumbnail=interactions.EmbedImageStruct(
            url=spell_icon, height=200, width=200
        ),
        color=0xE2E0DD,
    )
    embed_initial.set_author(author_name(author), icon_url=author_url(author))
    meta = f"**Casting Time**: {casting_time}\n"
    meta += f"**Range**: {spell_range}\n"
    meta += f"**Components**: {components}\n"
    meta += f"**Duration**: {duration}\n"
    embed_initial.add_field(
        name="Meta",
        value=meta,
    )

    if len(description) > 1024:  # embed limit
        split_descriptions = wrap_spell(
            description, separator_chars=["."]
        ).split("<linebreak>")
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


async def user_check(ctx):
    barred = constants.CONFIG.barred_users
    if int(ctx.author.id) in barred or int(ctx.user.id) in barred:
        await ctx.send(
            embeds=quick_embed(
                "Nah", "I'm not playing. Use your sheet.", "error"
            ),
            ephemeral=True,
        )
        return True
    return False


def unstable_roll_embed(
    author: User | Member,
    dice_expr: str,
    result,
    explanation: str,
    implication: str = "",
):
    if "K" in dice_expr:
        implication = "K"
    if "k" in dice_expr:
        implication = "k"
    title = dice_expr.replace("k", "", 1).replace("K", "", 1).replace("*", "\*")
    embed = interactions.Embed(title=title, color=0xE2E0DD)
    embed.set_author(name=author_name(author), icon_url=author_url(author))
    explanation = explanation.replace(",", ", ").replace("a", "+")

    match implication:
        case "k":
            embed.add_field("Implication", "*Rolling with Disadvantage*")
        case "K":
            embed.add_field("Implication", "*Rolling with Advantage*")
        case _:
            pass

    embed.add_field("Products", explanation)
    figlet = pyfiglet.figlet_format(str(result), "fraktur", width=60).replace(
        "`", "\u200b`"
    )
    result_field = f"```{figlet}```" if len(figlet) <= 1024 else f"**{result}**"
    embed.add_field("Result", result_field, inline=False)
    embed.set_footer(f"{result}")
    return embed


def stats_embed(author: User | Member, dice: list, syn: str):
    embed = interactions.Embed(title=syn, color=0xE2E0DD)
    embed.set_author(name=author_name(author), icon_url=author_url(author))
    for res, expl in dice:
        embed.add_field(
            expl.replace(",", ", "), "**" + str(res) + "**", inline=True
        )

    embed.set_footer(f"Total Stats: {sum([s for s, _ in dice])}")
    return embed


def normalize_implication(dice_syn: str, implication: str = ""):
    sub_str = r"\1{}".format(implication)
    dice_syn = re.sub(constants.INITIAL_DICE_SYNTAX, sub_str, dice_syn)
    if implication and dice_syn[0] == "1":
        dice_syn = "2" + dice_syn[1:]
    return dice_syn


def author_name(author: Member | User):
    if isinstance(author, Member):
        return author.user.username
    if isinstance(author, User):
        return author.username
    return ""
