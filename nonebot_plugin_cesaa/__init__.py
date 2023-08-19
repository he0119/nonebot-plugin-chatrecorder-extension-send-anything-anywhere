from nonebot import require

require("nonebot_plugin_chatrecorder")
require("nonebot_plugin_saa")

from .record import get_message_records_by_target as get_message_records_by_target
from .record import get_messages_by_target as get_messages_by_target
from .record import (
    get_messages_plain_text_by_target as get_messages_plain_text_by_target,
)
