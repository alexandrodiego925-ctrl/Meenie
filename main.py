import discord, random, io, os
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from collections import Counter

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 123456789 # <-- PUT YOUR DISCORD ID HERE

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATA =====
PLAYERS = {}
balances = {}
rank_points = {}
ranks = {}
inventories = {}
teams = {}
trades = {} # target_id -> {from_id, card}

PACKS = {
    "gold": {"price": 1000, "ovr": (88, 92), "unob": False},
    "epic": {"price": 2000, "ovr": (92, 94), "unob": False},
    "mythic": {"price": 6000, "ovr": (95, 97), "unob": False},
    "supreme": {"price": 12000, "ovr": (97, 100), "unob": False},
    "unob": {"price": 15000, "ovr": (96, 100), "unob": True},
}
RANK_COST = {1: 10, 2: 20, 3: 30}

def adm(uid): return uid == OWNER_ID
def bal(uid): return balances.get(uid, 1000)
def inv(uid): return inventories.get(uid, [])
def team(uid): return teams.setdefault(uid, {"players": [], "formation": "4-3-3", "captain": None})
def get_rank(uid, card): return ranks.get(uid, {}).get(card, 0)
def get_points(uid): return rank_points.get(uid, 0)

# RANKUP: ANY RATING CAN GO ON - NO CAP - MAX +3
def get_eff(uid, card):
    base = PLAYERS.get(card, {"rating": 80})["rating"]
    return base + get_rank(uid, card)

def find_cards(q):
    q = q.lower().strip()
    out = []
    for name, p in PLAYERS.items():
        if q == name.lower() or q == p.get("code_name","").lower() or q in name.lower():
            out.append(name)
    return out

def display_name(name, uid=None):
    p = PLAYERS.get(name, {"rating": 80})
    if uid is not None:
        eff = get_eff(uid, name); r = get_rank(uid, name)
        stars = f" {'⭐'*r}" if r > 0 else ""
        return f"{name} ({eff} OVR){stars}"
    return f"{name} ({p['rating']} OVR)"

def team_ovr(uid):
    t = team(uid)
    if not t["players"]: return 0
    return sum(get_eff(uid, x) for x in t["players"]) // len(t["players"])

