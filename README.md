# Auto Channel Creation Discord Bot

## 📌 Overview
This is a Discord bot that automates channel and category creation, provides moderation tools, and includes various fun commands. The bot is built using `discord.py`, and it features logging, server information retrieval, and interactive message handling.

## 📂 Project Structure
```
kamalc73-auto-channel-creation-discord/
├── build.bat
├── main.py
├── deployment/
└── other stuff/
    └── with_selenium.py
```

### Key Files:
- **`main.py`**: Core bot functionality and command definitions.
- **`build.bat`**: Script for packaging the bot using `pyinstaller`.
- **`with_selenium.py`**: Selenium script for automating category and channel creation via Discord Web.
- **`deployment/`**: (Optional) Deployment-related configurations.

## 🚀 Features
- **Category & Channel Management**: Create, delete, and manage categories and channels.
- **Automated Message Responses**: Custom responses for specific messages.
- **Server Info Command**: Displays server statistics.
- **Weather Command**: Retrieves weather data using OpenWeather API.
- **Moderation Tools**: Clear messages, manage permissions, and more.
- **Custom Views**: Interactive UI elements for role selection and privacy settings.

## 🛠️ Setup & Installation
### Prerequisites
- Python 3.8+
- `pip install -r requirements.txt`
- Create a `.env` file with:
  ```
  DISCORD_BOT_TOKEN=your-bot-token
  API_KEY_OPEN_WEATHER=your-api-key
  ```

### Running the Bot
```bash
python main.py
```

### Packaging the Bot
```bash
build.bat
```
This creates an executable using `pyinstaller`.

## 📜 Commands
### General Commands
| Command | Description |
|---------|-------------|
| `!info` | Show server statistics |
| `!weather <city>` | Get weather details |
| `!status <text>` | Change bot status |

### Moderation Commands
| Command | Description |
|---------|-------------|
| `!channel <category> <name>` | Create a channel in a category |
| `!categories <names>` | Create multiple categories |
| `!rmcc [--cat] [--cha]` | Delete categories/channels |
| `!clear <number>` | Delete messages |

### Fun & Interactive Features
- Auto-response to `hello`, `salam`, `arawkan`, etc.
- Custom UI for category privacy settings and role-based access.

## ✨ Contributing
Feel free to open issues and submit pull requests to improve the bot!

## 📬 Contact
For any inquiries, reach out to [GitHub Issues](https://github.com/kamaLc73/Auto-channel-creation-Discord/issues).

