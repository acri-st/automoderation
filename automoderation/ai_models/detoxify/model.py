"""Detoxify model"""

import json

import requests
from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus, MQContentModel
from msfwk.utils.config import read_config
from msfwk.utils.logging import get_logger

from automoderation.ai_models.abstract_model import AbstractModel
from automoderation.ai_models.detoxify.threshold import DetoxifyToxicityThresholds
from automoderation.utils.status_utils import aggregate_status

logger = get_logger(__name__)

RESPONSE_TEXT_NOT_AVAILABLE = "[Response text not available]"


class DetoxifyModel(AbstractModel):
    """Detoxify model"""

    toxic_thresholds: DetoxifyToxicityThresholds = DetoxifyToxicityThresholds

    def evaluate_content(self, content: MQContentModel) -> AutoModerationStatus:
        """Return the toxicity risk for each sentence of a text

        Args:
            content (MQContentModel): will test toxicity on this content
        """
        text = content.value
        response_text = None
        try:
            detoxify_service = read_config().get("services", {}).get("automoderation", {}).get("detoxify_service", "")
            logger.debug("Asking Detoxify API (%s) for %s", detoxify_service, text)
            response = requests.get(f"{detoxify_service}?text={text}", timeout=30)
            response.raise_for_status()
            toxicity_scores = response.json()
            if toxicity_scores == {}:
                return AutoModerationStatus.Need_Manual
            # convert detoxify scores intp automod status
            all_status = [self.match_score_with_status(score["toxicity"]) for score in toxicity_scores.values()]
            logger.debug(all_status)
            return aggregate_status(all_status)
        except requests.exceptions.Timeout:
            if response_text is None:
                response_text = RESPONSE_TEXT_NOT_AVAILABLE
            logger.warning(
                "Timed out in request to detoxify for text = %s | response_text = %s. Set to Need_Manual",
                text,
                response_text,
            )
            return AutoModerationStatus.Need_Manual
        except requests.exceptions.RequestException as e:
            if response_text is None:
                response_text = RESPONSE_TEXT_NOT_AVAILABLE
            message = f"Request to detoxify failed for text {text} | response_text = {response_text}"
            logger.exception(message, exc_info=e)
            return AutoModerationStatus.Need_Manual
        except json.JSONDecodeError as e:
            if response_text is None:
                response_text = RESPONSE_TEXT_NOT_AVAILABLE
            message = f"Failed to decode json for result of http on {text} | response_text = {response_text}"
            logger.exception(message, exc_info=e)
            return AutoModerationStatus.Need_Manual
