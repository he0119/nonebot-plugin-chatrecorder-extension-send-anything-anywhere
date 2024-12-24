from pathlib import Path

import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS, NONEBOT_START_LIFESPAN, App
from pytest_mock import MockerFixture
from sqlalchemy import StaticPool, delete


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "sqlalchemy_database_url": "sqlite+aiosqlite:///:memory:",
        "datastore_engine_options": {"poolclass": StaticPool},
        "driver": "~none",
        "alembic_startup_check": False,
    }
    config.stash[NONEBOT_START_LIFESPAN] = False


@pytest.fixture(scope="session", autouse=True)
async def after_nonebot_init(after_nonebot_init: None):
    # 加载插件
    nonebot.load_plugin("nonebot_plugin_cesaa")


@pytest.fixture
async def app(app: App, tmp_path: Path, mocker: MockerFixture):
    from nonebot_plugin_chatrecorder import MessageRecord
    from nonebot_plugin_orm import get_session, init_orm
    from nonebot_plugin_uninfo.orm import SessionModel

    mocker.patch("nonebot_plugin_orm._data_dir", tmp_path / "orm")

    await init_orm()

    yield app

    # 清理数据
    async with get_session() as session, session.begin():
        await session.execute(delete(MessageRecord))
        await session.execute(delete(SessionModel))
