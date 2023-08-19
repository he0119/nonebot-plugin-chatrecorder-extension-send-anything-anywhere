from datetime import datetime
from typing import List

import pytest
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message
from nonebot.adapters.onebot.v12 import Adapter as AdapterV12
from nonebot.adapters.onebot.v12 import Bot as BotV12
from nonebot.adapters.onebot.v12 import Message as MessageV12
from nonebug import App


@pytest.fixture
async def message_record(app: App):
    from nonebot_plugin_chatrecorder import serialize_message
    from nonebot_plugin_chatrecorder.model import MessageRecord
    from nonebot_plugin_datastore import create_session
    from nonebot_plugin_session import Session, SessionLevel
    from nonebot_plugin_session.model import get_or_add_session_model

    async with app.test_api() as ctx:
        adapter = Adapter(get_driver())
        adapter_v12 = AdapterV12(get_driver())
        bot = ctx.create_bot(base=Bot, adapter=adapter, auto_connect=False)
        bot_v12 = ctx.create_bot(
            base=BotV12,
            adapter=adapter_v12,
            auto_connect=False,
            platform="test",
            impl="test",
        )

    sessions = [
        Session(
            bot_id="test",
            bot_type="OneBot V11",
            platform="qq",
            level=SessionLevel.LEVEL2,
            id1="bot",
            id2="10000",
            id3=None,
        ),
        Session(
            bot_id="test",
            bot_type="OneBot V11",
            platform="qq",
            level=SessionLevel.LEVEL2,
            id1="10",
            id2="10000",
            id3=None,
        ),
        Session(
            bot_id="test",
            bot_type="OneBot V12",
            platform="qqguild",
            level=SessionLevel.LEVEL3,
            id1="bot",
            id2="100000",
            id3="10000",
        ),
        Session(
            bot_id="test",
            bot_type="OneBot V12",
            platform="qqguild",
            level=SessionLevel.LEVEL3,
            id1="10",
            id2="100000",
            id3="10000",
        ),
    ]
    session_ids: List[int] = []
    async with create_session() as db_session:
        for session in sessions:
            session_model = await get_or_add_session_model(session, db_session)
            session_ids.append(session_model.id)

    records = [
        MessageRecord(
            session_id=session_ids[0],
            time=datetime(2022, 1, 2, 4, 0, 0),
            type="message_sent",
            message_id="1",
            message=serialize_message(bot, Message("qq-10000-bot")),
            plain_text="qq-10000-bot",
        ),
        MessageRecord(
            session_id=session_ids[1],
            time=datetime(2022, 1, 2, 4, 0, 0),
            type="message",
            message_id="2",
            message=serialize_message(bot, Message("qq-10000-10")),
            plain_text="qq-10000-10",
        ),
        MessageRecord(
            session_id=session_ids[2],
            time=datetime(2022, 1, 2, 4, 0, 0),
            type="message_sent",
            message_id="3",
            message=serialize_message(bot, Message("qqguild-100000-10000-bot")),
            plain_text="qqguild-100000-10000-bot",
        ),
        MessageRecord(
            session_id=session_ids[3],
            time=datetime(2022, 1, 2, 4, 0, 0),
            type="message",
            message_id="4",
            message=serialize_message(bot_v12, MessageV12("qqguild-100000-10000-10")),
            plain_text="qqguild-100000-10000-10",
        ),
    ]
    async with create_session() as db_session:
        db_session.add_all(records)
        await db_session.commit()


async def test_target(app: App, message_record: None):
    from nonebot_plugin_saa import TargetQQGroup

    from nonebot_plugin_cesaa import get_messages_plain_text_by_target

    target = TargetQQGroup(group_id=10000)

    msgs = await get_messages_plain_text_by_target(target)
    assert msgs == ["qq-10000-bot", "qq-10000-10"]

    msgs = await get_messages_plain_text_by_target(
        target,
        types=["message"],  # 排除机器人自己发的消息
    )
    assert msgs == ["qq-10000-10"]

    # target 与主动提供的 id 相互独立
    msgs = await get_messages_plain_text_by_target(
        target,
        id1s=["10"],
    )
    assert msgs == ["qq-10000-10"]

    msgs = await get_messages_plain_text_by_target(
        target,
        types=["message"],
        id1s=["11"],
    )
    assert msgs == []
