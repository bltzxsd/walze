import interactions
from interactions import CommandContext
from lib import constants, misc


class AutoComplete(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_autocomplete("attack", "weapon")
    @interactions.extension_autocomplete("modify", "weapon")
    async def weapon_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            weapons: dict = content.get(str(ctx.author.id)).get("weapons")
        except KeyError:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in weapons.keys()
            if value.lower() in param.lower()
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("skill", "skill")
    @interactions.extension_autocomplete("modify", "skill")
    async def skill_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            skills = content.get(str(ctx.author.id)).get("stats")
        except KeyError:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in skills.keys()
            if value.lower() in param.lower()
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("cast", "spell")
    async def cast_autocomplete(self, ctx: CommandContext, value: str = ""):
        autocomplete = [
            misc.create_choice(spellname, url)
            for spellname, url in constants.SPELL_LIST
            if spellname.lower().startswith(value.lower())
        ][:25]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("custom", "custom")
    @interactions.extension_autocomplete("modify", "key")
    async def custom_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            parameters = content.get(str(ctx.author.id)).get("custom")
        except KeyError:
            return
        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in parameters.keys()
            if value.lower() in param.lower()
        ]
        await ctx.populate(autocomplete)

    @interactions.extension_autocomplete("modify", "char")
    async def char_autocomplete(self, ctx: CommandContext, value: str = ""):
        content = await misc.open_stats(ctx.author)
        try:
            params = content.get(str(ctx.author.id))
            # we don't want these to be modified
            params.pop("weapons", None)
            params.pop("stats", None)
            params.pop("custom", None)
            params.pop("spells", None)
            params.pop("features", None)
        except KeyError:
            return

        autocomplete = [
            interactions.Choice(name=param, value=param)
            for param in params.keys()
            if value.lower() in param.lower()
        ]
        await ctx.populate(autocomplete)


def setup(client):
    AutoComplete(client)
