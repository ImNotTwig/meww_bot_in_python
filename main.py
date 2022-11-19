import discord
from discord.ext import commands
import asyncio
import os
from config import config

from cogs.Unbound.unbound import UnboundCommands
from cogs.Music.music import MusicCommands
from cogs.Moderation.moderation import ModerationCommands
from cogs.LevelSystem.levelsystem import LevelSystemCommands

###############################################################################################################

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix=config.prefix, intents=intents, help_command=None)

###############################################################################################################


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    #setting status to "listening to {prefix}help" eg: "listening to ~help"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{config.prefix}help'))


@bot.event
async def on_command_error(ctx, error):
    print(f'Error: {error}')


@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()

###############################################################################################################

if __name__ == '__main__':
    asyncio.run(bot.add_cog(UnboundCommands(bot)))
    asyncio.run(bot.add_cog(MusicCommands(bot)))
    asyncio.run(bot.add_cog(ModerationCommands(bot)))

    if config.level_system.levels_on is True:
        asyncio.run(bot.add_cog(LevelSystemCommands(bot)))

    bot.run(config.tokens.discord_token, log_handler=None)
