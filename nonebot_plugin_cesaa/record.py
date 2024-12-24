# ruff: noqa: E501
from collections.abc import Sequence
from typing import Optional

from nonebot.adapters import Message
from nonebot_plugin_chatrecorder import MessageRecord, deserialize_message
from nonebot_plugin_chatrecorder.record import filter_statement
from nonebot_plugin_chatrecorder.utils import scope_value
from nonebot_plugin_orm import get_session
from nonebot_plugin_saa import (
    PlatformTarget,
    TargetDiscordChannel,
    TargetDoDoChannel,
    TargetDoDoPrivate,
    TargetFeishuGroup,
    TargetFeishuPrivate,
    TargetKaiheilaChannel,
    TargetKaiheilaPrivate,
    TargetOB12Unknow,
    TargetQQGroup,
    TargetQQGroupOpenId,
    TargetQQGuildChannel,
    TargetQQGuildDirect,
    TargetQQPrivate,
    TargetQQPrivateOpenId,
    TargetSatoriUnknown,
    TargetTelegramCommon,
    TargetTelegramForum,
)
from nonebot_plugin_uninfo import SceneType, SupportScope
from nonebot_plugin_uninfo.orm import BotModel, SceneModel, SessionModel, UserModel
from sqlalchemy import ColumnElement, select


def target_to_filter_statement(target: PlatformTarget) -> list[ColumnElement[bool]]:
    """将 PlatformTarget 转换为 chatrecorder 所需参数"""
    scope = None
    scene_id = None
    scene_type = None
    if isinstance(target, TargetQQPrivate):
        scope = SupportScope.qq_client
        scene_id = str(target.user_id)
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetQQGroup):
        scope = SupportScope.qq_client
        scene_id = str(target.group_id)
        scene_type = SceneType.GROUP
    elif isinstance(target, TargetQQGuildDirect):
        scope = SupportScope.qq_guild
        scene_id = str(target.recipient_id)
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetQQGuildChannel):
        scope = SupportScope.qq_guild
        scene_id = str(target.channel_id)
        scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetQQPrivateOpenId):
        scope = SupportScope.qq_api
        scene_id = target.user_openid
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetQQGroupOpenId):
        scope = SupportScope.qq_api
        scene_id = target.group_openid
        scene_type = SceneType.GROUP
    elif isinstance(target, TargetKaiheilaPrivate):
        scope = SupportScope.kook
        scene_id = target.user_id
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetKaiheilaChannel):
        scope = SupportScope.kook
        scene_id = target.channel_id
        scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetFeishuPrivate):
        scope = SupportScope.feishu
        scene_id = target.open_id
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetFeishuGroup):
        scope = SupportScope.feishu
        scene_id = target.chat_id
        scene_type = SceneType.GROUP
    elif isinstance(target, TargetTelegramCommon):
        scope = SupportScope.telegram
        scene_id = str(target.chat_id)
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetTelegramForum):
        scope = SupportScope.telegram
        scene_id = str(target.message_thread_id)
        scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetDoDoPrivate):
        scope = SupportScope.dodo
        scene_id = target.dodo_source_id
        scene_type = SceneType.PRIVATE
    elif isinstance(target, TargetDoDoChannel):
        scope = SupportScope.dodo
        scene_id = target.channel_id
        scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetDiscordChannel):
        scope = SupportScope.discord
        scene_id = target.channel_id
        scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetOB12Unknow):
        scope = SupportScope.ensure_ob12(target.platform)
        if target.detail_type == "private":
            scene_id = target.user_id
            scene_type = SceneType.PRIVATE
        elif target.detail_type == "group":
            scene_id = target.group_id
            scene_type = SceneType.GROUP
        else:
            scene_id = target.channel_id
            scene_type = SceneType.CHANNEL_TEXT
    elif isinstance(target, TargetSatoriUnknown):
        scope = SupportScope.ensure_satori(target.platform)
        if target.channel_id is None:
            scene_id = target.user_id
            scene_type = SceneType.PRIVATE
        elif target.guild_id is None:
            scene_id = target.channel_id
            scene_type = SceneType.GROUP
        else:
            scene_id = target.channel_id
            scene_type = SceneType.CHANNEL_TEXT
    else:
        raise ValueError(f"不支持的 PlatformTarget 类型：{target}")

    whereclause: list[ColumnElement[bool]] = []
    if scope is not None:
        whereclause.append(BotModel.scope == scope_value(scope))
    if scene_id:
        whereclause.append(SceneModel.scene_id == scene_id)
    if scene_type is not None:
        whereclause.append(SceneModel.scene_type == scene_type.value)
    return whereclause


