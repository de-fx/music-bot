import os
import psutil
import random
import asyncio
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import aiohttp

class Arle(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.queue = asyncio.Queue() # Queue to store the songs
        self.last_search = None
        
    async def stream_audio(self, search: str):
        loop = asyncio.get_event_loop()
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'auto',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(search, download=False))
                url = info_dict['entries'][0]['url']
                title = info_dict['entries'][0]['title']
                return url, title
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

    async def play_song(self, ctx, url, title):
        try:
            ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=url), after=lambda e: self.bot.loop.create_task(self.start_playing(ctx)) if e is None else print(f'Error playing audio: {e}'))
            await ctx.send(f'Now playing:\n**{title}**')
        except Exception as e:
            await ctx.send(f'Error playing audio stream: {e}')

    async def start_playing(self, ctx):
        while not self.queue.empty():
            url, title = await self.queue.get()
            await self.play_song(ctx, url, title)

            # Fetch lyrics for the currently playing song
            try:
                artist, song = title.split('-', 1)
                lyrics = await asyncio.wait_for(self.get_lyrics(artist.strip(), song.strip()), timeout=10)
                if lyrics is None or lyrics == 'Cannot find lyrics':
                    await ctx.send('Cannot find lyrics for this song.')
                else:
                    lyrics = lyrics.replace('Paroles de la chanson', '')  # Remove the lyrics source
                    lyrics = lyrics.replace('par', '|') 
                    await ctx.send(f'Lyrics -{lyrics}')
            except asyncio.TimeoutError:
                print(f'Timeout error getting lyrics for {title}')
            except Exception as e:
                print(f'Error finding lyrics: {e}')

    @commands.command(name='play', help='Plays music from YouTube')
    async def play(self, ctx, *, search):
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
            url, title = await self.stream_audio(search)
        except Exception as e:
            await ctx.send(f'Error getting audio stream: {e}')
            return
        # Add the song to the queue 
        await self.queue.put((url, title))
        # Start playing the song if not already playing
        if not ctx.voice_client.is_playing():
            await self.start_playing(ctx)

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
                url, title = await self.stream_audio(self.last_search)
                ctx.voice_client.play(FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=url))
                await ctx.send(f'Replaying :\n**{title}**')
            except Exception as e:
                await ctx.send(f'Error replaying audio file: {e}')
        else:
            await ctx.send('No track has been played yet to replay.')

    @commands.command(name='stop', help='Stops playing music')
    async def stop(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await ctx.send('The bot is not playing any audio or not connected to a voice channel.')

    # Queue system
    @commands.command(name='add', help='Adds a song to the queue')
    async def add(self, ctx, *, search):
        try:
            url, title = await self.stream_audio(search)
        except Exception as e:
            await ctx.send(f'Error getting audio stream: {e}')
            return

        # Add the song to the queue
        await self.queue.put((url, title))
        await ctx.send(f'{title} - added to queue')

    @commands.command(name='shuffle', help='Shuffles the songs in the queue')
    async def shuffle(self, ctx):
        if self.queue.empty():
            await ctx.send('The queue is empty.')
            return

        # Convert the queue to a list, shuffle it, and then convert it back to a queue
        queue_list = list(self.queue._queue)
        random.shuffle(queue_list)
        self.queue._queue = asyncio.Queue()
        for item in queue_list:
            self.queue._queue.put_nowait(item)

        await ctx.send('The queue has been shuffled.')

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

# Check CPU usage
cpu_percent = psutil.cpu_percent()
print(f'CPU Usage: {cpu_percent}%')

# Check memory usage
memory_percent = psutil.virtual_memory().percent
print(f'Memory Usage: {memory_percent}%')

# Run the bot
if __name__ == '__main__':
    bot.run(os.getenv('Arle'))
