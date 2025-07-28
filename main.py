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
        ("hello", "hi", "salam", "wa fen", "ahlan", "salam w 3lykom"): ["salam w 3lykom", "Ach endek alkhawa"],
        ("arawkan","ajihna"): [
            "Théoriquement", "plus ou moins", "Next", 
            "Tout ce qu'on a vu", "Pas de question ?", 
            "7yed telephone", "Parfait !", "Madmoiselle",
            "Pas de goblet sur table", "C'est la pire des solutions !!"
            "Ehhh, Aji lhna fen ghadi !",
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

# ========================
# CUSTOM VIEWS
# ========================
class PrivacyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30.0)
        self.is_private = None

    @discord.ui.button(label="Private", style=discord.ButtonStyle.red, emoji="🔒")
    async def private_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_private = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Public", style=discord.ButtonStyle.green, emoji="🌍")
    async def public_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_private = False
        await interaction.response.defer()
        self.stop()

class RoleSelectView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.selected_roles = []
        
        # Get eligible roles (excluding @everyone and roles above bot)
        roles = [role for role in ctx.guild.roles 
                if role.name != "@everyone" 
                and role < ctx.guild.me.top_role]

        # Only add dropdown if there are roles available
        if roles:
            self.select = discord.ui.Select(
                placeholder="Select roles...",
                min_values=1,
                max_values=min(25, len(roles)),
                options=[discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)
        else:
            self.selected_roles = None  # Special value to indicate no roles available

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return
            
        self.selected_roles = [interaction.guild.get_role(int(id)) for id in self.select.values]
        await interaction.response.defer()
        self.stop()

# =================================
# UPDATED CREATE CATEGORIES COMMAND
# =================================
@bot.command(aliases=["categories"])
@commands.has_permissions(administrator=True)
async def create_categories(ctx, *categories: str):
    """Create categories with optional privacy settings and role selection"""
    text_channels = ["cours", "tds", "tps", "exams", "bonus"]
    guild = ctx.guild
    
    logging.info(f"🏗️ Starting category creation in {guild.name} by {ctx.author}")
    
    for category_name in categories:
        if discord.utils.get(guild.categories, name=category_name):
            await ctx.send(f"⚠️ Category `{category_name}` already exists!", delete_after=5)
            continue

        try:
            # Step 1: Privacy selection
            privacy_view = PrivacyView()
            embed = discord.Embed(
                title=f"Category Privacy: {category_name}",
                description="Should this category be private?",
                color=discord.Color.blue()
            )
            privacy_msg = await ctx.send(embed=embed, view=privacy_view)
            
            await privacy_view.wait()
            if privacy_view.is_private is None:
                await ctx.send("⏰ Timed out. Skipping category creation.", delete_after=5)
                continue
                
            overwrites = {}
            roles = []
            
            # Step 2: Handle private category setup
            if privacy_view.is_private:
                role_view = RoleSelectView(ctx)
                
                if role_view.selected_roles is None:  # No roles available
                    await ctx.send("⚠️ No eligible roles found. Creating public category instead.", delete_after=5)
                    privacy_view.is_private = False
                else:
                    embed = discord.Embed(
                        description="Select roles that should access this category:",
                        color=discord.Color.blue()
                    )
                    role_msg = await ctx.send(embed=embed, view=role_view)
                    await role_view.wait()
                    
                    if role_view.selected_roles:
                        roles = role_view.selected_roles
                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(view_channel=False)
                        }
                        for role in roles:
                            overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                    else:
                        await ctx.send("⚠️ No roles selected. Creating public category instead.", delete_after=5)
                        privacy_view.is_private = False

            # Always initialize overwrites as a dict
            final_overwrites = overwrites if privacy_view.is_private else {}

            # Create category with permissions (FIXED LINE)
            category = await guild.create_category(
                name=category_name,
                overwrites=final_overwrites
            )
            logging.info(f"📁 Created category '{category_name}' in {guild.name}")

            # Rest of the code remains the same...

            # Create channels
            created = []
            for ch_name in text_channels:
                await guild.create_text_channel(ch_name, category=category)
                created.append(ch_name)
                logging.info(f"📄 Created channel '{ch_name}' in '{category_name}'")

            # Final response
            embed = discord.Embed(
                title=f"Created: {category_name}",
                description=f"**Channels:** {', '.join(created)}",
                color=discord.Color.green()
            )
            if roles:
                embed.add_field(name="🔒 Accessible by", value="\n".join(role.mention for role in roles))
            await ctx.send(embed=embed)

        except discord.HTTPException as e:
            logging.error(f"Category creation failed: {str(e)}")
            await ctx.send(f"❌ Error creating category: {str(e)}", delete_after=5)
        finally:
            # Cleanup messages
            try:
                await privacy_msg.delete()
                if 'role_msg' in locals():
                    await role_msg.delete()
            except discord.NotFound:
                pass

    logging.info(f"✅ Finished creating {len(categories)} categories in {guild.name}")

@bot.command(aliases=["rmcc"])
@commands.has_permissions(manage_channels=True)
async def delete_cat_chan(ctx, *, args: str):
    """Delete categories/channels with confirmation for categories"""

    category_name = None
    channel_name = None
    parts = args.split()
    
    for i, part in enumerate(parts):
        if part == "--cat" and i+1 < len(parts):
            category_name = " ".join(parts[i+1:]).split("--")[0].strip()
        if part == "--cha" and i+1 < len(parts):
            channel_name = " ".join(parts[i+1:]).split("--")[0].strip()

    guild = ctx.guild
    deleted = []
    confirmation_msg = None

    try:
        if channel_name:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if channel:
                await channel.delete()
                deleted.append(f"Channel '#{channel_name}'")
                logging.info(f"🗑️ Deleted channel '{channel_name}' in {guild.name} by {ctx.author}")
            else:
                await ctx.send(f"⚠️ Channel `{channel_name}` not found!", delete_after=5)

        if category_name:
            category = discord.utils.get(guild.categories, name=category_name)
            if category:
                channels = category.channels
                
                confirm_embed = discord.Embed(
                    title="⚠️ Confirm Category Deletion",
                    description=f"Delete **{category_name}** and its **{len(channels)}** channels?",
                    color=discord.Color.orange()
                )
                confirm_embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
                
                confirmation_msg = await ctx.send(embed=confirm_embed)
                await confirmation_msg.add_reaction('✅')
                await confirmation_msg.add_reaction('❌')

                def check(reaction, user):
                    return (
                        user == ctx.author and
                        str(reaction.emoji) in ['✅', '❌'] and
                        reaction.message.id == confirmation_msg.id
                    )

                try:
                    reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                    
                    if str(reaction.emoji) == '✅':
                        for channel in channels:
                            await channel.delete()
                            logging.info(f"🗑️ Deleted channel '{channel.name}' in category '{category_name}'")
                        
                        await category.delete()
                        deleted.append(f"Category '{category_name}' (with {len(channels)} channels)")
                        logging.info(f"🗑️ Deleted category '{category_name}' in {guild.name} by {ctx.author}")
                    else:
                        await ctx.send("🚫 Deletion cancelled.", delete_after=5)
                        return
                        
                except asyncio.TimeoutError:
                    await ctx.send("🕒 Confirmation timed out. Deletion cancelled.", delete_after=5)
                    return
            else:
                await ctx.send(f"⚠️ Category `{category_name}` not found!", delete_after=5)

        if deleted:
            final_embed = discord.Embed(
                description=f"✅ Successfully deleted:\n{'\n'.join(deleted)}",
                color=discord.Color.green()
            )
            await ctx.send(embed=final_embed)
        else:
            await ctx.send("⚠️ No valid deletions performed", delete_after=5)

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage channels!", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Error: {str(e)}", delete_after=5)
    finally:
        if confirmation_msg:
            await confirmation_msg.delete()

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
        # Confirmation embed
        action = "all unpinned messages" if amount == "-" else f"{amount} messages"
        confirm_embed = discord.Embed(
            title="⚠️ Confirm Message Deletion",
            description=f"You are about to delete {action}. Continue?",
            color=discord.Color.orange()
        )
        confirm_embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
        confirmation_msg = await ctx.send(embed=confirm_embed)
        await confirmation_msg.add_reaction('✅')
        await confirmation_msg.add_reaction('❌')

        # Reaction check
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == confirmation_msg.id

        try:
            reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                await confirmation_msg.delete()
                
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
            else:
                await ctx.send("🚫 Deletion cancelled.", delete_after=5)

        except asyncio.TimeoutError:
            await ctx.send("🕒 Confirmation timed out. Deletion cancelled.", delete_after=5)
        finally:
            try:
                await confirmation_msg.delete()
            except discord.NotFound:
                pass

    except ValueError:
        embed = discord.Embed(
            description="⚠️ Invalid amount. Use number or '-'",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)

