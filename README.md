# Arle Music Bot

Arle is a Discord bot that can play music from YouTube. It supports various commands such as play, pause, resume, replay, and stop.

## Features

- Play music from YouTube in a Discord voice channel.
- Pause, resume, and stop the currently playing music.
- Replay the last played track.
- Automatically cleans up downloaded audio files.

## Commands

- `/play [YouTube URL or search query]`: Plays music from YouTube.
- `/pause`: Pauses the currently playing music.
- `/resume`: Resumes paused music.
- `/replay`: Replays the last played track.
- `/stop`: Stops playing music and deletes the audio file.

## Setup

1. Clone this repository.
2. Install the required Python packages: 
```bash
pip install discord.py yt-dlp
```
3. Download and install [FFmpeg](https://ffmpeg.org/download.html).
4. Add FFmpeg to your system's PATH:
```bash
setx PATH "%PATH%;C:\path\to\ffmpeg\bin"
```
Replace `C:\path\to\ffmpeg\bin` with the actual path to the `bin` directory in your FFmpeg installation.
5. Set 'Arle' environment variable to your Discord Bot Token.
```bash
setx DISCORD_TOKEN "your-bot-token"
```
6. Run 'bot.py'

## Note

This bot requires the `ffmpeg` executable to be installed and its path to be specified in the `FFmpegPCMAudio` call in the `play` command.

## License

This project is licensed under the MIT License.