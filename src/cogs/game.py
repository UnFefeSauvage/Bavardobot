import discord
from discord.ext import commands

import os

#TODO Un jeu de placement de mots dans des conversations 

class Game(commands.Cog):
    def __init__(self, bot, resource_manager):
        self.bot = bot
        self.resource_manager = resource_manager

        self.ready_guilds = []
        self.games = {}
        os.listdir()

        logging.debug("Loading words...")
        # Load the words
        with open("resources/words", 'r') as file:
            line = file.readline()
            while line:
                    words.append(line.strip('\n'))
                    line = file.readline()
        
        logging.debug("Loading guild configs...")
        guilds_to_load = []
        
        #TODO Charger les fichiers nécéssaires
        """
            - Banque de mots
            - Jeux en cours
            - Configuration par serveur
        """
    
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
        #TODO créer le répertoire et les fichiers nécéssaires pour le serveur
        initialised = await self.create_guild_files(guild.id)
        if initialised:
            self.ready_guilds.append(guild.id)
        else:
            #TODO Annonce on a channel that the game initialisation failed (You should do it manually)

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
        path = os.path.normpath( f"{self.resource_manager.path}/guilds/{guild_id}" )
        os.mkdir(path)

        data = self.resource_manager.read("guilds/template/config.json")
        self.resource_manager.write(f"guilds/{guild_id}/config.json", data)

        data = self.resource_manager.read("guilds/template/games.json")
        self.resource_manager.write(f"guilds/{guild_id}/games.json", data)

        return True