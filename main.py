import discord
from discord import app_commands
from discord.ext import commands
import random, json, os, asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATA =====
DATA_FILE = "meenie.json"
PLAYERS = {}  # name -> {rating, position, rarity, spawn_image, info_image, level}
# Example: PLAYERS["Neymar"] = {"rating":99, "position":"LW", "rarity":"Icon", "spawn_image":"https://...", "info_image":"https://...", "level":1}

def load():
    global PLAYERS
    if os.path.exists(DATA_FILE):
        d = json.load(open(DATA_FILE))
        PLAYERS.update(d.get("players", {}))
        return d
    return {"balances":{}, "inventories":{}, "teams":{}, "market":{}, "next_listing":1}

DATA = load()
balances = DATA.get("balances", {})
inventories = DATA.get("inventories", {})  # user_id str -> [card names]
teams = DATA.get("teams", {})  # user_id str -> {position: card}
market = DATA.get("market", {})  # listing_id str -> {seller, card, price}
next_listing = DATA.get("next_listing", 1)

def save():
    json.dump({"players": PLAYERS, "balances": balances, "inventories": inventories, "teams": teams, "market": market, "next_listing": next_listing}, open(DATA_FILE, "w"), indent=2)

def bal(uid): return balances.get(str(uid), 0)
def inv(uid): return inventories.get(str(uid), [])
def display_name(card, owner_id=None):
    p = PLAYERS.get(card, {})
    lvl = p.get("level", 1)
    return f"{card} ({p.get('rating', '?')} OVR | {p.get('position','?')} | Lvl {lvl})"

def find_cards(q):
    q = q.lower()
    return [k for k in PLAYERS if q in k.lower()]

def info_embed(card):
    p = PLAYERS[card]
    e = discord.Embed(title=f"{card} - {p.get('rating')} OVR", description=f"Position: {p.get('position')}\nRarity: {p.get('rarity')}\nLevel: {p.get('level',1)}", color=0xFFD700)
    if p.get("info_image"):
        e.set_image(url=p["info_image"])
    return e

# ===== /IC GROUP =====
ic = app_commands.Group(name="ic", description="Meenie Dex")

