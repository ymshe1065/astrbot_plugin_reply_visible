"""不依赖 AstrBot 运行时的冒烟测试：用 stub 验证捕获/去重/注入。"""

import asyncio
import importlib.util
import logging
import sys
import types
from pathlib import Path

PLUGIN_MAIN = Path(__file__).resolve().parent.parent / "main.py"

# ---------- stub astrbot modules ----------
astrbot = types.ModuleType("astrbot")
api = types.ModuleType("astrbot.api")
api.AstrBotConfig = dict
api.logger = logging.getLogger("stub")

event_mod = types.ModuleType("astrbot.api.event")
class AstrMessageEvent: ...
event_mod.AstrMessageEvent = AstrMessageEvent
class _Filter:
    def after_message_sent(self, *a, **k): return lambda f: f
    def on_llm_request(self, *a, **k): return lambda f: f
    def command(self, *a, **k): return lambda f: f
event_mod.filter = _Filter()

comp_mod = types.ModuleType("astrbot.api.message_components")
class Image:
    def __init__(self, url=""): self.url = url
class Plain:
    def __init__(self, text=""): self.text = text
comp_mod.Image = Image
comp_mod.Plain = Plain

platform_mod = types.ModuleType("astrbot.api.platform")
class MessageType:
    GROUP_MESSAGE = "group"
    PRIVATE_MESSAGE = "private"
platform_mod.MessageType = MessageType

star_mod = types.ModuleType("astrbot.api.star")
class Context: ...
class Star:
    def __init__(self, context=None): self.context = context
def register(*a, **k): return lambda cls: cls
star_mod.Context = Context
star_mod.Star = Star
star_mod.register = register

agent_mod = types.ModuleType("astrbot.core.agent.message")
class TextPart:
    def __init__(self, text=""):
        self.text = text
        self.no_save = False
    def mark_as_temp(self):
        self.no_save = True
        return self
agent_mod.TextPart = TextPart

for name, mod in {
    "astrbot": astrbot,
    "astrbot.api": api,
    "astrbot.api.event": event_mod,
    "astrbot.api.message_components": comp_mod,
    "astrbot.api.platform": platform_mod,
    "astrbot.api.star": star_mod,
    "astrbot.core": types.ModuleType("astrbot.core"),
    "astrbot.core.agent": types.ModuleType("astrbot.core.agent"),
    "astrbot.core.agent.message": agent_mod,
}.items():
    sys.modules[name] = mod

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
    def is_llm_result(self): return self.llm
    def get_plain_text(self): return self.text

class Event:
    unified_msg_origin = "napcat:GroupMessage:1"
    message_str = "/签到"
    def __init__(self, result): self.result = result
    def get_message_type(self): return MessageType.GROUP_MESSAGE
    def get_group_id(self): return "1"
    def get_result(self): return self.result

class Req:
    def __init__(self): self.extra_user_content_parts = []

async def _run():
    plugin = Plugin(None, CFG)
    event = Event(Result("签到成功，获得 888 灵石"))

    await plugin.capture_reply(event)
    assert len(plugin._pending[event.unified_msg_origin]) == 1

    # 相同内容 5 秒内去重
    await plugin.capture_reply(event)
    assert len(plugin._pending[event.unified_msg_origin]) == 1

    # 图片只记录占位符（关闭识别）
    image_event = Event(Result("", [Image("http://example.com/card.png")]))
    await plugin.capture_reply(image_event)
    assert len(plugin._pending[event.unified_msg_origin]) == 2

    req = Req()
    await plugin.inject_replies(event, req)
    assert len(req.extra_user_content_parts) == 1
    part = req.extra_user_content_parts[0]
    text = part.text
    assert "888" in text
    assert "图片" in text
    assert 'no_learn="true"' in text
    assert "plugin_reply_context" in text
    assert part.no_save is True
    assert len(plugin._pending[event.unified_msg_origin]) == 0

    # 注入后再次请求不应重复
    req2 = Req()
    await plugin.inject_replies(event, req2)
    assert len(req2.extra_user_content_parts) == 0

    # 关闭防学习标注时，仍保持临时注入
    plugin_off = Plugin(None, {**CFG, "no_learn_enable": False})
    event_off = Event(Result("签到成功，获得 888 灵石"))
    await plugin_off.capture_reply(event_off)
    req_off = Req()
    await plugin_off.inject_replies(event_off, req_off)
    assert len(req_off.extra_user_content_parts) == 1
    assert "no_learn" not in req_off.extra_user_content_parts[0].text
    assert req_off.extra_user_content_parts[0].no_save is True

if __name__ == "__main__":
    asyncio.run(_run())
    print("smoke OK")
