from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_chatrecorder")
require("nonebot_plugin_saa")

from .record import get_message_records as get_message_records
from .record import get_messages as get_messages
from .record import get_messages_plain_text as get_messages_plain_text

__plugin_meta__ = PluginMetadata(
    name="聊天记录扩展",
    description="记录机器人收到和发出的消息",
    usage="请参考文档",
    type="library",
    homepage="https://github.com/he0119/nonebot-plugin-chatrecorder-extension-send-anything-anywhere",
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_chatrecorder", "nonebot_plugin_saa"
    ),
)
