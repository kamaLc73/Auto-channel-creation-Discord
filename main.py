import discord
import os
import random
import logging
import requests
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from ui_system import *
import sys
from datetime import datetime, timezone

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

# ========================
# SERVER COMMANDS
# ========================

@bot.command(aliases=["info", "serverinfo", "si"])
async def server_info(ctx):
    """Display comprehensive server information with interactive features"""
    guild = ctx.guild
    
    # Calculate various statistics
    total_members = guild.member_count
    online_members = len([m for m in guild.members if m.status != discord.Status.offline])
    bot_count = len([m for m in guild.members if m.bot])
    human_count = total_members - bot_count
    
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    
    roles = [role for role in guild.roles if role.name != "@everyone"]
    
    # Create main embed
    embed = discord.Embed(
        title=f"🖥️ {guild.name}",
        description=f"**Server ID:** `{guild.id}`",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # Basic info
    embed.add_field(
        name="👑 Owner",
        value=f"{guild.owner.mention}\n`{guild.owner}`",
        inline=True
    )
    
    embed.add_field(
        name="📅 Created",
        value=f"{guild.created_at.strftime('%B %d, %Y')}\n{guild.created_at.strftime('%H:%M UTC')}",
        inline=True
    )
    
    embed.add_field(
        name="🌍 Region",
        value=f"{getattr(guild, 'region', 'Unknown')}",
        inline=True
    )
    
    # Member statistics
    embed.add_field(
        name="👥 Members",
        value=f"**Total:** {total_members:,}\n"
              f"**Online:** {online_members:,}\n"
              f"**Humans:** {human_count:,}\n"
              f"**Bots:** {bot_count:,}",
        inline=True
    )
    
    # Channel statistics  
    embed.add_field(
        name="📢 Channels",
        value=f"**Categories:** {categories}\n"
              f"**Text:** {text_channels}\n"
              f"**Voice:** {voice_channels}\n"
              f"**Total:** {len(guild.channels)}",
        inline=True
    )
    
    # Role count
    embed.add_field(
        name="🎭 Roles",
        value=f"**Total:** {len(roles)}\n"
              f"**Highest:** {guild.roles[-1].mention if roles else 'None'}",
        inline=True
    )
    
    # Server features
    features = []
    if guild.premium_tier > 0:
        features.append(f"💎 Nitro Level {guild.premium_tier}")
    if guild.premium_subscription_count:
        features.append(f"🚀 {guild.premium_subscription_count} Boosts")
    if hasattr(guild, 'verification_level'):
        features.append(f"🛡️ Verification: {guild.verification_level.name.title()}")
    
    if features:
        embed.add_field(
            name="✨ Features",
            value="\n".join(features),
            inline=False
        )
    
    # Set thumbnail and footer
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(
        text=f"Requested by {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    # Create interactive view for additional info
    view = ServerInfoView(ctx.author, guild)
    
    message = await ctx.send(embed=embed, view=view)
    logging.info(f"Server info displayed for {ctx.author} in {guild.name}")

# ========================
# COMMANDS
# ========================

@bot.command(aliases=["channel", "ch"])
@commands.has_permissions(manage_channels=True)
async def create_channel_in_category(ctx, category_name: str = None, channel_name: str = None):
    """Create a text channel within a category with interactive UI"""
    guild = ctx.guild
    
    # If no arguments provided, show help
    if not category_name or not channel_name:
        embed = discord.Embed(
            title="📝 Create Channel",
            description="Create a text channel within a category",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Usage",
            value=f"`{ctx.prefix}channel <category_name> <channel_name>`",
            inline=False
        )
        embed.add_field(
            name="Example",
            value=f"`{ctx.prefix}channel \"General\" \"welcome\"`",
            inline=False
        )
        embed.set_footer(text="💡 Use quotes for names with spaces")
        await ctx.send(embed=embed)
        return
    
    try:
        # Check if category exists
        category = discord.utils.get(guild.categories, name=category_name)
        category_exists = category is not None
        
        # Check if channel already exists
        if category:
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name, category=category)
        else:
            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        if existing_channel:
            embed = discord.Embed(
                title="⚠️ Channel Already Exists",
                description=f"Channel `{channel_name}` already exists in the server!",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Existing Channel",
                value=f"{existing_channel.mention} in `{existing_channel.category.name if existing_channel.category else 'No Category'}`",
                inline=False
            )
            await ctx.send(embed=embed)
            logging.warning(f"🚫 Channel creation failed - '{channel_name}' already exists in '{category_name}' ({guild.name})")
            return
        
        # Create confirmation embed
        embed = discord.Embed(
            title="📝 Channel Creation Confirmation",
            color=discord.Color.blue()
        )
        
        if category_exists:
            embed.description = f"Create channel `{channel_name}` in existing category `{category_name}`?"
            embed.add_field(
                name="📂 Category",
                value=f"`{category_name}` (exists)",
                inline=True
            )
        else:
            embed.description = f"Create channel `{channel_name}` in new category `{category_name}`?"
            embed.add_field(
                name="📂 Category",
                value=f"`{category_name}` (will be created)",
                inline=True
            )
        
        embed.add_field(
            name="📝 Channel",
            value=f"`{channel_name}` (new)",
            inline=True
        )
        embed.add_field(
            name="🔧 Permissions",
            value="Default channel permissions",
            inline=True
        )
        
        # Use ActionConfirmationView for create action
        view = ActionConfirmationView(
            author=ctx.author,
            action_type="create",
            timeout=30.0
        )
        
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for user response
        await view.wait()
        
        if view.confirmed is None:
            # Timeout
            embed.title = "⏰ Channel Creation Timed Out"
            embed.description = "No response received within 30 seconds."
            embed.color = discord.Color.greyple()
            embed.clear_fields()
            await message.edit(embed=embed, view=None)
            return
        
        if not view.confirmed:
            # Cancelled
            embed.title = "❌ Channel Creation Cancelled"
            embed.description = "Channel creation has been cancelled."
            embed.color = discord.Color.red()
            embed.clear_fields()
            await message.edit(embed=embed, view=None)
            return
        
        # Proceed with creation
        try:
            # Create or get category
            if not category_exists:
                category = await guild.create_category(category_name)
                logging.info(f"📂 Created category '{category_name}' in {guild.name} by {ctx.author}")
            
            # Create channel
            new_channel = await guild.create_text_channel(channel_name, category=category)
            
            # Success embed
            embed = discord.Embed(
                title="✅ Channel Created Successfully",
                description=f"Channel {new_channel.mention} has been created!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📂 Category",
                value=f"`{category.name}`",
                inline=True
            )
            embed.add_field(
                name="📝 Channel",
                value=f"{new_channel.mention}",
                inline=True
            )
            embed.add_field(
                name="🆔 Channel ID",
                value=f"`{new_channel.id}`",
                inline=True
            )
            
            if not category_exists:
                embed.add_field(
                    name="📂 Category Created",
                    value="A new category was also created",
                    inline=False
                )
            
            embed.set_footer(text=f"Created by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            
            await message.edit(embed=embed, view=None)
            logging.info(f"📝 Created channel '{channel_name}' in category '{category_name}' ({guild.name}) by {ctx.author}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have the required permissions to create channels or categories!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value="• Manage Channels\n• Manage Categories",
                inline=False
            )
            await message.edit(embed=embed, view=None)
            logging.error(f"🚫 Permission denied for channel creation in {guild.name}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Creation Error",
                description="An unexpected error occurred while creating the channel.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Error Details",
                value=f"```{str(e)[:1000]}```",
                inline=False
            )
            await message.edit(embed=embed, view=None)
            logging.error(f"🚫 Error creating channel '{channel_name}': {e}")
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred while processing the command.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Error Details",
            value=f"```{str(e)[:1000]}```",
            inline=False
        )
        await ctx.send(embed=embed)
        logging.error(f"🚫 Command error in create_channel_in_category: {e}")

@bot.command(aliases=["channeli", "chi"])
@commands.has_permissions(manage_channels=True)
async def create_channel_interactive(ctx, channel_name: str = None):
    """Create a text channel with interactive category selection"""
    guild = ctx.guild
    
    if not channel_name:
        embed = discord.Embed(
            title="📝 Interactive Channel Creation",
            description="Create a text channel with category selection",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Usage",
            value=f"`{ctx.prefix}channeli <channel_name>`",
            inline=False
        )
        embed.add_field(
            name="Example",
            value=f"`{ctx.prefix}channeli \"welcome\"`",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    try:
        # Check if channel already exists
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            embed = discord.Embed(
                title="⚠️ Channel Already Exists",
                description=f"Channel `{channel_name}` already exists: {existing_channel.mention}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        
        # Get all categories
        categories = guild.categories
        
        if not categories:
            # No categories, create in root
            view = ActionConfirmationView(
                author=ctx.author,
                action_type="create",
                timeout=30.0
            )
            
            embed = discord.Embed(
                title="📝 Create Channel",
                description=f"No categories found. Create `{channel_name}` in the server root?",
                color=discord.Color.blue()
            )
            
            message = await ctx.send(embed=embed, view=view)
            await view.wait()
            
            if view.confirmed:
                new_channel = await guild.create_text_channel(channel_name)
                embed = discord.Embed(
                    title="✅ Channel Created",
                    description=f"Created {new_channel.mention} in server root",
                    color=discord.Color.green()
                )
                await message.edit(embed=embed, view=None)
            else:
                embed = discord.Embed(
                    title="❌ Creation Cancelled",
                    description="Channel creation was cancelled",
                    color=discord.Color.red()
                )
                await message.edit(embed=embed, view=None)
            return
        
        # Prepare category options for selection
        category_options = []
        for category in categories:
            category_options.append({
                'label': category.name[:100],
                'value': str(category.id),
                'description': f"{len(category.channels)} channels",
                'emoji': "📁"
            })
        
        # Add option to create new category
        category_options.append({
            'label': "➕ Create New Category",
            'value': "new_category",
            'description': "Create a new category for this channel",
            'emoji': "🆕"
        })
        
        embed = discord.Embed(
            title="📂 Select Category",
            description=f"Choose a category for channel `{channel_name}`\n{len(category_options)} options available",
            color=discord.Color.blue()
        )
        
        # Choose the appropriate view based on number of options
        if len(category_options) <= 25:
            # Use original SelectionView for small lists
            view = SelectionView(
                author=ctx.author,
                options=category_options,
                placeholder="Select a category...",
                timeout=60.0
            )
        elif len(category_options) <= 100:
            # Use paginated view for medium lists
            view = PaginatedSelectionView(
                author=ctx.author,
                options=category_options,
                placeholder="Select a category...",
                timeout=60.0,
                items_per_page=20
            )
        else:
            # Use searchable view for very large lists
            view = SearchableSelectionView(
                author=ctx.author,
                options=category_options,
                placeholder="Select a category...",
                timeout=60.0
            )
        
        message = await ctx.send(embed=embed, view=view)
        await view.wait()
        
        if not view.confirmed or not view.selected_values:
            embed = discord.Embed(
                title="❌ Selection Cancelled",
                description="Category selection was cancelled",
                color=discord.Color.red()
            )
            await message.edit(embed=embed, view=None)
            return
        
        selected_value = view.selected_values[0]
        
        if selected_value == "new_category":
            # Handle new category creation
            embed = discord.Embed(
                title="📝 New Category Name",
                description="Please provide a name for the new category in your next message.",
                color=discord.Color.blue()
            )
            await message.edit(embed=embed, view=None)
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                msg = await bot.wait_for('message', timeout=30.0, check=check)
                category_name = msg.content.strip()
                
                # Create category and channel
                category = await guild.create_category(category_name)
                new_channel = await guild.create_text_channel(channel_name, category=category)
                
                embed = discord.Embed(
                    title="✅ Channel and Category Created",
                    description=f"Created {new_channel.mention} in new category `{category_name}`",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ Timeout",
                    description="No category name provided within 30 seconds",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            # Use existing category
            category = guild.get_channel(int(selected_value))
            if category:
                new_channel = await guild.create_text_channel(channel_name, category=category)
                
                embed = discord.Embed(
                    title="✅ Channel Created",
                    description=f"Created {new_channel.mention} in category `{category.name}`",
                    color=discord.Color.green()
                )
                await message.edit(embed=embed, view=None)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(e)[:1000]}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        logging.error(f"Error in interactive channel creation: {e}")

@create_channel_interactive.error
async def channel_creation_error(ctx, error):
    """Handle errors for channel creation commands"""
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description="You need the `Manage Channels` permission to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Arguments",
            description=f"Please provide the required arguments. Use `{ctx.prefix}help {ctx.command}` for usage info.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Command Error",
            description="An unexpected error occurred while executing the command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        logging.error(f"Command error in {ctx.command}: {error}")

# =================================
# UPDATED CREATE CATEGORIES COMMAND
# =================================

@bot.command(aliases=["categories", "cats"])
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

        privacy_msg = None
        role_msg = None
        
        try:
            # Step 1: Privacy selection using SelectionView
            privacy_options = [
                {"label": "🔒 Private", "value": "private", "description": "Only selected roles can see this category"},
                {"label": "🌍 Public", "value": "public", "description": "Everyone can see this category"}
            ]
            
            privacy_view = SelectionView(
                author=ctx.author,
                options=privacy_options,
                placeholder="Choose privacy setting...",
                min_values=1,
                max_values=1,
                timeout=30.0
            )
            
            embed = discord.Embed(
                title=f"🏗️ Category Privacy: {category_name}",
                description="Should this category be private or public?",
                color=discord.Color.blue()
            )
            privacy_msg = await ctx.send(embed=embed, view=privacy_view)
            
            await privacy_view.wait()
            if privacy_view.confirmed is None or not privacy_view.selected_values:
                await ctx.send("⏰ Timed out. Skipping category creation.", delete_after=5)
                continue
                
            is_private = privacy_view.selected_values[0] == "private"
            overwrites = {}
            roles = []
            
            # Step 2: Handle private category setup
            if is_private:
                # Get eligible roles (excluding @everyone and roles above bot)
                eligible_roles = [role for role in guild.roles 
                                if role.name != "@everyone" 
                                and role < guild.me.top_role
                                and not role.managed]  # Exclude bot roles
                
                if not eligible_roles:
                    await ctx.send("⚠️ No eligible roles found. Creating public category instead.", delete_after=5)
                    is_private = False
                else:
                    # Create role selection options
                    role_options = [
                        {"label": role.name, "value": str(role.id), "description": f"Members: {len(role.members)}"}
                        for role in eligible_roles[:25]  # Discord limit of 25 options
                    ]
                    
                    role_view = SelectionView(
                        author=ctx.author,
                        options=role_options,
                        placeholder="Select roles that can access this category...",
                        min_values=1,
                        max_values=min(25, len(role_options)),
                        timeout=60.0
                    )
                    
                    embed = discord.Embed(
                        title=f"🔑 Role Selection: {category_name}",
                        description="Select which roles should have access to this private category:",
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text="💡 Tip: You can select multiple roles")
                    
                    role_msg = await ctx.send(embed=embed, view=role_view)
                    await role_view.wait()
                    
                    # Fix: Use selected_values instead of selected_roles
                    if role_view.confirmed and role_view.selected_values:
                        roles = [guild.get_role(int(role_id)) for role_id in role_view.selected_values]
                        roles = [role for role in roles if role is not None]  # Filter out None values
                        
                        if roles:
                            # Set up permissions
                            overwrites = {
                                guild.default_role: discord.PermissionOverwrite(view_channel=False)
                            }
                            for role in roles:
                                overwrites[role] = discord.PermissionOverwrite(
                                    view_channel=True,
                                    read_messages=True,
                                    send_messages=True
                                )
                        else:
                            await ctx.send("⚠️ No valid roles selected. Creating public category instead.", delete_after=5)
                            is_private = False
                    else:
                        await ctx.send("⚠️ No roles selected or timed out. Creating public category instead.", delete_after=5)
                        is_private = False

            # Always initialize overwrites as a dict
            final_overwrites = overwrites if is_private else {}

            # Create category with permissions
            category = await guild.create_category(
                name=category_name,
                overwrites=final_overwrites
            )
            logging.info(f"📁 Created category '{category_name}' in {guild.name}")

            # Create channels
            created = []
            for ch_name in text_channels:
                try:
                    channel = await guild.create_text_channel(ch_name, category=category)
                    created.append(ch_name)
                    logging.info(f"📄 Created channel '{ch_name}' in '{category_name}'")
                except discord.HTTPException as e:
                    logging.error(f"Failed to create channel '{ch_name}': {e}")

            # Final response
            embed = discord.Embed(
                title=f"✅ Created: {category_name}",
                description=f"**Channels:** {', '.join(created)}",
                color=discord.Color.green()
            )
            
            if is_private and roles:
                role_mentions = [role.mention for role in roles if role]
                embed.add_field(
                    name="🔒 Accessible by", 
                    value="\n".join(role_mentions) if role_mentions else "No valid roles",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌍 Visibility",
                    value="Public - Everyone can see this category",
                    inline=False
                )
                
            embed.set_footer(text=f"Created {len(created)} channels")
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send(f"❌ I don't have permission to create categories or channels!", delete_after=10)
            logging.error(f"Permission denied creating category '{category_name}'")
        except discord.HTTPException as e:
            logging.error(f"Category creation failed: {str(e)}")
            await ctx.send(f"❌ Error creating category `{category_name}`: {str(e)}", delete_after=10)
        except Exception as e:
            logging.error(f"Unexpected error creating category '{category_name}': {str(e)}")
            await ctx.send(f"❌ Unexpected error creating category `{category_name}`: {str(e)}", delete_after=10)
        finally:
            # Cleanup messages
            try:
                if privacy_msg:
                    await privacy_msg.delete()
                if role_msg:
                    await role_msg.delete()
            except (discord.NotFound, discord.HTTPException):
                pass  # Message already deleted or error occurred

    # Final summary
    embed = discord.Embed(
        title="🏁 Category Creation Complete",
        description=f"Finished processing {len(categories)} category request(s)",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    logging.info(f"✅ Finished creating categories in {guild.name}")

@create_categories.error
async def create_categories_error(ctx, error):
    """Error handler for create_categories command"""
    
    embed = discord.Embed(
        title="❌ Category Creation Error",
        color=discord.Color.red()
    )
    
    if isinstance(error, commands.MissingPermissions):
        embed.description = "You need Administrator permissions to create categories!"
    elif isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        if isinstance(original_error, discord.Forbidden):
            embed.description = "I don't have permission to create categories or manage channels!"
        elif isinstance(original_error, discord.HTTPException):
            embed.description = f"Discord API error: {str(original_error)}"
        else:
            embed.description = f"An error occurred: {str(original_error)}"
    else:
        embed.description = f"An unexpected error occurred: {str(error)}"
    
    embed.set_footer(text="Make sure the bot has 'Manage Channels' permission")
    
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send(f"❌ Error: {embed.description}")

@bot.command(aliases=["rmcc"])
@commands.has_permissions(manage_channels=True)
async def delete_cat_chan(ctx, *, args: str):
    """
    Delete categories/channels with confirmation
    
    Usage:
    - Delete channel: !rmcc --cha channel_name [--cat category_name]
    - Delete category: !rmcc --cat category_name
    - Delete category (direct): !rmcc category_name
    """

    category_name = None
    channel_name = None
    parts = args.split()
    
    # Parse arguments
    for i, part in enumerate(parts):
        if part == "--cat" and i+1 < len(parts):
            category_name = " ".join(parts[i+1:]).split("--")[0].strip()
        if part == "--cha" and i+1 < len(parts):
            channel_name = " ".join(parts[i+1:]).split("--")[0].strip()
    
    # If no flags are used, treat the entire argument as a category name
    if not category_name and not channel_name and not args.startswith("--"):
        category_name = args.strip()

    guild = ctx.guild
    deleted = []

    try:
        # Handle channel deletion
        if channel_name:
            target_channel = None
            
            # If category is specified, look for channel within that category
            if category_name:
                category = discord.utils.get(guild.categories, name=category_name)
                if category:
                    target_channel = discord.utils.get(category.text_channels, name=channel_name)
                    if not target_channel:
                        await ctx.send(f"⚠️ Channel `{channel_name}` not found in category `{category_name}`!", delete_after=5)
                        return
                else:
                    await ctx.send(f"⚠️ Category `{category_name}` not found!", delete_after=5)
                    return
            else:
                # Look for channel globally across all categories
                target_channel = discord.utils.get(guild.text_channels, name=channel_name)
                if not target_channel:
                    await ctx.send(f"⚠️ Channel `{channel_name}` not found!", delete_after=5)
                    return
            
            # Channel deletion confirmation
            confirm_view = ActionConfirmationView(
                author=ctx.author,
                action_type="delete",
                timeout=30.0
            )
            
            embed = discord.Embed(
                title="🗑️ Confirm Channel Deletion",
                description=(
                    f"Are you sure you want to delete the channel **#{channel_name}**?"
                    + (f"\n**Category:** {target_channel.category.name}" if target_channel.category else "\n**Category:** No Category")
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="This action cannot be undone!")
            
            confirmation_msg = await ctx.send(embed=embed, view=confirm_view)
            await confirm_view.wait()
            
            if confirm_view.confirmed:
                await target_channel.delete(reason=f"Channel deleted by {ctx.author}")
                deleted.append(f"Channel '#{channel_name}'" + (f" from category '{target_channel.category.name}'" if target_channel.category else ""))
                logging.info(f"🗑️ Deleted channel '{channel_name}' in {guild.name} by {ctx.author}")
            elif confirm_view.confirmed is False:
                await ctx.send("🚫 Channel deletion cancelled.", delete_after=5)
            else:
                await ctx.send("🕒 Confirmation timed out. Deletion cancelled.", delete_after=5)
            
            await confirmation_msg.delete()

        # Handle category deletion
        elif category_name:
            category = discord.utils.get(guild.categories, name=category_name)
            if category:
                channels = list(category.channels)
                
                # Use DangerConfirmationView for category deletion (more dangerous)
                danger_view = DangerConfirmationView(
                    author=ctx.author,
                    timeout=30.0,
                    action_name="deletion"
                )
                
                embed = discord.Embed(
                    title="⚠️ DANGER: Category Deletion",
                    description=(
                        f"**Category:** {category_name}\n"
                        f"**Channels to delete:** {len(channels)}\n\n"
                        f"**This will permanently delete:**\n"
                        f"• The category '{category_name}'\n"
                        f"• All {len(channels)} channels inside it\n"
                        f"• All messages in those channels"
                    ),
                    color=discord.Color.red()
                )
                embed.set_footer(text="⚠️ THIS ACTION CANNOT BE UNDONE! ⚠️")
                
                if channels:
                    # Group channels by type for better display
                    text_channels = [ch for ch in channels if isinstance(ch, discord.TextChannel)]
                    voice_channels = [ch for ch in channels if isinstance(ch, discord.VoiceChannel)]
                    stage_channels = [ch for ch in channels if isinstance(ch, discord.StageChannel)]
                    forum_channels = [ch for ch in channels if hasattr(ch, 'type') and ch.type == discord.ChannelType.forum]
                    
                    channel_details = []
                    if text_channels:
                        channel_details.append(f"**Text Channels ({len(text_channels)}):**")
                        for ch in text_channels[:8]:
                            channel_details.append(f"• #{ch.name}")
                        if len(text_channels) > 8:
                            channel_details.append(f"• ... and {len(text_channels) - 8} more text channels")
                    
                    if voice_channels:
                        channel_details.append(f"**Voice Channels ({len(voice_channels)}):**")
                        for ch in voice_channels[:5]:
                            channel_details.append(f"• 🔊 {ch.name}")
                        if len(voice_channels) > 5:
                            channel_details.append(f"• ... and {len(voice_channels) - 5} more voice channels")
                    
                    if stage_channels:
                        channel_details.append(f"**Stage Channels ({len(stage_channels)}):**")
                        for ch in stage_channels[:3]:
                            channel_details.append(f"• 🎭 {ch.name}")
                        if len(stage_channels) > 3:
                            channel_details.append(f"• ... and {len(stage_channels) - 3} more stage channels")
                    
                    if forum_channels:
                        channel_details.append(f"**Forum Channels ({len(forum_channels)}):**")
                        for ch in forum_channels[:3]:
                            channel_details.append(f"• 💬 {ch.name}")
                        if len(forum_channels) > 3:
                            channel_details.append(f"• ... and {len(forum_channels) - 3} more forum channels")
                    
                    embed.add_field(
                        name="Channels to be deleted:",
                        value="\n".join(channel_details),
                        inline=False
                    )
                
                confirmation_msg = await ctx.send(embed=embed, view=danger_view)
                await danger_view.wait()
                
                if danger_view.confirmed:
                    # Create a progress embed
                    progress_embed = discord.Embed(
                        title="🗑️ Deleting Category...",
                        description=f"Deleting category '{category_name}' and its {len(channels)} channels...",
                        color=discord.Color.orange()
                    )
                    progress_msg = await ctx.send(embed=progress_embed)
                    
                    deleted_channels_count = 0
                    failed_channels = []
                    
                    # Delete all channels first with progress tracking
                    for i, channel in enumerate(channels, 1):
                        try:
                            progress_embed.description = f"Deleting channel {i}/{len(channels)}: {channel.name}"
                            await progress_msg.edit(embed=progress_embed)
                            
                            await channel.delete(reason=f"Category deletion by {ctx.author}")
                            deleted_channels_count += 1
                            logging.info(f"🗑️ Deleted channel '{channel.name}' in category '{category_name}' by {ctx.author}")
                        except Exception as e:
                            failed_channels.append(f"{channel.name}: {str(e)}")
                            logging.warning(f"⚠️ Failed to delete channel '{channel.name}': {str(e)}")
                    
                    # Delete the category
                    progress_embed.description = f"Deleting category '{category_name}'..."
                    await progress_msg.edit(embed=progress_embed)
                    
                    try:
                        await category.delete(reason=f"Category deleted by {ctx.author}")
                        deleted.append(f"Category '{category_name}' ({deleted_channels_count}/{len(channels)} channels)")
                        logging.info(f"🗑️ Deleted category '{category_name}' in {guild.name} by {ctx.author}")
                        
                        # Final success message
                        success_embed = discord.Embed(
                            title="✅ Category Deletion Complete",
                            description=(
                                f"**Successfully deleted:**\n"
                                f"• Category: **{category_name}**\n"
                                f"• Channels: **{deleted_channels_count}**/{len(channels)}\n"
                                f"• Messages: **All messages permanently removed**"
                            ),
                            color=discord.Color.green()
                        )
                        
                        if failed_channels:
                            failed_list = "\n".join(failed_channels[:5])
                            if len(failed_channels) > 5:
                                failed_list += f"\n... and {len(failed_channels) - 5} more"
                            success_embed.add_field(
                                name="⚠️ Failed Channel Deletions:",
                                value=failed_list,
                                inline=False
                            )
                            success_embed.color = discord.Color.orange()
                        
                        await progress_msg.edit(embed=success_embed)
                        
                    except Exception as e:
                        error_embed = discord.Embed(
                            title="❌ Category Deletion Failed",
                            description=f"Failed to delete category '{category_name}': {str(e)}",
                            color=discord.Color.red()
                        )
                        await progress_msg.edit(embed=error_embed)
                        return
                    
                elif danger_view.confirmed is False:
                    await ctx.send("🚫 Category deletion cancelled.", delete_after=5)
                else:
                    await ctx.send("🕒 Confirmation timed out. Deletion cancelled.", delete_after=5)
                
                await confirmation_msg.delete()
            else:
                await ctx.send(f"⚠️ Category `{category_name}` not found!", delete_after=5)
        
        else:
            # No valid arguments provided
            embed = discord.Embed(
                title="❌ Invalid Arguments",
                description=(
                    "Please specify what to delete:\n\n"
                    "**Delete a channel:**\n"
                    "`!rmcc --cha channel_name` (search all categories)\n"
                    "`!rmcc --cha channel_name --cat category_name` (search specific category)\n\n"
                    "**Delete a category:**\n"
                    "`!rmcc --cat category_name`\n"
                    "`!rmcc category_name` (direct category name)"
                ),
                color=discord.Color.red()
            )
            embed.set_footer(text="Use quotes for names with spaces: !rmcc \"My Category\"")
            await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to manage channels!", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Discord API Error: {str(e)}", delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Unexpected Error: {str(e)}", delete_after=5)
        logging.error(f"Unexpected error in rmcc: {str(e)}")

@bot.command(aliases=["rmi"])
@commands.has_permissions(manage_channels=True)
async def interactive_delete(ctx):
    """Interactive deletion command for channels and categories"""
    
    guild = ctx.guild
    main_msg = None
    
    try:
        # Step 1: Choose what type to delete
        type_options = [
            {"label": "🗑️ Delete Channel", "value": "channel", "description": "Delete text channels from selected categories"},
            {"label": "🗂️ Delete Category", "value": "category", "description": "Delete entire categories with all their channels"}
        ]
        
        type_view = SelectionView(
            author=ctx.author,
            options=type_options,
            placeholder="What do you want to delete?",
            min_values=1,
            max_values=1,
            timeout=60.0,
            auto_confirm=True
        )
        
        embed = discord.Embed(
            title="🗑️ Interactive Deletion",
            description="Choose what type of element you want to delete:",
            color=discord.Color.blue()
        )
        
        main_msg = await ctx.send(embed=embed, view=type_view)
        
        await type_view.wait()
        if not type_view.selected_values:
            embed.color = discord.Color.red()
            embed.description = "⏰ Selection timed out. Operation cancelled."
            await main_msg.edit(embed=embed, view=None)
            return
        
        deletion_type = type_view.selected_values[0]
        
        # Step 2: Handle deletion flow
        if deletion_type == "channel":
            await _handle_channel_deletion(ctx, guild, main_msg)
        elif deletion_type == "category":
            await _handle_category_deletion(ctx, guild, main_msg)
            
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to manage channels!",
            color=discord.Color.red()
        )
        if main_msg:
            await main_msg.edit(embed=embed, view=None)
        else:
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Unexpected Error",
            description=f"An unexpected error occurred: {str(e)}",
            color=discord.Color.red()
        )
        if main_msg:
            await main_msg.edit(embed=embed, view=None)
        else:
            await ctx.send(embed=embed)

async def _handle_channel_deletion(ctx, guild, main_msg):
    """Handle channel deletion process with pagination"""
    
    # Get all categories
    categories = [cat for cat in guild.categories if cat.text_channels]
    
    if not categories:
        embed = discord.Embed(
            title="❌ No Categories Found",
            description="No categories with text channels found!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Prepare category options
    category_options = []
    for category in categories:
        text_channels = [ch for ch in category.text_channels]
        if text_channels:
            category_options.append({
                'label': category.name[:100],
                'value': str(category.id),
                'description': f"{len(text_channels)} text channels",
                'emoji': "📁"
            })
    
    if not category_options:
        embed = discord.Embed(
            title="❌ No Text Channels Found",
            description="No text channels found in any category!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Step 1: Select category with appropriate view
    embed = discord.Embed(
        title="📂 Select Category",
        description=f"Choose a category to delete channels from\n{len(category_options)} categories available",
        color=discord.Color.blue()
    )
    
    # Choose appropriate view based on number of categories
    if len(category_options) <= 25:
        category_view = SelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select a category...",
            timeout=60.0
        )
    elif len(category_options) <= 100:
        category_view = PaginatedSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select a category...",
            timeout=60.0,
            items_per_page=20
        )
    else:
        category_view = SearchableSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select a category...",
            timeout=60.0
        )
    
    await main_msg.edit(embed=embed, view=category_view)
    await category_view.wait()
    
    if not category_view.confirmed or not category_view.selected_values:
        embed = discord.Embed(
            title="❌ Selection Cancelled",
            description="Category selection was cancelled",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    category_id = int(category_view.selected_values[0])
    selected_category = guild.get_channel(category_id)
    
    if not selected_category:
        embed = discord.Embed(
            title="❌ Category Not Found",
            description="Selected category not found!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Get text channels in selected category
    text_channels = [ch for ch in selected_category.text_channels]
    
    if not text_channels:
        embed = discord.Embed(
            title="❌ No Text Channels",
            description=f"No text channels found in category `{selected_category.name}`!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Step 2: Select channels to delete
    channel_options = []
    for channel in text_channels:
        channel_options.append({
            'label': channel.name[:100],
            'value': str(channel.id),
            'description': f"#{channel.name}",
            'emoji': "💬"
        })
    
    embed = discord.Embed(
        title="🗑️ Select Channels to Delete",
        description=f"Choose channels to delete from `{selected_category.name}`\n{len(channel_options)} channels available",
        color=discord.Color.orange()
    )
    
    # Choose appropriate view for channels
    if len(channel_options) <= 25:
        channels_view = SelectionView(
            author=ctx.author,
            options=channel_options,
            placeholder="Select channels to delete...",
            min_values=1,
            max_values=min(len(channel_options), 25),
            timeout=60.0
        )
    elif len(channel_options) <= 100:
        channels_view = PaginatedSelectionView(
            author=ctx.author,
            options=channel_options,
            placeholder="Select channels to delete...",
            min_values=1,
            max_values=1,  # Pagination limits to 1 selection at a time
            timeout=60.0,
            items_per_page=20
        )
    else:
        channels_view = SearchableSelectionView(
            author=ctx.author,
            options=channel_options,
            placeholder="Select channels to delete...",
            timeout=60.0
        )
    
    await main_msg.edit(embed=embed, view=channels_view)
    await channels_view.wait()
    
    if not channels_view.confirmed or not channels_view.selected_values:
        embed = discord.Embed(
            title="❌ Selection Cancelled",
            description="Channel selection was cancelled",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Step 3: Confirmation
    channels_to_delete = []
    for channel_id in channels_view.selected_values:
        channel = guild.get_channel(int(channel_id))
        if channel:
            channels_to_delete.append(channel)
    
    if not channels_to_delete:
        embed = discord.Embed(
            title="❌ No Valid Channels",
            description="No valid channels found to delete!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Final confirmation
    channel_list = "\n".join([f"• #{ch.name}" for ch in channels_to_delete[:10]])
    if len(channels_to_delete) > 10:
        channel_list += f"\n... and {len(channels_to_delete) - 10} more"
    
    confirm_view = ActionConfirmationView(
        author=ctx.author,
        action_type="delete",
        timeout=30.0
    )
    
    embed = discord.Embed(
        title="⚠️ Confirm Channel Deletion",
        description=f"Are you sure you want to delete these **{len(channels_to_delete)} channels**?\n\n{channel_list}",
        color=discord.Color.red()
    )
    embed.set_footer(text="This action cannot be undone!")
    
    await main_msg.edit(embed=embed, view=confirm_view)
    await confirm_view.wait()
    
    if not confirm_view.confirmed:
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description="Channel deletion was cancelled",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Step 4: Delete channels
    embed = discord.Embed(
        title="🗑️ Deleting Channels...",
        description=f"Deleting {len(channels_to_delete)} channels...",
        color=discord.Color.orange()
    )
    await main_msg.edit(embed=embed, view=None)
    
    deleted_count = 0
    failed_channels = []
    
    for i, channel in enumerate(channels_to_delete, 1):
        try:
            # Update progress
            embed.description = f"Deleting channel {i}/{len(channels_to_delete)}: #{channel.name}"
            await main_msg.edit(embed=embed)
            
            await channel.delete(reason=f"Deleted by {ctx.author} via interactive deletion")
            deleted_count += 1
            logging.info(f"🗑️ Deleted channel '{channel.name}' by {ctx.author}")
        except Exception as e:
            failed_channels.append(f"{channel.name}: {str(e)}")
            logging.error(f"❌ Failed to delete channel '{channel.name}': {str(e)}")
    
    # Final result
    if deleted_count == len(channels_to_delete):
        embed = discord.Embed(
            title="✅ Channels Deleted Successfully",
            description=f"Successfully deleted **{deleted_count} channels** from `{selected_category.name}`",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Partial Success",
            description=f"Deleted {deleted_count}/{len(channels_to_delete)} channels",
            color=discord.Color.orange()
        )
        if failed_channels:
            failed_list = "\n".join(failed_channels[:5])
            if len(failed_channels) > 5:
                failed_list += f"\n... and {len(failed_channels) - 5} more"
            embed.add_field(name="Failed Deletions", value=failed_list, inline=False)
    
    await main_msg.edit(embed=embed, view=None)

async def _handle_category_deletion(ctx, guild, main_msg):
    """Handle category deletion process with explicit channel deletion"""
    
    categories = guild.categories
    
    if not categories:
        embed = discord.Embed(
            title="❌ No Categories Found",
            description="No categories found to delete!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Prepare category options
    category_options = []
    for category in categories:
        total_channels = len(category.channels)
        category_options.append({
            'label': category.name[:100],
            'value': str(category.id),
            'description': f"{total_channels} channels total",
            'emoji': "📁"
        })
    
    embed = discord.Embed(
        title="🗑️ Select Categories to Delete",
        description=f"Choose categories to delete (with all their channels)\n{len(category_options)} categories available",
        color=discord.Color.orange()
    )
    
    # Choose appropriate view based on number of categories
    if len(category_options) <= 25:
        categories_view = SelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select categories to delete...",
            min_values=1,
            max_values=min(len(category_options), 25),
            timeout=60.0
        )
    elif len(category_options) <= 100:
        categories_view = PaginatedSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select categories to delete...",
            min_values=1,
            max_values=1,  # Pagination limits to 1 selection at a time
            timeout=60.0,
            items_per_page=20
        )
    else:
        categories_view = SearchableSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select categories to delete...",
            timeout=60.0
        )
    
    await main_msg.edit(embed=embed, view=categories_view)
    await categories_view.wait()
    
    if not categories_view.confirmed or not categories_view.selected_values:
        embed = discord.Embed(
            title="❌ Selection Cancelled",
            description="Category selection was cancelled",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Get categories to delete
    categories_to_delete = []
    total_channels = 0
    
    for category_id in categories_view.selected_values:
        category = guild.get_channel(int(category_id))
        if category:
            categories_to_delete.append(category)
            total_channels += len(category.channels)
    
    if not categories_to_delete:
        embed = discord.Embed(
            title="❌ No Valid Categories",
            description="No valid categories found to delete!",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Final confirmation
    category_list = "\n".join([f"• **{cat.name}** ({len(cat.channels)} channels)" for cat in categories_to_delete[:10]])
    if len(categories_to_delete) > 10:
        category_list += f"\n... and {len(categories_to_delete) - 10} more"
    
    confirm_view = ActionConfirmationView(
        author=ctx.author,
        action_type="delete",
        timeout=30.0
    )
    
    embed = discord.Embed(
        title="⚠️ Confirm Category Deletion",
        description=(
            f"Are you sure you want to delete these **{len(categories_to_delete)} categories** and **{total_channels} channels**?\n\n"
            f"**This will permanently delete:**\n"
            f"• All selected categories\n"
            f"• All channels within them\n"
            f"• All messages in those channels\n\n"
            f"**Categories to delete:**\n{category_list}"
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="⚠️ THIS ACTION CANNOT BE UNDONE! ⚠️")
    
    await main_msg.edit(embed=embed, view=confirm_view)
    await confirm_view.wait()
    
    if not confirm_view.confirmed:
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description="Category deletion was cancelled",
            color=discord.Color.red()
        )
        await main_msg.edit(embed=embed, view=None)
        return
    
    # Delete categories with explicit channel deletion
    embed = discord.Embed(
        title="🗑️ Deleting Categories...",
        description="Preparing to delete categories and channels...",
        color=discord.Color.orange()
    )
    await main_msg.edit(embed=embed, view=None)
    
    total_deleted_categories = 0
    total_deleted_channels = 0
    total_failed_channels = []
    failed_categories = []
    
    for i, category in enumerate(categories_to_delete, 1):
        try:
            channels = list(category.channels)  # Create a copy of the channels list
            channel_count = len(channels)
            
            # Update progress for category
            embed.description = f"Processing category {i}/{len(categories_to_delete)}: **{category.name}** ({channel_count} channels)"
            await main_msg.edit(embed=embed)
            
            # Delete all channels in the category first
            deleted_channels_in_category = 0
            for j, channel in enumerate(channels, 1):
                try:
                    # Update progress for individual channel
                    embed.description = f"Category {i}/{len(categories_to_delete)}: **{category.name}**\nDeleting channel {j}/{channel_count}: #{channel.name}"
                    await main_msg.edit(embed=embed)
                    
                    await channel.delete(reason=f"Category deletion by {ctx.author} via interactive deletion")
                    deleted_channels_in_category += 1
                    total_deleted_channels += 1
                    logging.info(f"🗑️ Deleted channel '{channel.name}' from category '{category.name}' by {ctx.author}")
                except Exception as channel_error:
                    total_failed_channels.append(f"#{channel.name}: {str(channel_error)}")
                    logging.warning(f"⚠️ Failed to delete channel '{channel.name}': {str(channel_error)}")
            
            # Update progress for category deletion
            embed.description = f"Category {i}/{len(categories_to_delete)}: Deleting category **{category.name}**"
            await main_msg.edit(embed=embed)
            
            # Then delete the category itself
            await category.delete(reason=f"Deleted by {ctx.author} via interactive deletion")
            total_deleted_categories += 1
            logging.info(f"🗑️ Deleted category '{category.name}' with {deleted_channels_in_category}/{channel_count} channels by {ctx.author}")
            
        except Exception as e:
            failed_categories.append(f"**{category.name}**: {str(e)}")
            logging.error(f"❌ Failed to delete category '{category.name}': {str(e)}")
    
    # Final result with detailed information
    if total_deleted_categories == len(categories_to_delete) and not total_failed_channels:
        embed = discord.Embed(
            title="✅ Categories Deleted Successfully",
            description=(
                f"**Deletion Complete!**\n\n"
                f"✅ **{total_deleted_categories}** categories deleted\n"
                f"✅ **{total_deleted_channels}** channels deleted\n"
                f"✅ All messages permanently removed"
            ),
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Deletion Results",
            description=(
                f"**Summary:**\n"
                f"✅ Categories deleted: **{total_deleted_categories}**/{len(categories_to_delete)}\n"
                f"✅ Channels deleted: **{total_deleted_channels}**\n"
                f"❌ Failed categories: **{len(failed_categories)}**\n"
                f"❌ Failed channels: **{len(total_failed_channels)}**"
            ),
            color=discord.Color.orange() if total_deleted_categories > 0 else discord.Color.red()
        )
        
        if failed_categories:
            failed_cat_list = "\n".join(failed_categories[:3])
            if len(failed_categories) > 3:
                failed_cat_list += f"\n... and {len(failed_categories) - 3} more"
            embed.add_field(
                name="❌ Failed Category Deletions:",
                value=failed_cat_list,
                inline=False
            )
        
        if total_failed_channels:
            failed_ch_list = "\n".join(total_failed_channels[:5])
            if len(total_failed_channels) > 5:
                failed_ch_list += f"\n... and {len(total_failed_channels) - 5} more"
            embed.add_field(
                name="⚠️ Failed Channel Deletions:",
                value=failed_ch_list,
                inline=False
            )
    
    await main_msg.edit(embed=embed, view=None)

@interactive_delete.error
async def interactive_delete_error(ctx, error):
    """Error handler for interactive_delete command"""
    
    embed = discord.Embed(
        title="❌ Command Error",
        color=discord.Color.red()
    )
    
    if isinstance(error, commands.MissingPermissions):
        embed.description = "You don't have permission to manage channels!"
    elif isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        if isinstance(original_error, discord.Forbidden):
            embed.description = "I don't have permission to perform this action!"
        elif isinstance(original_error, discord.HTTPException):
            embed.description = f"Discord API error: {str(original_error)}"
        else:
            embed.description = f"An error occurred: {str(original_error)}"
    else:
        embed.description = f"An unexpected error occurred: {str(error)}"
    
    try:
        await ctx.send(embed=embed)
    except:
        await ctx.send(f"❌ Error: {embed.description}")

# =================================
# WEATHER COMMAND
# =================================

@bot.command(aliases=["w", "weather_info"])
@commands.cooldown(1, 15, commands.BucketType.user)
async def weather(ctx, *, city: str = None):
    """Get comprehensive weather information for a city"""
    
    if not city:
        embed = discord.Embed(
            title="🌤️ Weather Command",
            description="Get current weather information for any city!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Usage",
            value="```!w <city name>\n!w <city name>```",
            inline=False
        )
        embed.add_field(
            name="Examples",
            value="```!w London\n!w New York\n!w Tokyo Japan```",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    if not OPENWEATHER_API_KEY:
        embed = discord.Embed(
            title="❌ Service Unavailable",
            description="Weather service is currently unavailable. Please try again later.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # Show loading message
    loading_embed = discord.Embed(
        title="🔍 Fetching Weather Data...",
        description=f"Getting weather information for **{city}**",
        color=discord.Color.blue()
    )
    message = await ctx.send(embed=loading_embed)

    try:
        # Current weather API call
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        
        current_response = requests.get(current_url, timeout=10)
        current_data = current_response.json()

        # Debug logging
        logging.info(f"Weather API response for '{city}': {current_data}")

        if current_data.get('cod') != 200:
            error_messages = {
                '404': f"City '{city}' not found. Please check the spelling and try again.",
                '401': "Weather service authentication error.",
                '429': "Too many requests. Please wait before trying again.",
                '500': "Weather service is temporarily unavailable."
            }
            
            error_code = str(current_data.get('cod', 'unknown'))
            error_msg = error_messages.get(error_code, f"Error: {current_data.get('message', 'Unknown error')}")
            
            embed = discord.Embed(
                title="❌ Weather Data Error",
                description=error_msg,
                color=discord.Color.red()
            )
            embed.add_field(
                name="Error Details",
                value=f"Code: {error_code}\nResponse: {current_data.get('message', 'No message')}",
                inline=False
            )
            await message.edit(embed=embed)
            return

        # Safely extract weather data with fallbacks
        main = current_data.get('main', {})
        weather_list = current_data.get('weather', [{}])
        weather = weather_list[0] if weather_list else {}
        wind = current_data.get('wind', {})
        clouds = current_data.get('clouds', {})
        sys_data = current_data.get('sys', {})
        
        # Create comprehensive weather embed with safe data extraction
        embed = discord.Embed(
            title=f"🌤️ Weather in {current_data.get('name', city)}, {sys_data.get('country', '')}",
            description=f"**{weather.get('description', 'No description').title()}**",
            color=_get_weather_color(weather.get('main', 'Clear')),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Main weather info with safe extraction
        temp = main.get('temp', 0)
        feels_like = main.get('feels_like', temp)
        temp_min = main.get('temp_min', temp)
        temp_max = main.get('temp_max', temp)
        humidity = main.get('humidity', 0)
        pressure = main.get('pressure', 0)
        
        embed.add_field(
            name="🌡️ Temperature",
            value=f"**Current:** {temp:.1f}°C\n"
                  f"**Feels like:** {feels_like:.1f}°C\n"
                  f"**Min:** {temp_min:.1f}°C\n"
                  f"**Max:** {temp_max:.1f}°C",
            inline=True
        )
        
        embed.add_field(
            name="💧 Humidity & Pressure",
            value=f"**Humidity:** {humidity}%\n"
                  f"**Pressure:** {pressure} hPa\n"
                  f"**Visibility:** {current_data.get('visibility', 'N/A')}m",
            inline=True
        )
        
        # Wind and clouds with safe extraction
        wind_speed = wind.get('speed', 0) * 3.6  # Convert m/s to km/h
        wind_direction = _get_wind_direction(wind.get('deg', 0))
        cloud_coverage = clouds.get('all', 0)
        
        embed.add_field(
            name="💨 Wind & Clouds",
            value=f"**Wind:** {wind_speed:.1f} km/h {wind_direction}\n"
                  f"**Clouds:** {cloud_coverage}%\n"
                  f"**Condition:** {weather.get('main', 'Unknown')}",
            inline=True
        )
        
        # Sunrise/sunset if available
        if 'sunrise' in sys_data and 'sunset' in sys_data:
            try:
                sunrise = datetime.fromtimestamp(sys_data['sunrise']).strftime('%H:%M')
                sunset = datetime.fromtimestamp(sys_data['sunset']).strftime('%H:%M')
                embed.add_field(
                    name="🌅 Sun Times",
                    value=f"**Sunrise:** {sunrise}\n**Sunset:** {sunset}",
                    inline=True
                )
            except (ValueError, OSError) as e:
                logging.warning(f"Error parsing sunrise/sunset times: {e}")
        
        # Weather icon
        icon_code = weather.get('icon', '01d')  # Default sunny icon
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name} • Data from OpenWeatherMap",
            icon_url=ctx.author.display_avatar.url if ctx.author.display_avatar else None
        )
        
        # Add interactive buttons (if WeatherView is defined)
        try:
            view = WeatherView(ctx.author, city, current_data)
            await message.edit(embed=embed, view=view)
        except NameError:
            # WeatherView not defined, send without view
            await message.edit(embed=embed)
        
        logging.info(f"Weather data provided for {city} to {ctx.author}")
        
    except requests.exceptions.Timeout:
        embed = discord.Embed(
            title="⌛ Request Timeout",
            description="The weather service is taking too long to respond. Please try again later.",
            color=discord.Color.orange()
        )
        await message.edit(embed=embed)
        logging.error(f"Weather API timeout for city: {city}")
    except requests.exceptions.RequestException as e:
        embed = discord.Embed(
            title="❌ Connection Error",
            description="Unable to connect to the weather service. Please check your internet connection.",
            color=discord.Color.red()
        )
        await message.edit(embed=embed)
        logging.error(f"Weather API request error for {city}: {e}")
    except KeyError as e:
        embed = discord.Embed(
            title="❌ Data Processing Error",
            description="Error processing weather data. The API response format may have changed.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Missing Key",
            value=f"```{str(e)}```",
            inline=False
        )
        await message.edit(embed=embed)
        logging.error(f"Weather data KeyError for {city}: {e}")
    except Exception as e:
        embed = discord.Embed(
            title="❌ Unexpected Error",
            description="An unexpected error occurred while fetching weather data.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Error Details",
            value=f"```{str(e)[:1000]}```",
            inline=False
        )
        await message.edit(embed=embed)
        logging.error(f"Weather command error for {city}: {e}")

def _get_weather_color(condition):
    """Get color based on weather condition"""
    color_map = {
        'Clear': discord.Color.gold(),
        'Clouds': discord.Color.light_grey(),
        'Rain': discord.Color.blue(),
        'Drizzle': discord.Color.teal(),
        'Thunderstorm': discord.Color.purple(),
        'Snow': discord.Color.from_rgb(255, 255, 255),
        'Mist': discord.Color.lighter_grey(),
        'Fog': discord.Color.darker_grey(),
        'Haze': discord.Color.lighter_grey(),
        'Dust': discord.Color.from_rgb(210, 180, 140),
        'Sand': discord.Color.from_rgb(244, 164, 96),
        'Ash': discord.Color.darker_grey(),
        'Squall': discord.Color.purple(),
        'Tornado': discord.Color.dark_purple(),
    }
    return color_map.get(condition, discord.Color.blue())

def _get_wind_direction(degrees):
    """Convert wind degrees to direction"""
    if degrees is None:
        return "N/A"
    
    try:
        degrees = float(degrees)
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    except (ValueError, TypeError):
        return "N/A"

# Optional: Add a simple WeatherView if you want interactive buttons
class WeatherView(discord.ui.View):
    def __init__(self, author, city, weather_data):
        super().__init__(timeout=300.0)
        self.author = author
        self.city = city
        self.weather_data = weather_data
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_weather(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🔄 Refreshing weather for {self.city}...", ephemeral=True)
        # You could trigger a new weather fetch here
    
    @discord.ui.button(label="📍 Location", style=discord.ButtonStyle.secondary, emoji="📍")
    async def show_location(self, interaction: discord.Interaction, button: discord.ui.Button):
        coord = self.weather_data.get('coord', {})
        lat = coord.get('lat', 'N/A')
        lon = coord.get('lon', 'N/A')
        await interaction.response.send_message(f"📍 **{self.city}**\nLatitude: {lat}\nLongitude: {lon}", ephemeral=True)    
@weather.error
async def weather_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("ℹ️ Usage: `!weather <city>`")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Cooldown active. Try again in {error.retry_after:.1f}s")

# =================================
# STATUS COMMAND
# =================================

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

@bot.command(aliases=["clear", "clm", "cls"])
@commands.has_permissions(manage_messages=True)
async def delete_messages(ctx, amount: str = "5"):
    """Delete messages with interactive confirmation"""
    try:
        # Parse amount
        if amount == "-":
            action_desc = "all unpinned messages"
            delete_all = True
        else:
            try:
                amount_int = int(amount)
                if amount_int < 1 or amount_int > 1000:
                    embed = discord.Embed(
                        title="❌ Invalid Amount",
                        description="Please specify a number between 1-1000 or '-' for all unpinned messages",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed, delete_after=10)
                    return
                action_desc = f"{amount_int} messages"
                delete_all = False
            except ValueError:
                embed = discord.Embed(
                    title="❌ Invalid Input",
                    description="Please specify a valid number or '-' for all unpinned messages",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, delete_after=10)
                return

        # Interactive confirmation
        confirm_view = ActionConfirmationView(
            author=ctx.author,
            action_type="delete",
            timeout=30.0
        )
        
        embed = discord.Embed(
            title="⚠️ Confirm Message Deletion",
            description=f"You are about to delete **{action_desc}** in {ctx.channel.mention}.\n\n"
                       f"⚠️ This action cannot be undone!\n"
                       f"📝 **Note:** Your command message will also be deleted.",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Channel Info :",
            value=f"**\t Channel:** {ctx.channel.name}\n**\t Category:** {ctx.channel.category.name if ctx.channel.category else 'None'}",
            inline=False
        )
        
        message = await ctx.send(embed=embed, view=confirm_view)
        await confirm_view.wait()
        
        if not confirm_view.confirmed:
            embed = discord.Embed(
                title="❌ Deletion Cancelled",
                description="Message deletion was cancelled",
                color=discord.Color.red()
            )
            await message.edit(embed=embed, view=None)
            return
        
        # Show deletion progress
        embed = discord.Embed(
            title="🗑️ Deleting Messages...",
            description=f"Deleting {action_desc}...",
            color=discord.Color.orange()
        )
        await message.edit(embed=embed, view=None)
        
        # Store command message reference for deletion
        command_message = ctx.message
        
        # Delete messages
        if delete_all:
            # Delete all unpinned messages (excluding this confirmation message)
            deleted = await ctx.channel.purge(
                limit=None, 
                check=lambda m: not m.pinned and m.id != message.id
            )
        else:
            # First, collect the specified number of messages (excluding confirmation message and command)
            messages_to_delete = []
            async for msg in ctx.channel.history(limit=amount_int + 100):  # Search a bit more to find enough
                if msg.id != message.id and msg.id != command_message.id:  # Exclude confirmation and command
                    messages_to_delete.append(msg)
                    if len(messages_to_delete) >= amount_int:
                        break
            
            # Add the command message separately
            messages_to_delete.append(command_message)
            
            # Delete the collected messages
            deleted = []
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                    deleted.append(msg)
                except (discord.NotFound, discord.Forbidden):
                    pass
        
        # Show result
        # Calculate actual messages deleted (excluding the command message for the count display)
        actual_messages_deleted = len([msg for msg in deleted if msg.id != command_message.id])
        
        embed = discord.Embed(
            title="✅ Messages Deleted Successfully",
            description=f"🗑️ Deleted **{actual_messages_deleted}** messages from {ctx.channel.mention}\n"
                       f"📝 Plus your command message",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Deleted by {ctx.author.display_name}")
        
        await message.edit(embed=embed, view=None)
        await asyncio.sleep(5)
        await message.delete()
        
        logging.info(f"Deleted {actual_messages_deleted} messages + command in {ctx.channel} by {ctx.author}")

    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to delete messages in this channel!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Deletion Error",
            description=f"An error occurred while deleting messages: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)
        logging.error(f"Error deleting messages: {e}")
@bot.command(aliases=["clearb", "clmb", "clsbot"])
@commands.has_permissions(manage_messages=True)
async def delete_bot_messages(ctx, limit: str = "5"):
    """Delete the bot's recent messages"""
    
    # Parse limit parameter
    if limit.lower() in ["-", "all", "*"]:
        delete_all = True
        limit_int = None
        limit_desc = "all"
    else:
        try:
            limit_int = int(limit)
            if limit_int < 1 or limit_int > 500:
                embed = discord.Embed(
                    title="❌ Invalid Limit",
                    description="Please specify a number between 1-500, or use '-', 'all', or '*' for all bot messages",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            delete_all = False
            limit_desc = str(limit_int)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please specify a valid number, or use '-', 'all', or '*' for all bot messages",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return
    
    # Confirmation with clear description
    confirm_view = ActionConfirmationView(
        author=ctx.author,
        action_type="delete",
        timeout=30.0
    )
    
    embed = discord.Embed(
        title="⚠️ Confirm Bot Message Deletion",
        description=(f"**Target:** This bot's messages in this text channel\n"
                    f"**Amount:** {f'All bot messages' if delete_all else f'Up to {limit_int} messages'} (excluding this command)\n"
                    f"**Channel:** {ctx.channel.mention}\n"
                    f"**Note:** Your command message will also be deleted\n\n"
                    f"⚠️ This action cannot be undone!"),
        color=discord.Color.orange()
    )
    embed.add_field(
        name="📊 Details",
        value=(f"**Bot:** {bot.user.display_name}\n"
              f"**Channel:** {ctx.channel.name}\n"
              f"**Requested by:** {ctx.author.display_name}"),
        inline=False
    )
    
    message = await ctx.send(embed=embed, view=confirm_view)
    await confirm_view.wait()
    
    if not confirm_view.confirmed:
        embed = discord.Embed(
            title="❌ Deletion Cancelled",
            description="Bot message deletion was cancelled",
            color=discord.Color.red()
        )
        await message.edit(embed=embed, view=None)
        return
    
    # Show deletion progress
    embed = discord.Embed(
        title="🗑️ Deleting Bot Messages...",
        description=f"Searching and deleting {f'all' if delete_all else f'up to {limit_int}'} of this bot's messages...",
        color=discord.Color.orange()
    )
    await message.edit(embed=embed, view=None)
    
    try:
        # Store command message reference
        command_message = ctx.message
        
        if delete_all:
            # Delete all bot messages in the channel
            bot_messages_to_delete = []
            async for msg in ctx.channel.history(limit=None):
                if msg.author == bot.user and msg.id != message.id:
                    bot_messages_to_delete.append(msg)
        else:
            # Search through messages to find this bot's messages (limited)
            search_limit = min(limit_int * 5, 1000)  # Search up to 5x the limit or 1000 messages
            bot_messages_to_delete = []
            
            async for msg in ctx.channel.history(limit=search_limit):
                if len(bot_messages_to_delete) >= limit_int:
                    break
                if msg.author == bot.user and msg.id != message.id:
                    bot_messages_to_delete.append(msg)
        
        # Delete the found bot messages
        deleted_count = 0
        for msg in bot_messages_to_delete:
            try:
                await msg.delete()
                deleted_count += 1
            except discord.NotFound:
                pass  # Message already deleted
            except discord.Forbidden:
                logging.warning(f"No permission to delete message {msg.id}")
        
        # Delete the command message
        try:
            await command_message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        
        # Show results
        embed = discord.Embed(
            title="✅ Bot Messages Deleted",
            description=(f"🤖 Successfully deleted **{deleted_count}** of this bot's messages\n"
                        f"📝 Your command message was also deleted"),
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Cleanup Summary",
            value=(f"**Bot Messages:** {deleted_count}\n"
                  f"**Channel:** {ctx.channel.name}\n"
                  f"**Requested by:** {ctx.author.display_name}"),
            inline=False
        )
        
        await message.edit(embed=embed, view=None)
        await asyncio.sleep(5)
        await message.delete()
        
        logging.info(f"Deleted {deleted_count} bot messages in {ctx.channel} by {ctx.author}")
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Deletion Error",
            description=f"Error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await message.edit(embed=embed, view=None)
        logging.error(f"Error in bot message deletion: {e}")

# ========================
# HELP COMMAND
# ========================

@bot.command(aliases=["h", "helpme"])
async def help_(ctx, command: str = None):
    """Enhanced help system with interactive navigation and detailed command information"""
    
    if command:
        # Show specific command help
        await _show_command_help(ctx, command)
    else:
        # Show main help menu with interactive navigation
        await _show_main_help_menu(ctx)

async def _show_main_help_menu(ctx):
    """Display the main help menu with category selection"""
    
    # Create help categories based on actual commands
    help_categories = {
        "general": {
            "name": "General & Info",
            "description": "Basic bot information and server utilities",
            "emoji": "📋",
            "commands": [
                ("h", "Show this comprehensive help menu"),
                ("info", "Display detailed server statistics and information"),
                ("w", "Get comprehensive weather data for any city worldwide"),
                ("status", "Change bot's activity status (Admin only)")
            ]
        },
        "channels": {
            "name": "Channel & Category Management",
            "description": "Advanced channel and category creation tools",
            "emoji": "📝",
            "commands": [
                ("ch", "Create channel in specific category with confirmation"),
                ("chi", "Interactive channel creation with category selection"),
                ("cats", "Create multiple categories with privacy & role settings"),
                ("modcat", "Add/remove role access from existing categories")
            ]
        },
        "deletion": {
            "name": "Deletion & Cleanup",
            "description": "Safe deletion tools with confirmations",
            "emoji": "🗑️",
            "commands": [
                ("rmcc", "Delete categories/channels with advanced options"),
                ("rmi", "Interactive deletion with step-by-step guidance"),
                ("clm", "Delete messages with interactive confirmation"),
                ("clmb", "Advanced bot message cleanup with filtering")
            ]
        },
        "guest_management": {
            "name": "Guest & Role Management",
            "description": "Advanced guest role and permission management",
            "emoji": "🎭",
            "commands": [
                ("addgu", "Add guest role to selected categories interactively"),
                ("rmgu", "Remove guest access from selected categories"),
            ]
        },
        "fun_auto": {
            "name": "Fun & Auto-responses",
            "description": "Entertainment features and automatic responses",
            "emoji": "🎉",
            "commands": [
                ("Auto Greetings", "Responds to hello/hi/salam/ahlan automatically"),
                ("Professor Quotes", "Responds to 'arawkan/ajihna' with random quotes"),
            ]
        }
    }
    
    # Create main embed
    total_commands = len([cmd for cat in help_categories.values() for cmd in cat['commands']])
    embed = discord.Embed(
        title="🤖 Cheb BEKKALI Bot - Help Center",
        description=(
            f"**Prefix:** `!` | **Commands Available:** {total_commands}\n\n"
            f"🎯 **Quick Help:** Use `!help <command>` for detailed information\n"
            f"🔧 **Interactive:** Select categories below for organized browsing\n"
            f"📚 **Examples:** `!help weather` or `!help create_categories`"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    # Add category overview
    category_overview = []
    for category_key, category_data in help_categories.items():
        command_count = len(category_data['commands'])
        category_overview.append(f"{category_data['emoji']} **{category_data['name']}** ({command_count} commands)")
    
    embed.add_field(
        name="📖 Command Categories",
        value="\n".join(category_overview),
        inline=False
    )
    
    # Add most used commands with actual command names
    embed.add_field(
        name="⚡ Most Used Commands",
        value=(
            "```\n"
            "!info    → Detailed server statistics\n"
            "!w       → Weather information\n"
            "!cats    → Create categories with settings\n"
            "!clm     → Clean up messages safely\n"
            "!addgu   → Manage guest access\n"
            "```"
        ),
        inline=False
    )
    
    # Updated permission levels based on actual commands
    embed.add_field(
        name="🔐 Permission Requirements",
        value=(
            "🟢 **Everyone:** help, info, weather\n"
            "🟡 **Manage Channels:** channel/category creation, message deletion\n"
            "🔴 **Administrator:** guest management, category modification, status"
        ),
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {ctx.author.display_name} • Use buttons below to navigate categories",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    # Create interactive view
    view = HelpNavigationView(ctx.author, help_categories)
    
    message = await ctx.send(embed=embed, view=view)
    logging.info(f"Help menu displayed for {ctx.author} in {ctx.guild.name}")

async def _show_command_help(ctx, command_name):
    """Show detailed help for a specific command with updated information"""
    
    # Find the command
    cmd = bot.get_command(command_name.lower())
    if not cmd:
        # Search in aliases
        for bot_command in bot.commands:
            if command_name.lower() in bot_command.aliases:
                cmd = bot_command
                break
    
    if not cmd:
        embed = discord.Embed(
            title="❌ Command Not Found",
            description=f"Command `{command_name}` not found.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="💡 Suggestions",
            value=(
                f"• Use `!help` to see all available commands\n"
                f"• Check your spelling carefully\n"
                f"• Try searching for similar command names\n"
                f"• Use `!help` for the interactive menu"
            ),
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Create detailed command embed
    embed = discord.Embed(
        title=f"📖 Command Help: {cmd.name}",
        description=cmd.help or "No description available.",
        color=discord.Color.green()
    )
    
    # Command usage
    params = []
    if hasattr(cmd, 'clean_params') and cmd.clean_params:
        for param_name, param in cmd.clean_params.items():
            if param.default == param.empty:
                params.append(f"<{param_name}>")  # Required
            else:
                params.append(f"[{param_name}]")  # Optional
    
    usage = f"!{cmd.name} {' '.join(params)}"
    embed.add_field(
        name="📝 Usage Syntax",
        value=f"```{usage}```",
        inline=False
    )
    
    # Aliases
    if cmd.aliases:
        aliases_text = ", ".join(f"`!{alias}`" for alias in cmd.aliases)
        embed.add_field(
            name="🔄 Alternative Names",
            value=aliases_text,
            inline=True
        )
    
    # Required permissions - updated logic
    required_perms = []
    if hasattr(cmd, 'checks') and cmd.checks:
        for check in cmd.checks:
            check_name = getattr(check, '__qualname__', str(check))
            if 'administrator' in check_name.lower():
                required_perms.append('Administrator')
            elif 'manage_channels' in check_name.lower():
                required_perms.append('Manage Channels')
            elif 'manage_messages' in check_name.lower():
                required_perms.append('Manage Messages')
            elif 'has_permissions' in check_name:
                # Try to extract more specific permissions if possible
                required_perms.append('Special Permissions')
    
    if required_perms:
        perms_text = "\n".join(f"• {perm}" for perm in set(required_perms))
        embed.add_field(
            name="🔐 Required Permissions",
            value=perms_text,
            inline=True
        )
    else:
        embed.add_field(
            name="🌍 Access Level",
            value="Available to everyone",
            inline=True
        )
    
    # Updated command-specific examples and tips
    command_examples = {
        "weather": {
            "examples": [
                "!w London",
                "!weather_info \"San Francisco\""
            ],
            "tips": [
                "🌡️ Shows temperature, humidity, wind speed & direction",
                "🌍 Works with cities worldwide (OpenWeatherMap API)",
                "⏱️ Has 15-second cooldown to prevent spam",
                "🎨 Includes interactive weather view with buttons",
                "🔍 Supports city search with country specification"
            ]
        },
        "create_categories": {
            "examples": [
                "!cats Math Physics Chemistry",
                "!categories \"Computer Science\" Biology History",
                "!cats Mathematics \"Data Science\" Literature"
            ],
            "tips": [
                "📁 Creates categories with 5 default channels: cours, tds, tps, exams, bonus",
                "🔒 Interactive privacy settings (public/private)",
                "🎭 Role-based access control with multi-selection",
                "✅ Confirmation prompts for safety",
                "💡 Use quotes for category names with spaces"
            ]
        },
        "create_channel_in_category": {
            "examples": [
                "!channel General announcements",
                "!ch Math \"Problem solving\""
            ],
            "tips": [
                "📝 Creates text channel in specified category",
                "🆕 Auto-creates category if it doesn't exist",
                "✅ Interactive confirmation with detailed preview",
                "🔍 Checks for existing channels to prevent duplicates",
                "💡 Supports spaces in names with quotes"
            ]
        },
        "create_channel_interactive": {
            "examples": [
                "!channeli announcements",
                "!chi general-chat",
            ],
            "tips": [
                "🎯 Interactive category selection with pagination",
                "🔍 Searchable interface for servers with many categories",
                "🆕 Option to create new category during process",
                "📊 Shows channel counts for each category",
                "⚡ Streamlined workflow for quick channel creation"
            ]
        },
        "delete_messages": {
            "examples": [
                "!clear 50",
                "!clm -",
                "!cls 25"
            ],
            "tips": [
                "🗑️ Use '-' to delete all unpinned messages",
                "⚠️ Interactive confirmation prevents accidents",
                "🔢 Range: 1-1000 messages per operation",
                "📌 Pinned messages are automatically preserved",
                "📊 Shows deletion progress and results"
            ]
        },
        "delete_bot_messages": {
            "examples": [
                "!clearb 10",
                "!clmb -",
                "!clmb 20"
            ],
            "tips": [
                "🤖 Can target only this bot or all bots",
                "🔍 Advanced filtering options available",
                "⏱️ Time-based cleanup (hourly, daily)",
                "👤 User-specific message deletion",
                "📊 Detailed cleanup statistics"
            ]
        },
        "add_guest_selective": {
            "examples": [
                "!addguest Visitor",
                "!addgu \"External User\""
            ],
            "tips": [
                "🎯 Interactive category selection with visual indicators",
                "📄 Pagination for servers with many categories",
                "🔍 Search functionality for quick category finding",
                "✅ Shows current access status before modification",
                "⚡ Batch processing for efficiency"
            ]
        },
        "server_info": {
            "examples": [
                "!server_info",
                "!info",
            ],
            "tips": [
                "📊 Comprehensive server statistics and analytics",
                "👥 Member breakdown (online, bots, humans)",
                "📢 Channel and category counts",
                "🎭 Role information and hierarchy",
                "🌟 Server features and boost level"
            ]
        },
        "rmcc": {
            "examples": [
                "!rmcc --cha announcements",
                "!rmcc --cat \"Study Materials\"",
                "!rmcc Math",
                "!rmcc --cha homework --cat Math"
            ],
            "tips": [
                "🎯 Flexible syntax for channels and categories",
                "⚠️ Danger confirmation for category deletion",
                "🔍 Search within specific categories",
                "📊 Shows impact before deletion",
                "🛡️ Multiple safety confirmations"
            ]
        },
        "interactive_delete": {
            "examples": [
                "!rmi"
            ],
            "tips": [
                "🎯 Step-by-step guided deletion process",
                "📄 Paginated selection for large servers",
                "🔍 Search and filter capabilities",
                "📊 Real-time deletion progress",
                "✅ Multiple confirmation layers"
            ]
        }
    }
    
    if cmd.name in command_examples:
        cmd_info = command_examples[cmd.name]
        
        if cmd_info.get("examples"):
            examples_text = "\n".join(f"`{ex}`" for ex in cmd_info["examples"])
            embed.add_field(
                name="💡 Usage Examples",
                value=examples_text,
                inline=False
            )
        
        if cmd_info.get("tips"):
            tips_text = "\n".join(cmd_info["tips"])
            embed.add_field(
                name="🎯 Features & Tips",
                value=tips_text,
                inline=False
            )
    
    # Cooldown info
    if hasattr(cmd, '_buckets') and cmd._buckets:
        bucket = cmd._buckets._cooldown
        if bucket:
            embed.add_field(
                name="⏱️ Cooldown",
                value=f"{bucket.rate} use(s) per {bucket.per} second(s)",
                inline=True
            )
    
    # Add related commands
    related_commands = {
        "w": ["info", "h"],
        "cats": ["ch", "chi", "modcat"],
        "ch": ["cats", "chi"],
        "chi": ["ch", "cats"],
        "clm": ["clmb", "rmi"],
        "clmb": ["clm", "rmi"],
        "addgu": ["rmgu", "modcat"],
        "rmgu": ["addgu", "modcat"]
    }
    
    if cmd.name in related_commands:
        related_list = [f"`!{related}`" for related in related_commands[cmd.name]]
        embed.add_field(
            name="🔗 Related Commands",
            value=" • ".join(related_list),
            inline=False
        )
    
    embed.set_footer(
        text=f"Use !help for main menu • Requested by {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    
    await ctx.send(embed=embed)
    logging.info(f"Detailed help for '{cmd.name}' shown to {ctx.author}")

# ========================
# UPDATED HELP NAVIGATION VIEW
# ========================
class HelpNavigationView(discord.ui.View):
    def __init__(self, author, help_categories):
        super().__init__(timeout=300.0)  # 5 minutes timeout
        self.author = author
        self.help_categories = help_categories
        self.current_category = None
        
        # Add category select dropdown
        self.category_select = CategorySelectDropdown(help_categories)
        self.add_item(self.category_select)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command author can use the view"""
        if interaction.user != self.author:
            await interaction.response.send_message(
                "❌ Only the person who used the help command can navigate this menu.",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True
        
        # Try to edit the message to show it's expired
        try:
            if hasattr(self, 'message') and self.message:
                embed = discord.Embed(
                    title="⏰ Help Menu Expired",
                    description="This help menu has expired. Use `!help` to create a new one.",
                    color=discord.Color.greyple()
                )
                await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass
    
    @discord.ui.button(label="🏠 Main Menu", style=discord.ButtonStyle.primary, row=1)
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main menu"""
        await interaction.response.defer()
        
        # Recreate main help menu
        total_commands = len([cmd for cat in self.help_categories.values() for cmd in cat['commands']])
        embed = discord.Embed(
            title="🤖 Cheb BEKKALI Bot - Help Center",
            description=(
                f"**Prefix:** `!` | **Commands Available:** {total_commands}\n\n"
                f"🎯 **Quick Help:** Use `!help <command>` for detailed information\n"
                f"🔧 **Interactive:** Select categories below for organized browsing\n"
                f"📚 **Examples:** `!help weather` or `!help create_categories`"
            ),
            color=discord.Color.blue()
        )
        
        # Add category overview
        category_overview = []
        for category_key, category_data in self.help_categories.items():
            command_count = len(category_data['commands'])
            category_overview.append(f"{category_data['emoji']} **{category_data['name']}** ({command_count} commands)")
        
        embed.add_field(
            name="📖 Command Categories",
            value="\n".join(category_overview),
            inline=False
        )
        
        await interaction.edit_original_response(embed=embed, view=self)
        self.current_category = None
    
    @discord.ui.button(label="📚 Quick Reference", style=discord.ButtonStyle.secondary, row=1)
    async def quick_ref_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show quick reference card"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📚 Quick Reference Card",
            description="Most commonly used commands organized by function",
            color=discord.Color.green()
        )
        
        # Essential commands
        embed.add_field(
            name="🔥 Essential Commands",
            value=(
                "```\n"
                "!info         → Detailed server statistics\n"
                "!w <city>     → Comprehensive weather data\n"
                "!h <command>  → Detailed command help\n"
                "```"
            ),
            inline=False
        )
        
        # Channel & Category management
        embed.add_field(
            name="📝 Channel & Category Management",
            value=(
                "```\n"
                "!cats <names>            → Create multiple categories\n"
                "!chi                     → Interactive channel creation\n"
                "!rmcc --cat <cat_name>   → Delete categories safely\n"
                "!rmi                     → Guided deletion process\n"
                "```"
            ),
            inline=False
        )
        
        # Message Management
        embed.add_field(
            name="🛡️ Message Management",
            value=(
                "```\n"
                "!clm <amount>   → Clean up messages\n"
                "!clmb <amount>  → Clean bot messages\n"
                "![clm/clmb] -   → Clean all [/bot] messages\n"
                "```"
            ),
            inline=False
        )
        
        # Guest & Role management
        embed.add_field(
            name="🎭 Guest & Role Management",
            value=(
                "```\n"
                "!addgu <role>  → Add guest to categories\n"
                "!rmgu <role>   → Remove guest access\n"
                "!modcat        → Advanced access control\n"
                "```"
            ),
            inline=False
        )
        
        embed.set_footer(text="💡 Use !help <command> for detailed information and examples")
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label="ℹ️ Bot Info", style=discord.ButtonStyle.secondary, row=1)
    async def bot_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show bot information"""
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🤖 Cheb BEKKALI Bot Information",
            description="Academic server management bot with advanced features",
            color=discord.Color.blue()
        )
        
        # Bot stats
        total_commands = len(bot.commands)
        total_guilds = len(bot.guilds)
        total_users = sum(guild.member_count for guild in bot.guilds)
        
        embed.add_field(
            name="📊 Current Statistics",
            value=(
                f"**Commands:** {total_commands}\n"
                f"**Servers:** {total_guilds}\n"
                f"**Users:** {total_users:,}\n"
                f"**Latency:** {round(bot.latency * 1000)}ms"
            ),
            inline=True
        )
        
        # Key features
        embed.add_field(
            name="✨ Key Features",
            value=(
                "🔧 Interactive channel management\n"
                "🎭 Advanced guest role system\n"
                "🌤️ Weather information service\n"
                "🛡️ Safe deletion with confirmations\n"
                "📊 Comprehensive server analytics\n"
                "🎯 Smart auto-responses"
            ),
            inline=True
        )
        
        # Technical info
        embed.add_field(
            name="⚙️ Technical Details",
            value=(
                f"**Python:** {sys.version.split()[0]}\n"
                f"**Discord.py:** {discord.__version__}\n"
                f"**Prefix:** `!`\n"
                f"**Command Categories:** 5\n"
                f"**Interactive Features:** ✅\n"
                f"**API Integrations:** OpenWeatherMap"
            ),
            inline=True
        )
        
        # Command categories breakdown
        embed.add_field(
            name="**Command Distribution**",
            value=(
                f"📋 **General & Info:** 4 commands\n"
                f"📝 **Channel Management:** 4 commands\n"
                f"🗑️ **Deletion & Cleanup:** 4 commands\n"
                f"🎭 **Guest Management:** 4+ commands\n"
                f"🎉 **Fun & Auto-responses:** 3 features"
            ),
            inline=False
        )
        
        embed.set_footer(text="Built with ❤️ for academic server management • Open source")
        
        await interaction.edit_original_response(embed=embed, view=self)

class CategorySelectDropdown(discord.ui.Select):
    def __init__(self, help_categories):
        self.help_categories = help_categories
        
        options = []
        for category_key, category_data in help_categories.items():
            options.append(discord.SelectOption(
                label=category_data['name'],
                description=category_data['description'][:100],  # Discord limit
                emoji=category_data['emoji'],
                value=category_key
            ))
        
        super().__init__(
            placeholder="🔍 Select a category to explore commands...",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        category_key = self.values[0]
        category_data = self.help_categories[category_key]
        
        # Create category-specific embed
        embed = discord.Embed(
            title=f"{category_data['emoji']} {category_data['name']}",
            description=f"{category_data['description']}\n\n **{len(category_data['commands'])} commands available**",
            color=discord.Color.green()
        )
        
        # Add commands with better formatting
        commands_text = []
        for i, (cmd_name, cmd_desc) in enumerate(category_data['commands'], 1):
            # Handle both tuple and string formats
            if isinstance(cmd_name, str) and not cmd_name.startswith("Auto"):
                commands_text.append(f"**{i}.** `!{cmd_name}`\n   └ {cmd_desc}")
            else:
                commands_text.append(f"**{i}.** **{cmd_name}**\n   └ {cmd_desc}")
        
        embed.add_field(
            name=f"📋 Available Commands",
            value="\n\n".join(commands_text),
            inline=False
        )
        
        # Add category-specific enhanced tips
        category_tips = {
            "general": [
                "💡 Use `!help <command>` for comprehensive command information",
                "🌤️ Weather command includes interactive features and detailed forecasts",
                "📊 Server info provides real-time statistics and analytics",
                "⚙️ Status command allows customization of bot presence"
            ],
            "channels": [
                "🎯 All channel commands feature interactive step-by-step guidance",
                "🔒 Category creation supports advanced privacy and role settings",
                "✅ Safety confirmations prevent accidental operations",
                "💡 Interactive commands adapt to server size with pagination"
            ],
            "deletion": [
                "⚠️ Multiple confirmation layers ensure safe deletion",
                "🎯 Interactive deletion provides visual selection interfaces",
                "📊 Progress tracking and detailed result reporting",
                "🛡️ Special safety measures for category deletion"
            ],
            "guest_management": [
                "🎭 Supports batch operations for efficiency",
                "🔍 Visual indicators show current access status",
                "📄 Pagination handles servers with many categories",
                "⚡ Search functionality for quick category finding"
            ],
            "fun_auto": [
                "🎲 Auto-responses work across all text channels",
                "🎪 Professor quotes are context-aware and randomized",
                "🌟 Smart greeting detection in multiple languages",
                "🔧 More interactive features planned for future updates"
            ]
        }
        
        if category_key in category_tips:
            embed.add_field(
                name="Features & Tips",
                value="\n".join(category_tips[category_key]),
                inline=False
            )
        
        # Add usage statistics or additional info
        if category_key == "general":
            embed.add_field(
                name="📈 Usage Info",
                value="These commands are available to all users and form the core functionality of the bot.",
                inline=False
            )
        elif category_key == "channels":
            embed.add_field(
                name="🔐 Permission Note",
                value="Requires **Manage Channels** permission. All operations include safety confirmations.",
                inline=False
            )
        elif category_key == "guest_management":
            embed.add_field(
                name="⚡ Pro Tip",
                value="Use interactive commands for complex operations. They guide you through each step!",
                inline=False
            )
        
        embed.set_footer(text="Use buttons below to navigate or select another category")
        
        await interaction.edit_original_response(embed=embed, view=self.view)
        self.view.current_category = category_key

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
    
    # Préparer les options de rôles avec filtrage
    all_roles = [role for role in guild.roles 
                if role.name != "@everyone" and role < guild.me.top_role]

    if action.lower() == "add":
        # Pour "add", exclure les rôles qui ont déjà accès
        current_access_roles = {role.id for role, overwrite in category.overwrites.items() 
                                if isinstance(role, discord.Role) and overwrite.view_channel is True}
        eligible_roles = [role for role in all_roles if role.id not in current_access_roles]
    else:
        # Pour "remove", montrer seulement les rôles qui ont accès
        access_roles = {role.id for role, overwrite in category.overwrites.items() 
                        if isinstance(role, discord.Role) and overwrite.view_channel is True}
        eligible_roles = [role for role in all_roles if role.id in access_roles]

    if not eligible_roles:
        await ctx.send("⚠️ No eligible roles found.", delete_after=5)
        return

    # Créer les options pour la sélection
    role_options = []
    for role in eligible_roles:
        role_options.append({
            'label': role.name,
            'value': str(role.id),
            'description': f"Members: {len(role.members)}",
            'emoji': "🎭"
        })

    # Sélection des rôles
    embed = discord.Embed(
        title=f"Modify Access: {category_name}",
        description=f"**Action:** {action.title()}\nSelect roles to {action}:",
        color=discord.Color.blue()
    )
    
    role_view = PaginatedSelectionView(
        author=ctx.author,
        options=role_options,
        placeholder="Select roles...",
        min_values=1,
        max_values=min(10, len(role_options)),
        timeout=60.0
    )
    
    role_msg = await ctx.send(embed=embed, view=role_view)
    await role_view.wait()
    
    if not role_view.confirmed or not role_view.selected_values:
        await ctx.send("⚠️ No roles selected. Operation cancelled.", delete_after=5)
        return
    
    # Récupérer les rôles sélectionnés
    selected_roles = [guild.get_role(int(role_id)) for role_id in role_view.selected_values]
    selected_roles = [role for role in selected_roles if role]  # Filtrer les None
    
    # Confirmation avec les nouvelles classes
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
    
    confirm_view = ActionConfirmationView(ctx.author, action)
    confirm_msg = await ctx.send(embed=confirm_embed, view=confirm_view)
    await confirm_view.wait()
    
    if not confirm_view.confirmed:
        await ctx.send("🚫 Operation cancelled.", delete_after=5)
        return
    
    # Appliquer les modifications
    try:
        channels_modified = []
        
        if action.lower() == "add":
            # Code d'ajout existant...
            current_overwrites = category.overwrites
            
            if guild.default_role not in current_overwrites or current_overwrites[guild.default_role].view_channel is not False:
                current_overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            
            for role in selected_roles:
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

            await category.edit(overwrites=current_overwrites)
            
            for channel in category.channels:
                channel_overwrites = channel.overwrites.copy()
                
                if guild.default_role not in channel_overwrites or channel_overwrites[guild.default_role].view_channel is not False:
                    channel_overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                
                for role in selected_roles:
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
            # Code de suppression existant...
            current_overwrites = category.overwrites.copy()
            
            for role in selected_roles:
                if role in current_overwrites:
                    del current_overwrites[role]
            
            await category.edit(overwrites=current_overwrites)
            
            for channel in category.channels:
                channel_overwrites = channel.overwrites.copy()
                
                for role in selected_roles:
                    if role in channel_overwrites:
                        del channel_overwrites[role]
                
                await channel.edit(overwrites=channel_overwrites)
                channels_modified.append(channel.name)
            
            action_text = f"Removed access for {len(selected_roles)} roles"
        
        # Message de confirmation final
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
        
        if channels_modified:
            channel_list = ", ".join(f"#{ch}" for ch in channels_modified[:10])
            if len(channels_modified) > 10:
                channel_list += f" (+{len(channels_modified) - 10} more)"
            
            embed.add_field(
                name=f"📢 Channels modified [{len(channels_modified)}]:",
                value=channel_list,
                inline=False
            )
        
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
        await asyncio.sleep(2)
        try:
            await role_msg.delete()
            await confirm_msg.delete()
        except discord.NotFound:
            pass

# ========================
# GUESTS MANAGEMENT
# ========================
@bot.command(aliases=["addguest", "addgu"])
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
    
    # Préparer les options de catégories
    category_options = []
    for category in categories:
        has_access = (role in category.overwrites and 
                     category.overwrites[role].view_channel is True)
        
        emoji = "✅" if has_access else "📁"
        description = f"{len(category.channels)} canaux"
        if has_access:
            description += " (déjà accès)"
        
        category_options.append({
            'label': category.name,
            'value': str(category.id),
            'description': description,
            'emoji': emoji
        })
    
    # Utiliser SearchableSelectionView pour les grandes listes
    embed = discord.Embed(
        title=f"🎯 Sélection de catégories pour: {role_name}",
        description=f"**Rôle:** {role.mention}\n"
                   f"**Total catégories:** {len(categories)}\n\n"
                   f"**Instructions:**\n"
                   f"• Sélectionnez les catégories où ajouter le rôle\n"
                   f"• ✅ = Rôle a déjà accès\n"
                   f"• 📁 = Rôle n'a pas accès",
        color=discord.Color.blue()
    )
    
    # Choisir la vue appropriée selon le nombre de catégories
    if len(categories) > 25:
        view = SearchableSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select categories or search...",
            timeout=120.0,
            min_values=1,
            max_values=min(10, len(category_options))
        )
    else:
        view = PaginatedSelectionView(
            author=ctx.author,
            options=category_options,
            placeholder="Select categories...",
            min_values=1,
            max_values=min(10, len(category_options)),
            timeout=120.0
        )
    
    selection_msg = await ctx.send(embed=embed, view=view)
    await view.wait()
    
    if not view.confirmed or not view.selected_values:
        await ctx.send("⚠️ Aucune catégorie sélectionnée.", delete_after=5)
        return
    
    # Récupérer les catégories sélectionnées
    selected_categories = [guild.get_channel(int(cat_id)) for cat_id in view.selected_values]
    selected_categories = [cat for cat in selected_categories if cat and isinstance(cat, discord.CategoryChannel)]
    
    # Confirmation finale
    final_confirm_embed = discord.Embed(
        title="⚠️ Confirmation finale",
        description=f"**Rôle à ajouter:** {role.mention}\n"
                   f"**Catégories sélectionnées:** {len(selected_categories)}",
        color=discord.Color.orange()
    )
    
    selected_text = []
    total_channels = 0
    for cat in selected_categories:
        total_channels += len(cat.channels)
        selected_text.append(f"📁 **{cat.name}** ({len(cat.channels)} canaux)")
    
    final_confirm_embed.add_field(
        name="📋 Catégories qui seront modifiées:",
        value="\n".join(selected_text),
        inline=False
    )
    
    final_confirm_embed.add_field(
        name="📊 Impact:",
        value=f"**{len(selected_categories)}** catégories\n"
              f"**{total_channels}** canaux au total",
        inline=False
    )
    
    final_view = ActionConfirmationView(ctx.author, "apply")
    final_msg = await ctx.send(embed=final_confirm_embed, view=final_view)
    await final_view.wait()
    
    if not final_view.confirmed:
        await ctx.send("🚫 Opération annulée.", delete_after=5)
        return
    
    # Appliquer les modifications
    try:
        await final_msg.edit(embed=discord.Embed(
            title="⏳ Application des modifications...",
            description=f"Traitement de {len(selected_categories)} catégories...",
            color=discord.Color.yellow()
        ), view=None)
        
        success_count = 0
        error_count = 0
        processed_channels = 0
        errors = []
        
        for i, category in enumerate(selected_categories):
            try:
                if i % 3 == 0:
                    progress_embed = discord.Embed(
                        title="⏳ Traitement en cours...",
                        description=f"📁 **{category.name}** ({i+1}/{len(selected_categories)})",
                        color=discord.Color.yellow()
                    )
                    await final_msg.edit(embed=progress_embed)
                
                current_overwrites = category.overwrites.copy()
                current_overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                await category.edit(overwrites=current_overwrites)
                
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
                      f"✅ Catégories modifiées: {success_count}/{len(selected_categories)}\n"
                      f"📢 Canaux modifiés: {processed_channels}\n"
                      f"❌ Erreurs: {error_count}\n"
                      f"🎭 Rôle ajouté: {role_name}"
                      f"```",
                inline=False
            )
            
            success_categories = [cat.name for cat in selected_categories]
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

@bot.command(aliases=["rmguest", "rmgu"])
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
    
    # Préparer les options pour le menu de sélection
    options = [
        {
            'label': category.name,
            'value': str(category.id),
            'description': f"{len(category.channels)} canaux - ACCÈS ACTUEL",
            'emoji': "🔓"
        }
        for category in categories_with_access
    ]
    
    # Créer la vue de sélection paginée
    view = PaginatedSelectionView(
        author=ctx.author,
        options=options,
        placeholder="Sélectionnez les catégories à retirer...",
        min_values=0,
        max_values=len(options),
        timeout=120.0,
        auto_confirm=False,
        items_per_page=25
    )
    
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
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        return
    elif not view.confirmed:
        await ctx.send("🚫 Opération annulée par l'utilisateur.", delete_after=5)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        return
    
    # Récupérer les catégories sélectionnées
    selected_categories = [
        discord.utils.get(guild.categories, id=int(value))
        for value in view.selected_values
    ]
    selected_categories = [cat for cat in selected_categories if cat]  # Filtrer les None
    
    if not selected_categories:
        await ctx.send("⚠️ Aucune catégorie sélectionnée.", delete_after=5)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        return
    
    # Confirmation finale avec résumé
    final_confirm_embed = discord.Embed(
        title="⚠️ Confirmation - Retrait d'accès",
        description=f"**Rôle à retirer:** {role.mention}\n"
                   f"**Catégories sélectionnées:** {len(selected_categories)}",
        color=discord.Color.red()
    )
    
    # Afficher les catégories sélectionnées
    selected_text = []
    total_channels = 0
    for cat in selected_categories:
        total_channels += len(cat.channels)
        selected_text.append(f"🔒 **{cat.name}** ({len(cat.channels)} canaux)")
    
    final_confirm_embed.add_field(
        name="📋 Catégories qui perdront l'accès:",
        value="\n".join(selected_text),
        inline=False
    )
    
    final_confirm_embed.add_field(
        name="📊 Impact:",
        value=f"**{len(selected_categories)}** catégories\n"
              f"**{total_channels}** canaux au total\n"
              f"⚠️ **ATTENTION:** L'accès sera complètement retiré!",
        inline=False
    )
    
    final_confirm_embed.set_footer(text="Cette action retirera définitivement l'accès!")
    
    # Utiliser ActionConfirmationView pour la confirmation finale
    final_view = ActionConfirmationView(
        author=ctx.author,
        action_type="remove",
        timeout=30.0
    )
    final_msg = await ctx.send(embed=final_confirm_embed, view=final_view)
    await final_view.wait()
    
    if final_view.confirmed is None:
        await ctx.send("🕒 Confirmation expirée - Opération annulée.", delete_after=5)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        return
    elif not final_view.confirmed:
        await ctx.send("🚫 Opération annulée.", delete_after=5)
        try:
            await selection_msg.delete()
        except discord.NotFound:
            pass
        return
    
    # Appliquer les modifications
    try:
        await final_msg.edit(embed=discord.Embed(
            title="⏳ Retrait des accès en cours...",
            description=f"Traitement de {len(selected_categories)} catégories...",
            color=discord.Color.yellow()
        ), view=None)
        
        success_count = 0
        error_count = 0
        processed_channels = 0
        errors = []
        
        for i, category in enumerate(selected_categories):
            try:
                # Mise à jour du statut
                if i % 3 == 0:
                    progress_embed = discord.Embed(
                        title="⏳ Retrait en cours...",
                        description=f"🔒 **{category.name}** ({i+1}/{len(selected_categories)})",
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
                      f"🔒 Catégories modifiées: {success_count}/{len(selected_categories)}\n"
                      f"📢 Canaux modifiés: {processed_channels}\n"
                      f"❌ Erreurs: {error_count}\n"
                      f"🎭 Rôle retiré: {role_name}"
                      f"```",
                inline=False
            )
            
            # Lister les catégories modifiées avec succès
            success_categories = [cat.name for cat in selected_categories]
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

# ========================
# RUN BOT
# ========================
if __name__ == "__main__":
    if not TOKEN:
        logging.critical("❌ No bot token found in environment!")
    else:
        bot.run(TOKEN)