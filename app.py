from dataclasses import asdict
from typing import Any, Dict
from flask import Flask, jsonify, render_template, request
from src.geometry import PostureGeometryCalculator
from src.hysteresis import AlertHysteresisTracker
from src.models import Point3D, PostureLandmarks
from src.repository import SQLiteErgonomicsRepository
from src.service import ErgonomicsService


def _parse_point(data: Dict[str, Any], field_name: str) -> Point3D:
    point_data = data.get(field_name)
    if not isinstance(point_data, dict):
        raise ValueError(f"Missing or invalid point: {field_name}")
    try:
        return Point3D(
            x=float(point_data["x"]),
            y=float(point_data["y"]),
            z=float(point_data.get("z", 0.0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid coordinates for {field_name}") from exc


def _parse_landmarks(payload: Dict[str, Any]) -> PostureLandmarks:
    landmarks_data = payload.get("landmarks")
    if not isinstance(landmarks_data, dict):
        raise ValueError("Missing or invalid landmarks object.")
    return PostureLandmarks(
        ear=_parse_point(landmarks_data, "ear"),
        shoulder=_parse_point(landmarks_data, "shoulder"),
        left_shoulder=_parse_point(landmarks_data, "left_shoulder"),
        right_shoulder=_parse_point(landmarks_data, "right_shoulder"),
    )


def create_app(db_path: str = "ergonomics.db") -> Flask:
    app = Flask(__name__)
    repository = SQLiteErgonomicsRepository(db_path=db_path)
    service = ErgonomicsService(
        repository=repository,
        calculator=PostureGeometryCalculator(),
        tracker=AlertHysteresisTracker(),
    )

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/api/calibration", methods=["POST"])
    def save_calibration():
        payload = request.get_json(silent=True) or {}
        try:
            landmarks = _parse_landmarks(payload)
            profile = service.calibrate_user(
                user_id=payload.get("user_id", ""),
                landmarks=landmarks,
                neck_tolerance=float(payload["neck_tolerance"]),
                shoulder_tolerance=float(payload["shoulder_tolerance"]),
                hysteresis_seconds=int(payload["hysteresis_seconds"]),
            )
            return jsonify(asdict(profile)), 201
        except KeyError as exc:
            return jsonify({"error": f"Missing required field: {exc.args[0]}"}), 400
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/calibration/<user_id>", methods=["GET"])
    def get_calibration(user_id: str):
        try:
            profile = service.get_calibration(user_id)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if profile is None:
            return jsonify({"error": "Calibration profile not found."}), 404
        return jsonify(asdict(profile)), 200

    @app.route("/api/posture/evaluate", methods=["POST"])
    def evaluate_posture():
        payload = request.get_json(silent=True) or {}
        try:
            landmarks = _parse_landmarks(payload)
            result = service.evaluate_posture(
                user_id=payload.get("user_id", ""),
                landmarks=landmarks,
                elapsed_seconds=float(payload.get("elapsed_seconds", 0)),
                mode=str(payload.get("mode", "standard")),
            )
            return jsonify(asdict(result)), 200
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        except (KeyError, TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/sessions/<user_id>/stats", methods=["GET"])
    def get_session_stats(user_id: str):
        try:
            stats = service.get_user_statistics(user_id)
            return jsonify(stats), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/sessions/<user_id>", methods=["DELETE"])
    def clear_session_history(user_id: str):
        try:
            deleted_count = service.clear_user_history(user_id)
            return jsonify({"deleted_records": deleted_count}), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, port=5000)
