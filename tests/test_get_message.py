from datetime import datetime, timezone

import pytest
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message
from nonebot.adapters.onebot.v12 import Adapter as AdapterV12
from nonebot.adapters.onebot.v12 import Bot as BotV12
from nonebot.adapters.onebot.v12 import Message as MessageV12
from nonebug import App


@pytest.fixture
async def _message_record(app: App):
    from nonebot_plugin_chatrecorder import serialize_message
    from nonebot_plugin_chatrecorder.model import MessageRecord
    from nonebot_plugin_orm import get_session
    from nonebot_plugin_uninfo import (
        Scene,
        SceneType,
        Session,
        SupportAdapter,
        SupportScope,
        User,
    )
    from nonebot_plugin_uninfo.orm import get_session_persist_id

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
            self_id="test",
            adapter=SupportAdapter.onebot11,
            scope=SupportScope.qq_client,
            scene=Scene("10000", SceneType.GROUP),
            user=User("bot"),
        ),
        Session(
            self_id="test",
            adapter=SupportAdapter.onebot11,
            scope=SupportScope.qq_client,
            scene=Scene("10000", SceneType.GROUP),
            user=User("10"),
        ),
        Session(
            self_id="test",
            adapter=SupportAdapter.onebot12,
            scope=SupportScope.qq_guild,
            scene=Scene(
                "100000", SceneType.CHANNEL_TEXT, parent=Scene("10000", SceneType.GUILD)
            ),
            user=User("bot"),
        ),
        Session(
            self_id="test",
            adapter=SupportAdapter.onebot12,
            scope=SupportScope.qq_guild,
            scene=Scene(
                "100000", SceneType.CHANNEL_TEXT, parent=Scene("10000", SceneType.GUILD)
            ),
            user=User("10"),
        ),
    ]
    session_ids: list[int] = []
    async with get_session() as db_session:
        for session in sessions:
            session_id = await get_session_persist_id(session)
            session_ids.append(session_id)

    records = [
        MessageRecord(
            session_persist_id=session_ids[0],
            time=datetime(2022, 1, 2, 4, 0, 0, tzinfo=timezone.utc),
            type="message_sent",
            message_id="1",
            message=serialize_message(bot, Message("qq-10000-bot")),
            plain_text="qq-10000-bot",
        ),
        MessageRecord(
            session_persist_id=session_ids[1],
            time=datetime(2022, 1, 2, 4, 0, 0, tzinfo=timezone.utc),
            type="message",
            message_id="2",
            message=serialize_message(bot, Message("qq-10000-10")),
            plain_text="qq-10000-10",
        ),
        MessageRecord(
            session_persist_id=session_ids[2],
            time=datetime(2022, 1, 2, 4, 0, 0, tzinfo=timezone.utc),
            type="message_sent",
            message_id="3",
            message=serialize_message(bot, Message("qqguild-100000-10000-bot")),
            plain_text="qqguild-100000-10000-bot",
        ),
        MessageRecord(
            session_persist_id=session_ids[3],
            time=datetime(2022, 1, 2, 4, 0, 0, tzinfo=timezone.utc),
            type="message",
            message_id="4",
            message=serialize_message(bot_v12, MessageV12("qqguild-100000-10000-10")),
            plain_text="qqguild-100000-10000-10",
        ),
    ]
    async with get_session() as db_session:
        db_session.add_all(records)
        await db_session.commit()


@pytest.mark.usefixtures("_message_record")
async def test_target(app: App):
    from nonebot_plugin_saa import TargetQQGroup

    from nonebot_plugin_cesaa import get_messages

    msgs = await get_messages()
    assert msgs == [
        Message("qq-10000-bot"),
        Message("qq-10000-10"),
        MessageV12("qqguild-100000-10000-bot"),
        MessageV12("qqguild-100000-10000-10"),
    ]

    target = TargetQQGroup(group_id=10000)

    msgs = await get_messages(target=target)
    assert msgs == [Message("qq-10000-bot"), Message("qq-10000-10")]

    msgs = await get_messages(
        target=target,
        types=["message"],  # 排除机器人自己发的消息
    )
    assert msgs == [Message("qq-10000-10")]

    # target 与主动提供的 id 相互独立
    msgs = await get_messages(
        target=target,
        user_ids=["10"],
    )
    assert msgs == [Message("qq-10000-10")]

    msgs = await get_messages(
        target=target,
        types=["message"],
        user_ids=["11"],
    )
    assert msgs == []


@pytest.mark.usefixtures("_message_record")
async def test_target_record(app: App):
    from nonebot_plugin_saa import TargetQQGroup

    from nonebot_plugin_cesaa import get_message_records

    msgs = await get_message_records()
    plain_text = [msg.plain_text for msg in msgs]
    assert plain_text == [
        "qq-10000-bot",
        "qq-10000-10",
        "qqguild-100000-10000-bot",
        "qqguild-100000-10000-10",
    ]

    target = TargetQQGroup(group_id=10000)

    msgs = await get_message_records(target=target)
    plain_text = [msg.plain_text for msg in msgs]
    assert plain_text == ["qq-10000-bot", "qq-10000-10"]

    msgs = await get_message_records(
        target=target,
        types=["message"],  # 排除机器人自己发的消息
    )
    plain_text = [msg.plain_text for msg in msgs]
    assert plain_text == ["qq-10000-10"]

    # target 与主动提供的 id 相互独立
    msgs = await get_message_records(
        target=target,
        user_ids=["10"],
    )
    plain_text = [msg.plain_text for msg in msgs]
    assert plain_text == ["qq-10000-10"]

    msgs = await get_message_records(
        target=target,
        types=["message"],
        user_ids=["11"],
    )
    assert msgs == []


@pytest.mark.usefixtures("_message_record")
async def test_target_plain_text(app: App):
    from nonebot_plugin_saa import TargetQQGroup

    from nonebot_plugin_cesaa import get_messages_plain_text

    msgs = await get_messages_plain_text()
    assert msgs == [
        "qq-10000-bot",
        "qq-10000-10",
        "qqguild-100000-10000-bot",
        "qqguild-100000-10000-10",
    ]

    target = TargetQQGroup(group_id=10000)

    msgs = await get_messages_plain_text(target=target)
    assert msgs == ["qq-10000-bot", "qq-10000-10"]

    msgs = await get_messages_plain_text(
        target=target,
        types=["message"],  # 排除机器人自己发的消息
    )
    assert msgs == ["qq-10000-10"]

    # target 与主动提供的 id 相互独立
    msgs = await get_messages_plain_text(
        target=target,
        user_ids=["10"],
    )
    assert msgs == ["qq-10000-10"]

    msgs = await get_messages_plain_text(
        target=target,
        types=["message"],
        user_ids=["11"],
    )
    assert msgs == []
