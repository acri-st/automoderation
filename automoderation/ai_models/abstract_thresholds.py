"""Abstract thresholds"""

from enum import Enum

from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus


class ScoreToStatus:
    """Associate a threshold with a status"""

    threshold: float
    status: AutoModerationStatus

    def __init__(self, thr: float, status: AutoModerationStatus) -> "AutoModerationStatus":
        self.threshold = thr
        self.status = status


class ToxicityThresholds(Enum):
    """Base class for toxicity thresholds"""

    @classmethod
    def to_dict(cls) -> dict[str, float]:
        """Convert the enum values to a dictionary"""
        return {threshold.name: threshold.value for threshold in cls}

    @classmethod
    def match_score_to_status(cls, score: int) -> "AutoModerationStatus| None":
        """Get the toxicity level based on a given value"""
        sorted_risks = sorted(cls, key=lambda x: x.value.threshold, reverse=True)
        for score_risk in sorted_risks:
            if score >= score_risk.value.threshold:
                return score_risk.value.status
        return None
