import os
import discord
import random
import urllib
import re
import youtube_dl

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('SERVER_NAME')
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

MUSIC_QUEUE = []

"""
BOT is a subclass of CLIENT that offers additional functionality, 
such as commands. BOT handles events the same way that CLIENT does, 
using the @ decorator. Let us use BOT instead of CLIENT here, 
because we are working with a bot user.
"""
# client = discord.Client()                   
bot = commands.Bot(intents = discord.Intents.all(), command_prefix = '!')

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name = GUILD)
    print(f"{bot.user} has connected to {guild.name}!")

@bot.event
async def on_member_join(member):
    guild = discord.utils.get(bot.guilds, name = GUILD)
    print(f"Welcome to {guild.name}, {member.name}!")

"""
Overriding the default on_message() function prevents additional 
commands from running. If we want to use the @bot.command() 
functionality of BOT, then we cannot override on_message().
"""

@bot.command(name = "coin", category = "games", help = "Simulates a coin flip.")
async def flip_coin(ctx):
    msg = ctx.message.content.split()
    if len(msg) > 1:
        await ctx.send("Error: !coin only takes 1 argument.")
    else:
        result = random.choice(["heads", "tails"])
        await ctx.send(f"Coin landed {result}.")

@bot.command(name = "dice", category = "games", help = "Simulates a dice roll with m dice, each with n sides.")
async def dice_roll(ctx, num_dice: int = 1, num_sides: int = 6):
    msg = ctx.message.content.split()
    if len(msg) > 3:
        await ctx.send("Error: !dice takes at most 3 arguments.")
    else:
        await ctx.send([random.choice(range(num_sides)) + 1 for _ in range(num_dice)])

@bot.command(name = "join", category = "music", help = "Connects bot to user's voice channel.")
async def join(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client == None or not voice_client.is_connected():
        user_voice = ctx.message.author.voice
        if user_voice != None:
            voice_client = await user_voice.channel.connect()
        else:
            guild = ctx.message.guild
            general = discord.utils.get(guild.voice_channels, name = "General")
            voice_client = await general.connect()
        await ctx.send(f"Connected to {voice_client.channel.name}.")
    return voice_client

@bot.command(name = "leave", category = "music", help = "Disconnects bot from current voice channel.")
async def leave(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client != None and voice_client.is_connected:
        await voice_client.disconnect()
        await ctx.send(f"Disconnected from {voice_client.channel.name}")
    else:
        await ctx.send("Voice client not connected; no need to disconnect.")

@bot.command(name = "pause", category = "music", help = "Pauses current playing song.")
async def pause(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.message.channel.send("Music paused.")
    else:
        await ctx.message.channel.send("No music currently playing; no need to pause.")

@bot.command(name = "resume", category = "music", help = "Resumes paused song.")
async def resume(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.message.channel.send("Music resuming.")
    else:
        await ctx.message.channel.send("Music not currently paused; no need to resume.")

@bot.command(name = "skip", category = "music", help = "Stops current song and advances to next song in queue.")
async def skip(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing:
        voice_client.stop()
        await ctx.send("Song skipped.")
        if len(MUSIC_QUEUE) != 0:
            curr = MUSIC_QUEUE.pop(0)
            print('__________HERE___________:', curr)
            voice_client.source = discord.FFmpegPCMAudio(curr, **FFMPEG_OPTIONS)
        else:
            await ctx.send("No more music in queue.")
    else:
        await ctx.send("No music currently playing; no need to skip.")

@bot.command(name = "play", category = "music", help = "Plays a song from a Youtube video with input title.")
async def play_music(ctx):
    voice_client = await join(ctx)
    '''
    Search for query on Youtube, get URL of top search result
    '''
    query = "+".join(ctx.message.content.split()[1:])
    url = "https://www.youtube.com/results?search_query=" + query
    search_result_page = urllib.request.urlopen(url)
    video_results = re.findall(r"watch\?v=(\S{11})", search_result_page.read().decode())
    top_result_ID = video_results[0]
    top_result_url = "https://www.youtube.com/watch?v=" + top_result_ID

    with youtube_dl.YoutubeDL(YTDL_OPTIONS) as ytdl:
        info = ytdl.extract_info(top_result_url, download = False)
        URL = info['formats'][0]['url']
        # print("top_result_URL: ", top_result_url)
        # print("URL: ", URL)

    MUSIC_QUEUE.append(URL)
    '''
    Play audio from Youtube video
    '''
    if voice_client.is_playing() or voice_client.is_paused():
        await ctx.send("Music is already playing; song added to queue.")
    else:
        voice_client.play(discord.FFmpegPCMAudio(MUSIC_QUEUE.pop(0), **FFMPEG_OPTIONS))

# @bot.command(name = "clear", category = "music", help = "Clears music queue.")
# async def clear(ctx):
#     return

@bot.command(name = "repeat", category = "music", help = "Repeats the current song n times")
async def repeat(ctx, n=1):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing():
        MUSIC_QUEUE.append()

bot.run(TOKEN) 
