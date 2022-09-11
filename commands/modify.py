import logging
import string

import interactions
import requests
import validators
from interactions import CommandContext
from lib import json_lib, misc


class ModifyAttributes(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(name="modify", description="Modify a a value.")
    async def modify(self, ctx: CommandContext):
        pass

    @modify.subcommand(
        name="weapon",
        description="Modify weapon parameters.",
        options=[
            interactions.Option(
                name="weapon",
                description="Name of the weapon to modify Eg: `Longsword`, `Shortbow`",
                type=interactions.OptionType.STRING,
                required=True,
                autocomplete=True,
            ),
            interactions.Option(
                name="hit",
                description="Value of the weapon (hit) to modify, Eg: `1d20+2`, `1d20-4`.",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="dmg",
                description="Value of the weapon (dmg) to modify, Eg: `1d8+2`, `2d6`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="attribute",
                description="Value of the attribute of the weapon Eg: `2d6`, `1d6`",
                type=interactions.OptionType.STRING,
                required=False,
            ),
        ],
    )
    async def modify_weapon(
        self,
        ctx: CommandContext,
        weapon: str,
        hit: str,
        dmg: str,
        attribute: str = "",
    ):
        try:
            misc.decipher_all([hit, dmg])
            if attribute:
                misc.decipher_dice(attribute)
        except ValueError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "A value here does not fit the roll syntax!", "error"
                ),
                ephemeral=True,
            )
        value = {"hit": hit, "dmg": dmg, "attribute": attribute}

        output, reply, color = await json_lib.modify_param(
            ctx, access="weapons", key=string.capwords(weapon), value=value
        )
        await ctx.send(
            embeds=misc.quick_embed(output, f"```{reply}```", color), ephemeral=True
        )

    @modify.subcommand(
        name="char",
        description="Modifies character parameters.",
        options=[
            interactions.Option(
                name="char",
                description="Key to modify. Eg: `Name`, `Initiative`",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
            ),
            interactions.Option(
                name="value",
                description="Value to modify. Eg: `1`, `2`, `1d8+4`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
        ],
    )
    async def modify_char(self, ctx: CommandContext, key: str, value: str):
        output, reply, color = await json_lib.modify_param(
            ctx, access="char", key=key, value=value
        )
        await ctx.send(
            embeds=misc.quick_embed(output, f"```{reply}```", color), ephemeral=True
        )

    @modify.subcommand(
        name="custom",
        description="Modify custom rolls.",
        options=[
            interactions.Option(
                name="key",
                description="Key to modify. Eg: `Wis Save`, `Int Save`",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
            ),
            interactions.Option(
                name="value",
                description="Value to modify. Eg: `1d20+4`, `1d4+5`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
        ],
    )
    async def modify_custom(self, ctx: CommandContext, key: str, value: str):
        try:
            misc.decipher_dice(value)
        except Exception as e:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error",
                    f"Not a valid dice roll: {value}\nOnly valid dice syntax is allowed\n{e}",
                    "error",
                ),
                ephemeral=True,
            )
        output, reply, color = await json_lib.modify_param(
            ctx, access="custom", key=string.capwords(key), value=value
        )
        await ctx.send(
            embeds=misc.quick_embed(output, f"```{reply}```", color), ephemeral=True
        )

    @modify.subcommand(
        name="spell",
        description="Modify prepared spells in your spellbook.",
        options=[
            interactions.Option(
                name="spell",
                description="Name of the spell you want to modify. Eg: `Bless`, `Bane`",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
            ),
            interactions.Option(
                name="description",
                description="Description of the spell. (pastebin links are allowed)",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="level",
                description="Level of the spell.",
                type=interactions.OptionType.STRING,
                choices=misc.Choices().from_list(
                    [
                        "Cantrip",
                        "1st",
                        "2nd",
                        "3rd",
                        "4th",
                        "5th",
                        "6th",
                        "7th",
                        "8th",
                        "9th",
                    ]
                ),
                required=True,
            ),
            interactions.Option(
                name="school",
                description="School of the spell.",
                type=interactions.OptionType.STRING,
                choices=misc.Choices().from_list(
                    [
                        "Abjuration",
                        "Conjuration",
                        "Divination",
                        "Enchantment",
                        "Evocation",
                        "Illusion",
                        "Necromancy",
                        "Transmutation",
                    ]
                ),
                required=True,
            ),
            interactions.Option(
                name="casting_time",
                description="Time taken to cast the spell. Eg: `1 action`, `1 reaction`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="range",
                description="Range of the spell. Eg: `120 ft`, `Touch`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="components",
                description="Components needed for the spell. Eg: `V`, `S`, `M: 100gp`, `V, S, M`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="duration",
                description="How long the spell lasts. Eg: `Concentration, upto 1 minutes`, `Instantaneous`",
                type=interactions.OptionType.STRING,
                required=True,
            ),
            interactions.Option(
                name="saving_throw",
                description="Saving throw for the spell. (if it has any)",
                type=interactions.OptionType.STRING,
                required=False,
            ),
            interactions.Option(
                name="source",
                description="Source of the spell. Eg: `PHB 74`, `TCoE 110`, `MotM`, `XGtE`",
                type=interactions.OptionType.STRING,
                required=False,
            ),
        ],
    )
    async def modify_spells(
        self,
        ctx: CommandContext,
        spell: str,
        description: str,
        level: str,
        school: str,
        casting_time: str,
        range: str,
        components: str,
        duration: str,
        saving_throw: str = "",
        source: str = "",
    ):
        if validators.url(description):
            description = requests.get(description).text
        spell = string.capwords(spell)

        spell_attr = {
            "Description": description,
            "Level": level,
            "School": school,
            "Casting Time": casting_time,
            "Range": range,
            "Components": components,
            "Duration": duration,
            "Saving Throw": saving_throw,
            "Source": source,
        }
        title, _, color = await json_lib.modify_param(
            ctx, access="spells", key=spell, value=spell_attr
        )

        embeds = misc.create_spell_embed(
            ctx,
            spell,
            description,
            level,
            school,
            casting_time,
            range,
            components,
            duration,
            saving_throw,
            source,
        )
        embeds.insert(0, misc.quick_embed(title, "", color))
        await ctx.send(embeds=embeds, ephemeral=True)

    @modify.subcommand(
        name="skill",
        description="Modifies skill parameters.",
        options=[
            interactions.Option(
                name="skill",
                description="Skill to modify. Eg. `Acrobatics`, `Deception`",
                type=interactions.OptionType.STRING,
                autocomplete=True,
                required=True,
            ),
            interactions.Option(
                name="value",
                description="Value to modify. Eg. `1`, `2`, `4`, `8`.",
                type=interactions.OptionType.INTEGER,
                required=True,
            ),
        ],
    )
    async def modify_skill(self, ctx: CommandContext, skill: str, value: int):

        output, reply, color = await json_lib.modify_param(
            ctx, access="skills", key=string.capwords(skill), value=value
        )
        await ctx.send(
            embeds=misc.quick_embed(output, f"```{reply}```", color), ephemeral=True
        )


def setup(client):
    ModifyAttributes(client)
