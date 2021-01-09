import discord
from discord.ext import commands

#TODO Un jeu de placement de mots dans des conversations 

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
    
    #TODO on_server_join: créer le répertoire et les fichiers nécéssaires pour le serveur

    #TODO event: on_message: vérifier si l'auteur joue et a placé son mot
    #TODO event: on_message_edit: vérifier que l'auteur ne triche pas
    #TODO event: on_message_delete: vérifier que l'auteur ne triche pas

    #TODO command: jouer: donne un mot à placer en MP (cooldown)
    #TODO command: unmask(mot): démasque un joueur sur son mot (cooldown en cas de faux)
    #TODO command: classement: affiche le classement des joueurs