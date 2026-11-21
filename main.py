# ===== main.py - FULL BOT - PASTE ALL =====
import discord, random, json, asyncio, os
from discord.ext import commands

TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATA =====
PLAYERS = {
    "ney-bd": {"name": "Neymar BD", "ovr": 97, "rarity": "BD"},
    "haa-bd": {"name": "Haaland BD", "ovr": 96, "rarity": "BD"},
    "mba-bd": {"name": "Mbappe BD", "ovr": 96, "rarity": "BD"},
    "bel-bd": {"name": "Bellingham BD", "ovr": 95, "rarity": "BD"},
    "rod-bd": {"name": "Rodrygo BD", "ovr": 94, "rarity": "BD"},
    "vin-bd": {"name": "Vinicius BD", "ovr": 94, "rarity": "BD"},
    "mes-bd": {"name": "Messi BD", "ovr": 98, "rarity": "BD"},
    "ron-bd": {"name": "Ronaldo BD", "ovr": 97, "rarity": "BD"},
    "ped-bd": {"name": "Pedri BD", "ovr": 93, "rarity": "BD"},
    "yam-bd": {"name": "Lamine Yamal BD", "ovr": 92, "rarity": "BD"},
}

# Add more players here if you want
# "code": {"name": "Name", "ovr": 90, "rarity": "BD"},

DATA_FILE = "data.json"
data = {"inv": {}, "teams": {}, "coins": {}}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE) as f: data = json.load(f)
    except: pass

def inv(uid):
    uid = str(uid)
    if uid not in data["inv"]: data["inv"][uid] = []
    return data["inv"][uid]

def teams_get(uid):
    uid = str(uid)
    if uid not in data["teams"]: data["teams"][uid] = []
    return data["teams"][uid]

def get_eff(uid, code):
    return PLAYERS[code]["ovr"] if code in PLAYERS else 80

def save_all():
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# ===== BET / TRADE STORAGE =====
active_bets = {} # key: "id1-id2" -> bet arena
active_match_bets = {}
active_trades = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# ===== CLAIM =====
@bot.tree.command(name="claim", description="Claim a player")
async def claim_cmd(i: discord.Interaction, player: str):
    code = player.lower()
    if code not in PLAYERS:
        return await i.response.send_message(f"Not found! Try: {', '.join(PLAYERS.keys())}", ephemeral=True)
    inv(i.user.id).append(code)
    save_all()
    p = PLAYERS[code]
    e = discord.Embed(title="✅ Claimed!", description=f"**{p['name']}**\nOVR {p['ovr']} | {p['rarity']}", color=0x00FF00)
    await i.response.send_message(embed=e)

@bot.tree.command(name="inv", description="Your inventory")
async def inv_cmd(i: discord.Interaction):
    cards = inv(i.user.id)
    if not cards: return await i.response.send_message("Empty! Do `/claim player:ney-bd`", ephemeral=True)
    from collections import Counter
    c = Counter(cards)
    desc = "\n".join([f"{PLAYERS[k]['name']} x{v} - OVR {PLAYERS[k]['ovr']}" for k,v in c.items() if k in PLAYERS])
    await i.response.send_message(embed=discord.Embed(title=f"{i.user.display_name}'s Inventory", description=desc, color=0x2b2d31))

# ===== TEAM =====
@bot.tree.command(name="team", description="Team - auto / show")
async def team_cmd(i: discord.Interaction, action: str):
    action = action.lower()
    if action == "auto":
        cards = inv(i.user.id)
        if len(cards) < 5: return await i.response.send_message("Need at least 5 cards! Claim more", ephemeral=True)
        # Best 11 or all if less
        best = sorted(cards, key=lambda c: get_eff(i.user.id, c), reverse=True)[:11]
        data["teams"][str(i.user.id)] = best
        save_all()
        ovr = sum([get_eff(i.user.id,c) for c in best])//len(best)
        desc = "\n".join([f"{PLAYERS[c]['name']} - {get_eff(i.user.id,c)}" for c in best if c in PLAYERS])
        await i.response.send_message(embed=discord.Embed(title=f"Team Set! OVR {ovr}", description=desc, color=0x2b2d31))
    elif action == "show":
        t = teams_get(i.user.id)
        if not t: return await i.response.send_message("No team! Do `/team action:auto`", ephemeral=True)
        ovr = sum([get_eff(i.user.id,c) for c in t])//len(t)
        desc = "\n".join([f"{PLAYERS[c]['name']} - {get_eff(i.user.id,c)}" for c in t if c in PLAYERS])
        await i.response.send_message(embed=discord.Embed(title=f"{i.user.display_name} Team OVR {ovr}", description=desc, color=0x2b2d31))

