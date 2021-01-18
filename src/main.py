# -*- coding: UTF-8 -*-
import discord
from discord.ext import commands

import json
import logging

import resources
import cogs

root = logging.getLogger()
root.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)
#* Pour plus de paramètres:
#* https://discordpy.readthedocs.io/en/latest/logging.html?highlight=logger#setting-up-logging

resource_manager = resources.ResourcesManager("resources")
config = json.loads(resource_manager.read("config.json"))

#Ce que le bot a l'intention d'utiliser
bot_intents = discord.Intents(
    messages=True,
    members=True,
    guilds=True,
    dm_messages=True
)

bot = commands.Bot(command_prefix=config["prefix"], intents=bot_intents)

@bot.event
async def on_ready():
    print("Ready to go!")

if __name__ == "__main__":
    bot.add_cog(cogs.GameCog(bot,resource_manager))
    bot.run(config["token"])