@bot.command(aliases=["clearB"])
@commands.has_permissions(manage_messages=True)
async def delete_bot_messages(ctx, limit: int = 5):
    """Delete the bot's recent messages"""
    # Confirmation embed
    confirm_embed = discord.Embed(
        title="⚠️ Confirm Bot Message Deletion",
        description=f"You are about to delete {limit} bot messages. Continue?",
        color=discord.Color.orange()
    )
    confirm_embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
    confirmation_msg = await ctx.send(embed=confirm_embed)
    await confirmation_msg.add_reaction('✅')
    await confirmation_msg.add_reaction('❌')

    # Reaction check
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == confirmation_msg.id

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        if str(reaction.emoji) == '✅':
            await confirmation_msg.delete()
            
            def is_bot(m):
                return m.author == bot.user
            
            deleted = await ctx.channel.purge(limit=limit, check=is_bot)
            embed = discord.Embed(
                description=f"🤖 Deleted **{len(deleted)}** bot messages",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, delete_after=5)
            logging.info(f"Deleted bot messages in {ctx.channel} by {ctx.author}")
        else:
            await ctx.send("🚫 Deletion cancelled.", delete_after=5)

    except asyncio.TimeoutError:
        await ctx.send("🕒 Confirmation timed out. Deletion cancelled.", delete_after=5)
    finally:
        try:
            await confirmation_msg.delete()
        except discord.NotFound:
            pass

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
                  "!h        -> Show this message\n"
                  "!info     -> Server statistics\n"
                  "!weather  -> Check city weather\n"
                  "!clearB   -> Remove bot messages\n"
                  "```",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Moderation Commands",
            value="```"
                  "!channel <category> <name> -> Create channel\n"
                  "!categories <names...>     -> Create categories\n"
                  "!modcat <category> [action]-> Modify category access\n"
                  "!rmcc [--cat] [--cha]      -> Delete categories/channels\n"
                  "!status                    -> Change bot status\n"
                  "!clear                     -> Clear messages\n"
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
# CHANGE CATEGORY ACCESS
# ========================
@bot.command(aliases=["modcat", "modify_category"])
@commands.has_permissions(administrator=True)
async def modify_category_access(ctx, category_name: str, action: str = "add"):
    """
    Modifier l'accès d'une catégorie pour certains rôles
    Usage: !modify_category_access <category_name> [add/remove]
    """
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name=category_name)
    
    if not category:
        await ctx.send(f"❌ Category `{category_name}` not found!", delete_after=5)
        return
    
    # Vérifier l'action
    if action.lower() not in ["add", "remove"]:
        await ctx.send("❌ Action must be: `add` or `remove`", delete_after=5)
        return

    # Créer une version modifiée de RoleSelectView pour cette commande
    class FilteredRoleSelectView(discord.ui.View):
        def __init__(self, ctx, action_type, category):
            super().__init__(timeout=30.0)
            self.ctx = ctx
            self.selected_roles = []
            
            # Get eligible roles (excluding @everyone and roles above bot)
            all_roles = [role for role in ctx.guild.roles 
                        if role.name != "@everyone" 
                        and role < ctx.guild.me.top_role]

            # Apply filtering based on action
            if action_type == "add":
                # Pour "add", exclure les rôles qui ont déjà accès
                current_access_roles = {role.id for role, overwrite in category.overwrites.items() 
                                       if isinstance(role, discord.Role) and overwrite.view_channel is True}
                roles = [role for role in all_roles if role.id not in current_access_roles]
            elif action_type == "remove":
                # Pour "remove", montrer seulement les rôles qui ont accès
                access_roles = {role.id for role, overwrite in category.overwrites.items() 
                               if isinstance(role, discord.Role) and overwrite.view_channel is True}
                roles = [role for role in all_roles if role.id in access_roles]
            else:
                roles = all_roles

            # Only add dropdown if there are roles available
            if roles:
                self.select = discord.ui.Select(
                    placeholder="Select roles...",
                    min_values=1,
                    max_values=min(25, len(roles)),
                    options=[discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
                )
                self.select.callback = self.select_callback
                self.add_item(self.select)
            else:
                self.selected_roles = None  # Special value to indicate no roles available

        async def select_callback(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return
                
            self.selected_roles = [interaction.guild.get_role(int(id)) for id in self.select.values]
            await interaction.response.defer()
            self.stop()
    
    # Sélection des rôles avec filtrage selon l'action
    role_view = FilteredRoleSelectView(ctx, action.lower(), category)
    
    if role_view.selected_roles is None:
        await ctx.send("⚠️ No eligible roles found.", delete_after=5)
        return
    
    embed = discord.Embed(
        title=f"Modify Access: {category_name}",
        description=f"**Action:** {action.title()}\nSelect roles to {action}:",
        color=discord.Color.blue()
    )
    role_msg = await ctx.send(embed=embed, view=role_view)
    await role_view.wait()
    
    if not role_view.selected_roles:
        await ctx.send("⚠️ No roles selected. Operation cancelled.", delete_after=5)
        return
    
    # Confirmation avec boutons
    selected_roles = role_view.selected_roles
    confirm_embed = discord.Embed(
        title=f"⚠️ Confirm Category Access Modification",
        description=f"**Category:** {category_name}\n**Action:** {action.title()}",
        color=discord.Color.orange()
    )
    confirm_embed.add_field(
        name="🎭 Selected Roles:",
        value="\n".join(role.mention for role in selected_roles),
        inline=False
    )
    confirm_embed.add_field(
        name="📢 Affected Channels:",
        value=f"{len(category.channels)} channels will be modified",
        inline=False
    )
    confirm_embed.set_footer(text="Click ✅ to confirm or ❌ to cancel")
    
    # Créer les boutons de confirmation
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30.0)
            self.confirmed = None

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
        async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Only the command author can confirm.", ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Only the command author can cancel.", ephemeral=True)
                return
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    confirm_view = ConfirmView()
    confirm_msg = await ctx.send(embed=confirm_embed, view=confirm_view)
    await confirm_view.wait()
    
    if confirm_view.confirmed is None:
        await ctx.send("🕒 Confirmation timed out. Operation cancelled.", delete_after=5)
        return
    elif not confirm_view.confirmed:
        await ctx.send("🚫 Operation cancelled.", delete_after=5)
        return
    
    try:
        channels_modified = []
        
        if action.lower() == "add":
            # Ajouter l'accès aux rôles sélectionnés
            current_overwrites = category.overwrites
            
            # S'assurer que @everyone ne peut pas voir si c'est privé
            if guild.default_role not in current_overwrites or current_overwrites[guild.default_role].view_channel is not False:
                current_overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            
            for role in selected_roles:
                # Vérifier si c'est un rôle "Guest" ou similaire pour appliquer les restrictions
                if "guest" in role.name.lower() or "invite" in role.name.lower():
                    current_overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False,
                        send_messages_in_threads=False
                    )
                else:
                    current_overwrites[role] = discord.PermissionOverwrite(view_channel=True)

            # Appliquer à la catégorie
            await category.edit(overwrites=current_overwrites)
            
            # Appliquer à tous les canaux de la catégorie
            for channel in category.channels:
                channel_overwrites = channel.overwrites.copy()
                
                # S'assurer que @everyone ne peut pas voir
                if guild.default_role not in channel_overwrites or channel_overwrites[guild.default_role].view_channel is not False:
                    channel_overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                
                for role in selected_roles:
                    # Vérifier si c'est un rôle "Guest" ou similaire pour appliquer les restrictions
                    if "guest" in role.name.lower() or "invite" in role.name.lower():
                        channel_overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=False,
                            add_reactions=False,
                            create_public_threads=False,
                            create_private_threads=False,
                            send_messages_in_threads=False
                        )
                    else:
                        channel_overwrites[role] = discord.PermissionOverwrite(view_channel=True)

                await channel.edit(overwrites=channel_overwrites)
                channels_modified.append(channel.name)
            
            action_text = f"Added access for {len(selected_roles)} roles"
            
        elif action.lower() == "remove":
            # Retirer l'accès aux rôles sélectionnés
            current_overwrites = category.overwrites.copy()
            
            for role in selected_roles:
                if role in current_overwrites:
                    del current_overwrites[role]
            
            # Appliquer à la catégorie
            await category.edit(overwrites=current_overwrites)
            
            # Appliquer à tous les canaux de la catégorie
            for channel in category.channels:
                channel_overwrites = channel.overwrites.copy()
                
                for role in selected_roles:
                    if role in channel_overwrites:
                        del channel_overwrites[role]
                
                await channel.edit(overwrites=channel_overwrites)
                channels_modified.append(channel.name)
            
            action_text = f"Removed access for {len(selected_roles)} roles"
        
        # Message de confirmation
        embed = discord.Embed(
            title=f"✅ Modified: {category_name}",
            description=f"**Action:** {action_text}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🎭 Roles affected:",
            value="\n".join(role.mention for role in selected_roles),
            inline=False
        )
        
        # Afficher les canaux modifiés
        if channels_modified:
            channel_list = ", ".join(f"#{ch}" for ch in channels_modified[:10])  # Limiter à 10 pour éviter les messages trop longs
            if len(channels_modified) > 10:
                channel_list += f" (+{len(channels_modified) - 10} more)"
            
            embed.add_field(
                name=f"📢 Channels modified [{len(channels_modified)}]:",
                value=channel_list,
                inline=False
            )
        
        # Afficher les rôles qui ont actuellement accès
        current_roles = [role for role, overwrite in category.overwrites.items() 
                        if isinstance(role, discord.Role) and role != guild.default_role 
                        and overwrite.view_channel is True]
        
        if current_roles:
            embed.add_field(
                name="🔓 Current access:",
                value="\n".join(role.mention for role in current_roles),
                inline=False
            )
        else:
            embed.add_field(
                name="🌍 Access:",
                value="Public (everyone can see)",
                inline=False
            )
        
        await ctx.send(embed=embed)
        logging.info(f"🔧 Modified category '{category_name}' and {len(channels_modified)} channels access in {guild.name} by {ctx.author} - {action_text}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permissions to manage channels!", delete_after=5)
        logging.error(f"🚫 Permission denied for category modification in {guild.name}")
    except discord.HTTPException as e:
        logging.error(f"Category modification failed: {str(e)}")
        await ctx.send(f"❌ Error modifying category: {str(e)}", delete_after=5)
    finally:
        # Supprimer les messages temporaires après un délai
        await asyncio.sleep(2)  # Petit délai pour laisser voir la confirmation finale
        try:
            await role_msg.delete()
            await confirm_msg.delete()
        except discord.NotFound:
            pass


