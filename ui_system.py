import discord
from typing import Optional, List, Dict, Any, Callable
import math
from datetime import datetime, timezone

# ========================
# REUSABLE BUTTON CLASSES
# ========================

ctx = ""

class ConfirmationView(discord.ui.View):
    """Standard confirmation view with Confirm/Cancel buttons"""

    def __init__(self,
                 author: discord.Member,
                 timeout: float = 30.0,
                 confirm_label: str = "Confirm",
                 cancel_label: str = "Cancel",
                 confirm_style: discord.ButtonStyle = discord.ButtonStyle.green,
                 cancel_style: discord.ButtonStyle = discord.ButtonStyle.red,
                 confirm_emoji: str = "✅",
                 cancel_emoji: str = "✖"):
        super().__init__(timeout=timeout)
        self.author = author
        self.confirmed: Optional[bool] = None
        
        # Bouton de confirmation
        self.confirm_button = discord.ui.Button(
            label=confirm_label,
            style=confirm_style,
            emoji=confirm_emoji,
            row=0
        )
        self.confirm_button.callback = self._confirm_callback
        self.add_item(self.confirm_button)
        
        # Bouton d'annulation
        self.cancel_button = discord.ui.Button(
            label=cancel_label,
            style=cancel_style,
            emoji=cancel_emoji,
            row=0
        )
        self.cancel_button.callback = self._cancel_callback
        self.add_item(self.cancel_button)
    
    async def _confirm_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can confirm.", ephemeral=True)
            return
        self.confirmed = True
        await interaction.response.defer()
        self.stop()
    
    async def _cancel_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the command author can cancel.", ephemeral=True)
            return
        self.confirmed = False
        await interaction.response.defer()
        self.stop()
    
    async def on_timeout(self):
        self.confirmed = None
        self.stop()

class DangerConfirmationView(ConfirmationView):
    """Confirmation view for dangerous actions (deletion, etc.)"""

    def __init__(self, author: discord.Member, timeout: float = 30.0, action_name: str = "this action"):
        super().__init__(
            author=author,
            timeout=timeout,
            confirm_label=f"Confirm {action_name}",
            cancel_label="Cancel",
            confirm_style=discord.ButtonStyle.red,
            cancel_style=discord.ButtonStyle.secondary,
            confirm_emoji="⚠️",
            cancel_emoji="❌"
        )

class ActionConfirmationView(ConfirmationView):
    """Confirmation view for specific actions with customization"""

    def __init__(self,
                 author: discord.Member,
                 action_type: str,
                 timeout: float = 30.0):

        # Predefined configurations for different action types
        configs = {
            "delete": {
                "confirm_label": "Delete",
                "confirm_style": discord.ButtonStyle.red,
                "confirm_emoji": "🗑️"
            },
            "modify": {
                "confirm_label": "Modify",
                "confirm_style": discord.ButtonStyle.green,
                "confirm_emoji": "🔧"
            },
            "add": {
                "confirm_label": "Add",
                "confirm_style": discord.ButtonStyle.green,
                "confirm_emoji": "➕"
            },
            "remove": {
                "confirm_label": "Remove",
                "confirm_style": discord.ButtonStyle.red,
                "confirm_emoji": "➖"
            },
            "create": {
                "confirm_label": "Create",
                "confirm_style": discord.ButtonStyle.green,
                "confirm_emoji": "🆕"
            },
            "apply": {
                "confirm_label": "Apply",
                "confirm_style": discord.ButtonStyle.green,
                "confirm_emoji": "✅"
            }
        }
        
        config = configs.get(action_type.lower(), configs["apply"])
        
        super().__init__(
            author=author,
            timeout=timeout,
            confirm_label=config["confirm_label"],
            cancel_label="Cancel",
            confirm_style=config["confirm_style"],
            cancel_style=discord.ButtonStyle.secondary,
            confirm_emoji=config["confirm_emoji"],
            cancel_emoji="❌"
        )

