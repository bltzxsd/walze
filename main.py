import json
import logging
import operator
import os
import string
import sys

import interactions
import pyfiglet
from dotenv import load_dotenv
from py_expression_eval import Parser

import lib.json_lib as json_lib
import lib.misc as misc
from lib.misc import decipher_dice, open_stats, quick_embed

synced: bool = False

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S %p",
    filename="bot.log",
)

bot = interactions.Client(token=os.getenv("DISCORD_TOKEN"))
hq = os.getenv("HQ")


@bot.event
async def on_ready():
    # just in case i need to do something on start
    if not synced:
        pass

    logging.info(f"Logged in as {bot.me.name}")


@bot.event
async def on_command(ctx: interactions.CommandContext):
    logging.debug(
        f"Command: {ctx.data.name}#{ctx.data.id} by {ctx.author} in guild {ctx.guild_id}:#{ctx.channel}"
    )


# @bot.event
# async def on_command_error(ctx: interactions.CommandContext, error: Traceback):
#     await ctx.send(
#         embeds=quick_embed(
#             "Something went wrong!", f"Please report this:\n{error}\n", "error"
#         ),
#         ephemeral=True,
#     )


@bot.command(
    name="ping",
    description="Get latency.",
)
async def ping(ctx: interactions.CommandContext):
    await ctx.send(
        embeds=quick_embed(
            "Ping", f"Can't stop the A-Train, baby! 😈 ({round(bot.latency)}ms)", "ok"
        )
    )


@bot.command(name="kill", description="Kill bot.", scope=hq)
async def kill(ctx: interactions.CommandContext):
    if ctx.author.id == int(os.getenv("OWNER")):
        await ctx.send("Killing bot.", ephemeral=True)
        await sys.exit(0)
    else:
        return await ctx.send("LMFAOOOOOO", ephemeral=True)


