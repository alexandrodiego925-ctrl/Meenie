import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

ADMIN_ID = 1565079902418632704
import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"MEENIE DEX ONLINE as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! Meenie Dex online")

bot.run(TOKEN)


# --- CONFIG ---
PACKS = {
    "gold": {"price": 500, "name": "Gold Pack"},
    "epic": {"price": 1500, "name": "Epic Pack"},
    "mythic": {"price": 4000, "name": "Mythic Pack"},
    "supreme": {"price": 10000, "name": "Supreme Pack"},
}

# Chance to get Unob in that pack
UNOB_CHANCE = {
    "gold": 0.02,
    "epic": 0.03,
    "mythic": 0.04,
    "supreme": 0.05,
}

SELL_PRICES = {
    "gold": 100,
    "epic": 300,
    "mythic": 800,
    "supreme": 2000,
    "unob": 50000,
}

# Your cards - sorted 100 -> lowest automatically
CARDS = [
    {"name": "Neymar Custom BD", "rating": 100, "rarity": "Unob", "version": "Custom BD"},
    {"name": "Ronaldinho_ginga", "rating": 100, "rarity": "Unob", "version": "Ginga"},
    # ADD YOUR OTHER CARDS HERE LIKE THIS:
    # {"name": "Joshua Kimmich", "rating": 86, "rarity": "Uncommon II", "version": "UCL25/26"},
]

# Rarity colors
COLORS = {"Unob": 0xffd700, "Supreme": 0xff00ff, "Mythic": 0xff0000, "Epic": 0xa020f0, "Gold": 0xffff00}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    if not os.path.exists("data.json"):
        return {}
    with open("data.json") as f:
        return json.load(f)
def save_data(d):
    with open("data.json","w") as f:
        json.dump(d,f,indent=2)

def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 1000, "inventory": []}
        save_data(data)
    return data[uid]

def get_id_for_card(card):
    # Simple ID like #MEO - use first letters
    base = "".join([w[0] for w in card["name"].split()]).upper()[:3]
    return f"#{base}{random.randint(100,999)}"

# --- INVENTORY VIEW - MATCHDEX STYLE ---
class InvView(discord.ui.View):
    def __init__(self, user, cards, page=0):
        super().__init__(timeout=120)
        self.user = user
        self.cards = sorted(cards, key=lambda x: x["rating"], reverse=True) # 100 -> lowest
        self.page = page
        self.per_page = 10
        self.total_pages = max(1, (len(self.cards)+self.per_page-1)//self.per_page)
        self.update_dropdown()

    def get_embed(self):
        start = self.page*self.per_page
        end = start+self.per_page
        page_cards = self.cards[start:end]
        desc = ""
        for c in page_cards:
            desc += f"**{c['name']} ({c['version']}) ({c['rating']})**\n{c.get('id','')} | {c['rarity']}\n\n"
        if not desc:
            desc = "No cards yet. Open packs!"
        embed = discord.Embed(
            title=f"{self.user.display_name}'s Card Inventory - Page {self.page+1} of {self.total_pages} - Total Cards: {len(self.cards)}",
            description=desc,
            color=0x2b2d31
        )
        return embed

    def update_dropdown(self):
        # Clear old select
        for child in list(self.children):
            if isinstance(child, discord.ui.Select):
                self.remove_item(child)
        start = self.page*self.per_page
        end = start+self.per_page
        options = []
        for c in self.cards[start:end]:
            options.append(discord.SelectOption(
                label=f"{c['name']} ({c['version']}) ({c['rating']})",
                description=f"{c.get('id','')} | {c['rarity']}",
                value=c['name']
            ))
        if options:
            select = discord.ui.Select(placeholder="Select a card to view...", options=options)
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        name = interaction.data["values"][0]
        card = next(c for c in self.cards if c["name"]==name)
        embed = discord.Embed(
            title=f"{card['name']} ({card['version']}) ({card['rating']})",
            description=f"**ID:** {card.get('id','')}\n**Rarity:** {card['rarity']}\n**Rating:** {card['rating']}\n**Version:** {card['version']}",
            color=COLORS.get(card['rarity'], 0x2b2d31)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        self.update_dropdown()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="...", style=discord.ButtonStyle.secondary)
    async def dots(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

    @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.total_pages-1
        self.update_dropdown()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Skip to page...", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Type page number 1-{self.total_pages} (use /list page:NUMBER)", ephemeral=True)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="list", description="View your inventory - 100 to lowest")
