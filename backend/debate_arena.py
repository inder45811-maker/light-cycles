"""
Debate Arena — AI agents face off in structured debates.
LLM judge scores arguments on logic, rhetoric, and evidence.
"""

import json
import time
import threading
import urllib.request
from dataclasses import dataclass, field
from enum import Enum


class DebateStatus(Enum):
    WAITING = "waiting"
    ARGUING = "arguing"
    JUDGING = "judging"
    COMPLETE = "complete"


@dataclass
class DebateRound:
    round_num: int
    speaker: str  # who is speaking
    content: str = ""
    judge_score: float | None = None
    judge_feedback: str = ""


@dataclass
class Debate:
    id: str
    topic: str
    position_for: str  # agent arguing FOR
    position_against: str  # agent arguing AGAINST
    rounds: list[DebateRound] = field(default_factory=list)
    status: DebateStatus = DebateStatus.WAITING
    winner: str | None = None
    final_scores: dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "position_for": self.position_for,
            "position_against": self.position_against,
            "rounds": [
                {
                    "round": r.round_num,
                    "speaker": r.speaker,
                    "content": r.content,
                    "judge_score": r.judge_score,
                    "judge_feedback": r.judge_feedback,
                }
                for r in self.rounds
            ],
            "status": self.status.value,
            "winner": self.winner,
            "final_scores": self.final_scores,
            "created_at": self.created_at,
        }


class DebateJudge:
    """LLM-based judge that scores debate arguments."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"

    def _call_llm(self, system: str, user: str, model: str = "gpt-4o") -> str:
        """Call the configured LLM. Auto-detects DeepSeek/OpenAI."""
        from api_resolver import call_llm, get_api_config

        config = get_api_config()
        if not config["api_key"]:
            return self._mock_judge(user)

        try:
            return call_llm(system, user, temperature=0.5, max_tokens=1000)
        except Exception:
            return self._mock_judge(user)

    def _mock_judge(self, text: str) -> str:
        """Fallback judge when no API key is configured. Scores with heuristic variety."""
        import random, hashlib

        # Seed from the text so the same argument always gets the same score
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        words = len(text.split())
        has_evidence = any(kw in text.lower() for kw in ["because", "therefore", "evidence", "data", "study", "research"])
        has_structure = any(kw in text.lower() for kw in ["first", "second", "finally", "moreover", "however", "conclusion"])

        base = 5.0
        if words > 100: base += rng.uniform(0.5, 1.5)
        if words > 200: base += rng.uniform(0.3, 0.8)
        if has_evidence: base += rng.uniform(1.0, 2.0)
        if has_structure: base += rng.uniform(0.5, 1.5)
        base += rng.uniform(-0.5, 0.5)  # natural variation

        score = round(min(10.0, max(1.0, base)), 1)

        feedbacks = [
            "Strong logical flow with clear reasoning.",
            "Good use of evidence but could be more persuasive.",
            "Solid argument, though some points need more support.",
            "Well-structured with compelling points.",
            "Decent argument but lacks concrete examples.",
            "Clear and concise with effective rhetoric.",
        ]

        return json.dumps({
            "score": score,
            "logic": round(score * 0.85, 1),
            "rhetoric": round(score * 0.75, 1),
            "evidence": round(score * 0.65 if has_evidence else score * 0.4, 1),
            "feedback": rng.choice(feedbacks),
        })

    def score_argument(self, topic: str, position: str, argument: str, opponent_argument: str = "") -> dict:
        """Score a single debate argument. Returns {score, logic, rhetoric, evidence, feedback}."""
        system = """You are an impartial debate judge. Score arguments on three criteria:
1. LOGIC (1-10): Sound reasoning, no fallacies
2. RHETORIC (1-10): Persuasiveness, clarity, style
3. EVIDENCE (1-10): Use of facts, examples, data

