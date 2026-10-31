"""插件捕获、合并、注入的冒烟测试。"""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import astrbot_stub

PLUGIN_DIR = Path(__file__).resolve().parent.parent
PLUGIN_MAIN = PLUGIN_DIR / "main.py"
sys.path.insert(0, str(PLUGIN_DIR))
astrbot_stub.install()

spec = importlib.util.spec_from_file_location("reply_visible_main", PLUGIN_MAIN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
Plugin = mod.ReplyVisiblePlugin

CFG = {
    "enabled": True,
    "group_only": True,
    "whitelist_groups": [],
    "max_pending": 10,
    "text_limit": 800,
    "merge_window_ms": 0,
    "image_caption_enable": False,
    "vision_provider_id": "",
    "image_caption_prompt": "describe",
    "image_caption_limit": 300,
    "image_max_per_turn": 3,
    "inject_header": "<system_reminder>\n插件回复：",
    "no_learn_enable": True,
}


class Result:
    def __init__(self, text="", chain=None, llm=False):
        self.text = text
        self.chain = chain or []
        self.llm = llm

    def is_llm_result(self):
        return self.llm

    def get_plain_text(self):
        return self.text


class Event:
    unified_msg_origin = "napcat:GroupMessage:1"

    def __init__(self, result, message_str="/签到"):
        self.result = result
        self.message_str = message_str
        self._extras = {}

    def get_message_type(self):
        return astrbot_stub.MessageType.GROUP_MESSAGE

    def get_group_id(self):
        return "1"

    def get_result(self):
        return self.result

    def get_sender_id(self):
        return "10001"

    def get_sender_name(self):
        return "测试用户"

    def set_extra(self, key, value):
        self._extras[key] = value

    def get_extra(self, key, default=None):
        return self._extras.get(key, default)

    def plain_result(self, text):
        return types.SimpleNamespace(text=text)


class Req:
    def __init__(self):
        self.extra_user_content_parts = []


async def _run():
    plugin = Plugin(None, CFG)
    assert plugin.capture_before_send.__doc__
    assert plugin.capture_reply.__doc__
    assert plugin.inject_replies.__doc__
    assert plugin.reply_status.__doc__
    assert plugin.reply_debug.__doc__

    class FakeCommandFilter:
        def get_complete_command_names(self):
            return ["签到"]

    mod.star_map = {
        "test.plugin.main": types.SimpleNamespace(
            name="test_plugin", display_name="测试插件"
        )
    }
    event = Event(Result("签到成功，获得 888 灵石"))
    event.set_extra(
        "activated_handlers",
        [
            types.SimpleNamespace(
                handler_module_path="test.plugin.main",
                event_filters=[FakeCommandFilter()],
            )
        ],
    )
    assert plugin._plugin_info(event) == ("test_plugin", "测试插件")
    prefix = plugin._format_prefix(
        {
            "plugin_name": "test_plugin",
            "plugin_display_name": "测试插件",
            "sender_id": "10001",
            "sender_name": "测试用户",
            "source": "/签到",
        }
    )
    assert "插件：测试插件（test_plugin）" in prefix
    assert "回复对象：测试用户(10001)" in prefix

    await plugin.capture_reply(event)
    assert len(plugin._pending[event.unified_msg_origin]) == 1

    # 相同内容 5 秒内去重
    await plugin.capture_reply(event)
    assert len(plugin._pending[event.unified_msg_origin]) == 1

    # 图片只记录占位符（关闭识别）
    image_event = Event(Result("", [astrbot_stub.Image("http://example.com/card.png")]))
    await plugin.capture_reply(image_event)
    assert len(plugin._pending[event.unified_msg_origin]) == 2

    req = Req()
    await plugin.inject_replies(event, req)
    assert len(req.extra_user_content_parts) == 1
    part = req.extra_user_content_parts[0]
    text = part.text
    assert "888" in text
    assert "图片" in text
    assert "插件：测试插件（test_plugin）" in text
    assert "回复对象：测试用户(10001)" in text
    assert 'no_learn="true"' in text
    assert "plugin_reply_context" in text
    assert part.no_save is True
    assert len(plugin._pending[event.unified_msg_origin]) == 0

    # 注入后再次请求不应重复
    req2 = Req()
    await plugin.inject_replies(event, req2)
    assert len(req2.extra_user_content_parts) == 0

    # 发送前钩子捕获后，发送后兜底不再重复
    pre_plugin = Plugin(None, CFG)
    pre_event = Event(Result("发送前捕获"))
    await pre_plugin.capture_before_send(pre_event)
    assert len(pre_plugin._pending[pre_event.unified_msg_origin]) == 1
    await pre_plugin.capture_reply(pre_event)
    assert len(pre_plugin._pending[pre_event.unified_msg_origin]) == 1

    # 多段回复合并
    merge_plugin = Plugin(None, {**CFG, "merge_window_ms": 2000})
    await merge_plugin.capture_reply(Event(Result("第一段")))
    await merge_plugin.capture_reply(Event(Result("第二段")))
    queue = merge_plugin._pending["napcat:GroupMessage:1"]
    assert len(queue) == 1
    assert "第一段" in queue[0]["text"] and "第二段" in queue[0]["text"]

    # 调试指令
    debug_event = Event(Result("调试捕获"))
    debug_event.set_extra(
        "activated_handlers",
        [
            types.SimpleNamespace(
                handler_module_path="test.plugin.main",
                event_filters=[FakeCommandFilter()],
            )
        ],
    )
    await plugin.capture_reply(debug_event)
    debug_messages = [item.text async for item in plugin.reply_debug(debug_event)]
    assert debug_messages
    assert "已捕获" in debug_messages[0]
    assert "测试插件" in debug_messages[0]
    assert "测试用户(10001)" in debug_messages[0]

    # 关闭防学习标注时，仍保持临时注入
    plugin_off = Plugin(None, {**CFG, "no_learn_enable": False})
    event_off = Event(Result("签到成功，获得 888 灵石"))
    await plugin_off.capture_reply(event_off)
    req_off = Req()
    await plugin_off.inject_replies(event_off, req_off)
    assert len(req_off.extra_user_content_parts) == 1
    assert "no_learn" not in req_off.extra_user_content_parts[0].text
    assert req_off.extra_user_content_parts[0].no_save is True

    # LLM 回复不捕获
    llm_event = Event(Result("AI 自己的回复", llm=True))
    before = len(plugin._pending[llm_event.unified_msg_origin])
    await plugin.capture_reply(llm_event)
    assert len(plugin._pending[llm_event.unified_msg_origin]) == before


if __name__ == "__main__":
    asyncio.run(_run())
    print("smoke OK")
