import os
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from discord import FFmpegPCMAudio


# Create a bot instance
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='join', help='joins the voice channel.')
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel!")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    else:
        await ctx.voice_client.move_to(channel)






@bot.command(name='pause', help='pauses the music.')
async def pause(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.pause()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

@bot.command(name='resume', help='resumes the music.')
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
    else:
        await ctx.send("Audio is not paused.")




@bot.command()
async def play(ctx, *, search: str):
    # Check if the user is in a voice channel
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel!")
        return

    # Connect to the voice channel
    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        try:
            await channel.connect()
        except Exception as e:
            await ctx.send(f'Error connecting to voice channel: {e}')
            return
    else:
        try:
            await ctx.voice_client.move_to(channel)
        except Exception as e:
            await ctx.send(f'Error moving to voice channel: {e}')
            return

    # Download and convert the audio file
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': './Downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'default_search': 'auto',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        if not os.path.exists('./Downloads'):
            os.mkdir('./Downloads')
    except Exception as e:
        await ctx.send(f'Error creating download directory: {e}')
        return
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(search, download=True)
            title = info_dict['entries'][0]['title']
            artist = info_dict['entries'][0]['uploader']
            filename = ydl.prepare_filename(info_dict['entries'][0]).replace('.webm', '.mp3')

    except Exception as e:
        await ctx.send(f'Error downloading audio file: {e}')
        return

    if not os.path.exists(filename):
        await ctx.send(f'Audio file does not exist : {filename}')
        return
    
    def after_playing(error):
        if error:
            print(f'Error playing audio file: {error}')
            return
        os.remove(filename)

    # Play the audio file and delete it when done
    try:
        ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=filename), after=after_playing)
        await ctx.send(f'Now playing :\n{title} | {artist}')    
    except Exception as e:
        await ctx.send(f'Error playing audio file: {e}')


@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send('The bot is not connected to a voice channel.')


@bot.command()
async def stop(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.stop()
    else:
        await ctx.send('The bot is not connected to a voice channel.')

bot.run(os.getenv('Arle'))