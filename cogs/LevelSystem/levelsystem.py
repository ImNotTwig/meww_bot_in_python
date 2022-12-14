import discord
from discord.ext import commands
import json
import asyncio
import random
from config import config 

# xp_needed formula is:
# 5*(level^2) + (50*level) + 100 - current_xp

with open('cogs/LevelSystem/levels.json', 'r+') as file:
    levels = json.load(file)
with open('cogs/LevelSystem/server_level_system_enabler.json', 'r+') as file:
    server_enabler = json.load(file)

# since sometimes members data will have false it will be written to file
# this sets it to true when it loads the file so users can gain xp
for server in levels:
    for member in levels[server]:
        if server == "global":
            continue
        else:
            levels[server][member]['can_gain_xp'] = True

# calculate the global levels on startup
for member in levels['global']:
    levels['global'][member]['level'] = 0
    levels['global'][member]['total_xp'] = 0
for server in levels:
    if server == "global":
        continue
    else:
        for member in levels[server]:
            for field in levels['global'][member]:
                levels['global'][member][field] += levels[server][member][field]

with open('cogs/LevelSystem/levels.json', 'w') as file:
    json.dump(levels, file, indent=4)


def new_member(server, author):
    levels[server][author] = {}
    levels['global'][author] = {}
    levels['global'][author]['level'] = 0
    levels['global'][author]['total_xp'] = 0
    levels[server][author]['level'] = 0
    levels[server][author]['total_xp'] = 0
    levels[server][author]['current_xp'] = 0
    levels[server][author]['xp_needed'] = 100
    levels[server][author]['can_gain_xp'] = True

############-LEVELSYSTEM COMMANDS-#############################################################################


class LevelSystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

