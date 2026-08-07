"""
Arena: battle engine that pits AI agents against each other.
Spawns Hermes subagents, collects code submissions, runs judging.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum

from judge import Judge, Score, TestResult


class BattleStatus(Enum):
    WAITING = "waiting"
    CODING = "coding"       # agents are writing code
    JUDGING = "judging"    # running test cases
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentSubmission:
    agent_name: str
    model: str
    code: str = ""
    status: str = "waiting"  # waiting | coding | submitted | error
    error: str | None = None
    score: Score | None = None


@dataclass
class Battle:
    id: str
    title: str
    description: str
    test_cases: list[dict]
    agents: list[AgentSubmission]
    status: BattleStatus = BattleStatus.WAITING
    winner: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    scores: list[Score] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "winner": self.winner,
            "agents": [
                {
                    "name": a.agent_name,
                    "model": a.model,
                    "status": a.status,
                    "error": a.error,
                    "score": {
                        "score": a.score.score,
                        "tests_passed": a.score.tests_passed,
                        "tests_total": a.score.tests_total,
                        "duration_ms": a.score.total_duration_ms,
                        "errors": a.score.errors,
                    } if a.score else None,
                }
                for a in self.agents
            ],
            "scores": [
                {
                    "agent": s.agent_name,
                    "score": s.score,
                    "passed": s.tests_passed,
                    "total": s.tests_total,
                    "duration_ms": s.total_duration_ms,
                }
                for s in self.scores
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class Arena:
    """Manages battles — creation, execution, judging."""

    def __init__(self, hermes_api_base: str | None = None):
        self.battles: dict[str, Battle] = {}
        self.judge = Judge()
        self._counter = 0

    def create_battle(
        self,
        title: str,
        description: str,
        test_cases: list[dict],
        agents: list[dict],
    ) -> Battle:
        """Create a new battle."""
        self._counter += 1
        battle_id = f"battle-{self._counter:04d}"

        agent_subs = [
            AgentSubmission(
                agent_name=a["name"],
                model=a.get("model", "default"),
            )
            for a in agents
        ]

        battle = Battle(
            id=battle_id,
            title=title,
            description=description,
            test_cases=test_cases,
            agents=agent_subs,
        )
        self.battles[battle_id] = battle
        return battle

    def submit_code(self, battle_id: str, agent_name: str, code: str, error: str | None = None):
        """Record an agent's code submission."""
        battle = self.battles.get(battle_id)
        if not battle:
            return

        for agent in battle.agents:
            if agent.agent_name == agent_name:
                if error:
                    agent.code = ""
                    agent.status = "error"
                    agent.error = error
                else:
                    agent.code = code
                    agent.status = "submitted"
                break

    def run_judging(self, battle_id: str) -> Battle:
        """Score all submissions and determine winner."""
        battle = self.battles.get(battle_id)
        if not battle:
            raise ValueError(f"Battle {battle_id} not found")

        battle.status = BattleStatus.JUDGING
        battle.scores = []

        for agent in battle.agents:
            if agent.status == "submitted" and agent.code:
                score = self.judge.score_submission(
                    agent.agent_name, agent.code, battle.test_cases
                )
                agent.score = score
                battle.scores.append(score)
            elif agent.status == "error":
                battle.scores.append(Score(
                    agent_name=agent.agent_name,
                    tests_passed=0,
                    tests_total=len(battle.test_cases),
                    total_duration_ms=0,
                    max_memory_kb=0,
                    errors=[agent.error or "Unknown error"],
                ))

        # Determine winner
        if battle.scores:
            battle.scores.sort(key=lambda s: s.score, reverse=True)
            battle.winner = battle.scores[0].agent_name

        battle.status = BattleStatus.COMPLETE
        battle.completed_at = time.time()
        return battle

    def get_battle(self, battle_id: str) -> Battle | None:
        return self.battles.get(battle_id)

    def list_battles(self) -> list[dict]:
        return [b.to_dict() for b in self.battles.values()]

    def get_leaderboard(self) -> list[dict]:
        """Aggregate scores across all completed battles."""
        agent_stats: dict[str, dict] = {}

        for battle in self.battles.values():
            if battle.status != BattleStatus.COMPLETE:
                continue
            for score in battle.scores:
                name = score.agent_name
                if name not in agent_stats:
                    agent_stats[name] = {
                        "name": name,
                        "battles": 0,
                        "wins": 0,
                        "total_score": 0.0,
                        "avg_score": 0.0,
                    }
                stats = agent_stats[name]
                stats["battles"] += 1
                stats["total_score"] += score.score
                if battle.winner == name:
                    stats["wins"] += 1

        for stats in agent_stats.values():
            if stats["battles"] > 0:
                stats["avg_score"] = round(stats["total_score"] / stats["battles"], 1)

        return sorted(agent_stats.values(), key=lambda s: s["wins"], reverse=True)
