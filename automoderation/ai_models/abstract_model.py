"""Abstract model"""

from abc import abstractmethod

from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus

from automoderation.ai_models.abstract_thresholds import ToxicityThresholds


class AbstractModel:
    """Abstract class for AI Model"""

    toxic_thresholds: ToxicityThresholds

    def match_score_with_status(self, score: int) -> AutoModerationStatus:
        """Return the risk associated with a score

        Args:
            score (int): toxicity score
        """
        return self.toxic_thresholds.match_score_to_status(score)

    @abstractmethod
    def evaluate_content(self, text: str) -> AutoModerationStatus:
        """Loops around all the given content.
        Should fill the rejected_reasons for content that failed to pass

        Args:
            text (str): will test toxicity on this text
        """
        raise NotImplementedError
