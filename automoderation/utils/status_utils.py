from msfwk.desp.rabbitmq.mq_message import AutoModerationStatus


def aggregate_status(status_list: list[AutoModerationStatus]) -> AutoModerationStatus:
    """Aggregate all the status in a list, to return the most important one

    Failed > Need_Manual > Pass > Pending

    Args:
        status_list (list[AutoModerationStatus]): _description_

    Returns:
        AutoModerationStatus: _description_
    """
    if AutoModerationStatus.Failed in status_list:
        return AutoModerationStatus.Failed

    if AutoModerationStatus.Need_Manual in status_list:
        return AutoModerationStatus.Need_Manual

    return AutoModerationStatus.Pass if len(status_list) > 0 else AutoModerationStatus.Pending
