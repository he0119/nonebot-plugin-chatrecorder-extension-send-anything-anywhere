from typing import Any, Dict, List, Sequence

from nonebot import require

require("nonebot_plugin_chatrecorder")
require("nonebot_plugin_saa")
from nonebot_plugin_chatrecorder import (
    MessageRecord,
    get_message_records,
    get_messages_plain_text,
)
from nonebot_plugin_saa import (
    PlatformTarget,
    TargetFeishuGroup,
    TargetFeishuPrivate,
    TargetKaiheilaChannel,
    TargetKaiheilaPrivate,
    TargetOB12Unknow,
    TargetQQGroup,
    TargetQQGuildChannel,
    TargetQQGuildDirect,
    TargetQQPrivate,
)


def target_to_kwargs(target: PlatformTarget) -> Dict[str, Any]:
    """将 PlatformTarget 转换为 chatrecorder 所需参数"""
    platform = None
    id1 = None
    id2 = None
    id3 = None
    if isinstance(target, TargetQQPrivate):
        platform = "qq"
        id1 = str(target.user_id)
    elif isinstance(target, TargetQQGroup):
        platform = "qq"
        id2 = str(target.group_id)
    elif isinstance(target, TargetQQGuildDirect):
        platform = "qqguild"
        id1 = str(target.recipient_id)
        id3 = str(target.source_guild_id)
    elif isinstance(target, TargetQQGuildChannel):
        platform = "qqguild"
        id2 = str(target.channel_id)
    elif isinstance(target, TargetKaiheilaPrivate):
        platform = "kaiheila"
        id1 = (str(target.user_id),)
    elif isinstance(target, TargetKaiheilaChannel):
        platform = "kaiheila"
        id2 = (str(target.channel_id),)
    elif isinstance(target, TargetFeishuPrivate):
        platform = "feishu"
        id1 = (str(target.open_id),)
    elif isinstance(target, TargetFeishuGroup):
        platform = "feishu"
        id2 = (str(target.chat_id),)
    elif isinstance(target, TargetOB12Unknow):
        if target.detail_type == "private":
            platform = target.platform
            id1 = str(target.user_id)
        elif target.detail_type == "group":
            platform = target.platform
            id2 = str(target.group_id)
        else:
            platform = target.platform
            id2 = target.channel_id
            id3 = target.guild_id
    else:
        raise ValueError(f"不支持的 PlatformTarget 类型：{target}")

    return {
        "platforms": [platform] if platform is not None else None,
        "id1s": [id1] if id1 is not None else None,
        "id2s": [id2] if id2 is not None else None,
        "id3s": [id3] if id3 is not None else None,
    }


async def get_message_records_by_target(
    target: PlatformTarget, **kwargs
) -> Sequence[MessageRecord]:
    """根据 PlatformTarget 获取消息记录"""
    kwargs.update(target_to_kwargs(target))
    return await get_message_records(**kwargs)


async def get_messages_plain_text_by_target(
    target: PlatformTarget, **kwargs
) -> List[str]:
    """根据 PlatformTarget 获取消息记录"""
    kwargs.update(target_to_kwargs(target))
    return await get_messages_plain_text(**kwargs)
