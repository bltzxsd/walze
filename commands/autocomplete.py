import interactions
import string
from lib import misc
import logging
from interactions import CommandContext


class AutoComplete(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_autocomplete("attack", "weapon")
    @interactions.extension_autocomplete("modify", "weapon")
    async def weapon_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            weapons = content[str(ctx.author.id)]["weapons"]
        except:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in weapons.keys()
            if string.capwords(value) in param
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("skill", "skill")
    @interactions.extension_autocomplete("modify", "skill")
    async def skill_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            skills = content[str(ctx.author.id)]["stats"]
        except:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in skills.keys()
            if value.capitalize() in param
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("cast", "spell")
    @interactions.extension_autocomplete("modify", "spell")
    async def cast_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            spells = content.get(str(ctx.author.id)).get("spells")
            spells = spells.keys()
        except:
            return

        autocomplete = [
            misc.create_choice(spell)
            for spell in spells
            if string.capwords(value) in spell
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("custom", "custom")
    @interactions.extension_autocomplete("modify", "key")
    async def custom_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            parameters = content.get(str(ctx.author.id)).get("custom")
        except:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in parameters.keys()
            if string.capwords(value) in param
        ]
        await ctx.populate(autocomplete)
    
    @interactions.extension_autocomplete("modify", "char")
    async def m_char_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            params = content.get(str(ctx.author.id))
            params.pop("weapon", None)
            params.pop("stats", None)
            params.pop("custom", None)
        except:
            return

        autocomplete = [
            interactions.Choice(name=string.capwords(param), value=param)
            for param in params.keys()
            if value in param
        ]
        await ctx.populate(autocomplete)


def setup(client):
    AutoComplete(client)
