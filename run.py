import discord
from discord.ext import commands
from discord import app_commands
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

with open(config_file, 'r') as f:
    token = json.load(f)["TOKEN"]


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

class ServerData:
    def __init__(self, id, channel_ids, roles_to_ping, max_events, current_no_events, is_blocked, messages):
        self.id = id
        self.channel_ids = channel_ids
        self.roles_to_ping = roles_to_ping
        self.max_events = max_events
        self.current_no_events = current_no_events
        self.is_blocked = is_blocked
        self.messages = messages

def create_default_config(server_id):
    with open(config_file, 'r') as f:
        data = json.load(f)
    servers_data = data["SERVERS"]
    servers_data[server_id] = { }
    servers_data[server_id]["CHANNEL_IDS"] = []
    servers_data[server_id]["ROLES_TO_PING"] = []
    servers_data[server_id]["MAX_NO_EVENTS"] = 3
    servers_data[server_id]["CURRENT_NO_EVENTS"] = 0
    servers_data[server_id]["IS_BLOCKED"] = 0
    servers_data[server_id]["MESSAGES"] = [ "Be ashamed <user>!" ]
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=4)


def get_server_config(server_id) -> ServerData:
    with open(config_file, 'r') as f:
        config = json.load(f)
    data = config["SERVERS"]
    if (str(server_id) not in data):
        create_default_config(server_id)
    server_data = data[str(server_id)]
    return ServerData(server_id, server_data["CHANNEL_IDS"], server_data["ROLES_TO_PING"], server_data["MAX_NO_EVENTS"], server_data["CURRENT_NO_EVENTS"], server_data["IS_BLOCKED"], server_data["MESSAGES"])

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as a bot with id {bot.user.id}")

def is_in_allowed_channel(interaction: discord.Interaction, channel_ids):
    if interaction.channel.id in channel_ids:
        return True
    return False

def check_who_to_shame(ctx, user_ids_list: list):
    voice_channels = [channel for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
    user_objects_dict = {member.id: member for member in ctx.guild.members if member.id in user_ids_list}
    for channel in voice_channels:
        voice_channel_ids = [member.id for member in channel.members]
        user_objects_dict = {user_id: member for user_id, member in user_objects_dict.items() if user_id not in voice_channel_ids}
    return user_objects_dict.values()

async def shame_users(interaction, user_to_shame_objects, messages):
    if len(user_to_shame_objects) == 0:
        date = datetime.now().strftime("%d/%m/%Y")
        await interaction.followup.send(f"Let it be known, that on {date} Everybody was on time 🥳!")
        return
    for user in user_to_shame_objects:
        if len(messages) == 0:
            await interaction.followup.send(user.mention)
        else:
            random_message = random.choice(messages)
            formatted_message = random_message.replace("<user>", user.mention)
            await interaction.followup.send(formatted_message)

@bot.tree.command(name="ping_users_at")
@app_commands.describe(time_str="Set a timer for pings (HH:MM)", users="Comma-separated list of display_names of users")
async def ping_users_at(interaction: discord.Interaction, time_str: str, users: str):
    """Set a timer for pings (HH:MM) <display_names of users>."""
    data = get_server_config(interaction.guild_id)
    if not is_in_allowed_channel(interaction, data.channel_ids):
        return
    message_author = interaction.user
    if data.is_blocked == 1:
        return
    if data.current_no_events > data.max_events:
        await interaction.response.send_message(f"Maximum number of events has been exceeded, is someone trolling in MY discord server {message_author.mention}!? locking the bot, message the bot owner.")
        soft_lock_bot(data)
        return
    looking_for_ids = []
    could_not_find = []
    stop_command = False
    try:
        target_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now().time()

        if target_time < now:
            await interaction.response.send_message(f"The time {time_str} has already passed for today {interaction.author.mention}!")
            return

        members_dict = {member.display_name: member for member in interaction.guild.members}
        user_list = users.split(',')
        user_list = [user.strip() for user in user_list]
        for user in user_list:
            if user not in members_dict:
                stop_command = True
                could_not_find.append(user)
            else:
                looking_for_ids.append(members_dict[user].id)
        if stop_command:
            await interaction.response.send_message(f"Could not find members with display_name {could_not_find}!, {message_author.mention}, aborting")
            return

        target_time = datetime.combine(datetime.today(), target_time)
        delay = (target_time - datetime.now()).total_seconds()

        IncrementEvents(data)
        await interaction.response.send_message("🫡")
        await asyncio.sleep(delay)

        data = get_server_config(interaction.guild_id)
        if data.is_blocked == 1:
            return
        await shame_users(interaction, check_who_to_shame(interaction, looking_for_ids), data.messages)
        DecrementEvents(data)

    except ValueError:
        await interaction.response.send_message(f"{message_author.mention} Please use the format HH:MM (24-hour format).")

def IncrementEvents(server_data : ServerData):
    with open(config_file, 'r') as f:
        data = json.load(f)
    data["SERVERS"][str(server_data.id)]["CURRENT_NO_EVENTS"] = server_data.current_no_events + 1
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=4)

