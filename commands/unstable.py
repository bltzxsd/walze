import interactions
import pyfiglet
import rolldice
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
        name="eval",
        description="Evaluates compound dice rolls. ",
        options=[
            interactions.Option(
                name="expr",
                description="Dice expression. Eg: `1d8+4-1d6*1d6/1d6",
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
    async def unstable_eval(
        self,
        ctx: interactions.CommandContext,
        expr: str,
        ephemeral: bool = False,
    ):
        try:
            result, explanation = rolldice.roll_dice(expr)
            explanation = explanation.replace(",", ", ")
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )

        figlet = pyfiglet.figlet_format(str(result), "fraktur")
        figlet = figlet.replace("`", "\u200B`")
        desc = f"```{figlet}```" if len(figlet) < 1024 else f"**{result}**"
        title, status = f"Evaluation: {expr}", "ok"
        embed = misc.quick_embed(title, desc, status)

        embed.set_footer(f"{explanation} = {result}")
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
    async def unstable_chance(
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
                embed_image = "https://imgur.com/0waYikK.png"
            case "adv":
                chance_decimal = (1 - (((target - bonus - 1) ** 2) / 400)) * 100
                embed_image = "https://imgur.com/n3zqzJI.png"
                implication = "*Advantage*"
            case "dis":
                chance_decimal = ((21 + bonus - target) ** 2 / 400) * 100
                embed_image = "https://imgur.com/L5M3KnW.png"
                implication = "*Disadvantage*"
            case "ea":
                chance_decimal = (1 - ((target - bonus - 1) ** 3) / 8000) * 100
                embed_image = "https://imgur.com/O6DbU4w.png"
                implication = "*Elven Accuracy*"

        if chance_decimal < 0:
            chance_decimal = 0.0

        if chance_decimal > 66:
            likelihood = "Likely to hit or exceed."
        elif chance_decimal == 0:
            likelihood = "Impossible to hit."
        else:
            likelihood = "Unlikely to hit or exceed."

        chance_decimal = str(round(chance_decimal, 2)) + "%"
        author_url = misc.author_url(ctx.author)
        embed = interactions.Embed(
            title=f"Probability to exceed {target}",
            description="**" + chance_decimal + "**",
            color=0xE2E0DD,
            image=interactions.EmbedImageStruct(url=embed_image),
        )
        embed.add_field(name="Bonus", value=bonus, inline=True)
        if implication:
            embed.add_field(name="Implication", value=implication, inline=True)
        embed.set_author(ctx.author.user.username, icon_url=author_url)
        embed.set_footer(likelihood)
        await ctx.send(embeds=embed, ephemeral=ephemeral)


def setup(client):
    Unstable(client)
