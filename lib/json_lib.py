import contextlib
import json
import pprint
import re

import aiofiles
from interactions import CommandContext, Member

from lib import misc


async def modify_param(
    ctx: CommandContext, access: str, key: str, value: str | dict
) -> tuple[str, str, str]:

    content = await misc.open_stats(ctx.author)

    author: dict = content.get(str(ctx.author.id), {})

    match access:
        case "char":
            level = author
        case "skills":
            level = author.get("stats", {})
        case "weapons":
            level = author.get("weapons", {})
        case "custom":
            level = author.get("custom", {})
        case _:
            return "Error", "Access Level not specified", "error"

    async with aiofiles.open("stats.json", "w") as save:
        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                value = int(value)

        try:
            prev_value = level.get(key)
        except KeyError:
            prev_value = None

        level[key] = value
        await save.write(json.dumps(content, indent=4))

        prev_value = (
            pprint.pformat(prev_value, indent=4)
            if prev_value is not None
            else prev_value
        )
        new_value = pprint.pformat(level[key], indent=4)
        desc = f"Changed '{key}' from:\n\t{prev_value}\nto:\n\t{new_value}"
        return ("Values Modified", desc, "ok")


def create_skills(skills: str):
    skill_values = [int(value) for value in re.findall(r"-?\d+", skills)]
    try:
        assert len(skill_values) == 18
    except AssertionError as exc:
        error = f"Invalid number of values provided ({len(skill_values)})\n"
        raise AssertionError(
            error + pprint.pformat(skill_values, indent=4)
        ) from exc
    skills: dict = dict(zip(misc.stats, skill_values))

    return skills


async def write_stats(author: Member, skills: str):
    try:
        skills = create_skills(skills)
    except AssertionError as exc:
        return (
            "Error",
            str(exc),
            "error",
        )
    content = await misc.open_stats(author)
    skills_json: dict = content.get(str(author.id)).get("stats")
    prev = json.dumps(skills_json, indent=4)
    skills_json.update(skills)

    async with aiofiles.open("stats.json", "w") as save:
        await save.write(json.dumps(content, indent=4))
        return (
            "Values Added",
            f"```Previous Values:\n{prev}\nNew Values:\n{json.dumps(skills_json, indent=4)}```",
            "ok",
        )


def spell_to_dict(web_spell: str) -> tuple[str, dict]:
    spell_txt = web_spell.splitlines()[1:-9]
    spell_txt = "\n".join(spell_txt).replace("\u2019", "'")
    spell_splits: list[str] = spell_txt.splitlines()

    for x in range(1, 4):
        spell_splits.pop(x)

    spell_lists = spell_splits[-1].split(". ")[-1]
    name = spell_splits[0]
    spell_source = spell_splits[3].split(": ")[-1]
    level_school = (
        spell_splits[4].split(": ")[-1].lower() + f". ({spell_lists})"
    )
    casting_time = spell_splits[5].split(": ")[-1]
    spell_range = spell_splits[6].split(": ")[-1]
    components = spell_splits[7].split(": ")[-1]
    duration = spell_splits[8].split(": ")[-1]
    proto_description = "\n".join(spell_splits[9:-1])

    if "At Higher Levels." in proto_description:
        proto_info = proto_description.split("At Higher Levels.")
        description = "\n".join(proto_info[:-1])
        at_higher_levels = proto_info[-1].strip()
    else:
        description = proto_description
        at_higher_levels = ""

    return name, {
        "School": level_school,
        "Casting Time": casting_time,
        "Range": spell_range,
        "Components": components,
        "Duration": duration,
        "Description": description,
        "At Higher Levels": at_higher_levels,
        "Source": spell_source,
    }
