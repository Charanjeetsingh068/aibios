from datetime import date
from typing import Dict, List

_state: Dict[str, object] = {
    "count": 0,
    "day": date.today().isoformat(),
    "response_times": [],
}


def record_request(response_time_ms: float) -> None:
    """Records a single API request's response time, resetting counters at midnight."""
    today = date.today().isoformat()
    if _state["day"] != today:
        _state["count"] = 0
        _state["response_times"] = []
        _state["day"] = today

    _state["count"] = int(_state["count"]) + 1
    times: List[float] = _state["response_times"]  # type: ignore[assignment]
    times.append(response_time_ms)
    if len(times) > 2000:
        times.pop(0)


def get_stats() -> Dict[str, float]:
    times: List[float] = _state["response_times"]  # type: ignore[assignment]
    avg = round(sum(times) / len(times), 2) if times else 0.0
    return {
        "requests_today": int(_state["count"]),
        "avg_response_time_ms": avg,
    }