@bot.command(
    name="sort",
    description="Sorts entities by their values.",
    options=[
        interactions.Option(
            name="names",
            description="Names of the entities. Eg: `Entity1 Entity2 Entitiy3`.",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="initiatives",
            description="Values for the entities. Eg: `21 15 19`",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def sort(ctx: interactions.CommandContext, names: str, initiatives: str):
    names = names.split()
    initiatives = [int(n) for n in initiatives.split()]
    zipped = list(zip(names, initiatives))
    sorted_list = sorted(zipped, key=operator.itemgetter(1), reverse=True)
    pretty_print = "\n".join(
        f"{name}:\t{value}".expandtabs(8) for name, value in sorted_list
    )
    await ctx.send(
        embeds=quick_embed("Ordered List", f"```\n{pretty_print}\n```", "ok")
    )


@bot.command(
    name="eval",
    description="Evaluate mathematical expressions quickly.",
    options=[
        interactions.Option(
            name="expr",
            description="Expression to be calculated. Eg: `1 + 1 * 1 - 1 ^ 1 / 1`",
            type=interactions.OptionType.STRING,
            required=True,
        )
    ],
)
async def eval(ctx: interactions.CommandContext, expr: str):
    parser = Parser()
    try:
        expression = parser.parse(expr).evaluate({})
    except Exception as e:
        title, desc, status = "Error", f"Exception Occured:\n{e}", "error"
        ephemeral = True
    else:
        figlet = pyfiglet.figlet_format(str(expression), "fraktur")
        figlet = figlet.replace("`", "​`")
        desc = f"```{figlet}```" if len(figlet) < 1024 else f"**{expression}**"
        title, status = f"Evaluation: {expr}", "ok"
        ephemeral = False

    embed = quick_embed(title, desc, status)
    embed.set_footer(f"{expression}")
    await ctx.send(embeds=embed, ephemeral=ephemeral)


@bot.command(
    name="roll",
    description="Roll a dice.",
    options=[
        interactions.Option(
            name="rolls",
            description="Number of times to roll the dice. Eg: `1`, `2`, `3`",
            type=interactions.OptionType.INTEGER,
            required=True,
        ),
        interactions.Option(
            name="sides",
            description="Number of sides the dice should have. Eg: `4`, `6`, `8`, `10`, `20`",
            type=interactions.OptionType.INTEGER,
            required=True,
        ),
        interactions.Option(
            name="mod",
            description="Add or subtract modifiers from the dice roll. Eg: `1` or `-2`",
            type=interactions.OptionType.INTEGER,
            required=False,
        ),
        interactions.Option(
            name="implication",
            description="Choose if the roll should have an advantage or disadvantage.",
            type=interactions.OptionType.STRING,
            choices=[
                interactions.Choice(name="Advantage", value="adv"),
                interactions.Choice(name="Disadvantage", value="dis"),
            ],
            required=False,
        ),
        interactions.Option(
            name="ephemeral",
            description="Whether the result should only be visible to the user.",
            type=interactions.OptionType.BOOLEAN,
            required=False,
        ),
    ],
)
async def roll(
    ctx: interactions.CommandContext,
    rolls: int,
    sides: int,
    ephemeral: bool = False,
    implication: str = "",
    mod: int = 0,
):
    if rolls <= 0:
        return await ctx.send(
            embed=quick_embed("Error", "Rolls can't be negative or zero!", "error")
        )
    elif sides < 1:
        return await ctx.send(
            embed=quick_embed("Error", "A dice can't have less than 1 sides", "error")
        )

    result, generated_values = misc.roll_dice(rolls, sides, implication, mod)
    embed = misc.roll_embed(
        ctx.author, rolls, sides, result, generated_values, implication, mod=mod
    )

    await ctx.send(embeds=embed, ephemeral=ephemeral)

@bot.command(
    name="modify",
    description="Modify a value",
)
async def modify(_ctx: interactions.CommandContext):
    pass

@bot.command(
    name="weapon",
    description="Rolls a weapon from your inventory.",
    options=[
        interactions.Option(
            name="name",
            description="The name of the weapon to roll.",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        ),
        interactions.Option(
            name="implication",
            description="Roll type for the weapon.",
            type=interactions.OptionType.STRING,
            choices=[
                interactions.Choice(name="Hit", value="hit"),
                interactions.Choice(name="Damage", value="dmg"),
                interactions.Choice(name="Attribute", value="attr"),
            ],
            required=True,
        ),
    ],
)
async def weapon(ctx: interactions.CommandContext, name: str, implication: str):
    content = await open_stats(ctx.author)
    try:
        weapons = content[str(ctx.author.id)]["weapon"]
        weapon = weapons[string.capwords(name)]
    except:
        return await ctx.send(
            embeds=quick_embed("Error", "No such weapon available!", "error"),
            ephemeral=True,
        )
    match implication:
        case "hit":
            weapon = weapon["hit"]
        case "dmg":
            weapon = weapon["dmg"]
        case "attr":
            weapon = weapon["attribute"]
            if not weapon:
                return await ctx.send(
                    embeds=quick_embed(
                        "Error", "Weapon does not have an attribute!", "error"
                    ),
                    ephemeral=True,
                )

    rolls, sides, mod = misc.decipher_dice(weapon)
    result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
    embed = misc.roll_embed(ctx.author, rolls, sides, result, generated_values, mod=mod)
    await ctx.send(embeds=embed)


@bot.autocomplete("weapon", "name")
async def weapon_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        weapons = content[str(ctx.author.id)]["weapon"]
    except:
        return

    autocomplete = [
        interactions.Choice(name=param, value=param)
        for param in weapons.keys()
        if string.capwords(value) in param
    ]
    await ctx.populate(autocomplete)


@bot.command(
    name="skill",
    description="Roll for skill in saved parameter.",
    options=[
        interactions.Option(
            name="skill",
            description="Roll for the given skill. Eg: `Insight`, `Perception`",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        )
    ],
)
async def skill(ctx: interactions.CommandContext, skill: str):
    content = await open_stats(ctx.author)
    try:
        skill = content[str(ctx.author.id)]["stats"][string.capwords(skill)]
    except:
        return await ctx.send(
            embeds=quick_embed(
                "Error", f"No such skill available! ({string.capwords(skill)})", "error"
            ),
            ephemeral=True,
        )

    rolls, sides, mod = 1, 20, skill
    result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
    embed = misc.roll_embed(ctx.author, rolls, sides, result, generated_values, mod=mod)
    await ctx.send(embeds=embed)


@bot.autocomplete("skill", "skill")
async def skill_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        skills = content[str(ctx.author.id)]["stats"]
    except:
        return

    autocomplete = [
        interactions.Choice(name=param, value=param)
        for param in skills.keys()
        if value.capitalize() in param
    ]
    await ctx.populate(autocomplete)


@bot.command(
    name="initiative",
    description="Roll for initiative.",
)
async def initiative(ctx: interactions.CommandContext):
    content = await open_stats(ctx.author)
    init = content[str(ctx.author.id)]["initiative"]
    if not init:
        return await ctx.send(
            embeds=quick_embed("Error", "Initiative has not been set.", "error"),
            ephemeral=True,
        )

    try:
        rolls, sides, mod = decipher_dice(init)
    except ValueError as e:
        return await ctx.send(
            embeds=quick_embed("Error", f"Please report this!\n{e}", "error"),
            ephemeral=True,
        )

    result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
    embed = misc.roll_embed(ctx.author, rolls, sides, result, generated_values, mod=mod)
    await ctx.send(embeds=embed)


@modify.subcommand(
    name="skill",
    description="Modifies skill parameters.",
    options=[
        interactions.Option(
            name="skill",
            description="Skill to modify. Eg. `Acrobatics`, `Deception`",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        ),
        interactions.Option(
            name="value",
            description="Value to modify. Eg. `1`, `2`, `4`, `8`.",
            type=interactions.OptionType.INTEGER,
            required=True,
        ),
    ],
)
async def modify_skill(ctx: interactions.CommandContext, skill: str, value: int):

    output, reply, color = await json_lib.modify_param(
        ctx, access="skills", key=string.capwords(skill), value=value
    )
    await ctx.send(embeds=quick_embed(output, f"```{reply}```", color), ephemeral=True)


@bot.autocomplete("modify", "skill")
async def modify_skill_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        skills = content[str(ctx.author.id)]["stats"]
    except:
        return

    autocomplete = [
        interactions.Choice(name=param, value=param)
        for param in skills.keys()
        if value.capitalize() in param
    ]
    await ctx.populate(autocomplete)



@modify.subcommand(
    name="weapon",
    description="Modify weapon parameters.",
    options=[
        interactions.Option(
            name="weapon",
            description="Name of the weapon to modify Eg. `Longsword`, `Shortbow`",
            type=interactions.OptionType.STRING,
            required=True,
            autocomplete=True,
        ),
        interactions.Option(
            name="hit",
            description="Value of the weapon (hit) to modify, Eg. `1d20+2`, `1d20-4`.",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="dmg",
            description="Value of the weapon (dmg) to modify, Eg. `1d8+2`, `2d6`",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="attribute",
            description="Value of the attribute of the weapon Eg. `2d6`, `1d6`",
            type=interactions.OptionType.STRING,
            required=False,
        ),
    ],
)
async def modify_weapon(
    ctx: interactions.CommandContext, name: str, hit: str, dmg: str, attribute: str = ""
):
    try:
        misc.decipher_all([hit, dmg])
        if attribute:
            misc.decipher_dice(attribute)
    except ValueError:
        return await ctx.send(
            embeds=quick_embed(
                "Error", f"A value here does not fit the roll syntax!", "error"
            ),
            ephemeral=True,
        )
    value = {"hit": hit, "dmg": dmg, "attribute": attribute}

    output, reply, color = await json_lib.modify_param(
        ctx, access="weapon", key=string.capwords(name), value=value
    )
    await ctx.send(embeds=quick_embed(output, f"```{reply}```", color), ephemeral=True)


@bot.autocomplete("modify", "weapon")
async def modify_weapon_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        params: dict = content[str(ctx.author.id)]["weapon"]
    except:
        logging.error(params)
        return

    autocomplete = [
        interactions.Choice(name=string.capwords(param), value=param)
        for param in params.keys()
        if string.capwords(value) in param
    ]
    await ctx.populate(autocomplete)


@modify.subcommand(
    name="char",
    description="Modifies character parameters.",
    options=[
        interactions.Option(
            name="char",
            description="Key to modify. Eg. `Name`, `Initiative`",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        ),
        interactions.Option(
            name="value",
            description="Value to modify. Eg. `1`, `2`, `1d8+4`",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def modify_char(ctx: interactions.CommandContext, key: str, value: str):
    output, reply, color = await json_lib.modify_param(
        ctx, access="char", key=key, value=value
    )
    await ctx.send(embeds=quick_embed(output, f"```{reply}```", color), ephemeral=True)


@bot.autocomplete("modify", "char")
async def modify_char_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        params = content.get(str(ctx.author.id))
        params.pop("weapon", None)
        params.pop("stats", None)
        params.pop("custom", None)
    except:
        return

    autocomplete = [
        interactions.Choice(name=string.capwords(param), value=param)
        for param in params.keys()
        if value in param
    ]

    await ctx.populate(autocomplete)

@bot.command(
    name="save",
    description="Saves a key value pair.",
)
async def save(_ctx: interactions.CommandContext): 
    pass

@save.subcommand(
    name="skills",
    description="Saves initial skills.",
    options=[
        interactions.Option(
            name="attributes",
            description="Save all skills at once in alphabetical order. Eg: `1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18`",
            type=interactions.OptionType.STRING,
            required=True,
        )
    ],
)
async def save_skills(ctx: interactions.CommandContext, attributes: str):
    title, desc, outcome = await json_lib.write_stats(ctx.author, attributes)
    await ctx.send(embeds=quick_embed(title, desc, outcome), ephemeral=True)


@bot.command(
    name="retrieve",
    description="Shows all saved parameters for your character.",
    options=[
        interactions.Option(
            name="ephemeral",
            description="Whether the reply should be visible only to the user.",
            type=interactions.OptionType.BOOLEAN,
        ),
    ],
)
async def retrieve(ctx: interactions.CommandContext, ephemeral: bool = False):
    try:
        retrieve = await misc.open_stats(ctx.author)
        retrieve = retrieve.get(str(ctx.author.id))
    except Exception as e:
        logging.error(e)
        return await ctx.send(
            embeds=quick_embed(
                "Error", "You do not have any saved parameters!", "error"
            ),
            ephemeral=True,
        )

    retrieve = json.dumps(retrieve, indent=4)
    await ctx.send(
        embeds=quick_embed(
            f"{ctx.author.name}'s Parameters",
            f"```{retrieve}```",
            "ok",
        ),
        ephemeral=ephemeral,
    )


@bot.command(
    name="custom",
    description="Rolls a custom dice.",
    options=[
        interactions.Option(
            name="name",
            description="The name of the parameter to roll.",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        )
    ],
)
async def custom(ctx: interactions.CommandContext, name: str):
    content = await open_stats(ctx.author)
    try:
        parameter = content[str(ctx.author.id)]["custom"][name]
    except:
        return await ctx.send(
            embeds=quick_embed("Error", "No such parameter available!", "error"),
            ephemeral=True,
        )

    # rollables: list[tuple[int, int, int]] = misc.decipher_all(parameters.keys())
    rolls, sides, mod = misc.decipher_dice(parameter)
    result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
    embed = misc.roll_embed(ctx.author, rolls, sides, result, generated_values, mod=mod)
    await ctx.send(embeds=embed)


@bot.autocomplete("custom", "name")
async def char_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)
    try:
        parameters = content[str(ctx.author.id)]["custom"]
    except:
        return await ctx.send(
            embeds=quick_embed("Error", "No values exist!", "error"), ephemeral=True
        )

    autocomplete = [
        interactions.Choice(name=param, value=param)
        for param in parameters.keys()
        if string.capwords(value) in param
    ]

    await ctx.populate(autocomplete)


@modify.subcommand(
    name="custom",
    description="Modify custom rolls.",
    options=[
        interactions.Option(
            name="key",
            description="Key to modify. Eg: `Wis Save`, `Int Save`",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        ),
        interactions.Option(
            name="value",
            description="Value to modify. Eg: `1d20+4`, `1d4+5`",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def modify_custom(ctx: interactions.CommandContext, key: str, value: str):
    try:
        misc.decipher_dice(value)
    except Exception as e:
        return await ctx.send(
            embeds=quick_embed(
                "Error",
                f"Not a valid dice roll: {value}\nOnly valid dice syntax is allowed\n{e}",
                "error",
            ),
            ephemeral=True,
        )
    output, reply, color = await json_lib.modify_param(
        ctx, access="custom", key=string.capwords(key), value=value
    )
    await ctx.send(embeds=quick_embed(output, f"```{reply}```", color), ephemeral=True)
    pass


@bot.autocomplete("modify", "key")
async def modify_custom_autocomplete(ctx: interactions.CommandContext, value: str = ""):
    content = await open_stats(ctx.author)

    try:
        params = content.get(str(ctx.author.id)).get("custom")
    except:
        return

    autocomplete = [
        interactions.Choice(name=param, value=param)
        for param in params.keys()
        if value in param
    ]

    await ctx.populate(autocomplete)


bot.start()
