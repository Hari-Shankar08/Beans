from discord.ext.commands import Bot
import discord
import asyncio
import pickle
import random
import re

with open("auth.pkl", "rb") as file:
    token = pickle.load(file)

with open('skeld_locations.pkl', 'rb') as pkl_file:
    skeld_locations = pickle.load(pkl_file)

with open('skeld_map.pkl', 'rb') as pkl_file:
    skeld_map = pickle.load(pkl_file)

with open('skeld_vents.pkl', 'rb') as pkl_file:
    skeld_vents = pickle.load(pkl_file)

bot = Bot(command_prefix='!')
games = {}
in_a_game = {}
guild_premium = []


class NoPremiumError(Exception):
    pass


class InvalidMovement(Exception):
    pass


class Game:
    def __init__(self, n_players=2):
        self.n_players = n_players
        self.game_in_progress = False
        self.meeting_in_progress = False
        self.has_killed = {}
        self.impostors = []
        self.players = []
        self.players_alive = []
        self.player_locations = []
        self.death_place = [None] * len(skeld_map)
        self.player_colours = {}
        self.voting_names = []
        self.ejected = ''
        self.ej_list = []
        self.vote_count = 0
        self.votes = {}
        self.can_emergency = False
        self.discuss = False
        self.voted = []


@bot.command()
async def game(ctx, *args):
    global games
    try:
        if not args:
            this_game = Game()
            n_players = 2
            code = str(round(random.random() * 1000))
        else:
            try:
                n_players = int(args[0])
            except ValueError:
                await ctx.send('Placeholder angry message.')
                return
            this_game = Game(n_players=n_players)
            try:
                code = args[1]
            except IndexError:
                code = str(round(random.random() * 1000))

        g_id = ctx.message.guild.id
        if g_id in games.keys():
            if len(games[g_id]) >= 2:
                if g_id not in guild_premium:
                    raise NoPremiumError(f'Guild with Guild ID {g_id} does not have premium.')
        try:
            games[ctx.message.guild.id][code] = this_game
        except KeyError:  # No games running at the time on that server
            games[ctx.message.guild.id] = {code: this_game}

        await ctx.send(f'Alright. Queueing game of {n_players} with unique code {code}')
    except NoPremiumError as npe:
        await ctx.send(f'Whoa, got this error...\n```\nNoPremiumError: {str(npe)}```')
        await ctx.send('Only Premium guilds can have more than 2 games running at a time.')


@bot.command()
async def join(ctx, *args):
    global games
    global in_a_game
    g_id = ctx.message.guild.id
    available_games = games[g_id]
    if ctx.message.author not in in_a_game:
        try:
            if args[0] in available_games:
                game_ = available_games[args[0]]
                if not game_.game_in_progress:
                    game_.players.append(ctx.message.author)
                    await ctx.send(f'Ok, joined the game, {ctx.message.author}.')
                    await ctx.send('Set a nickname with !nick.')
                    if len(game_.players) == len(game_.player_colours) == game_.n_players:
                        await ctx.send('Alright, starting game.\n\nNo this is not done yet.')
                        await start_game(game)
                    available_games[args[0]] = game_
                    games[g_id] = available_games

                    in_a_game[ctx.message.author] = [g_id, args[0]]
                else:
                    await ctx.send('Sorry, that game is in progress.')
            else:
                await ctx.send('Invalid Code. Are you sure this is the one?')
        except IndexError:
            await ctx.send('Ok, sure, you want to join a game... but I need the game code for that!')
    else:
        await ctx.send(f'I can\'t allow you join more than one game, {ctx.message.author}')


@bot.command()
async def which(ctx):
    if ctx.message.author in in_a_game:
        await ctx.send(f'You have joined the game with unique code: {in_a_game[ctx.message.author][1]}')
    else:
        await ctx.send(f'You aren\'t in a game yet, {ctx.message.author}.')


