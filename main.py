import discord, random, json, asyncio, os
from discord.ext import commands
from discord import app_commands

OWNER_ID = 1535155949461839933
TOKEN = "PASTE_YOUR_REAL_TOKEN_HERE"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

try:
    with open("players.json") as f: PLAYERS = {p["name"]: p for p in json.load(f)}
except: PLAYERS = {"Neymar": {"name": "Neymar", "rating": 100, "rarity": "Unob", "code_name": "El Mago", "desc": "Pure Brazilian sauce", "spawn_image": "https://picsum.photos/400/600?random=1", "info_image": "https://picsum.photos/400/600?random=2"}}

PACKS = {"Gold Pack": {"price": 1000, "locked": True}, "Epic Pack": {"price": 2000, "locked": True}, "Mythic Pack": {"price": 6000, "locked": True}, "Supreme Pack": {"price": 12000, "locked": True}, "Unob Pack": {"price": 15000, "locked": False}}
balances = {}; inventories = {}; wallets = {}; teams = {}; active_trades = {}; active_bets = {}; active_spawn = None
FB = {"4-3-3": 2, "4-2-3-1": 3, "3-5-2": 2, "4-4-2": 1, "3-4-3": 1, "5-3-2": -1, "4-1-2-1-2": 2, "3-4-2-1": 2}
def bal(u): return balances.get(u, 0)
def inv(u): return inventories.setdefault(u, [])
def wal(u): return wallets.setdefault(u, {})
def team(u): return teams.setdefault(u, {"players": [], "formation": "4-3-3"})
def ovr(n): return sum(PLAYERS.get(x, {"rating": 80})["rating"] for x in n)//len(n) if n else 0
def adm(u): return u == OWNER_ID

class PV(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60); self.user = user
        for n, d in PACKS.items():
            b = discord.ui.Button(label=f"{n} - {d['price']}" if not d['locked'] else f"{n} - LOCKED", style=discord.ButtonStyle.primary if not d['locked'] else discord.ButtonStyle.grey, disabled=d['locked'])
            async def buy(i, n=n):
                if i.user.id != self.user.id: return await i.response.send_message("Not your shop", ephemeral=True)
                if bal(i.user.id) < PACKS[n]['price']: return await i.response.send_message("Not enough coins", ephemeral=True)
                balances[i.user.id] = bal(i.user.id) - PACKS[n]['price']; w = wal(i.user.id); w[n] = w.get(n, 0)+1
                await i.response.send_message(f"Bought 1x {n}!", ephemeral=True)
            b.callback = buy; self.add_item(b)

@bot.tree.command(name="pack", description="Packs")
@app_commands.choices(action=[app_commands.Choice(name="buy", value="buy"), app_commands.Choice(name="wallet", value="wallet"), app_commands.Choice(name="open", value="open")])
async def pack(i: discord.Interaction, action: app_commands.Choice[str]):
    if action.value == "buy":
        e = discord.Embed(title="Pack Shop")
        for n, d in PACKS.items(): e.add_field(name=n, value="LOCKED" if d['locked'] else f"{d['price']} coins", inline=False)
        await i.response.send_message(embed=e, view=PV(i.user))
    elif action.value == "wallet":
        w = wal(i.user.id); await i.response.send_message(embed=discord.Embed(title="Your Pack Wallet", description="\n".join([f"{k}: {v}x" for k, v in w.items()]) or "No packs"))
    else:
        w = wal(i.user.id)
        if w.get("Unob Pack", 0) <= 0: return await i.response.send_message("No Unob Pack", ephemeral=True)
        w["Unob Pack"] -= 1; inv(i.user.id).append("Neymar"); p = PLAYERS["Neymar"]
        e = discord.Embed(title="You pulled Neymar!", description=f"Rating: {p['rating']} | {p['rarity']}"); e.set_image(url=p['info_image']); await i.response.send_message(embed=e)

@bot.tree.command(name="player", description="Player info")
async def player(i: discord.Interaction, name: str = None):
    if name not in PLAYERS: return await i.response.send_message("Not found", ephemeral=True)
    p = PLAYERS[name]; e = discord.Embed(title=f"{name} - {p['rating']} {p['rarity']}", description=f"Code: {p['code_name']}\n\n{p['desc']}"); e.set_image(url=p['info_image']); await i.response.send_message(embed=e)

