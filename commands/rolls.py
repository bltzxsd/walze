import asyncio
import string

import interactions
import requests
import rolldice
from bs4 import BeautifulSoup, SoupStrainer
from interactions import CommandContext
from lib import json_lib, misc


class RollCommands(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
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
    async def roll(
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
        if sides < 1:
            return await ctx.send(
                embed=misc.quick_embed(
                    "Error", "A dice can't have less than 1 sides", "error"
                )
            )

        dice_expr = str(rolls) + "d" + str(sides)
        display_syn = dice_expr
        if implication:
            dice_expr += implication
            display_syn += implication
            if dice_expr[0] == "1":
                dice_expr = "2" + dice_expr[1:]

        if mod != 0:
            modifier = str(mod) if str(mod)[0] == "-" else f"+{mod}"
            dice_expr += modifier
            display_syn += modifier
        if extension:
            match extension[0]:
                case "-" | "*" | "/" | "+":
                    opr = ""
                case _:
                    opr = "+"
            dice_expr += opr + extension
            display_syn += opr + extension

        try:
            result, explanation = rolldice.roll_dice(dice_expr)
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )
        embed = misc.unstable_roll_embed(
            ctx.author, display_syn, result, explanation, implication
        )
        await ctx.send(embeds=embed, ephemeral=ephemeral)

    @interactions.extension_command(
        name="custom",
        description="Rolls a custom dice.",
        options=[
            interactions.Option(
                name="custom",
                description="The name of the custom parameter to roll.",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
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
        ],
    )
    async def custom(
        self, ctx: CommandContext, custom: str, implication: str = ""
    ):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            parameter = (
                content.get(str(ctx.author.id)).get("custom").get(custom)
            )
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "No such parameter available!", "error"
                ),
                ephemeral=True,
            )
        display_param = parameter
        parameter = "".join(parameter.split())
        parameter = misc.normalize_implication(parameter, implication)
        try:
            result, explanation = rolldice.roll_dice(parameter)
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )

        embed = misc.unstable_roll_embed(
            ctx.author, display_param, result, explanation, implication
        )
        await ctx.send(embeds=embed)

    @interactions.extension_command(
        name="cast",
        description="Cast spells from your spellbook.",
        options=[
            interactions.Option(
                name="spell",
                description="Name of the Spell.",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
            ),
        ],
    )
    async def cast(self, ctx: CommandContext, spell: str):
        if await misc.user_check(ctx):
            return

        spell_url = spell.lower().replace(" ", "-").replace("'", "")
        spell_url = "http://dnd5e.wikidot.com/spell:" + spell_url
        page = requests.get(spell_url)
        if page.status_code != 200:
            return await ctx.send(
                embeds=misc.quick_embed(
                    f"Failed to fetch spell: {spell_url}",
                    "Please check if spell exists and try again. Status Code:"
                    + str(page.status_code),
                    "error",
                ),
                ephemeral=True,
            )
        soup = BeautifulSoup(
            page.text,
            "html.parser",
            parse_only=SoupStrainer("div", "main-content"),
        )
        spellname, spell_attrs = json_lib.spell_to_dict(soup.get_text())

        embed = misc.spell_embed(ctx, spellname, spell_attrs)

        dice = spell_attrs.get("Description")
        dice: str = dice + spell_attrs.get("At Higher Levels")
        dice_syns = [*set(misc.find_dice(dice))]  # remove dupes

        buttons = [misc.to_button(dice) for dice in dice_syns]

        link_button = interactions.Button(
            style=interactions.ButtonStyle.LINK,
            label="Wiki",
            url=f"http://dnd5e.wikidot.com/spell:{spell.lower().replace(' ', '-')}",
        )
        if buttons:
            cancel_button = interactions.Button(
                style=interactions.ButtonStyle.DANGER,
                label="Cancel",
                custom_id="cancel",
            )
            buttons.append(link_button)
            buttons.append(cancel_button)
            rows = interactions.spread_to_rows(*buttons)
            await ctx.send(embeds=embed, components=rows)
        else:
            return await ctx.send(embeds=embed, components=link_button)

        async def check(button_ctx: interactions.ComponentContext):
            if int(button_ctx.author.id) == int(ctx.author.id):
                return True
            else:
                error_embed = misc.quick_embed(
                    "Error",
                    "Not allowed to interact with this button.",
                    "error",
                )
                error_embed.set_author(
                    name=misc.author_name(button_ctx.author),
                    icon_url=misc.author_url(button_ctx.author),
                )
                await button_ctx.send(embeds=error_embed, ephemeral=True)
                return False

        def disable(buttons: list[interactions.Button]):
            for button in buttons:
                if button.style != interactions.ButtonStyle.LINK:
                    button.disabled = True

        try:
            button_ctx: interactions.ComponentContext = (
                await self.client.wait_for_component(
                    components=rows, check=check, timeout=30
                )
            )
            performed = button_ctx.data.custom_id
            if performed == "cancel":
                disable(buttons)
                await button_ctx.send(
                    embeds=misc.quick_embed(
                        "Cancelled Roll", "No rolls selected.", "ok"
                    ),
                    ephemeral=True,
                )
                return await ctx.edit(
                    components=interactions.spread_to_rows(*buttons)
                )
            else:
                rolls, sides, mod = misc.decipher_dice(performed)
                dice_syn = str(rolls) + "d" + str(sides)
                if mod != 0:
                    dice_syn += str(mod) if mod < 0 else f"+{mod}"

                disable(buttons)
                await ctx.edit(components=interactions.spread_to_rows(*buttons))
                try:
                    result, explanation = rolldice.roll_dice(dice_syn)
                except (
                    rolldice.DiceGroupException,
                    rolldice.DiceOperatorException,
                ) as exc:
                    return await ctx.send(
                        embeds=misc.quick_embed("Error", str(exc), "error"),
                        ephemeral=True,
                    )
                roll_embed = misc.unstable_roll_embed(
                    ctx.author, dice_syn, result, explanation, ""
                )

                return await button_ctx.send(embeds=roll_embed)
        except asyncio.TimeoutError:
            disable(buttons)
            return await ctx.edit(
                components=interactions.spread_to_rows(*buttons)
            )

    @interactions.extension_command(
        name="initiative",
        description="Roll for initiative.",
    )
    async def initiative(self, ctx: interactions.CommandContext):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        init = content.get(str(ctx.author.id)).get("initiative")
        if not init:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "Initiative has not been set.", "error"
                ),
                ephemeral=True,
            )

        try:
            result, explanation = rolldice.roll_dice(init)
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )

        embed = misc.unstable_roll_embed(ctx.author, init, result, explanation)

        syntax_embed = misc.quick_embed(
            "Initiative Syntax",
            f"```{misc.author_name(ctx.author)}:{result} ```",
            "ok",
        )
        syntax_embed.set_footer(
            "Copy this ⬆️ (including the space at the end) for the `/sort` command! "
        )
        await ctx.send(embeds=[embed, syntax_embed])

    @interactions.extension_command(
        name="skill",
        description="Roll for skill in saved parameter.",
        options=[
            interactions.Option(
                name="skill",
                description="Roll for the given skill. Eg: `Insight`, `Perception`",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
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
        ],
    )
    async def skill(
        self,
        ctx: interactions.CommandContext,
        skill: str,
        implication: str = "",
    ):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            display_skill = skill
            skill = (
                content.get(str(ctx.author.id))
                .get("stats")
                .get(string.capwords(skill))
            )
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error",
                    f"No such skill available! ({string.capwords(skill)})",
                    "error",
                ),
                ephemeral=True,
            )

        dice_syn = "1d20"
        if implication:
            dice_syn = "2" + dice_syn[1:] + implication
        if skill != 0:
            dice_syn += str(skill) if skill < 0 else f"+{skill}"

        try:
            result, explanation = rolldice.roll_dice(dice_syn)
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )
        title = (
            string.capwords(display_skill)
            + ": "
            + "1d20"
            + (str(skill) if skill < 0 else f"+{skill}")
        )
        embed = misc.unstable_roll_embed(
            ctx.author,
            title,
            result,
            explanation,
            implication,
        )
        await ctx.send(embeds=embed)

    @interactions.extension_command(
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
                description="implication for the roll",
                type=interactions.OptionType.STRING,
                choices=[
                    interactions.Choice(name="Advantage", value="K"),
                    interactions.Choice(name="Disadvantage", value="k"),
                ],
                required=False,
            ),
        ],
    )
    async def attack(
        self,
        ctx: interactions.CommandContext,
        weapon: str,
        implication: str = "",
    ):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            weapons = content.get(str(ctx.author.id)).get("weapons")
            weapon_str = weapon
            weapon = weapons.get(weapon)
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "No such weapon available!", "error"
                ),
                ephemeral=True,
            )

        hit = weapon.get("hit")
        dmg = weapon.get("dmg")
        typ = weapon.get("type")
        initial_embed = misc.quick_embed(weapon_str, "", "ok")
        initial_embed.set_author(
            misc.author_name(ctx.author), icon_url=misc.author_url(ctx.author)
        )
        initial_embed.add_field("Damage Type", f"*{typ}*")
        initial_embed.add_field("Hit", hit)
        initial_embed.add_field("Damage", dmg)
        attacks = [("Attack", hit), ("Damage", dmg)]

        buttons = [misc.to_button(name, dice) for name, dice in attacks]

        await ctx.send(embeds=initial_embed, components=buttons)

        async def auth_check(button_ctx: interactions.ComponentContext):
            if int(button_ctx.author.id) == int(ctx.author.id):
                return True
            else:
                error_embed = misc.quick_embed(
                    "Error",
                    "Not allowed to interact with this button.",
                    "error",
                )
                error_embed.set_author(
                    name=misc.author_name(button_ctx.author),
                    icon_url=misc.author_url(button_ctx.author),
                )
                await button_ctx.send(embeds=error_embed, ephemeral=True)
                return False

        try:
            button_ctx: interactions.ComponentContext = (
                await self.client.wait_for_component(
                    components=buttons, check=auth_check, timeout=45
                )
            )
            selected = button_ctx.data.custom_id

            dice_syn = misc.normalize_implication(selected, implication)

            try:
                result, explanation = rolldice.roll_dice(dice_syn)
            except (
                rolldice.DiceGroupException,
                rolldice.DiceOperatorException,
            ) as exc:
                return await ctx.send(
                    embeds=misc.quick_embed("Error", str(exc), "error"),
                    ephemeral=True,
                )
            roll_embed = misc.unstable_roll_embed(
                ctx.author, dice_syn, result, explanation, ""
            )
            for button in buttons:
                button.disabled = True
            await ctx.edit(components=buttons)
            await button_ctx.send(embeds=roll_embed)
        except asyncio.TimeoutError:
            for button in buttons:
                button.disabled = True
            return await ctx.edit(components=buttons)

    @interactions.extension_command(
        name="dicestats",
        description="Roll dice for stats.",
        options=[
            interactions.Option(
                name="dice",
                description="Dice rolls to use.",
                type=interactions.OptionType.STRING,
                autocomplete=True,
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
    async def roll_stats(
        self, ctx: CommandContext, dice: str, ephemeral: bool = False
    ):
        try:
            stats = [rolldice.roll_dice(dice) for _ in range(6)]
        except (
            rolldice.DiceGroupException,
            rolldice.DiceOperatorException,
        ) as exc:
            return await ctx.send(
                embeds=misc.quick_embed("Error", str(exc), "error"),
                ephemeral=True,
            )

        embed = misc.stats_embed(ctx.author, stats, dice)

        await ctx.send(embeds=embed, ephemeral=ephemeral)


def setup(client):
    RollCommands(client)
