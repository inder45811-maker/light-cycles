"""
Auto-Promotion Engine — generates viral social media posts from battle results.
Twitter, Reddit, Discord formats with stats, emojis, and hooks.
"""

import random
from dataclasses import dataclass


@dataclass
class BattleResult:
    title: str
    mode: str  # tournament, pit, debate, battle
    winner: str
    loser: str | None = None
    score: str = ""
    prize: str = ""
    pnl: str = ""
    trades: int = 0
    turns: int = 0
    tests_passed: str = ""
    verdict: str = ""
    url: str = ""


HOOKS_TWITTER = [
    "The Grid just spoke.",
    "Another program derezzed.",
    "Results are in.",
    "The light cycle trail is still glowing.",
    "A new champion emerges.",
]

HOOKS_REDDIT = [
    "Just ran another battle on the Grid.",
    "Results from the latest Light Cycles showdown:",
    "The arena delivered again.",
    "Update from the agent fighting pit:",
]

VICTORY_PHRASES = [
    "{winner} obliterated {loser}",
    "{winner} came out on top against {loser}",
    "{winner} left {loser} in the dust",
    "{winner} showed {loser} how it's done",
]


def generate_twitter(result: BattleResult) -> str:
    """Generate a tweet-format post."""
    hook = random.choice(HOOKS_TWITTER)

    if result.mode == "tournament":
        body = f"{result.winner} wins the {result.title}! 🏆\n\n"
        if result.prize:
            body += f"💰 Prize: {result.prize}\n"
        if result.tests_passed:
            body += f"📊 {result.tests_passed}\n"

    elif result.mode == "pit":
        body = f"{result.winner} dominated the {result.title} trading floor 📈\n\n"
        if result.pnl:
            body += f"💰 P&L: {result.pnl}\n"
        if result.trades:
            body += f"📊 {result.trades} trades in {result.turns} turns\n"

    elif result.mode == "debate":
        body = f"{result.winner} won the debate on \"{result.title}\" ⚖️\n\n"
        if result.verdict:
            body += f"📝 {result.verdict}\n"

    else:
        body = f"{result.winner} wins the battle ⚔️\n\n"
        if result.score:
            body += f"📊 Score: {result.score}\n"

    post = f"{hook}\n\n{body}\n⚡ Watch agents fight live: {result.url}\n\n#AI #Agents #TRON"
    return post[:280]  # Twitter limit


def generate_reddit(result: BattleResult) -> tuple[str, str]:
    """Generate a Reddit post (title, body)."""
    hook = random.choice(HOOKS_REDDIT)
    victory = random.choice(VICTORY_PHRASES).format(
        winner=f"**{result.winner}**",
        loser=f"**{result.loser or 'the competition'}**",
    )

    title = f"{hook} {result.winner} wins the {result.title}"

    body_parts = [f"{victory} in the latest {result.mode} on [Light Cycles]({result.url})."]
    body_parts.append("")

    if result.mode == "tournament":
        body_parts.append(f"🏆 **Winner:** {result.winner}")
        if result.prize:
            body_parts.append(f"💰 **Prize Pool:** {result.prize}")
        if result.tests_passed:
            body_parts.append(f"📊 **Performance:** {result.tests_passed}")

    elif result.mode == "pit":
        body_parts.append(f"📈 **Winner:** {result.winner}")
        if result.pnl:
            body_parts.append(f"💰 **P&L:** {result.pnl}")
        if result.trades:
            body_parts.append(f"📊 **Stats:** {result.trades} trades over {result.turns} turns")

    elif result.mode == "debate":
        body_parts.append(f"⚖️ **Winner:** {result.winner}")
        if result.verdict:
            body_parts.append(f"📝 **Verdict:** {result.verdict}")

    else:
        body_parts.append(f"⚔️ **Winner:** {result.winner}")
        if result.score:
            body_parts.append(f"📊 **Score:** {result.score}")

    body_parts.append("")
    body_parts.append("---")
    body_parts.append("*Light Cycles — AI agents compete in coding battles, trading pits, and debates. Build your agent and enter the arena.*")

    return title, "\n".join(body_parts)


def generate_discord(result: BattleResult) -> str:
    """Generate a Discord-friendly message."""
    if result.mode == "tournament":
        return (
            f"🏆 **{result.title}**\n"
            f"👑 Winner: **{result.winner}**\n"
            f"💰 Prize: {result.prize}\n"
            f"📊 {result.tests_passed}\n"
            f"🔗 {result.url}"
        )
    elif result.mode == "pit":
        return (
            f"📈 **{result.title}**\n"
            f"👑 Winner: **{result.winner}**\n"
            f"💰 P&L: {result.pnl}\n"
            f"📊 {result.trades} trades | {result.turns} turns\n"
            f"🔗 {result.url}"
        )
    elif result.mode == "debate":
        return (
            f"⚖️ **{result.title}**\n"
            f"👑 Winner: **{result.winner}**\n"
            f"📝 {result.verdict}\n"
            f"🔗 {result.url}"
        )
    else:
        return (
            f"⚔️ **{result.title}**\n"
            f"👑 Winner: **{result.winner}**\n"
            f"📊 Score: {result.score}\n"
            f"🔗 {result.url}"
        )


def generate_all(result: BattleResult) -> dict:
    """Generate posts for all platforms."""
    tweet = generate_twitter(result)
    reddit_title, reddit_body = generate_reddit(result)
    discord = generate_discord(result)
    return {
        "twitter": tweet,
        "reddit_title": reddit_title,
        "reddit_body": reddit_body,
        "discord": discord,
    }


def battle_to_result(battle_data: dict, base_url: str = "https://light-cycleslight-cycles.onrender.com") -> BattleResult:
    """Convert a battle API response to a BattleResult."""
    mode = "battle"
    if battle_data.get("prize_pool_display"):
        mode = "tournament"
    elif battle_data.get("price_history"):
        mode = "pit"
    elif battle_data.get("rounds"):
        mode = "debate"

    winner = battle_data.get("winner") or battle_data.get("winner_name") or "Unknown"
    agents = battle_data.get("agents", [])
    loser = None
    if len(agents) > 1:
        for a in agents:
            if a.get("name") != winner:
                loser = a["name"]
                break

    score = ""
    if battle_data.get("scores"):
        winner_score = next((s for s in battle_data["scores"] if s.get("agent") == winner), None)
        if winner_score:
            score = f"{winner_score['score']}/100 ({winner_score['passed']}/{winner_score['total']} tests)"

    tests_passed = ""
    if battle_data.get("winner_name") and battle_data.get("matches"):
        tests_passed = f"{len(battle_data['matches'])} rounds"

    return BattleResult(
        title=battle_data.get("title", "Battle"),
        mode=mode,
        winner=winner,
        loser=loser,
        score=score,
        prize=battle_data.get("prize_pool_display", ""),
        pnl=battle_data.get("final_scores", {}).get(winner, ""),
        trades=len(battle_data.get("recent_trades", [])),
        turns=battle_data.get("total_turns", 0),
        tests_passed=tests_passed,
        verdict=battle_data.get("verdict", ""),
        url=f"{base_url}",
    )
