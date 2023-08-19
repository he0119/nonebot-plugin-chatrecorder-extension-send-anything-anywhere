from datetime import datetime
from typing import Iterable, List, Literal, Optional, Union

from nonebot.adapters import Message
from nonebot_plugin_chatrecorder import MessageRecord
from nonebot_plugin_saa import PlatformTarget
from nonebot_plugin_session import Session, SessionIdType, SessionLevel

async def get_message_records_by_target(
    target: PlatformTarget,
    *,
    session: Optional[Session] = None,
    id_type: SessionIdType = SessionIdType.GROUP_USER,
    include_platform: bool = True,
    include_bot_type: bool = True,
    include_bot_id: bool = True,
    bot_ids: Optional[Iterable[str]] = None,
    bot_types: Optional[Iterable[str]] = None,
    platforms: Optional[Iterable[str]] = None,
    levels: Optional[Iterable[Union[str, SessionLevel]]] = None,
    id1s: Optional[Iterable[str]] = None,
    id2s: Optional[Iterable[str]] = None,
    id3s: Optional[Iterable[str]] = None,
    exclude_id1s: Optional[Iterable[str]] = None,
    exclude_id2s: Optional[Iterable[str]] = None,
    exclude_id3s: Optional[Iterable[str]] = None,
    time_start: Optional[datetime] = None,
    time_stop: Optional[datetime] = None,
    types: Optional[Iterable[Literal["message", "message_sent"]]] = None,
) -> List[MessageRecord]: ...
async def get_messages_by_target(
    target: PlatformTarget,
    *,
    session: Optional[Session] = None,
    id_type: SessionIdType = SessionIdType.GROUP_USER,
    include_platform: bool = True,
    include_bot_type: bool = True,
    include_bot_id: bool = True,
    bot_ids: Optional[Iterable[str]] = None,
    bot_types: Optional[Iterable[str]] = None,
    platforms: Optional[Iterable[str]] = None,
    levels: Optional[Iterable[Union[str, SessionLevel]]] = None,
    id1s: Optional[Iterable[str]] = None,
    id2s: Optional[Iterable[str]] = None,
    id3s: Optional[Iterable[str]] = None,
    exclude_id1s: Optional[Iterable[str]] = None,
    exclude_id2s: Optional[Iterable[str]] = None,
    exclude_id3s: Optional[Iterable[str]] = None,
    time_start: Optional[datetime] = None,
    time_stop: Optional[datetime] = None,
    types: Optional[Iterable[Literal["message", "message_sent"]]] = None,
) -> List[Message]: ...
async def get_messages_plain_text_by_target(
    target: PlatformTarget,
    *,
    session: Optional[Session] = None,
    id_type: SessionIdType = SessionIdType.GROUP_USER,
    include_platform: bool = True,
    include_bot_type: bool = True,
    include_bot_id: bool = True,
    bot_ids: Optional[Iterable[str]] = None,
    bot_types: Optional[Iterable[str]] = None,
    platforms: Optional[Iterable[str]] = None,
    levels: Optional[Iterable[Union[str, SessionLevel]]] = None,
    id1s: Optional[Iterable[str]] = None,
    id2s: Optional[Iterable[str]] = None,
    id3s: Optional[Iterable[str]] = None,
    exclude_id1s: Optional[Iterable[str]] = None,
    exclude_id2s: Optional[Iterable[str]] = None,
    exclude_id3s: Optional[Iterable[str]] = None,
    time_start: Optional[datetime] = None,
    time_stop: Optional[datetime] = None,
    types: Optional[Iterable[Literal["message", "message_sent"]]] = None,
) -> List[str]: ...
