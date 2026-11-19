import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# --- YOUR IMAGES - KEEP YOUR OLD LINKS IF YOU HAVE THEM ---
NEYMAR_URL = "https://i.imgur.com/YOUR_NEYMAR_LINK.png"
RONALDINHO_URL = "https://i.imgur.com/YOUR_RONALDINHO_LINK..."

def get_rarity(rating):
    r = float(rating)
    if r == 0.01:
        return "👑 Mythic - Rarest"
    elif r == 0.02:
        return "💎 Divine"
    elif r == 0.03:
        return "🔥 Immortal"
    elif r == 0.04:
        return "✨ God Tier"
    elif r == 0.05:
        return "🟡 Legendary"
    elif 0.06 <= r <= 0.09:
        return "🟣 Epic"
    elif r == 0.1:
        return "🔵 Ultra Rare"
    elif r == 0.2:
        return "🟢 Super Rare"
    elif r == 0.3:
        return "🟠 Rare"
    elif r == 0.4:
        return "⚪ Uncommon"
    elif r == 0.5:
        return "⚪ Common"
    elif r == 0.6:
        return "⚪ Common +"
    elif r == 0.7:
        return "⚪ Common ++"
    elif r == 0.8:
        return "⚪ Common +++"
    elif r == 0.9:
        return "⚪ Almost Normal"
    elif r == 1.0:
        return "⚪ Normal"
    elif 1.1 <= r <= 1.9:
        return "🗑️ Washed"
    else:
        return "❓ Unknown"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="list", description="See all my cards")
async def list_cards(interaction: discord.Interaction):
    embed = discord.Embed(title="⚽ All My Cards", description="Here are all my cards:", color=0x0099ff)
    embed.add_field(name="🇧🇷 Ronaldinho Ginga", value="/ronaldinho_ginga\nRating: .05 • 🟡 Legendary", inline=False)
    embed.add_field(name="🇧🇷 Neymar 2015 BD", value="/neymar_2015_bd\nRating: .01 • 👑 Mythic - Rarest", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ronaldinho_ginga", description="See Ronaldinho card")
async def ronaldinho_ginga(interaction: discord.Interaction):
    embed = discord.Embed(title="🇧🇷 Ronaldinho Ginga", description="The Magician ✨ Ginga Style", color=0xffcc00)
    embed.add_field(name="Position", value="Attacking Midfielder", inline=False)
    embed.add_field(name="Rating", value=".05", inline=False)
    embed.add_field(name="Rarity", value=get_rarity(".05"), inline=False)
    embed.add_field(name="Year", value="2005", inline=False)
    embed.set_image(url=RONALDINHO_URL)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="neymar_2015_bd", description="See Neymar card")
async def neymar_2015_bd(interaction: discord.Interaction):
    embed = discord.Embed(title="🇧🇷 Neymar 2015 BD", description="Joga Bonito 🔥 2015 Season", color=0x00ff00)
    embed.add_field(name="Position", value="Left Wing", inline=False)
    embed.add_field(name="Rating", value=".01", inline=False)
    embed.add_field(name="Rarity", value=get_rarity(".01"), inline=False)
    embed.add_field(name="Year", value="2015", inline=False)
    embed.set_image(url=NEYMAR_URL)
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
