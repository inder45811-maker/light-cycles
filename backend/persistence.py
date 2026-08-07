"""
SQLite persistence for Light Cycles.
Stores tournaments, battles, leaderboard — survives server restarts.
"""

import json
import time
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "light_cycles.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection with WAL mode."""
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    """Create tables if they don't exist."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            problem_statement TEXT DEFAULT '',
            entry_fee_cents INTEGER DEFAULT 0,
            player_cap INTEGER DEFAULT 8,
            status TEXT DEFAULT 'upcoming',
            winner_id TEXT,
            current_round INTEGER DEFAULT 0,
            scheduled_at REAL,
            created_at REAL NOT NULL,
            completed_at REAL,
            data_json TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS tournament_players (
            id TEXT PRIMARY KEY,
            tournament_id TEXT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            paid INTEGER DEFAULT 0,
            payment_id TEXT,
            eliminated INTEGER DEFAULT 0,
            seed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tournament_matches (
            id TEXT PRIMARY KEY,
            tournament_id TEXT NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
            round_num INTEGER NOT NULL,
            player1_id TEXT NOT NULL,
            player2_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            winner_id TEXT,
            battle_id TEXT
        );

        CREATE TABLE IF NOT EXISTS battles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'waiting',
            winner TEXT,
            test_cases_json TEXT DEFAULT '[]',
            created_at REAL NOT NULL,
            completed_at REAL
        );

        CREATE TABLE IF NOT EXISTS battle_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id TEXT NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
            agent_name TEXT NOT NULL,
            model TEXT DEFAULT 'default',
            code TEXT DEFAULT '',
            status TEXT DEFAULT 'waiting',
            error TEXT,
            score REAL,
            tests_passed INTEGER DEFAULT 0,
            tests_total INTEGER DEFAULT 0,
            duration_ms REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS leaderboard (
            agent_name TEXT PRIMARY KEY,
            battles INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0,
            avg_score REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    db.commit()
    db.close()


# ── Tournament persistence ──────────────────────────────────────────────

def save_tournament(tournament) -> None:
    """Save or update a tournament to the database."""
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO tournaments (id, title, description, problem_statement,
            entry_fee_cents, player_cap, status, winner_id, current_round,
            scheduled_at, created_at, completed_at, data_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tournament.id, tournament.title, tournament.description,
        tournament.problem_statement, tournament.entry_fee_cents,
        tournament.player_cap, tournament.status.value,
        tournament.winner_id, tournament.current_round,
        tournament.scheduled_at, tournament.created_at,
        tournament.completed_at, json.dumps({})
    ))

    # Save players
    db.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (tournament.id,))
    for pid, player in tournament.players.items():
        db.execute("""
            INSERT INTO tournament_players (id, tournament_id, name, paid, payment_id, eliminated, seed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pid, tournament.id, player.name, int(player.paid),
              player.payment_id, int(player.eliminated), player.seed))

    # Save matches
    db.execute("DELETE FROM tournament_matches WHERE tournament_id = ?", (tournament.id,))
    for match in tournament.matches:
        db.execute("""
            INSERT INTO tournament_matches (id, tournament_id, round_num, player1_id, player2_id, status, winner_id, battle_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (match.id, tournament.id, match.round_num,
              match.player1_id, match.player2_id, match.status.value,
              match.winner_id, match.battle_id))

    db.commit()
    db.close()


def load_tournaments(tournament_manager) -> None:
    """Load all tournaments from DB into the manager."""
    db = get_db()
    rows = db.execute("SELECT * FROM tournaments ORDER BY created_at DESC").fetchall()

    for row in rows:
        from tournament import Tournament, Player, Match, TournamentStatus, MatchStatus

        tournament = Tournament(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            problem_statement=row["problem_statement"] or "",
            test_cases=json.loads(row["data_json"]).get("test_cases", []),
            entry_fee_cents=row["entry_fee_cents"],
            player_cap=row["player_cap"],
            scheduled_at=row["scheduled_at"],
        )
        tournament.status = TournamentStatus(row["status"])
        tournament.winner_id = row["winner_id"]
        tournament.current_round = row["current_round"]
        tournament.created_at = row["created_at"]
        tournament.completed_at = row["completed_at"]

        # Load players
        player_rows = db.execute(
            "SELECT * FROM tournament_players WHERE tournament_id = ? ORDER BY seed",
            (tournament.id,)
        ).fetchall()
        for pr in player_rows:
            player = Player(
                id=pr["id"], name=pr["name"], paid=bool(pr["paid"]),
                payment_id=pr["payment_id"], eliminated=bool(pr["eliminated"]),
                seed=pr["seed"]
            )
            tournament.players[pr["id"]] = player

        # Load matches
        match_rows = db.execute(
            "SELECT * FROM tournament_matches WHERE tournament_id = ? ORDER BY round_num",
            (tournament.id,)
        ).fetchall()
        for mr in match_rows:
            match = Match(
                id=mr["id"], round_num=mr["round_num"],
                player1_id=mr["player1_id"], player2_id=mr["player2_id"],
                status=MatchStatus(mr["status"]),
                winner_id=mr["winner_id"], battle_id=mr["battle_id"]
            )
            tournament.matches.append(match)

        tournament_manager.tournaments[tournament.id] = tournament
        # Update counter to avoid ID collisions
        num = int(tournament.id.split("-")[1])
        if num > tournament_manager._counter:
            tournament_manager._counter = num

    db.close()


# ── Battle persistence ─────────────────────────────────────────────────

def save_battle(battle) -> None:
    """Save a battle to the database."""
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO battles (id, title, description, status, winner, test_cases_json, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (battle.id, battle.title, battle.description, battle.status.value,
          battle.winner, json.dumps(battle.test_cases),
          battle.created_at, battle.completed_at))

    # Save agents
    db.execute("DELETE FROM battle_agents WHERE battle_id = ?", (battle.id,))
    for agent in battle.agents:
        db.execute("""
            INSERT INTO battle_agents (battle_id, agent_name, model, code, status, error, score, tests_passed, tests_total, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (battle.id, agent.agent_name, agent.model, agent.code,
              agent.status, agent.error,
              agent.score.score if agent.score else None,
              agent.score.tests_passed if agent.score else 0,
              agent.score.tests_total if agent.score else 0,
              agent.score.total_duration_ms if agent.score else 0))

    db.commit()
    db.close()


def load_battles(arena) -> None:
    """Load all battles from DB into the arena."""
    db = get_db()
    rows = db.execute("SELECT * FROM battles ORDER BY created_at DESC").fetchall()

    for row in rows:
        from arena import Battle, AgentSubmission, BattleStatus

        battle = Battle(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            test_cases=json.loads(row["test_cases_json"]),
            agents=[],
        )
        battle.status = BattleStatus(row["status"])
        battle.winner = row["winner"]
        battle.created_at = row["created_at"]
        battle.completed_at = row["completed_at"]

        # Load agents
        agent_rows = db.execute(
            "SELECT * FROM battle_agents WHERE battle_id = ?", (battle.id,)
        ).fetchall()
        for ar in agent_rows:
            from arena import Score
            agent = AgentSubmission(
                agent_name=ar["agent_name"],
                model=ar["model"],
                code=ar["code"] or "",
                status=ar["status"],
                error=ar["error"],
            )
            if ar["score"] is not None:
                agent.score = Score(
                    agent_name=ar["agent_name"],
                    tests_passed=ar["tests_passed"],
                    tests_total=ar["tests_total"],
                    total_duration_ms=ar["duration_ms"],
                    max_memory_kb=0,
                )
            battle.agents.append(agent)

        arena.battles[battle.id] = battle
        num = int(battle.id.split("-")[1])
        if num > arena._counter:
            arena._counter = num

    db.close()


# ── Leaderboard persistence ────────────────────────────────────────────

def save_leaderboard_entry(agent_name: str, battles: int, wins: int, total_score: float, avg_score: float):
    """Save or update a leaderboard entry."""
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO leaderboard (agent_name, battles, wins, total_score, avg_score)
        VALUES (?, ?, ?, ?, ?)
    """, (agent_name, battles, wins, total_score, avg_score))
    db.commit()
    db.close()


def update_leaderboard(arena) -> None:
    """Rebuild leaderboard from all battles and persist."""
    lb = arena.get_leaderboard()
    db = get_db()
    db.execute("DELETE FROM leaderboard")
    for entry in lb:
        db.execute("""
            INSERT INTO leaderboard (agent_name, battles, wins, total_score, avg_score)
            VALUES (?, ?, ?, ?, ?)
        """, (entry["name"], entry["battles"], entry["wins"],
              entry["total_score"], entry["avg_score"]))
    db.commit()
    db.close()


def load_leaderboard() -> list[dict]:
    """Load the leaderboard from DB."""
    db = get_db()
    rows = db.execute("SELECT * FROM leaderboard ORDER BY wins DESC, avg_score DESC").fetchall()
    result = [dict(r) for r in rows]
    db.close()
    return result


# ── Auto-persist hooks ─────────────────────────────────────────────────

class PersistenceHooks:
    """Hooks that auto-persist whenever state changes."""

    @staticmethod
    def after_tournament_change(tournament):
        save_tournament(tournament)

    @staticmethod
    def after_battle_change(battle, arena=None):
        save_battle(battle)
        if arena:
            update_leaderboard(arena)


# Initialize the database on import
init_db()
