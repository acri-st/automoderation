"""Main"""

from msfwk.application import app
from msfwk.context import current_config, register_destroy, register_init
from msfwk.mqclient import load_default_rabbitmq_config
from msfwk.utils.config import add_reliability_check
from msfwk.utils.logging import get_logger

from automoderation.modules.moderation_module import add_module, start_modules, stop_modules
from automoderation.modules.text_toxicity import TextToxicityModule
from automoderation.modules.url_validation import UrlValidationModule

logger = get_logger("application")


# To let the import, and uses the app lifespan

automoderation_app = app


async def init(config: dict) -> bool:
    """Init"""
    logger.info("Initialising Automoderation ...")
    load_succeded = load_default_rabbitmq_config()
    current_config.set(config)
    if load_succeded:
        add_module(TextToxicityModule())
        add_module(UrlValidationModule())
        logger.info("added all automoderation modules")
        await start_modules()
    else:
        logger.error("Failed to load rabbitmq config")
    add_reliability_check("rabbitmq", config.get("rabbitmq", {}).get("mq_host"))
    return load_succeded


async def destroy(_: dict) -> bool:
    """Destroy"""
    logger.info("Destroying Automoderation ...")
    await stop_modules()
    return True


register_init(init)
register_destroy(destroy)
