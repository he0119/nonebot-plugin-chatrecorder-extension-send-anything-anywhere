from pathlib import Path

import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS, App
from sqlalchemy import StaticPool, delete


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "sqlalchemy_database_url": "sqlite+aiosqlite:///:memory:",
        "datastore_engine_options": {"poolclass": StaticPool},
        "driver": "~none",
        "alembic_startup_check": False,
    }


@pytest.fixture
async def app(tmp_path: Path):
    # 加载插件
    nonebot.require("nonebot_plugin_cesaa")
    from nonebot_plugin_chatrecorder.model import MessageRecord
    from nonebot_plugin_orm import get_session, init_orm
    from nonebot_plugin_session_orm import SessionModel

    await init_orm()

    yield App()

    from nonebot_plugin_chatrecorder.model import MessageRecord
    from nonebot_plugin_session_orm import SessionModel

    # 清理数据
    async with get_session() as session, session.begin():
        await session.execute(delete(MessageRecord))
        await session.execute(delete(SessionModel))