# ===== TRADE =====
@bot.tree.command(name="trade", description="Trade - offer / accept")
async def trade_cmd(i: discord.Interaction, action: str, opponent: discord.User, player: str = ""):
    action = action.lower()
    if action == "offer":
        code = player.lower()
        if code not in PLAYERS: return await i.response.send_message("Use `player:ney-bd`", ephemeral=True)
        if code not in inv(i.user.id): return await i.response.send_message("You don't have that card", ephemeral=True)
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        active_trades[key] = {"p1": i.user.id, "p2": opponent.id, "name1": i.user.display_name, "name2": opponent.display_name, "offers": {i.user.id: code, opponent.id: None}}
        await i.response.send_message(f"🤝 **TRADE OFFER!**\n{i.user.display_name} offers **{PLAYERS[code]['name']}**\n\n{opponent.mention} do `/trade action:accept opponent:@{i.user.display_name} player:haa-bd` to offer yours and complete!")
    elif action == "accept":
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        if key not in active_trades: return await i.response.send_message("No trade found!", ephemeral=True)
        t = active_trades[key]
        code = player.lower()
        if code not in inv(i.user.id): return await i.response.send_message("You don't have that card", ephemeral=True)
        # Swap
        c1 = t["offers"][t["p1"]]
        c2 = code
        inv(t["p1"]).remove(c1); inv(t["p2"]).remove(c2)
        inv(t["p1"]).append(c2); inv(t["p2"]).append(c1)
        save_all()
        del active_trades[key]
        await i.response.send_message(f"✅ **TRADE DONE!**\n{t['name1']} gets **{PLAYERS[c2]['name']}**\n{t['name2']} gets **{PLAYERS[c1]['name']}**")

# ===== BET ARENA - PENALTY SHOOTOUT =====
@bot.tree.command(name="bet", description="Bet arena - challenge / add / start")
async def bet_cmd(i: discord.Interaction, action: str, opponent: discord.User = None, player: str = ""):
    action = action.lower()
    if action == "challenge":
        if not opponent: return await i.response.send_message("Need opponent!", ephemeral=True)
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        active_bets[key] = {"p1": i.user.id, "p2": opponent.id, "name1": i.user.display_name, "name2": opponent.display_name, "stakes": {i.user.id: [], opponent.id: []}}
        return await i.response.send_message(f"🎲 **BET ARENA CREATED!**\n{i.user.display_name} vs {opponent.display_name}\nBoth do `/bet action:add opponent:@Other player:ney-bd` to stake cards!\nThen `/bet action:start opponent:@Other`")
    if action == "add":
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        if key not in active_bets: return await i.response.send_message("No bet! Do `/bet action:challenge` first", ephemeral=True)
        code = player.lower()
        if code not in inv(i.user.id): return await i.response.send_message("You don't have that card", ephemeral=True)
        active_bets[key]["stakes"][i.user.id].append(code)
        return await i.response.send_message(f"✅ {i.user.display_name} staked **{PLAYERS[code]['name']}**\nStakes: {len(active_bets[key]['stakes'][active_bets[key]['p1']])} vs {len(active_bets[key]['stakes'][active_bets[key]['p2']])}")
    if action == "start":
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        if key not in active_bets: return await i.response.send_message("No bet!", ephemeral=True)
        b = active_bets[key]
        if not b["stakes"][b["p1"]] or not b["stakes"][b["p2"]]: return await i.response.send_message("Both need to stake!", ephemeral=True)
        # Penalty shootout
        p1 = p2 = 0
        for _ in range(5):
            if random.random() < 0.7: p1+=1
            if random.random() < 0.7: p2+=1
        while p1==p2:
            if random.random()<0.5: p1+=1
            else: p2+=1
        winner = b["p1"] if p1>p2 else b["p2"]
        loser = b["p2"] if winner==b["p1"] else b["p1"]
        winner_name = b["name1"] if winner==b["p1"] else b["name2"]
        all_cards = b["stakes"][b["p1"]] + b["stakes"][b["p2"]]
        for c in b["stakes"][loser]:
            if c in inv(loser): inv(loser).remove(c)
        for c in b["stakes"][winner]:
            if c in inv(winner): inv(winner).remove(c)
        for c in all_cards: inv(winner).append(c)
        save_all()
        del active_bets[key]
        names = "\n".join([f"• {PLAYERS[c]['name']}" for c in all_cards])
        return await i.response.send_message(f"🏆 **BET ARENA FINISHED!**\n{b['name1']} {p1} - {p2} {b['name2']} (Pens)\n\n**Winner: {winner_name}** takes ALL:\n{names}")

