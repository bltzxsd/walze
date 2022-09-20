import asyncio
import string

import interactions
import requests
from bs4 import BeautifulSoup, SoupStrainer
from interactions import CommandContext
from lib import json_lib, misc


class RollCommands(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

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
                    interactions.Choice(name="Advantage", value="adv"),
                    interactions.Choice(name="Disadvantage", value="dis"),
                ],
                required=False,
            ),
        ],
    )
    async def custom(self, ctx: CommandContext, custom: str, implication: str = ""):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            parameter = content.get(str(ctx.author.id)).get("custom").get(custom)
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "No such parameter available!", "error"
                ),
                ephemeral=True,
            )

        rolls, sides, mod = misc.decipher_dice(parameter)
        result, generated_values = misc.roll_dice(rolls, sides, implication, mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, implication, mod
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
                    "Failed to fetch spell",
                    "Please check if spell exists and try again. Status Code:"
                    + page.status_code,
                    "error",
                ),
                ephemeral=True,
            )
        soup = BeautifulSoup(
            page.text, "html.parser", parse_only=SoupStrainer("div", "main-content")
        )
        spellname, spell_attrs = json_lib.spell_to_dict(soup.get_text())

        embed = misc.create_spell_embed_unstable(ctx, spellname, spell_attrs)

        dice = spell_attrs.get("Description")
        dice: str = dice + spell_attrs.get("At Higher Levels")
        dice_syns = [*set(misc.find_dice(dice))]  # remove dupes

        def to_button(button):
            return interactions.Button(
                style=interactions.ButtonStyle.SECONDARY, label=button, custom_id=button
            )

        buttons = [to_button(dice) for dice in dice_syns]

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
                    "Error", "Not allowed to interact with this button.", "error"
                )
                error_embed.set_author(
                    button_ctx.author.name,
                    icon_url=misc.author_url(button_ctx.author, ctx.guild_id),
                )
                await button_ctx.send(embeds=error_embed, ephemeral=True)
                return False

        def disable(buttons: list[interactions.Button]):
            for button in buttons:
                if not button.style == interactions.ButtonStyle.LINK:
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
                return await ctx.edit(components=interactions.spread_to_rows(*buttons))
            else:
                rolls, sides, mod = misc.decipher_dice(performed)
                disable(buttons)
                await ctx.edit(components=interactions.spread_to_rows(*buttons))
                result, generated_values = misc.roll_dice(rolls, sides, "", mod)
                roll_embed = misc.roll_embed(
                    ctx.author, rolls, sides, result, generated_values, "", mod=mod
                )
                return await button_ctx.send(embeds=roll_embed)
        except asyncio.TimeoutError:
            disable(buttons)
            return await ctx.edit(components=interactions.spread_to_rows(*buttons))

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
            rolls, sides, mod = misc.decipher_dice(init)
        except ValueError as e:
            return await ctx.send(
                embeds=misc.quick_embed("Error", f"Please report this!\n{e}", "error"),
                ephemeral=True,
            )

        result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, mod=mod
        )
        syntax_embed = misc.quick_embed(
            "Initiative Syntax", f"```{ctx.author.user.username}:{result} ```", "ok"
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
                    interactions.Choice(name="Advantage", value="adv"),
                    interactions.Choice(name="Disadvantage", value="dis"),
                ],
                required=False,
            ),
        ],
    )
    async def skill(
        self, ctx: interactions.CommandContext, skill: str, implication: str = ""
    ):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            skill = (
                content.get(str(ctx.author.id)).get("stats").get(string.capwords(skill))
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

        rolls, sides, mod = 1, 20, skill
        result, generated_values = misc.roll_dice(rolls, sides, implication, mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, implication, mod
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
                name="atk",
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
    async def attack(
        self,
        ctx: interactions.CommandContext,
        weapon: str,
        atk: str,
        implication: str = "",
    ):
        if await misc.user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        try:
            weapons = content.get(str(ctx.author.id)).get("weapons")
            weapon = weapons.get(string.capwords(weapon))
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed("Error", "No such weapon available!", "error"),
                ephemeral=True,
            )
        match atk:
            case "hit":
                weapon = weapon["hit"]
            case "dmg":
                weapon = weapon["dmg"]
            case "attr":
                weapon = weapon["attribute"]
                if not weapon:
                    return await ctx.send(
                        embeds=misc.quick_embed(
                            "Error", "Weapon does not have an attribute!", "error"
                        ),
                        ephemeral=True,
                    )

        rolls, sides, mod = misc.decipher_dice(weapon)
        result, generated_values = misc.roll_dice(rolls, sides, implication, mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, implication, mod
        )
        await ctx.send(embeds=embed)


def setup(client):
    RollCommands(client)
