import discord
from discord.ext import commands
import os
import random
import asyncio
from datetime import datetime
import json
import sys
from random_unicode_emoji import random_emoji
import itertools

config_file = 'config.json'
if not os.path.exists(config_file):
    print("config not found, aborting!")
    sys.exit()

# load_dotenv()
with open(config_file, 'r') as f:
    config = json.load(f)


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
shame_events_count = 0

MESSAGES = config['MESSAGES']

softlock_bot = False

@bot.event
async def on_ready():
    print(f"Logged in as a bot with id {bot.user.id}")

def is_in_allowed_channel(ctx):
    if ctx.channel.id in config["CHANNEL_IDS"]:
        return True
    return False

def check_who_to_shame(ctx, user_ids_list: list):
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    user_objects_dict = {member.id: member for member in ctx.guild.members if member.id in user_ids_list}
    for channel in voice_channels:
        voice_channel_ids = [member.id for member in channel.members]
        user_objects_dict = {user_id: member for user_id, member in user_objects_dict.items() if user_id not in voice_channel_ids}
    return user_objects_dict.values()

async def shame_users(ctx, user_to_shame_objects):
    if len(user_to_shame_objects) == 0:
        date = datetime.now().strftime("%d/%m/%Y")
        await ctx.send(f"Let it be known, that on {date} Everybody was on time 🥳!")
        return
    for user in user_to_shame_objects:
        if len(MESSAGES) == 0:
            await ctx.send(user.mention)
        else:
            random_message = random.choice(MESSAGES)
            formatted_message = random_message.replace("<user>", user.mention)
            await ctx.send(formatted_message)

@bot.command()
async def set(ctx, time_str: str, *users: str):
    """Set a timer for pings (HH:MM) <display_names of users>."""
    if not is_in_allowed_channel(ctx):
        return
    global shame_events_count, softlock_bot
    message_author = ctx.author
    if softlock_bot:
        return
    if shame_events_count > config['MAX_NO_EVENTS']:
        bot_owner_object = [member for member in ctx.guild.members if member.name == config["BOT_OWNER"]][0]
        await ctx.send(f"Maximum number of events has been exceeded, is someone trolling in MY discord server {message_author.mention}!? locking the bot until {bot_owner_object.mention} restarts me")
        softlock_bot = True
        return
    looking_for_ids = []
    could_not_find = []
    stop_command = False
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now().time()

        if target_time < now:
            await ctx.send(f"The time {time_str} has already passed for today {ctx.author.mention}!")
            return

        members_dict = {member.display_name: member for member in ctx.guild.members}
        for user in users:
            if user not in members_dict:
                stop_command = True
                could_not_find.append(user)
            else:
                looking_for_ids.append(members_dict[user].id)
        if stop_command:
            await ctx.send(f"Could not find members with display_name {could_not_find}!, {message_author.mention}, aborting")
            return

        target_time = datetime.combine(datetime.today(), target_time)
        delay = (target_time - datetime.now()).total_seconds()

        shame_events_count += 1
        await ctx.message.add_reaction("🫡") # on discord its - :saluting_face:
        await asyncio.sleep(delay)

        if softlock_bot:
            return
        await shame_users(ctx, check_who_to_shame(ctx, looking_for_ids))
        shame_events_count -= 1

    except ValueError:
        await ctx.send(f"{message_author.mention} Please use the format HH:MM (24-hour format).")

@bot.command()
async def add_message(ctx, new_message: str):
    if not is_in_allowed_channel(ctx):
        return
    if len(new_message.split("<user>")) != 2:
        await ctx.send(f"The message has to contain exactly one \"<user>\" {ctx.author.mention}")
        return
    MESSAGES.append(new_message)  # Add new message to the list

    with open(config_file, 'w') as f:
        json.dump({
            "TOKEN" : config["TOKEN"],
            "CHANNEL_IDS" : config["CHANNEL_IDS"],
            "MAX_NO_EVENTS": config['MAX_NO_EVENTS'],
            "MESSAGES": MESSAGES
        }, f, indent=4)
    await ctx.message.add_reaction("✍️")
    await ctx.message.add_reaction("😉")

@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    if message.content == "🫡" and message.author.id != bot.user.id: #:saluting_face:
        await ctx.send("🫡")
    await bot.process_commands(message)

@bot.command()
async def create_timetable(ctx, *hours: str):
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    role_mention = f"<@&{1165021388797640775}>, <@&{1160682796474454056}>"
    product = list(itertools.product(days, hours))
    result = [i + " " + j for i, j in product]
    emojis_drawn = random_emoji(count=len(result))
    final_emojis = []
    for i in range(len(result)):
        current_emoji = emojis_drawn[i][0]
        while current_emoji in final_emojis:
            current_emoji = random_emoji()[0][0]
        final_emojis.append(current_emoji)
    my_message = "Emojis Randomized!" + role_mention
    for i in range(len(result)):
        my_message += f"\n{result[i]} - {final_emojis[i]}"
    message = await ctx.send(my_message)
    for emote in final_emojis:
        await message.add_reaction(emote)

@bot.command()
async def ping(ctx):
    role_mention = f"<@&{1165021388797640775}>, <@&{1160682796474454056}>"
    await ctx.send(role_mention)


bot.run(config["TOKEN"])