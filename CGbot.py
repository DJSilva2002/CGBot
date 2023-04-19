import discord
from discord.ext import commands
import json
import requests
import discord.ui
import os
import asyncio
import datetime
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")
# BuddyBotty = 1022646163301736458
# OTB_Testing = 1072413437604401202
Naraku = 1040475128091385876
OTB = 1097439166226239528

servers = [1022646163301736458, 1072413437604401202]

# Intenets are set to all in the code so it doesnt get complicated. Bot only requires basic permissions to function in Discord


def load_prefixes():
    try:
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        return {int(user_id): balance for user_id, balance in prefixes.items()}
    except FileNotFoundError:
        return {}

# Create a function to save balances to a JSON file


def save_prefixes(prefixes):
    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


LAST_PLAYED_FILENAME = 'prefixes.json'

try:
    with open(LAST_PLAYED_FILENAME, 'r') as f:
        prefixes = json.load(f)
except FileNotFoundError:
    prefixes = {}
    with open(LAST_PLAYED_FILENAME, 'w') as f:
        json.dump(prefixes, f)


# Create a function that returns the appropriate prefix for a guild
def get_prefix(ctx, message):
    # Load prefixes from file
    prefixes = load_prefixes()
    # Check if the guild has a custom prefix
    if message.guild and message.guild.id in prefixes:
        return prefixes[message.guild.id]
    # Otherwise use the default prefix '/'
    else:
        return '/'


