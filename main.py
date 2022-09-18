import logging

import interactions
import pyfiglet
from interactions.ext import wait_for
from py_expression_eval import Parser

from lib import constants, misc
from lib.misc import quick_embed

synced: bool = False
discord_token = constants.CONFIG.tokens.get("discord", "")
constants.CONFIG.set_logs()

bot = interactions.Client(token=discord_token, intents=interactions.Intents.DEFAULT)

bot.load("interactions.ext.files")
wait_for.setup(bot)


@bot.event
async def on_ready():
    # just in case i need to do something on start
    if not synced:
        pass

    logging.info(f"Logged in as {bot.me.name}")


@bot.event
async def on_command(ctx: interactions.CommandContext):
    logging.info(
        f"Command: {ctx.data.name} by {ctx.author} in guild {ctx.guild_id}:#{ctx.channel}"
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
        ),
        interactions.Option(
            name="ephemeral",
            description="Whether the result should only be visible to the user.",
            type=interactions.OptionType.BOOLEAN,
            required=False,
        ),
    ],
)
async def evaluate(
    ctx: interactions.CommandContext, expr: str, ephemeral: bool = False
):
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


bot.load("commands.base")
bot.load("commands.rolls")
bot.load("commands.modify")
bot.load("commands.unstable")
bot.load("commands.autocomplete")
bot.start()
