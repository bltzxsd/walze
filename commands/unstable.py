import interactions
import pyfiglet
import rolldice
from interactions import CommandContext, User, Member
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
        self, ctx: interactions.CommandContext, expr: str, ephemeral: bool = False
    ):
        try:
            result, explanation = rolldice.roll_dice(expr)
            explanation = explanation.replace(",", ", ")
        except (rolldice.DiceGroupException, rolldice.DiceOperatorException) as exc:
            return await ctx.send(
                embeds=misc.quick_embed(f"Error", str(exc), "error"),
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

    @unstable.subcommand(
        name="roll",
        description="Roll dice.",
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
                    interactions.Choice(name="Advantage", value="K"),
                    interactions.Choice(name="Disadvantage", value="k"),
                ],
                required=False,
            ),
            interactions.Option(
                name="extension",
                description="Any additional dice to add or subtract. Eg: `1d4+2d6+4`",
                type=interactions.OptionType.STRING,
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
    async def unstable_roll(
        self,
        ctx,
        rolls: int,
        sides: int,
        mod: int = 0,
        implication: str = "",
        extension: str = "",
        ephemeral: bool = False,
    ):
        if rolls <= 0:
            return await ctx.send(
                embed=misc.quick_embed(
                    "Error", "Rolls can't be negative or zero!", "error"
                )
            )
        elif sides < 1:
            return await ctx.send(
                embed=misc.quick_embed(
                    "Error", "A dice can't have less than 1 sides", "error"
                )
            )

        dice_expr = str(rolls) + "d" + str(sides)
        if implication:
            dice_expr += str(implication)
            if dice_expr[0] == "1":
                dice_expr = "2" + dice_expr[1:]
        if mod != 0:
            mod: str = str(mod)
            dice_expr += mod if mod[0] == "-" else f"+{mod}"
        if extension:
            match extension[0]:
                case "-" | "*" | "/":
                    pass
                case _:
                    opr = "+"
            dice_expr += opr + extension

        try:
            result, explanation = rolldice.roll_dice(dice_expr)
        except (rolldice.DiceGroupException, rolldice.DiceOperatorException) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"), ephemeral=True
            )

        display_expr = dice_expr
        if implication:
            display_expr = "1" + dice_expr[1:]

        embed = unstable_roll_embed(
            ctx.author, display_expr, result, explanation, implication
        )
        await ctx.send(embeds=embed, ephemeral=ephemeral)


def unstable_roll_embed(
    author: User | Member, dice_expr: str, result, explanation: str, implication: str
):
    author_icon = misc.author_url(author)
    title = dice_expr.replace("k", "").replace("K", "")
    embed = interactions.Embed(title=title, color=0xE2E0DD)
    name = author.user.username if isinstance(author, Member) else author.username
    embed.set_author(name=name, icon_url=author_icon)

    match implication:
        case "k":
            embed.add_field("Implication", "*Rolling with Disadvantage*")
        case "K":
            embed.add_field("Implication", "*Rolling with Advantage*")
        case _:
            pass

    embed.add_field("Products", explanation)
    figlet = pyfiglet.figlet_format(str(result), "fraktur").replace("`", "\u200b`")
    result_field = f"```{figlet}```" if len(figlet) <= 1024 else f"**{result}**"
    embed.add_field("Result", result_field, inline=False)
    embed.set_footer(f"{result}")
    return embed


def setup(client):
    Unstable(client)
