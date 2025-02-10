@echo off
pyinstaller --onefile ^
    --hidden-import=dotenv ^
    --hidden-import=discord.ext.commands ^
    --hidden-import=logging ^
    --add-data ".env;." ^
    --icon=bot.ico ^
    main.py