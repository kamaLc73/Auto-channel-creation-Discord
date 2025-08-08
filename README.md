# Auto-creation channel : Discord Bot

A feature-rich Discord bot designed for academic server management, providing tools for channel organization, guest management, weather information, and interactive user experiences. Built with Python and Discord.py, this bot offers robust functionality with a focus on safety and user-friendly interactions.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
  - [General &amp; Info](#general--info)
  - [Channel &amp; Category Management](#channel--category-management)
  - [Deletion &amp; Cleanup](#deletion--cleanup)
  - [Guest &amp; Role Management](#guest--role-management)
  - [Fun &amp; Auto-responses](#fun--auto-responses)
- [Dependencies](#dependencies)
- [Environment Variables](#environment-variables)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Interactive Channel Management**: Create and delete channels/categories with step-by-step confirmation and pagination for large servers.
- **Guest Role System**: Add or remove guest roles to specific categories with fine-grained permission control.
- **Weather Information**: Fetch real-time weather data for any city using the OpenWeatherMap API.
- **Safe Deletion**: Multiple confirmation layers for destructive actions like message or category deletion.
- **Auto-responses**: Fun and context-aware responses to greetings and specific keywords.
- **Comprehensive Help System**: Interactive help menu with detailed command information and navigation.
- **Server Analytics**: Detailed server statistics including member counts, channel information, and more.
- **Customizable Status**: Change the bot's playing status (admin-only).

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/kamaLc73/Auto-channel-creation-Discord.git
   cd Auto-channel-creation-Discord
   ```
2. **Install Python**:
   Ensure Python 3.8+ is installed. Download from [python.org](https://www.python.org/downloads/).
3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
4. **Set Up Environment Variables**:
   Create a `.env` file in the project root and configure it (see [Environment Variables](#environment-variables)).
5. **Run the Bot**:

   ```bash
   python main.py
   ```

## Configuration

1. **Create a Discord Bot**:

   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new application and add a bot.
   - Enable all **Privileged Gateway Intents** (Presence, Server Members, Message Content).
   - Copy the bot token.
2. **Invite the Bot**:

   - Generate an invite link with appropriate permissions (e.g., Administrator for full functionality).
   - Invite the bot to your server.
3. **Set Up OpenWeatherMap API**:

   - Sign up at [OpenWeatherMap](https://openweathermap.org/) and get an API key.
   - Add the key to your `.env` file.

## Usage

- **Command Prefix**: `!` (case-insensitive).
- **Example**: `!weather_info London` or `!help`.
- **Permissions**:
  - Most commands require specific permissions (e.g., `Manage Channels` for channel creation).
  - Guest management and status changes require `Administrator` permissions.
- **Interactive Views**: Many commands use buttons and dropdowns for user input. Only the command issuer can interact with these views.

## Commands

### General & Info

| Command         | Aliases                 | Description                                | Example                  |
| --------------- | ----------------------- | ------------------------------------------ | ------------------------ |
| `help_`       | `h`, `helpme`       | Interactive help menu with command details | `!h`                   |
| `server_info` | `info`                | Detailed server statistics                 | `!info`                |
| `weather`     | `w`, `weather_info` | Weather data for a city                    | `!w London`            |
| `set_status`  | `status`              | Change bot's playing status (Admin)        | `!status Playing Java` |

### Channel & Category Management

| Command                        | Aliases                  | Description                                      | Example                       |
| ------------------------------ | ------------------------ | ------------------------------------------------ | ----------------------------- |
| `create_channel_in_category` | `channel`, `ch`      | Create a channel in a category                   | `!ch General announcements` |
| `create_channel_interactive` | `channeli`, `chi`    | Interactive channel creation                     | `!chi welcome`              |
| `create_categories`          | `categories`, `cats` | Create multiple categories with privacy settings | `!cats Math Physics`        |
| `modify_category_access`     | `modcat`               | Modify role access for a category                | `!modcat Math add`          |

### Deletion & Cleanup

| Command                 | Aliases                          | Description                                  | Example                       |
| ----------------------- | -------------------------------- | -------------------------------------------- | ----------------------------- |
| `delete_cat_chan`     | `rmcc`                         | Delete channels/categories with confirmation | `!rmcc --cha announcements` |
| `interactive_delete`  | `rmi`                          | Interactive deletion with guidance           | `!rmi`                      |
| `delete_messages`     | `clear`, `clm`, `cls`      | Delete messages with confirmation            | `!clm 50`                   |
| `delete_bot_messages` | `clearb`, `clmb`, `clsbot` | Delete bot messages                          | `!clmb 10`                  |

### Guest & Role Management

| Command                    | Aliases                 | Description                            | Example          |
| -------------------------- | ----------------------- | -------------------------------------- | ---------------- |
| `add_guest_selective`    | `addguest`, `addgu` | Add a role to selected categories      | `!addgu Guest` |
| `remove_guest_selective` | `rmguest`, `rmgu`   | Remove a role from selected categories | `!rmgu Guest`  |

### Fun & Auto-responses

- **Greetings**: Responds to `hello`, `hi`, `salam`, etc., with random replies like "salam w 3lykom".
- **Professor Quotes**: Responds to `arawkan` or `ajihna` with random academic quotes.

## Dependencies

- `discord.py`: For Discord API interactions.
- `python-dotenv`: For environment variable management.
- `requests`: For HTTP requests (e.g., OpenWeatherMap API).
- `asyncio`: For asynchronous operations.

Install with:

```bash
pip install discord.py python-dotenv requests
```

## Environment Variables

Create a `.env` file in the project root with:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token
API_KEY_OPEN_WEATHER=your_openweather_api_key
```

- `DISCORD_BOT_TOKEN`: Your Discord bot token from the Developer Portal.
- `API_KEY_OPEN_WEATHER`: Your OpenWeatherMap API key.

## Logging

- Logs are output to the console with timestamps.
- Format: `YYYY-MM-DD HH:MM:SS - MESSAGE`
- Levels: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- Tracks bot activity, errors, and command usage.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please follow the code style and include tests for new features.

Made by @kamaLc73
