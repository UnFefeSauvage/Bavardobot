import discord
from discord.ext import commands

#TODO Un jeu de placement de mots dans des conversations 

def create_guild_files(guild_id):
    pass

class Game(commands.Cog):
    def __init__(self, bot, resource_manager):
        self.bot = bot
        self.resource_manager = resource_manager
        #TODO Charger les fichiers nécéssaires
        """
            - Banque de mots
            - Jeux en cours
            - Configuration par serveur
        """
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        #TODO créer le répertoire et les fichiers nécéssaires pour le serveur
        pass

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