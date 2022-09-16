import asyncio
import operator

import interactions
import tabulate
from interactions import CommandContext
from lib import constants, misc

scope = constants.config.owner.get("servers", [])


class Unstable(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(
        name="unstable", description="Group for unstable commands", scope=scope
    )
    async def unstable(self, _ctx: CommandContext):
        pass

    @unstable.subcommand(
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
        pretty_print = tabulate.tabulate(
            [["Name", "Initiative"], *pretty_print],
            tablefmt="orgtbl",
            headers="firstrow",
        )
        await ctx.send(
            embeds=misc.quick_embed(
                "Ordered Initiative", f"```{pretty_print}```", "ok"
            ),
            components=rows,
        )

        try:
            button_ctx = (
                interactions.ComponentContext
            ) = await self.client.wait_for_component(
                components=buttons, check=button_auth, timeout=5400
            )
            interacted = button_ctx.data.custom_id

            if interacted == "Cancel":
                misc.disable(buttons)
                await button_ctx.send(
                    embeds=misc.quick_embed(
                        "Closing Order Modification.", "Disabling all buttons.", "ok"
                    ),
                    ephemeral=True,
                )
                return await ctx.edit(components=interactions.spread_to_rows(*buttons))

            sorted_list = [
                [name, initiative]
                for name, initiative in sorted_list
                if name != interacted
            ]
            for button in buttons:
                if button.custom_id == interacted:
                    button.disabled = True

            rows = interactions.spread_to_rows(*buttons)
            pretty_print = [[name, initiative] for name, initiative in sorted_list]
            pretty_print = tabulate.tabulate(
                [["Name", "Initiative"], *pretty_print],
                tablefmt="orgtbl",
                headers="firstrow",
            )
            await button_ctx.send(
                embeds=misc.quick_embed("Removed", interacted, "ok"), ephemeral=True
            )
            await ctx.edit(
                embeds=misc.quick_embed(
                    "Ordered Initiative", f"```{pretty_print}```", "ok"
                ),
                components=rows,
            )
        except asyncio.TimeoutError:
            misc.disable(buttons)
            return await ctx.edit(components=interactions.spread_to_rows(*buttons))


def setup(client):
    Unstable(client)