# --- INFO ---
@ic.command(name="info", description="Show info pic for a player")
async def ic_info(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    await i.response.send_message(embed=info_embed(m[0]))

# --- DEX / LIST ---
@ic.command(name="list", description="See your cards")
async def ic_list(i: discord.Interaction):
    cards = inv(i.user.id)
    if not cards: return await i.response.send_message("You have no cards! Do `/ic daily` or `/ic buy-pack`", ephemeral=True)
    desc = "\n".join([f"• {display_name(c, i.user.id)}" for c in cards])
    await i.response.send_message(embed=discord.Embed(title=f"{i.user.display_name}'s List", description=desc, color=0x2b2d31))

@ic.command(name="dex", description="See all cards in game")
async def ic_dex(i: discord.Interaction):
    if not PLAYERS: return await i.response.send_message("No cards yet", ephemeral=True)
    desc = "\n".join([f"• {k} - {v.get('rating')} OVR" for k,v in PLAYERS.items()])
    await i.response.send_message(embed=discord.Embed(title="Meenie Dex", description=desc, color=0x2b2d31))

# --- DAILY / SHOP / PACK ---
@ic.command(name="daily", description="Daily coins")
async def ic_daily(i: discord.Interaction):
    balances[str(i.user.id)] = bal(i.user.id) + 500
    save()
    await i.response.send_message(embed=discord.Embed(title="Daily Reward", description=f"+500 coins!\nBalance: {balances[str(i.user.id)]}", color=0x00ff00))

@ic.command(name="shop", description="Shop")
async def ic_shop(i: discord.Interaction):
    await i.response.send_message(embed=discord.Embed(title="🏪 Shop", description="Pack - 1000 coins\n`/ic buy-pack`\n\nBalance: " + str(bal(i.user.id)), color=0xFFD700))

@ic.command(name="buy-pack", description="Buy a pack - 1000 coins")
async def ic_buypack(i: discord.Interaction):
    if bal(i.user.id) < 1000: return await i.response.send_message(f"Need 1000, you have {bal(i.user.id)}", ephemeral=True)
    balances[str(i.user.id)] = bal(i.user.id) - 1000
    card = random.choice(list(PLAYERS.keys())) if PLAYERS else "Neymar"
    inventories.setdefault(str(i.user.id), []).append(card)
    save()
    await i.response.send_message(f"You pulled...", embed=info_embed(card))

# --- TEAM ---
@ic.command(name="team", description="View your team")
async def ic_team_view(i: discord.Interaction):
    t = teams.get(str(i.user.id), {})
    if not t: return await i.response.send_message("No team yet. `/ic team-add player: Neymar`", ephemeral=True)
    desc = "\n".join([f"{pos}: {display_name(c)}" for pos,c in t.items()])
    await i.response.send_message(embed=discord.Embed(title="Your Team", description=desc, color=0x2b2d31))

@ic.command(name="team-add", description="Add player to team")
async def ic_team_add(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own that card", ephemeral=True)
    pos = PLAYERS[card].get("position", "SUB")
    teams.setdefault(str(i.user.id), {})[pos] = card
    save()
    await i.response.send_message(f"✅ Added {card} to team as {pos}")

@ic.command(name="team-auto", description="Auto build best team")
async def ic_team_auto(i: discord.Interaction):
    cards = sorted(inv(i.user.id), key=lambda c: PLAYERS.get(c,{}).get("rating",0), reverse=True)[:11]
    t = {}
    for c in cards: t[PLAYERS[c].get("position","SUB")] = c
    teams[str(i.user.id)] = t
    save()
    await i.response.send_message(f"✅ Auto team built with {len(cards)} players! `/ic team`")

# --- RANKUP ---
@ic.command(name="rankup", description="Rankup a player")
async def ic_rankup(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own it", ephemeral=True)
    PLAYERS[card]["level"] = PLAYERS[card].get("level",1) + 1
    PLAYERS[card]["rating"] = PLAYERS[card].get("rating",80) + 1
    save()
    await i.response.send_message(f"✅ {card} ranked up to Lvl {PLAYERS[card]['level']} - {PLAYERS[card]['rating']} OVR!")

# ===== TRADE - GREEN BUTTON =====
class TradeView(discord.ui.View):
    def __init__(self, sender_id, receiver_id, offered_card, wanted_card):
        super().__init__(timeout=120)
        self.sender_id=sender_id; self.receiver_id=receiver_id; self.offered_card=offered_card; self.wanted_card=wanted_card
    def embed(self):
        return discord.Embed(title="🔄 TRADE OFFER", description=f"<@{self.sender_id}> offers **{display_name(self.offered_card)}**\n\nFor <@{self.receiver_id}>'s **{display_name(self.wanted_card)}**\n\n<@{self.receiver_id}> tap ✅ to accept!", color=0xFFD700)
    @discord.ui.button(label="Accept ✅", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id: return await interaction.response.send_message("Not your trade!", ephemeral=True)
        if self.offered_card not in inv(self.sender_id) or self.wanted_card not in inv(self.receiver_id):
            return await interaction.response.send_message("Someone doesn't have the card anymore!", ephemeral=True)
        inventories[str(self.sender_id)].remove(self.offered_card)
        inventories[str(self.receiver_id)].remove(self.wanted_card)
        inventories[str(self.sender_id)].append(self.wanted_card)
        inventories[str(self.receiver_id)].append(self.offered_card)
        save()
        for c in self.children: c.disabled=True
        await interaction.response.edit_message(embed=discord.Embed(title="✅ TRADE DONE!", description=f"<@{self.sender_id}> got {self.wanted_card}\n<@{self.receiver_id}> got {self.offered_card}", color=0x00ff00), view=self)
        self.stop()
    @discord.ui.button(label="Decline ❌", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id: return await interaction.response.send_message("Not your trade!", ephemeral=True)
        for c in self.children: c.disabled=True
        await interaction.response.edit_message(embed=discord.Embed(title="❌ Trade Declined", color=0xff0000), view=self)
        self.stop()

trade_group = app_commands.Group(name="trade", description="Trade cards")
@trade_group.command(name="send", description="Send a trade - other person taps green to accept")
async def trade_send(i: discord.Interaction, user: discord.Member, offer: str, want: str):
    mo = find_cards(offer); mw = find_cards(want)
    if not mo or not mw: return await i.response.send_message("Card not found", ephemeral=True)
    oc, wc = mo[0], mw[0]
    if oc not in inv(i.user.id): return await i.response.send_message("You don't own the offered card", ephemeral=True)
    if wc not in inv(user.id): return await i.response.send_message("They don't own the wanted card", ephemeral=True)
    view = TradeView(i.user.id, user.id, oc, wc)
    await i.response.send_message(f"{user.mention} you got a trade!", embed=view.embed(), view=view)
ic.add_command(trade_group)

# ===== MARKET - SHOWS AMOUNT =====
class MarketBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        for lid, data in list(market.items())[:25]:
            btn = discord.ui.Button(label=f"{data['card']} - {data['price']} coins", style=discord.ButtonStyle.green, custom_id=f"buy_{lid}")
            btn.callback = self.make_cb(lid)
            self.add_item(btn)
    def make_cb(self, lid):
        async def cb(interaction: discord.Interaction):
            if lid not in market: return await interaction.response.send_message("Listing gone!", ephemeral=True)
            data = market[lid]; buyer = interaction.user.id; seller = int(data['seller']); card = data['card']; price = int(data['price'])
            if buyer == seller: return await interaction.response.send_message("Can't buy your own!", ephemeral=True)
            if bal(buyer) < price: return await interaction.response.send_message(f"Need {price}, you have {bal(buyer)}", ephemeral=True)
            balances[str(buyer)] = bal(buyer) - price
            balances[str(seller)] = bal(seller) + price
            inventories.setdefault(str(buyer), []).append(card)
            del market[lid]; save()
            for c in self.children: c.disabled=True
            await interaction.response.edit_message(content=f"✅ **BOUGHT!** {interaction.user.mention} bought **{display_name(card)}** for **{price} coins** from <@{seller}>\nAuto-added to your list! `/ic list`", embed=None, view=self)
        return cb

market_group = app_commands.Group(name="market", description="Buy / sell cards")
@market_group.command(name="add", description="Put your card in market for sale")
async def market_add(i: discord.Interaction, player: str, price: int):
    global next_listing
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own that card", ephemeral=True)
    if price <= 0: return await i.response.send_message("Price must be 1+", ephemeral=True)
    inventories[str(i.user.id)].remove(card)
    lid = str(next_listing); next_listing += 1
    market[lid] = {"seller": str(i.user.id), "card": card, "price": price}
    save()
    e = discord.Embed(title="🏪 LISTED IN MARKET", description=f"**{display_name(card)}**\nSeller: {i.mention}\nPrice: **{price} coins**\n\nOthers do `/ic market info` to see it, `/ic market buy` to tap & buy!", color=0xFFD700)
    if PLAYERS[card].get("info_image"): e.set_image(url=PLAYERS[card]["info_image"])
    await i.response.send_message(embed=e)

@market_group.command(name="info", description="See players for sale + amount they're selling for")
async def market_info(i: discord.Interaction):
    if not market: return await i.response.send_message("🏪 Market empty! `/ic market add player: Neymar price: 500`", ephemeral=True)
    desc = "**🏪 MARKET - FOR SALE**\n\n"
    for lid, data in market.items():
        desc += f"• **{display_name(data['card'])}** - **{data['price']} coins** - Seller: <@{data['seller']}>\n"
    desc += "\nTo buy: `/ic market buy` then tap the player!"
    await i.response.send_message(embed=discord.Embed(description=desc, color=0x2b2d31))

@market_group.command(name="buy", description="Tap a player to auto-buy, auto-adds to your list")
async def market_buy(i: discord.Interaction):
    if not market: return await i.response.send_message("🏪 Market empty!", ephemeral=True)
    desc = "**🏪 TAP TO BUY**\n\n"
    for lid, data in market.items():
        desc += f"• {data['card']} - {data['price']} coins - Seller: <@{data['seller']}>\n"
    await i.response.send_message(embed=discord.Embed(description=desc, color=0x00ff00), view=MarketBuyView())

@market_group.command(name="remove", description="Take your card back from market")
async def market_remove(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    card = m[0]
    found = None
    for lid, data in list(market.items()):
        if data['seller'] == str(i.user.id) and data['card'] == card: found = lid; break
    if not found: return await i.response.send_message("You don't have that listed", ephemeral=True)
    del market[found]
    inventories.setdefault(str(i.user.id), []).append(card)
    save()
    await i.response.send_message(f"✅ Took {card} back, it's in your list again.")
ic.add_command(market_group)

# ===== ADMIN - NEEDS BOTH PICS =====
@ic.command(name="admin-add-card", description="Admin: add card - NEEDS both spawn pic + info pic")
async def admin_add(i: discord.Interaction, name: str, rating: int, position: str, rarity: str, spawn_image: str, info_image: str):
    if not i.user.guild_permissions.administrator: return await i.response.send_message("Admin only", ephemeral=True)
    if not spawn_image or not info_image: return await i.response.send_message("❌ You MUST give BOTH spawn_image AND info_image!", ephemeral=True)
    PLAYERS[name] = {"rating": rating, "position": position, "rarity": rarity, "spawn_image": spawn_image, "info_image": info_image, "level": 1}
    save()
    await i.response.send_message(f"✅ Added {name}", embed=info_embed(name))

@ic.command(name="admin-spawn", description="Admin: spawn a card - first to type name claims it")
async def admin_spawn(i: discord.Interaction, player: str):
    if not i.user.guild_permissions.administrator: return await i.response.send_message("Admin only", ephemeral=True)
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    card = m[0]
    p = PLAYERS[card]
    e = discord.Embed(title=f"🔥 {card} SPAWNED!", description=f"First to type **{card}** exactly claims it!", color=0xff0000)
    if p.get("spawn_image"): e.set_image(url=p["spawn_image"])
    await i.response.send_message(embed=e)
    def check(msg): return msg.channel.id == i.channel.id and msg.content.strip().lower() == card.lower() and not msg.author.bot
    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        inventories.setdefault(str(msg.author.id), []).append(card)
        save()
        await i.channel.send(f"🎉 {msg.author.mention} claimed **{card}**!")
    except asyncio.TimeoutError:
        await i.channel.send(f"⏰ No one claimed {card}")

bot.tree.add_command(ic)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} - Meenie Dex ready")

bot.run("YOUR_TOKEN_HERE")
