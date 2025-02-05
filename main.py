import discord
import os
import random
from discord.ext import commands
from dotenv import load_dotenv
import requests
import asyncio


load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
api_key = os.getenv('API_KEY_OPEN_WEATHER')  
client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f'✅ We have logged in as {client.user}')
    print("✅ Bot is starting ...")
    print("-----------------------------------------")
    
    await client.change_presence(activity=discord.Game(name="Java ♨"))
    print("✅ Bot status set to: Java ♨")

    for guild in client.guilds:
        print(f'✅ Connected to: {guild.name} (ID: {guild.id})')


@client.event
async def on_message(message):
    if message.author == client.user:
        return 

    content = message.content.lower()  
    hello_keywords = ["hello", "hi", "salam", "wa fen"]
    arawkan_keywords = ["arawkan"]

    if any(word in content for word in hello_keywords):
        response = "Ach endek alkhawa"
        await message.channel.send(response)
        print(f'📩 Sent message: "{response}" in {message.guild.name}#{message.channel.name}')

    elif any(word in content for word in arawkan_keywords):
        quotes = [
            "Théoriquement", "plus ou moins", "Next", "Tout ce qu'on a vu", 
            "Pas de question ?", "7yed telephone", "Parfait !", "Madmoiselle", 
            "Pas de goblet sur table", "C'est la pire des solutions !!"
        ]
        random_quote = random.choice(quotes)
        await message.channel.send(random_quote)
        print(f'📩 Sent quote: "{random_quote}" in {message.guild.name}#{message.channel.name}')

    await client.process_commands(message) 

@client.command()
async def create_channel_in_category(ctx, category_name, channel_name):
    guild = ctx.guild  
    category = discord.utils.get(guild.categories, name=category_name)

    if not category:
        category = await guild.create_category(category_name)
        await ctx.send(f"✅ Catégorie `{category_name}` créée avec succès !")
        print(f'✅ Created category: {category_name} in {guild.name}')

    existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
    if not existing_channel:
        await guild.create_text_channel(channel_name, category=category)
        await ctx.send(f"✅ Canal `{channel_name}` ajouté à la catégorie `{category_name}`")
        print(f'✅ Created channel: {channel_name} in category: {category_name} ({guild.name})')
    else:
        await ctx.send(f"⚠️ Le canal `{channel_name}` existe déjà dans `{category_name}`.")
        print(f'⚠️ Channel {channel_name} already exists in {category_name} ({guild.name})')

@client.command()
async def create_categories_with_channels(ctx, *categories):
    guild = ctx.guild  
    text_channels = ["cours", "tds", "tps", "exams", "bonus"]

    for category_name in categories:
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            category = await guild.create_category(category_name)
            await ctx.send(f"✅ Catégorie `{category_name}` créée avec succès !")
            print(f'✅ Created category: {category_name} in {guild.name}')
        
        for channel_name in text_channels:
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
            if not existing_channel:
                await guild.create_text_channel(channel_name, category=category)
                await ctx.send(f"✅ Canal `{channel_name}` ajouté à la catégorie `{category_name}`")
                print(f'✅ Created channel: {channel_name} in category: {category_name} ({guild.name})')
            else:
                print(f'⚠️ Channel {channel_name} already exists in {category_name} ({guild.name})')

    await ctx.send("✅ **Toutes les catégories et leurs canaux ont été créés !** 🎉")
    print(f'✅ All requested categories and channels have been created in {guild.name}.')

@client.command()
async def delete_messages(ctx, amount: str = "5"):
    """Deletes a specified number of messages or all messages if '-' is given."""
    if amount == "-":
        deleted_count = 0
        async for message in ctx.channel.history(limit=100):  
            await message.delete()
            deleted_count += 1
            await asyncio.sleep(1)  

        await ctx.send(f"✅ Deleted **{deleted_count}** messages.", delete_after=3)
        print(f'🗑 Deleted all messages in {ctx.guild.name}#{ctx.channel.name}')
    else:
        try:
            amount = int(amount)
            if amount < 1:
                await ctx.send("⚠️ Please specify a valid number of messages to delete.", delete_after=3)
                return
            
            deleted = await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"✅ Deleted **{len(deleted) - 1}** messages.", delete_after=3)
            print(f'🗑 Deleted {len(deleted) - 1} messages in {ctx.guild.name}#{ctx.channel.name}')
        
        except ValueError:
            await ctx.send("⚠️ Invalid input. Use a number or '-' to delete all messages.", delete_after=3)


