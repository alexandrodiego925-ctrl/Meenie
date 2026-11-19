import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

RONALDINHO_URL = "https://i.imgur.com/YourRonaldinhoLink.png"
NEYMAR_URL = "https://i.imgur.com/YourNeymarLink.png"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="list", description="See all my cards")
async def list_cards(interaction: discord.Interaction):
    embed = discord.Embed(title="⚽ All My Cards", description="Here are all my cards:", color=0x00ff00)
    embed.add_field(name="🇧🇷 Ronaldinho Ginga", value="`/ronaldinho_ginga`", inline=False)
    embed.add_field(name="🇧🇷 Neymar 2015 BD", value="`/neymar_2015_bd`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="See info for all cards")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(title="ℹ️ My Other Cards - Info", color=0x0099ff)
    embed.add_field(name="🇧🇷 Ronaldinho Ginga", value="Position: Attacking Midfielder\nRating: 0.05\nStyle: Ginga ✨", inline=False)
    embed.add_field(name="🇧🇷 Neymar 2015 BD", value="Position: Left Wing\nRating: 0.01\nYear: 2015 - Joga Bonito 🔥", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ronaldinho_ginga", description="
