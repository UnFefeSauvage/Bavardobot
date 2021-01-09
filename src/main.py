import discord
from discord.ext import commands

import json

import resources
import cogs

resource_manager = resources.ResourcesManager("resources")
config = json.loads(resource_manager.read("config.json"))

bot = commands.Bot(command_prefix=config["prefix"])

@bot.event
async def on_ready():
    print("Ready to go!")

if __name__ == "__main__":
    bot.run(config["token"])