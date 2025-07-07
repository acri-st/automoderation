"""Url validation module"""

import socket
from urllib.parse import urlparse

import requests
from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus, AutoModerationType, MQContentModel, MQContentType
from msfwk.mqclient import RabbitMQConfig
from msfwk.utils.logging import get_logger

from automoderation.modules.moderation_module import ModerationModule
from automoderation.utils.status_utils import aggregate_status

logger = get_logger(__name__)

HTTP_SUCCESS_THRESHOLD = 400


class UrlValidationModule(ModerationModule):
    """Verify url"""

    automoderation_type: AutoModerationType = AutoModerationType.Url_Validation
    content_type: MQContentType = MQContentType.Url

    def __init__(self) -> "UrlValidationModule":
        self.consume_queue = RabbitMQConfig.URL_VALIDATION_AUTOMODERATION_QUEUE
        self.queue_rkey = RabbitMQConfig.TO_AUTO_URL_VALIDATION_RKEY

    def analyze(self, content_list: list[MQContentModel]) -> AutoModerationStatus:
        """Analyze content, and set reason of fails"""
        all_status = []
        for content in content_list:
            status, additionnal_infos = self.check_url_accessibility(content.value)
            all_status.append(status)
            if status != AutoModerationStatus.Pass:
                self.generate_reason_message(status, content, additionnal_infos=additionnal_infos)

        return aggregate_status(all_status)

    def check_url_accessibility(self, url: str) -> tuple[AutoModerationStatus, str | None]:
        """Securely checks if the given URL is accessible.

        Returns An AutomoderationStatus, and a reason (for Fail or Need_Manual, None if Pass)
        """
        try:
            with requests.Session() as session:
                response = session.head(url, allow_redirects=True, timeout=2)
                if response.status_code < HTTP_SUCCESS_THRESHOLD:
                    return AutoModerationStatus.Pass, None
                return (AutoModerationStatus.Failed, f"{url} returns {response.status_code}")
        except requests.ConnectionError:
            parsed_url = urlparse(url)
            message = f"Error during connection with: '{url}'"
            try:
                socket.gethostbyname(parsed_url.hostname)
            except socket.gaierror:
                message = f"Could not find URL: '{url}'"
                logger.info(message)
            return AutoModerationStatus.Failed, message
        except requests.Timeout as te:
            message = f"Timeout error while checking URL: '{url}'"
            logger.exception(message, exc_info=te)
            return AutoModerationStatus.Need_Manual, message
        except requests.RequestException as re:
            message = f"General request error while checking URL: '{url}'"
            logger.exception(message, exc_info=re)
            return AutoModerationStatus.Need_Manual, message