def DecrementEvents(server_data : ServerData):
    with open(config_file, 'r') as f:
        data = json.load(f)
    data["SERVERS"][str(server_data.id)]["CURRENT_NO_EVENTS"] = server_data.current_no_events - 1
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=4)

def soft_lock_bot(server_data : ServerData):
    with open(config_file, 'r') as f:
        data = json.load(f)
    data[server_data.id]["IS_BLOCKED"] = 1
    with open(config_file, 'w') as f:
        json.dump(data, f, indent=4)



@bot.tree.command(name="add_message")
@app_commands.describe(new_message="The shame message you want to add, it has to contain exactly one \"<user>\"")
async def add_message(interaction: discord.Interaction, new_message: str):
    data = get_server_config(interaction.guild_id)
    if not is_in_allowed_channel(interaction, data.channel_ids):
        return
    if len(new_message.split("<user>")) != 2:
        await interaction.response.send_message(f"The message has to contain exactly one \"<user>\" {interaction.author.mention}")
        return
    data.messages.append(new_message)  # Add new message to the list

    with open(config_file, 'r') as f:
        all_data = json.load(f)
    all_data["SERVERS"][str(interaction.guild_id)]["MESSAGES"] = data.messages
    with open(config_file, 'w') as f:
        json.dump(all_data, f, indent=4)
    await interaction.response.send_message(f"✍️😉")

@bot.event
async def on_message(message):
    ctx = await bot.get_context(message)
    if message.content == "🫡" and message.author.id != bot.user.id: #:saluting_face:
        await ctx.send("🫡")


@bot.tree.command(name="create_timetable")
@app_commands.describe(hours_str="Space-separated list of hours for which the bot will create the timetable")
async def create_timetable(interaction: discord.Interaction, hours_str: str):
    hours = hours_str.split(' ')
    data = get_server_config(interaction.guild_id)
    if not is_in_allowed_channel(interaction, data.channel_ids):
        return
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    role_mention = []
    for role in data.roles_to_ping:
        role_mention.append(discord.utils.get(interaction.guild.roles, name=role).mention)
    product = list(itertools.product(days, hours))
    result = [i + " " + j for i, j in product]
    emojis_drawn = random_emoji(count=len(result))
    final_emojis = []
    for i in range(len(result)):
        current_emoji = emojis_drawn[i][0]
        while current_emoji in final_emojis:
            current_emoji = random_emoji()[0][0]
        final_emojis.append(current_emoji)
    my_message = "Emojis Randomized!" + " ".join(role_mention)
    for i in range(len(result)):
        my_message += f"\n{result[i]} - {final_emojis[i]}"
    await interaction.response.send_message(my_message)
    message = await interaction.edit_original_response(content=my_message)
    for emote in final_emojis:
        await message.add_reaction(emote)

bot.run(token)