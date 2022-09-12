import asyncio
import io
import json
import logging
import operator
import os
import string
import sys

import interactions
from interactions.ext import wait_for
import pyfiglet
import requests
import validators
from dotenv import load_dotenv
from py_expression_eval import Parser

from lib import json_lib
from lib import misc
from lib.misc import decipher_dice, open_stats, quick_embed

synced: bool = False

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S %p",
    filename="bot.log",
)

bot = interactions.Client(
    token=os.getenv("DISCORD_TOKEN"), intents=interactions.Intents.DEFAULT
)
bot.load("interactions.ext.files")
wait_for.setup(bot)

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
async def evaluate(ctx: interactions.CommandContext, expr: str):
    parser = Parser()
    try:
        expression = parser.parse(expr).evaluate({})
    except Exception as e:
        title, desc, status = "Error", f"Exception Occured:\n{e}", "error"
        ephemeral = True
    else:
        figlet = pyfiglet.figlet_format(str(expression), "fraktur")
        figlet = figlet.replace("`", "\u200B`")
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
    name="attack",
    description="Rolls a weapon attack from your inventory.",
    options=[
        interactions.Option(
            name="weapon",
            description="Name of the weapon to attack with.",
            type=interactions.OptionType.STRING,
            autocomplete=True,
            required=True,
        ),
        interactions.Option(
            name="implication",
            description="Implication type for the weapon.",
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
async def attack(ctx: interactions.CommandContext, weapon: str, implication: str):
    content = await open_stats(ctx.author)
    try:
        weapons = content[str(ctx.author.id)]["weapons"]
        weapon = weapons[string.capwords(weapon)]
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


@bot.command(
    name="initiative",
    description="Roll for initiative.",
)
async def initiative(ctx: interactions.CommandContext):
    content = await open_stats(ctx.author)
    init = content[str(ctx.author.id)]["Initiative"]
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
        retrieved = await misc.open_stats(ctx.author)
        retrieved = retrieved.get(str(ctx.author.id))
    except Exception as error:
        logging.error(error)
        return await ctx.send(
            embeds=quick_embed(
                "Error", "You do not have any saved parameters!", "error"
            ),
            ephemeral=True,
        )

    retrieved = json.dumps(retrieve, indent=4)
    if len(retrieve) > 1024:
        file = io.StringIO(retrieve)
        files = interactions.File(filename=f"{ctx.author.name}_stats.json", fp=file)
        return await ctx.send(
            embeds=quick_embed(f"{ctx.author.name}'s Parameters", "", "ok"),
            files=files,
            ephemeral=ephemeral,
        )

    await ctx.send(
        embeds=quick_embed(
            f"{ctx.author.name}'s Parameters",
            f"```{retrieve}```",
            "ok",
        ),
        ephemeral=ephemeral,
    )

bot.load("commands.base")
bot.load("commands.modify")
bot.load("commands.autocomplete")
bot.start()
