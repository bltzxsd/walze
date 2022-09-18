import string

import interactions
from interactions import CommandContext
from lib import json_lib, misc
from lib.misc import user_check


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
        if await user_check(ctx):
            return
        try:
            dmg = int(dmg) - 1
            op = "+" if dmg >= 0 else ""
            dmg = "1d1" + op + str(dmg)
        except:
            pass

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
    async def modify_char(self, ctx: CommandContext, char: str, value: str):
        if await user_check(ctx):
            return
        output, reply, color = await json_lib.modify_param(
            ctx, access="char", key=char, value=value
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
        if await user_check(ctx):
            return
        try:
            misc.decipher_dice(value)
        except ValueError as error:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error",
                    f"Not a valid dice roll: {value}\nOnly valid dice syntax is allowed\n{error}",
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
        if await user_check(ctx):
            return
        output, reply, color = await json_lib.modify_param(
            ctx, access="skills", key=string.capwords(skill), value=value
        )
        await ctx.send(
            embeds=misc.quick_embed(output, f"```{reply}```", color), ephemeral=True
        )

    @interactions.extension_command(
        name="save",
        description="Saves a key value pair.",
    )
    async def save(self, _ctx: interactions.CommandContext):
        pass

    @save.subcommand(
        name="skills",
        description="Saves initial skills.",
        options=[
            interactions.Option(
                name="attributes",
                description="Save all skills at once in alphabetical order. Eg: `1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18`",
                type=interactions.OptionType.STRING,
                required=True,
            )
        ],
    )
    async def save_skills(self, ctx: interactions.CommandContext, attributes: str):
        if await user_check(ctx):
            return
        title, desc, outcome = await json_lib.write_stats(ctx.author, attributes)
        await ctx.send(embeds=misc.quick_embed(title, desc, outcome), ephemeral=True)


def setup(client):
    ModifyAttributes(client)