async def get_message_records(
    *, target: Optional[PlatformTarget] = None, **kwargs
) -> Sequence[MessageRecord]:
    """获取消息记录

    参数:
      * ``target: Optional[PlatformTarget]``: 发送目标，传入时会根据 `PlatformTarget` 中的字段筛选
      * ``session: Optional[Session]``: 会话模型，传入时会根据 `session` 中的字段筛选
      * ``id_type: SessionIdType``: 会话 id 类型，仅在传入 `session` 时有效
      * ``filter_self_id: bool``: 是否筛选 bot id，仅在传入 `session` 时有效
      * ``filter_adapter: bool``: 是否筛选适配器类型，仅在传入 `session` 时有效
      * ``filter_scope: bool``: 是否筛选平台类型，仅在传入 `session` 时有效
      * ``filter_scene: bool``: 是否筛选事件场景，仅在传入 `session` 时有效
      * ``filter_user: bool``: 是否筛选用户，仅在传入 `session` 时有效
      * ``self_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 适配器类型列表，为空表示所有适配器
      * ``scopes: Optional[Iterable[Union[str, SupportScope]]]``: 平台类型列表，为空表示所有平台
      * ``scene_types: Optional[Iterable[Union[str, SceneType]]]``: 事件场景类型列表，为空表示所有类型
      * ``scene_ids: Optional[Iterable[str]]``: 事件场景 id 列表，为空表示所有 id
      * ``user_ids: Optional[Iterable[str]]``: 用户 id 列表，为空表示所有 id
      * ``exclude_self_ids: Optional[Iterable[str]]``: 不包含的 bot id 列表，为空表示不限制
      * ``exclude_adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 不包含的适配器类型列表，为空表示不限制
      * ``exclude_scopes: Optional[Iterable[Union[str, SupportScope]]]``: 不包含的平台类型列表，为空表示不限制
      * ``exclude_scene_types: Optional[Iterable[Union[str, SceneType]]]``: 不包含的事件场景类型列表，为空表示不限制
      * ``exclude_scene_ids: Optional[Iterable[str]]``: 不包含的事件场景 id 列表，为空表示不限制
      * ``exclude_user_ids: Optional[Iterable[str]]``: 不包含的用户 id 列表，为空表示不限制
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
        .join(BotModel, BotModel.id == SessionModel.bot_persist_id)
        .join(SceneModel, SceneModel.id == SessionModel.scene_persist_id)
        .join(UserModel, UserModel.id == SessionModel.user_persist_id)
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
      * ``filter_self_id: bool``: 是否筛选 bot id，仅在传入 `session` 时有效
      * ``filter_adapter: bool``: 是否筛选适配器类型，仅在传入 `session` 时有效
      * ``filter_scope: bool``: 是否筛选平台类型，仅在传入 `session` 时有效
      * ``filter_scene: bool``: 是否筛选事件场景，仅在传入 `session` 时有效
      * ``filter_user: bool``: 是否筛选用户，仅在传入 `session` 时有效
      * ``self_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 适配器类型列表，为空表示所有适配器
      * ``scopes: Optional[Iterable[Union[str, SupportScope]]]``: 平台类型列表，为空表示所有平台
      * ``scene_types: Optional[Iterable[Union[str, SceneType]]]``: 事件场景类型列表，为空表示所有类型
      * ``scene_ids: Optional[Iterable[str]]``: 事件场景 id 列表，为空表示所有 id
      * ``user_ids: Optional[Iterable[str]]``: 用户 id 列表，为空表示所有 id
      * ``exclude_self_ids: Optional[Iterable[str]]``: 不包含的 bot id 列表，为空表示不限制
      * ``exclude_adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 不包含的适配器类型列表，为空表示不限制
      * ``exclude_scopes: Optional[Iterable[Union[str, SupportScope]]]``: 不包含的平台类型列表，为空表示不限制
      * ``exclude_scene_types: Optional[Iterable[Union[str, SceneType]]]``: 不包含的事件场景类型列表，为空表示不限制
      * ``exclude_scene_ids: Optional[Iterable[str]]``: 不包含的事件场景 id 列表，为空表示不限制
      * ``exclude_user_ids: Optional[Iterable[str]]``: 不包含的用户 id 列表，为空表示不限制
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
        select(MessageRecord.message, BotModel.adapter)
        .where(*whereclause)
        .join(SessionModel, SessionModel.id == MessageRecord.session_persist_id)
        .join(BotModel, BotModel.id == SessionModel.bot_persist_id)
        .join(SceneModel, SceneModel.id == SessionModel.scene_persist_id)
        .join(UserModel, UserModel.id == SessionModel.user_persist_id)
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
      * ``filter_self_id: bool``: 是否筛选 bot id，仅在传入 `session` 时有效
      * ``filter_adapter: bool``: 是否筛选适配器类型，仅在传入 `session` 时有效
      * ``filter_scope: bool``: 是否筛选平台类型，仅在传入 `session` 时有效
      * ``filter_scene: bool``: 是否筛选事件场景，仅在传入 `session` 时有效
      * ``filter_user: bool``: 是否筛选用户，仅在传入 `session` 时有效
      * ``self_ids: Optional[Iterable[str]]``: bot id 列表，为空表示所有 bot id
      * ``adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 适配器类型列表，为空表示所有适配器
      * ``scopes: Optional[Iterable[Union[str, SupportScope]]]``: 平台类型列表，为空表示所有平台
      * ``scene_types: Optional[Iterable[Union[str, SceneType]]]``: 事件场景类型列表，为空表示所有类型
      * ``scene_ids: Optional[Iterable[str]]``: 事件场景 id 列表，为空表示所有 id
      * ``user_ids: Optional[Iterable[str]]``: 用户 id 列表，为空表示所有 id
      * ``exclude_self_ids: Optional[Iterable[str]]``: 不包含的 bot id 列表，为空表示不限制
      * ``exclude_adapters: Optional[Iterable[Union[str, SupportAdapter]]]``: 不包含的适配器类型列表，为空表示不限制
      * ``exclude_scopes: Optional[Iterable[Union[str, SupportScope]]]``: 不包含的平台类型列表，为空表示不限制
      * ``exclude_scene_types: Optional[Iterable[Union[str, SceneType]]]``: 不包含的事件场景类型列表，为空表示不限制
      * ``exclude_scene_ids: Optional[Iterable[str]]``: 不包含的事件场景 id 列表，为空表示不限制
      * ``exclude_user_ids: Optional[Iterable[str]]``: 不包含的用户 id 列表，为空表示不限制
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
        .join(BotModel, BotModel.id == SessionModel.bot_persist_id)
        .join(SceneModel, SceneModel.id == SessionModel.scene_persist_id)
        .join(UserModel, UserModel.id == SessionModel.user_persist_id)
    )
    async with get_session() as db_session:
        records = (await db_session.scalars(statement)).all()
    return records