class PaginationView(discord.ui.View):
    """Reusable pagination view"""

    def __init__(self,
                 author: discord.Member,
                 pages: list,
                 timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.author = author
        self.pages = pages
        self.current_page = 0
        
        # Navigation buttons
        self.prev_button = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            emoji="◀️",
            disabled=True,
            row=0
        )
        self.prev_button.callback = self._prev_page
        self.add_item(self.prev_button)
        
        self.page_info = discord.ui.Button(
            label=f"1/{len(pages)}",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=0
        )
        self.add_item(self.page_info)
        
        self.next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            emoji="▶️",
            disabled=len(pages) <= 1,
            row=0
        )
        self.next_button.callback = self._next_page
        self.add_item(self.next_button)
    
    async def _prev_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can navigate.", ephemeral=True)
            return
        
        self.current_page = max(0, self.current_page - 1)
        await self._update_view(interaction)
    
    async def _next_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can navigate.", ephemeral=True)
            return
        
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        await self._update_view(interaction)
    
    async def _update_view(self, interaction: discord.Interaction):
        # Update buttons
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.pages) - 1
        self.page_info.label = f"{self.current_page + 1}/{len(self.pages)}"

        # Update message with new page
        embed = self.pages[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)
    
    def get_current_embed(self):
        return self.pages[self.current_page] if self.pages else None

class SelectionView(discord.ui.View):
    """Generic selection view with dropdown and optional confirmation"""

    def __init__(self,
                 author: discord.Member,
                 options: list,
                 placeholder: str = "Select an option...",
                 min_values: int = 1,
                 max_values: int = 1,
                 timeout: float = 60.0,
                 auto_confirm: bool = False,
                 show_back_button: bool = False,
                 back_callback=None):
        super().__init__(timeout=timeout)
        self.author = author
        self.selected_values = []
        self.confirmed: Optional[bool] = None
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.select_options_data = options
        self.auto_confirm = auto_confirm
        self.show_back_button = show_back_button
        self.back_callback = back_callback

        # Create the Select menu
        self.select = discord.ui.Select(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=min(self.max_values, len(self.select_options_data)),
            options=[],
            row=0
        )
        self.update_select_options()
        self.select.callback = self._select_callback
        self.add_item(self.select)

        # Bouton précédent (si activé)
        if self.show_back_button:
            self.back_button = discord.ui.Button(
                label="← Previous",
                style=discord.ButtonStyle.secondary,
                emoji="⬅️",
                row=1
            )
            self.back_button.callback = self._back_callback
            self.add_item(self.back_button)

        # Boutons de confirmation (seulement si auto_confirm est False)
        if not self.auto_confirm:
            self.confirm_button = discord.ui.Button(
                label="Confirm",
                style=discord.ButtonStyle.green,
                emoji="✅",
                disabled=True,
                row=1
            )
            self.confirm_button.callback = self._confirm_callback
            self.add_item(self.confirm_button)

            self.cancel_button = discord.ui.Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="✖",
                row=1
            )
            self.cancel_button.callback = self._cancel_callback
            self.add_item(self.cancel_button)

    def update_select_options(self):
        """Update dropdown options and reflect current selection"""
        self.select.options.clear()
        for i, option in enumerate(self.select_options_data):
            value = option.get('value', str(i)) if isinstance(option, dict) else str(i)
            is_selected = value in self.selected_values

            if isinstance(option, dict):
                self.select.append_option(discord.SelectOption(
                    label=option.get('label', f'Option {i+1}'),
                    value=value,
                    description=option.get('description', None),
                    emoji=option.get('emoji', None),
                    default=is_selected
                ))
            else:
                self.select.append_option(discord.SelectOption(
                    label=str(option),
                    value=value,
                    default=is_selected
                ))

    async def _select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can select.", ephemeral=True)
            return

        self.selected_values = interaction.data['values']
        
        if self.auto_confirm:
            # Confirmation automatique
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        else:
            # Mode manuel avec bouton de confirmation
            self.confirm_button.disabled = len(self.selected_values) == 0
            self.update_select_options()
            await interaction.response.edit_message(view=self)

    async def _back_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can go back.", ephemeral=True)
            return
        
        if self.back_callback:
            await self.back_callback(interaction)
        else:
            await interaction.response.defer()

    async def _confirm_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can confirm.", ephemeral=True)
            return
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    async def _cancel_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can cancel.", ephemeral=True)
            return
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

# ========================
# CUSTOM VIEWS
# ========================

