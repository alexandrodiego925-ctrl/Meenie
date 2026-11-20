from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- DATA (in-memory) ---
balances = {}  # user_id -> coins
inventory = {}  # user_id -> list of cards
last_daily = {}
last_weekly = {}

# --- CARDS ---
# name, rating, rarity, year
CARDS = {
    "Gold": [
        {"name": "Bukayo Saka", "rating": 88, "rarity": "Gold", "year": 2024},
        {"name": "Jamal Musiala", "rating": 89, "rarity": "Gold", "year": 2024},
        {"name": "Pedri", "rating": 90, "rarity": "Gold", "year": 2024},
        {"name": "Phil Foden", "rating": 91, "rarity": "Gold", "year": 2024},
        {"name": "Lamine Yamal", "rating": 92, "rarity": "Gold", "year": 2024},
    ],
    "Epic": [
        {"name": "Neymar Jr", "rating": 92, "rarity": "Epic", "year": 2015},
        {"name": "Kevin De Bruyne", "rating": 93, "rarity": "Epic", "year": 2023},
        {"name": "Mohamed Salah", "rating": 94, "rarity": "Epic", "year": 2024},
        {"name": "Vinicius Jr", "rating": 94, "rarity": "Epic", "year": 2024},
    ],
    "Mythic": [
        {"name": "Ronaldinho Gaúcho", "rating": 95, "rarity": "Mythic", "year": 2005},
        {"name": "Zinedine Zidane", "rating": 96, "rarity": "Mythic", "year": 2002},
        {"name": "Ronaldo Nazario", "rating": 97, "rarity": "Mythic", "year": 2002},
    ],
    "Supreme": [
        {"name": "Lionel Messi", "rating": 98, "rarity": "Supreme", "year": 2022},
        {"name": "Cristiano Ronaldo", "rating": 99, "rarity": "Supreme", "year": 2018},
        {"name": "Pele", "rating": 100, "rarity": "Supreme", "year": 1970},
    ]
}

PACKS = {
    "gold": {"name": "Gold Pack", "price": 1000, "range": "88 - 92", "key": "Gold"},
    "epic": {"name": "Epic Pack", "price": 2000, "range": "92 - 94", "key": "Epic"},
    "mythic": {"name": "Mythic Pack", "price": 6000, "range": "95 - 97", "key": "Mythic"},
    "supreme": {"name": "Supreme Pack", "price": 12000, "range": "97 - 100", "key": "Supreme"},
}

def get_balance(uid):
    return balances.get(uid, 0)

def make_card_embed(card, caught_date=None):
    embed = discord.Embed(title=f"{card['name']}", color=discord.Color.gold())
    embed.add_field(name="Rarity", value=card['rarity'], inline=True)
    embed.add_field(name="Rating", value=str(card['rating']), inline=True)
    embed.add_field(name="Year", value=str(card['year']), inline=True)
    if caught_date:
        embed.add_field(name="Caught", value=caught_date, inline=False)
    return embed

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="list", description="See all cards in the game")
async def list_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📋 All Cards", color=discord.Color.blue())
    for pack_key, cards in CARDS.items():
        text = "\n".join([f"{c['name']} - {c['rating']} - {c['year']}" for c in cards])
        embed.add_field(name=f"{pack_key} Pack", value=text, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="balance", description="Check your coins")
async def balance_cmd(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(f"💰 {interaction.user.mention} you have **{bal} coins**")

@bot.tree.command(name="daily", description="Claim daily coins (10-100)")
async def daily_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    now = datetime.now()
    if uid in last_daily and now - last_daily[uid] < timedelta(hours=24):
        left = timedelta(hours=24) - (now - last_daily[uid])
        hours = int(left.total_seconds() // 3600)
        await interaction.response.send_message(f"⏰ You already claimed! Come back in {hours}h")
        return
    amount = random.randint(10, 100)
    balances[uid] = get_balance(uid) + amount
    last_daily[uid] = now
    await interaction.response.send_message(f"🎁 Daily claimed! You got **{amount} coins**! Balance: **{balances[uid]}**")

@bot.tree.command(name="weekly", description="Claim weekly coins (100-1000)")
async def weekly_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    now = datetime.now()
    if uid in last_weekly and now - last_weekly[uid] < timedelta(days=7):
        left = timedelta(days=7) - (now - last_weekly[uid])
        days = left.days
        await interaction.response.send_message(f"⏰ You already claimed! Come back in {days} days")
        return
    amount = random.randint(100, 1000)
    balances[uid] = get_balance(uid) + amount
    last_weekly[uid] = now
    await interaction.response.send_message(f"🎁 Weekly claimed! You got **{amount} coins**! Balance: **{balances[uid]}**")

@bot.tree.command(name="shop", description="Show the shop")
@app_commands.describe(info="Type 'info' to see shop")
async def shop_cmd(interaction: discord.Interaction, info: str = "info"):
    embed = discord.Embed(title="🛒 Meenie Shop - Only Packs", color=discord.Color.green())
    embed.description = "Unlimited stock!"
    for p in PACKS.values():
        embed.add_field(name=f"{p['name']} - {p['price']} coins", value=f"Rating: {p['range']}", inline=False)
    embed.set_footer(text="Buy with /pack buy [pack name]")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pack", description="Buy a pack")
@app_commands.describe(action="Type 'buy'", pack_name="gold / epic / mythic / supreme")
async def pack_cmd(interaction: discord.Interaction, action: str, pack_name: str):
    if action.lower() != "buy":
        await interaction.response.send_message("Use `/pack buy [pack]` - e.g. `/pack buy gold`")
        return
    key = pack_name.lower()
    if key not in PACKS:
        await interaction.response.send_message("Pack not found! Use: gold, epic, mythic, supreme")
        return
    pack = PACKS[key]
    uid = interaction.user.id
    bal = get_balance(uid)
    if bal < pack["price"]:
        await interaction.response.send_message(f"❌ You need {pack['price']} coins, you have {bal}. Do /daily!")
        return
    balances[uid] = bal - pack["price"]
    card = random.choice(CARDS[pack["key"]])
    caught = datetime.now().strftime("%d %b %Y")
    if uid not in inventory:
        inventory[uid] = []
    inventory[uid].append({**card, "caught": caught})
    embed = make_card_embed(card, caught)
    embed.title = f"🎉 You pulled {card['name']}!"
    await interaction.response.send_message(f"You bought {pack['name']} for {pack['price']} coins! Balance: {balances[uid]}", embed=embed)

@bot.tree.command(name="inventory", description="See your cards")
async def inventory_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    cards = inventory.get(uid, [])
    if not cards:
        await interaction.response.send_message("You have no cards yet! Buy a pack with /pack buy gold")
        return
    embed = discord.Embed(title=f"{interaction.user.name}'s Cards", color=discord.Color.purple())
    for c in cards:
        embed.add_field(name=f"{c['name']} - {c['rating']}", value=f"{c['rarity']} | Year: {c['year']} | Caught: {c['caught']}", inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
