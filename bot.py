import discord
import json
import re
import pickle
import asyncio
import random

with open("auth.json", "r") as file:
    token = json.load(file)["token"].strip()

with open('skeld_locations.pkl', 'rb') as pkl_file:
    skeld_locations = pickle.load(pkl_file)

with open('skeld_map.pkl', 'rb') as pkl_file:
    skeld_map = pickle.load(pkl_file)

with open('skeld_vents.pkl', 'rb') as pkl_file:
    skeld_vents = pickle.load(pkl_file)


client = discord.Client()
game_requested = False
game_in_progress = False
default_n_players = 2  # Change this in the end to 10 
n_players = 2
impostors = []
players = []
players_alive = []
player_locations = []


@client.event
async def on_ready():
    print("Ready to go!")


# This is checking when the bot receives a message.
@client.event
async def on_message(message):
    global game_requested
    global skeld_map
    global skeld_locations
    global skeld_vents
    global players_alive
    global player_locations
    global default_n_players
    global impostors
    global players
    global game_in_progress
    global n_players

    if message.author == client.user:
        return
    else:
        if message.content.strip().lower() == "sus.game()":
            if not game_in_progress:
                if not game_requested:
                    # Sends to the channel where the last message was sent
                    await message.channel.send(f"Ok people. Let's go!\nJoin this game by using \"game.join()\"\n\
{n_players} players' game")
                    game_requested = True
                    players.append(message.author)
                else:
                    await message.channel.send("A game has already been requested.")
            else:
                await message.channel.send("A game is currently in progress. Please wait.")

        if re.match(r'sus.game\(\d+\)', message.content.strip().lower()):
            m = message.content.strip().lower()
            if not game_in_progress:
                if not game_requested:
                    # Sends to the channel where the last message was sent
                    await message.channel.send("Ok people. Let's go!\nJoin this game of by using \"game.join()\"")
                    n_players = eval(m[m.index('('):])
                    if n_players > 0:
                        await message.channel.send(f"{n_players} players' game")
                        game_requested = True
                        players.append(message.author)
                    else:
                        n_players = default_n_players
                        await message.channel.send("Bruh. Did you think I wouldn't think of these things?")
                else:
                    await message.channel.send("A game has already been requested.")
            else:
                await message.channel.send("A game is currently in progress. Please wait.")

        if message.content.strip().lower() == "game.join()":
            if not game_in_progress:
                if len(players) < n_players:
                    if message.author not in players:
                        players.append(message.author)
                    else:
                        await message.channel.send(f"Looks like you've already joined the game, {message.author}")
                else:
                    await message.channel.send("Maximum number of players reached.")

                if len(players) == n_players:
                    await message.channel.send("Alright, starting game.")
                    for player in players:
                        await player.send("Here we go then!")
                    game_in_progress = True
                    await asyncio.sleep(2)
                    players_alive = [1] * len(players)  # 1 for alive, 0 for dead
                    player_locations = [14] * len(players_alive)
                    if len(players) >= 2:
                        impostors = random.sample(players, 2)
                    else:
                        impostors = [random.choice(players)]

                    for i in range(len(players)):
                        if players[i] in impostors:
                            await players[i].send('You are the impostor. Don\'t get caught!')
                        else:
                            await players[i].send('You are innocent. Two impostors remain.')
                        await players[i].send(f"You are currently in {skeld_locations[player_locations[i]]} \
(Tile {player_locations[i]})")

            else:
                await message.channel.send("There's already a game in progress. Please wait.")

        if message.content.strip().lower() == "game.players":
            if len(players) > 0:
                await message.channel.send("These dudes are in the game right now:")
                for player in players:
                    await message.channel.send(player)
            else:
                await message.channel.send("No players yet.")

        # Reset Game
        if message.content.strip().lower() == "game.reset()":
            # Only if you are a player
            if message.author in players:
                game_requested = False
                game_in_progress = False
                n_players = default_n_players
                impostors = []
                players = []
                players_alive = []
                player_locations = []

                for player in players:
                    await player.send(f"Game has been reset by {message.author}.")
            else:
                await message.channel.send('You can\'t reset the game. Be nice for a change.')

        # Things to do
        # Move around the map
        if re.match(r'!m \d+', message.content.strip().lower()):
            if message.author in players:
                _, tile_number = tuple(message.content.strip().split())
                tile_number = int(tile_number)

                # Check message author's current position
                current_location = player_locations[players.index(message.author)]
                allowed_tiles = skeld_map[current_location]
                same_place = []
                for i in range(len(player_locations)):
                    if player_locations[i] == current_location:
                        if players[i] != message.author:
                            await players[i].send(f'{message.author} is leaving \
{skeld_locations[current_location]}: Tile {current_location}')

                if tile_number in allowed_tiles:
                    player_locations[players.index(message.author)] = tile_number
                    await message.channel.send(f"You are currently in {skeld_locations[tile_number]} \
(Tile {tile_number})")

                    if message.author in impostors and tile_number in skeld_vents:
                        await message.channel.send('You can vent here. Use !v to enter the vent')

                    same_place = []
                    for i in range(len(player_locations)):
                        if player_locations[i] == tile_number:
                            same_place.append(players[i])
                    same_place = [player for player in same_place if player != message.author]
                    if same_place:  # Runs if non-empty
                        await message.channel.send("You also see:")
                        
                        for player in same_place:
                            await message.channel.send(f"{player}")
                            # Send message to player as well
                            await player.send(f'{message.author} has entered \
{skeld_locations[tile_number]}: Tile {tile_number}')
                    else:
                        await message.channel.send("You're the only one here.")
                else:
                    await message.channel.send('That\'s not allowed. Use !map to view a map and corresponding tile \
number. (Not Implemented Yet!)')

        # Vent if available, if impostor
        # Use !v
        if message.content.strip().lower() == "!v":
            # Check if impostor
            if message.author in impostors:
                #  Check if in a vent-able location
                current_tile = player_locations[players.index(message.author)]

                if current_tile in skeld_vents.keys():
                    # Make "invisible"
                    player_locations[players.index(message.author)] = current_tile + 50
                    # Get the allowed movements
                    allowed_tiles = skeld_vents[current_tile]

                    await message.channel.send('You can move to:')
                    for tile in allowed_tiles:
                        # Send the name of location and Tile number
                        await message.channel.send(f"{skeld_locations[tile]}: Tile {tile}")
                    await message.channel.send("Move using !v (Tile Number)")
                else:
                    await message.channel.send("You can't vent here!")
            else:
                message.channel.send("Do you think you're an impostor?\nYou're not. Run along now.")

        if re.match(r'!v \d+', message.content.strip().lower()):
            if message.author in players:
                # Check if impostor
                if message.author in impostors:
                    #  Check if in a vent-able location
                    current_tile = player_locations[players.index(message.author)]
                    if current_tile > 50:
                        current_tile -= 50
                    _, tile_to = tuple(message.content.strip().lower().split())

                    tile_to = int(tile_to)
                    if tile_to in skeld_vents[current_tile]:
                        player_locations[players.index(message.author)] = tile_to + 50
                        await message.channel.send(f"You are currently in the vent at {skeld_locations[tile_to]}: \
Tile Number {tile_to}.\nYou are not seen.")

                        same_place = []
                        for i in range(len(player_locations)):
                            if player_locations[i] == tile_to:
                                same_place.append(players[i])
                        same_place = [player for player in same_place if player != message.author]
                        if same_place:  # Runs if non-empty
                            await message.channel.send("You can see:")
                            for player in same_place:
                                await message.channel.send(f"{player}")
                        else:
                            await message.channel.send("There's no one here. Use !v up to move up.")
                        # Get the allowed movements
                        allowed_tiles = skeld_vents[tile_to]

                        await message.channel.send('You can move to:')
                        for tile in allowed_tiles:
                            # Send the name of location and Tile number
                            await message.channel.send(f"{skeld_locations[tile]}: Tile {tile}")
                    else:
                        await message.channel.send("You can't move there! Use !v \
to enter vent and see where you can go to.")
                else:
                    await message.channel.send("Do you think you're an impostor?\nYou're not. Run along now.")

        if message.content.strip().lower() == '!v up':
            if message.author in players:
                # Check if impostor
                if message.author in impostors:
                    current_tile = player_locations[players.index(message.author)]
                    if current_tile > 40:
                        current_tile = current_tile - 50
                        same_place = []
                        await message.channel.send(f"You are currently in {skeld_locations[current_tile]} \
(Tile {current_tile})")
                        for i in range(len(player_locations)):
                            if player_locations[i] == current_tile:
                                same_place.append(players[i])
                        same_place = [player for player in same_place if player != message.author]
                        if same_place:  # Runs if non-empty
                            await message.channel.send("You can see:")
                            for player in same_place:
                                await message.channel.send(f"{player}")
                        else:
                            await message.channel.send("You're the only one here.")

                        player_locations[players.index(message.author)] = current_tile
                    else:
                        await message.channel.send('You\'re not even in a vent. Seriously. Think I wouldn\'t notice?')

                else:
                    await message.channel.send("Do you think you're an impostor?\nYou're not. Run along now.")

        if message.content.lower() == '!where':
            if message.author in players:
                current_tile = player_locations[players.index(message.author)]
                if current_tile > 40:
                    current_tile -= 50
                await message.channel.send(f"You are currently in {skeld_locations[current_tile]}: Tile {current_tile}")


@client.event
async def on_member_join(member):
    # We need to change this thing here. I'm thinking as an explanation and tutorial to start game
    await member.send("""Hello, there, I'm your friendly neighbourhood bean.
You can call for a game of BEAN SUS using "sus.game()" """)


client.run(token)
