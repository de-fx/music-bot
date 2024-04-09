import os
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import aiohttp
from collections import deque
class Arle(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)    
        self.bot = bot
        self.current_filename = None
        self.last_search = None 
        self.queue = deque()

    async def download_audio(self, search: str):
        loop = asyncio.get_event_loop()
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
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(search, download=True))
                filename = ydl.prepare_filename(info_dict['entries'][0]).replace('.webm', '.mp3')
                title = info_dict['entries'][0]['title']
                return filename, title
        except Exception as e:
            raise e

    async def get_lyrics(self, artist, title):
        url = f'https://api.lyrics.ovh/v1/{artist}/{title}'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return "Cannot find lyrics"
                    json_response = await response.json()
                    if 'lyrics' not in json_response:
                        return "Cannot find lyrics"
                    return json_response['lyrics']
            except aiohttp.ClientError as e:
                print(f"Error getting lyrics: {e}")
                return "Cannot find lyrics"

    @commands.command(name='play', help='Plays music from YouTube')
    async def play(self, ctx, *, search):

        if search is None and len(self.queue) > 0:
            search = self.queue.popleft()
        elif search is None and len(self.queue) == 0:
            await ctx.send('No song to play.')
            return
        
        self.last_search = search

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
            try:
                os.remove(filename)
            except PermissionError:
                pass
            print(f'Deleted audio file: {filename}')
            if len(self.queue) > 0:
                next_search = self.queue.popleft()
                asyncio.run_coroutine_threadsafe(self.play(ctx, search=next_search), self.bot.loop)
        self.current_filename = None
        
        try:
            ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=filename), after=after_playing)
            await ctx.send(f'Now playing:\n**{title}**')
            print(f'Filename of the currently playing track: {filename}')    
        except Exception as e:
            await ctx.send(f'Error playing audio file: {e}')
        self.current_filename = filename

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
            ctx.voice_client.stop()
            try:
                filename, title = await self.download_audio(self.last_search)
                ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=filename))
                await ctx.send(f'Replaying :\n**{title}**')
            except Exception as e:
                await ctx.send(f'Error replaying audio file: {e}')
        else:
            await ctx.send('No track has been played yet to replay.')
                

    @commands.command(name='stop', help='Stops playing music and deletes the audio file')
    async def stop(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            current_filename = self.current_filename
            ctx.voice_client.stop()

            while ctx.voice_client.is_playing():
                await asyncio.sleep(1) 
            await asyncio.sleep(1)
            try:
                if current_filename and os.path.exists(current_filename):
                    os.remove(current_filename)
                    self.current_filename = None
                else:
                    await ctx.send('Error: Audio file not found or filename not set.')
            except Exception as e:
                await ctx.send(f'Error deleting audio file: {e}')
        else:
            await ctx.send('The bot is not playing any audio or not connected to a voice channel.')
    
    @commands.command(name='add', help='Adds a song to the queue')
    async def add(self, ctx, *, search):
        # Split the input string by commas to get a list of songs
        songs = [song.strip() for song in search.split(',')]
    
        # Add each song to the queue
        for song in songs:
            self.queue.append(song)
            await ctx.send(f'Added to queue: {song}')
    @commands.command(name='queue', help='Displays the current queue')
    async def queue(self, ctx):
        if len(self.queue) == 0:
            await ctx.send('The queue is empty.')
        else:
            queue_list = '\n'.join([f'{i+1}. {song}' for i, song in enumerate(self.queue)])
            await ctx.send(f'Queue:\n{queue_list}')


    @commands.command(name='lyrics', help='Displays the lyrics of the currently playing song')
    async def lyrics(self, ctx,*, search):
        parts = search.split('-', 1)
        if len(parts) != 2:
            await ctx.send('Please provide the artist and song title in the format "artist - song".')
            return
        try:
            artist, song = search.split('-', 1)
            lyrics = await asyncio.wait_for(self.get_lyrics(artist.strip(), song.strip()), timeout=10)
            if lyrics is None or lyrics == 'Cannot find lyrics':
                await ctx.send('Cannot find lyrics for this song.')
            else:
                lyrics = lyrics.replace('Paroles de la chanson', '')  # Remove the lyrics source
                lyrics = lyrics.replace('par', '|') 
                await ctx.send(f'Lyrics -{lyrics}')
        except asyncio.TimeoutError:
                print(f'Timeout error getting lyrics for {search}')
        except Exception as e:
            print(f'Error finding lyrics: {e}')
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