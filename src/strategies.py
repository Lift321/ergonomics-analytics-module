from abc import ABC, abstractmethod
from src.models import CalibrationProfile


class PostureEvaluationStrategy(ABC):
    @abstractmethod
    def is_posture_incorrect(
        self,
        neck_deviation: float,
        shoulder_deviation: float,
        profile: CalibrationProfile,
    ) -> bool:
        pass


class ToleranceScaledPostureStrategy(PostureEvaluationStrategy):
    TOLERANCE_MULTIPLIER = 1.0

    def is_posture_incorrect(
        self,
        neck_deviation: float,
        shoulder_deviation: float,
        profile: CalibrationProfile,
    ) -> bool:
        neck_limit = profile.neck_tolerance * self.TOLERANCE_MULTIPLIER
        shoulder_limit = profile.shoulder_tolerance * self.TOLERANCE_MULTIPLIER
        return neck_deviation > neck_limit or shoulder_deviation > shoulder_limit


class StandardPostureStrategy(ToleranceScaledPostureStrategy):
    TOLERANCE_MULTIPLIER = 1.0


class StrictPostureStrategy(ToleranceScaledPostureStrategy):
    TOLERANCE_MULTIPLIER = 0.7


class RelaxedPostureStrategy(ToleranceScaledPostureStrategy):
    TOLERANCE_MULTIPLIER = 1.3


class StrategyFactory:
    _STRATEGIES = {
        "standard": StandardPostureStrategy,
        "strict": StrictPostureStrategy,
        "relaxed": RelaxedPostureStrategy,
    }

    @classmethod
    def create(cls, mode: str) -> PostureEvaluationStrategy:
        strategy_class = cls._STRATEGIES.get(mode.lower())
        if strategy_class is None:
            raise ValueError(f"Unsupported evaluation mode: {mode}")
        return strategy_class()
