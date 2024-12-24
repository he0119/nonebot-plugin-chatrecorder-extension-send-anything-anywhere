from pathlib import Path

import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS, App
from pytest_mock import MockerFixture
from sqlalchemy import StaticPool, delete


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "sqlalchemy_database_url": "sqlite+aiosqlite:///:memory:",
        "datastore_engine_options": {"poolclass": StaticPool},
        "driver": "~none",
        "alembic_startup_check": False,
    }


@pytest.fixture
async def app(tmp_path: Path, mocker: MockerFixture):
    # 加载插件
    nonebot.require("nonebot_plugin_cesaa")
    from nonebot_plugin_chatrecorder.model import MessageRecord
    from nonebot_plugin_orm import get_session, init_orm
    from nonebot_plugin_uninfo.orm import BotModel, SceneModel, SessionModel, UserModel

    mocker.patch("nonebot_plugin_orm._data_dir", tmp_path / "orm")

    await init_orm()

    yield App()

    # 清理数据
    async with get_session() as session, session.begin():
        await session.execute(delete(MessageRecord))
        await session.execute(delete(SessionModel))
        await session.execute(delete(SceneModel))
        await session.execute(delete(BotModel))
        await session.execute(delete(UserModel))
