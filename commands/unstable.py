import interactions
import py_expression_eval
import pyfiglet
from interactions import CommandContext
from lib import constants, misc

scope = constants.config.owner.get("servers", [])


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
            title, desc, status = "Error", f"Exception Occured:\n{e}", "error"
            ephemeral = True
        else:
            figlet = pyfiglet.figlet_format(str(expression), "fraktur")
            figlet = figlet.replace("`", "\u200B`")
            desc = f"```{figlet}```" if len(figlet) < 1024 else f"**{expression}**"
            title, status = f"Evaluation: {dice_syntax}", "ok"

        embed = misc.quick_embed(title, desc, status)
        embed.set_footer(f"{expr} = {expression}")
        await ctx.send(embeds=embed, ephemeral=ephemeral)


def setup(client):
    Unstable(client)
