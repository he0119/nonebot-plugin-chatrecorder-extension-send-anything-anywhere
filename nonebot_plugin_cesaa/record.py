from typing import List, Optional, Sequence

from nonebot.adapters import Message
from nonebot_plugin_chatrecorder import MessageRecord, deserialize_message
from nonebot_plugin_chatrecorder.record import filter_statement
from nonebot_plugin_orm import get_session
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
from nonebot_plugin_session_orm import SessionModel
from sqlalchemy import ColumnElement, select


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


async def get_message_records(
    *, target: Optional[PlatformTarget] = None, **kwargs
) -> Sequence[MessageRecord]:
    """获取消息记录

    参数:
      * ``target: Optional[PlatformTarget]``: 发送目标，传入时会根据 `PlatformTarget` 中的字段筛选
      * ``session: Optional[Session]``: 会话模型，传入时会根据 `session` 中的字段筛选
      * ``id_type: SessionIdType``: 会话 id 类型，仅在传入 `session` 时有效
      * ``include_platform: bool``: 是否限制平台类型，仅在传入 `session` 时有效
      * ``include_bot_type: bool``: 是否限制适配器类型，仅在传入 `session` 时有效
      * ``include_bot_id: bool``: 是否限制 bot id，仅在传入 `session` 时有效
      * ``bot_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``bot_types: Optional[Iterable[str]]``: 协议适配器类型列表，为空表示所有适配器
      * ``platforms: Optional[Iterable[str]]``: 平台类型列表，为空表示所有平台
      * ``levels: Optional[Iterable[Union[str, SessionLevel]]]``: 会话级别列表，为空表示所有级别
      * ``id1s: Optional[Iterable[str]]``: 会话 id1（用户级 id）列表，为空表示所有 id
      * ``id2s: Optional[Iterable[str]]``: 会话 id2（群组级 id）列表，为空表示所有 id
      * ``id3s: Optional[Iterable[str]]``: 会话 id3（两级群组级 id）列表，为空表示所有 id
      * ``exclude_id1s: Optional[Iterable[str]]``: 不包含的会话 id1（用户级 id）列表，为空表示不限制
      * ``exclude_id2s: Optional[Iterable[str]]``: 不包含的会话 id2（群组级 id）列表，为空表示不限制
      * ``exclude_id3s: Optional[Iterable[str]]``: 不包含的会话 id3（两级群组级 id）列表，为空表示不限制
      * ``time_start: Optional[datetime]``: 起始时间，为空表示不限制起始时间（传入带时区的时间或 UTC 时间）
      * ``time_stop: Optional[datetime]``: 结束时间，为空表示不限制结束时间（传入带时区的时间或 UTC 时间）
      * ``types: Optional[Iterable[Literal["message", "message_sent"]]]``: 消息事件类型列表，为空表示所有类型

    返回值:
      * ``List[MessageRecord]``: 消息记录列表
    """
    whereclause = filter_statement(**kwargs)
    if target:
        whereclause.extend(target_to_filter_statement(target))
    statement = (
        select(MessageRecord)
        .where(*whereclause)
        .join(SessionModel, SessionModel.id == MessageRecord.session_persist_id)
    )
    async with get_session() as db_session:
        records = (await db_session.scalars(statement)).all()
    return records


