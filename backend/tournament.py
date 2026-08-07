"""
Tournament engine: entry fees, prize pools, bracketing, scheduling.
Plugged into the Arena — players pay, compete, winner takes the pot.
"""

import time
import uuid
import hashlib
import hmac
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TournamentStatus(Enum):
    UPCOMING = "upcoming"     # open for registration
    REGISTERING = "registering"  # same as upcoming, kept for clarity
    FULL = "full"             # player cap hit
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class MatchStatus(Enum):
    PENDING = "pending"
    LIVE = "live"
    COMPLETE = "complete"


@dataclass
class Player:
    id: str
    name: str
    paid: bool = False
    payment_id: str | None = None
    eliminated: bool = False
    seed: int = 0


@dataclass
class Match:
    id: str
    round_num: int
    player1_id: str
    player2_id: str
    status: MatchStatus = MatchStatus.PENDING
    winner_id: str | None = None
    battle_id: str | None = None  # linked Arena battle


@dataclass
class Tournament:
    id: str
    title: str
    description: str
    problem_statement: str
    test_cases: list[dict]
    entry_fee_cents: int         # in cents (Stripe convention)
    prize_pool_cents: int = 0    # computed: entry_fee * player_count * 0.85
    platform_fee_cents: int = 0  # computed: entry_fee * player_count * 0.15
    player_cap: int = 8
    players: dict[str, Player] = field(default_factory=dict)
    matches: list[Match] = field(default_factory=list)
    status: TournamentStatus = TournamentStatus.UPCOMING
    winner_id: str | None = None
    current_round: int = 0
    scheduled_at: float | None = None    # unix timestamp
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    ROUND_NAMES = {1: "ROUND 1", 2: "QUARTER-FINALS", 3: "SEMI-FINALS", 4: "FINAL", 5: "GRAND FINAL"}

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def paid_count(self) -> int:
        return sum(1 for p in self.players.values() if p.paid)

    @property
    def total_rounds(self) -> int:
        """Number of rounds needed for this many players."""
        count = self.player_count or self.player_cap
        rounds = 0
        while count > 1:
            count //= 2
            rounds += 1
        return max(rounds, 1)

    def add_player(self, name: str) -> Player:
        """Register a player. Returns the player."""
        pid = f"player-{len(self.players)+1:03d}"
        player = Player(id=pid, name=name, seed=len(self.players)+1)
        self.players[pid] = player

        if self.player_count >= self.player_cap:
            self.status = TournamentStatus.FULL

        return player

    def confirm_payment(self, player_id: str, payment_id: str):
        """Mark a player as paid."""
        player = self.players.get(player_id)
        if player:
            player.paid = True
            player.payment_id = payment_id

        # Recalculate prize pool
        paid = self.paid_count
        total = self.entry_fee_cents * paid
        self.platform_fee_cents = int(total * 0.15)
        self.prize_pool_cents = total - self.platform_fee_cents

    def generate_bracket(self):
        """Generate single-elimination bracket from paid players."""
        paid_players = [p for p in self.players.values() if p.paid]
        if len(paid_players) < 2:
            return

        # Sort by seed
        paid_players.sort(key=lambda p: p.seed)

        # First round pairings: standard bracket (1 vs N, 2 vs N-1, ...)
        n = len(paid_players)
        round_num = 1
        self.matches = []

        for i in range(n // 2):
            p1 = paid_players[i]
            p2 = paid_players[n - 1 - i]
            match = Match(
                id=f"match-{round_num}-{i+1:02d}",
                round_num=round_num,
                player1_id=p1.id,
                player2_id=p2.id,
            )
            self.matches.append(match)

        self.current_round = 1
        self.status = TournamentStatus.IN_PROGRESS

    def get_current_matches(self) -> list[Match]:
        """Get matches for the current round."""
        return [m for m in self.matches if m.round_num == self.current_round and m.status != MatchStatus.COMPLETE]

    def report_match_result(self, match_id: str, winner_id: str, battle_id: str | None = None):
        """Record a match result and advance the bracket."""
        for match in self.matches:
            if match.id == match_id:
                match.status = MatchStatus.COMPLETE
                match.winner_id = winner_id
                match.battle_id = battle_id
                break

        # Mark loser as eliminated
        for match in self.matches:
            if match.id == match_id:
                loser = match.player1_id if match.player1_id != winner_id else match.player2_id
                if loser in self.players:
                    self.players[loser].eliminated = True
                break

        # Check if round is complete
        current_matches = [m for m in self.matches if m.round_num == self.current_round]
        if all(m.status == MatchStatus.COMPLETE for m in current_matches):
            winners = [m.winner_id for m in current_matches if m.winner_id]

            if len(winners) == 1:
                # Tournament over
                self.winner_id = winners[0]
                self.status = TournamentStatus.COMPLETE
                self.completed_at = time.time()
            else:
                # Generate next round
                self.current_round += 1
                round_num = self.current_round
                for i in range(0, len(winners), 2):
                    if i + 1 < len(winners):
                        match = Match(
                            id=f"match-{round_num}-{i//2+1:02d}",
                            round_num=round_num,
                            player1_id=winners[i],
                            player2_id=winners[i+1],
                        )
                        self.matches.append(match)

    def get_round_name(self) -> str:
        """Get the display name for the current round."""
        remaining_rounds = self.total_rounds - self.current_round + 1
        if remaining_rounds <= 1:
            return "FINAL"
        if remaining_rounds <= 2:
            return "SEMI-FINALS"
        return self.ROUND_NAMES.get(self.current_round, f"ROUND {self.current_round}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "problem_statement": self.problem_statement,
            "entry_fee_cents": self.entry_fee_cents,
            "entry_fee_display": f"${self.entry_fee_cents / 100:.2f}",
            "prize_pool_cents": self.prize_pool_cents,
            "prize_pool_display": f"${self.prize_pool_cents / 100:.2f}",
            "platform_fee_cents": self.platform_fee_cents,
            "platform_fee_display": f"${self.platform_fee_cents / 100:.2f}",
            "player_cap": self.player_cap,
            "player_count": self.player_count,
            "paid_count": self.paid_count,
            "status": self.status.value,
            "winner_id": self.winner_id,
            "winner_name": self.players[self.winner_id].name if self.winner_id in self.players else None,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "round_name": self.get_round_name(),
            "players": [
                {"id": p.id, "name": p.name, "paid": p.paid, "eliminated": p.eliminated, "seed": p.seed}
                for p in sorted(self.players.values(), key=lambda x: x.seed)
            ],
            "matches": [
                {
                    "id": m.id,
                    "round": m.round_num,
                    "round_name": self.ROUND_NAMES.get(m.round_num, f"ROUND {m.round_num}"),
                    "player1": self.players[m.player1_id].name if m.player1_id in self.players else "???",
                    "player2": self.players[m.player2_id].name if m.player2_id in self.players else "???",
                    "status": m.status.value,
                    "winner": self.players[m.winner_id].name if m.winner_id and m.winner_id in self.players else None,
                    "battle_id": m.battle_id,
                }
                for m in self.matches
            ],
            "scheduled_at": self.scheduled_at,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class TournamentManager:
    """Manages tournaments — creation, registration, bracketing, payouts."""

    def __init__(self, stripe_secret: str | None = None, stripe_webhook_secret: str | None = None):
        self.tournaments: dict[str, Tournament] = {}
        self._counter = 0
        self.stripe_secret = stripe_secret
        self.stripe_webhook_secret = stripe_webhook_secret

    def create_tournament(
        self,
        title: str,
        description: str,
        problem_statement: str,
        test_cases: list[dict],
        entry_fee_cents: int,
        player_cap: int = 8,
        scheduled_at: float | None = None,
    ) -> Tournament:
        self._counter += 1
        tid = f"tourney-{self._counter:04d}"

        tournament = Tournament(
            id=tid,
            title=title,
            description=description,
            problem_statement=problem_statement,
            test_cases=test_cases,
            entry_fee_cents=entry_fee_cents,
            player_cap=player_cap,
            scheduled_at=scheduled_at,
        )
        self.tournaments[tid] = tournament
        return tournament

    def get_tournament(self, tid: str) -> Tournament | None:
        return self.tournaments.get(tid)

    def list_tournaments(self, status: str | None = None) -> list[dict]:
        result = list(self.tournaments.values())
        if status:
            result = [t for t in result if t.status.value == status]
        return [t.to_dict() for t in sorted(result, key=lambda x: x.created_at, reverse=True)]

    def create_stripe_checkout_session(
        self, tournament_id: str, player_id: str, success_url: str, cancel_url: str
    ) -> dict | None:
        """Create a Stripe Checkout session for tournament entry."""
        if not self.stripe_secret:
            return None

        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return None

        try:
            import stripe
            stripe.api_key = self.stripe_secret

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Light Cycles: {tournament.title}",
                            "description": f"Entry fee — {tournament.player_cap}-player tournament",
                        },
                        "unit_amount": tournament.entry_fee_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&tournament={tournament_id}&player={player_id}",
                cancel_url=cancel_url,
                metadata={
                    "tournament_id": tournament_id,
                    "player_id": player_id,
                },
            )
            return {"url": session.url, "session_id": session.id}
        except ImportError:
            return {"error": "stripe package not installed"}
        except Exception as e:
            return {"error": str(e)}

    def verify_stripe_webhook(self, payload: bytes, sig_header: str) -> dict | None:
        """Verify Stripe webhook signature and return the event."""
        if not self.stripe_webhook_secret:
            return None

        try:
            import stripe
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
            return event
        except Exception:
            return None

    def handle_payment_success(self, tournament_id: str, player_id: str, payment_id: str):
        """Handle successful payment — mark player as paid."""
        tournament = self.tournaments.get(tournament_id)
        if tournament:
            tournament.confirm_payment(player_id, payment_id)

    def start_tournament(self, tournament_id: str) -> Tournament | None:
        """Generate bracket and start the tournament."""
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            return None
        if tournament.paid_count < 2:
            return None

        tournament.generate_bracket()
        return tournament

    def get_active_tournament_matches(self) -> list[dict]:
        """Get all pending/live matches from active tournaments for the Arena."""
        matches = []
        for t in self.tournaments.values():
            if t.status == TournamentStatus.IN_PROGRESS:
                for m in t.get_current_matches():
                    if m.status == MatchStatus.PENDING:
                        p1 = t.players.get(m.player1_id)
                        p2 = t.players.get(m.player2_id)
                        if p1 and p2:
                            matches.append({
                                "match_id": m.id,
                                "tournament_id": t.id,
                                "tournament_title": t.title,
                                "round": t.current_round,
                                "round_name": t.get_round_name(),
                                "player1": p1.name,
                                "player2": p2.name,
                                "test_cases": t.test_cases,
                                "problem_statement": t.problem_statement,
                            })
        return matches
