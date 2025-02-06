import discord
import os
import random
import logging
import requests
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv('API_KEY_OPEN_WEATHER')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# ========================
# EVENTS
# ========================
@bot.event
async def on_ready():
    print(f'✅ We have logged in as {bot.user}')
    print("✅ Bot is starting ...")
    print("-----------------------------------------")
    
    await bot.change_presence(activity=discord.Game(name="Java ♨"))
    print("✅ Bot status set to: Java ♨")

    for guild in bot.guilds:
        print(f'✅ Connected to: {guild.name} (ID: {guild.id})')

@bot.event
async def on_message(message):
    if message.author == bot.user:  
        return

    content = message.content.lower()
    responses = {
        ("hello", "hi", "salam", "wa fen"): "Ach endek alkhawa",
        ("arawkan",): [
            "Théoriquement", "plus ou moins", "Next", 
            "Tout ce qu'on a vu", "Pas de question ?", 
            "7yed telephone", "Parfait !", "Madmoiselle",
            "Pas de goblet sur table", "C'est la pire des solutions !!"
        ]
    }

    for keywords, response in responses.items():
        if any(word in content for word in keywords):
            if isinstance(response, list):
                chosen = random.choice(response)
                await message.channel.send(chosen)
                logging.info(f"Sent quote: '{chosen}' in {message.channel}")
            else:
                await message.channel.send(response)
                logging.info(f"Sent greeting in {message.channel}")
            break

    await bot.process_commands(message)

# ========================
# SERVER COMMANDS
# ========================
@bot.command(aliases=["info"])
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
    print(f'ℹ️ Server Name: {guild.name} | Owner: {owner} | Members: {member_count} | Channels: {num_channels}.')

# ========================
# COMMANDS
# ========================