class PaginatedSelectionView(discord.ui.View):
    """Selection view with pagination for handling large lists of options"""

    def __init__(self,
                 author: discord.Member,
                 options: List[Dict[str, Any]],
                 placeholder: str = "Select an option...",
                 min_values: int = 1,
                 max_values: int = 1,
                 timeout: float = 60.0,
                 auto_confirm: bool = False,
                 show_back_button: bool = False,
                 back_callback: Optional[Callable] = None,
                 items_per_page: int = 20):  # Max 20 pour laisser place aux options spéciales
        super().__init__(timeout=timeout)
        self.author = author
        self.selected_values = []
        self.confirmed: Optional[bool] = None
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.all_options = options
        self.auto_confirm = auto_confirm
        self.show_back_button = show_back_button
        self.back_callback = back_callback
        self.items_per_page = items_per_page
        
        # Pagination
        self.current_page = 0
        self.total_pages = max(1, math.ceil(len(self.all_options) / self.items_per_page))
        
        # Create the Select menu
        self.select = discord.ui.Select(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=1,  # Limité à 1 pour la pagination
            options=[],
            row=0
        )
        self.select.callback = self._select_callback
        self.add_item(self.select)

        # Pagination buttons (row 1)
        if self.total_pages > 1:
            self.prev_button = discord.ui.Button(
                label="◀ Previous",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=1
            )
            self.prev_button.callback = self._prev_page_callback
            self.add_item(self.prev_button)

            self.page_button = discord.ui.Button(
                label=f"Page 1/{self.total_pages}",
                style=discord.ButtonStyle.gray,
                disabled=True,
                row=1
            )
            self.add_item(self.page_button)

            self.next_button = discord.ui.Button(
                label="Next ▶",
                style=discord.ButtonStyle.secondary,
                disabled=self.total_pages <= 1,
                row=1
            )
            self.next_button.callback = self._next_page_callback
            self.add_item(self.next_button)

        # Back button (row 2)
        if self.show_back_button:
            self.back_button = discord.ui.Button(
                label="← Previous",
                style=discord.ButtonStyle.secondary,
                emoji="⬅️",
                row=2
            )
            self.back_button.callback = self._back_callback
            self.add_item(self.back_button)

        # Confirmation buttons (row 2 or 3)
        button_row = 3 if self.show_back_button else 2
        if not self.auto_confirm:
            self.confirm_button = discord.ui.Button(
                label="Confirm",
                style=discord.ButtonStyle.green,
                emoji="✅",
                disabled=True,
                row=button_row
            )
            self.confirm_button.callback = self._confirm_callback
            self.add_item(self.confirm_button)

            self.cancel_button = discord.ui.Button(
                label="Cancel",
                style=discord.ButtonStyle.red,
                emoji="✖",
                row=button_row
            )
            self.cancel_button.callback = self._cancel_callback
            self.add_item(self.cancel_button)

        # Update initial options
        self.update_select_options()

    def get_current_page_options(self) -> List[Dict[str, Any]]:
        """Get options for the current page"""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.all_options[start_idx:end_idx]

    def update_select_options(self):
        """Update dropdown options for current page"""
        self.select.options.clear()
        
        current_options = self.get_current_page_options()
        
        for i, option in enumerate(current_options):
            value = option.get('value', str(i)) if isinstance(option, dict) else str(i)
            is_selected = value in self.selected_values

            if isinstance(option, dict):
                self.select.append_option(discord.SelectOption(
                    label=option.get('label', f'Option {i+1}')[:100],  # Discord limit
                    value=value,
                    description=option.get('description', None)[:100] if option.get('description') else None,
                    emoji=option.get('emoji', None),
                    default=is_selected
                ))
            else:
                self.select.append_option(discord.SelectOption(
                    label=str(option)[:100],
                    value=value,
                    default=is_selected
                ))

        # Update pagination buttons if they exist
        if self.total_pages > 1:
            self.prev_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page >= self.total_pages - 1
            self.page_button.label = f"Page {self.current_page + 1}/{self.total_pages}"

    async def _select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can select.", ephemeral=True)
            return

        selected_value = interaction.data['values'][0]
        
        if selected_value in self.selected_values:
            self.selected_values.remove(selected_value)
        else:
            if len(self.selected_values) >= self.max_values:
                self.selected_values = [selected_value]
            else:
                self.selected_values.append(selected_value)
        
        if self.auto_confirm and self.selected_values:
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        else:
            if not self.auto_confirm:
                self.confirm_button.disabled = len(self.selected_values) == 0
            self.update_select_options()
            await interaction.response.edit_message(view=self)

    async def _prev_page_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can navigate.", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self.update_select_options()
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()

    async def _next_page_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can navigate.", ephemeral=True)
            return
        
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_select_options()
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.defer()

    async def _back_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can go back.", ephemeral=True)
            return
        
        if self.back_callback:
            await self.back_callback(interaction)
        else:
            await interaction.response.defer()

    async def _confirm_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can confirm.", ephemeral=True)
            return
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    async def _cancel_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can cancel.", ephemeral=True)
            return
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

    def get_selected_option_labels(self) -> List[str]:
        """Get the labels of selected options for display purposes"""
        selected_labels = []
        for option in self.all_options:
            if isinstance(option, dict):
                if option.get('value') in self.selected_values:
                    selected_labels.append(option.get('label', 'Unknown'))
            elif str(self.all_options.index(option)) in self.selected_values:
                selected_labels.append(str(option))
        return selected_labels