# ===== MATCH - 40 SEC ANIMATED, LOW SCORING / CRAZY =====
@bot.tree.command(name="match", description="Match - play / bet")
async def match_cmd(i: discord.Interaction, action: str, opponent: discord.User, player: str = ""):
    action = action.lower()

    # --- MATCH BET ---
    if action == "bet":
        code = player.lower()
        if code not in PLAYERS: return await i.response.send_message("Use `player:ney-bd`", ephemeral=True)
        if code not in inv(i.user.id): return await i.response.send_message(f"You don't have `{code}`", ephemeral=True)
        key = f"{min(i.user.id, opponent.id)}-{max(i.user.id, opponent.id)}"
        if key not in active_match_bets:
            active_match_bets[key] = {"p1": i.user.id, "p2": opponent.id, "name1": i.user.display_name, "name2": opponent.display_name, "stakes": {i.user.id: [code], opponent.id: []}}
            return await i.response.send_message(f"⚽ **MATCH BET CREATED!**\n{i.user.display_name} staked **{PLAYERS[code]['name']}**\n\n{opponent.mention} do `/match action:bet opponent:@{i.user.display_name} player:haa-bd` to stake yours and START!")
        b = active_match_bets[key]
        b["stakes"][i.user.id] = [code]
        # Play animated match for bet - winner takes all, we will run play logic below with bet flag
        # For simplicity, run quick sim for bet
        t1 = teams_get(b["p1"]); t2 = teams_get(b["p2"])
        o1 = sum([get_eff(b["p1"],c) for c in t1])//len(t1) if t1 else PLAYERS[b["stakes"][b["p1"]][0]]["ovr"]
        o2 = sum([get_eff(b["p2"],c) for c in t2])//len(t2) if t2 else PLAYERS[b["stakes"][b["p2"]][0]]["ovr"]
        # Simple 1-0 style
        if random.random() < 0.5 + (o1-o2)*0.02: g1, g2 = 1, 0
        else: g1, g2 = 0, 1
        winner = b["p1"] if g1>g2 else b["p2"]
        loser = b["p2"] if winner==b["p1"] else b["p1"]
        winner_name = b["name1"] if winner==b["p1"] else b["name2"]
        all_cards = b["stakes"][b["p1"]] + b["stakes"][b["p2"]]
        for c in b["stakes"][loser]:
            if c in inv(loser): inv(loser).remove(c)
        for c in b["stakes"][winner]:
            if c in inv(winner): inv(winner).remove(c)
        for c in all_cards: inv(winner).append(c)
        save_all()
        del active_match_bets[key]
        return await i.response.send_message(f"🏆 **MATCH BET FINISHED!**\n{b['name1']} {g1} - {g2} {b['name2']} (OVR {o1} vs {o2})\n\n**Winner: {winner_name}** takes:\n• {PLAYERS[all_cards[0]]['name']}\n• {PLAYERS[all_cards[1]]['name']}")

    if action != "play":
        return await i.response.send_message("Use `action:play` or `action:bet`", ephemeral=True)

    # --- ANIMATED MATCH - 40 SEC ---
    t1 = teams_get(i.user.id); t2 = teams_get(opponent.id)
    if not t1 or not t2:
        return await i.response.send_message("Both need a team! Do `/team action:auto` first", ephemeral=True)
    o1 = sum([get_eff(i.user.id,c) for c in t1])//len(t1)
    o2 = sum([get_eff(opponent.id,c) for c in t2])//len(t2)

    await i.response.send_message("🏟️ Match starting...")
    msg = await i.original_response()

    mode = random.random()
    if mode < 0.7:
        total_goals = random.choice([1,1,1,2,0,2]); game_type = "🔒 TIGHT GAME"
    else:
        total_goals = random.choice([4,5,6,3]); game_type = "🔥 CRAZY GAME"
    goal_minutes = sorted(random.sample(range(5, 91), total_goals)) if total_goals>0 else []
    mom = 50 + (o1-o2)*1.5; mom = max(35, min(65, mom))
    g1 = g2 = 0; events = []; scorers = []; ball = 5

    def get_scorer(uid, cards):
        c = random.choice(cards)
        return PLAYERS[c]['name'] if c in PLAYERS else c
    def pitch(m, g1, g2, ball):
        line = ["·"]*11; line[ball]="⚽"; line[0]="🥅"; line[10]="🥅"
        return f"```\n▬▬▬▬▬▬▬▬▬▬▬\n{''.join(line)}\n▬▬▬▬▬▬▬▬▬▬▬\n⏱️ {m}' | {g1} - {g2}\n```"

    # PRE-MATCH 2s
    e = discord.Embed(title="🏟️ PRE-MATCH", description=f"**{i.user.display_name} ({o1}) vs {opponent.display_name} ({o2})**\n{game_type}\n\n🎤 Teams walking out...", color=0xFFFF00)
    await msg.edit(embed=e); await asyncio.sleep(2)

    # LIVE 32s
    for minute in range(0, 91, 5):
        ball += random.choice([-2,-1,0,1,2]); ball = max(1, min(9, ball))
        goal_text = ""
        hit = [gm for gm in goal_minutes if minute <= gm < minute+5]
        if hit:
            gm = hit[0]; goal_minutes.remove(gm)
            if random.random() < mom/100:
                g1+=1; s = get_scorer(i.user.id, t1)
                style = random.choice(["⚽ TAP-IN", "🎯 HEADER", "🚀 BANGER", "🔥 BICYCLE KICK"])
                goal_text = f"\n\n🎉 **GOAL! {gm}' {style} - {s} ({i.user.display_name}) - {g1}-{g2}**"
                events.append(f"{gm}' {s} - {g1}-{g2}"); scorers.append(s); ball=9; mom-=6
            else:
                g2+=1; s = get_scorer(opponent.id, t2)
                style = random.choice(["⚽ TAP-IN", "🎯 HEADER", "🚀 BANGER", "🔥 BICYCLE KICK"])
                goal_text = f"\n\n🎉 **GOAL! {gm}' {style} - {s} ({opponent.display_name}) - {g1}-{g2}**"
                events.append(f"{gm}' {s} - {g1}-{g2}"); scorers.append(s); ball=1; mom+=6
        elif random.random() < 0.30:
            goal_text = f"\n\n{random.choice(['🧤 HUGE SAVE!', '😱 OFF THE POST!', '💥 BIG TACKLE!', '🔥 CROWD GOES WILD!', '🎯 FREE KICK JUST WIDE!'])}"
        if minute == 45:
            e = discord.Embed(title="⏸️ HALF TIME", description=f"**{i.user.display_name} {g1} - {g2} {opponent.display_name}**\n\n" + "\n".join(events) + "\n\n⏳ 2nd half...", color=0xFFFF00)
            await msg.edit(embed=e); await asyncio.sleep(2); continue
        half = "1ST HALF" if minute < 45 else "2ND HALF"
        desc = f"**{i.user.display_name} {g1} - {g2} {opponent.display_name}**\nOVR {o1} vs {o2} | {half} | {game_type}\n"
        desc += pitch(minute, g1, g2, ball)
        if events: desc += "**📋 Live:**\n" + "\n".join(events[-4:])
        desc += goal_text
        e = discord.Embed(title="⚽ LIVE MATCH ⚽", description=desc, color=0x2b2d31)
        e.set_footer(text=f"Minute {minute}' / 90' - Live... Ends in ~40s")
        await msg.edit(embed=e); await asyncio.sleep(1.8)

    # STOPPAGE 2s
    if g1==g2 and random.random() < 0.5:
        if random.random() < mom/100: g1+=1; s = get_scorer(i.user.id, t1)
        else: g2+=1; s = get_scorer(opponent.id, t2)
        events.append(f"90+' {s} WINNER! - {g1}-{g2}"); scorers.append(s)
        e = discord.Embed(title="🚨 90+' LAST MINUTE WINNER! 🚨", description=f"**{i.user.display_name} {g1} - {g2} {opponent.display_name}**\n\n🚨 **{s} SCORES AT THE DEATH!**", color=0xFF0000)
        await msg.edit(embed=e); await asyncio.sleep(2)

    pens = ""
    if g1==g2:
        p1=p2=0
        for _ in range(5):
            if random.random()<0.7: p1+=1
            if random.random()<0.7: p2+=1
        while p1==p2:
            if random.random()<0.5: p1+=1
            else: p2+=1
        pens = f"\n**PENALTIES: {p1} - {p2}**"
        winner = i.user.display_name if p1>p2 else opponent.display_name
    else:
        winner = i.user.display_name if g1>g2 else opponent.display_name
    final = f"**{i.user.display_name} {g1} - {g2} {opponent.display_name}**{pens}\nOVR {o1} vs {o2} | {game_type}\n\n**📋 FULL MATCH:**\n" + "\n".join(events) + f"\n\n🏆 **Winner: {winner}**\n⭐ **MOTM: {scorers[-1] if scorers else 'Defensive masterclass'}**"
    e = discord.Embed(title="🏆 FULL TIME! 🏆", description=final, color=0x00FF00)
    await msg.edit(embed=e)

# ===== ADMIN - GIVE =====
@bot.tree.command(name="give", description="Admin give player")
async def give_cmd(i: discord.Interaction, user: discord.User, player: str):
    # Change YOUR_ID to your Discord ID
    if i.user.id != 123456789012345678:
        return await i.response.send_message("Admin only!", ephemeral=True)
    code = player.lower()
    if code not in PLAYERS: return await i.response.send_message("Player not found", ephemeral=True)
    inv(user.id).append(code); save_all()
    await i.response.send_message(f"Gave **{PLAYERS[code]['name']}** to {user.display_name}")

bot.run(TOKEN)
