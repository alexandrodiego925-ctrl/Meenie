import discord, os
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Online as " + str(bot.user))

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

bot.run(os.getenv("DISCORD_TOKEN"))
import discord, random, os, datetime
from discord.ext import commands, tasks
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

teams = {}
balances = {}
inventories = {}
match_history = []
trade_history = []
pack_history = []
bet_history = []
active_trades = {}
active_bets = {}
active_spawn = None
spawn_channel_id = None

FORMATION_BONUS = {"4-3-3": 2, "4-2-3-1": 3, "3-5-2": 2, "4-4-2": 1, "3-4-3": 1, "5-3-2": -1, "4-1-2-1-2": 2, "3-4-2-1": 2}

PACKS = {
    "bronze": {"price": 500, "ovr": (70, 80)},
    "silver": {"price": 1500, "ovr": (80, 88)},
    "gold": {"price": 3500, "ovr": (88, 94)},
    "unob": {"price": 10000, "ovr": (94, 99)},
}

PLAYERS = [
    ("Mbappe", "ST"), ("Haaland", "ST"), ("Bellingham", "CM"), ("Saka", "RW"),
    ("Vini Jr", "LW"), ("Pedri", "CM"), ("Saliba", "CB"), ("Courtois", "GK"),
    ("Yamal", "RW"), ("Musiala", "CAM"), ("Valverde", "CM"), ("Rudiger", "CB"),
    ("Kane", "ST"), ("Salah", "RW"), ("De Bruyne", "CAM"), ("Van Dijk", "CB"),
    ("Ronaldo", "ST"), ("Messi", "RW"), ("Lewandowski", "ST"),
]

SPAWN_PLAYERS = PLAYERS + [("Neymar Junior", "LW")]

def get_ovr(players):
    return sum(p["ovr"] for p in players) // len(players) if players else 0

def get_balance(uid):
    return balances.get(uid, 1000)

def calc_poss(t1, t2):
    ovr1 = get_ovr(t1["players"])
    ovr2 = get_ovr(t2["players"])
    diff = max(-8, min(8, ovr1 - ovr2))
    f1 = FORMATION_BONUS.get(t1.get("formation", "4-3-3"), 0)
    f2 = FORMATION_BONUS.get(t2.get("formation", "4-3-3"), 0)
    u1 = 1 if any(p.get("unob") for p in t1["players"]) else 0
    u2 = 1 if any(p.get("unob") for p in t2["players"]) else 0
    base = 50 + diff + (f1 - f2) + (u1 - u2) + random.randint(-4, 4)
    p1 = max(32, min(68, base))
    return p1, 100 - p1, ovr1, ovr2

def log_history(lst, text):
    lst.append(datetime.datetime.now().strftime("%m-%d %H:%M") + " - " + text)
    if len(lst) > 50:
        lst.pop(0)

def unob_tag(card):
    if card.get("unob"):
        return " UNOB"
    return ""

@bot.event
async def on_ready():
    await bot.tree.sync()
    spawn_loop.start()
    print("Online as " + str(bot.user))

@tasks.loop(minutes=15)
async def spawn_loop():
    global active_spawn, spawn_channel_id
    if spawn_channel_id is None or active_spawn is not None:
        return
    try:
        ch = bot.get_channel(spawn_channel_id)
        if not ch:
            return
        if random.random() < 0.25:
            name = "Neymar Junior"
            pos = "LW"
            ovr = 100
            is_unob = True
        else:
            name, pos = random.choice(PLAYERS)
            ovr = random.randint(88, 98)
            is_unob = random.random() < 0.15
        active_spawn = {"name": name, "pos": pos, "ovr": ovr, "unob": is_unob}
        if name == "Neymar Junior":
            await ch.send("**NEYMAR JUNIOR SPAWN!**\nLW - Neymar Junior - 100 - UNOB\nFirst to type !claim gets him!")
            try:
                await ch.send(file=discord.File("neymar_spawn.png"))
            except:
                await ch.send("Pic 1 missing - upload neymar_spawn.png")
        else:
            tag = "UNOB SPAWN!" if is_unob else "RARE SPAWN!"
            await ch.send("**" + tag + "**\n" + pos + " - " + name + " - " + str(ovr) + "\nFirst to type !claim gets it!")
    except Exception as e:
        print(e)