# ========================
# GUESTS MANAGEMENT
# ========================
@bot.command(aliases=["select_guest", "guest_select"])
@commands.has_permissions(administrator=True)
async def add_guest_selective(ctx, role_name: str = "Guest"):
    """
    Ajoute un rôle à des catégories sélectionnées interactivement
    Usage: !add_guest_selective [nom_du_role]
    """
    guild = ctx.guild
    
    # Vérifier que le rôle existe
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        embed = discord.Embed(
            title="❌ Rôle non trouvé",
            description=f"Le rôle `{role_name}` n'existe pas sur ce serveur.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Récupérer toutes les catégories
    categories = guild.categories
    if not categories:
        embed = discord.Embed(
            title="⚠️ Aucune catégorie",
            description="Ce serveur ne contient aucune catégorie.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return
    
    # Créer une vue de sélection pour les catégories
    class CategorySelectView(discord.ui.View):
        def __init__(self, ctx, categories, role):
            super().__init__(timeout=120.0)  # 2 minutes
            self.ctx = ctx
            self.role = role
            self.selected_categories = []
            
            # Diviser les catégories en groupes de 25 (limite Discord)
            self.category_chunks = [categories[i:i+25] for i in range(0, len(categories), 25)]
            self.current_chunk = 0
            
            self.create_select_menu()
            self.add_navigation_buttons()
        
        def create_select_menu(self):
            # Supprimer l'ancien menu s'il existe
            for item in self.children[:]:
                if isinstance(item, discord.ui.Select):
                    self.remove_item(item)
            
            # Créer le nouveau menu pour le chunk actuel
            chunk = self.category_chunks[self.current_chunk]
            options = []
            
            for category in chunk:
                # Vérifier si le rôle a déjà accès
                has_access = (self.role in category.overwrites and 
                             category.overwrites[self.role].view_channel is True)
                
                emoji = "✅" if has_access else "📁"
                description = f"{len(category.channels)} canaux"
                if has_access:
                    description += " (déjà accès)"
                
                options.append(discord.SelectOption(
                    label=category.name[:100],  # Limite de Discord
                    value=str(category.id),
                    description=description[:100],
                    emoji=emoji
                ))
            
            if options:
                select = discord.ui.Select(
                    placeholder=f"Sélectionnez les catégories (Page {self.current_chunk + 1}/{len(self.category_chunks)})",
                    min_values=0,
                    max_values=len(options),
                    options=options,
                    row=0
                )
                select.callback = self.select_callback
                self.add_item(select)
        
        def add_navigation_buttons(self):
            # Boutons de navigation (seulement si plusieurs pages)
            if len(self.category_chunks) > 1:
                # Bouton Précédent
                prev_button = discord.ui.Button(
                    label="◀️ Précédent",
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_chunk == 0,
                    row=1
                )
                prev_button.callback = self.prev_page
                self.add_item(prev_button)
                
                # Bouton Suivant
                next_button = discord.ui.Button(
                    label="Suivant ▶️",
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_chunk >= len(self.category_chunks) - 1,
                    row=1
                )
                next_button.callback = self.next_page
                self.add_item(next_button)
            
            # Bouton de confirmation
            confirm_button = discord.ui.Button(
                label=f"Confirmer ({len(self.selected_categories)} sélectionnées)",
                style=discord.ButtonStyle.green,
                emoji="✅",
                disabled=len(self.selected_categories) == 0,
                row=2
            )
            confirm_button.callback = self.confirm_selection
            self.add_item(confirm_button)
            
            # Bouton d'annulation
            cancel_button = discord.ui.Button(
                label="Annuler",
                style=discord.ButtonStyle.red,
                emoji="❌",
                row=2
            )
            cancel_button.callback = self.cancel_selection
            self.add_item(cancel_button)
        
        async def select_callback(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut sélectionner.", ephemeral=True)
                return
            
            # Récupérer les catégories sélectionnées pour cette page
            selected_ids = interaction.data['values']
            chunk = self.category_chunks[self.current_chunk]
            
            # Retirer les catégories de cette page des sélections précédentes
            chunk_ids = {str(cat.id) for cat in chunk}
            self.selected_categories = [cat for cat in self.selected_categories 
                                       if str(cat.id) not in chunk_ids]
            
            # Ajouter les nouvelles sélections
            for cat_id in selected_ids:
                category = discord.utils.get(chunk, id=int(cat_id))
                if category:
                    self.selected_categories.append(category)
            
            # Mettre à jour les boutons
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def prev_page(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut naviguer.", ephemeral=True)
                return
            
            self.current_chunk = max(0, self.current_chunk - 1)
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def next_page(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut naviguer.", ephemeral=True)
                return
            
            self.current_chunk = min(len(self.category_chunks) - 1, self.current_chunk + 1)
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def confirm_selection(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut confirmer.", ephemeral=True)
                return
            
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        
        async def cancel_selection(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut annuler.", ephemeral=True)
                return
            
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    # Créer et afficher la vue de sélection
    view = CategorySelectView(ctx, categories, role)
    
    embed = discord.Embed(
        title=f"🎯 Sélection de catégories pour: {role_name}",
        description=f"**Rôle:** {role.mention}\n"
                   f"**Total catégories:** {len(categories)}\n\n"
                   f"**Instructions:**\n"
                   f"• Sélectionnez les catégories où ajouter le rôle\n"
                   f"• ✅ = Rôle a déjà accès\n"
                   f"• 📁 = Rôle n'a pas accès\n"
                   f"• Utilisez les boutons pour naviguer entre les pages",
        color=discord.Color.blue()
    )
    
    selection_msg = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    # Vérifier la confirmation
    if not hasattr(view, 'confirmed') or view.confirmed is None:
        await ctx.send("🕒 Sélection expirée - Opération annulée.", delete_after=5)
        return
    elif not view.confirmed:
        await ctx.send("🚫 Opération annulée par l'utilisateur.", delete_after=5)
        return
    
    if not view.selected_categories:
        await ctx.send("⚠️ Aucune catégorie sélectionnée.", delete_after=5)
        return
    
    # Confirmation finale avec résumé
    final_confirm_embed = discord.Embed(
        title="⚠️ Confirmation finale",
        description=f"**Rôle à ajouter:** {role.mention}\n"
                   f"**Catégories sélectionnées:** {len(view.selected_categories)}",
        color=discord.Color.orange()
    )
    
    # Afficher les catégories sélectionnées
    selected_text = []
    total_channels = 0
    for cat in view.selected_categories:
        total_channels += len(cat.channels)
        selected_text.append(f"📁 **{cat.name}** ({len(cat.channels)} canaux)")
    
    final_confirm_embed.add_field(
        name="📋 Catégories qui seront modifiées:",
        value="\n".join(selected_text),
        inline=False
    )
    
    final_confirm_embed.add_field(
        name="📊 Impact:",
        value=f"**{len(view.selected_categories)}** catégories\n"
              f"**{total_channels}** canaux au total",
        inline=False
    )
    
    final_confirm_embed.set_footer(text="Dernière chance pour confirmer !")
    
    # Boutons de confirmation finale
    class FinalConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30.0)
            self.confirmed = None

        @discord.ui.button(label="Confirmer et appliquer", style=discord.ButtonStyle.green, emoji="✅")
        async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut confirmer.", ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Annuler", style=discord.ButtonStyle.red, emoji="❌")
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut annuler.", ephemeral=True)
                return
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    final_view = FinalConfirmView()
    final_msg = await ctx.send(embed=final_confirm_embed, view=final_view)
    await final_view.wait()
    
    if final_view.confirmed is None:
        await ctx.send("🕒 Confirmation expirée - Opération annulée.", delete_after=5)
        return
    elif not final_view.confirmed:
        await ctx.send("🚫 Opération annulée.", delete_after=5)
        return
    
    # Appliquer les modifications
    try:
        await final_msg.edit(embed=discord.Embed(
            title="⏳ Application des modifications...",
            description=f"Traitement de {len(view.selected_categories)} catégories...",
            color=discord.Color.yellow()
        ), view=None)
        
        success_count = 0
        error_count = 0
        processed_channels = 0
        errors = []
        
        for i, category in enumerate(view.selected_categories):
            try:
                # Mise à jour du statut
                if i % 3 == 0:  # Mettre à jour plus souvent car moins de catégories
                    progress_embed = discord.Embed(
                        title="⏳ Traitement en cours...",
                        description=f"📁 **{category.name}** ({i+1}/{len(view.selected_categories)})",
                        color=discord.Color.yellow()
                    )
                    await final_msg.edit(embed=progress_embed)
                
                # Modifier la catégorie
                current_overwrites = category.overwrites.copy()
                current_overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                await category.edit(overwrites=current_overwrites)
                
                # Modifier tous les canaux de la catégorie
                for channel in category.channels:
                    try:
                        channel_overwrites = channel.overwrites.copy()
                        channel_overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                        await channel.edit(overwrites=channel_overwrites)
                        processed_channels += 1
                    except discord.HTTPException as e:
                        errors.append(f"Canal {channel.name}: {str(e)}")
                        error_count += 1
                
                success_count += 1
                logging.info(f"✅ Added {role_name} to selected category '{category.name}'")
                
                # Délai pour éviter le rate limiting
                await asyncio.sleep(0.5)
                
            except discord.HTTPException as e:
                error_count += 1
                errors.append(f"Catégorie {category.name}: {str(e)}")
                logging.error(f"❌ Failed to add {role_name} to category '{category.name}': {str(e)}")
        
        # Message de résultat final
        if success_count > 0:
            result_embed = discord.Embed(
                title="✅ Modifications appliquées avec succès!",
                color=discord.Color.green()
            )
            
            result_embed.add_field(
                name="📊 Résultats:",
                value=f"```"
                      f"✅ Catégories modifiées: {success_count}/{len(view.selected_categories)}\n"
                      f"📢 Canaux modifiés: {processed_channels}\n"
                      f"❌ Erreurs: {error_count}\n"
                      f"🎭 Rôle ajouté: {role_name}"
                      f"```",
                inline=False
            )
            
            # Lister les catégories modifiées avec succès
            success_categories = [cat.name for cat in view.selected_categories]
            if len(success_categories) <= 10:
                result_embed.add_field(
                    name="📁 Catégories modifiées:",
                    value="\n".join(f"✅ {cat}" for cat in success_categories),
                    inline=False
                )
            else:
                result_embed.add_field(
                    name="📁 Catégories modifiées:",
                    value=f"✅ {len(success_categories)} catégories (voir logs pour détails)",
                    inline=False
                )
            
            if errors and len(errors) <= 5:
                result_embed.add_field(
                    name="⚠️ Erreurs:",
                    value="\n".join(f"• {error}" for error in errors[:5]),
                    inline=False
                )
        else:
            result_embed = discord.Embed(
                title="❌ Échec des modifications",
                description="Aucune catégorie n'a pu être modifiée.",
                color=discord.Color.red()
            )
        
        await final_msg.edit(embed=result_embed)
        
        # Supprimer le message de sélection après un délai
        await asyncio.sleep(3)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        
        logging.info(f"🎯 Selective role addition completed: {success_count} categories modified by {ctx.author}")
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erreur inattendue",
            description=f"```{str(e)}```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        logging.error(f"Selective role addition error: {str(e)}")

# Commande rapide pour des catégories spécifiques par nom
@bot.command(aliases=["quick_guest"])
@commands.has_permissions(administrator=True)
async def add_guest_to_specific(ctx, role_name: str = "Guest", *category_names):
    """
    Ajoute un rôle à des catégories spécifiques par leur nom
    Usage: !add_guest_to_specific [role] "catégorie1" "catégorie2" ...
    """
    guild = ctx.guild
    
    if not category_names:
        await ctx.send("⚠️ Usage: `!quick_guest [role] \"catégorie1\" \"catégorie2\" ...`")
        return
    
    # Vérifier le rôle
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle `{role_name}` non trouvé!")
        return
    
    # Trouver les catégories
    found_categories = []
    not_found = []
    
    for cat_name in category_names:
        category = discord.utils.get(guild.categories, name=cat_name)
        if category:
            found_categories.append(category)
        else:
            not_found.append(cat_name)
    
    if not found_categories:
        await ctx.send("❌ Aucune catégorie trouvée avec ces noms!")
        return
    
    # Confirmation rapide
    confirm_text = "\n".join(f"📁 {cat.name}" for cat in found_categories)
    if not_found:
        confirm_text += f"\n\n❌ Non trouvées: {', '.join(not_found)}"
    
    embed = discord.Embed(
        title=f"⚠️ Ajouter {role_name} à {len(found_categories)} catégories?",
        description=confirm_text,
        color=discord.Color.orange()
    )
    
    # Confirmation simple avec réactions
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
    
    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        if str(reaction.emoji) == '✅':
            # Appliquer les modifications
            success = 0
            for category in found_categories:
                try:
                    overwrites = category.overwrites.copy()
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                    await category.edit(overwrites=overwrites)
                    
                    # Appliquer aux canaux
                    for channel in category.channels:
                        ch_overwrites = channel.overwrites.copy()
                        ch_overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                        await channel.edit(overwrites=ch_overwrites)
                    
                    success += 1
                    await asyncio.sleep(0.3)
                    
                except discord.HTTPException:
                    pass
            
            await ctx.send(f"✅ Rôle **{role_name}** ajouté à {success}/{len(found_categories)} catégories!")
        else:
            await ctx.send("🚫 Opération annulée.")
            
    except asyncio.TimeoutError:
        await ctx.send("🕒 Timeout - Opération annulée.")
    finally:
        try:
            await msg.delete()
        except discord.NotFound:
            pass

# ========================
# REMOVE GUESTS FROM CATEGORIES
# ========================

@bot.command(aliases=["remove_guest", "guest_remove"])
@commands.has_permissions(administrator=True)
async def remove_guest_selective(ctx, role_name: str = "Guest"):
    """
    Enlève un rôle de catégories sélectionnées interactivement
    Usage: !remove_guest_selective [nom_du_role]
    """
    guild = ctx.guild
    
    # Vérifier que le rôle existe
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        embed = discord.Embed(
            title="❌ Rôle non trouvé",
            description=f"Le rôle `{role_name}` n'existe pas sur ce serveur.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Récupérer seulement les catégories où le rôle a accès
    categories_with_access = []
    for category in guild.categories:
        if (role in category.overwrites and 
            category.overwrites[role].view_channel is True):
            categories_with_access.append(category)
    
    if not categories_with_access:
        embed = discord.Embed(
            title="⚠️ Aucun accès trouvé",
            description=f"Le rôle `{role_name}` n'a accès à aucune catégorie privée.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return
    
    # Créer une vue de sélection pour les catégories avec accès
    class RemoveCategorySelectView(discord.ui.View):
        def __init__(self, ctx, categories, role):
            super().__init__(timeout=120.0)
            self.ctx = ctx
            self.role = role
            self.selected_categories = []
            
            # Diviser les catégories en groupes de 25
            self.category_chunks = [categories[i:i+25] for i in range(0, len(categories), 25)]
            self.current_chunk = 0
            
            self.create_select_menu()
            self.add_navigation_buttons()
        
        def create_select_menu(self):
            # Supprimer l'ancien menu s'il existe
            for item in self.children[:]:
                if isinstance(item, discord.ui.Select):
                    self.remove_item(item)
            
            # Créer le nouveau menu pour le chunk actuel
            chunk = self.category_chunks[self.current_chunk]
            options = []
            
            for category in chunk:
                description = f"{len(category.channels)} canaux - ACCÈS ACTUEL"
                
                options.append(discord.SelectOption(
                    label=category.name[:100],
                    value=str(category.id),
                    description=description[:100],
                    emoji="🔓"
                ))
            
            if options:
                select = discord.ui.Select(
                    placeholder=f"Sélectionnez les catégories à retirer (Page {self.current_chunk + 1}/{len(self.category_chunks)})",
                    min_values=0,
                    max_values=len(options),
                    options=options,
                    row=0
                )
                select.callback = self.select_callback
                self.add_item(select)
        
        def add_navigation_buttons(self):
            # Boutons de navigation (seulement si plusieurs pages)
            if len(self.category_chunks) > 1:
                # Bouton Précédent
                prev_button = discord.ui.Button(
                    label="◀️ Précédent",
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_chunk == 0,
                    row=1
                )
                prev_button.callback = self.prev_page
                self.add_item(prev_button)
                
                # Bouton Suivant
                next_button = discord.ui.Button(
                    label="Suivant ▶️",
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_chunk >= len(self.category_chunks) - 1,
                    row=1
                )
                next_button.callback = self.next_page
                self.add_item(next_button)
            
            # Bouton de confirmation
            confirm_button = discord.ui.Button(
                label=f"Retirer l'accès ({len(self.selected_categories)} sélectionnées)",
                style=discord.ButtonStyle.red,
                emoji="🔒",
                disabled=len(self.selected_categories) == 0,
                row=2
            )
            confirm_button.callback = self.confirm_selection
            self.add_item(confirm_button)
            
            # Bouton d'annulation
            cancel_button = discord.ui.Button(
                label="Annuler",
                style=discord.ButtonStyle.secondary,
                emoji="❌",
                row=2
            )
            cancel_button.callback = self.cancel_selection
            self.add_item(cancel_button)
        
        async def select_callback(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut sélectionner.", ephemeral=True)
                return
            
            # Récupérer les catégories sélectionnées pour cette page
            selected_ids = interaction.data['values']
            chunk = self.category_chunks[self.current_chunk]
            
            # Retirer les catégories de cette page des sélections précédentes
            chunk_ids = {str(cat.id) for cat in chunk}
            self.selected_categories = [cat for cat in self.selected_categories 
                                       if str(cat.id) not in chunk_ids]
            
            # Ajouter les nouvelles sélections
            for cat_id in selected_ids:
                category = discord.utils.get(chunk, id=int(cat_id))
                if category:
                    self.selected_categories.append(category)
            
            # Mettre à jour les boutons
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def prev_page(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut naviguer.", ephemeral=True)
                return
            
            self.current_chunk = max(0, self.current_chunk - 1)
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def next_page(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut naviguer.", ephemeral=True)
                return
            
            self.current_chunk = min(len(self.category_chunks) - 1, self.current_chunk + 1)
            self.clear_items()
            self.create_select_menu()
            self.add_navigation_buttons()
            
            await interaction.response.edit_message(view=self)
        
        async def confirm_selection(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut confirmer.", ephemeral=True)
                return
            
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        
        async def cancel_selection(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut annuler.", ephemeral=True)
                return
            
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    # Créer et afficher la vue de sélection
    view = RemoveCategorySelectView(ctx, categories_with_access, role)
    
    embed = discord.Embed(
        title=f"🔒 Retirer l'accès pour: {role_name}",
        description=f"**Rôle:** {role.mention}\n"
                   f"**Catégories avec accès:** {len(categories_with_access)}\n\n"
                   f"**Instructions:**\n"
                   f"• Sélectionnez les catégories d'où retirer le rôle\n"
                   f"• 🔓 = Rôle a actuellement accès\n"
                   f"• Utilisez les boutons pour naviguer entre les pages",
        color=discord.Color.orange()
    )
    
    selection_msg = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    # Vérifier la confirmation
    if not hasattr(view, 'confirmed') or view.confirmed is None:
        await ctx.send("🕒 Sélection expirée - Opération annulée.", delete_after=5)
        return
    elif not view.confirmed:
        await ctx.send("🚫 Opération annulée par l'utilisateur.", delete_after=5)
        return
    
    if not view.selected_categories:
        await ctx.send("⚠️ Aucune catégorie sélectionnée.", delete_after=5)
        return
    
    # Confirmation finale avec résumé
    final_confirm_embed = discord.Embed(
        title="⚠️ Confirmation - Retrait d'accès",
        description=f"**Rôle à retirer:** {role.mention}\n"
                   f"**Catégories sélectionnées:** {len(view.selected_categories)}",
        color=discord.Color.red()
    )
    
    # Afficher les catégories sélectionnées
    selected_text = []
    total_channels = 0
    for cat in view.selected_categories:
        total_channels += len(cat.channels)
        selected_text.append(f"🔒 **{cat.name}** ({len(cat.channels)} canaux)")
    
    final_confirm_embed.add_field(
        name="📋 Catégories qui perdront l'accès:",
        value="\n".join(selected_text),
        inline=False
    )
    
    final_confirm_embed.add_field(
        name="📊 Impact:",
        value=f"**{len(view.selected_categories)}** catégories\n"
              f"**{total_channels}** canaux au total\n"
              f"⚠️ **ATTENTION:** L'accès sera complètement retiré!",
        inline=False
    )
    
    final_confirm_embed.set_footer(text="Cette action retirera définitivement l'accès!")
    
    # Boutons de confirmation finale
    class FinalConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30.0)
            self.confirmed = None

        @discord.ui.button(label="Confirmer le retrait", style=discord.ButtonStyle.red, emoji="🔒")
        async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut confirmer.", ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut annuler.", ephemeral=True)
                return
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    final_view = FinalConfirmView()
    final_msg = await ctx.send(embed=final_confirm_embed, view=final_view)
    await final_view.wait()
    
    if final_view.confirmed is None:
        await ctx.send("🕒 Confirmation expirée - Opération annulée.", delete_after=5)
        return
    elif not final_view.confirmed:
        await ctx.send("🚫 Opération annulée.", delete_after=5)
        return
    
    # Appliquer les modifications
    try:
        await final_msg.edit(embed=discord.Embed(
            title="⏳ Retrait des accès en cours...",
            description=f"Traitement de {len(view.selected_categories)} catégories...",
            color=discord.Color.yellow()
        ), view=None)
        
        success_count = 0
        error_count = 0
        processed_channels = 0
        errors = []
        
        for i, category in enumerate(view.selected_categories):
            try:
                # Mise à jour du statut
                if i % 3 == 0:
                    progress_embed = discord.Embed(
                        title="⏳ Retrait en cours...",
                        description=f"🔒 **{category.name}** ({i+1}/{len(view.selected_categories)})",
                        color=discord.Color.yellow()
                    )
                    await final_msg.edit(embed=progress_embed)
                
                # Retirer le rôle de la catégorie
                current_overwrites = category.overwrites.copy()
                if role in current_overwrites:
                    del current_overwrites[role]
                    await category.edit(overwrites=current_overwrites)
                
                # Retirer le rôle de tous les canaux de la catégorie
                for channel in category.channels:
                    try:
                        channel_overwrites = channel.overwrites.copy()
                        if role in channel_overwrites:
                            del channel_overwrites[role]
                            await channel.edit(overwrites=channel_overwrites)
                        processed_channels += 1
                    except discord.HTTPException as e:
                        errors.append(f"Canal {channel.name}: {str(e)}")
                        error_count += 1
                
                success_count += 1
                logging.info(f"🔒 Removed {role_name} from category '{category.name}'")
                
                # Délai pour éviter le rate limiting
                await asyncio.sleep(0.5)
                
            except discord.HTTPException as e:
                error_count += 1
                errors.append(f"Catégorie {category.name}: {str(e)}")
                logging.error(f"❌ Failed to remove {role_name} from category '{category.name}': {str(e)}")
        
        # Message de résultat final
        if success_count > 0:
            result_embed = discord.Embed(
                title="✅ Accès retiré avec succès!",
                color=discord.Color.green()
            )
            
            result_embed.add_field(
                name="📊 Résultats:",
                value=f"```"
                      f"🔒 Catégories modifiées: {success_count}/{len(view.selected_categories)}\n"
                      f"📢 Canaux modifiés: {processed_channels}\n"
                      f"❌ Erreurs: {error_count}\n"
                      f"🎭 Rôle retiré: {role_name}"
                      f"```",
                inline=False
            )
            
            # Lister les catégories modifiées avec succès
            success_categories = [cat.name for cat in view.selected_categories]
            if len(success_categories) <= 10:
                result_embed.add_field(
                    name="🔒 Accès retiré de:",
                    value="\n".join(f"✅ {cat}" for cat in success_categories),
                    inline=False
                )
            else:
                result_embed.add_field(
                    name="🔒 Accès retiré de:",
                    value=f"✅ {len(success_categories)} catégories (voir logs pour détails)",
                    inline=False
                )
            
            if errors and len(errors) <= 5:
                result_embed.add_field(
                    name="⚠️ Erreurs:",
                    value="\n".join(f"• {error}" for error in errors[:5]),
                    inline=False
                )
        else:
            result_embed = discord.Embed(
                title="❌ Échec du retrait",
                description="Aucune catégorie n'a pu être modifiée.",
                color=discord.Color.red()
            )
        
        await final_msg.edit(embed=result_embed)
        
        # Supprimer le message de sélection après un délai
        await asyncio.sleep(3)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        
        logging.info(f"🔒 Selective role removal completed: {success_count} categories modified by {ctx.author}")
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Erreur inattendue",
            description=f"```{str(e)}```",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        logging.error(f"Selective role removal error: {str(e)}")

# Commande rapide pour retirer des catégories spécifiques par nom
@bot.command(aliases=["quick_remove_guest"])
@commands.has_permissions(administrator=True)
async def remove_guest_from_specific(ctx, role_name: str = "Guest", *category_names):
    """
    Retire un rôle de catégories spécifiques par leur nom
    Usage: !remove_guest_from_specific [role] "catégorie1" "catégorie2" ...
    """
    guild = ctx.guild
    
    if not category_names:
        await ctx.send("⚠️ Usage: `!quick_remove_guest [role] \"catégorie1\" \"catégorie2\" ...`")
        return
    
    # Vérifier le rôle
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle `{role_name}` non trouvé!")
        return
    
    # Trouver les catégories et vérifier l'accès
    found_categories = []
    not_found = []
    no_access = []
    
    for cat_name in category_names:
        category = discord.utils.get(guild.categories, name=cat_name)
        if category:
            # Vérifier si le rôle a accès
            if (role in category.overwrites and 
                category.overwrites[role].view_channel is True):
                found_categories.append(category)
            else:
                no_access.append(cat_name)
        else:
            not_found.append(cat_name)
    
    if not found_categories:
        message = "❌ Aucune catégorie valide trouvée!"
        if not_found:
            message += f"\n🔍 Non trouvées: {', '.join(not_found)}"
        if no_access:
            message += f"\n🔒 Pas d'accès: {', '.join(no_access)}"
        await ctx.send(message)
        return
    
    # Confirmation rapide
    confirm_text = "\n".join(f"🔒 {cat.name}" for cat in found_categories)
    if not_found:
        confirm_text += f"\n\n❓ Non trouvées: {', '.join(not_found)}"
    if no_access:
        confirm_text += f"\n\n⚪ Pas d'accès: {', '.join(no_access)}"
    
    embed = discord.Embed(
        title=f"⚠️ Retirer {role_name} de {len(found_categories)} catégories?",
        description=confirm_text,
        color=discord.Color.red()
    )
    
    # Confirmation simple avec réactions
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
    
    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        if str(reaction.emoji) == '✅':
            # Appliquer les modifications
            success = 0
            for category in found_categories:
                try:
                    # Retirer de la catégorie
                    overwrites = category.overwrites.copy()
                    if role in overwrites:
                        del overwrites[role]
                        await category.edit(overwrites=overwrites)
                    
                    # Retirer des canaux
                    for channel in category.channels:
                        ch_overwrites = channel.overwrites.copy()
                        if role in ch_overwrites:
                            del ch_overwrites[role]
                            await channel.edit(overwrites=ch_overwrites)
                    
                    success += 1
                    await asyncio.sleep(0.3)
                    
                except discord.HTTPException:
                    pass
            
            await ctx.send(f"🔒 Rôle **{role_name}** retiré de {success}/{len(found_categories)} catégories!")
        else:
            await ctx.send("🚫 Opération annulée.")
            
    except asyncio.TimeoutError:
        await ctx.send("🕒 Timeout - Opération annulée.")
    finally:
        try:
            await msg.delete()
        except discord.NotFound:
            pass

# Commande pour voir les accès actuels d'un rôle
@bot.command(aliases=["check_guest", "guest_access"])
@commands.has_permissions(administrator=True)
async def check_role_access(ctx, role_name: str = "Guest"):
    """
    Affiche toutes les catégories auxquelles un rôle a accès
    Usage: !check_role_access [nom_du_role]
    """
    guild = ctx.guild
    
    # Vérifier que le rôle existe
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        embed = discord.Embed(
            title="❌ Rôle non trouvé",
            description=f"Le rôle `{role_name}` n'existe pas sur ce serveur.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Trouver toutes les catégories avec accès
    categories_with_access = []
    total_channels = 0
    
    for category in guild.categories:
        if (role in category.overwrites and 
            category.overwrites[role].view_channel is True):
            categories_with_access.append(category)
            total_channels += len(category.channels)
    
    # Créer l'embed de résultat
    embed = discord.Embed(
        title=f"🔍 Accès pour: {role_name}",
        description=f"**Rôle:** {role.mention}\n"
                   f"**Catégories avec accès:** {len(categories_with_access)}\n"
                   f"**Total des canaux:** {total_channels}",
        color=discord.Color.blue()
    )
    
    if categories_with_access:
        # Grouper par tranches de 20 pour éviter les messages trop longs
        category_chunks = [categories_with_access[i:i+20] for i in range(0, len(categories_with_access), 20)]
        
        for i, chunk in enumerate(category_chunks):
            field_name = "🔓 Catégories avec accès:" if i == 0 else f"🔓 Suite ({i+1}):"
            field_value = "\n".join(f"📁 **{cat.name}** ({len(cat.channels)} canaux)" for cat in chunk)
            embed.add_field(name=field_name, value=field_value, inline=False)
        
        # Boutons d'action
        class AccessActionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60.0)

            @discord.ui.button(label="Retirer des accès", style=discord.ButtonStyle.red, emoji="🔒")
            async def remove_access(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ Seul l'auteur peut utiliser cette action.", ephemeral=True)
                    return
                
                await interaction.response.send_message("🔄 Lancement de la sélection pour retirer les accès...", ephemeral=True)
                # Lancer la commande de retrait
                await remove_guest_selective(ctx, role_name)
                self.stop()

            @discord.ui.button(label="Ajouter des accès", style=discord.ButtonStyle.green, emoji="🔓")
            async def add_access(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ Seul l'auteur peut utiliser cette action.", ephemeral=True)
                    return
                
                await interaction.response.send_message("🔄 Lancement de la sélection pour ajouter des accès...", ephemeral=True)
                # Lancer la commande d'ajout
                await add_guest_selective(ctx, role_name)
                self.stop()
        
        view = AccessActionView()
        embed.set_footer(text="Utilisez les boutons ci-dessous pour modifier les accès")
        await ctx.send(embed=embed, view=view)
        
    else:
        embed.add_field(
            name="⚪ Aucun accès spécial",
            value=f"Le rôle `{role_name}` n'a accès à aucune catégorie privée.\n"
                  f"Il peut voir les catégories publiques comme tous les membres.",
            inline=False
        )
        
        # Bouton pour ajouter des accès
        class AddAccessView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60.0)

            @discord.ui.button(label="Ajouter des accès", style=discord.ButtonStyle.green, emoji="🔓")
            async def add_access(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("❌ Seul l'auteur peut utiliser cette action.", ephemeral=True)
                    return
                
                await interaction.response.send_message("🔄 Lancement de la sélection pour ajouter des accès...", ephemeral=True)
                await add_guest_selective(ctx, role_name)
                self.stop()
        
        view = AddAccessView()
        embed.set_footer(text="Utilisez le bouton ci-dessous pour ajouter des accès")
        await ctx.send(embed=embed, view=view)


# ========================
# NOUVELLE COMMANDE POUR GÉRER LES PERMISSIONS DE FAÇON GRANULAIRE
# ========================
@bot.command(aliases=["set_guest_perms"])
@commands.has_permissions(administrator=True)
async def set_guest_permissions(ctx, role_name: str = "Guest", permission_type: str = "readonly"):
    """
    Définit le type de permissions pour un rôle invité
    Types: readonly, full, custom
    Usage: !set_guest_permissions Guest readonly
    """
    guild = ctx.guild
    
    # Vérifier le rôle
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle `{role_name}` non trouvé!")
        return
    
    # Définir les types de permissions
    permission_types = {
        "readonly": {
            "name": "Lecture seule",
            "description": "Peut voir mais pas écrire",
            "perms": {
                "view_channel": True,
                "send_messages": False,
                "add_reactions": False,
                "create_public_threads": False,
                "create_private_threads": False,
                "send_messages_in_threads": False
            },
            "emoji": "👁️"
        },
        "full": {
            "name": "Accès complet",
            "description": "Peut voir et écrire",
            "perms": {
                "view_channel": True,
                "send_messages": True,
                "add_reactions": True,
                "create_public_threads": False,
                "create_private_threads": False,
                "send_messages_in_threads": True
            },
            "emoji": "✅"
        },
        "limited": {
            "name": "Accès limité",
            "description": "Peut voir, écrire mais pas créer de threads",
            "perms": {
                "view_channel": True,
                "send_messages": True,
                "add_reactions": True,
                "create_public_threads": False,
                "create_private_threads": False,
                "send_messages_in_threads": False
            },
            "emoji": "⚠️"
        }
    }
    
    if permission_type.lower() not in permission_types:
        embed = discord.Embed(
            title="❌ Type de permission invalide",
            description=f"Types disponibles: {', '.join(permission_types.keys())}",
            color=discord.Color.red()
        )
        for ptype, pdata in permission_types.items():
            embed.add_field(
                name=f"{pdata['emoji']} {ptype.title()}",
                value=pdata['description'],
                inline=True
            )
        await ctx.send(embed=embed)
        return
    
    selected_perms = permission_types[permission_type.lower()]
    
    # Trouver les catégories où le rôle a accès
    categories_with_access = []
    for category in guild.categories:
        if (role in category.overwrites and 
            category.overwrites[role].view_channel is True):
            categories_with_access.append(category)
    
    if not categories_with_access:
        await ctx.send(f"⚠️ Le rôle `{role_name}` n'a accès à aucune catégorie privée.")
        return
    
    # Confirmation
    embed = discord.Embed(
        title=f"⚠️ Modifier les permissions pour: {role_name}",
        description=f"**Nouveau type:** {selected_perms['emoji']} {selected_perms['name']}\n"
                   f"**Description:** {selected_perms['description']}\n"
                   f"**Catégories affectées:** {len(categories_with_access)}",
        color=discord.Color.orange()
    )
    
    # Afficher les détails des permissions
    perm_details = []
    for perm, value in selected_perms['perms'].items():
        emoji = "✅" if value else "❌"
        perm_name = perm.replace('_', ' ').title()
        perm_details.append(f"{emoji} {perm_name}")
    
    embed.add_field(
        name="🔧 Permissions détaillées:",
        value="\n".join(perm_details),
        inline=False
    )
    
    embed.add_field(
        name="📁 Catégories qui seront modifiées:",
        value="\n".join(f"📁 {cat.name}" for cat in categories_with_access[:10]) + 
              (f"\n... et {len(categories_with_access) - 10} autres" if len(categories_with_access) > 10 else ""),
        inline=False
    )
    
    # Boutons de confirmation
    class PermissionConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30.0)
            self.confirmed = None

        @discord.ui.button(label="Appliquer les permissions", style=discord.ButtonStyle.green, emoji="🔧")
        async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut confirmer.", ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()

        @discord.ui.button(label="Annuler", style=discord.ButtonStyle.red, emoji="❌")
        async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user != ctx.author:
                await interaction.response.send_message("❌ Seul l'auteur peut annuler.", ephemeral=True)
                return
            self.confirmed = False
            await interaction.response.defer()
            self.stop()
    
    view = PermissionConfirmView()
    msg = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    if view.confirmed is None:
        await ctx.send("🕒 Timeout - Opération annulée.", delete_after=5)
        return
    elif not view.confirmed:
        await ctx.send("🚫 Opération annulée.", delete_after=5)
        return
    
    # Appliquer les permissions
    try:
        await msg.edit(embed=discord.Embed(
            title="⏳ Application des nouvelles permissions...",
            description=f"Traitement de {len(categories_with_access)} catégories...",
            color=discord.Color.yellow()
        ), view=None)
        
        success_count = 0
        processed_channels = 0
        
        for i, category in enumerate(categories_with_access):
            try:
                # Mise à jour du statut
                if i % 3 == 0:
                    progress_embed = discord.Embed(
                        title="⏳ Mise à jour des permissions...",
                        description=f"🔧 **{category.name}** ({i+1}/{len(categories_with_access)})",
                        color=discord.Color.yellow()
                    )
                    await msg.edit(embed=progress_embed)
                
                # Modifier la catégorie
                current_overwrites = category.overwrites.copy()
                current_overwrites[role] = discord.PermissionOverwrite(**selected_perms['perms'])
                await category.edit(overwrites=current_overwrites)
                
                # Modifier tous les canaux
                for channel in category.channels:
                    channel_overwrites = channel.overwrites.copy()
                    channel_overwrites[role] = discord.PermissionOverwrite(**selected_perms['perms'])
                    await channel.edit(overwrites=channel_overwrites)
                    processed_channels += 1
                
                success_count += 1
                await asyncio.sleep(0.5)
                
            except discord.HTTPException as e:
                logging.error(f"Permission update failed for {category.name}: {str(e)}")
        
        # Résultat final
        result_embed = discord.Embed(
            title="✅ Permissions mises à jour!",
            description=f"**Type appliqué:** {selected_perms['emoji']} {selected_perms['name']}",
            color=discord.Color.green()
        )
        
        result_embed.add_field(
            name="📊 Résultats:",
            value=f"```"
                  f"🔧 Catégories modifiées: {success_count}\n"
                  f"📢 Canaux modifiés: {processed_channels}\n"
                  f"🎭 Rôle configuré: {role_name}"
                  f"```",
            inline=False
        )
        
        await msg.edit(embed=result_embed)
        logging.info(f"🔧 Updated permissions for {role_name} to {permission_type} in {success_count} categories")
        
    except Exception as e:
        await ctx.send(f"❌ Erreur: {str(e)}")
        logging.error(f"Permission update error: {str(e)}")

# ========================
# COMMANDE POUR VÉRIFIER LES PERMISSIONS ACTUELLES
# ========================
@bot.command(aliases=["check_perms"])
@commands.has_permissions(administrator=True)
async def check_role_permissions(ctx, role_name: str = "Guest", category_name: str = None):
    """
    Vérifie les permissions détaillées d'un rôle
    Usage: !check_perms Guest [catégorie]
    """
    guild = ctx.guild
    
    # Vérifier le rôle
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Rôle `{role_name}` non trouvé!")
        return
    
    embed = discord.Embed(
        title=f"🔍 Permissions pour: {role_name}",
        description=f"**Rôle:** {role.mention}",
        color=discord.Color.blue()
    )
    
    if category_name:
        # Vérifier une catégorie spécifique
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            await ctx.send(f"❌ Catégorie `{category_name}` non trouvée!")
            return
        
        if role in category.overwrites:
            overwrite = category.overwrites[role]
            perms = []
            perm_checks = [
                ("view_channel", "👁️ Voir les canaux"),
                ("send_messages", "💬 Envoyer des messages"),
                ("add_reactions", "😀 Ajouter des réactions"),
                ("create_public_threads", "🧵 Créer des threads publics"),
                ("create_private_threads", "🔒 Créer des threads privés"),
                ("send_messages_in_threads", "💬 Écrire dans les threads")
            ]
            
            for perm, desc in perm_checks:
                value = getattr(overwrite, perm)
                if value is True:
                    perms.append(f"✅ {desc}")
                elif value is False:
                    perms.append(f"❌ {desc}")
                else:
                    perms.append(f"⚪ {desc} (par défaut)")
            
            embed.add_field(
                name=f"📁 Permissions dans: {category_name}",
                value="\n".join(perms),
                inline=False
            )
        else:
            embed.add_field(
                name=f"📁 {category_name}",
                value="⚪ Aucune permission spéciale (suit les permissions du serveur)",
                inline=False
            )
    else:
        # Vérifier toutes les catégories avec accès
        categories_with_perms = []
        
        for category in guild.categories:
            if role in category.overwrites:
                overwrite = category.overwrites[role]
                if overwrite.view_channel is True:
                    # Déterminer le type d'accès
                    if overwrite.send_messages is False:
                        access_type = "👁️ Lecture seule"
                    elif overwrite.send_messages is True:
                        if overwrite.create_public_threads is False:
                            access_type = "⚠️ Limité"
                        else:
                            access_type = "✅ Complet"
                    else:
                        access_type = "⚪ Par défaut"
                    
                    categories_with_perms.append(f"📁 **{category.name}** - {access_type}")
        
        if categories_with_perms:
            # Grouper par chunks de 15
            chunks = [categories_with_perms[i:i+15] for i in range(0, len(categories_with_perms), 15)]
            
            for i, chunk in enumerate(chunks):
                field_name = "🔓 Catégories avec permissions:" if i == 0 else f"🔓 Suite ({i+1}):"
                embed.add_field(
                    name=field_name,
                    value="\n".join(chunk),
                    inline=False
                )
        else:
            embed.add_field(
                name="⚪ Aucune permission spéciale",
                value="Ce rôle n'a pas de permissions spéciales sur les catégories.",
                inline=False
            )
    
    embed.set_footer(text="Utilisez !set_guest_perms pour modifier les permissions")
    await ctx.send(embed=embed)

# ========================
# RUN BOT
# ========================
if __name__ == "__main__":
    if not TOKEN:
        logging.critical("❌ No bot token found in environment!")
    else:
        bot.run(TOKEN)