import interactions
import py_expression_eval
import pyfiglet
from interactions import CommandContext
from lib import constants, misc

scope = constants.CONFIG.owner.get("servers", [])


class Unstable(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="unstable", description="Group for unstable commands", scope=scope
    )
    async def unstable(self, _ctx: CommandContext):
        pass

    @unstable.subcommand(
        name="evaluate",
        description="Evaluates compound dice rolls. ",
        options=[
            interactions.Option(
                name="expr",
                description="Dice expression. Eg: `1d8+4+1d6+1d6+1d6",
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
    async def complex(
        self, ctx: interactions.CommandContext, expr: str, ephemeral: bool = False
    ):
        dice_syntax = expr
        expr = misc.parse_compound_dice(expr)
        parser = py_expression_eval.Parser()
        try:
            expression = parser.parse(expr).evaluate({})
        except Exception as e:
            expression = ""
            title, desc, status = "Error", f"Exception Occured:\n{e}", "error"
            ephemeral = True
        else:
            figlet = pyfiglet.figlet_format(str(expression), "fraktur")
            figlet = figlet.replace("`", "\u200B`")
            desc = f"```{figlet}```" if len(figlet) < 1024 else f"**{expression}**"
            title, status = f"Evaluation: {dice_syntax}", "ok"

        embed = misc.quick_embed(title, desc, status)
        if expression:
            embed.set_footer(f"{expr} = {expression}")
        await ctx.send(embeds=embed, ephemeral=ephemeral)

    @unstable.subcommand(
        name="chance",
        description="Quick dice chance calculations",
        options=[
            interactions.Option(
                name="target",
                description="Target to hit",
                type=interactions.OptionType.INTEGER,
                required=True,
            ),
            interactions.Option(
                name="bonus",
                description="bonuses on the number",
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
                    interactions.Choice(name="Elven Accuracy", value="ea"),
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
    async def chance(
        self,
        ctx: CommandContext,
        target: int,
        bonus: int = 0,
        implication: str = "",
        ephemeral: bool = True,
    ):
        match implication:
            case "":
                chance_decimal = ((21 + bonus - target) / 20) * 100
            case "adv":
                chance_decimal = (1 - (((target - bonus - 1) ** 2) / 400)) * 100
            case "dis":
                chance_decimal = ((21 + bonus - target) ** 2 / 400) * 100
            case "ea":
                chance_decimal = (1 - ((target - bonus - 1) ** 3) / 8000) * 100

        if chance_decimal < 0:
            chance_decimal = 0.0

        if chance_decimal > 66:
            likelihood = "Likely to hit or exceed."
        elif chance_decimal == 0:
            likelihood = "Impossible to hit."
        else:
            likelihood = "Unlikely to hit to exceed."

        chance_decimal = str(round(chance_decimal, 2)) + "%"
        author_url = misc.author_url(ctx.author, ctx.guild_id)
        embed = interactions.Embed(
            title=f"Chance to hit {target}",
            description="**" + chance_decimal + "**",
            color=0xE2E0DD,
        )
        embed.set_author(ctx.author.user.username, icon_url=author_url)
        # embed.add_field(name="\u200B", value=f"**{chance_decimal}**")
        embed.set_footer(likelihood)
        await ctx.send(embeds=embed, ephemeral=ephemeral)


def setup(client):
    Unstable(client)
