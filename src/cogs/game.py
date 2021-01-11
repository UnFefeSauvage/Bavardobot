import discord
from discord.ext import commands

import os
import random
import time
import json
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)


#TODO Un jeu de placement de mots dans des conversations 

class GameCog(commands.Cog):
    def __init__(self, bot, resource_manager):
        logger.info("Initializing Game cog...")
        self.bot = bot
        self.resource_manager = resource_manager
        self.ready_guilds = []
        self.games = {}
        self.configs = {}
        os.listdir()

        logger.debug("Loading words...")
        # Load the words
        self.words = []
        with open("resources/words", 'r') as file:
            line = file.readline()
            while line:
                    self.words.append(line.strip('\n'))
                    line = file.readline()
        
        logger.debug("Loading guild configs...")
        guilds_to_load = os.listdir("resources/guilds")
        guilds_to_load.remove("template")

        for guild_id in guilds_to_load:
            logger.debug(f"Loading guild {guild_id}")
            self.configs[guild_id] = json.loads(resource_manager.read(f"guilds/{guild_id}/guild_config.json"))
            games = json.loads(resource_manager.read(f"guilds/{guild_id}/games.json"))

            self.games[guild_id] = {}

            logger.debug(f"loading games for guild {guild_id}")
            for user_id, game in games.items():
                logger.debug(f"{user_id}: {game}")
                self.games[guild_id][user_id] = game
            
            #TODO initialiser les tasks pour chaque partie
            
            self.ready_guilds.append(guild_id)
            logger.debug(f"Initialised guild {guild_id}")

            

        logger.info("Finished Game cog initialisation!")
    
    #TODO Gérer les timers de partie
    #* https://docs.python.org/3/library/asyncio-task.html#task-object
    
    # Invoquée à chaque commande: s'il renvoie faux, la commande n'est pas lancée
    def cog_check(self, ctx):
        if not (ctx.guild.id in self.ready_guilds):
            return False

        return True
    
    #TODO gestion d'erreur

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild ):
        logger.info(f'Initializing data for guild "{guild.name}" (id: {guild.id})')
        initialised = await self.create_guild_files(guild.id)
        if initialised:
            self.ready_guilds.append(guild.id)
        else:
            logger.info(f'Initialisation failed for guild "{guild.name}" (id: {guild.id})')
            dm = guild.owner.dm_channel()
            if dm is None:
                dm = guild.owner.create_dm()
                dm.send(f"Bonjour! Je viens d'arriver sur {guild.name} et j'ai malheureusement échoué à initialiser le jeu pour le serveur :<\n"
                      + f"Vous pouvez réessayer d'initialiser le jeu en utilisant la commande `=init_game` n'importe où sur le serveur.")

    @commands.Cog.listener()
    async def on_message(self, msg):
        #TODO vérifier si l'auteur joue et a placé son mot
        pass

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        #TODO vérifier que l'auteur ne triche pas (invalider si triche)
        #* https://discordpy.readthedocs.io/en/latest/api.html?highlight=on_message#rawmessageupdateevent
        pass

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        #TODO vérifier que l'auteur ne triche pas (invalider si triche)
        #* https://discordpy.readthedocs.io/en/latest/api.html?highlight=on_message#rawmessagedeleteevent
        pass
    
    
    @commands.command()
    async def jouer(self, ctx):
        logger.debug(f'Starting a game for "{ctx.author}" (id: {ctx.author.id}) on "{ctx.guild}" (id: {ctx.guild.id})')
        #TODO donne un mot à placer en MP (cooldown) et créé le jeu en cours
        pass

    @commands.command()
    async def unmask(self, ctx, *, mot):
        #TODO démasque un joueur sur son mot (cooldown en cas de faux) et résoud le jeu
        pass

    @commands.command()
    async def classement(self, ctx):
        #TODO affiche le classement des joueurs
        pass

    async def create_guild_files(self, guild_id):
        logger.info(f"Creating new game files for guild {guild_id}...")
        path = os.path.normpath( f"{self.resource_manager.path}/guilds/{guild_id}" )
        os.mkdir(path)

        data = self.resource_manager.read("guilds/template/config.json")
        self.resource_manager.write(f"guilds/{guild_id}/config.json", data)

        data = self.resource_manager.read("guilds/template/games.json")
        self.resource_manager.write(f"guilds/{guild_id}/games.json", data)

        return True