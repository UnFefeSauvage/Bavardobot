import discord
from discord.ext import commands

import json
import logging

import resources
import cogs

logging.basicConfig(level=logging.INFO)
#* Pour plus de paramètres:
#* https://discordpy.readthedocs.io/en/latest/logging.html?highlight=logger#setting-up-logging

resource_manager = resources.ResourcesManager("resources")
config = json.loads(resource_manager.read("config.json"))

bot = commands.Bot(command_prefix=config["prefix"])

@bot.event
async def on_ready():
    print("Ready to go!")

if __name__ == "__main__":
    bot.add_cog(cogs.Game(bot,resource_manager))
    bot.run(config["token"])