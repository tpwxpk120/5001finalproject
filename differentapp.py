import asyncio
import discord
from discord.ext import commands
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
    """
    Represents a playable audio source, derived from the discord.PCMVolumeTransformer class.

    Args:
        source (discord.AudioSource): The audio source being passed to the class.
        data (dict): A dictionary containing the song data.
        volume (float): The volume level of the audio source, defaults to 0.5.
    Attributes:
        data (dict): A dictionary containing the song data.
        title (str): The title of the audio source.
        url (str): The URL of the audio source.    
    """
    def __init__(self, source, *, data, volume = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
    
    """
    Methods:
    from_url(cls, url, *, loop = None, stream = False): 
    A class method that extracts the song using YoutubeDL in a separate thread and returns the filename 
    of the song based on whether it's a stream or a file.
    
    Usage:
    To use this class, you need to pass a discord.AudioSource to the class constructor along with the song data in a 
    dictionary format. You can also specify the volume level of the audio source. Additionally, there is a class 
    method named from_url that takes in the URL of the song and returns the filename of the song based on whether it's 
    a stream or a file.
    """
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
    """
    Event handler for when the bot is ready. This function is called automatically when the bot is fully loaded 
    and ready to execute commands.
    """
    print("|Bot is ready.|")


#Function to show the playlist
async def show_playlist(msg):
    """
    An asynchronous function that shows the playlist to the user.
    
    Args:
        msg (discord.Message): The Discord message object.
    """
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
    """
    A command that makes the bot join the voice channel that the user is currently connected to.
    
    Args:
        msg (discord.Message): The Discord message object.
    """
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
    """
    A command that plays all the songs in the queue automatically.
   
    Args:
        msg (discord.Message): The Discord message object.
    """
    try:
        channel = msg.message.guild.voice_client
        try:
            while len(queue) > 0:
                #Get the next song from the queue
                filename = queue.pop(0)
                #Play all the song in the queue automatically
                channel.play(discord.FFmpegPCMAudio(
                    executable = "ffmpeg.exe", source = filename), after = lambda x: asyncio.run_coroutine_threadsafe(play_song(msg), bot.loop))
                await msg.send('——Now playing: {}'.format(filename))
                #Wait for the song to finish playing
                while channel.is_playing():
                    await asyncio.sleep(1)
        except Exception as err:
            print("Something wrong with play function")
    except Exception as err:
        print("Something wrong with user sending")


#Command to add a song to the queue
@bot.command(name = 'addq', help = 'Add a song to the list')
async def enqueue(msg, url=None):
    """
    Adds a song to the queue.
    
    Args:
        msg: The message object that triggered the command.
        url(str): The URL or name of the song to add to the queue.
    """
    try:
        if url is None:
            raise commands.MissingRequiredArgument(commands.ParamInfo(
                'url', 'Please provide a valid URL or name of Song'))
        else:
            # Get the filename of the song from the url and add it to the queue
            filename = await YTDLSource.from_url(url)
            queue.append(filename)
            await msg.send('Added to queue')
    except commands.MissingRequiredArgument as e:
        await msg.send(str(e))
    except Exception as err:
        print("Add to queue failed")
        await msg.send('Add to queue failed, and please provide a valid URL or name of Song')


#Command to resume the currently paused song
@bot.command(name = 'pauses', help = 'This command pauses the song')
async def pause(msg):
    """
    Pauses the currently playing song.
    
    Args:
        msg: The message object that triggered the command.
    """
    try: 
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the client is currently playing a song, pause it
        if channel.is_playing():
            channel.pause()
            await msg.send("The bot is paused")
        else:
            #Otherwise, inform the user that the bot is already paused
            await msg.send("No music.")
    except Exception as err:
        print("Pause failed")


#Command to resume the currently paused song
@bot.command(name = 'resumes', help = 'Resumes the song')
async def resume(msg):
    """
    Resumes playing the currently paused song.
    
    Args:
        msg: The message object that triggered the command.
    """
    try:
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the client is currently paused, resume playing the song
        if channel.is_paused():
            channel.resume()
            await msg.send("Song stoped will replay")
        #Otherwise, inform the user that there is no paused song to resume
        else:
            await msg.send("No music.")
    except Exception as err:
        print("Resume failed")


#Command to make the bot leave the voice channel
@bot.command(name = 'leave', help = 'To make the bot leave the voice channel')
async def leave(msg):
    """Disconnects the bot from the voice channel.

    Args:
        msg: The message object that triggered the command.
    """
    try:
        #Get the voice client for the guild the message was sent from
        channel = msg.message.guild.voice_client
        #If the bot is connected to a voice channel, disconnect it
        if channel.is_connected():
            # Bot disconnects to the channel
            await channel.disconnect()
            await msg.send("The bot leaved")
        else:
            await msg.send("The bot is not here")
    except AttributeError as err:
        print("The bot is not connected to a voice channel.")


#Command to stop current music
@bot.command(name = 'stops', help = 'Stops the song')
async def stop(msg):
    """
    Stops the currently playing song.

    Args:
        msg: The message object that triggered the command.
    """
    try:
        #Get the voice client for the guild where the message was sent
        channel = msg.message.guild.voice_client
        #Check if the bot is currently playing audio
        if channel.is_playing():
            #Stop playing the current audio
            channel.stop()
        else:
            #If the bot is not playing any audio, send a message saying so
            await msg.send("No music will play")
    except Exception as err:
        print("Bot did not stop.")


#Command to display the current playlist
@bot.command(name = 'playlist', help = 'Displays the current playlist')
async def display_playlist(msg):
    """
    Displays the current playlist.
    Args:
        msg: The message object that triggered the command.
    """
    await show_playlist(msg)


if __name__ == "__main__" :
    bot.run(key)