@bot.command()
async def nick(ctx, *args):
    global games
    try:
        if ctx.message.author in in_a_game:
            g_id = ctx.message.guild.id
            nick_ = args[0]
            if nick_.startswith('http') or nick_.strip().lower() == 'skip':
                raise ValueError('Disallowed nickname.')

            gm = games[g_id][in_a_game[ctx.message.author]]
            if not gm.game_in_progress and nick_ not in game_.player_colours.values():
                gm.player_colours[ctx.message.author] = nick
                await ctx.send('Ok, nickname set.')
                print(len(gm.players) == len(game_.player_colours) == game_.n_players)
                if len(gm.players) == len(game_.player_colours) == game_.n_players:
                    await ctx.send('Alright, starting game.\n\nNo this is not done yet.')
                    await start_game(game_)
                games[g_id][in_a_game[ctx.message.author]] = gm
            elif gm.game_in_progress:
                await ctx.semd('Hey! You can\'t change nicknames in between the game!')
            elif nick_ in gm.player_colours.values():
                raise ValueError('Nickname has already been taken.')
        else:
            await ctx.send('You aren\'t in a game yet, {}'.format(ctx.message.author))

    except IndexError:
        await ctx.send('You want to set a nickname, huh? I need the name for that!')

    except ValueError as ve:
        await ctx.send(f'I can\'t allow you to take that nickname.\n```\nReason: {str(ve)}```')


@bot.command()
async def m(ctx, tile):
    try:
        if ctx.message.author in in_a_game:
            tile = int(tile)
            g_id, u_id = tuple(in_a_game[ctx.message.author])
            gm = games[g_id][u_id]
            await move_player(gm, pl, tile)
            await ctx.send('Movement not implemented yet.')
    except ValueError:
        await ctx.send('That\'s not allowed. Use "!map" to see a map of allowed tiles.')

# --- Non bot commands ---

async def start_game(gm):
    for player in gm.players:
        await player.send("Game is now in progress.")
    gm.game_in_progress = True
    await asyncio.sleep(2)
    gm.players_alive = [1] * len(players)  # 1 for alive, 0 for dead
    gm.player_locations = [14] * len(players_alive)
    gm.impostors = random.sample(players, n_impostors)
    gm.has_killed = dict.fromkeys(impostors, True)
    d = {player: player_colours[player] for player in players}
    for i in range(len(gm.players)):
        if gm.players[i] in impostors:
            await gm.players[i].send('You are the `impostor`. Don\'t get caught!')
            embed = await make_embed('In Game', 'Players and their Nicknames:', dict_=d, is_impostor=True, gm=gm)
            await gm.players[i].send(embed=embed)
        else:
            await gm.players[i].send(f'You are a `crew-mate`. There is {len(impostors)} impostor among you.')
            embed = await make_embed('In Game', 'Players and their Nicknames:', dict_=gm.player_colours)
            await gm.players[i].send(embed=embed)

        await gm.players[i].send(f"You are currently in {skeld_locations[player_locations[i]]} \
(Tile {player_locations[i]})")
        await asyncio.sleep(15)
        gm.has_killed = dict.fromkeys(impostors, False)
        gm.can_emergency = True

        await putback_game(gm, random.choice(gm.players))


async def putback_game(gm, pl):
    global games
    global in_a_game

    g_id, u_id = tuple(in_a_game(pl))
    games[g_id][u_id] = gm
    print('Games dictionary updated.')


async def move_player(gm, pl, tile):
    if pl in gm.players:
    pass

async def make_embed(title, desc, dict_, is_impostor=False, footer=None, gm=None):
    embed = discord.Embed(title=title,
                          description=desc)
    embed.set_thumbnail(url=bot.user.avatar_url)
    if not is_impostor:
        for key, val in dict_.items():
            embed.add_field(name=str(key), value=val)
    else:
        for key, val in dict_.items():
            if key in gm.impostors:
                embed.add_field(name=str(key) + ' (Impostor)', value=val)
            else:
                embed.add_field(name=str(key), value=val)
    if footer is not None:
        embed.set_footer(text=footer, icon_url=bot.user.avatar_url)
    else:
        embed.set_footer(text='BEAN SUS: TEXT BASED AMONG US ON DISCORD', icon_url=bot.user.avatar_url)

    return embed


# --- Running the bot ---

if __name__ == '__main__':
    print('Running...')
    bot.run(token)
