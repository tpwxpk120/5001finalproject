import asyncio
import discord
from discord.ext import commands,tasks
import yt_dlp as youtube_dl


key = 'Your Token'
intents = discord.Intents().all()
client = discord.Client(intents = intents)

#Initializing the bot and "/" need to add before any bot command.
bot = commands.Bot(command_prefix='/', intents = intents)

#Set an empty queue for music list 
queue = []


# Setting up the YoutubeDL object with some configuration options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

#The YTDLSource class that represents a playable audio source
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()
        #Extract the song using YoutubeDL in a separate thread
        link = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download = not stream))
        if 'entries' in link:
            # take first item from a playlist
            link = link['entries'][0]
        #Get the filename of the song based on whether it's a stream or a file
        filename = link['title'] if stream else ytdl.prepare_filename(link)
        return filename


#Event handler for when the bot is ready
@bot.event
async def on_ready():
    print("|Bot is ready.|")


#Function to show the playlist
async def show_playlist(msg):
    try:
        #Join the songs in queue into a string with index number for each song
        playlist = ""
        if len(queue) == 0:
            #If the playlist is currently empty
            playlist = "The playlist is currently empty."
            await msg.send("The playlist is currently empty.")
        else:
            for i, song in enumerate(queue):
                #Add each song to the playlist string with its index number
                playlist += f"{i+1}. {song}\n"
                await msg.send(f"Playlist:\n{playlist}")
    except Exception as err:
        print("Playlist has error")


#Command to make the bot join the voice channel
@bot.command(name = 'join', help = 'Tells the bot to join the voice channel')
async def join(msg):
    try:
        #Bot joins the voice channel that the user is currently connected to
        channel = msg.author.voice.channel
        await channel.connect()
    except AttributeError:
        #If the user is not connected to a voice channel
        await msg.send("{} is not connected to a voice channel".format(msg.author.name))
    except Exception as err:
        #If it it not problem of user, check the bot
        print("Bot is not connect")


#Command to play a song
@bot.command(name = 'plays', help = 'To play song')
async def play_song(msg):
    try:
        server = msg.message.guild
        voice_channel = server.voice_client
        try:
            while len(queue) > 0:
                #Get the next song from the queue
                filename = queue.pop(0)
                #Play all the song in the queue automatically
                voice_channel.play(discord.FFmpegPCMAudio(
                    executable = "ffmpeg.exe", source = filename), after = lambda x: asyncio.run_coroutine_threadsafe(play_song(msg), bot.loop))
                await msg.send('——Now playing: {}'.format(filename))
                #Wait for the song to finish playing
                while voice_channel.is_playing():
                    await asyncio.sleep(1)
        except Exception as err:
            print("Something wrong with play function")
    except Exception as err:
        print("Something wrong with user sending")


#Command to add a song to the queue
@bot.command(name = 'addq', help = 'Add a song to the list')
async def enqueue(msg, url):
    async with msg.typing():
        try:
            #Get the filename of the song from the url and add it to the queue
            filename = await YTDLSource.from_url(url)
            queue.append(filename)
            await msg.send('Added to queue')
        except Exception as err:
            print("Add to queue failed")


#Command to resume the currently paused song
@bot.command(name = 'pauses', help = 'This command pauses the song')
async def pause(msg):
    try:
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the client is currently playing a song, pause it
        if channel.is_playing():
            await channel.pause()
        else:
            #Otherwise, inform the user that the bot is already paused
            await msg.send("The bot is paused")
    except Exception as err:
        print("Player did not pause.")


#Command to resume the currently paused song
@bot.command(name = 'resumes', help = 'Resumes the song')
async def resume(msg):
    try:
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the client is currently paused, resume playing the song
        if channel.is_paused():
            await channel.resume()
        #Otherwise, inform the user that there is no paused song to resume
        else:
            await msg.send("Song stoped will replay")
    except Exception as err:
        print("Player did not resume well.")


#Command to make the bot leave the voice channel
@bot.command(name = 'leave', help = 'To make the bot leave the voice channel')
async def leave(msg):
    try:
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the bot is connected to a voice channel, disconnect it
        if channel.is_connected():
            # Bot disconnects to the channel
            await channel.disconnect()
        #Otherwise, inform the user that the bot has already left the channel
        else:
            await msg.send("The bot leaved")
    except Exception as err:
        print("Bot did not leave.")


#Command to stop current music
@bot.command(name = 'stops', help = 'Stops the song')
async def stop(msg):
    try:
        #Get the voice client for the guild where the message was sent
        channel = msg.message.guild.voice_client
        #Check if the bot is currently playing audio
        if channel.is_playing():
            #Stop playing the current audio
            await channel.stop()
        else:
            #If the bot is not playing any audio, send a message saying so
            await msg.send("No music will play")
    except Exception as err:
        print("Bot did not stop.")


#Command to display the current playlist
@bot.command(name = 'playlist', help = 'Displays the current playlist')
async def display_playlist(msg):
    await show_playlist(msg)


if __name__ == "__main__" :
    bot.run(key)
