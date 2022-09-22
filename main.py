import logging

import interactions
from interactions.ext import wait_for

from lib import constants

synced: bool = False
discord_token = constants.CONFIG.tokens.get("discord", "")
constants.CONFIG.set_logs()

bot = interactions.Client(
    token=discord_token, intents=interactions.Intents.DEFAULT
)

bot.load("interactions.ext.files")
wait_for.setup(bot)


@bot.event
async def on_ready():
    # just in case i need to do something on start
    if not synced:
        pass

    logging.info(f"Logged in as {bot.me.name}")


@bot.event
async def on_command(ctx: interactions.CommandContext):
    logging.info(
        f"Command: {ctx.data.name} by {ctx.author} in guild {ctx.guild_id}:#{ctx.channel}"
    )


bot.load("commands.base")
bot.load("commands.rolls")
bot.load("commands.modify")
bot.load("commands.unstable")
bot.load("commands.autocomplete")
bot.start()