Also provide an OVERALL score (1-10) and ONE LINE of constructive feedback.
Respond ONLY with a JSON object: {"score": X, "logic": X, "rhetoric": X, "evidence": X, "feedback": "..."}"""

        opponent_context = f"\n\nOPPONENT'S ARGUMENT:\n{opponent_argument}" if opponent_argument else ""
        user = f"""TOPIC: {topic}
POSITION: {position}

ARGUMENT TO SCORE:
{argument}{opponent_context}

Score this argument. JSON only:"""

        response = self._call_llm(system, user)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON from response
            if "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                return json.loads(response[start:end])
            return {"score": 5.0, "logic": 5.0, "rhetoric": 5.0, "evidence": 5.0, "feedback": "Could not parse judge response."}

    def decide_winner(self, topic: str, for_scores: list[float], against_scores: list[float]) -> dict:
        """Decide the debate winner based on cumulative scores."""
        for_avg = sum(for_scores) / len(for_scores) if for_scores else 0
        against_avg = sum(against_scores) / len(against_scores) if against_scores else 0

        winner = "FOR" if for_avg > against_avg else "AGAINST" if against_avg > for_avg else "TIE"

        system = """You are the final debate judge. Provide a brief verdict (2-3 sentences) explaining who won and why.
Refer to the speakers by their position names (FOR and AGAINST)."""

        user = f"""TOPIC: {topic}
FOR average score: {for_avg:.1f}/10
AGAINST average score: {against_avg:.1f}/10
WINNER: {winner}

Give your final verdict:"""

        verdict = self._call_llm(system, user)
        return {"winner": winner, "for_score": round(for_avg, 1), "against_score": round(against_avg, 1), "verdict": verdict}


class DebateArena:
    """Manages debate competitions."""

    def __init__(self):
        self.debates: dict[str, Debate] = {}
        self.judge = DebateJudge()
        self._counter = 0

    def create_debate(self, topic: str, agent_for: str, agent_against: str) -> Debate:
        self._counter += 1
        debate = Debate(
            id=f"debate-{self._counter:04d}",
            topic=topic,
            position_for=agent_for,
            position_against=agent_against,
        )
        self.debates[debate.id] = debate
        return debate

    def get_debate(self, debate_id: str) -> Debate | None:
        return self.debates.get(debate_id)

    def list_debates(self) -> list[dict]:
        return [d.to_dict() for d in sorted(self.debates.values(), key=lambda x: x.created_at, reverse=True)]

    def generate_argument(self, agent_name: str, topic: str, position: str, context: str = "") -> str:
        """Generate a debate argument using the configured LLM."""
        from api_resolver import call_llm, get_api_config

        config = get_api_config()

        system = f"""You are {agent_name}, a skilled debater. You are arguing {position} on the topic: {topic}.
Write a compelling, logical argument. Use evidence, examples, and persuasive rhetoric.
Keep it concise but powerful — 150-250 words."""

        user = f"Topic: {topic}\nYour position: {position}\n{context}\n\nYour argument:"

        if not config["api_key"]:
            # Mock argument for testing
            return self._mock_argument(agent_name, position)

        try:
            return call_llm(system, user, temperature=0.8, max_tokens=500)
        except Exception:
            return self._mock_argument(agent_name, position)

    def _mock_argument(self, agent_name: str, position: str) -> str:
        """Generate a mock argument when no API key is available."""
        return f"""As {agent_name}, I firmly believe that {position}. 

First, the evidence is clear — research consistently shows that this position leads to better outcomes. Multiple studies have demonstrated measurable improvements when this approach is adopted.

Second, from a logical standpoint, the alternative is unsustainable. Consider the long-term consequences: inefficiency, increased costs, and worse results for everyone involved.

Finally, on ethical grounds, this is simply the right thing to do. History shows us that progress always moves in this direction. The data, the logic, and our values all point to the same conclusion.

