import asyncio
import discord
import requests
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from lyricsgenius import Genius
from config import config
from cogs.Music.song_queue import Queue
from cogs.Music.song_queue import Song

############-CONFIGS-##########################################################################################

if config.tokens.genius_token:
    genius = Genius(access_token=config.tokens.genius_token, remove_section_headers=True)

if config.tokens.spotify_id and config.tokens.spotify_secret:
    client_credentials_manager = SpotifyClientCredentials(config.tokens.spotify_id, config.tokens.spotify_secret)
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

############-MUSIC COMMANDS-###################################################################################

queue_dict = {}


class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-PLAY COMMAND-#####################################################################################

    @commands.command(name="play")
    async def play(self, ctx, *arg):

        arg = ' '.join(arg)

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if ctx.guild.id not in queue_dict:
            queue_dict[ctx.guild.id] = Queue(
                songs=[],
                current_pos=0,
                loop=False,
                voice=voice,
                bot=self.bot,
                ctx=ctx
            )

        song_list = []
        if arg.startswith("https://open.spotify.com/playlist"):
            for i in spotify.playlist(playlist_id=arg)['tracks']['items']:
                song = f"{i['track']['name']} - {i['track']['album']['artists'][0]['name']}"
                song_list.append(song)

        elif arg.startswith("https://open.spotify.com/album"):
            for i in spotify.album(arg)['tracks']['items']:
                song = f"{i['name']} - {i['artists'][0]['name']}"
                song_list.append(song)

        elif arg.startswith("https://open.spotify.com/track"):
            track = spotify.track(track_id=arg)
            song = f"{track['name']} - {track['album']['artists'][0]['name']}"
            song_list.append(song)

        if song_list != []:
            for song in song_list:
                with yt_dlp.YoutubeDL({'fragment_count': '64', 'extract_flat': True, 'format': 'bestaudio/best', 'downloader': 'aria2c', 'skip_download': True, 'dump_single_json': True}) as ydl:
                    try:
                        requests.get(song)
                    except Exception as e:
                        print(e)
                        info = ydl.extract_info(f"ytsearch:{song}", download=False)
                    else:
                        info = ydl.extract_info(song, download=False)

                    if 'entries' in info.keys():
                        for entry in info['entries']:
                            await asyncio.sleep(.1)

                            song = Song(
                                title=entry['title'],
                                url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                                number_in_queue=queue_dict[ctx.guild.id].len() + 1
                            )

                            queue_dict[ctx.guild.id].enqueue(song)

                    else:
                        song = Song(
                            title=info['title'],
                            url=info['webpage_url'],
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )
                        queue_dict[ctx.guild.id].enqueue(song)
                    if voice.is_playing():
                        pass
                    else:
                        await queue_dict[ctx.guild.id].play_next()
        # handling youtube links
        elif arg.startswith("https://music.youtube.com") or arg.startswith("https://www.youtube.com"):
            with yt_dlp.YoutubeDL({'fragment_count': '64', 'extract_flat': True, 'format': 'bestaudio/best', 'downloader': 'aria2c', 'skip_download': True, 'dump_single_json': True}) as ydl:
                try:
                    requests.get(arg)
                except Exception as e:
                    print(e)
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                else:
                    info = ydl.extract_info(arg, download=False)

                if 'entries' in info.keys():
                    for entry in info['entries']:
                        await asyncio.sleep(.1)

                        song = Song(
                            title=entry['title'],
                            url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )

                        queue_dict[ctx.guild.id].enqueue(song)

                else:
                    song = Song(
                        title=info['title'],
                        url=info['webpage_url'],
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    queue_dict[ctx.guild.id].enqueue(song)
        # handling queries that arent links
        else:
            with yt_dlp.YoutubeDL({'fragment_count': '64', 'extract_flat': True, 'format': 'bestaudio/best', 'downloader': 'aria2c', 'skip_download': True, 'dump_single_json': True}) as ydl:
                try:
                    requests.get(arg)
                except Exception as e:
                    print(e)
                    info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                else:
                    info = ydl.extract_info(arg, download=False)

                if 'entries' in info.keys():
                    for entry in info['entries']:
                        await asyncio.sleep(.1)

                        song = Song(
                            title=entry['title'],
                            url=entry['url'].removesuffix('#__youtubedl_smuggle=%7B%22is_music_url%22%3A+true%7D'),
                            number_in_queue=queue_dict[ctx.guild.id].len() + 1
                        )

                        queue_dict[ctx.guild.id].enqueue(song)

                else:
                    song = Song(
                        title=info['title'],
                        url=info['webpage_url'],
                        number_in_queue=queue_dict[ctx.guild.id].len() + 1
                    )
                    queue_dict[ctx.guild.id].enqueue(song)

        if voice.is_playing() is True:
            pass
        else:
            if queue_dict[ctx.guild.id].end_of_queue is True:
                await queue_dict[ctx.guild.id].play_last()
            else:
                await queue_dict[ctx.guild.id].play_next()
            queue_dict[ctx.guild.id].voice.resume()

############-QUEUE COMMAND-####################################################################################

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):

        embed_list = []

        if ctx.guild.id in queue_dict:
            for x in queue_dict[ctx.guild.id].songs:
                if x.number_in_queue == queue_dict[ctx.guild.id].current_pos:
                    embed_list.append(f'-> {x.number_in_queue} - {x.title}')
                else:
                    embed_list.append(f'{x.number_in_queue} - {x.title}')

            embed_desc = '\n'.join(
                f'{x}'
                for x in embed_list)

            embed_to_send = discord.Embed(
                title="Queue",
                description=embed_desc
            )
            await ctx.send(embed=embed_to_send)
        else: 
            await ctx.send("Nothing is playing.")

