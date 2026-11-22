from typing import Dict, Tuple


class AlertHysteresisTracker:
    def __init__(self) -> None:
        self._bad_posture_durations: Dict[str, float] = {}

    def update(
        self,
        user_id: str,
        is_bad_posture: bool,
        elapsed_seconds: float,
        threshold_seconds: int,
    ) -> Tuple[bool, float]:
        if elapsed_seconds < 0:
            raise ValueError("Elapsed seconds cannot be negative.")
        if threshold_seconds < 0:
            raise ValueError("Threshold seconds cannot be negative.")

        if not is_bad_posture:
            self._bad_posture_durations[user_id] = 0.0
            return False, 0.0

        current_duration = self._bad_posture_durations.get(user_id, 0.0) + elapsed_seconds
        self._bad_posture_durations[user_id] = current_duration
        alert_triggered = current_duration >= threshold_seconds
        return alert_triggered, round(current_duration, 2)

    def reset(self, user_id: str) -> None:
        self._bad_posture_durations[user_id] = 0.0
