from typing import List, Sequence

from nonebot.adapters import Message
from nonebot_plugin_chatrecorder import MessageRecord, deserialize_message
from nonebot_plugin_chatrecorder.record import filter_statement
from nonebot_plugin_datastore import create_session
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
from nonebot_plugin_session import Session, SessionIdType, SessionLevel
from nonebot_plugin_session.model import SessionModel
from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import ColumnElement


def target_to_filter_statement(target: PlatformTarget) -> List[ColumnElement[bool]]:
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

    whereclause: List[ColumnElement[bool]] = []
    if platform is not None:
        whereclause.append(SessionModel.platform == platform)
    if id1 is not None:
        whereclause.append(SessionModel.id1 == id1)
    if id2 is not None:
        whereclause.append(SessionModel.id2 == id2)
    if id3 is not None:
        whereclause.append(SessionModel.id3 == id3)
    return whereclause


async def get_message_records_by_target(
    target: PlatformTarget, **kwargs
) -> Sequence[MessageRecord]:
    """根据 PlatformTarget 获取消息记录列表"""
    whereclause = filter_statement(**kwargs)
    whereclause.extend(target_to_filter_statement(target))
    statement = (
        select(MessageRecord)
        .where(*whereclause)
        .join(SessionModel)
        .options(selectinload(MessageRecord.session))
    )
    async with create_session() as db_session:
        records = (await db_session.scalars(statement)).all()
    return records


async def get_messages_by_target(**kwargs) -> Sequence[Message]:
    """根据 PlatformTarget 获取消息列表"""
    records = await get_message_records_by_target(**kwargs)
    return [
        deserialize_message(record.session.bot_type, record.message)
        for record in records
    ]


async def get_messages_plain_text_by_target(
    target: PlatformTarget, **kwargs
) -> Sequence[str]:
    """根据 PlatformTarget 获取纯文本消息列表"""
    whereclause = filter_statement(**kwargs)
    whereclause.extend(target_to_filter_statement(target))
    statement = select(MessageRecord.plain_text).where(*whereclause).join(SessionModel)
    async with create_session() as db_session:
        records = (await db_session.scalars(statement)).all()
    return records