COOLDOWN_TIME = 60

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.cooldowns = commands.CooldownMapping.from_cooldown(
    1, COOLDOWN_TIME, commands.BucketType.user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = error.retry_after
        message = f"This command is on cooldown. Please try again in {seconds:.0f} seconds."
        await ctx.send(message)

    # specify the key parameter to make the cooldown per user
    bot.cooldowns.update_rate_limit(ctx.message)


@bot.command()
async def setprefix(ctx, prefix: str):
    if ctx.author == ctx.guild.owner:
        prefixes = load_prefixes()
        prefixes[ctx.guild.id] = prefix
        save_prefixes(prefixes)
        await ctx.send(f"New prefix is {prefix}")
    else:
        await ctx.send("Only the server owner can change the prefix.")


command_count = {}

data = {}

sent_messages = []


async def find_message_by_title(channel, title):
    async for message in channel.history(limit=10):
        if message.author == bot.user:
            if len(message.embeds) > 0:
                embed = message.embeds[0]
                if embed.title == title:
                    return message
    return None


async def display_custom_games(channel, game_title, reach_filter=None, jumps_filter=False):
    async def update_embed():
        if game_title == "$HALO_3_TITLE":
            title = "Halo 3"
        elif game_title == "$HALO_REACH_TITLE":
            title = "Halo Reach"
        response = requests.get(
            "https://63df0e2159bccf35daae0f80.mockapi.io/CGB")

        msg = await find_message_by_title(channel, title)

        current_time = datetime.datetime.now()
        new_time = current_time - datetime.timedelta(hours=5)

        # Format the date and time as a string
        timestamp_str = new_time.strftime("%I:%M %p")

        if response.status_code != 200:
            print('Failed to retrieve data from API')
            await channel.send('No games were found.')
            return

        json_data = response.json()

        # Extract the custom game array from the API response
        custom_game_array = None
        if isinstance(json_data, list) and len(json_data) > 0:
            obj = json_data[0]
            if isinstance(obj, dict) and '2' in obj:
                custom_game_array = obj['2'][1]

        if custom_game_array is None:
            print('CustomGameArray not found in JSON data')
            await channel.send('No games were found.')
            return

        # Creates an embed to display specific keys located within the customgamearray
        games = {}
        i = 0
        for game in custom_game_array:
            # print(game["CurrentlyPlayingVariant"]["MCCGame"])
            seats = int(game["MaxPlayers"]) - int(game["PlayersInGame"])

            # Check if the game matches the specified title
            if game_title in game["CurrentlyPlayingVariant"]["MCCGame"]:
                if reach_filter is not None and "HALO_REACH_TITLE" in game["CurrentlyPlayingVariant"]["MCCGame"]:
                    if "parkour" not in game["CurrentlyPlayingVariant"]["GameType"].lower():
                        continue
                if jumps_filter:
                    if game["CurrentlyPlayingVariant"]["MCCGame"] != "$HALO_3_TITLE":
                        continue
                    if "jump" not in game["CurrentlyPlayingVariant"]["GameType"].lower():
                        continue
                games[i] = {
                    "Server": game['CustomGameName'],
                    "CurrentMap": game['CurrentlyPlayingMap']['MapName'],
                    "CurrentType": game['CurrentlyPlayingVariant']['GameType'],
                    "MapCount": game['TotalMapCount'],
                    "Region": game['ServerRegionName'],
                    "Ping": game['PingMilliseconds'],
                    "Seats": seats,
                    "ID": game['GameID']
                }
                i += 1

        emoji, emoji2 = bot.get_emoji(
            1097055068001419284), bot.get_emoji(1097056055005020182)

        embed = discord.Embed(title=title, color=discord.Color.purple())
        i = 0
        for game in games:
            if i > 0:
                embed.add_field(
                    name="\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-", value="\n")
            embed.add_field(
                name=f"-Server {i+1}-", value=f"{emoji}  **Name:** {games[i]['Server']}\n{emoji}  **Map:** {games[i]['CurrentMap']}\n{emoji}  **Game Type:** {games[i]['CurrentType']}\n{emoji}  **Map Count:** {games[i]['MapCount']}\n{emoji}  **Region:** {games[i]['Region']}\n{emoji}  **Ping:** {games[i]['Ping']}\n{emoji}  **Seats:** {games[i]['Seats']}\n{emoji2}  **ID:** {games[i]['ID']}", inline=False)
            i += 1
        # Burnts code needs to be updated before this will work
        # embed.add_field(name="Next Map",
        #                 value=game['VariantArray'][0]['MapArray'][0]['MapName'], inline=False)
        # embed.add_field(
        #     name="Info", value="Halo 3 is filtering for the word Jumps so every server with Jumps in the game type will be displayed. \n\n Halo Reach is filtering for the word Parkour so every server with Parkour in the game type will be displayed. \n\n If there are servers without those keywords they will not be displayed.", inline=False)
        embed.set_thumbnail(url="https://imgur.com/PekVEte.png")
        embed.set_footer(text=f"Created by Pownin | DasOfTheBroken | BurntKurisu - {timestamp_str}",
                         icon_url="https://imgur.com/Mz2kaCE.png")

        if not games:
            embed2 = discord.Embed(title=title, color=discord.Color.purple())

            if title == "Halo 3":
                embed2.set_image(url="https://imgur.com/gxEfJN5.png")
            elif title == "Halo Reach":
                embed2.set_image(url="https://imgur.com/dGz0253.png")

            embed2.set_thumbnail(url="https://imgur.com/PekVEte.png")
            embed2.set_footer(text=f"Created by Pownin | DasOfTheBroken | BurntKurisu - {timestamp_str}",
                              icon_url="https://imgur.com/Mz2kaCE.png")
            if msg:
                await msg.edit(embed=embed2)
            elif not msg:
                await channel.send(embed=embed2)
            await msg.clear_reactions()
            return
        else:
            emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣",
                          "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            if msg:
                await msg.edit(embed=embed)

            else:
                await channel.send(embed=embed)
            await channel.purge(limit=5, check=lambda message: message.author != channel.guild.me)
            embed_ids = await get_embed_message_ids(channel)
            if embed_ids is not None:
                halo_reach_id = embed_ids["Halo Reach"]
                halo_3_id = embed_ids["Halo 3"]
            c = 0
            if title == "Halo 3":
                message = await channel.fetch_message(halo_3_id)
            elif title == "Halo Reach":
                message = await channel.fetch_message(halo_reach_id)
            if msg:
                await msg.clear_reactions()
                await asyncio.sleep(1)
            for i in range(len(games)):
                await msg.add_reaction(emoji_list[i])
                await asyncio.sleep(1)
            for game in games:
                await message.add_reaction(f"{emoji_list[c]}")
                c += 1
    await update_embed()


async def get_embed_message_ids(channel):
    messages = []
    async for message in channel.history(limit=10):
        messages.append(message)
    embed_ids = {}
    for message in messages:
        for embed in message.embeds:
            if embed.title == "Halo Reach" or embed.title == "Halo 3":
                embed_ids[embed.title] = message.id
                if len(embed_ids) == 2:
                    return embed_ids
    return None


async def get_bot_messages(channel):
    bot_messages = []
    async for message in channel.history():
        if message.author == bot.user:
            bot_messages.append(message.id)
    return bot_messages


def new_embed(custom_game_array, s):
    emoji, emoji2 = bot.get_emoji(
        1097055068001419284), bot.get_emoji(1097056055005020182)
    index = s.find("ID:") + 4
    number = s[index:].strip()
    number = number.strip("* ").strip()
    game_list = {}
    name = ""
    for game in custom_game_array:
        if number == game["GameID"]:
            deep = 0
            name = game['CurrentlyPlayingMap']['MapName']
            name1 = game["CustomGameName"]
            for variant in game["VariantArray"]:
                deeper = 0
                maps = {}
                for map in game["VariantArray"][deep]["MapArray"]:
                    maps[deeper] = game["VariantArray"][deep]["MapArray"][deeper]["MapName"]
                    deeper += 1
                game_list[deep] = maps
                deep += 1

    mapstr = []
    emoji, emoji2, emoji3, emoji4 = bot.get_emoji(1097055068001419284), bot.get_emoji(
        1097056055005020182), bot.get_emoji(1097131980023418900), bot.get_emoji(1097132427538870332)
    for outer_key in game_list:
        maps = ""
        o = 0
        i = 0
        inner_dict = game_list[outer_key]
        for inner_key in inner_dict:

            if inner_dict[inner_key] == name:
                if i == list(inner_dict.keys())[-1]:
                    maps += f"{emoji4}**>Map {o+1}:** "
                else:
                    maps += f"{emoji3}**>Map {o+1}:** "
                maps += "**"+inner_dict[inner_key] + "<**\n"
            else:
                if i == list(inner_dict.keys())[-1]:
                    maps += f"{emoji2}**Map {o+1}:** "
                else:
                    maps += f"{emoji}**Map {o+1}:** "
                maps += inner_dict[inner_key] + "\n"
            o += 1
            i += 1
        mapstr.append(maps)

    i = 1
    embed2 = discord.Embed(
        title=f"All maps in \"{name1}\"", color=discord.Color.purple())
    for item in mapstr:
        if i > 1:
            embed2.add_field(
                name="\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-\_-", value="\n")
        embed2.add_field(name=f"-Variant {i}-", value=item, inline=False)
        i += 1

    embed2.set_thumbnail(url="https://imgur.com/PekVEte.png")
    embed2.set_footer(text="Created by Pownin | DasOfTheBroken | BurntKurisu",
                      icon_url="https://imgur.com/Mz2kaCE.png")
    return embed2


@bot.event
async def on_raw_reaction_add(payload):

    # Check if the reaction was added to a bot message
    response = requests.get(
        "https://63df0e2159bccf35daae0f80.mockapi.io/CGB")

    json_data = response.json()

    # Extract the custom game array from the API response
    custom_game_array = None
    if isinstance(json_data, list) and len(json_data) > 0:
        obj = json_data[0]
        if isinstance(obj, dict) and '2' in obj:
            custom_game_array = obj['2'][1]

    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = await bot.fetch_user(payload.user_id)
    if user.bot:
        return
    emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "8️⃣", "9️⃣", "🔟"]
    i = 0
    for emoji in emoji_list:
        if str(payload.emoji) == emoji:
            message_embed = message.embeds[0]
            s = message_embed.fields[i].value
            embed = new_embed(custom_game_array, s)
            await user.send(embed=embed, delete_after=30)
        i += 2

