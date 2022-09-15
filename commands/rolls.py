import asyncio
import os
import string

import interactions
from interactions import CommandContext
from lib import misc
from lib.misc import user_check

hq = os.getenv("HQ")


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
            )
        ],
    )
    async def custom(self, ctx: CommandContext, custom: str):
        if await user_check(ctx):
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
        result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, mod=mod
        )
        await ctx.send(embeds=embed)

    @interactions.extension_command(
        name="cast",
        description="Cast spells from your spellbook.",
        scope=hq,
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
        if await user_check(ctx):
            return
        content: dict = await misc.open_stats(ctx.author)
        spell = string.capwords(spell)
        try:
            spellbook = content.get(str(ctx.author.id)).get("spells")
            spellname: dict = spellbook[spell]
        except KeyError:
            return await ctx.send(
                embeds=misc.quick_embed("Error", "No such spell available!", "error"),
                ephemeral=True,
            )

        embed = misc.create_spell_embed_unstable(ctx, spell, spellname)

        dice = spellname.get("Description")
        dice: str = dice + spellname.get("At Higher Levels")
        dice_syns = misc.find_dice(dice)

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
                    components=rows, check=check, timeout=10
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
        if await user_check(ctx):
            return
        content = await misc.open_stats(ctx.author)
        init = content.get(str(ctx.author.id)).get("Initiative")
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
        await ctx.send(embeds=embed)

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
            )
        ],
    )
    async def skill(self, ctx: interactions.CommandContext, skill: str):
        if await user_check(ctx):
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
        result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, mod=mod
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
        self, ctx: interactions.CommandContext, weapon: str, implication: str
    ):
        if await user_check(ctx):
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
        match implication:
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
        result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
        embed = misc.roll_embed(
            ctx.author, rolls, sides, result, generated_values, mod=mod
        )
        await ctx.send(embeds=embed)


def setup(client):
    RollCommands(client)