############-XP COMMAND-#######################################################################################

    @commands.command(name="xp", pass_context=True, case_insensitive=True)
    async def xp(self, ctx, member: discord.Member = None):
        # setting author name
        server = str(ctx.message.guild.id)

        if member is None:
            author = str(ctx.author.id)
            member = ctx.author
        else:
            author = str(member.id)

        # if author is in the levels dict already
        if server in levels.keys():
            if author in levels[server]:
                # sending the embed
                # title
                embed = discord.Embed(title=f"{member.name}'s level stats")
                # global xp that the user has until next level up
                embed.add_field(name="Global Xp",
                                value=levels["global"][author]['total_xp'],
                                inline=True)
                # global level of the user
                embed.add_field(name="Global Level",
                                value=levels["global"][author]['level'],
                                inline=True)
                # current_xp that the user has until next level up
                embed.add_field(name=f"{ctx.guild.name} Xp",
                                value=levels[server][author]['current_xp'],
                                inline=True)
                # current level of the user
                embed.add_field(name=f"{ctx.guild.name} Level",
                                value=levels[server][author]['level'],
                                inline=True)

                current_xp = levels[server][author]['current_xp']
                xp_needed = levels[server][author]['xp_needed']
                xp_needed_to_lvl_up = xp_needed - current_xp

                amount_per_box = xp_needed / 20
                current_boxes = current_xp / amount_per_box
                boxes_left = xp_needed_to_lvl_up / amount_per_box
                # there should be 20 boxes when the embed is sent
                # a percentage of white and blue squares should correspond to the current_xp and total_xp - current_xp
                embed.add_field(name=f"Progress to leveling up in {ctx.guild.name}",
                                value=(int(current_boxes)) * ":blue_square:" + (int(boxes_left)) * ":white_large_square:",
                                inline=False)
                embed.set_thumbnail(url=member.avatar.url)

                await ctx.send(embed=embed)
            # if the ~member~ is not in the levels dict already
            else:
                # create new user data
                new_member(server, author)
                with open('cogs/LevelSystem/levels.json', 'w') as file:
                    json.dump(levels, file, indent=4)

        # if the ~server~ is not in the levels dict already
        else:
            levels[server] = {}
            # create new user data
            new_member(server, author)
            # sending the embed

            embed = discord.Embed(title=f"{ctx.author.name}'s level stats")
            embed.add_field(name="Name", value=ctx.author.mention, inline=True)
            embed.add_field(name="Xp",
                            value=levels[server][author]['current_xp'],
                            inline=True)
            embed.add_field(name="Level",
                            value=levels[server][author]['level'],
                            inline=True)

            current_xp = levels[server][author]['current_xp']
            xp_needed = levels[server][author]['xp_needed']
            xp_needed_to_lvl_up = xp_needed - current_xp

            amount_per_box = xp_needed / 20
            current_boxes = current_xp / amount_per_box
            boxes_left = xp_needed_to_lvl_up / amount_per_box

            embed.add_field(name="Progress Bar [level]",
                            value=(int(current_boxes)) * ":blue_square:" + (int(boxes_left)) * ":white_large_square:",
                            inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

############-DETECT MESSAGE FOR XP-############################################################################

    @commands.Cog.listener()
    async def on_message(self, message):
        # if the server isnt in the server_enabler dict
        if str(message.guild.id) not in server_enabler.keys():
            server_enabler[str(message.guild.id)] = False
            with open('cogs/LevelSystem/server_level_system_enabler.json', 'r+') as file:
                json.dump(server_enabler, file, indent=4)
        # if the message starts with the prefix ignore it
        if message.content.startswith(str({config.prefix})):
            return

        # if author is a bot
        if message.author.bot is True:
            return

        # if the server has the level system turned on
        if server_enabler[str(message.guild.id)] is True:

            server = str(message.guild.id)
            author = str(message.author.id)

            # if the server isnt in the levels dict yet, add it
            if server not in levels.keys():
                levels[server] = {}
            if author not in levels[server]:
                # create a new entry in the json with default level 0 values
                new_member(server, author)

                with open('cogs/LevelSystem/levels.json', 'w') as file:
                    json.dump(levels, file, indent=4)

            # if the author can gain xp
            if levels[server][author]['can_gain_xp'] is True:
                # increase authors total_xp and current_xp
                xp_gained = random.randint(
                    config.level_system.xp_per_message[0],
                    config.level_system.xp_per_message[1])

                levels[server][author]['current_xp'] += xp_gained                
                levels[server][author]['total_xp'] += xp_gained
                # if the current_xp is over or equal to the xp_needed
                if levels[server][author]['current_xp'] >= levels[server][author]['xp_needed']:
                    # calculate how much current_xp went over xp_needed if it did
                    if levels[server][author]['current_xp'] > levels[server][author]['xp_needed']:
                        # set the authors current_xp to the difference between it and the xp_needed
                        levels[server][author]['current_xp'] = levels[server][author]['current_xp'] - levels[server][author]['xp_needed']
                    # if the current_xp is equal to xp_needed
                    else:
                        levels[server][author]['current_xp'] = 0

                    # increment the authors level by 1
                    levels[server][author]['level'] += 1
                    # setting the new xp_needed according to the formula defined at the top of this file
                    levels[server][author]['xp_needed'] = 5 * (levels[server][author]['level'] ^ 2) + (50 * levels[server][author]['level']) + 100

                # write the new xp amounts to levels.json
                with open('cogs/LevelSystem/levels.json', 'w') as file:
                    json.dump(levels, file, indent=4)

                # don't let the author gain xp until the cooldown is over
                levels[server][author]['can_gain_xp'] = False
                await asyncio.sleep(config.level_system.cooldown_in_seconds)
                levels[server][author]['can_gain_xp'] = True
        # if the server has the level system turned off
        else:
            return

############-LEADERBOARD COMMAND-##############################################################################

    @commands.command(name="leaderboard", aliases=["lb"], case_insensitive=True)
    async def leaderboard(self, ctx):
        server = str(ctx.message.guild.id)
        server_dict = levels[server]
        # sorting the users in the levels dict by total xp
        rankings = {
            key: value
            for key, value in sorted(
                server_dict.items(),
                key=lambda dict_item: -dict_item[1]['total_xp'])
        }

        # adding the fields for the first 10 people in the rankings dict
        i = 0
        embed = discord.Embed(title=f"Rankings for {ctx.guild.name}")
        for x in rankings:
            try:
                temp = ctx.guild.get_member(int(x))
                tempxp = levels[server][x]["total_xp"]
                templevel = levels[server][x]["level"]

                embed.add_field(name=f"{i+1}: {temp.name}", 
                                value=f"""Level: {templevel}
Total Xp: {tempxp}""", inline=False)

                i += 1
            except Exception:
                pass
            # when the amount of users added is 10 break
            if i == 10:
                break
        # sending the embed
        await ctx.channel.send(embed=embed)

############-LEVELSWITCH COMMAND-##############################################################################

    @commands.command(name="levelswitch", case_insensitive=True)
    @commands.has_permissions(manage_messages=True)
    async def levelswitch(self, ctx, arg):
        server = str(ctx.guild.id)

        if arg.lower() == "on":
            server_enabler[server] = True
            await ctx.channel.send(f"Switched the level system on for {ctx.guild.name}")

        if arg.lower() == "off":
            server_enabler[server] = False
            await ctx.channel.send(f"Switched the level system off for {ctx.guild.name}")

        with open('cogs/LevelSystem/server_level_system_enabler.json', 'w') as file:
            json.dump(server_enabler, file, indent=4)

############-GIVEXP COMMAND-###################################################################################

    @commands.command(name="givexp", case_insensitive=True)
    @commands.has_permissions(manage_messages=True)
    async def givexp(self, ctx, arg, member: discord.Member = None):
        try:
            amount_of_xp = int(arg)
        except ValueError:
            await ctx.channel.send("You did not supply a valid integer amount!")

        server = str(ctx.guild.id)
        author = str(member.id)

        if member is None:
            author = str(ctx.author.id)

        if member.id not in levels[server]:
            new_member(server, author)

        levels[server][author]['current_xp'] += amount_of_xp
        levels[server][author]['total_xp'] += amount_of_xp
        levels['global'][author]['total_xp'] += amount_of_xp

        # while the author's current_xp is greater or equal to xp_needed for level up
        while levels[server][author]['current_xp'] >= levels[server][author]['xp_needed']:
            # calculate how much current_xp went over xp_needed if it did
            if levels[server][author]['current_xp'] > levels[server][author]['xp_needed']:
                # set the author's current_xp to the difference between it and the xp_needed
                levels[server][author]['current_xp'] = levels[server][author]['current_xp'] - levels[server][author]['xp_needed']
            # if the author's current_xp is equal to xp_needed
            else:
                levels[server][author]['current_xp'] = 0

            # increment the authors level by 1
            levels[server][author]['level'] += 1
            levels["global"][author]['level'] += 1
            # setting the new xp_needed according to the formula defined at the top of this file
            levels[server][author]['xp_needed'] = 5 * (levels[server][author]['level'] ^ 2) + (50 * levels[server][author]['level']) + 100

            # write the new xp amounts to levels.json
        with open('cogs/LevelSystem/levels.json', 'w') as file:
            json.dump(levels, file, indent=4)

        await ctx.channel.send(f"{ctx.author.name} has given {member.name} {arg} xp.")
