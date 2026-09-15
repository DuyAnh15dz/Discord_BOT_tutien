import discord
from discord.ext import commands
import asyncio

from config import DISCORD_TOKEN
from database.connection import init_pool, close_pool


# ===== Setup bot =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


# ===== Events =====
@bot.event
async def on_ready():
    print(f'[BOT] Logged in as {bot.user}')
    print(f'[BOT] Serving {len(bot.guilds)} guild(s)')
    
    try:
        # Sync tất cả command
        synced = await bot.tree.sync()
        print(f'[BOT] Synced {len(synced)} slash command(s)')
        
        # In danh sách
        for cmd in bot.tree.get_commands():
            print(f'  - /{cmd.name}')
    except Exception as e:
        print(f'[BOT] Sync failed: {e}')


# ===== Load cogs =====
async def load_cogs():
    cogs = [
        'cogs.onboarding',
        'cogs.tuluyen',
        'cogs.admin',
        'cogs.nghe',
        'cogs.linhcan',
        'cogs.dotpha',
        'cogs.lichluyen',
        'cogs.stats',
        'cogs.tui_do',
        'cogs.shop',
        'cogs.study',
        'cogs.congphap',
        'cogs.daocu',
        'cogs.dan_duoc',
        'cogs.dan_phuong',
        'cogs.luyen_dan',
        'cogs.bxh',
        'cogs.bxh_task',
        'cogs.daily',
        'cogs.dotpha_linhcan',
        'cogs.help',
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'[BOT] Loaded {cog}')
        except Exception as e:
            print(f'[BOT] Failed to load {cog}: {e}')


# ===== Main =====
async def main():
    # 1. Init DB pool
    init_pool()

    # 2. Start bot
    async with bot:
        await load_cogs()
        try:
            await bot.start(DISCORD_TOKEN)
        finally:
            close_pool()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('[BOT] Shutdown by user')