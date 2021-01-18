# Bavardobot

Un bot codé en 10 jours avec [discord.py](https://pypi.org/project/discord.py/)
dans le cadre du concours de programmation de l'AML en Janvier 2020.

## Installation

Clonez le répertoire:

```sh
git clone https://github.com/UnFefeSauvage/Bavardobot

cd Bavardobot 
```

Créez un environnement python virtuel et activez le:

```sh
python3 -m venv ./venv

source venv/bin/activate
```

Installez [discord.py](https://github.com/Rapptz/discord.py):

```sh
pip install discord.py
```

Ajoutez les [fichiers nécéssaires](https://github.com/UnFefeSauvage/Bavardobot#configuration).

Assurez vous d'avoir activé l'environnement virtuel python puis vous pouvez lancer le bot avec:

```sh
python src/main.py
```

## Configuration

Pour faire fonctionner le bot, vous devez ajouter 2 fichiers:

### resources/config.json

Les paramètres globaux du bot

Exemple:

```json
{
    "token": "votre-token",
    "prefix": "="
}
```

`prefix` étant le préfixe des commandes de votre bot

### resources/words

Il s'agit de la liste de mots que le bot distribuera aléatoirement à chaque partie

Exemple:

```txt
mot
montagne
escalier
abri-bus
encore_un_mot
Toujours un seul et même 'mot'
```

Les espaces avant et après les mots ne sont pas considérés

**/ ! \\** Étant donné les limitations de Discord, **votre mot ne doit pas faire plus de 1024 caractères** si jamais il vous en prenait l'envie...

## Concept

Une commande (`=jouer`) pour obtenir un mot.

Un temps donné pour placer le mot dans une conversation.

Une commande (`=unmask`) pour démasquer les mots dans les message des autres.

Un temps donné pour trouver les mots placés.

Et **PAF!** Ça fait un jeu sur Discord! \
(Et des Chocapics si vous y tenez)

## Autres points notables

`resources/guilds/template` \
C'est le dossier copié pour initialiser les données d'un serveur. \
C'est donc dans ce dossier que se trouvent les paramètres par défaut du jeu.

#### resource_manager

Le resource_manager utilisé par le jeu pour accéder aux fichiers sans se soucier des 'race conditions' est initialisé dans le main avec pour racine `resources`. \
Vous pouvez changer ce dossier à ce qui vous arrange mais **il doit contenir la hiérarchie de fichiers de `resources`.**
  
