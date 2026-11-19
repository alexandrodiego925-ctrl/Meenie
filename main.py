import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

NEYMAR_URL = "https://cdn.discordapp.com/attachments/1572680544460738681/1572711163999817738/Picsart_26-11-18_20-04-27-377.png"
RONALDINHO_URL = "https://cdn.discordapp.com/attachments/1572680544460738681/1572713625741692958/Picsart_26-11-18_22-41-52-419.png"

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
    embed = discord.Embed(title="⚽ All My Cards", description="Here are all my cards:", color=0x0099FF)
    embed.add_field(name="🇧🇷 Ronaldinho Ginga", value="`/ronaldinho_ginga`", inline=False)
    embed.add_field(name="🇧🇷 Neymar 2015 BD", value="`/neymar_2015_bd`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="info", description="See my other cards info")
async def info_cards(interaction: discord.Interaction):
    embed = discord.Embed(title="ℹ️ My Other Cards - Info", description="Details for all my cards:", color=0xFFD700)
    embed.add_field(name="🇧🇷 Ronaldinho Ginga", value="Position: Attacking Midfielder\nRating: 94\nStyle: Ginga ✨", inline=False)
    embed.add_field(name="🇧🇷 Neymar 2015 BD", value="Position: Left Wing\nRating: 92\nYear: 2015 - Joga Bonito 🔥", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ronaldinho_ginga", description="Show Ronaldinho Ginga card")
async def ronaldinho_ginga(interaction: discord.Interaction):
    embed = discord.Embed(title="🇧🇷 Ronaldinho Ginga", description="The Magician ✨ Ginga Style", color=0xFFD700)
    embed.set_image(url=RONALDINHO_URL)
    embed.add_field(name="Position", value="Attacking Midfielder", inline=True)
    embed.add_field(name="Rating", value="94", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="neymar_2015_bd", description="Show Neymar 2015 BD card")
async def neymar_2015_bd(interaction: discord.Interaction):
    embed = discord.Embed(title="🇧🇷 Neymar Jr - 2015 BD", description="Joga Bonito 🔥 2015 Season", color=0x00FF00)
    embed.set_image(url=NEYMAR_URL)
    embed.add_field(name="Position", value="Left Wing", inline=True)
    embed.add_field(name="Rating", value="92", inline=True)
    embed.add_field(name="Year", value="2015", inline=True)
    await interaction.response.send_message(embed=embed)

bot.run(os.environ.get("TOKEN"))
