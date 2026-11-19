import discordimport discord
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
from discord.ext import commands
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

NEYMAR_URL = "https://i.imgur.com/YOUR_NEYMAR_LINK.png"
RONALDINHO_URL = "https://i.imgur.com/YOUR_RONALDINHO_LINK.png"

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

CARDS = {
    "neymar": {
        "title": "🇧🇷 Neymar Jr - 2015 BD",
        "desc": "Joga Bonito 🔥 2015 Season",
        "position": "Left Wing",
        "rating": ".01",
        "year": "2015",
        "color": 0x00ff00,
        "image": NEYMAR_URL,
    },
    "ronaldinho": {
        "title": "🇧🇷 Ronaldinho Ginga",
        "desc": "Ginga ✨",
        "position": "Attacking Midfielder",
        "rating": ".05",
        "year": "2005",
        "color": 0xffcc00,
        "image": RONALDINHO_URL,
    }
}

def make_embed(key):
    card = CARDS[key]
    embed = discord.Embed(title=card["title"], description=card["desc"], color=card["color"])
    embed.add_field(name="Position", value=card["position"], inline=False)
    embed.add_field(name="Rating", value=card["rating"], inline=False)
    embed.add_field(name="Rarity", value=get_rarity(card["rating"]), inline=False)
    embed.add_field(name="Year", value=card["year"], inline=False)
    embed.set_image(url=card["image"])
    return embed

class CardSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Neymar Jr (2015 BD)", description="Rating: .01 • 👑 Mythic - Rarest", value="neymar", emoji="👑"),
            discord.SelectOption(label="Ronaldinho Ginga", description="Rating: .05 • 🟡 Legendary", value="ronaldinho", emoji="🟡"),
        ]
        super().__init__(placeholder="Make a selection", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=make_embed(self.values[0]), ephemeral=True)

class CardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(CardSelect())

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Closed.", view=None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="list", description="See all cards")
async def list_cards(interaction: discord.Interaction):
    await interaction.response.send_message("Select a card:", view=CardView())

@bot.tree.command(name="neymar_2015_bd", description="See Neymar card")
async def neymar(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_embed("neymar"))

@bot.tree.command(name="ronaldinho_ginga", description="See Ronaldinho card")
async def ronaldinho(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_embed("ronaldinho"))

bot.run(os.getenv("DISCORD_TOKEN"))
