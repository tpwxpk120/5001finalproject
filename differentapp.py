import asyncio
import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
import yt_dlp as youtube_dl

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='/',intents=intents)
key = ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename
    

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")


@bot.command(name= 'join', help= 'Tells the bot to join the voice channel')
async def join(ctx):
    try:
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()
    except Exception as err:
        print("Bot is not connect")

@bot.command(name= 'play', help= 'To play song')
async def play(ctx, url):
    try:
        server = ctx.message.guild
        channel = server.voice_client
        try:
            async with ctx.typing():
                try:
                    filename = await YTDLSource.from_url(url, loop=bot.loop)
                    channel.play(discord.FFmpegPCMAudio(
                        executable="ffmpeg.exe", source=filename))
                    await ctx.send('**Now playing:** {}'.format(filename))
                except Exception as err:
                    print("ffmpeg.exe is not found.")
            await ctx.send('**Now playing:** {}'.format(filename))
        except Exception as err:
            print("file is not found.")
    except Exception as err:
        print("Bot is not playing.")


@bot.command(name= 'pause', help= 'This command pauses the song')
async def pause(ctx):
    try:
        client = ctx.message.guild.voice_client
        if client.is_playing():
            await client.pause()
        else:
            await ctx.send("The bot is paused")
    except Exception as err:
        print("Player did not pause.")
    
@bot.command(name= 'resume', help= 'Resumes the song')
async def resume(ctx):
    try:
        client = ctx.message.guild.voice_client
        if client.is_paused():
            await client.resume()
        else:
            await ctx.send("Song stoped will replay")
    except Exception as err:
        print("Player did not resume well.")


@bot.command(name= 'leave', help= 'To make the bot leave the voice channel')
async def leave(ctx):
    try:
        client = ctx.message.guild.voice_client
        if client.is_connected():
            await client.disconnect()
        else:
            await ctx.send("The bot leaved")
    except Exception as err:
        print("Bot did not leave.")


@bot.command(name= 'stop', help= 'Stops the song')
async def stop(ctx):
    try:
        client = ctx.message.guild.voice_client
        if client.is_playing():
            await client.stop()
        else:
            await ctx.send("No music will play")
    except Exception as err:
        print("Bot did not stop.")


if __name__ == "__main__" :
    bot.run(key)
