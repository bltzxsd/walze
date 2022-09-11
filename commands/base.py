import logging
import string

import interactions
import requests
import validators
from interactions import CommandContext
from lib import json_lib, misc
import os
import sys
import operator
import tabulate
import asyncio

hq = os.getenv('HQ')

class BaseCommands(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="ping",
        description="Get latency.",
    )
    async def ping(self, ctx: CommandContext):
        await ctx.send(
            embeds=misc.quick_embed(
                "Ping",
                f"Can't stop the A-Train, baby! 😈 ({round(self.client.latency)}ms)",
                "ok",
            )
        )

    @interactions.extension_command(name="kill", description="Kill bot.")
    async def kill(self, ctx: CommandContext):
        if ctx.author.id == int(os.getenv("OWNER")):
            await ctx.send("Killing bot.", ephemeral=True)
            await sys.exit(0)
        else:
            return await ctx.send("LMFAOOOOOO", ephemeral=True)

    @interactions.extension_command(
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
    async def sort(self, ctx: CommandContext, names: str, initiatives: str):
        names = names.split()
        initiatives = [int(n) for n in initiatives.split()]
        zipped = list(zip(names, initiatives))
        sorted_list = sorted(zipped, key=operator.itemgetter(1), reverse=True)

        buttons: list[interactions.Button] = [
            misc.to_button(sorted_name[0], interactions.ButtonStyle.SECONDARY)
            for sorted_name in sorted_list
        ]

        end_combat = misc.to_button("Cancel", interactions.ButtonStyle.DANGER)
        buttons.append(end_combat)
        rows = interactions.spread_to_rows(*buttons)

        async def button_auth(button_ctx: interactions.ComponentContext) -> bool:
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

        pretty_print = [[name, initiative] for name, initiative in sorted_list]
        pretty_print = tabulate.tabulate([["Name", "Initiative"], *pretty_print],tablefmt="presto", headers="firstrow")
        await ctx.send(embeds=misc.quick_embed("Ordered Initiative", f"```{pretty_print}```", "ok"), components=rows)

        try: 
            button_ctx = interactions.ComponentContext = await self.client.wait_for_component(
                components=rows, check=button_auth, timeout=10
            )
            interacted = button_ctx.data.custom_id  
            
            if interacted == "Cancel":
                misc.disable(buttons)
                await button_ctx.send(embeds=misc.quick_embed("Closing Order Modification.", "Disabling all buttons.", "ok"), ephemeral=True)
                return await ctx.edit(components=interactions.spread_to_rows(*buttons))
            
            sorted_list = [[name, initiative] for name, initiative in sorted_list if name != interacted]
            for button in buttons: 
                if button.custom_id == interacted:
                    button.disabled = True

            rows = interactions.spread_to_rows(*buttons)
            pretty_print = [[name, initiative] for name, initiative in sorted_list]
            pretty_print = tabulate.tabulate([["Name", "Initiative"], *pretty_print], tablefmt="presto", headers="firstrow")
            await button_ctx.send(embeds=misc.quick_embed("Removed", interacted, "ok"), ephemeral=True)
            await ctx.edit(embeds=misc.quick_embed("Ordered Initiative", f"```{pretty_print}```", "ok"), components=rows)
        except asyncio.TimeoutError:
            misc.disable(buttons)
            return await ctx.edit(components=interactions.spread_to_rows(*buttons))

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
    async def custom(self, ctx: CommandContext, name: str):
        content = await misc.open_stats(ctx.author)
        try:
            parameter = content[str(ctx.author.id)]["custom"][name]
        except:
            return await ctx.send(
                embeds=misc.quick_embed("Error", "No such parameter available!", "error"),
                ephemeral=True,
            )

        rolls, sides, mod = misc.decipher_dice(parameter)
        result, generated_values = misc.roll_dice(rolls=rolls, sides=sides, mod=mod)
        embed = misc.roll_embed(ctx.author, rolls, sides, result, generated_values, mod=mod)
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
        content: dict = await misc.open_stats(ctx.author)
        spell = string.capwords(spell)
        try:
            spellbook = content[str(ctx.author.id)]["spells"]
            spellname: dict = spellbook[spell]
        except:
            return await ctx.send(
                embeds=misc.quick_embed("Error", "No such spell available!", "error"),
                ephemeral=True,
            )

        values = spellname.values()
        embed = misc.create_spell_embed(ctx, spell, *values)

        dice = spellname["Description"]
        dice_syns = misc.find_dice(dice)
        to_button = lambda x: interactions.Button(
            style=interactions.ButtonStyle.SECONDARY, label=x, custom_id=x
        )
        buttons = [to_button(dice) for dice in dice_syns]

        link_button = interactions.Button(
            style=interactions.ButtonStyle.LINK,
            label="Wiki",
            url=f"http://dnd5e.wikidot.com/spell:{spell.lower().replace(' ', '-')}",
        )
        if buttons:
            cancel_button = interactions.Button(
                style=interactions.ButtonStyle.DANGER, label="Cancel", custom_id="cancel"
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
            button_ctx: interactions.ComponentContext = await self.client.wait_for_component(
                components=rows, check=check, timeout=10
            )
            performed = button_ctx.data.custom_id
            if performed == "cancel":
                disable(buttons)
                await button_ctx.send(
                    embeds=misc.quick_embed("Cancelled Roll", "No rolls selected.", "ok"),
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
        except Exception as e:
            logging.warning(e)


def setup(client):
    BaseCommands(client)