class SearchableSelectionView(discord.ui.View):
    """Selection view with text-based search for very large lists"""

    def __init__(self,
                 author: discord.Member,
                 options: List[Dict[str, Any]],
                 placeholder: str = "Select an option...",
                 timeout: float = 60.0,
                 auto_confirm: bool = False):
        super().__init__(timeout=timeout)
        self.author = author
        self.all_options = options
        self.filtered_options = options[:20]  # Show first 20 initially
        self.selected_values = []
        self.confirmed: Optional[bool] = None
        self.auto_confirm = auto_confirm
        self.search_query = ""

        # Search input button
        self.search_button = discord.ui.Button(
            label="🔍 Search Categories",
            style=discord.ButtonStyle.secondary,
            row=0
        )
        self.search_button.callback = self._search_callback
        self.add_item(self.search_button)

        # Select menu
        self.select = discord.ui.Select(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=[],
            row=1
        )
        self.select.callback = self._select_callback
        self.add_item(self.select)

        # Confirmation buttons
        if not self.auto_confirm:
            self.confirm_button = discord.ui.Button(
                label="Confirm",
                style=discord.ButtonStyle.green,
                emoji="✅",
                disabled=True,
                row=2
            )
            self.confirm_button.callback = self._confirm_callback
            self.add_item(self.confirm_button)

        self.cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.red,
            emoji="✖",
            row=2
        )
        self.cancel_button.callback = self._cancel_callback
        self.add_item(self.cancel_button)

        self.update_select_options()

    def update_select_options(self):
        """Update select options based on current filter"""
        self.select.options.clear()
        
        for option in self.filtered_options:
            value = option.get('value') if isinstance(option, dict) else str(option)
            is_selected = value in self.selected_values

            if isinstance(option, dict):
                self.select.append_option(discord.SelectOption(
                    label=option.get('label', 'Unknown')[:100],
                    value=value,
                    description=option.get('description', None)[:100] if option.get('description') else None,
                    emoji=option.get('emoji', None),
                    default=is_selected
                ))

        # Update search button label
        if self.search_query:
            self.search_button.label = f"🔍 Search: '{self.search_query}' ({len(self.filtered_options)} found)"
        else:
            self.search_button.label = f"🔍 Search Categories ({len(self.filtered_options)}/{len(self.all_options)} shown)"

    async def _search_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can search.", ephemeral=True)
            return

        # Create a modal for search input
        modal = SearchModal(self)
        await interaction.response.send_modal(modal)

    async def _select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can select.", ephemeral=True)
            return

        self.selected_values = interaction.data['values']
        
        if self.auto_confirm:
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        else:
            self.confirm_button.disabled = len(self.selected_values) == 0
            self.update_select_options()
            await interaction.response.edit_message(view=self)

    async def _confirm_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can confirm.", ephemeral=True)
            return
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    async def _cancel_callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can cancel.", ephemeral=True)
            return
        self.confirmed = False
        await interaction.response.defer()
        self.stop()

    def filter_options(self, query: str):
        """Filter options based on search query"""
        if not query:
            self.filtered_options = self.all_options[:20]
            self.search_query = ""
        else:
            query_lower = query.lower()
            filtered = []
            for option in self.all_options:
                if isinstance(option, dict):
                    label = option.get('label', '').lower()
                    description = option.get('description', '').lower()
                    if query_lower in label or query_lower in description:
                        filtered.append(option)
                else:
                    if query_lower in str(option).lower():
                        filtered.append(option)
            
            self.filtered_options = filtered[:20]  # Limit to 20 results
            self.search_query = query

