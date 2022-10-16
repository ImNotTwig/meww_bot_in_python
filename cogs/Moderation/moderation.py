import discord
from discord.ext import commands
import json
from collections import OrderedDict

with open('cogs/Moderation/mute_roles.json', 'r+') as mute_role_file:
    mute_role_dict = json.load(mute_role_file)

with open('config.json', 'r+') as config_file:
    config = json.load(config_file)

user_spam_count = OrderedDict()

############-MODERATION COMMANDS-##############################################################################

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-KICK COMMAND-#####################################################################################

    @commands.command(name="kick", pass_context=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.kick(member)
        if reason is not None:
            await ctx.send(f'User {member.mention} has been kicked for {reason}')
            return

        await ctx.send(f'User {member.mention} has been kicked')
        return

############-BAN COMMAND-######################################################################################

    @commands.command(name="ban", pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):

        await ctx.guild.ban(member)
        if reason is not None:
            await ctx.send(f'User {member.mention} has been banned for {reason}')
            return

        await ctx.send(f'User {member.mention} has been banned')
        return

############-MUTE COMMAND-#####################################################################################

    @commands.command(name="mute", pass_context=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):

        mute_role_name = mute_role_dict[str(ctx.guild.id)]

        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)

        await member.add_roles(mute_role)

        if reason is not None:
            await ctx.send(f'{member} has been muted for {reason}')
            return

        await ctx.send(f'{member} has been muted')
        return

############-UNMUTE COMMAND-###################################################################################

    @commands.command(name="unmute", pass_context=True)
    @commands.has_permissions(manage_messages=True, manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):

        mute_role_name = mute_role_dict[str(ctx.guild.id)]

        mute_role = discord.utils.get(ctx.guild.roles, name=mute_role_name)

        await member.remove_roles(mute_role)

        await ctx.send(f'{member} has been un-muted')
        return

############-MUTEROLE COMMAND-#################################################################################

    @commands.command(name="muterole")
    @commands.has_permissions(manage_roles=True)
    async def muterole(self, ctx, role: discord.Role):

        if ctx.guild.id not in mute_role_dict.keys():
            mute_role_dict[ctx.guild.id] = str(role)

        with open('cogs/Moderation/mute_roles.json', 'r+') as file:
            json.dump(mute_role_dict, file, indent=4)

        await ctx.send(f'Set mute role to {role}.')
        return

############-PURGE COMMAND-####################################################################################

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, arg: int):
        await ctx.channel.purge(limit=arg+1)

        embed_to_send = discord.Embed(title=f'{arg} messages have been deleted.')
        embed_to_send.set_footer(text=f'{ctx.message.author} used {config["prefix"]}purge')

        await ctx.send(embed=embed_to_send, delete_after=5)

############-ANTISPAM AND BLACKLIST-###########################################################################
    
    @commands.Cog.listener()
    async def on_message(self, message):

        #if author is an administrator
        if message.author.guild_permissions.administrator is True:
            return
        
        author_id = str(message.author.id)
        words_in_message = message.content.split()

        #if message has a blacklisted word
        for black_listed_word in config['word_blacklist']:
            for word in words_in_message:
                if word.startswith(black_listed_word) or word.endswith(black_listed_word):
                    await message.delete()
                    await message.channel.send(f'{message.author.mention} your message contains a blacklisted word, it has been deleted.')

        #if author has the manage messages permission
        if message.author.guild_permissions.manage_messages:
            return
        #if the author is a bot
        if message.author.bot:
            return

        #if the antispam feature is turned on
        if config['spam_settings']['antispam']:
            if author_id not in user_spam_count.keys():
                #if the user's id is not in the dictionary add it
                user_spam_count[author_id] = [0, message.content]

            if user_spam_count[author_id][1] != message.content:
                #if the message in the user's spam count is not the same reset the counter
                user_spam_count[author_id] = [0, message.content]

            if user_spam_count[author_id][0] == 0:
                #if the spam count is 0 set it to 1
                user_spam_count[author_id][0] = 1

            elif user_spam_count[author_id][0] == config['spam_settings']['spam_count'] - 1:
                #if the user has sent the same message the amount of times in a row
                #that is defined by the config they will be muted
                mute_role_name = mute_role_dict[author_id]
                mute_role = discord.utils.get(message.guild.roles, name=mute_role_name)

                await message.author.add_roles(mute_role)
                await message.channel.send(f"{message.author.mention} has been muted for spamming.")
                user_spam_count[author_id][0] = 0

            else:
                #add to the counter
                user_spam_count[author_id][0] += 1

            if len(user_spam_count) > 50:
                user_spam_count.pop(50)

###############################################################################################################