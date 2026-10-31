"""最小 AstrBot 运行时 stub，供插件单元测试使用。"""

from __future__ import annotations

import logging
import sys
import types


class Image:
    def __init__(self, url: str = "", file: str = "", path: str = ""):
        self.url = url
        self.file = file
        self.path = path


class Plain:
    def __init__(self, text: str = ""):
        self.text = text


class At:
    def __init__(self, qq: str = "", name: str = ""):
        self.qq = qq
        self.name = name


class Face:
    def __init__(self, id: int = 1):
        self.id = id


class Record:
    def __init__(self, file: str = "", text: str | None = None):
        self.file = file
        self.text = text


class Video:
    def __init__(self, file: str = ""):
        self.file = file


class File:
    def __init__(self, name: str = "", file: str = "", url: str = ""):
        self.name = name
        self.file_ = file
        self.url = url


class Json:
    def __init__(self, data=None):
        self.data = data if data is not None else {}


class Reply:
    def __init__(self, message_str: str = ""):
        self.message_str = message_str


class Poke:
    def __init__(self, id: str = "1"):
        self.id = id


class Forward:
    def __init__(self, id: str = "1"):
        self.id = id


class Node:
    def __init__(self, name: str = "", content=None):
        self.name = name
        self.content = content or []


class Nodes:
    def __init__(self, nodes=None):
        self.nodes = nodes or []


class Share:
    def __init__(self, title: str = "", content: str = "", url: str = ""):
        self.title = title
        self.content = content
        self.url = url


class Location:
    def __init__(self, title: str = "", content: str = ""):
        self.title = title
        self.content = content


class Unknown:
    def __init__(self, text: str = ""):
        self.text = text


class MessageType:
    GROUP_MESSAGE = "group"
    PRIVATE_MESSAGE = "private"


class AstrMessageEvent:
    pass


class _Filter:
    def _decorator(self, *args, **kwargs):
        return lambda fn: fn

    after_message_sent = _decorator
    on_decorating_result = _decorator
    on_llm_request = _decorator
    command = _decorator


class Context:
    pass


class Star:
    def __init__(self, context=None):
        self.context = context


def register(*args, **kwargs):
    return lambda cls: cls


class TextPart:
    def __init__(self, text: str = ""):
        self.text = text
        self.no_save = False

    def mark_as_temp(self):
        self.no_save = True
        return self


def install() -> None:
    """注册测试所需的 astrbot 模块。"""

    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    api.AstrBotConfig = dict
    api.logger = logging.getLogger("astrbot.stub")

    event_mod = types.ModuleType("astrbot.api.event")
    event_mod.AstrMessageEvent = AstrMessageEvent
    event_mod.filter = _Filter()

    comp_mod = types.ModuleType("astrbot.api.message_components")
    for cls in (
        Image,
        Plain,
        At,
        Face,
        Record,
        Video,
        File,
        Json,
        Reply,
        Poke,
        Forward,
        Node,
        Nodes,
        Share,
        Location,
        Unknown,
    ):
        setattr(comp_mod, cls.__name__, cls)

    platform_mod = types.ModuleType("astrbot.api.platform")
    platform_mod.MessageType = MessageType

    star_mod = types.ModuleType("astrbot.api.star")
    star_mod.Context = Context
    star_mod.Star = Star
    star_mod.register = register

    agent_mod = types.ModuleType("astrbot.core.agent.message")
    agent_mod.TextPart = TextPart

    modules = {
        "astrbot": astrbot,
        "astrbot.api": api,
        "astrbot.api.event": event_mod,
        "astrbot.api.message_components": comp_mod,
        "astrbot.api.platform": platform_mod,
        "astrbot.api.star": star_mod,
        "astrbot.core": types.ModuleType("astrbot.core"),
        "astrbot.core.agent": types.ModuleType("astrbot.core.agent"),
        "astrbot.core.agent.message": agent_mod,
    }
    sys.modules.update(modules)