############-NOWPLAYING COMMAND-###############################################################################

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx):

        embed_to_send = discord.Embed(
            title="Now playing",
            description=f"""Title: {queue_dict[ctx.guild.id].current().title}
Posistion: {queue_dict[ctx.guild.id].current().number_in_queue}"""
        )

        await ctx.send(embed=embed_to_send)

############-PAUSE COMMAND-####################################################################################

    @commands.command(name="pause")
    async def pause(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if voice.is_paused() is False:
            voice.pause()
            await ctx.send("The player has been paused.")
        else:
            await ctx.send("The player is already paused.")

############-UNPAUSE COMMAND-##################################################################################

    @commands.command(name="unpause", aliases=["resume"])
    async def unpause(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        voice.resume()
        await ctx.send("The queue has been un-paused.")

############-SKIP COMMAND-#####################################################################################

    @commands.command(name="next", aliases=["skip"])
    async def next(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await ctx.channel.send("Skipped the current song.")

        voice.stop()
        await queue_dict[ctx.guild.id].play_next()

############-GOTO COMMAND-#####################################################################################

    @commands.command(name="goto")
    async def goto(self, ctx, arg: int):
        print(arg)
        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await queue_dict[ctx.guild.id].move_to(arg)

        await ctx.channel.send(f"Skipped to {arg} in queue.")

############-LEAVE COMMAND-####################################################################################

    @commands.command(name="leave", aliases=["fuckoff", "disconnect", "quit"])
    async def leave(self, ctx):

        try:
            voice_channel = ctx.author.voice.channel
        # if author is not in a voice channel this will run
        except AttributeError as e:
            print(e)
            await ctx.send("You are not connected to a voice channel.")
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            await ctx.guild.change_voice_state(channel=voice_channel, self_mute=False, self_deaf=True)

        await voice.disconnect()
        del queue_dict[ctx.guild.id]

        await ctx.send("The bot has left the voice channel, and the queue has been cleared.")

############-REMOVE COMMAND-###################################################################################

    @commands.command(name="remove")
    async def remove(self, ctx, arg: int):
        removed_song = queue_dict[ctx.guild.id].songs.pop(arg - 1)
        await ctx.channel.send(f"Removed {removed_song.title} from the queue.")