@bot.tree.command(name="admin_spawn", description="[ADMIN] Spawn - type name to claim")
async def aspawn(i: discord.Interaction, card: str):
    global active_spawn
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    if card not in PLAYERS: return await i.response.send_message(f"Available: {', '.join(PLAYERS.keys())}", ephemeral=True)
    if active_spawn: return await i.response.send_message("Already spawned!", ephemeral=True)
    p = PLAYERS[card]; active_spawn = {"card": card, "claimed": False}
    e = discord.Embed(title="✨ WILD CARD APPEARED! ✨", description="Type their **name** to claim! 30 sec"); e.set_image(url=p['spawn_image']); await i.response.send_message(embed=e)
    await asyncio.sleep(30)
    if active_spawn and active_spawn["card"] == card and not active_spawn["claimed"]: active_spawn = None; await i.followup.send(f"Too slow! It was **{card}**")

@bot.event
async def on_message(m):
    global active_spawn
    if m.author.bot: return
    if active_spawn and not active_spawn["claimed"] and m.content.lower().strip() == active_spawn["card"].lower():
        active_spawn["claimed"] = True; c = active_spawn["card"]; inv(m.author.id).append(c); p = PLAYERS[c]
        e = discord.Embed(title=f"🎉 {m.author.display_name} GOT IT!", description=f"It was **{c} - {p['rating']}**"); e.set_image(url=p['info_image']); await m.channel.send(embed=e); active_spawn = None; return
    await bot.process_commands(m)

@bot.tree.command(name="admin_give", description="[ADMIN] Give card + coins")
async def agive(i: discord.Interaction, user: discord.Member, card: str = None, amount: int = 0):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    if amount: balances[user.id] = bal(user.id) + amount
    if card: inv(user.id).append(card)
    await i.response.send_message(f"Gave {user.mention} {card or ''} + {amount} coins")

@bot.tree.command(name="admin_give_pack", description="[ADMIN] Give packs")
async def agp(i: discord.Interaction, user: discord.Member, pack_name: str, amount: int = 1):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    w = wal(user.id); w[pack_name] = w.get(pack_name, 0) + amount; await i.response.send_message(f"Gave {user.mention} {amount}x {pack_name}")

@bot.tree.command(name="admin_coins", description="[ADMIN] Set coins")
async def acoins(i: discord.Interaction, user: discord.Member, amount: int):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    balances[user.id] = amount; await i.response.send_message(f"Set {user.mention} to {amount}")

@bot.tree.command(name="admin_remove", description="[ADMIN] Remove card")
async def arem(i: discord.Interaction, user: discord.Member, card: str):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    if card in inv(user.id): inv(user.id).remove(card); await i.response.send_message(f"Removed {card}")
    else: await i.response.send_message("Doesn't have it")

@bot.tree.command(name="admin_list", description="[ADMIN] List cards")
async def alist(i: discord.Interaction):
    if not adm(i.user.id): return await i.response.send_message("Only owner", ephemeral=True)
    await i.response.send_message("\n".join([f"{n} - {p['rating']} {p['rarity']}" for n, p in PLAYERS.items()]))

@bot.tree.command(name="balance", description="Coins")
async def balance(i: discord.Interaction): await i.response.send_message(f"💰 {bal(i.user.id)} coins")
@bot.tree.command(name="daily", description="Daily")
async def daily(i: discord.Interaction):
    r = random.randint(800, 1500); balances[i.user.id] = bal(i.user.id) + r; await i.response.send_message(f"💰 +{r}! Balance: {balances[i.user.id]}")
@bot.tree.command(name="inventory", description="Your cards")
async def inventory(i: discord.Interaction):
    v = inv(i.user.id)
    if not v: return await i.response.send_message("Empty!")
    await i.response.send_message("\n".join([f"{x+1}. {n} - {PLAYERS.get(n, {'rating': 80})['rating']}" for x, n in enumerate(v)]))

@bot.tree.command(name="team", description="Show team")
async def teamc(i: discord.Interaction):
    t = team(i.user.id)
    if not t["players"]: return await i.response.send_message("No team. Do /team-auto")
    await i.response.send_message(f"**{t['formation']} | OVR {ovr(t['players'])}**\n" + "\n".join(t["players"]))
@bot.tree.command(name="team-auto", description="Auto best 11")
async def tauto(i: discord.Interaction):
    v = inv(i.user.id)
    if not v: return await i.response.send_message("Empty!")
    best = sorted(v, key=lambda x: PLAYERS.get(x, {"rating": 80})["rating"], reverse=True)[:11]; team(i.user.id)["players"] = best; await i.response.send_message(f"Team set! OVR: {ovr(best)}")
@bot.tree.command(name="team-formation", description="Change formation")
async def tform(i: discord.Interaction, formation: str):
    if formation not in FB: return await i.response.send_message(f"Use: {', '.join(FB.keys())}")
    team(i.user.id)["formation"] = formation; await i.response.send_message(f"Formation -> {formation}")

