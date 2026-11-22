from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.geometry import PostureGeometryCalculator
from src.hysteresis import AlertHysteresisTracker
from src.models import (
    CalibrationProfile,
    PostureLandmarks,
    PostureMeasurement,
    SessionRecord,
)
from src.repository import ErgonomicsRepository
from src.strategies import StrategyFactory


class ErgonomicsService:
    RECENT_RECORDS_LIMIT = 50

    def __init__(
        self,
        repository: ErgonomicsRepository,
        calculator: PostureGeometryCalculator,
        tracker: AlertHysteresisTracker,
    ) -> None:
        self._repository = repository
        self._calculator = calculator
        self._tracker = tracker

    def calibrate_user(
        self,
        user_id: str,
        landmarks: PostureLandmarks,
        neck_tolerance: float,
        shoulder_tolerance: float,
        hysteresis_seconds: int,
    ) -> CalibrationProfile:
        self._validate_user_id(user_id)
        if neck_tolerance <= 0 or shoulder_tolerance <= 0:
            raise ValueError("Tolerance values must be greater than zero.")
        if hysteresis_seconds < 0:
            raise ValueError("Hysteresis seconds cannot be negative.")

        baseline_neck_angle = self._calculator.calculate_neck_angle(
            landmarks.ear, landmarks.shoulder
        )
        baseline_shoulder_diff = self._calculator.calculate_shoulder_asymmetry(
            landmarks.left_shoulder, landmarks.right_shoulder
        )

        profile = CalibrationProfile(
            user_id=user_id.strip(),
            baseline_neck_angle=baseline_neck_angle,
            baseline_shoulder_diff=baseline_shoulder_diff,
            neck_tolerance=neck_tolerance,
            shoulder_tolerance=shoulder_tolerance,
            hysteresis_seconds=hysteresis_seconds,
        )
        self._tracker.reset(profile.user_id)
        return self._repository.save_calibration(profile)

    def get_calibration(self, user_id: str) -> Optional[CalibrationProfile]:
        self._validate_user_id(user_id)
        return self._repository.get_calibration(user_id.strip())

    def evaluate_posture(
        self,
        user_id: str,
        landmarks: PostureLandmarks,
        elapsed_seconds: float,
        mode: str = "standard",
    ) -> PostureMeasurement:
        self._validate_user_id(user_id)
        normalized_user_id = user_id.strip()
        profile = self._repository.get_calibration(normalized_user_id)
        if profile is None:
            raise LookupError("Calibration profile not found for user.")

        strategy = StrategyFactory.create(mode)
        neck_angle = self._calculator.calculate_neck_angle(
            landmarks.ear, landmarks.shoulder
        )
        shoulder_asymmetry = self._calculator.calculate_shoulder_asymmetry(
            landmarks.left_shoulder, landmarks.right_shoulder
        )

        neck_deviation = self._calculator.calculate_deviation(
            neck_angle, profile.baseline_neck_angle
        )
        shoulder_deviation = self._calculator.calculate_deviation(
            shoulder_asymmetry, profile.baseline_shoulder_diff
        )

        is_bad_posture = strategy.is_posture_incorrect(
            neck_deviation, shoulder_deviation, profile
        )
        alert_triggered, bad_duration = self._tracker.update(
            normalized_user_id,
            is_bad_posture,
            elapsed_seconds,
            profile.hysteresis_seconds,
        )

        timestamp = datetime.now(timezone.utc).isoformat()
        record = SessionRecord(
            id=None,
            user_id=normalized_user_id,
            neck_angle=neck_angle,
            shoulder_asymmetry=shoulder_asymmetry,
            is_bad_posture=is_bad_posture,
            alert_triggered=alert_triggered,
            mode=mode.lower(),
            created_at=timestamp,
        )
        self._repository.save_session_record(record)

        status = self._resolve_status(is_bad_posture, alert_triggered)
        return PostureMeasurement(
            neck_angle=neck_angle,
            shoulder_asymmetry=shoulder_asymmetry,
            neck_deviation=neck_deviation,
            shoulder_deviation=shoulder_deviation,
            is_bad_posture=is_bad_posture,
            alert_triggered=alert_triggered,
            bad_posture_duration=bad_duration,
            status=status,
        )

    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        self._validate_user_id(user_id)
        normalized_user_id = user_id.strip()
        records = self._repository.get_session_records(normalized_user_id, limit=None)
        total_samples = len(records)

        if total_samples == 0:
            return {
                "user_id": normalized_user_id,
                "total_samples": 0,
                "good_posture_samples": 0,
                "bad_posture_samples": 0,
                "alerts_count": 0,
                "good_posture_percentage": 0.0,
                "average_neck_angle": 0.0,
                "records": [],
            }

        bad_samples = sum(1 for item in records if item.is_bad_posture)
        good_samples = total_samples - bad_samples
        alerts_count = sum(1 for item in records if item.alert_triggered)
        average_neck_angle = round(
            sum(item.neck_angle for item in records) / total_samples, 2
        )
        good_percentage = round((good_samples / total_samples) * 100, 2)

        return {
            "user_id": normalized_user_id,
            "total_samples": total_samples,
            "good_posture_samples": good_samples,
            "bad_posture_samples": bad_samples,
            "alerts_count": alerts_count,
            "good_posture_percentage": good_percentage,
            "average_neck_angle": average_neck_angle,
            "records": [
                asdict(item) for item in records[: self.RECENT_RECORDS_LIMIT]
            ],
        }

    def clear_user_history(self, user_id: str) -> int:
        self._validate_user_id(user_id)
        normalized_user_id = user_id.strip()
        self._tracker.reset(normalized_user_id)
        return self._repository.delete_user_records(normalized_user_id)

    def _validate_user_id(self, user_id: str) -> None:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("User ID must be a non-empty string.")

    def _resolve_status(self, is_bad_posture: bool, alert_triggered: bool) -> str:
        if alert_triggered:
            return "ALERT"
        if is_bad_posture:
            return "WARNING"
        return "GOOD"