async def get_messages(
    *, target: Optional[PlatformTarget] = None, **kwargs
) -> Sequence[Message]:
    """获取消息记录的消息列表

    参数:
      * ``target: Optional[PlatformTarget]``: 发送目标，传入时会根据 `PlatformTarget` 中的字段筛选
      * ``session: Optional[Session]``: 会话模型，传入时会根据 `session` 中的字段筛选
      * ``id_type: SessionIdType``: 会话 id 类型，仅在传入 `session` 时有效
      * ``include_platform: bool``: 是否限制平台类型，仅在传入 `session` 时有效
      * ``include_bot_type: bool``: 是否限制适配器类型，仅在传入 `session` 时有效
      * ``include_bot_id: bool``: 是否限制 bot id，仅在传入 `session` 时有效
      * ``bot_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``bot_types: Optional[Iterable[str]]``: 协议适配器类型列表，为空表示所有适配器
      * ``platforms: Optional[Iterable[str]]``: 平台类型列表，为空表示所有平台
      * ``levels: Optional[Iterable[Union[str, SessionLevel]]]``: 会话级别列表，为空表示所有级别
      * ``id1s: Optional[Iterable[str]]``: 会话 id1（用户级 id）列表，为空表示所有 id
      * ``id2s: Optional[Iterable[str]]``: 会话 id2（群组级 id）列表，为空表示所有 id
      * ``id3s: Optional[Iterable[str]]``: 会话 id3（两级群组级 id）列表，为空表示所有 id
      * ``exclude_id1s: Optional[Iterable[str]]``: 不包含的会话 id1（用户级 id）列表，为空表示不限制
      * ``exclude_id2s: Optional[Iterable[str]]``: 不包含的会话 id2（群组级 id）列表，为空表示不限制
      * ``exclude_id3s: Optional[Iterable[str]]``: 不包含的会话 id3（两级群组级 id）列表，为空表示不限制
      * ``time_start: Optional[datetime]``: 起始时间，为空表示不限制起始时间（传入带时区的时间或 UTC 时间）
      * ``time_stop: Optional[datetime]``: 结束时间，为空表示不限制结束时间（传入带时区的时间或 UTC 时间）
      * ``types: Optional[Iterable[Literal["message", "message_sent"]]]``: 消息事件类型列表，为空表示所有类型

    返回值:
      * ``List[Message]``: 消息列表
    """
    whereclause = filter_statement(**kwargs)
    if target:
        whereclause.extend(target_to_filter_statement(target))
    statement = (
        select(MessageRecord.message, SessionModel.bot_type)
        .where(*whereclause)
        .join(SessionModel, SessionModel.id == MessageRecord.session_persist_id)
    )
    async with get_session() as db_session:
        results = (await db_session.execute(statement)).all()
    return [deserialize_message(result[1], result[0]) for result in results]


async def get_messages_plain_text(
    *, target: Optional[PlatformTarget] = None, **kwargs
) -> Sequence[str]:
    """获取消息记录的纯文本消息列表

    参数:
      * ``target: Optional[PlatformTarget]``: 发送目标，传入时会根据 `PlatformTarget` 中的字段筛选
      * ``session: Optional[Session]``: 会话模型，传入时会根据 `session` 中的字段筛选
      * ``id_type: SessionIdType``: 会话 id 类型，仅在传入 `session` 时有效
      * ``include_platform: bool``: 是否限制平台类型，仅在传入 `session` 时有效
      * ``include_bot_type: bool``: 是否限制适配器类型，仅在传入 `session` 时有效
      * ``include_bot_id: bool``: 是否限制 bot id，仅在传入 `session` 时有效
      * ``bot_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``bot_types: Optional[Iterable[str]]``: 协议适配器类型列表，为空表示所有适配器
      * ``platforms: Optional[Iterable[str]]``: 平台类型列表，为空表示所有平台
      * ``levels: Optional[Iterable[Union[str, SessionLevel]]]``: 会话级别列表，为空表示所有级别
      * ``id1s: Optional[Iterable[str]]``: 会话 id1（用户级 id）列表，为空表示所有 id
      * ``id2s: Optional[Iterable[str]]``: 会话 id2（群组级 id）列表，为空表示所有 id
      * ``id3s: Optional[Iterable[str]]``: 会话 id3（两级群组级 id）列表，为空表示所有 id
      * ``exclude_id1s: Optional[Iterable[str]]``: 不包含的会话 id1（用户级 id）列表，为空表示不限制
      * ``exclude_id2s: Optional[Iterable[str]]``: 不包含的会话 id2（群组级 id）列表，为空表示不限制
      * ``exclude_id3s: Optional[Iterable[str]]``: 不包含的会话 id3（两级群组级 id）列表，为空表示不限制
      * ``time_start: Optional[datetime]``: 起始时间，为空表示不限制起始时间（传入带时区的时间或 UTC 时间）
      * ``time_stop: Optional[datetime]``: 结束时间，为空表示不限制结束时间（传入带时区的时间或 UTC 时间）
      * ``types: Optional[Iterable[Literal["message", "message_sent"]]]``: 消息事件类型列表，为空表示所有类型

    返回值:
      * ``List[str]``: 纯文本消息列表
    """
    whereclause = filter_statement(**kwargs)
    if target:
        whereclause.extend(target_to_filter_statement(target))
    statement = (
        select(MessageRecord.plain_text)
        .where(*whereclause)
        .join(SessionModel, SessionModel.id == MessageRecord.session_persist_id)
    )
    async with get_session() as db_session:
        records = (await db_session.scalars(statement)).all()
    return records