# Displays Halo 3 games


# @bot.command()
# @commands.cooldown(1, COOLDOWN_TIME, commands.BucketType.user)
# @commands.has_role("CGBFix")  # Check if the user has the role
# async def halo3(ctx):
#     channel = ctx.channel

#     async def delete_message():
#         await asyncio.sleep(0)

#         await ctx.message.delete()
#     bot.loop.create_task(delete_message())
#     await display_custom_games(channel, "$HALO_3_TITLE", jumps_filter=True)


# @halo3.error
# async def halo3_error(ctx, error):
#     if isinstance(error, commands.MissingRole):
#         await ctx.send("Sorry, you do not have permissions to use this command.")

# # Displays Halo Reach games


# @bot.command()
# @commands.cooldown(1, COOLDOWN_TIME, commands.BucketType.user)
# @commands.has_role("CGBFix")  # Check if the user has the role
# async def haloreach(ctx):
#     channel = ctx.channel

#     # Delete the command message after 10 seconds
#     async def delete_message():
#         await asyncio.sleep(0)
#         await ctx.message.delete()

#     bot.loop.create_task(delete_message())
#     await display_custom_games(channel, "$HALO_REACH_TITLE", reach_filter="parkour")


# @haloreach.error
# async def haloreach_error(ctx, error):
#     if isinstance(error, commands.MissingRole):
#         await ctx.send("Sorry, you do not have permissions to use this command.")

