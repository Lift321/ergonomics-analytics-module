from abc import ABC, abstractmethod
from contextlib import closing
import sqlite3
from typing import List, Optional
from src.models import CalibrationProfile, SessionRecord


class ErgonomicsRepository(ABC):
    @abstractmethod
    def save_calibration(self, profile: CalibrationProfile) -> CalibrationProfile:
        pass

    @abstractmethod
    def get_calibration(self, user_id: str) -> Optional[CalibrationProfile]:
        pass

    @abstractmethod
    def save_session_record(self, record: SessionRecord) -> SessionRecord:
        pass

    @abstractmethod
    def get_session_records(
        self, user_id: str, limit: Optional[int] = 50
    ) -> List[SessionRecord]:
        pass

    @abstractmethod
    def delete_user_records(self, user_id: str) -> int:
        pass


class SQLiteErgonomicsRepository(ErgonomicsRepository):
    def __init__(self, db_path: str = "ergonomics.db") -> None:
        self._db_path = db_path
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS calibrations (
                        user_id TEXT PRIMARY KEY,
                        baseline_neck_angle REAL NOT NULL,
                        baseline_shoulder_diff REAL NOT NULL,
                        neck_tolerance REAL NOT NULL,
                        shoulder_tolerance REAL NOT NULL,
                        hysteresis_seconds INTEGER NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS session_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        neck_angle REAL NOT NULL,
                        shoulder_asymmetry REAL NOT NULL,
                        is_bad_posture INTEGER NOT NULL,
                        alert_triggered INTEGER NOT NULL,
                        mode TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

    def save_calibration(self, profile: CalibrationProfile) -> CalibrationProfile:
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO calibrations (
                        user_id,
                        baseline_neck_angle,
                        baseline_shoulder_diff,
                        neck_tolerance,
                        shoulder_tolerance,
                        hysteresis_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        baseline_neck_angle = excluded.baseline_neck_angle,
                        baseline_shoulder_diff = excluded.baseline_shoulder_diff,
                        neck_tolerance = excluded.neck_tolerance,
                        shoulder_tolerance = excluded.shoulder_tolerance,
                        hysteresis_seconds = excluded.hysteresis_seconds
                    """,
                    (
                        profile.user_id,
                        profile.baseline_neck_angle,
                        profile.baseline_shoulder_diff,
                        profile.neck_tolerance,
                        profile.shoulder_tolerance,
                        profile.hysteresis_seconds,
                    ),
                )
        return profile

    def get_calibration(self, user_id: str) -> Optional[CalibrationProfile]:
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                "SELECT * FROM calibrations WHERE user_id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        return CalibrationProfile(
            user_id=row["user_id"],
            baseline_neck_angle=row["baseline_neck_angle"],
            baseline_shoulder_diff=row["baseline_shoulder_diff"],
            neck_tolerance=row["neck_tolerance"],
            shoulder_tolerance=row["shoulder_tolerance"],
            hysteresis_seconds=row["hysteresis_seconds"],
        )

    def save_session_record(self, record: SessionRecord) -> SessionRecord:
        with closing(self._get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO session_records (
                        user_id,
                        neck_angle,
                        shoulder_asymmetry,
                        is_bad_posture,
                        alert_triggered,
                        mode,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.user_id,
                        record.neck_angle,
                        record.shoulder_asymmetry,
                        int(record.is_bad_posture),
                        int(record.alert_triggered),
                        record.mode,
                        record.created_at,
                    ),
                )
                record_id = cursor.lastrowid
        return SessionRecord(
            id=record_id,
            user_id=record.user_id,
            neck_angle=record.neck_angle,
            shoulder_asymmetry=record.shoulder_asymmetry,
            is_bad_posture=record.is_bad_posture,
            alert_triggered=record.alert_triggered,
            mode=record.mode,
            created_at=record.created_at,
        )

    def get_session_records(
        self, user_id: str, limit: Optional[int] = 50
    ) -> List[SessionRecord]:
        sql_limit = -1 if limit is None else limit
        with closing(self._get_connection()) as conn:
            rows = conn.execute(
                """
                SELECT * FROM session_records
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, sql_limit),
            ).fetchall()
        return [
            SessionRecord(
                id=row["id"],
                user_id=row["user_id"],
                neck_angle=row["neck_angle"],
                shoulder_asymmetry=row["shoulder_asymmetry"],
                is_bad_posture=bool(row["is_bad_posture"]),
                alert_triggered=bool(row["alert_triggered"]),
                mode=row["mode"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def delete_user_records(self, user_id: str) -> int:
        with closing(self._get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM session_records WHERE user_id = ?", (user_id,)
                )
                return cursor.rowcount
