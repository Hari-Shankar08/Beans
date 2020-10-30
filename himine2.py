import discord
import json
import re
import pickle
import asyncio
import random

with open("auth.pkl", "rb") as file:
    token = pickle.load(file)

with open('skeld_locations.pkl', 'rb') as pkl_file:
    skeld_locations = pickle.load(pkl_file)

with open('skeld_map.pkl', 'rb') as pkl_file:
    skeld_map = pickle.load(pkl_file)

with open('skeld_vents.pkl', 'rb') as pkl_file:
    skeld_vents = pickle.load(pkl_file)


client = discord.Client()
game_requested = False
game_in_progress = False
meeting_in_progress = False
default_n_players = 2
n_players = 2
impostors = []
players = []
players_alive = []
player_locations = []
death_place = [None] * len(skeld_map)
time_remaining = 0
time_remaining_message = ''
help_coms = {
    'sus.game': 'Starts the game.',
    'sus.game(n)': 'Starts the game with n players.',
    'game.join()': 'Join the current game.',
    'game.players': 'See the players who are part of the game.',
    'game.reset()': 'Resets the game',
    '!m n': 'Move to the tile numbered n',
    '!k': 'Kill a player (Impostor only)',
    '!v': 'Use vents (Impostor only)',
    '!v up': 'Exit vents (Impostor only)',
    '!rep': 'Report a dead body.',
    '!where': 'See your current location',
    '!map': 'See a map of The Skeld (not implemented yet)'
    }
voting_names = []
ejected = ''
ej_list = []
vote_count = 0

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
    global death_place
    global meeting_in_progress
    global time_remaining_message
    global time_remaining
    global help_coms
    global voting_names
    global ejected
    global ej_list
    global vote_count

    if message.author == client.user:
        return

    if message.content == '!help':
        embed = discord.Embed(title='Help',
                              description='List of available commands:')
        for key, val in help_coms.items():
            embed.add_field(name=key, value=val)
        await message.channel.send(embed=embed)

    if True:
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
                        voting_names.append(message.author)
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
                        voting_names.append(message.author)
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
                    if len(players) > 2:
                        impostors = random.sample(players, 2)
                    else:
                        impostors = [random.choice(players)]

                    for i in range(len(players)):
                        if players[i] in impostors:
                            await players[i].send('You are the impostor. Don\'t get caught!')
                        else:
                            await players[i].send('You are a crew-mate.')
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
                    if player_locations[i] == current_location and players_alive[i] != 0:
                        if players[i] != message.author:
                            await players[i].send(f'{message.author} is leaving \
{skeld_locations[current_location]}: Tile {current_location}')

                if tile_number in allowed_tiles:
                    player_locations[players.index(message.author)] = tile_number
                    await message.channel.send(f"You are currently in {skeld_locations[tile_number]} \
(Tile {tile_number})")
                    if death_place[tile_number] is not None:
                        await message.channel.send("There is a dead body here!\nType '!rep' to report!")

                    if message.author in impostors and tile_number in skeld_vents:
                        await message.channel.send('You can vent here. Use !v to enter the vent')

                    same_place = []
                    for i in range(len(player_locations)):
                        if player_locations[i] == tile_number and players_alive[i] != 0:
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
                            if player_locations[i] == tile_to and players_alive[i] != 0:
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
                            if player_locations[i] == current_tile and players_alive[i] != 0:
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

        if message.content.lower() == "!k":
            if message.author in players:
                if message.author in impostors:
                    current_tile = player_locations[players.index(message.author)]
                    if current_tile < 40:
                        same_place = []
                        for i in range(len(player_locations)):
                            if player_locations[i] == current_tile and players_alive[i] != 0:
                                same_place.append(players[i])
                        same_place = [player for player in same_place if player != message.author]

                        # same_place contains players (in same place)
                        if same_place:  # Runs if non-empty
                            players_alive[players.index(same_place[0])] = 0
                            await message.channel.send(f"You just killed {same_place[0]}!")
                            await same_place[0].send(f'You have been killed by {message.author}')
                            for player in same_place[1:]:
                                await player.send(f"Player {same_place[0]} has been killed by {message.author}")
                            if death_place[current_tile] is None:
                                death_place[current_tile] = [same_place[0]]
                            else:
                                death_place[current_tile].append(same_place[0])
                        else:
                            await message.channel.send("You're the only one here.")
                    else:
                        await message.channel.send("You can't kill from a vent! Get out!")
                else:
                    await message.channel.send("Do you think you're an impostor?\nYou're not. Run along now.")

        if message.content.strip().lower() == 'admin/impostors':
            await message.channel.send(str(impostors))

        if message.content.lower().strip() == "!rep":
            current_tile = player_locations[players.index(message.author)]
            if death_place[current_tile] is not None:
                player_locations = [14] * len(players_alive)
                for player in players:
                    await player.send(f"A dead body was found!\nReported by {message.author} \
    \nDiscuss!!\n You've got 30s")
                    await player.send("Dead dudes please don't chat. Keep the game interesting!")
                await asyncio.sleep(30)
                meeting_in_progress = True
                for player in players:
                    time_remaining = 30
                    while time_remaining > 0:
                        time_remaining -= 1
                        if time_remaining >= 0:
                            await time_remaining_message.edit(content=f'Time remaining :{time_remaining} seconds')
                        else:
                            await time_remaining_message.edit(content=f'Time Up!')
                        await asyncio.sleep(0.1)
                    else:
                        await time_remaining_message.edit(content=f'Voting starts! You have 20s!')
                        #hey how to not let the players move or vent until voting stops? we have to put it here
                        # and we need to add the cooldown for the killing(20s)
                await message.channel.send("The list of player names are:")
                for player in players:
                    await message.channel.send(f"{player}\n")
                    if player.startswith('~'):
                        voting_names[voting_names.index(player)] = player.lstrip('~')# to check if original name startswith '~'
                await message.channel.send("Type '!vo @(suspect's name(to mention/tag))'\nDont type anything if you want to abstain! ")
                for player in players:
                    if player.mention in message.content.split():
                        vote_count += 1
                        if len(player) < 5:
                             voting_names[voting_names.index(player)] = player + 'z'*(5-len(player))# to keep all name sizes uniform
                        if player.startswith('~'):
                            voting_names[voting_names.index(player)] = '~' + player# to count multiple votes
                        else:
                            voting_names[voting_names.index(player)] = "~" + player[:5]# to keep all name sizes uniform
                ejected = max(voting_names)
                ej_list = [player for player in voting_names if player == ejected]# to find multiple maximums
                if vote_count < ceil(len(players)/2):#atleast half the people should vote
                    await message.channel.send("No one was ejected(Skipped)")
                elif len(ej-list) > 1:
                    await message.channel.send("No one was ejected(Tie)")
                else:
                    await message.channel.send(f"Player {ejected.strip('~')} was ejected!\
                    \nContinue Playing!")
                    for player in players:
                        if ejected.strip('~') in player:# to check which player was ejected
                            players_alive[players.index(player)] = 0
            else:
                await message.channel.send("You don't even see a corpse!")
                #will implement emergency meetings tomorrow!

@client.event
async def on_member_join(member):
    # We need to change this thing here. I'm thinking as an explanation and tutorial to start game
    await member.send("""Hello, there, I'm your friendly neighbourhood bean.
You can call for a game of BEAN SUS using "sus.game()" """)


client.run(token)