@bot.command()
@commands.cooldown(1, COOLDOWN_TIME, commands.BucketType.user)
@commands.has_role("CGBFix")  # Check if the user has the role
async def cgbfix(ctx):
    channel = ctx.channel

    # Delete the command message after 10 seconds
    async def delete_message():
        await asyncio.sleep(0)
        await ctx.message.delete()

    bot.loop.create_task(delete_message())
    while True:

        print(channel)
        tasks = [
            asyncio.create_task(display_custom_games(
                channel, "$HALO_3_TITLE", jumps_filter=True)),
            asyncio.sleep(2),
            asyncio.create_task(display_custom_games(
                channel, "$HALO_REACH_TITLE", reach_filter="parkour"))
        ]

        await asyncio.gather(*tasks)
        print("no")
        await asyncio.sleep(10)


@cgbfix.error
async def cgbfix_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("Sorry, you do not have permissions to use this command.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = error.retry_after
        message = f"This command is on cooldown. Please try again in {seconds:.0f} seconds."
        await ctx.send(message)


# Allows the bot to break each server into a separate message so we do not throw a discord limit error
async def send_large_message(channel, messages):
    for message in messages:
        await channel.send(embed=message)


# Establishes the command for the bot to let everyone know when the server is going down. Will update it so only a specific role can use it. This command is just for the devs. It will never
# be used in any other server but the devs testing server
@bot.command()
async def messageserver(ctx, *, custom_message: str):
    command_invoked_guild = ctx.guild
    command_invoked_channel = ctx.channel

    for guild in bot.guilds:
        if guild == command_invoked_guild:
            target_channel = command_invoked_channel
        else:
            target_channel = None
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    target_channel = channel
                    break

        if target_channel is not None:
            try:
                await target_channel.send(custom_message)
            except discord.errors.Forbidden:
                print(
                    f"Unable to send message to {guild.name} due to insufficient permissions.")
                continue


# @bot.command()
# async def Quadwing(ctx):
#     embed = discord.Embed(title="Congratulations!",
#                           description=f"{ctx.author.mention} has discovered the secret command and wins a $20 gift card!", color=discord.Color.green())
#     embed.set_footer(text="Remember drugs are bad... But fun.")
#     await ctx.send(embed=embed)


# Template for specific server command.
# @bot.command()
# async def neww(ctx):
#     # Check if the command was invoked in the allowed server
#     if ctx.guild.id != BuddyBotty:
#         await ctx.send("This command can only be used in the allowed server.")
#         return
#     embed = discord.Embed(title="Congratulations!",
#                           description=f"{ctx.author.mention} has discovered the secret command and wins a $20 gift card!", color=discord.Color.green())
#     embed.set_footer(text="Remember drugs are bad... But fun.")

#     await ctx.send(embed=embed)


@bot.command()
async def games(ctx):
    # Check if the command was invoked in the allowed server
    if ctx.guild.id != Naraku:
        await ctx.send("This command can only be used in the allowed server.")
        return
    embed = discord.Embed(title="",
                          description=f"{ctx.author.mention} the games command has been retired and no longer works. For Halo 3 use the halo3 command and for Halo Reach use the haloreach command.", color=discord.Color.red())

    await ctx.send(embed=embed)


async def find_channel_with_embeds(guild):
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            messages = []
            async for message in channel.history(limit=10):
                messages.append(message)

            embed_titles = set()
            for message in messages:
                for embed in message.embeds:
                    embed_titles.add(embed.title)
                if len(embed_titles) == 2 and "Halo Reach" in embed_titles and "Halo 3" in embed_titles:

                    return channel


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    channels = []

    for guild_id in servers:
        guild = bot.get_guild(guild_id)
        if guild == None:
            continue
        channel = await find_channel_with_embeds(guild)
        if channel == None:

            continue
        channels.append(channel)
        print(channels)

    if channels == None:
        pass
    elif channels:
        while True:

            for channel in channels:
                o = 70/len(channels)
                print(channel)
                tasks = [
                    asyncio.create_task(display_custom_games(
                        channel, "$HALO_3_TITLE", jumps_filter=True)),
                    asyncio.sleep(2),
                    asyncio.create_task(display_custom_games(
                        channel, "$HALO_REACH_TITLE", reach_filter="parkour"))
                ]
                print(channel)
                await asyncio.gather(*tasks)
                await asyncio.sleep(o)


@bot.event
async def on_message(message):
    await bot.process_commands(message)


bot.run(TOKEN)