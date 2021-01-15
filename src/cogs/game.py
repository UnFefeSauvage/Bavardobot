import discord
from discord.ext import commands

import os
import random
import time
import json
import logging
import asyncio

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
        self.tasks = {}
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
            
            self.ready_guilds.append(int(guild_id))
            logger.debug(f"Initialised guild {guild_id}")

            

        logger.info("Finished Game cog initialisation!")
    
    @commands.Cog.listener()
    async def on_ready(self):
        #* Création des coroutines d'attente d'expiration des parties
        self.tasks = {}
        for guild_id, games in self.games.items():
            self.tasks[guild_id] = {}
            for user_id, game in games.items():
                logger.debug(f"Creating task for game {user_id} in guild {guild_id}")
                if not game["placed"]:
                    self.tasks[guild_id][user_id] = asyncio.create_task(self.wait_until_game_expires(guild_id, game))
                else:
                    #TODO Créer une tâche: attendre la validation de la partie
                    pass


    #TODO Gérer les timers de partie
    #* https://docs.python.org/3/library/asyncio-task.html#task-object
    
    # Invoquée à chaque commande: s'il renvoie faux, la commande n'est pas lancée
    def cog_check(self, ctx):
        if not (ctx.guild.id in self.ready_guilds):
            return False

        return True
    
    #TODO gestion d'erreur

    #*-*-*-*-*-*-*-*-*#
    #*-*-LISTENERS-*-*#
    #*-*-*-*-*-*-*-*-*#

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild ):
        logger.info(f'Initializing data for guild "{guild.name}" (id: {guild.id})')
        initialised = await self.create_guild_files(guild.id)
        if initialised:
            self.ready_guilds.append(guild.id)
        else:
            dm = guild.owner.dm_channel()
            if dm is None:
                dm = guild.owner.create_dm()
                dm.send(f"Bonjour! Je viens d'arriver sur {guild.name} et j'ai malheureusement échoué à initialiser le jeu pour le serveur :<\n"
                      + f"Vous pouvez réessayer d'initialiser le jeu en utilisant la commande `=init_game` n'importe où sur le serveur.")

    @commands.Cog.listener()
    async def on_message(self, msg):
        #Si l'auteur a une partie en cours sur le serveur
        if str(msg.author.id) in self.games[str(msg.guild.id)]:
            game = self.games[str(msg.guild.id)][str(msg.author.id)]
            # ... et si son mot n'a pas encore été placé:
            #FIXME Autoriser n'importe quelle casse
            if (not game["placed"]) and (game["word"] in msg.content):
                #TODO Valider le placement et passer le jeu en phase 2
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
    
    #*-*-*-*-*-*-*-*-*#
    #*-*-COMMANDS--*-*#
    #*-*-*-*-*-*-*-*-*#
    
    @commands.command()
    async def jouer(self, ctx):
        """Démarre une partie et te donne un mot à placer en MP"""
        if self.has_running_game(ctx.author):
            # Renvoie les détails de sa partie à l'auteur
            dm = ctx.author.dm_channel
            if dm is None:
                dm = await ctx.author.create_dm()
            game_embed = self.get_game_info_embed(ctx.author)
            await dm.send(embed=game_embed)
            await ctx.send("Tu as déjà une partie en cours, je te renvoie les détails!")
            return

        #else
        logger.debug(f'Starting a game for "{ctx.author}" (id: {ctx.author.id}) on "{ctx.guild}" (id: {ctx.guild.id})')
        # donne un mot à placer en MP (cooldown) et créé le jeu en cours
        game = self.new_game(ctx.author.id)
        self.games[str(ctx.guild.id)][str(ctx.author.id)] = game
        self.resource_manager.write(f"guilds/{ctx.guild.id}/games.json", json.dumps(self.games[str(ctx.guild.id)], indent=4))
        asyncio.create_task(self.wait_until_game_expires(ctx.guild.id, game))
        dm = ctx.author.dm_channel
        if dm is None:
            dm = await ctx.author.create_dm()
        game_embed = self.get_game_info_embed(ctx.author)
        await dm.send(embed=game_embed)
        await ctx.send("Partie créée! Je t'ai envoyé les détails!")


    @commands.command()
    async def unmask(self, ctx, *, mot):
        """unmask [lien] [mot]  Te permet de démasquer un mot dans le message de quelqu'un"""
        #TODO démasque un joueur sur son mot (cooldown en cas de faux) et résoud le jeu
        #TODO tester si le message répond à un autre (type 19)
        #* https://discord.com/developers/docs/resources/channel#message-object-message-structure
        pass

    @commands.command()
    async def classement(self, ctx):
        """Affiche le classement des joueurs du serveur"""
        #TODO affiche le classement des joueurs
        pass

    #*-*-*-*-*-*-*#
    #*-*-TASKS-*-*#
    #*-*-*-*-*-*-*#

    async def wait_until_game_expires(self, guild_id, game):
        duration = self.configs[str(guild_id)]["write_timer"]
        start = game["time"]
        now = int(time.time())
        wait_time = duration - (now - start)
        if wait_time > 0:
            try:
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.debug(f"Game of user {game['user_id']} in guild {guild_id} has been cancelled" % ())
                return
        
        #else
        logger.debug(f"Game of user {game['user_id']} in guild {guild_id} has expired, deleting...")
        #TODO Inform user that his game has expired (and he can create a new one)
        del self.games[str(guild_id)][str(game["user_id"])]
        self.resource_manager.write(f"guilds/{guild_id}/games.json", json.dumps(self.games[str(guild_id)], indent=4) )

    #*-*-*-*-*-*-*-*-*#
    #*-*-UTILITIES-*-*#
    #*-*-*-*-*-*-*-*-*#

    def has_running_game(self, member):
        if str(member.id) in self.games[str(member.guild.id)]:
            return True
        else:
            return False
    

    def get_game_info_embed(self, member):
        game = self.games[str(member.guild.id)][str(member.id)]
        timer = self.configs[str(member.guild.id)]["write_timer"] - (int(time.time()) - game["time"])
        hours = timer // 3600 
        remaining_time = "%sh %smin %ss" % (timer//3600, (timer%3600)//60, (timer%60))
        embed = discord.Embed(title="Détails de ta partie:", color=member.color).add_field(name="Mot à placer", value=game["word"]).add_field(name="Temps restant", value=remaining_time)
        return embed
        

    async def create_guild_files(self, guild_id):
        logger.info(f"Creating new game files for guild {guild_id}...")
        path = os.path.normpath( f"{self.resource_manager.path}/guilds/{guild_id}" )
        try:
            os.mkdir(path)

            data = self.resource_manager.read("guilds/template/guild_config.json")
            self.resource_manager.write(f"guilds/{guild_id}/config.json", data)

            data = self.resource_manager.read("guilds/template/games.json")
            self.resource_manager.write(f"guilds/{guild_id}/games.json", data)
        except:
            logger.warning(f"Initialisation failed for guild {guild_id}")
            return False

        return True
    
    def new_game(self, user_id):
        now = int(time.time())
        return {
            "user_id": user_id,
            "time": now,
            "word": self.words[random.randint(0, len(self.words))],
            "placed": False,
            "msg_link": False,
            "msg_content": False,
            "msg_id": False
        }
