import json
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
        skills = author["stats"]
        weapon = author["weapons"]
        custom = author["custom"]
        spells = author["spells"]
        features = author["features"]
    except:
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
        try:
            value = int(value)
        except:
            pass

        try:
            prev_value = level[key]
        except:
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
    except AssertionError:
        raise Exception(f"{skill_values}")

    skills: dict = {name: value for name, value in zip(misc.stats, skill_values)}
    return skills


async def write_stats(author: Member, skills: str):
    try:
        skills = create_skills(skills)
    except Exception as e:
        return (
            "Error",
            f"Invalid number of values provided ({len(skills)}). Needed: 18.\n{e}",
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
