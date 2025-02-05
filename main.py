import discord
import os
import random
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID_2"))  

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, id=GUILD_ID)

    if guild:
        print(f'✅ Connected to: {guild.name} (ID: {guild.id})')
    else:
        print(f'⚠️ Bot is not in the guild with ID {GUILD_ID}')
    
    print(f'✅ We have logged in as {client.user}')
    print("✅ Bot is starting ...")
    print("-----------------------------------------")

@client.event
async def on_message(message):
    if message.author == client.user:
        return 

    if message.guild.id != GUILD_ID:
        return  

    content = message.content.lower()  
    hello_keywords = ["hello", "hi", "salam", "wa fen"]
    arawkan_keywords = ["arawkan"]

    if any(word in content for word in hello_keywords):
        response = "Ach endek alkhawa"
        await message.channel.send(response)
        print(f'📩 Sent message: "{response}" in #{message.channel.name}')

    elif any(word in content for word in arawkan_keywords):
        quotes = [
            "Théoriquement", "plus ou moins", "Next", "Tout ce qu'on a vu", 
            "Pas de question ?", "7yed telephone", "Parfait !", "Madmoiselle", 
            "Pas de goblet sur table", "C'est la pire des solutions !!"
        ]
        random_quote = random.choice(quotes)
        await message.channel.send(random_quote)
        print(f'📩 Sent quote: "{random_quote}" in #{message.channel.name}')

    await client.process_commands(message) 

@client.command()
async def create_channel_in_category(ctx, category_name, channel_name):
    if ctx.guild.id != GUILD_ID:
        await ctx.send("⚠️ This command can only be used in the designated server.")
        print(f'⚠️ Unauthorized attempt to create a channel in another server.')
        return

    guild = ctx.guild
    category = discord.utils.get(guild.categories, name=category_name)

    if not category:
        category = await guild.create_category(category_name)
        await ctx.send(f"✅ Catégorie `{category_name}` créée avec succès !")
        print(f'✅ Created category: {category_name}')

    existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
    if not existing_channel:
        await guild.create_text_channel(channel_name, category=category)
        await ctx.send(f"✅ Canal `{channel_name}` ajouté à la catégorie `{category_name}`")
        print(f'✅ Created channel: {channel_name} in category: {category_name}')
    else:
        await ctx.send(f"⚠️ Le canal `{channel_name}` existe déjà dans `{category_name}`.")
        print(f'⚠️ Channel {channel_name} already exists in category {category_name}')

@client.command()
async def create_categories_with_channels(ctx, *categories):
    if ctx.guild.id != GUILD_ID:
        await ctx.send("⚠️ This command can only be used in the designated server.")
        print(f'⚠️ Unauthorized attempt to create categories in another server.')
        return

    guild = ctx.guild
    text_channels = ["cours", "tds", "tps", "exams", "bonus"]

    for category_name in categories:
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            category = await guild.create_category(category_name)
            await ctx.send(f"✅ Catégorie `{category_name}` créée avec succès !")
            print(f'✅ Created category: {category_name}')
        
        for channel_name in text_channels:
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
            if not existing_channel:
                await guild.create_text_channel(channel_name, category=category)
                await ctx.send(f"✅ Canal `{channel_name}` ajouté à la catégorie `{category_name}`")
                print(f'✅ Created channel: {channel_name} in category: {category_name}')
            else:
                print(f'⚠️ Channel {channel_name} already exists in category {category_name}')

    await ctx.send("✅ **Toutes les catégories et leurs canaux ont été créés !** 🎉")
    print(f'✅ All requested categories and channels have been created.')

client.run(TOKEN)
