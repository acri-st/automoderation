"""Moderation module"""

import asyncio
from abc import abstractmethod

import aio_pika
from msfwk.context import current_transaction
from msfwk.desp.rabbitmq.mq_message import (
    AutoModerationStatus,
    AutoModerationType,
    DespMQMessage,
    ModerationEventStatus,
    MQContentModel,
    MQContentType,
    decode_consume_message,
)
from msfwk.mqclient import RabbitMQConfig, consume_mq_queue_async, send_mq_message
from msfwk.utils.logging import get_logger

logger = get_logger(__name__)

END_OF_AUTO_QUEUE = RabbitMQConfig.HANDLING_MODERATION_QUEUE

module_holder: dict[AutoModerationType, "ModerationModule"] = {}


def get_next_moderation_queue(mq_message: DespMQMessage, automoderation_type: AutoModerationType) -> str | None:
    """Returns the next item in the list after the one with the given moderation_type.
    If the given type is not found or is the last item, returns None.
    """
    auto_moderations = mq_message.auto_mod_routing
    for i, moderation in enumerate(auto_moderations):
        if moderation.moderation_type == automoderation_type:
            return (
                get_queue_rkey_from_module_type(auto_moderations[i + 1].moderation_type)
                if i + 1 < len(auto_moderations)
                else None
            )
    return None


def automod_to_moderation_status(mq_message: DespMQMessage) -> None:
    """Set mq_message.status according this rules:

    Rejected if one or more auto_mod_routing Failed
    Accepted if each auto_mod in auto_mod_routing Pass
    Manual_Pending otherwise
    """
    all_status = [auto_mod.status for auto_mod in mq_message.auto_mod_routing]
    if AutoModerationStatus.Failed in all_status:
        mq_message.status = ModerationEventStatus.Rejected
        return

    if AutoModerationStatus.Need_Manual not in all_status:
        mq_message.status = ModerationEventStatus.Accepted
        return

    if AutoModerationStatus.Pending in all_status:
        message = "Should not have a auto_moderation pending at end of auto_moderation"
        logger.warning(message)

    mq_message.status = ModerationEventStatus.Manual_Pending


class ModerationModule:
    """One module of moderation"""

    automoderation_type: AutoModerationType
    content_type: MQContentType
    consume_queue: str
    queue_rkey: str
    task: asyncio.Task | None = None

    @abstractmethod
    def analyze(self, content_list: list[MQContentModel]) -> AutoModerationStatus:
        """Analyze content"""

    async def on_message(self, message: aio_pika.IncomingMessage) -> None:
        """Calls self.analyse on message received from the listened queue

        Args:
            mq_message (DespMQMessage): _description_
            message (aio_pika.IncomingMessage): _description_
        """
        mq_message = await decode_consume_message(message, DespMQMessage)
        logger.debug("current_transaction : %s", current_transaction.get())
        if mq_message is None:
            logger.warning("Cannot apply moderation on message due to decoding error")
            return
        logger.info("%s module Start analysing %s content", self.automoderation_type.value, mq_message.id)
        status = self.analyze(mq_message.content.data_by_type.get(self.content_type))
        mq_message.history.append(f"Automoderation [{self.automoderation_type.value}]: {status}")
        logger.info(
            "%s module Finished analysing %s content: %s", self.automoderation_type.value, mq_message.id, status.value
        )
        self.set_current_module_status(mq_message, status)
        await message.ack()
        await self.send_to_next_queue(mq_message)

    async def send_to_next_queue(self, mq_message: DespMQMessage) -> None:
        """Send the mq_message to the next queue, or handling if not next queue

        Args:
            mq_message (DespMQMessage): __desc__
        """
        exchange = RabbitMQConfig.MODERATION_EXCHANGE
        if (next_queue := get_next_moderation_queue(mq_message, self.automoderation_type)) is None:
            logger.debug("Last element for %s: Sending to Handling", mq_message.id)
            next_queue = RabbitMQConfig.TO_HANDLING_RKEY
            automod_to_moderation_status(mq_message)
        logger.info("Send to next queue: %s on exchange %s", next_queue, exchange)
        await send_mq_message(mq_message, exchange, next_queue)

    async def start(self) -> None:
        """Start the module

        Listen to "consume_queue" and analyse the incomming message.
        Then redirect them in the next automod Queue, or handling
        """
        self.task = await consume_mq_queue_async(self.consume_queue, lambda msg: self.on_message(msg))
        logger.info(
            "Automoderation Module %s Start listening on %s", self.automoderation_type.value, self.consume_queue
        )

    async def stop(self) -> None:
        """Stop the module"""
        if self.task is not None:
            self.task.cancel()

    def generate_reason_message(
        self, status: AutoModerationType, content: MQContentModel, additionnal_infos: list[str] | None = None
    ) -> None:
        """Write the error reason for a content

        Args:
            status (AutoModerationType): _description_
            content (MQContentModel): _description_
            additionnal_infos (list[str] | None): __description__
        """
        reason = f"[Automoderation] - {self.automoderation_type} module evaluate this content as [{status.value}]"
        if additionnal_infos:
            reason += ":" + "\n".join(additionnal_infos)
        content.rejected_reasons.append(reason)

    def set_current_module_status(self, mq_message: DespMQMessage, status: AutoModerationStatus) -> None:
        """_summary_

        Args:
            mq_message (DespMQMessage): _description_
            status (AutoModerationStatus): _description_
        """
        auto_moderations = mq_message.auto_mod_routing
        for moderation in auto_moderations:
            if moderation.moderation_type == self.automoderation_type:
                moderation.status = status


def add_module(module: ModerationModule) -> None:
    """Adds a new module in the module_holder

    Args:
        module (ModerationModule): _description_
    """
    if old_module := module_holder.get(module.automoderation_type):
        logger.warning(
            "Set [%s] module for %s, replacing the old one [%s].",
            module.__class__.__name__,
            module.automoderation_type,
            old_module.__class__.__name__,
        )
    module_holder[module.automoderation_type] = module


def get_queue_rkey_from_module_type(auto_mod_type: AutoModerationType) -> str:
    """Return the queue routing key from the module of type auto_mod_type"""
    module = module_holder.get(auto_mod_type)
    return module.queue_rkey if module is not None else None


async def start_modules() -> None:
    """Start a mod"""
    for module in module_holder.values():
        await module.start()
    logger.debug("All Modules Started")


async def stop_modules() -> None:
    """Stop a mod"""
    for module in module_holder.values():
        module.stop()
    logger.debug("All Modules Stopped")
