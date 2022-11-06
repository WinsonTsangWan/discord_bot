import os
import discord
import random
import urllib
import re
import youtube_dl
from discord_bot_queue import Queue
from datetime import timedelta

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('SERVER_NAME')
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

AUTOMOD = True
QUEUE = Queue()

# TO DO:
# 1. make music queue (!play, !repeat, !clear)
# 2. switch from ffmpeg to lavalink or opus (?)
# 3. support music playback for spotify
# 4. implement automod

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

@bot.event
async def on_message(message):
    if AUTOMOD:
        msg = message.content.lower()
        author = message.author
        if author != bot:
            fuck = re.findall(r"\b(f+\s*u+\s*c+\s*k+)", msg)
            shit = re.findall(r"\b([s5\s*]+h+\s*[i1!\s*]+\s*t+)", msg)
            bitch = re.findall(r"\b(b+\s*[i1!\s*]+\s*t+\s*c+\s*h+)", msg)
            ass = re.findall(r"\b([a4]+[s5]{2,})", msg)
            retard = re.findall(r"\b(r+\s*[e3\s*]+\s*t+[a4\s*]+r+\s*d+)", msg)
            n_word = re.findall(r"\b(n+\s*[i1!\s*]+g\s*g+\s*[e3\s*]+\s*r+)\b", msg)
            if n_word:
                await message.channel.send("Hey no racism :(")
                # await author.timeout(timedelta(minutes = 10))
            elif retard:
                await message.channel.send("Hey not cool man :^<")
                # await author.timeout(timedelta(minutes = 5))
            elif fuck or shit or bitch or ass:
                await message.channel.send("Hey stop that >:^(")
                # await author.timeout(timedelta(minutes = 1))
            await bot.process_commands(message)
"""
Overriding the default on_message() function prevents additional 
commands from running. If we want to use the @bot.command() 
functionality of BOT as well as on_message(), then we need to 
add bot.process_commands(msg) to ensure that the bot still performs
commands.
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
        # await ctx.send(f"Connected to {voice_client.channel.name}.")
    return voice_client

@bot.command(name = "leave", category = "music", help = "Disconnects bot from current voice channel.")
async def leave(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client != None and voice_client.is_connected:
        await voice_client.disconnect()
        await ctx.send(f"Disconnected from {voice_client.channel.name}")
    else:
        await ctx.send("Voice client not connected. No need to disconnect.")

@bot.command(name = "pause", category = "music", help = "Pauses current playing song.")
async def pause(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.message.channel.send("Music paused.")
    else:
        await ctx.message.channel.send("No music currently playing. No need to pause.")

@bot.command(name = "resume", category = "music", help = "Resumes paused song.")
async def resume(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
        await ctx.message.channel.send("Music resuming.")
    else:
        await ctx.message.channel.send("Music not currently paused. No need to resume.")

@bot.command(name = "skip", category = "music", help = "Stops current song and advances to next song in queue.")
async def skip(ctx):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing:
        if QUEUE.size > 0:
            next_song_info = QUEUE.next_song()
            title = next_song_info.get("title")
            URL = next_song_info.get("url")
            page_URL = next_song_info.get("page_url")
            await ctx.send(f"Song skipped. Now playing: **{title}**\n" + page_URL)
            voice_client.source = discord.FFmpegOpusAudio(URL, **FFMPEG_OPTIONS)
        else:
            await ctx.send("No more music in queue.")
            voice_client.stop()
    else:
        await ctx.send("No music currently playing. No need to skip.")

@bot.command(name = "clear", category = "music", help = "Clears music queue.")
async def clear(ctx):
    QUEUE.clear()
    await ctx.send("Queue cleared.")

@bot.command(name = "queue", category = "music", help = "Displays current music queue.")
async def show_queue(ctx):
    res = f"> __**QUEUE**__\n> Now Playing: {QUEUE.curr_song_info.get('title')}\n> Next Up:\n"
    for index, info in enumerate(QUEUE.queue):
        res += f"> {index + 1}.  " + info.get("title") + "\n"
    await ctx.send(res)

@bot.command(name = "history", category = "music", help = "Displays song history.")
async def show_history(ctx):
    res = f"> __**HISTORY**__\n"
    for index, info in enumerate(QUEUE.history):
        res += f"> {index + 1}.  " + info.get("title") + "\n"
    await ctx.send(res)

@bot.command(name = "play", category = "music", help = "Plays a song from a Youtube video with input title.")
async def play_music(ctx):
    voice_client = await join(ctx)
    next_song_title = QUEUE.add_song(ctx)

    # Play audio from downloaded Youtube video
    if voice_client.is_playing() or voice_client.is_paused():
        await ctx.send("Song added to queue.")
    else:
        next_song_info = QUEUE.next_song()
        page_URL = next_song_info.get("page_url")
        URL = next_song_info.get("url")
        title = next_song_info.get("title")
        await ctx.send(f"Now playing: **{title}**\n" + page_URL)
        voice_client.play(discord.FFmpegOpusAudio(URL, **FFMPEG_OPTIONS))

@bot.command(name = "repeat", category = "music", help = "Repeats the current song n times")
async def repeat(ctx, n=1):
    guild = ctx.message.guild
    voice_client = guild.voice_client
    if voice_client.is_playing():
        QUEUE.queue.insert(0, QUEUE.curr_song_info)

bot.run(TOKEN) 