class SearchModal(discord.ui.Modal, title="Search Categories"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    search_input = discord.ui.TextInput(
        label="Search term",
        placeholder="Type to search categories...",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value.strip()
        self.parent_view.filter_options(query)
        self.parent_view.update_select_options()
        
        embed = discord.Embed(
            title="📂 Select Category",
            description=f"Search results for: `{query}`" if query else "All categories",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=self.parent_view)

class ServerInfoView(discord.ui.View):
    """Interactive view for server info with additional details"""
    
    def __init__(self, author: discord.Member, guild: discord.Guild):
        super().__init__(timeout=300.0)
        self.author = author
        self.guild = guild
    
    @discord.ui.button(label="🎭 View Roles", style=discord.ButtonStyle.secondary, emoji="🎭")
    async def view_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can use this.", ephemeral=True)
            return
        
        roles = [role for role in self.guild.roles if role.name != "@everyone"]
        
        if not roles:
            embed = discord.Embed(
                title="🎭 Server Roles",
                description="No custom roles found",
                color=discord.Color.blue()
            )
        else:
            # Create paginated role list
            role_chunks = [roles[i:i+10] for i in range(0, len(roles), 10)]
            role_pages = []
            
            for i, chunk in enumerate(role_chunks):
                embed = discord.Embed(
                    title=f"🎭 Server Roles ({len(roles)} total)",
                    color=discord.Color.blue()
                )
                
                role_list = []
                for role in reversed(chunk):  # Show highest roles first
                    member_count = len(role.members)
                    role_list.append(f"{role.mention} - `{member_count}` members")
                
                embed.description = "\n".join(role_list)
                embed.set_footer(text=f"Page {i+1}/{len(role_chunks)}")
                role_pages.append(embed)
            
            if len(role_pages) == 1:
                await interaction.response.send_message(embed=role_pages[0], ephemeral=True)
            else:
                # For multiple pages, you could implement a pagination system here
                await interaction.response.send_message(embed=role_pages[0], ephemeral=True)
    
    @discord.ui.button(label="📊 Statistics", style=discord.ButtonStyle.secondary, emoji="📊")
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can use this.", ephemeral=True)
            return
        
        # Detailed statistics
        embed = discord.Embed(
            title="📊 Detailed Server Statistics",
            color=discord.Color.green()
        )
        
        # Member join dates analysis
        now = datetime.now(timezone.utc)
        recent_joins = len([m for m in self.guild.members if m.joined_at and (now - m.joined_at).days <= 7])

        embed.add_field(
            name="📈 Recent Activity",
            value=f"**New members (7 days):** {recent_joins}\n"
                  f"**Average members per day:** {self.guild.member_count // max(1, (now - self.guild.created_at).days)}\n",
            inline=False
        )
        
        # Channel activity (if accessible)
        text_channels = self.guild.text_channels
        embed.add_field(
            name="💬 Channel Information",
            value=f"**Text channels:** {len(text_channels)}\n"
                  f"**Voice channels:** {len(self.guild.voice_channels)}\n"
                  f"**Categories:** {len(self.guild.categories)}\n",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.green, emoji="🔄")
    async def refresh_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can refresh.", ephemeral=True)
            return
        
        # Refresh the server info (re-run the main command logic)
        await interaction.response.defer()
        # You could refresh the embed here with updated data

class WeatherView(discord.ui.View):
    """Interactive view for weather information"""
    
    def __init__(self, author: discord.Member, city: str, weather_data: dict):
        super().__init__(timeout=300.0)
        self.author = author
        self.city = city
        self.weather_data = weather_data
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.green, emoji="🔄")
    async def refresh_weather(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can refresh.", ephemeral=True)
            return
        
        await interaction.response.defer()
        # You could refresh the weather data here
    
    @discord.ui.button(label="📍 Location Info", style=discord.ButtonStyle.secondary, emoji="📍")
    async def location_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Only the author can view this.", ephemeral=True)
            return
        
        coord = self.weather_data.get('coord', {})
        embed = discord.Embed(
            title=f"📍 Location: {self.city}",
            color=discord.Color.blue()
        )
        
        if coord:
            embed.add_field(
                name="Coordinates",
                value=f"**Latitude:** {coord.get('lat', 'N/A')}\n**Longitude:** {coord.get('lon', 'N/A')}",
                inline=False
            )
        
        embed.add_field(
            name="Timezone",
            value=f"**Offset:** UTC{'+' if self.weather_data.get('timezone', 0) >= 0 else ''}{self.weather_data.get('timezone', 0)//3600}h",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

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