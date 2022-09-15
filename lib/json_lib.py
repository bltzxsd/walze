import json
import logging
import re

import aiofiles
from interactions import CommandContext, Member

import lib.misc as misc


async def modify_param(
    ctx: CommandContext, access: str, key: str, value: str | dict
) -> tuple[str, str, str]:

    content = await misc.open_stats(ctx.author)

    author = content[str(ctx.author.id)]
    try:
        skills = author.get("stats")
        weapon = author.get("weapons")
        custom = author.get("custom")
        spells = author.get("spells")
        features = author.get("features")
    except KeyError:
        author["stats"] = {}
        author["weapons"] = {}
        author["custom"] = {}
        author["spells"] = {}
        author["features"] = {}

    match access:
        case "char":
            level = author
        case "skills":
            level = skills
        case "weapons":
            level = weapon
        case "custom":
            level = custom
        case "spells":
            level = spells
        case "features":
            level = features
        case _:
            return "Error", "Access Level not specified", "error"

    async with aiofiles.open("stats.json", "w") as save:
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                pass

        try:
            prev_value = level.get(key)
        except KeyError:
            prev_value = None

        level[key] = value
        await save.write(json.dumps(content, indent=4))
        return (
            "Values Modified",
            f"Previous Value:\n{key}: {prev_value}\nNew Value:\n{key}: {level[key]}",
            "ok",
        )


def create_skills(skills: str):
    skill_values = [int(value) for value in re.findall(r"-?\d+", skills)]
    try:
        assert len(skill_values) == 18
    except AssertionError as exc:
        raise AssertionError(f"{skill_values}") from exc

    skills: dict = {name: value for name, value in zip(misc.stats, skill_values)}
    return skills


async def write_stats(author: Member, skills: str):
    try:
        skills = create_skills(skills)
    except AssertionError as exc:
        return (
            "Error",
            f"Invalid number of values provided ({len(skills)}). Needed: 18.\n{exc}",
            "error",
        )
    content = await misc.open_stats(author)
    skills_json: dict = content[str(author.id)]["stats"]
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
    level_school = spell_splits[4].split(": ")[-1].lower() + f". ({spell_lists})"
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