@bot.tree.command(name="trade", description="Offer trade")
async def trade(i: discord.Interaction, target: discord.Member, your_card: int, their_card: int):
    my = inv(i.user.id); th = inv(target.id)
    if your_card < 1 or your_card > len(my) or their_card < 1 or their_card > len(th): return await i.response.send_message("Invalid numbers. Check /inventory")
    tid = f"T{random.randint(1000,9999)}"; active_trades[tid] = {"from": i.user.id, "to": target.id, "my": your_card-1, "their": their_card-1}
    await i.response.send_message(f"🔄 TRADE {tid}\n{i.user.display_name} offers: {my[your_card-1]}\nFor {target.display_name}'s: {th[their_card-1]}\n{target.mention} do `/accept-trade {tid}` or `/decline-trade {tid}`")
@bot.tree.command(name="accept-trade", description="Accept trade")
async def atrade(i: discord.Interaction, trade_id: str):
    if trade_id not in active_trades: return await i.response.send_message("Not found")
    t = active_trades.pop(trade_id)
    if i.user.id != t["to"]: return await i.response.send_message("Not for you")
    a = inv(t["from"]); b = inv(t["to"]); ac = a.pop(t["my"]); bc = b.pop(t["their"]); a.append(bc); b.append(ac); await i.response.send_message(f"✅ Traded! You got {ac}, they got {bc}")
@bot.tree.command(name="decline-trade", description="Decline trade")
async def dtrade(i: discord.Interaction, trade_id: str):
    if trade_id in active_trades: active_trades.pop(trade_id); await i.response.send_message("Declined")
    else: await i.response.send_message("Not found")

@bot.tree.command(name="bet", description="Bet coins")
async def bet(i: discord.Interaction, opponent: discord.Member, amount: int):
    if amount <= 0 or bal(i.user.id) < amount: return await i.response.send_message(f"You have {bal(i.user.id)}")
    balances[i.user.id] = bal(i.user.id) - amount; bid = f"B{random.randint(1000,9999)}"; active_bets[bid] = {"opp": opponent.id, "amt": amount}
    await i.response.send_message(f"🎲 BET {bid}: {amount} vs {opponent.display_name}\nOpponent do `/accept-bet {bid}`")
@bot.tree.command(name="accept-bet", description="Accept bet")
async def abet(i: discord.Interaction, bet_id: str):
    if bet_id not in active_bets: return await i.response.send_message("Not found")
    b = active_bets[bet_id]
    if i.user.id != b["opp"]: return await i.response.send_message("Not for you")
    if bal(i.user.id) < b["amt"]: return await i.response.send_message("Not enough")
    balances[i.user.id] = bal(i.user.id) - b["amt"]; b["accepted"] = True; await i.response.send_message(f"Accepted! Pot: {b['amt']*2}")
@bot.tree.command(name="resolve-bet", description="Resolve bet")
async def rbet(i: discord.Interaction, bet_id: str, winner: discord.Member):
    if bet_id not in active_bets: return await i.response.send_message("Not found")
    b = active_bets.pop(bet_id); pot = b["amt"]*2 if b.get("accepted") else b["amt"]; balances[winner.id] = bal(winner.id) + pot; await i.response.send_message(f"🏆 {winner.display_name} won +{pot}!")

@bot.tree.command(name="match", description="Play match")
async def match(i: discord.Interaction, opponent: discord.Member):
    t1 = team(i.user.id); t2 = team(opponent.id)
    if not t1["players"] or not t2["players"]: return await i.response.send_message("Both need /team-auto")
    o1 = ovr(t1["players"]); o2 = ovr(t2["players"]); p1 = max(32, min(68, 50 + max(-8, min(8, o1-o2)) + FB.get(t1["formation"], 0) - FB.get(t2["formation"], 0) + random.randint(-4, 4))); p2 = 100-p1
    g1 = max(0, int((p1-35)/10 + random.randint(0, 2))); g2 = max(0, int((p2-35)/10 + random.randint(0, 2)))
    w = i.user.display_name if g1 > g2 else opponent.display_name if g2 > g1 else "Draw"
    if g1 != g2: balances[i.user.id if g1 > g2 else opponent.id] = bal(i.user.id if g1 > g2 else opponent.id) + 500
    await i.response.send_message(f"🏆 {i.user.display_name} {g1} - {g2} {opponent.display_name}\nPoss: {p1}% - {p2}% | OVR {o1} vs {o2}\nWinner: {w} (+500)")

@bot.event
async def on_ready(): await bot.tree.sync(); print(f"Online {bot.user}")
bot.run(os.getenv("DISCORD_TOKEN") or TOKEN)
