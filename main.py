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
PLAYERS = {}  # name -> {rating, code_name, spawn_image, info_image, rarity}
balances = {} # user_id -> coins
rank_points = {} # user_id -> rank points
ranks = {} # user_id -> {card_name: 0-3}
inventories = {} # user_id -> [card_names]
teams = {} # user_id -> {players: [], formation: "4-3-3", captain: None}
claims = {} # code -> user_id (for spawn claim)

RANK_COST = {1: 10, 2: 20, 3: 30}
FB = {"4-3-3": 0, "4-4-2": 0, "3-5-2": 0, "4-2-3-1": 0}

def adm(uid): return uid == OWNER_ID
def bal(uid): return balances.get(uid, 0)
def inv(uid): return inventories.get(uid, [])
def team(uid): return teams.setdefault(uid, {"players": [], "formation": "4-3-3", "captain": None})
def get_rank(uid, card): return ranks.get(uid, {}).get(card, 0)
def get_points(uid): return rank_points.get(uid, 0)
def get_eff(uid, card): return PLAYERS.get(card, {"rating": 80})["rating"] + get_rank(uid, card)

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

# ===== LINEUP IMAGE =====
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
    # positions for 4-3-3
    pos = [(0.22,0.22),(0.22,0.5),(0.22,0.78),(0.48,0.22),(0.48,0.5),(0.48,0.78),(0.73,0.15),(0.73,0.38),(0.73,0.62),(0.73,0.85),(0.90,0.5)]
    for idx, (yf,xf) in enumerate(pos):
        x = int(x0+(x1-x0)*xf); y = int(y0+(y1-y0)*yf); r=48
        name = t["players"][idx] if idx < len(t["players"]) else "EMPTY"
        d.ellipse([x-r-4,y-r-4,x+r+4,y+r+4], fill="white")
        # try spawn_image face crop
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

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try: await bot.tree.sync(); print("Synced")
    except Exception as e: print(e)

# ===== /DAILY - 0-100 COINS =====
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
    # sort by eff OVR
    sorted_cards = sorted(set(inv(i.user.id)), key=lambda x: -get_eff(i.user.id, x))
    t["players"] = sorted_cards[:11]
    await i.response.send_message(f"✅ Auto team set - {len(t['players'])}/11 - OVR {team_ovr(i.user.id)}")
bot.tree.add_command(team_group)

# ===== /RANKUP =====
rank_group = app_commands.Group(name="rankup", description="Rank Up - +1 OVR per rank")
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
    await i.response.send_message(f"⬆️ You have **{get_points(i.user.id)} Rank Points**\nCosts: Rank1=10pts | Rank2=20pts | Rank3=30pts | Total 0->3=60pts\nBuy: 100 coins per point")
@rank_group.command(name="view", description="See your ranked cards")
async def rankup_view(i: discord.Interaction):
    ur=ranks.get(i.user.id,{})
    if not ur: return await i.response.send_message(f"No ranked cards yet. Points: {get_points(i.user.id)}", ephemeral=True)
    desc=f"Points: {get_points(i.user.id)}\n\n"
    for c,r in ur.items(): desc+=f"• {c} Rank {r} {'⭐'*r} - {PLAYERS.get(c,{'rating':80})['rating']} -> {PLAYERS.get(c,{'rating':80})['rating']+r} OVR\n"
    await i.response.send_message(embed=discord.Embed(title="Your Rank Ups", description=desc, color=0x2b2d31))
bot.tree.add_command(rank_group)

# ===== ADMIN =====
@bot.tree.command(name="admin_add_card", description="[ADMIN] Add card")
async def aac(i: discord.Interaction, name: str, rating: int, code_name: str, spawn_image: str = "", info_image: str = "", rarity: str = "Common"):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    PLAYERS[name]={"rating":rating,"code_name":code_name,"spawn_image":spawn_image or info_image,"info_image":info_image or spawn_image,"rarity":rar