@client.command()
async def delete_bot_messages(ctx, limit: int = 5):
    """Deletes the bot's last messages in the current channel (default: 5 messages)."""
    deleted = 0
    async for message in ctx.channel.history(limit=100):
        if message.author == client.user and deleted < limit:
            await message.delete()
            deleted += 1

    await ctx.send(f"✅ Deleted {deleted} bot messages.", delete_after=3)
    print(f'🗑 Deleted {deleted} bot messages in {ctx.guild.name}#{ctx.channel.name}')

@client.command()
async def weather(ctx, city: str):
    if not api_key:
        await ctx.send("⚠️ API key for OpenWeather not found in the environment variables.")
        print("⚠️ OpenWeather API key not found.")
        return

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data['cod'] != '404':
        main_data = data['main']
        weather_data = data['weather'][0]
        temperature = main_data['temp']
        description = weather_data['description']
        await ctx.send(f"Weather in {city.capitalize()}:\nTemperature: {temperature}°C\nDescription: {description.capitalize()}")
        print(f'🌦 Weather for {city}: {temperature}°C, {description}')
    else:
        await ctx.send("City not found!")
        print(f'⚠️ City "{city}" not found.')

@client.command()
async def set_status(ctx, *, status: str):
    await client.change_presence(activity=discord.Game(name=status))
    await ctx.send(f"Bot status updated to: {status}")
    print(f'✅ Bot status updated to: {status}')

@client.command()
async def server_info(ctx):
    """Displays detailed server information in a well-formatted way."""
    guild = ctx.guild
    owner = guild.owner  
    creation_date = guild.created_at.strftime("%B %d, %Y")  
    member_count = guild.member_count  
    num_channels = len(guild.channels)  
    roles = [role.mention for role in guild.roles if role.name != "@everyone"]  

    embed = discord.Embed(
        title=f"🖥️ **{guild.name}** Server Information",
        description=f"👑 **Owner:** {owner.mention}\n🆔 **Server ID:** `{guild.id}`",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📆 **Creation Date:**", value=creation_date, inline=True)
    embed.add_field(name="👥 **Members:**", value=f"{member_count}", inline=True)
    embed.add_field(name="📢 **Channels:**", value=f"{num_channels}", inline=True)
    
    roles_text = ", ".join(roles) if roles else "None"
    embed.add_field(name=f"🎭 **Roles [{len(guild.roles) - 1}]:**", value=roles_text, inline=False)

    embed.set_thumbnail(url=guild.icon.url if guild.icon else None) 
    embed.set_footer(text="🔹 Use !help_ for more commands!")

    await ctx.send(embed=embed)

    print(f'ℹ️ Server info command used by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}')
    print(f'ℹ️ Server Name: {guild.name} | Owner: {owner} | Members: {member_count} | Channels: {num_channels}')


@client.command()
async def kick_(ctx, user: discord.User, *, reason: str = "No reason provided"):
    await ctx.guild.kick(user, reason=reason)
    await ctx.send(f"{user} has been kicked for {reason}.")
    print(f'⚡ Kicked {user} from the server for {reason}.')

@client.command()
async def help_(ctx):
    """Displays all available commands and their usage."""
    help_text = """
    **🤖 Bot Commands Guide**  
    Use these commands to interact with the bot:  

    🔹 **General Commands:**  
    `!help_` → Show this help message.  
    `!server_info` → Display server name, creation date, and member count.  

    🔹 **Messaging Commands:**  
    `!delete_messages [amount]` → Delete a specific number of messages (default: 5).  
    `!delete_messages -` → Delete **all messages** in the current channel (use with caution!).  

    🔹 **Weather :**  
    `!weather <city>` → Get current weather information for a city.
     
    🔹 Fun Commands:**
    `arawkan` → Get a random quote from a predefined list.   
    """
    await ctx.send(help_text)
    print(f'📜 Help command used by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}')

client.run(TOKEN)
