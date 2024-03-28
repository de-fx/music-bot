import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import requests


class Arle(commands.Cog):


    def __init__(self, bot):
        self.bot = bot
        self.current_filename = None
        
    async def download_audio(self, search):
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
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(search, download=True)
                filename = ydl.prepare_filename(info_dict['entries'][0]).replace('.webm', '.mp3')
                title = info_dict['entries'][0]['title']
                return filename, title, 
        except Exception as e:
            raise e


    def get_lyrics(self, artist, title):
        response = f'https://api.lyrics.ovh/v1/{artist}/{title}'
        data = requests.get(response).json()
        return data['lyrics']


    @commands.command(name='play', help='Plays music from YouTube')
    async def play(self, ctx, *, search: str):
        #Store the search query for replay command
        self.last_played_search_query = search
        if ctx.author.voice is None:
            await ctx.send('You are not connected to a voice channel.')
            return
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

        try:
            filename, title = await self.download_audio(search)
        except Exception as e:
            await ctx.send(f'Error downloading audio file: {e}')
            return

        def after_playing(error):
            if error:
                print(f'Error playing audio file: {error}')
                return
            os.remove(filename)
        self.current_filename = None
        
        try:
            ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=filename), after=after_playing)
            await ctx.send(f'Now playing: \n{title}')
            # Print the filename for debugging
            print(f'Filename of the currently playing track: {filename}')    
        except Exception as e:
            await ctx.send(f'Error playing audio file: {e}')
        self.current_filename = filename

        try:
            lyrics = self.get_lyrics(title.split('-')[0].strip(), title.split('-')[1].strip())
            lyrics = lyrics.replace('Paroles de la chanson', '')
            lyrics = lyrics.replace('par', 'by')
            await ctx.send(f'Lyrics:\n{lyrics}')
        except Exception as e:
            await ctx.send(f'Cannot find lyrics for this song.')

    @commands.command(name='pause', help='Pauses the currently playing music')
    async def pause(self, ctx):
        if ctx.voice_client is not None:
            ctx.voice_client.pause()
        else:
            await ctx.send('The bot is not connected to a voice channel.')


    @commands.command(name='resume', help='Resumes paused music')
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send("Audio is not paused.")


    @commands.command(name='replay', help='Replays the last played track')
    async def replay(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current track
            if hasattr(self, 'last_played_search_query'):
                try:
                    filename, title = await self.download_audio(self.last_played_search_query)
                    ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=filename))
                    await ctx.send(f'Replaying :\n{title}')
                except Exception as e:
                    await ctx.send(f'Error replaying audio file: {e}')
            else:
                await ctx.send('No track has been played yet to replay.')
        else:
            await ctx.send('The bot is not playing any audio.')



    @commands.command(name='stop', help='Stops playing music and deletes the audio file')
    async def stop(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            # Get the currently playing filename
            current_filename = self.current_filename
            ctx.voice_client.stop()

            # Wait for the audio to stop playing
            while ctx.voice_client.is_playing():
                await asyncio.sleep(2)  # Small delay to avoid CPU intensive loop
            await asyncio.sleep(1)  # Additional delay to ensure the audio is completely stopped
            try:
                if current_filename and os.path.exists(current_filename):
                    os.remove(current_filename)
                    self.current_filename = None  # Reset the filename after deletion
                else:
                    await ctx.send('Error: Audio file not found or filename not set.')
            except Exception as e:
                await ctx.send(f'Error deleting audio file: {e}')
        else:
            await ctx.send('The bot is not playing any audio or not connected to a voice channel.')


# Create a bot instance
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)


# Event listener for when the bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.add_cog(Arle(bot))

# Run the bot
if __name__ == '__main__':
    bot.run(os.getenv('Arle')) 

