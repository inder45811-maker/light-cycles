"""
Trading Pit — AI agents compete in simulated financial markets.
Multi-turn decision making, P&L scoring, real-time price feeds.
"""

import json
import time
import math
import random
import threading
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PitStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETE = "complete"


@dataclass
class Trade:
    turn: int
    agent_name: str
    action: str  # buy, sell, hold
    amount: float  # in units of the asset
    price: float
    pnl: float = 0.0


@dataclass
class AgentPosition:
    agent_name: str
    cash: float
    units: float = 0.0
    trades: list[Trade] = field(default_factory=list)
    pnl_history: list[float] = field(default_factory=list)

    @property
    def total_value(self) -> float:
        return self.cash + self.units * self._last_price

    _last_price: float = 0.0


@dataclass
class MarketState:
    turn: int
    price: float
    volume: float
    bid: float
    ask: float
    high_24h: float
    low_24h: float
    change_24h: float


@dataclass
class TradingPit:
    id: str
    title: str
    asset_name: str
    agents: list[str]
    starting_capital: float = 10000.0
    total_turns: int = 60       # 60 turns = ~5 min at 5s per turn
    volatility: float = 0.02    # 2% price moves per turn
    starting_price: float = 100.0
    drift: float = 0.0          # bullish/bearish bias

    # Runtime state
    status: PitStatus = PitStatus.WAITING
    current_turn: int = 0
    positions: dict[str, AgentPosition] = field(default_factory=dict)
    price_history: list[float] = field(default_factory=list)
    market_history: list[MarketState] = field(default_factory=list)
    all_trades: list[Trade] = field(default_factory=list)
    winner: str | None = None
    final_scores: dict[str, float] = field(default_factory=dict)

    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def init_positions(self):
        """Set up starting positions for all agents."""
        self.price_history = [self.starting_price]
        for name in self.agents:
            self.positions[name] = AgentPosition(
                agent_name=name,
                cash=self.starting_capital,
            )

    def simulate_price(self) -> float:
        """Geometric Brownian motion — random walk with drift."""
        last = self.price_history[-1]
        shock = random.gauss(0, 1)  # standard normal
        change = math.exp(
            (self.drift - 0.5 * self.volatility ** 2) * (1 / self.total_turns)
            + self.volatility * math.sqrt(1 / self.total_turns) * shock
        )
        return max(0.01, last * change)

    def get_market_state(self) -> MarketState:
        """Build current market snapshot for agents."""
        price = self.price_history[-1]
        spread = price * 0.001  # 0.1% spread

        if len(self.price_history) >= 24:
            window = self.price_history[-24:]
        else:
            window = self.price_history

        return MarketState(
            turn=self.current_turn,
            price=round(price, 2),
            volume=random.uniform(100, 1000),
            bid=round(price - spread / 2, 2),
            ask=round(price + spread / 2, 2),
            high_24h=round(max(window), 2),
            low_24h=round(min(window), 2),
            change_24h=round(((price / self.starting_price) - 1) * 100, 2),
        )

    def execute_trade(self, agent_name: str, action: str, amount: float = 0) -> Trade:
        """Execute a buy/sell/hold and update the agent's position."""
        pos = self.positions[agent_name]
        price = self.price_history[-1]
        trade = Trade(turn=self.current_turn, agent_name=agent_name, action=action, amount=0, price=price)

        if action == "buy" and amount > 0:
            cost = amount * price
            if cost <= pos.cash:
                pos.cash -= cost
                pos.units += amount

        elif action == "sell" and amount > 0:
            if amount <= pos.units:
                revenue = amount * price
                pos.cash += revenue
                pos.units -= amount

        elif action == "sell" and amount == 0:
            # Sell all
            if pos.units > 0:
                pos.cash += pos.units * price
                pos.units = 0

        trade.amount = amount if action in ("buy", "sell") else 0
        pos.trades.append(trade)
        pos._last_price = price
        return trade

    def calculate_pnl(self, agent_name: str) -> float:
        """Current unrealized P&L for an agent."""
        pos = self.positions[agent_name]
        current = self.price_history[-1]
        return pos.cash + pos.units * current - self.starting_capital

    def run_turn(self) -> dict:
        """Advance one turn: update price, get agent decisions, execute."""
        self.current_turn += 1
        new_price = self.simulate_price()
        self.price_history.append(new_price)
        state = self.get_market_state()
        self.market_history.append(state)

        return {
            "turn": self.current_turn,
            "price": state.price,
            "change": round(((new_price / self.price_history[-2]) - 1) * 100, 3) if len(self.price_history) > 1 else 0,
            "volume": state.volume,
        }

    def decide_for_agent(self, agent_name: str, market: MarketState, position: AgentPosition) -> tuple[str, float]:
        """Get an AI agent's trading decision. Uses the configured LLM."""
        from api_resolver import call_llm, get_api_config

        config = get_api_config()

        system = f"""You are {agent_name}, an AI trader competing in a simulated market.
You manage ${position.cash:.2f} cash and hold {position.units:.4f} units of the asset.
Your total portfolio value is ${position.cash + position.units * market.price:.2f}.
Starting capital was $10000. Your current P&L is ${position.cash + position.units * market.price - 10000:.2f}.

Market data:
- Current price: ${market.price}
- Bid/Ask: ${market.bid} / ${market.ask}
- 24h high/low: ${market.high_24h} / ${market.low_24h}
- 24h change: {market.change_24h}%
- Volume: {market.volume}
- Turn: {market.turn}

Recent trades you made:
{[f'T{t.turn}: {t.action.upper()} {t.amount:.2f} @ ${t.price}' for t in position.trades[-5:]]}

Respond with ONLY a JSON object:
{{"action": "buy"|"sell"|"hold", "amount": number, "reasoning": "one sentence"}}

For "buy" or "sell", amount is how many units to trade.
For "sell" with amount=0, it means sell ALL.
For "hold", amount is ignored.

Be strategic. Don't just hold every turn. Trade when you see opportunity."""

        user = f"Turn {market.turn}/{self.total_turns}. Current price ${market.price}. Your decision:"

        if not config["api_key"]:
            return self._mock_decision(agent_name, market, position)

        try:
            response = call_llm(system, user, temperature=0.4, max_tokens=200)
            # Extract JSON
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                action = data.get("action", "hold")
                amount = float(data.get("amount", 0))
                if action not in ("buy", "sell", "hold"):
                    action = "hold"
                return action, amount
        except Exception:
            pass

        return self._mock_decision(agent_name, market, position)

    def _mock_decision(self, agent_name: str, market: MarketState, position: AgentPosition) -> tuple[str, float]:
        """Heuristic agent with varied strategies. More aggressive now."""
        rng = random.Random(f"{agent_name}-{market.turn}")
        pnl = position.cash + position.units * market.price - self.starting_capital
        pnl_pct = pnl / self.starting_capital
        total = position.cash + position.units * market.price

        # Personality from agent name hash
        seed = sum(ord(c) for c in agent_name) % 4

        if seed == 0:
            # Aggressive scalper — trades frequently, small positions
            if rng.random() < 0.7:  # 70% chance to act each turn
                if rng.random() < 0.5 and position.cash > 500:
                    amt = min(position.cash * rng.uniform(0.1, 0.4) / market.price, 15)
                    return ("buy", round(amt, 2))
                elif position.units > 0:
                    amt = position.units * rng.uniform(0.2, 0.8)
                    return ("sell", round(amt, 2))

        elif seed == 1:
            # Momentum trader — follows trends, bigger bets
            if len(self.price_history) >= 5:
                trend = (self.price_history[-1] / self.price_history[-5] - 1) * 100
                if trend > 0.5 and position.cash > 1000:
                    amt = min(position.cash * rng.uniform(0.2, 0.6) / market.price, 20)
                    return ("buy", round(amt, 2))
                elif trend < -0.5 and position.units > 0:
                    return ("sell", round(position.units * rng.uniform(0.4, 1.0), 2))

        elif seed == 2:
            # Value investor — buys dips, sells rips
            if len(self.price_history) >= 10:
                avg = sum(self.price_history[-10:]) / 10
                deviation = (market.price / avg - 1) * 100
                if deviation < -2 and position.cash > 2000:
                    amt = min(position.cash * rng.uniform(0.3, 0.7) / market.price, 25)
                    return ("buy", round(amt, 2))
                elif deviation > 3 and position.units > 0:
                    return ("sell", round(position.units * rng.uniform(0.5, 1.0), 2))

        else:
            # Risk manager — tight stop-losses, takes profit early
            if position.units > 0:
                entry_price = position.trades[-1].price if position.trades else market.price
                change = (market.price / entry_price - 1) * 100
                if change > 2:  # take profit
                    return ("sell", round(position.units * rng.uniform(0.3, 0.7), 2))
                elif change < -1.5:  # stop loss
                    return ("sell", 0)  # sell all
            elif position.cash > 5000 and rng.random() < 0.3:
                amt = min(position.cash * 0.2 / market.price, 10)
                return ("buy", round(amt, 2))

        return ("hold", 0)

    def get_pit_state(self) -> dict:
        """Full state for the frontend."""
        return {
            "id": self.id,
            "title": self.title,
            "asset_name": self.asset_name,
            "agents": self.agents,
            "starting_capital": self.starting_capital,
            "total_turns": self.total_turns,
            "status": self.status.value,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "final_scores": self.final_scores,
            "price_history": [round(p, 2) for p in self.price_history],
            "positions": {
                name: {
                    "cash": round(pos.cash, 2),
                    "units": round(pos.units, 4),
                    "total_value": round(pos.cash + pos.units * (self.price_history[-1] if self.price_history else 0), 2),
                    "pnl": round(pos.cash + pos.units * (self.price_history[-1] if self.price_history else 0) - self.starting_capital, 2),
                    "pnl_pct": round((pos.cash + pos.units * (self.price_history[-1] if self.price_history else 0) - self.starting_capital) / self.starting_capital * 100, 2),
                    "trade_count": len(pos.trades),
                    "pnl_history": [round(p, 2) for p in pos.pnl_history[-100:]],
                }
                for name, pos in self.positions.items()
            },
            "recent_trades": [
                {"turn": t.turn, "agent": t.agent_name, "action": t.action, "amount": round(t.amount, 4), "price": round(t.price, 2)}
                for t in self.all_trades[-20:]
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    def to_dict(self) -> dict:
        return self.get_pit_state()


class PitArena:
    """Manages trading pits — creation, execution, results."""

    def __init__(self):
        self.pits: dict[str, TradingPit] = {}
        self._counter = 0

    def create_pit(
        self,
        title: str,
        asset_name: str,
        agents: list[str],
        starting_capital: float = 10000,
        total_turns: int = 60,
        volatility: float = 0.02,
        drift: float = 0.0,
    ) -> TradingPit:
        self._counter += 1
        pit = TradingPit(
            id=f"pit-{self._counter:04d}",
            title=title,
            asset_name=asset_name,
            agents=agents,
            starting_capital=starting_capital,
            total_turns=total_turns,
            volatility=volatility,
            drift=drift,
        )
        pit.init_positions()
        self.pits[pit.id] = pit
        return pit

    def get_pit(self, pit_id: str) -> TradingPit | None:
        return self.pits.get(pit_id)

    def list_pits(self) -> list[dict]:
        return [p.to_dict() for p in sorted(self.pits.values(), key=lambda x: x.created_at, reverse=True)]

    def run_pit(self, pit_id: str, on_turn=None):
        """Run the full pit simulation in a background thread. Calls on_turn(turn_data) each tick."""
        pit = self.pits.get(pit_id)
        if not pit:
            return

        pit.status = PitStatus.RUNNING

        def run():
            for _ in range(pit.total_turns):
                turn_data = pit.run_turn()
                market = pit.market_history[-1]

                # Get decisions from all agents
                turn_trades = []
                for agent_name in pit.agents:
                    pos = pit.positions[agent_name]
                    action, amount = pit.decide_for_agent(agent_name, market, pos)
                    trade = pit.execute_trade(agent_name, action, amount)
                    turn_trades.append(trade)
                pit.all_trades.extend(turn_trades)

                # Update P&L history
                for agent_name in pit.agents:
                    pos = pit.positions[agent_name]
                    pnl = pos.cash + pos.units * pit.price_history[-1] - pit.starting_capital
                    pos.pnl_history.append(round(pnl, 2))

                # Build turn event
                event = {
                    "turn": turn_data["turn"],
                    "price": turn_data["price"],
                    "change": turn_data["change"],
                    "trades": [
                        {"agent": t.agent_name, "action": t.action, "amount": round(t.amount, 4)}
                        for t in turn_trades
                    ],
                    "positions": {
                        name: {
                            "pnl": round(pit.positions[name].cash + pit.positions[name].units * pit.price_history[-1] - pit.starting_capital, 2),
                            "pnl_pct": round((pit.positions[name].cash + pit.positions[name].units * pit.price_history[-1] - pit.starting_capital) / pit.starting_capital * 100, 2),
                        }
                        for name in pit.agents
                    },
                }

                if on_turn:
                    on_turn(event)

                time.sleep(2)  # 2 seconds between turns for spectator effect

            # Determine winner
            final_pnls = {}
            for agent_name in pit.agents:
                pos = pit.positions[agent_name]
                final_pnl = pos.cash + pos.units * pit.price_history[-1] - pit.starting_capital
                final_pnls[agent_name] = round(final_pnl, 2)

            pit.final_scores = final_pnls
            pit.winner = max(final_pnls, key=final_pnls.get) if final_pnls else None
            pit.status = PitStatus.COMPLETE
            pit.completed_at = time.time()

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread


# Singleton
pit_arena = PitArena()
