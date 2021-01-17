import discord
from discord.ext import commands, tasks

import os
import random
import time
import json
import logging
import asyncio
import operator

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler.setFormatter(logFormatter)
logger.addHandler(handler)


#Tags des types de données de guildes
GAMES = "games"
CONFIG = "config"
SCORES = "scores"

#Un jeu de placement de mots dans des conversations 

class GameCog(commands.Cog):
    """Un ensemble de commandes et évènements créant un jeu de placement de mots dans des conversations"""
    def __init__(self, bot, resource_manager):
        logger.info("Initializing Game cog...")
        self.bot = bot
        self.resource_manager = resource_manager
        self.ready_guilds = []
        self.games = {}
        self.tasks = {}
        self.configs = {}
        self.scores = {}
        self._is_modified = {}
        self.msg_cache = {}

        logger.debug("Loading words...")

        #Chargement des mots
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

            #Config
            self.configs[guild_id] = json.loads(resource_manager.read(f"guilds/{guild_id}/guild_config.json"))
            
            #Games
            self.games[guild_id] = json.loads(resource_manager.read(f"guilds/{guild_id}/games.json"))

            #Scores 
            self.scores[guild_id] = json.loads(resource_manager.read(f"guilds/{guild_id}/scores.json"))

            #Modification flags
            self._is_modified[guild_id] = {GAMES: False, CONFIG: False, SCORES: False}

            
            self.ready_guilds.append(int(guild_id))
            logger.debug(f"Initialised guild {guild_id}")

        #Démarrage de la boucle de sauvegarde
        self.save_modified_files.start()
        logger.info("Finished Game cog initialisation!")
    
    #Invoquée après la connection du bot
    @commands.Cog.listener()
    async def on_ready(self):
        #Mise en cache des messages de placement des mots
        for guild_id, games in self.games.items():
            self.msg_cache[guild_id] = {}
            guild = self.bot.get_guild(int(guild_id))
            for user_id, game in games.items():
                if game["placed"]:
                    channel_id = str(game["msg_link"][1])
                    message_id = str(game["msg_link"][2])
                    
                    if not (channel_id in self.msg_cache[guild_id].keys()):
                        self.msg_cache[guild_id][channel_id] = {}
                    
                    channel = guild.get_channel(int(channel_id))
                    try:
                        self.msg_cache[guild_id][channel_id][message_id] = await channel.fetch_message(int(message_id))
                    except discord.errors.NotFound:
                        #FIXME En cas de reconnexion, si la partie est déjà gagnée, elle sera annulée quand même
                        #Invalider la partie pour cause de message supprimé
                        self.cancel_win(guild_id, user_id)

                        player = guild.get_member(int(user_id))
                        game_embed = self.get_game_info_embed(player)
                        if player is None:
                            pass
                        else:
                            dm = player.dm_channel
                            if dm is None:
                                dm = await player.create_dm()
                            #! Si la création de dm échoue, on_ready s'arrête, ce qui est une erreur critique pour le fonctionnement du jeu
                            await dm.send(f"Le message où tu as placé ton mot a été supprimé! Ta partie a été invalidée!", embed=game_embed)
                    else:
                        #TODO Vérifier la potentielle modification du message
                        pass

        #Création des coroutines d'attente d'expiration des parties
        self.tasks = {}
        for guild_id, games in self.games.items():
            self.tasks[guild_id] = {}
            for user_id, game in games.items():
                logger.debug(f"Creating task for game {user_id} in guild {guild_id}")
                if not game["placed"]:
                    self.tasks[guild_id][user_id] = asyncio.create_task(self.wait_until_game_expires(guild_id, game))
                else:
                    self.tasks[guild_id][user_id] = asyncio.create_task(self.wait_for_victory(guild_id, game))

    
    # Invoquée à chaque commande: s'il renvoie faux, la commande n'est pas lancée
    def cog_check(self, ctx):
        if not (ctx.guild.id in self.ready_guilds):
            return False

        return True
    
    async def close(self):
        #TODO Save all files
        pass
    
    #TODO gestion d'erreur

    #*-*-*-*-*-*-*-*-*#
    #*-*-LISTENERS-*-*#
    #*-*-*-*-*-*-*-*-*#

    @commands.Cog.listener()
    async def on_guild_join(self, guild : discord.Guild ):
        logger.info(f'Initializing data for guild "{guild.name}" (id: {guild.id})')
        initialised = await self.create_guild_files(guild.id)
        if initialised:
            self._is_modified[str(guild.id)] = {GAMES: False, CONFIG: False, SCORES: False}
            self.msg_cache[str(guild.id)] = {}
            self.ready_guilds.append(guild.id)
        else:
            dm = guild.owner.dm_channel
            if dm is None:
                dm = await guild.owner.create_dm()

            await dm.send(f"Bonjour! Je viens d'arriver sur {guild.name} et j'ai malheureusement échoué à initialiser le jeu pour le serveur :<\n"
                    + f"Vous pouvez réessayer d'initialiser le jeu en utilisant la commande `=init_game` n'importe où sur le serveur.")

    @commands.Cog.listener()
    async def on_message(self, msg):
        #Si l'auteur est un bot, ignorer
        if msg.author.bot:
            return
        
        guild_id = str(msg.guild.id)
        channel_id = str(msg.channel.id)
        message_id = str(msg.id)
        author_id = str(msg.author.id)
        #Si l'auteur a une partie en cours sur le serveur
        if self.has_running_game(msg.author):
            game = self.games[guild_id][author_id]
            # ... et si son mot n'a pas encore été placé:
            if (not game["placed"]) and (game["word"].lower() in msg.content.lower()):
                #Valider le placement et mettre à jour la partie
                game["placed"] = True
                game["msg_link"] = [msg.guild.id, msg.channel.id, msg.id]
                game["msg_content"] = msg.content
                game["msg_id"] = msg.id
                game["time_placed"] = int(time.time())
                self.games[guild_id][author_id] = game
                self.tag_as_modified(msg.guild.id, GAMES)

                #Stockage du message en cache
                if not channel_id in self.msg_cache[guild_id]:
                    self.msg_cache[guild_id][channel_id] = {}
                
                self.msg_cache[guild_id][channel_id][message_id] = msg

                #Passage de la partie en phase 2
                self.tasks[guild_id][author_id].cancel()
                self.tasks[guild_id][author_id] = asyncio.create_task(self.wait_for_victory(msg.guild.id, game))

                #Informer le joueur
                dm = msg.author.dm_channel
                if dm is None:
                    dm = await msg.author.create_dm()

                game_embed = self.get_game_info_embed(msg.author)
                await dm.send("Bravo! Tu as placé ton mot! Ta partie passe en phase 2:", embed=game_embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        #* Détails du payload:
        #* https://discordpy.readthedocs.io/en/latest/api.html?highlight=on_message#rawmessageupdateevent
        required_data =["author", "content", "guild_id","id"]
        has_data = True
        for key in required_data:
            if not (key in payload.data.keys()):
                has_data = False
                break
        
        if has_data:
            author_id = payload.data["author"]["id"]
            content = payload.data["content"]
            guild_id = payload.data["guild_id"]
            message_id = payload.data["id"]
        else:
            if "guild_id" in payload.data.keys():
                guild_id = payload.data["guild_id"]
            else:
                logger.debug("on_raw_message_edit did not get the guild_id of the message: assuming it is not in a guild")
                return
            
            guild = self.bot.get_guild(int(guild_id))
            channel = guild.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            #S'il s'agit d'un message système, l'ignorer
            if msg.type != discord.MessageType.default:
                logger.debug("on_raw_message_edit: update is a system update, ignoring")
                return
            else:
                author_id = str(msg.author.id)
                content = msg.content
                guild_id = str(msg.guild.id)
                message_id = str(msg.id)

        logger.debug(f"author_id: {author_id}, guild_id: {guild_id}, msg_id: {message_id}, content: {content}")

        #Si le serveur n'est pas initialisé, quitter
        if not (int(guild_id) in self.ready_guilds):
            logger.debug("Exiting on_raw_message_edit: guild not in ready_guilds")
            return
        #Sinon...
        #Si l'auteur n'a pas de partie en cours, quitter
        if not (author_id in self.games[guild_id]):
            logger.debug("Exiting on_raw_message_edit: user doesn't have a running game")
            return
        #Sinon...
        game = self.games[guild_id][author_id]

        #Si le joueur n'a pas encore placé son mot, quitter
        if not game["placed"]:
            logger.debug("Exiting on_raw_message_edit: word is not yet placed")
            return

        #if the message is not the winning message, quit
        if not (str(game["msg_id"]) == message_id):
            logger.debug("Exiting on_raw_message_edit: the message isn't a winning one")
            return
        
        #Si le mot a disparu du message, l'invalider
        if not (game["word"] in content):
            self.games[guild_id][author_id]["placed"] = False
            self.tag_as_modified(guild_id, GAMES)

            #Arrêt du timer de partie
            logger.debug(f"Stopping game of {author_id} in {guild_id} for hiding his word.")
            self.tasks[guild_id][author_id].cancel()

            #Relancer la phase de placement de la partie
            game = self.games[guild_id][author_id]
            self.tasks[guild_id][author_id] = asyncio.create_task(self.wait_until_game_expires(guild_id, game))

            #Avertissement du joueur
            guild = discord.utils.get(self.bot.guilds, id=int(guild_id))
            author = discord.utils.get(guild.members, id=int(author_id))
            dm = author.dm_channel
            if dm is None:
                dm = await author.create_dm()
            game_embed = self.get_game_info_embed(author)
            await dm.send(f'Tu as supprimé le mot de ton message gagnant dans "{guild.name}"! Ton placement est invalidé, tu dois replacer ton mot dans un nouveau message...', embed=game_embed)
        else:
            logger.debug("Exiting on_raw_message_edit: Word still in content")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        #* https://discordpy.readthedocs.io/en/latest/api.html?highlight=on_message#rawmessagedeleteevent
        if not (payload.guild_id in self.ready_guilds):
            return
        
        guild_id = str(payload.guild_id)
        channel_id = str(payload.channel_id)
        message_id = str(payload.message_id)

        try:
            #Récupérer le message dans le cache
            msg = self.msg_cache[guild_id][channel_id][message_id]
        except KeyError:
            #Si le message n'est pas dans le cache, c'est qu'il ne nous intéresse pas
            return

        assert(self.has_running_game(msg.author))

        author_id = str(msg.author.id)
        game = self.games[guild_id][author_id]
        if game["placed"]:
            #Invalider la partie
            self.cancel_win(guild_id,author_id)
            
            #Informer le joueur
            guild = self.bot.get_guild(int(guild_id))
            player = guild.get_member(int(author_id))

            dm = player.dm_channel
            if dm is None:
                dm = await player.create_dm()
            
            game_embed = self.get_game_info_embed(player)
            await dm.send(f"Le message où tu avais placé ton mot dans \"{guild.name}\" a été supprimé! Le placement a été annulé, tu dois le replacer...", embed=game_embed)
            

    
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

        #Sinon
        logger.debug(f'Starting a game for "{ctx.author}" (id: {ctx.author.id}) on "{ctx.guild}" (id: {ctx.guild.id})')
        
        #Donne un mot à placer en MP (cooldown) et créé le jeu en cours
        guild_id = str(ctx.guild.id)
        author_id = str(ctx.author.id)
        game = self.new_game(ctx.author.id)
        self.games[guild_id][author_id] = game
        if not (author_id in self.scores[guild_id].keys()):
            self.scores[guild_id][author_id] = 0
            self.tag_as_modified(guild_id, SCORES)

        self.tag_as_modified(guild_id, GAMES)

        #Créé la tâche d'attente d'expiration
        self.tasks[guild_id][author_id] =  asyncio.create_task(self.wait_until_game_expires(ctx.guild.id, game))

        #Envoie les détails de sa partie au joueur
        dm = ctx.author.dm_channel
        if dm is None:
            dm = await ctx.author.create_dm()
        game_embed = self.get_game_info_embed(ctx.author)
        await dm.send(embed=game_embed)
        await ctx.send("Partie créée! Je t'ai envoyé les détails!")


    @commands.command()
    async def unmask(self, ctx, ping, *, mot):
        """unmask [lien] [mot]  Te permet de démasquer un mot dans le message de quelqu'un"""

        if not self.has_running_game(ctx.message.author):
            await ctx.send("Tu dois toi même jouer pour pouvoir utiliser cette commande!")
            return

        mot = mot.strip(' \n')
        mentions = ctx.message.mentions

        if len(mentions) != 1:
            await ctx.send(f"La commande prend exactement une mention! (pas {len(mentions)})")
            return
        
        target = mentions[0]

        if target.id == ctx.author.id:
            await ctx.send("Tu ne peux pas te démasquer toi même!")
            return

        if not self.has_running_game(target):
            await ctx.send("Cette personne n'a pas de partie en cours!")
            return

        guild_id = str(ctx.guild.id)
        target_id = str(target.id)
        author_id = str(ctx.author.id)
        good_guess = False
        if str(target.id) in self.games[guild_id].keys():
            if self.games[guild_id][target_id]["word"] == mot:
                good_guess = True
        
        if good_guess:
            #Arrêter la partie de 'target'
            del self.games[guild_id][target_id]
            self.tag_as_modified(guild_id, GAMES)
            
            self.tasks[guild_id][target_id].cancel()
            #NEXT Retirer des points à target?

            #Confirmer la réussite
            await ctx.send(f'{mot} était bien le mot de {target.name}! Tu as gagné {self.configs[guild_id]["points_per_find"]} points!')

            #Prévenir 'target' que son mot a été trouvé
            dm = target.dm_channel
            if dm is None:
                dm = await target.create_dm()
            
            await dm.send(f'Ton mot a été trouvé sur "{ctx.guild.name}"! Ta partie est arrêtée. Tu peux rejouer en tapant `=jouer` sur le serveur.')
            
            #Donner des points à l'auteur de la commande
            self.scores[guild_id][author_id] += self.configs[guild_id]["points_per_find"]
            self.tag_as_modified(guild_id, SCORES)
            
        else:
            if self.scores[guild_id][author_id] > 0:
                await ctx.send(f'"{mot}" n\'est pas le mot de {target.name}! Tu as perdu {self.configs[guild_id]["mistake_cost"]} points!' )
                #TODO Retirer des points à l'auteur du message
                self.scores[guild_id][author_id] = max(0, self.scores[guild_id][author_id] - self.configs[guild_id]["mistake_cost"])
                self.tag_as_modified(guild_id, SCORES)
            else:
                #TODO définir le cooldown
                await ctx.send(f'"{mot}" n\'est pas le mot de {target.name}! Cooldown de x minutes' )
                #TODO Appliquer le cooldown

                pass
        

    @commands.command()
    async def classement(self, ctx):
        """Affiche le classement des joueurs du serveur"""
        #TODO affiche le classement des joueurs
        guild_id = str(ctx.guild.id)
        classement = discord.Embed(title="Classement")
        scores = self.scores[guild_id]
        #tri du dictionnaire par score
        sorted_scores = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
        names = ""
        scores = ""
        ranks = ""
        rank = 1
        for user_id, score in sorted_scores:
            ranks += f"{rank}\n"
            names += f"<@{user_id}>\n"
            scores += f"{score}\n"
            rank += 1

        classement.add_field(name="Rang", value=ranks)
        classement.add_field(name="Nom", value=names)
        classement.add_field(name="Score", value=scores)
        
        await ctx.send(embed=classement)


    #*-*-*-*-*-*-*#
    #*-*-TASKS-*-*#
    #*-*-*-*-*-*-*#

    @tasks.loop(seconds=30.0)
    async def save_modified_files(self):
        for guild_id, modified in self._is_modified.items():
            if modified[GAMES]:
                logger.debug(f"games of guild {guild_id} have been modified, writing file")
                self.resource_manager.write(f"guilds/{guild_id}/games.json", json.dumps(self.games[guild_id], indent=4))
                self._is_modified[guild_id][GAMES] = False
            if modified[CONFIG]:
                logger.debug(f"config of guild {guild_id} has been modified, writing file")
                self.resource_manager.write(f"guilds/{guild_id}/guild_config.json", json.dumps(self.configs[guild_id]))
                self._is_modified[guild_id][CONFIG] = False
            if modified[SCORES]:
                logger.debug(f"scores of guild {guild_id} have been modified, writing file")
                self.resource_manager.write(f"guilds/{guild_id}/scores.json", json.dumps(self.scores[guild_id]))
                self._is_modified[guild_id][SCORES] = False
                

    @save_modified_files.before_loop
    async def before_save_modified_files(self):
        await self.bot.wait_until_ready()
        logger.info("Launching save_modified_files task loop")

    async def wait_until_game_expires(self, guild_id, game):
        duration = self.configs[str(guild_id)]["write_timer"]
        logger.debug(f"Waiting for game of user {game['user_id']} in guild {guild_id} to expire...")
        start = game["time"]
        now = int(time.time())
        wait_time = duration - (now - start)
        if wait_time > 0:
            try:
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.debug(f"Game (phase 1) of user {game['user_id']} in guild {guild_id} has been cancelled")
                return
        
        #Si le temps est écoulé...
        logger.debug(f"Game of user {game['user_id']} in guild {guild_id} has expired, deleting...")

        #Informer le joueur
        guild = self.bot.get_guild(int(guild_id))
        player = guild.get_member(int(game['user_id']))
        dm = player.dm_channel
        if dm is None:
            dm = await player.create_dm()
        await dm.send(f'Ta partie sur le serveur {guild.name} a expiré! Tu peux rejouer en tapant `=jouer` sur le serveur.')

        #Supprimer la partie
        del self.games[str(guild_id)][str(game["user_id"])]
        self.tag_as_modified(guild_id, GAMES)

    async def wait_for_victory(self, guild_id, game):
        guild_id = str(guild_id)
        user_id = str(game['user_id'])
        duration = self.configs[guild_id]["find_timer"]
        start = game["time_placed"]
        now = int(time.time())
        wait_time = duration - (now - start)
        logger.debug(f"Phase 2 of the user {user_id}'s game in guild {guild_id} has begun")
        if wait_time > 0:
            try:
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                logger.debug(f"Game (phase 2) of user {user_id} in guild {guild_id} has been cancelled")
                return
        
        logger.debug(f"Find timer of user {user_id} in guild {guild_id} timed out! Processing win...")

        #Supprimer la partie
        del self.games[guild_id][user_id]
        self.tag_as_modified(guild_id, GAMES)

        #Ajouter des points au joueur
        self.scores[guild_id][user_id] += self.configs[guild_id]["points_per_word"]

        #Informer le joueur
        guild = self.bot.get_guild(int(guild_id))
        player = guild.get_member(int(user_id))
        dm = player.dm_channel
        if dm is None:
            dm = await player.create_dm()
        await dm.send(f'Ta partie sur le serveur {guild.name} est terminée! Tu as gagné {self.configs[guild_id]["points_per_word"]} points sur le classement de "{guild.name}"! Tu peux rejouer en tapant `=jouer` sur le serveur.')


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
        if not game["placed"]:
            timer = self.configs[str(member.guild.id)]["write_timer"] - (int(time.time()) - game["time"])
            remaining_time = "%sh %smin %ss" % (timer//3600, (timer%3600)//60, (timer%60))
            embed = discord.Embed(title="Détails de ta partie:", color=member.color).add_field(name="Mot à placer", value=game["word"]).add_field(name="Temps restant", value=remaining_time)
        else:
            timer = self.configs[str(member.guild.id)]["find_timer"] - (int(time.time()) - game["time_placed"])
            remaining_time = "%sh %smin %ss" % (timer//3600, (timer%3600)//60, (timer%60))
            embed = discord.Embed(title="Détails de ta partie:", color=member.color).add_field(name="Mot placé", value=game["word"]).add_field(name="Temps avant victoire", value=remaining_time)
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
            "time_placed": False,
            "msg_link": False,
            "msg_content": False,
            "msg_id": False
        }

    def tag_as_modified(self, guild_id, filetype):
        guild_id = str(guild_id)
        if filetype in (GAMES, CONFIG, SCORES):
            self._is_modified[guild_id][filetype] = True
        