import io
import json
import operator
import re

import interactions
import tabulate
from interactions import CommandContext
from lib import constants, misc

scope = constants.CONFIG.scope


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

    @interactions.extension_command(
        name="kill", description="Kill bot.", scope=scope
    )
    async def kill(self, ctx: CommandContext):
        if int(ctx.author.id) == constants.CONFIG.owner.get("id", 0):
            await ctx.send(
                embeds=misc.quick_embed(
                    "Terminating", "Terminating bot.", "ok"
                ),
                ephemeral=True,
            )
            raise KeyboardInterrupt
        else:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Lacking privilege.", "Not a bot administrator.", "error"
                ),
                ephemeral=True,
            )

    @interactions.extension_command(
        name="sort",
        description="Sorts entities by their values.",
        options=[
            interactions.Option(
                name="entities",
                description="Entities and their values. Eg: `Entity4:18 Entity3:17 Entity2:14 Entity1:9`.",
                type=interactions.OptionType.STRING,
                required=True,
            )
        ],
    )
    async def sort(self, ctx: CommandContext, entities: str):
        entities = re.findall(constants.ENTITIES_SYNTAX, entities)
        entities: list = [entity.split(":") for entity in entities]

        for item in entities:
            try:
                item[1] = int(item[1])
            except ValueError:
                item[1] = None

        entities = list(
            filter(lambda e: e[0] != "" and e[1] is not None, entities)
        )
        entities.sort(key=operator.itemgetter(1), reverse=True)

        pretty_print = [[name, initiative] for name, initiative in entities]
        pretty_print = tabulate.tabulate(
            [["Name", "Initiative"], *pretty_print],
            tablefmt="orgtbl",
            headers="firstrow",
        )
        await ctx.send(
            embeds=misc.quick_embed(
                "Ordered Initiative", f"```{pretty_print}```", "ok"
            )
        )

    @interactions.extension_command(
        name="retrieve",
        description="Shows all saved parameters for your character.",
        options=[
            interactions.Option(
                name="ephemeral",
                description="Whether the reply should be visible only to the user.",
                type=interactions.OptionType.BOOLEAN,
            ),
        ],
    )
    async def retrieve(self, ctx: CommandContext, ephemeral: bool = False):
        try:
            retrieved = await misc.open_stats(ctx.author)
            retrieved = retrieved.get(str(ctx.author.id))
        except KeyError as error:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Error", "You do not have any saved parameters!\n%s" %error, "error"
                ),
                ephemeral=True,
            )
        retrieved = json.dumps(retrieved, indent=2)

        if len(retrieved) > 1024:
            file = io.StringIO(retrieved)
            files = interactions.File(
                filename=f"{misc.author_name(ctx.author)}_stats.json", fp=file
            )
            embed = misc.quick_embed(
                f"{ctx.author.name}'s Parameters", "", "ok"
            )
            embed.set_author(
                name=misc.author_name(ctx.author),
                icon_url=misc.author_url(ctx.author),
            )
            embed.set_footer("Length: " + str(len(retrieved)))
            return await ctx.send(
                embeds=embed,
                files=files,
                ephemeral=ephemeral,
            )

        embed = misc.quick_embed("Saved Parameters", f"```{retrieved}```", "ok")
        embed.set_author(
            name=misc.author_name(ctx.author),
            icon_url=misc.author_url(ctx.author),
        )
        embed.set_footer("Length: " + str(len(retrieved)))
        await ctx.send(
            embeds=embed,
            ephemeral=ephemeral,
        )

    @interactions.extension_command(
        name="backup",
        description="Send all saved parameters to the channel.",
        scope=constants.CONFIG.scope,
        options=[
            interactions.Option(
                name="ephemeral",
                description="Whether the reply should be visible only to the user.",
                type=interactions.OptionType.BOOLEAN,
                required=False,
            )
        ],
    )
    async def backup(self, ctx: CommandContext, ephemeral: bool = False):
        try:
            owner = constants.CONFIG.owner_id
            assert owner != 0
        except AssertionError:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "No owner set.",
                    "Owner ID was not set in `Config.toml`",
                    "error",
                ),
                ephemeral=True,
            )

        if int(ctx.author.id) != owner:
            return await ctx.send(
                embeds=misc.quick_embed(
                    "Insufficient privileges.", "Not Owner.", "error"
                ),
                ephemeral=True,
            )

        file = constants.SHEETS.read()
        file = io.StringIO(file)
        files = interactions.File(filename="sheets.json", fp=file)
        await ctx.send(files=files, ephemeral=ephemeral)


def setup(client):
    BaseCommands(client)
