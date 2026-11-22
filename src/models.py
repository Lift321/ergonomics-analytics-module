from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class PostureLandmarks:
    ear: Point3D
    shoulder: Point3D
    left_shoulder: Point3D
    right_shoulder: Point3D


@dataclass(frozen=True)
class CalibrationProfile:
    user_id: str
    baseline_neck_angle: float
    baseline_shoulder_diff: float
    neck_tolerance: float
    shoulder_tolerance: float
    hysteresis_seconds: int


@dataclass(frozen=True)
class PostureMeasurement:
    neck_angle: float
    shoulder_asymmetry: float
    neck_deviation: float
    shoulder_deviation: float
    is_bad_posture: bool
    alert_triggered: bool
    bad_posture_duration: float
    status: str


@dataclass(frozen=True)
class SessionRecord:
    id: Optional[int]
    user_id: str
    neck_angle: float
    shoulder_asymmetry: float
    is_bad_posture: bool
    alert_triggered: bool
    mode: str
    created_at: str
