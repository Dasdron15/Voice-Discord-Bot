import discord
from discord.ext import commands, tasks
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
client = commands.Bot(command_prefix="$", intents=intents)
created_voice = []
join_voice = {}
error_channel = None

@client.event
async def on_ready():
    await client.tree.sync()
    delete.start()
    print(f'Logged in as {client.user}!')

@client.event
async def on_app_command_error(interaction: discord.Interaction, error):
    global error_channel
    print(f"Error occurred: {error}")
    if error_channel is None:
        print("Error channel is not set.")
        return

    channel = client.get_channel(error_channel)
    if channel is None:
        print(f"Channel with ID {error_channel} not found.")
        return

    try:
        await channel.send(f"An error occurred: {str(error)}")
    except Exception as e:
        print(f"Failed to send error message: {e}")

@client.event
async def on_voice_state_update(member, before, after):
    global created_voice
    global join_voice

    guild = member.guild
    
    if after.channel and after.channel.id in join_voice:
        if len(after.channel.members) == 1:
            join_data = join_voice[after.channel.id]
            new_channel = await guild.create_voice_channel(name=join_data['name'], category=after.channel.category)
            await new_channel.set_permissions(member, connect=True, move_members=join_data['edit'], manage_channels=join_data['edit'], manage_permissions=join_data['edit'])
            channel = client.get_channel(new_channel.id)
            await channel.edit(user_limit=join_data['limit'])
            created_voice.append(new_channel.id)
            print(f"Created new voice channel: {new_channel.name}")
            await member.move_to(new_channel)
            print(f"Moved {member.name} to {new_channel.name}")
    elif before.channel:
        if before.channel.id in created_voice:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                created_voice.remove(before.channel.id)
                print(f"Deleted empty voice channel: {before.channel.name}")

@tasks.loop(seconds=1.0)
async def delete():
    empty_channels = []
    for channel_id in created_voice:
        channel = client.get_channel(channel_id)
        if channel and len(channel.members) == 0:
            empty_channels.append(channel_id)
    await asyncio.sleep(2)
    for channel_id in empty_channels:
        channel = client.get_channel(channel_id)
        if channel and len(channel.members) == 0:
            await channel.delete()
            created_voice.remove(channel_id)
            print(f"Deleted empty voice channel: {channel.name}")


@client.tree.command(name="bitrate", description="You can change the bitrate of a channel with this command!")
async def bitrate(interaction: discord.Interaction, bitrate: int):
    member = interaction.guild.get_member(interaction.user.id)

    if member is None or member.voice is None or member.voice.channel is None:
        await interaction.response.send_message("You are not connected to any voice channel.", ephemeral=True)
        return
    else:
        vchannel = member.voice.channel
    
    if bitrate < 8000:
        await interaction.response.send_message("Bitrate value should be greater than or equal to 8000.", ephemeral=True)
    elif bitrate > 96000:
        await interaction.response.send_message("Bitrate value should be less than or equal to 96000.", ephemeral=True)
    else:
        await vchannel.edit(bitrate=bitrate)
        await interaction.response.send_message(f"Bitrate for {vchannel.name} has been changed to {bitrate}.", ephemeral=True)

@client.tree.command(name="error-channel")
async def set_error_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global error_channel
    error_channel = channel.id
    await interaction.response.send_message(f"Error channel has been successfully set to {channel.mention}.", ephemeral=True)
    print(f"Error channel set to {channel.id}")

@client.tree.command(name="create-voice-channel", description="You can create voice chat with this command!")
async def create_voice(interaction: discord.Interaction, name: str, limit: int = None, edit: bool = False):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    existing_channel = discord.utils.get(guild.voice_channels, name=name)
    if existing_channel:
        await interaction.response.send_message("Voice chat with that name already exists.", ephemeral=True)
        return
    try:
        voice_channel = await guild.create_voice_channel(name, user_limit=limit)
        if edit == True:
            await voice_channel.set_permissions(guild.default_role, connect=True, move_members=True, manage_channels=True, manage_permissions=True)
        
        await interaction.response.send_message(f"Voice channel '{name}' has been created.", ephemeral=True)
    except discord.HTTPException as e:
        await interaction.response.send_message(f"An error occurred while creating the voice channel: {e}", ephemeral=True)

@client.tree.command(name="join-to-create", description="Create Join to Create voice channel.")
async def join_create(interaction: discord.Interaction, name: str = "Default", limit: int = None, edit: bool = True):
    global join_voice, join_name, join_limit, join_edit
    join_name = name
    join_limit = limit
    join_edit = edit

    join_category = await interaction.guild.create_category("JOIN TO CREATE")
    join_channel = await interaction.guild.create_voice_channel("Join To Create", category=join_category)
    join_voice[join_channel.id] = {"name": join_name, "limit": join_limit, "edit": join_edit}
    await interaction.response.send_message("New Join To Create channel has been successfully created.", ephemeral=True)

client.run("TOKEN")
