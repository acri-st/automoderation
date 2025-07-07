"""Interfaces"""

from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus
from pydantic import BaseModel


class SentenceStatusModel(BaseModel):
    """Associate a sentence with a risk"""

    sentence: str
    risk: AutoModerationStatus


class TextToxicityRiskModel(BaseModel):
    """All the sentence of a text, associated with their toxicity risk"""

    sentences: list[SentenceStatusModel]