@app_commands.describe(page="Page number")
async def list_cmd(interaction: discord.Interaction, page: int = 1):
    data = load_data()
    user_data = get_user(interaction.user.id)
    # Give user their cards - inventory stores card names
    inv = user_data.get("inventory", [])
    # Build full card objects
    cards = []
    for name in inv:
        found = next((c for c in CARDS if c["name"]==name), None)
        if found:
            cc = found.copy()
            cc["id"] = get_id_for_card(cc)
            cards.append(cc)
    # If empty for testing, show example
    if not cards:
        cards = [{"name":"Neymar Custom BD","rating":100,"rarity":"Unob","version":"Custom BD","id":"#NE1"},
                 {"name":"Ronaldinho_ginga","rating":100,"rarity":"Unob","version":"Ginga","id":"#RO1"}]
    view = InvView(interaction.user, cards, page=max(0, page-1))
    await interaction.response.send_message(embed=view.get_embed(), view=view)

@bot.tree.command(name="balance", description="Check balance")
async def bal(interaction: discord.Interaction):
    u = get_user(interaction.user.id)
    await interaction.response.send_message(f"💰 Balance: **{u['balance']}** coins")

@bot.tree.command(name="open", description="Open a pack")
@app_commands.describe(pack="gold, epic, mythic, supreme")
async def open_pack(interaction: discord.Interaction, pack: str):
    pack = pack.lower()
    if pack not in PACKS:
        await interaction.response.send_message("Packs: gold, epic, mythic, supreme", ephemeral=True)
        return
    data = load_data()
    u = get_user(interaction.user.id)
    price = PACKS[pack]["price"]
    if u["balance"] < price:
        await interaction.response.send_message(f"Not enough! Need {price}, you have {u['balance']}", ephemeral=True)
        return
    u["balance"] -= price
    # Roll Unob?
    if random.random() < UNOB_CHANCE[pack]:
        pulled = random.choice([c for c in CARDS if c["rarity"]=="Unob"])
        rarity_text = "🔥🔥 UNOBTAINABLE 🔥🔥"
    else:
        # Normal pull - random from non-unob, or random rating 88-97
        pool = [c for c in CARDS if c["rarity"]!="Unob"]
        if pool:
            pulled = random.choice(pool)
        else:
            pulled = {"name":"Random Player","rating":random.randint(88,97),"rarity":pack.capitalize(),"version":"Base"}
        rarity_text = pulled["rarity"]
    u["inventory"].append(pulled["name"])
    data[str(interaction.user.id)] = u
    save_data(data)
    embed = discord.Embed(title=f"{PACKS[pack]['name']} Opened!", description=f"**{pulled['name']} ({pulled['version']}) ({pulled['rating']})**\n{rarity_text}", color=COLORS.get(pulled["rarity"], 0x2b2d31))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sell", description="Sell a card")
@app_commands.describe(card="Card name to sell")
async def sell(interaction: discord.Interaction, card: str):
    data = load_data()
    u = get_user(interaction.user.id)
    if card not in u["inventory"]:
        await interaction.response.send_message("You don't own that card!", ephemeral=True)
        return
    found = next((c for c in CARDS if c["name"]==card), None)
    price = SELL_PRICES.get(found["rarity"].lower() if found else "gold", 100)
    u["inventory"].remove(card)
    u["balance"] += price
    data[str(interaction.user.id)] = u
    save_data(data)
    await interaction.response.send_message(f"Sold **{card}** for **{price}** coins! Balance: {u['balance']}")

@bot.tree.command(name="give", description="Admin: give card/coins")
@app_commands.describe(user="User", card="Card name", amount="Coins")
async def give(interaction: discord.Interaction, user: discord.Member, card: str = None, amount: int = 0):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("Only admin!", ephemeral=True)
        return
    data = load_data()
    u = get_user(user.id)
    if card:
        u["inventory"].append(card)
    if amount:
        u["balance"] += amount
    data[str(user.id)] = u
    save_data(data)
    await interaction.response.send_message(f"Gave {user.mention} {card or ''} + {amount} coins")

bot.run(TOKEN)
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
import random

class BetView(discord.ui.View):
    def __init__(self, p1, p2, p1_card):
        super().__init__(timeout=120)
        self.p1 = p1
        self.p2 = p2
        self.p1_card = p1_card
        self.locked = set()
        self.ticked = set()
    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.primary)
    async def lock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.p1.id, self.p2.id]:
            await interaction.response.send_message("Not your bet!", ephemeral=True)
            return
        self.locked.add(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.name} locked 🔒 ({len(self.locked)}/2)")
        if len(self.locked) == 2:
            await interaction.followup.send("Both locked! Now tap ✅ Tick!")
    @discord.ui.button(label="✅ Tick", style=discord.ButtonStyle.success)
    async def tick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.locked:
            await interaction.response.send_message("Tap 🔒 Lock first!", ephemeral=True)
            return
        self.ticked.add(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.name} ticked ✅ ({len(self.ticked)}/2)")
        if len(self.ticked) == 2:
            winner = random.choice([self.p1, self.p2])
            await interaction.followup.send(f"🎲 50/50... **{winner.name} WINS {
bot.run(os.getenv("DISCORD_TOKEN"))