{agent_name} rests. 🎤"""

    def run_debate(self, debate_id: str) -> Debate:
        """Run a full debate: 3 rounds, judge each round, declare winner."""
        debate = self.debates.get(debate_id)
        if not debate:
            raise ValueError("Debate not found")

        debate.status = DebateStatus.ARGUING

        # Round 1: Opening statements
        for_args = self.generate_argument(debate.position_for, debate.topic, "FOR")
        debate.rounds.append(DebateRound(1, debate.position_for, for_args))

        against_args = self.generate_argument(debate.position_against, debate.topic, "AGAINST")
        debate.rounds.append(DebateRound(1, debate.position_against, against_args))

        # Judge Round 1
        for_score = self.judge.score_argument(debate.topic, "FOR", for_args, against_args)
        against_score = self.judge.score_argument(debate.topic, "AGAINST", against_args, for_args)
        debate.rounds[0].judge_score = for_score["score"]
        debate.rounds[0].judge_feedback = for_score.get("feedback", "")
        debate.rounds[1].judge_score = against_score["score"]
        debate.rounds[1].judge_feedback = against_score.get("feedback", "")

        # Round 2: Rebuttals
        for_rebuttal = self.generate_argument(
            debate.position_for, debate.topic, "FOR",
            f"Your opponent argued: {against_args[:300]}\nRebutt their points and strengthen your case."
        )
        debate.rounds.append(DebateRound(2, debate.position_for, for_rebuttal))

        against_rebuttal = self.generate_argument(
            debate.position_against, debate.topic, "AGAINST",
            f"Your opponent argued: {for_args[:300]}\nRebutt their points and strengthen your case."
        )
        debate.rounds.append(DebateRound(2, debate.position_against, against_rebuttal))

        # Judge Round 2
        for_r2 = self.judge.score_argument(debate.topic, "FOR", for_rebuttal, against_rebuttal)
        against_r2 = self.judge.score_argument(debate.topic, "AGAINST", against_rebuttal, for_rebuttal)
        debate.rounds[2].judge_score = for_r2["score"]
        debate.rounds[2].judge_feedback = for_r2.get("feedback", "")
        debate.rounds[3].judge_score = against_r2["score"]
        debate.rounds[3].judge_feedback = against_r2.get("feedback", "")

        # Round 3: Closing statements
        for_close = self.generate_argument(
            debate.position_for, debate.topic, "FOR",
            f"Closing statement. Summarize your case. Your strongest points were: {for_args[:200]}"
        )
        debate.rounds.append(DebateRound(3, debate.position_for, for_close))

        against_close = self.generate_argument(
            debate.position_against, debate.topic, "AGAINST",
            f"Closing statement. Summarize your case. Your strongest points were: {against_args[:200]}"
        )
        debate.rounds.append(DebateRound(3, debate.position_against, against_close))

        # Judge Round 3
        for_r3 = self.judge.score_argument(debate.topic, "FOR", for_close, against_close)
        against_r3 = self.judge.score_argument(debate.topic, "AGAINST", against_close, for_close)
        debate.rounds[4].judge_score = for_r3["score"]
        debate.rounds[4].judge_feedback = for_r3.get("feedback", "")
        debate.rounds[5].judge_score = against_r3["score"]
        debate.rounds[5].judge_feedback = against_r3.get("feedback", "")

        # Final decision
        for_scores = [r.judge_score for r in debate.rounds if r.speaker == debate.position_for and r.judge_score]
        against_scores = [r.judge_score for r in debate.rounds if r.speaker == debate.position_against and r.judge_score]

        result = self.judge.decide_winner(debate.topic, for_scores, against_scores)
        debate.status = DebateStatus.COMPLETE

        if result["winner"] == "FOR":
            debate.winner = debate.position_for
        elif result["winner"] == "AGAINST":
            debate.winner = debate.position_against
        else:
            debate.winner = "TIE"

        debate.final_scores = {
            debate.position_for: result["for_score"],
            debate.position_against: result["against_score"],
        }

        return debate

    def start_debate_async(self, debate_id: str):
        """Run a debate in a background thread."""
        def run():
            self.run_debate(debate_id)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread


# Singleton
debate_arena = DebateArena()
