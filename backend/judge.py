"""
Judge: scores agent code submissions against test cases.
Measures correctness, execution time, and memory usage.
"""

import time
import sys
import io
import traceback
import ast
from dataclasses import dataclass, field


@dataclass
class TestResult:
    passed: bool
    input_args: str
    expected: str
    actual: str
    error: str | None = None
    duration_ms: float = 0


@dataclass
class Score:
    agent_name: str
    tests_passed: int
    tests_total: int
    total_duration_ms: float
    max_memory_kb: float
    errors: list[str] = field(default_factory=list)
    test_results: list[TestResult] = field(default_factory=list)
    score: float = 0.0  # final weighted score 0–100

    def __post_init__(self):
        if self.tests_total > 0:
            correctness = (self.tests_passed / self.tests_total) * 70  # 70% weight
            # Speed bonus — faster is better, up to 20 points
            # Normalized: assume 5000ms as baseline
            speed = max(0, 20 * (1 - min(self.total_duration_ms, 5000) / 5000))
            # Memory bonus — up to 10 points
            mem = max(0, 10 * (1 - min(self.max_memory_kb, 102400) / 102400))
            self.score = round(correctness + speed + mem, 1)


class Judge:
    """Runs code submissions against test cases and returns scores."""

    @staticmethod
    def _safe_exec(code: str, test_input: str, timeout_sec: float = 5.0) -> tuple[str | None, str | None, float, float]:
        """Execute code in a sandboxed-ish environment. Returns (output, error, duration_ms, memory_kb)."""
        stdout = io.StringIO()
        stderr = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stderr

        start_time = time.perf_counter()
        start_mem = 0

        try:
            # Parse the test input as a dict of variable assignments
            local_env: dict = {}
            if test_input.strip():
                exec(f"test_input = {test_input}", {}, local_env)
                test_data = local_env["test_input"]
            else:
                test_data = None

            # Execute user code in isolated namespace
            user_ns: dict = {}
            exec(code, {"__builtins__": __builtins__}, user_ns)

            # Find the solution function
            solution = None
            for name, obj in user_ns.items():
                if callable(obj) and not name.startswith("_"):
                    solution = obj
                    break

            if solution is None:
                return None, "No callable function found in submission", 0, 0

            # Call it
            if isinstance(test_data, dict):
                result = solution(**test_data)
            elif isinstance(test_data, (list, tuple)):
                result = solution(*test_data)
            elif test_data is not None:
                result = solution(test_data)
            else:
                result = solution()

            output = str(result)

        except Exception as e:
            output = None
            error_str = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        else:
            error_str = stderr.getvalue() if stderr.getvalue() else None
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            duration_ms = (time.perf_counter() - start_time) * 1000

        return output, error_str, duration_ms, 0  # memory tracking skipped for simplicity

    def score_submission(
        self, agent_name: str, code: str, test_cases: list[dict]
    ) -> Score:
        """Run all test cases and return a Score."""
        results: list[TestResult] = []
        errors: list[str] = []
        total_duration = 0.0

        for tc in test_cases:
            output, error, duration_ms, mem_kb = self._safe_exec(code, tc["input"])

            result = TestResult(
                passed=False,
                input_args=tc["input"],
                expected=tc["expected"],
                actual=output if output else "(error)",
                error=error,
                duration_ms=duration_ms,
            )

            if error:
                result.passed = False
                errors.append(f"Test '{tc.get('name', 'unnamed')}': {error.split(chr(10))[0]}")
            elif output and output.strip() == tc["expected"].strip():
                result.passed = True
            elif output:
                # Try numeric comparison with tolerance
                try:
                    if abs(float(output) - float(tc["expected"])) < 1e-9:
                        result.passed = True
                except (ValueError, TypeError):
                    result.passed = False

            total_duration += duration_ms
            results.append(result)

        passed = sum(1 for r in results if r.passed)

        return Score(
            agent_name=agent_name,
            tests_passed=passed,
            tests_total=len(test_cases),
            total_duration_ms=total_duration,
            max_memory_kb=0,
            errors=errors,
            test_results=results,
        )
