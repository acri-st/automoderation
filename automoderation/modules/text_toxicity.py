"""Text toxicity module"""

from bs4 import BeautifulSoup
from markdown import markdown
from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus, AutoModerationType, MQContentModel, MQContentType
from msfwk.mqclient import RabbitMQConfig
from msfwk.utils.logging import get_logger

from automoderation.ai_models.detoxify.model import DetoxifyModel
from automoderation.modules.moderation_module import ModerationModule
from automoderation.utils.status_utils import aggregate_status

logger = get_logger(__name__)


class TextToxicityModule(ModerationModule):
    """Verify text toxicity"""

    automoderation_type: AutoModerationType = AutoModerationType.Text_Toxicity
    content_type: MQContentType = MQContentType.Text
    detoxify_model: DetoxifyModel | None = None

    def __init__(self) -> "TextToxicityModule":
        self.detoxify_model = DetoxifyModel()
        self.consume_queue = RabbitMQConfig.TEXT_TOXICITY_AUTOMODERATION_QUEUE
        self.queue_rkey = RabbitMQConfig.TO_AUTO_TEXT_TOXICITY_RKEY

    def analyze(self, content_list: list[MQContentModel]) -> AutoModerationStatus:
        """Analyze content, and set reason of fails"""
        all_status = []
        for content in content_list:
            # Process markdown and extract text using BeautifulSoup
            if isinstance(content.value, str):
                html = markdown(content.value)
                content.value = "".join(BeautifulSoup(html, features="html.parser").findAll(text=True))
            status = self.detoxify_model.evaluate_content(content)
            all_status.append(status)
            if status != AutoModerationStatus.Pass:
                self.generate_reason_message(status, content)

        return aggregate_status(all_status)