@bot.tree.command(name="set-spawn-channel", description="Set where spawns drop")
async def set_spawn(interaction: discord.Interaction, channel: discord.TextChannel):
    global spawn_channel_id
    spawn_channel_id = channel.id
    await interaction.response.send_message("Spawns will now drop in " + channel.mention + " every ~15 mins!")

@bot.tree.command(name="force-spawn", description="Force a spawn now")
async def force_spawn(interaction: discord.Interaction):
    global active_spawn
    if active_spawn:
        await interaction.response.send_message("A spawn is already active! Claim it first.")
        return
    if random.random() < 0.5:
        name = "Neymar Junior"
        pos = "LW"
        ovr = 100
        is_unob = True
    else:
        name, pos = random.choice(PLAYERS)
        ovr = random.randint(88, 98)
        is_unob = random.random() < 0.2
    active_spawn = {"name": name, "pos": pos, "ovr": ovr, "unob": is_unob}
    if name == "Neymar Junior":
        await interaction.response.send_message("**NEYMAR JUNIOR SPAWN!**\nLW - Neymar Junior - 100 - UNOB\nType !claim to claim!")
        try:
            await interaction.followup.send(file=discord.File("neymar_spawn.png"))
        except:
            pass
    else:
        await interaction.response.send_message("**SPAWN!**\n" + pos + " - " + name + " - " + str(ovr) + "\nType !claim to claim!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global active_spawn
    if message.content.lower() == "!claim" and active_spawn:
        card = active_spawn.copy()
        active_spawn = None
        uid = str(message.author.id)
        if uid not in inventories:
            inventories[uid] = []
        inventories[uid].append(card)
        tag = unob_tag(card)
        await message.channel.send("🎉 " + message.author.mention + " claimed **" + card["pos"] + " - " + card["name"] + " - " + str(card["ovr"]) + "**" + tag + "!")
        if card["name"] == "Neymar Junior":
            await message.channel.send("Do /info to see his full card!")
        log_history(pack_history, message.author.display_name + " claimed spawn " + card["name"] + " " + str(card["ovr"]))
    await bot.process_commands(message)

@bot.tree.command(name="info", description="Info for Neymar Junior - shows Pic 2")
async def info_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("**NEYMAR JUNIOR - 100 - LW**\nCODE NAME: El MAGO\nPure Brazilian sauce - flicks, nutmegs, rainbows at full sprint.\nUNOB - SPAWN ONLY - Cannot get from packs")
    try:
        await interaction.followup.send(file=discord.File("neymar_info.png"))
    except:
        await interaction.followup.send("Pic 2 missing - upload neymar_info.png to GitHub!")

@bot.tree.command(name="team", description="Show your team")
async def team_cmd(interaction: discord.Interaction):
    t = teams.get(str(interaction.user.id), {"players": [], "formation": "4-3-3"})
    if not t["players"]:
        await interaction.response.send_message("No team yet. Buy packs / claim spawns!")
        return
    ovr = get_ovr(t["players"])
    msg = "**" + interaction.user.display_name + " | " + t["formation"] + " | OVR " + str(ovr) + "**\n\n"
    for p in t["players"]:
        msg += p["pos"] + " - " + p["name"] + " - " + str(p["ovr"]) + "\n"
    await interaction.response.send_message(msg)

@bot.tree.command(name="team-auto", description="Auto pick best 11")
async def team_auto(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    inv = inventories.get(uid, [])
    if not inv:
        await interaction.response.send_message("Empty inventory. /buy-pack or claim spawn!")
        return
    best = sorted(inv, key=lambda x: x["ovr"], reverse=True)[:11]
    if uid not in teams:
        teams[uid] = {"players": best, "formation": "4-3-3"}
    else:
        teams[uid]["players"] = best
    await interaction.response.send_message("Auto team set! OVR: " + str(get_ovr(best)))

@bot.tree.command(name="team-formation", description="Change formation")
@app_commands.describe(formation="e.g. 4-3-3")
async def team_formation(interaction: discord.Interaction, formation: str):
    if formation not in FORMATION_BONUS:
        await interaction.response.send_message("Use: " + ", ".join(FORMATION_BONUS.keys()))
        return
    uid = str(interaction.user.id)
    if uid not in teams:
        teams[uid] = {"players": [], "formation": formation}
    else:
        teams[uid]["formation"] = formation
    await interaction.response.send_message("Formation -> **" + formation + "**")

@bot.tree.command(name="balance", description="Check coins")
async def balance(interaction: discord.Interaction):
    await interaction.response.send_message("Balance: **" + str(get_balance(str(interaction.user.id))) + " coins**")

@bot.tree.command(name="daily", description="Claim daily coins")
async def daily(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    reward = random.randint(800, 1500)
    balances[uid] = get_balance(uid) + reward
    await interaction.response.send_message("+" + str(reward) + " coins! Balance: " + str(balances[uid]))

@bot.tree.command(name="inventory", description="See your cards")
async def inventory(interaction: discord.Interaction):
    inv = inventories.get(str(interaction.user.id), [])
    if not inv:
        await interaction.response.send_message("Empty. Buy pack or claim spawn!")
        return
    msg = "**" + interaction.user.display_name + " Inventory (" + str(len(inv)) + ")**\n\n"
    for i, p in enumerate(inv):
        msg += str(i + 1) + ". " + p["pos"] + " - " + p["name"] + " - " + str(p["ovr"]) + unob_tag(p) + "\n"
    await interaction.response.send_message(msg)

@bot.tree.command(name="sell", description="Sell a card")
@app_commands.describe(card_number="From /inventory")
async def sell(interaction: discord.Interaction, card_number: int):
    uid = str(interaction.user.id)
    inv = inventories.get(uid, [])
    if card_number < 1 or card_number > len(inv):
        await interaction.response.send_message("Invalid number.")
        return
    card = inv.pop(card_number - 1)
    price = card["ovr"] * 20
    balances[uid] = get_balance(uid) + price
    await interaction.response.send_message("Sold " + card["name"] + " for " + str(price) + " coins! Balance: " + str(balances[uid]))

@bot.tree.command(name="pack", description="Pack shop")
async def pack_shop(interaction: discord.Interaction):
    msg = "**PACK SHOP**\n\n"
    for n, d in PACKS.items():
        msg += "**" + n.upper() + "** - " + str(d["price"]) + " coins - OVR " + str(d["ovr"][0]) + "-" + str(d["ovr"][1]) + "\n"
    await interaction.response.send_message(msg)

@bot.tree.command(name="buy-pack", description="Buy a pack")
@app_commands.describe(pack_name="bronze, silver, gold, unob")
async def buy_pack(interaction: discord.Interaction, pack_name: str):
    pack_name = pack_name.lower()
    if pack_name not in PACKS:
        await interaction.response.send_message("Packs: bronze, silver, gold, unob")
        return
    uid = str(interaction.user.id)
    price = PACKS[pack_name]["price"]
    bal = get_balance(uid)
    if bal < price:
        await interaction.response.send_message("Need " + str(price) + ", you have " + str(bal) + ". Do /daily")
        return
    balances[uid] = bal - price
    lo, hi = PACKS[pack_name]["ovr"]
    pulled = []
    for _ in range(3):
        name, pos = random.choice(PLAYERS)
        ovr = random.randint(lo, hi)
        is_unob = (pack_name == "unob")
        card = {"name": name, "pos": pos, "ovr": ovr, "unob": is_unob}
        pulled.append(card)
        if uid not in inventories:
            inventories[uid] = []
        inventories[uid].append(card)
    msg = "**" + pack_name.upper() + " PACK!**\n\n"
    for c in pulled:
        msg += c["pos"] + " - " + c["name"] + " - " + str(c["ovr"]) + unob_tag(c) + "\n"
    msg += "\nBalance: " + str
