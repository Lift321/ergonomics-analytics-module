import math
from src.models import Point3D


class PostureGeometryCalculator:
    def calculate_neck_angle(self, ear: Point3D, shoulder: Point3D) -> float:
        delta_x = abs(ear.x - shoulder.x)
        delta_y = abs(ear.y - shoulder.y)
        if delta_x == 0 and delta_y == 0:
            raise ValueError("Ear and shoulder coordinates cannot be identical.")
        return round(math.degrees(math.atan2(delta_x, delta_y)), 2)

    def calculate_shoulder_asymmetry(
        self, left_shoulder: Point3D, right_shoulder: Point3D
    ) -> float:
        return round(abs(left_shoulder.y - right_shoulder.y), 4)

    def calculate_deviation(self, current_value: float, baseline_value: float) -> float:
        return round(abs(current_value - baseline_value), 4)