@bot.command(aliases=["channel"])
@commands.has_permissions(manage_channels=True)
async def create_channel_in_category(ctx, category_name: str, channel_name: str):
    """Create a text channel within a category"""
    guild = ctx.guild
    
    try:
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            logging.info(f"📂 Created category '{category_name}' in {guild.name} by {ctx.author}")

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
        if existing_channel:
            await ctx.send(f"⚠️ Channel `{channel_name}` already exists!")
            logging.warning(f"🚫 Channel creation failed - '{channel_name}' already exists in '{category_name}' ({guild.name})")
            return

        await guild.create_text_channel(channel_name, category=category)
        embed = discord.Embed(
            description=f"✅ Created `{channel_name}` in `{category_name}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        logging.info(f"📝 Created channel '{channel_name}' in category '{category_name}' ({guild.name}) by {ctx.author}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permissions to manage channels!")
        logging.error(f"🚫 Permission denied for channel creation in {guild.name}")

@bot.command(aliases=["categories"])
@commands.has_permissions(administrator=True)
async def create_categories(ctx, *categories: str):
    """Create multiple categories with standard channels"""
    text_channels = ["cours", "tds", "tps", "exams", "bonus"]
    guild = ctx.guild
    
    logging.info(f"🏗️ Starting category creation in {guild.name} by {ctx.author}")
    
    for category_name in categories:
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
            logging.info(f"📁 Created category '{category_name}' in {guild.name}")

        created = []
        for ch_name in text_channels:
            if not discord.utils.get(guild.text_channels, name=ch_name, category=category):
                await guild.create_text_channel(ch_name, category=category)
                created.append(ch_name)
                logging.info(f"📄 Created channel '{ch_name}' in '{category_name}' ({guild.name})")

        if created:
            embed = discord.Embed(
                title=f"Category: {category_name}",
                description=f"Created channels: {', '.join(created)}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    logging.info(f"✅ Finished creating {len(categories)} categories in {guild.name}")

@bot.command(aliases=["w"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def weather(ctx, *, city: str):
    """Get weather data for a city"""
    if not OPENWEATHER_API_KEY:
        await ctx.send("❌ Weather service unavailable")
        return

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=10)
        data = res.json()

        if data['cod'] != 200:
            await ctx.send(f"❌ Error: {data.get('message', 'Unknown error')}")
            return

        main = data['main']
        weather = data['weather'][0]
        
        embed = discord.Embed(
            title=f"Weather in {data['name']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🌡 Temperature", value=f"{main['temp']}°C")
        embed.add_field(name="💨 Humidity", value=f"{main['humidity']}%")
        embed.add_field(name="☁️ Condition", value=weather['description'].title(), inline=False)
        embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather['icon']}.png")
        
        await ctx.send(embed=embed)
        
    except requests.exceptions.Timeout:
        await ctx.send("⌛ Request timed out. Try again later.")
    except Exception as e:
        logging.error(f"Weather Error: {str(e)}")
        await ctx.send("❌ Failed to fetch weather data")

@bot.command(aliases=["status"])
@commands.has_permissions(administrator=True)
async def set_status(ctx, *, text: str):
    """Change the bot's playing status"""
    await bot.change_presence(activity=discord.Game(name=text))
    embed = discord.Embed(
        description=f"🎮 Status set to: **{text}**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ========================
# MESSAGE MANAGEMENT
# ========================

@bot.command(aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: str = "5"):
    """Delete messages (specify number or '-' to delete all)"""
    try:
        if amount == "-":
            deleted = await ctx.channel.purge(limit=None, check=lambda m: not m.pinned)
            msg = f"🗑️ Deleted **{len(deleted)}** messages"
        else:
            amount = int(amount)
            if amount < 1:
                raise ValueError
            deleted = await ctx.channel.purge(limit=amount + 1)
            msg = f"🗑️ Deleted **{len(deleted)-1}** messages"
            
        embed = discord.Embed(description=msg, color=discord.Color.green())
        await ctx.send(embed=embed, delete_after=5)
        logging.info(f"Deleted messages in {ctx.channel} by {ctx.author}")

    except ValueError:
        embed = discord.Embed(
            description="⚠️ Invalid amount. Use number or '-'",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)

@bot.command(aliases=["clearB"])
async def delete_bot_messages(ctx, limit: int = 5):
    """Delete the bot's recent messages"""
    def is_bot(m):
        return m.author == bot.user
    
    deleted = await ctx.channel.purge(limit=limit, check=is_bot)
    embed = discord.Embed(
        description=f"🤖 Deleted **{len(deleted)}** bot messages",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, delete_after=5)
    logging.info(f"Deleted bot messages in {ctx.channel} by {ctx.author}")

# ========================
# HELP COMMAND
# ========================

@bot.command(aliases=["h"])
async def help_(ctx, command: str = None):
    """Show detailed help information"""
    embed = discord.Embed(
        title="🤖 Cheb BEKKALI Bot Help Center",
        description="**Prefix:** `!`\nGet detailed help with `!help_ <command>`",
        color=discord.Color.blue()
    )
    
    if not command:
        # Main help menu
        embed.add_field(
            name="📋 General Commands",
            value="```"
                  "help_        -> Show this message\n"
                  "server_info  -> Server statistics\n"
                  "weather      -> Check city weather\n"
                  "```",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Moderation Commands",
            value="```"
                  "create_channel_in_category <category> <name> -> Create channel\n"
                  "create_categories <names...>                 -> Bulk create categories\n"
                  "set_status                                   -> Change bot status\n"
                  "delete_messages                              -> Clear messages\n"
                  "delete_bot_messages                          -> Remove bot messages\n"
                  "create_channel                               -> Create channels\n"
                  "```",
            inline=False
        )
        
        embed.add_field(
            name="🎉 Fun Features",
            value="```"
                  "Auto-responses to:\n"
                  "- hello/hi/salam\n"
                  "- 'arawkan' keyword\n"
                  "```",
            inline=False
        )
        
        embed.set_footer(text="🔹 Required permissions: [🛠️] Manage Messages/Channels")
        
    else:
        cmd = bot.get_command(command.lower())
        if not cmd:
            embed = discord.Embed(
                description=f"❌ Command `{command}` not found",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        embed.title = f"ℹ️ Help for: {cmd.name}"
        embed.description = f"**Description:** {cmd.help or 'No description'}"
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            
        if isinstance(cmd, commands.Command):
            params = " ".join(f"<{param}>" for param in cmd.clean_params)
            embed.add_field(
                name="Usage", 
                value=f"```!{cmd.name} {params}```",
                inline=False
            )
            
        if cmd.checks:
            perms = []
            for check in cmd.checks:
                if hasattr(check, '__qualname__') and 'has_permissions' in check.__qualname__:
                    perms.extend(check.kwargs.get('manage_messages', []))
            if perms:
                embed.add_field(
                    name="Required Permissions",
                    value="\n".join(f"• {perm.replace('_', ' ').title()}" for perm in perms),
                    inline=False
                )

    await ctx.send(embed=embed)

# ========================
# ERROR HANDLERS
# ========================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            description="❌ Command not found. Use `!help_` for available commands",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ {ctx.author.mention} doesn't have permission to use this command.")
    else:
        logging.error(f"Command Error: {str(error)}")

@weather.error
async def weather_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("ℹ️ Usage: `!weather <city>`")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Cooldown active. Try again in {error.retry_after:.1f}s")

# ========================
# RUN BOT
# ========================
if __name__ == "__main__":
    if not TOKEN:
        logging.critical("❌ No bot token found in environment!")
    else:
        bot.run(TOKEN)