def build_lineup_image(uid, t):
    W,H = 1000, 1400
    img = Image.new("RGB", (W,H), (0,200,90))
    d = ImageDraw.Draw(img)
    try:
        ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
        fn = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    except: ft = fn = fs = ImageFont.load_default()
    d.text((W//2, 50), "LINE UP", fill="white", font=ft, anchor="mm")
    d.text((W//2, 115), f"4-3-3 • OVR {team_ovr(uid)} • {len(t['players'])}/11", fill="white", font=fs, anchor="mm")
    x0,y0,x1,y1 = 60,170,W-60,H-120
    d.rectangle([x0,y0,x1,y1], outline="white", width=4)
    d.line([(W//2,y0),(W//2,y1)], fill="white", width=3)
    d.ellipse([W//2-90,(y0+y1)//2-90,W//2+90,(y0+y1)//2+90], outline="white", width=3)
    pos = [(0.22,0.22),(0.22,0.5),(0.22,0.78),(0.48,0.22),(0.48,0.5),(0.48,0.78),(0.73,0.15),(0.73,0.38),(0.73,0.62),(0.73,0.85),(0.90,0.5)]
    for idx, (yf,xf) in enumerate(pos):
        x = int(x0+(x1-x0)*xf); y = int(y0+(y1-y0)*yf); r=48
        name = t["players"][idx] if idx < len(t["players"]) else "EMPTY"
        d.ellipse([x-r-4,y-r-4,x+r+4,y+r+4], fill="white")
        avatar_done = False
        if name != "EMPTY":
            url = PLAYERS.get(name, {}).get("spawn_image","")
            if url:
                try:
                    resp = requests.get(url, timeout=5)
                    sp = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    w,h = sp.size
                    face = sp.crop((int(w*0.25), int(h*0.02), int(w*0.75), int(h*0.35)))
                    av = ImageOps.fit(face, (r*2,r*2), Image.LANCZOS)
                    mask = Image.new("L", (r*2,r*2), 0)
                    ImageDraw.Draw(mask).ellipse([0,0,r*2,r*2], fill=255)
                    img.paste(av, (x-r,y-r), mask); avatar_done=True
                except: pass
        if not avatar_done:
            if name == "EMPTY":
                d.ellipse([x-r,y-r,x+r,y+r], fill=(0,160,70)); d.text((x,y), "+", fill="white", font=ft, anchor="mm")
            else:
                d.ellipse([x-r,y-r,x+r,y+r], fill=(0,150,80))
                d.ellipse([x-13,y-26,x+13,y-2], fill="white"); d.arc([x-26,y-6,x+26,y+34], start=180, end=360, fill="white", width=6)
        label = f"{display_name(name, uid)}" if name!="EMPTY" else "EMPTY"
        d.text((x, y+r+28), label, fill="white", font=fn, anchor="mm", stroke_width=2, stroke_fill=(0,120,50))
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0); return buf

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try: await bot.tree.sync(); print("Synced")
    except Exception as e: print(e)

@bot.tree.command(name="daily", description="Daily coins - 0 to 100")
async def daily(i: discord.Interaction):
    r = random.randint(0,100)
    balances[i.user.id] = bal(i.user.id)+r
    await i.response.send_message(f"💰 +{r} coins! Balance: {balances[i.user.id]} coins")

# ===== /LIST =====
@bot.tree.command(name="list", description="See a list - yours or someone else's")
async def list_cmd(i: discord.Interaction, user: discord.Member = None):
    target = user or i.user
    inv_list = inv(target.id)
    if not inv_list: return await i.response.send_message(f"{target.display_name} has no cards yet.", ephemeral=True)
    counts = Counter(inv_list)
    desc = f"**{target.display_name}'s List** - {len(inv_list)} cards ({len(counts)} unique)\nCoins: {bal(target.id)} | Rank Points: {get_points(target.id)}\n\n"
    for card, cnt in sorted(counts.items(), key=lambda x: -get_eff(target.id, x[0])):
        eff = get_eff(target.id, card); r = get_rank(target.id, card); stars = f" {'⭐'*r}" if r>0 else ""
        code = PLAYERS.get(card, {}).get("code_name","")
        desc += f"• {card} ({eff} OVR){stars} x{cnt} | `{code}`\n"
    await i.response.send_message(embed=discord.Embed(title=f"📋 {target.display_name}'s List", description=desc, color=0x2b2d31))

# ===== /INFO =====
@bot.tree.command(name="info", description="Info on a card")
async def info_cmd(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found - use code like ney-bd", ephemeral=True)
    if len(m)>1: return await i.response.send_message(f"Multiple found: {', '.join(m)} - use code!", ephemeral=True)
    card = m[0]; p = PLAYERS[card]
    r = get_rank(i.user.id, card); eff = get_eff(i.user.id, card)
    stars = f" {'⭐'*r}" if r>0 else ""
    e = discord.Embed(title=f"{card} ({eff} OVR){stars}", description=f"**Base:** {p['rating']} OVR\n**Your Rank:** {r}/3\n**Code:** `{p.get('code_name','')}`\n**Rarity:** {p.get('rarity','Common')}\n**Owned:** {'Yes' if card in inv(i.user.id) else 'No'}", color=0x00ff00)
    if p.get("info_image"): e.set_image(url=p["info_image"])
    await i.response.send_message(embed=e)

# ===== /TEAM =====
team_group = app_commands.Group(name="team", description="Team commands")
@team_group.command(name="view", description="View a team - yours or someone else's")
async def team_view(i: discord.Interaction, user: discord.Member = None):
    target = user or i.user
    t = team(target.id)
    if not t["players"]: return await i.response.send_message(f"{target.display_name} has no team yet.", ephemeral=True)
    img = build_lineup_image(target.id, t)
    desc = f"**{target.display_name}'s Team** - {t['formation']} - OVR {team_ovr(target.id)}\n"
    for p in t["players"]: desc += f"• {display_name(p, target.id)}\n"
    if t.get("captain"): desc += f"\n© Captain: {t['captain']}"
    await i.response.send_message(embed=discord.Embed(title=f"LINE UP - {target.display_name}", description=desc, color=0x2b2d31), file=discord.File(img, "team.png"))
@team_group.command(name="add", description="Add a player to your team")
async def team_add(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found - use code like ney-bd", ephemeral=True)
    if len(m)>1: return await i.response.send_message("Use code! Example: ney-bd", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own that card", ephemeral=True)
    t = team(i.user.id)
    if card in t["players"]: return await i.response.send_message("Already in team", ephemeral=True)
    if len(t["players"])>=11: return await i.response.send_message("Team is full (11)", ephemeral=True)
    t["players"].append(card); await i.response.send_message(f"✅ Added {display_name(card, i.user.id)} to your team!")
@team_group.command(name="remove", description="Remove a player from your team")
async def team_remove(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found - use code like ney-bd", ephemeral=True)
    card = m[0]; t = team(i.user.id)
    if card not in t["players"]: return await i.response.send_message("Not in your team", ephemeral=True)
    t["players"].remove(card); await i.response.send_message(f"✅ Removed {card} - back to inventory. Team now {len(t['players'])}/11")
@team_group.command(name="auto", description="Auto fill your team")
async def team_auto(i: discord.Interaction, formation: str = "4-3-3"):
    t = team(i.user.id); t["formation"]=formation
    sorted_cards = sorted(set(inv(i.user.id)), key=lambda x: -get_eff(i.user.id, x))
    t["players"] = sorted_cards[:11]
    await i.response.send_message(f"✅ Auto team set - {len(t['players'])}/11 - OVR {team_ovr(i.user.id)}")
bot.tree.add_command(team_group)

# ===== /RANKUP =====
rank_group = app_commands.Group(name="rankup", description="Rank Up - +1 OVR per rank, max +3, any rating")
@rank_group.command(name="player", description="Rank up a card")
async def rankup_player(i: discord.Interaction, player: str):
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found - use code like ney-bd", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own that card", ephemeral=True)
    cur = get_rank(i.user.id, card)
    if cur>=3: return await i.response.send_message(f"{display_name(card, i.user.id)} is already MAX Rank 3 ⭐⭐⭐", ephemeral=True)
    nxt=cur+1; cost=RANK_COST[nxt]; pts=get_points(i.user.id)
    if pts<cost: return await i.response.send_message(f"Need {cost} points for Rank {nxt}, you have {pts}\nBuy: /rankup buy amount: {cost-pts} (100 coins each)", ephemeral=True)
    rank_points[i.user.id]=pts-cost; ranks.setdefault(i.user.id,{})[card]=nxt
    base=PLAYERS.get(card,{"rating":80})["rating"]
    await i.response.send_message(f"⬆️ RANK UP! **{card}** Rank {cur} -> **Rank {nxt}** {'⭐'*nxt}\nOVR: {base+cur} -> **{base+nxt}**\nPoints left: {rank_points[i.user.id]}")
@rank_group.command(name="buy", description="Buy Rank Up Points - 100 coins per point")
async def rankup_buy(i: discord.Interaction, amount: int):
    if amount<=0: return await i.response.send_message("Amount must be 1+", ephemeral=True)
    cost=amount*100
    if bal(i.user.id)<cost: return await i.response.send_message(f"Need {cost} coins, you have {bal(i.user.id)}", ephemeral=True)
    balances[i.user.id]=bal(i.user.id)-cost; rank_points[i.user.id]=get_points(i.user.id)+amount
    await i.response.send_message(f"✅ Bought {amount} Rank Points for {cost} coins\nPoints: {get_points(i.user.id)} | Coins left: {bal(i.user.id)}")
@rank_group.command(name="points", description="Check Rank Points")
async def rankup_points(i: discord.Interaction):
    await i.response.send_message(f"⬆️ You have **{get_points(i.user.id)} Rank Points**\nCosts: Rank1=10pts | Rank2=20pts | Rank3=30pts | Total 0->3=60pts\nBuy: 100 coins per point | Any rating can rank up, max +3")
@rank_group.command(name="view", description="See your ranked cards")
async def rankup_view(i: discord.Interaction):
    ur=ranks.get(i.user.id,{})
    if not ur: return await i.response.send_message(f"No ranked cards yet. Points: {get_points(i.user.id)}", ephemeral=True)
    desc=f"Points: {get_points(i.user.id)}\n\n"
    for c,r in ur.items(): desc+=f"• {c} Rank {r} {'⭐'*r} - {PLAYERS.get(c,{'rating':80})['rating']} -> {get_eff(i.user.id, c)} OVR\n"
    await i.response.send_message(embed=discord.Embed(title="Your Rank Ups", description=desc, color=0x2b2d31))
bot.tree.add_command(rank_group)

# ===== /TRADE =====
trade_group = app_commands.Group(name="trade", description="Trade cards")
@trade_group.command(name="send", description="Send a trade offer to someone")
async def trade_send(i: discord.Interaction, user: discord.Member, player: str):
    if user.id == i.user.id: return await i.response.send_message("Can't trade yourself", ephemeral=True)
    m = find_cards(player)
    if not m: return await i.response.send_message("Card not found - use code like ney-bd", ephemeral=True)
    card = m[0]
    if card not in inv(i.user.id): return await i.response.send_message("You don't own that card", ephemeral=True)
    trades[user.id] = {"from_id": i.user.id, "card": card}
    await i.response.send_message(f"📩 Trade sent to {user.mention}!\nYou offer: **{display_name(card, i.user.id)}**\nThey need to do `/trade accept` to get it!")
@trade_group.command(name="accept", description="Accept a trade offer")
async def trade_accept(i: discord.Interaction):
    t = trades.get(i.user.id)
    if not t: return await i.response.send_message("No trade offer for you", ephemeral=True)
    from_id = t["from_id"]; card = t["card"]
    if card not in inv(from_id):
        del trades[i.user.id]
        return await i.response.send_message("They don't have that card anymore", ephemeral=True)
    inventories[from_id].remove(card)
    inventories.setdefault(i.user.id, []).append(card)
    del trades[i.user.id]
    await i.response.send_message(f"✅ Trade accepted! You got **{display_name(card, i.user.id)}**!")
@trade_group.command(name="decline", description="Decline a trade offer")
async def trade_decline(i: discord.Interaction):
    if i.user.id not in trades: return await i.response.send_message("No trade offer", ephemeral=True)
    del trades[i.user.id]
    await i.response.send_message("❌ Trade declined")
bot.tree.add_command(trade_group)

# ===== /BET =====
@bot.tree.command(name="bet", description="Bet coins - 50/50 coinflip, win double")
async def bet_cmd(i: discord.Interaction, amount: int):
    if amount <= 0: return await i.response.send_message("Amount must be 1+", ephemeral=True)
    if bal(i.user.id) < amount: return await i.response.send_message(f"Need {amount} coins, you have {bal(i.user.id)}", ephemeral=True)
    win = random.random() < 0.5
    if win:
        balances[i.user.id] = bal(i.user.id) + amount
        await i.response.send_message(f"🎉 YOU WON! +{amount} coins! Balance: {balances[i.user.id]}")
    else:
        balances[i.user.id] = bal(i.user.id) - amount
        await i.response.send_message(f"💀 YOU LOST! -{amount} coins! Balance: {balances[i.user.id]}")

# ===== /SHOP + /BUY-PACK =====
@bot.tree.command(name="shop", description="See pack shop")
async def shop(i: discord.Interaction):
    msg = "**📦 PACK SHOP**\n\n"
    for name, data in PACKS.items():
        tag = " 🔥 UNOB ONLY" if data["unob"] else ""
        msg += f"**{name.upper()}** - {data['price']} coins - OVR {data['ovr'][0]}-{data['ovr'][1]}{tag}\n"
    msg += "\nUse /buy-pack [name] - gives 3 cards"
    await i.response.send_message(msg)

@bot.tree.command(name="buy-pack", description="Buy and open a pack")
@app_commands.describe(pack_name="gold, epic, mythic, supreme, unob")
async def buy_pack(i: discord.Interaction, pack_name: str):
    pack_name = pack_name.lower()
    if pack_name not in PACKS:
        await i.response.send_message("Packs: gold, epic, mythic, supreme, unob")
        return
    uid = i.user.id
    price = PACKS[pack_name]["price"]
    if bal(uid) < price:
        await i.response.send_message(f"Not enough! You have {bal(uid)}, need {price}. Do /daily")
        return
    balances[uid] = bal(uid) - price
    lo, hi = PACKS[pack_name]["ovr"]
    is_unob = PACKS[pack_name]["unob"]
    pool = [n for n,p in PLAYERS.items() if lo <= p["rating"] <= hi]
    if not pool: pool = list(PLAYERS.keys())
    if not pool:
        await i.response.send_message("No cards added yet! Admin needs to do /admin_add_card first")
        return
    pulled = []
    for _ in range(3):
        if is_unob:
            unob_pool = [n for n,p in PLAYERS.items() if p.get("rarity","").lower()=="unob" or n.lower()=="hes"]
            name = random.choice(unob_pool) if unob_pool else random.choice(pool)
        else:
            name = random.choice(pool)
        inventories.setdefault(uid,[]).append(name)
        pulled.append(name)
    msg = f"**📦 {pack_name.upper()} PACK OPENED!**\n\n"
    for c in pulled:
        msg += f"• {display_name(c, uid)}\n"
    msg += f"\nBalance: {balances[uid]} | /team auto to use them!"
    await i.response.send_message(msg)

# ===== ADMIN =====
@bot.tree.command(name="admin_add_card", description="[ADMIN] Add card")
async def aac(i: discord.Interaction, name: str, rating: int, code_name: str, spawn_image: str = "", info_image: str = "", rarity: str = "Common"):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    PLAYERS[name]={"rating":rating,"code_name":code_name,"spawn_image":spawn_image or info_image,"info_image":info_image or spawn_image,"rarity":rarity}
    await i.response.send_message(f"✅ Added {name} ({rating} OVR) code: {code_name}")
@bot.tree.command(name="admin_give", description="[ADMIN] Give card")
async def ag(i: discord.Interaction, user: discord.Member, card: str):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    m=find_cards(card)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    inventories.setdefault(user.id,[]).append(m[0]); await i.response.send_message(f"Gave {user.mention} {m[0]}")
@bot.tree.command(name="admin_spawn", description="[ADMIN] Spawn a card")
async def aspawn(i: discord.Interaction, card: str):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    m=find_cards(card)
    if not m: return await i.response.send_message("Card not found", ephemeral=True)
    c=m[0]; p=PLAYERS[c]
    e=discord.Embed(title="✨ WILD CARD APPEARED! ✨", description=f"Type **{c}** OR code **{p['code_name']}** to claim!", color=0x00ff00)
    e.set_image(url=p.get("info_image",""))
    await i.response.send_message(embed=e)

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    q=msg.content.lower().strip()
    for name,p in PLAYERS.items():
        if q==name.lower() or q==p.get("code_name","").lower():
            inventories.setdefault(msg.author.id,[]).append(name)
            await msg.channel.send(f"✅ {msg.author.mention} claimed **{display_name(name, msg.author.id)}**!")
            break
    await bot.process_commands(msg)

bot.run(TOKEN)
