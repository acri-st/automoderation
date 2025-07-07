"""Detoxify thresholds"""

from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus

from automoderation.ai_models.abstract_thresholds import ScoreToStatus, ToxicityThresholds


class DetoxifyToxicityThresholds(ToxicityThresholds):
    """Derived class for detoxify toxicity thresholds"""

    NOT_TOXIC = ScoreToStatus(0, AutoModerationStatus.Pass)
    MODERATELY_TOXIC = ScoreToStatus(0.25, AutoModerationStatus.Need_Manual)
    HIGHLY_TOXIC = ScoreToStatus(0.75, AutoModerationStatus.Failed)
