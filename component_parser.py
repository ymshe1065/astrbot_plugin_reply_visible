"""把 AstrBot 消息链转换成可注入 AI 的文本和图片引用。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable

try:  # AstrBot 公开导出
    from astrbot.api import message_components as Comp
except Exception:  # pragma: no cover - 兼容旧版导入路径
    from astrbot.core.message import components as Comp


_JSON_KEYS = (
    "title",
    "desc",
    "description",
    "prompt",
    "text",
    "content",
    "summary",
    "name",
    "nickname",
    "tag",
    "message",
)
_JSON_CONTAINER_KEYS = ("meta", "detail_1", "detail", "data")
_SKIP_JSON_VALUE_PREFIXES = (
    "http://",
    "https://",
    "data:",
    "base64://",
)


@dataclass
class ExtractedContent:
    """一条插件回复的可注入内容。"""

    text: str = ""
    image_refs: list[str] = field(default_factory=list)
    kinds: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)


class _Extractor:
    def __init__(
        self,
        *,
        max_chars: int,
        max_images: int,
        max_nodes: int,
        max_depth: int,
    ) -> None:
        self.max_chars = max(0, max_chars)
        self.max_images = max(0, max_images)
        self.max_nodes = max(0, max_nodes)
        self.max_depth = max(0, max_depth)
        self.parts: list[str] = []
        self.image_refs: list[str] = []
        self.kinds: list[str] = []
        self.unknown: list[str] = []
        self._chars = 0
        self._nodes = 0
        self._truncated = False

    def result(self) -> ExtractedContent:
        text = " ".join(part for part in self.parts if part).strip()
        if self._truncated and text:
            text += "…（已截断）"
        return ExtractedContent(
            text=text,
            image_refs=self.image_refs,
            kinds=self.kinds,
            unknown=self.unknown,
        )

    def _kind(self, name: str) -> None:
        if name and name not in self.kinds:
            self.kinds.append(name)

    def _add_text(self, value: Any) -> None:
        text = str(value or "").strip()
        if not text or self._chars >= self.max_chars:
            return
        remaining = self.max_chars - self._chars
        if len(text) > remaining:
            text = text[:remaining].rstrip() + "…"
            self._truncated = True
        self.parts.append(text)
        self._chars += len(text)

    def _add_image(self, value: Any) -> None:
        ref = str(value or "").strip()
        if not ref or len(self.image_refs) >= self.max_images:
            return
        if ref not in self.image_refs:
            self.image_refs.append(ref)

    def walk(self, chain: Iterable[Any] | None, depth: int = 0) -> None:
        if depth > self.max_depth:
            self._add_text("[嵌套层级过深]")
            return
        for comp in chain or []:
            self._walk_component(comp, depth)

    def _walk_component(self, comp: Any, depth: int) -> None:
        if isinstance(comp, Comp.Plain):
            self._kind("Plain")
            self._add_text(getattr(comp, "text", ""))
            return
        if isinstance(comp, Comp.At):
            self._kind("At")
            qq = str(getattr(comp, "qq", "") or "")
            if qq == "all":
                self._add_text("@全体成员")
            else:
                name = getattr(comp, "name", "") or qq
                self._add_text(f"@{name}" if name else "@某人")
            return
        if isinstance(comp, Comp.Image):
            self._kind("Image")
            for attr in ("url", "file", "path"):
                ref = getattr(comp, attr, None)
                if ref:
                    self._add_image(ref)
                    return
            return
        if isinstance(comp, Comp.Json):
            self._kind("Json")
            payload = self._json_text(getattr(comp, "data", None))
            self._add_text(f"[JSON卡片] {payload}" if payload else "[JSON卡片]")
            return
        if isinstance(comp, Comp.Nodes):
            self._kind("Nodes")
            self._add_text("[合并转发]")
            for node in getattr(comp, "nodes", []) or []:
                self._walk_node(node, depth)
            return
        if isinstance(comp, Comp.Node):
            self._kind("Node")
            self._walk_node(comp, depth)
            return
        if isinstance(comp, Comp.Forward):
            self._kind("Forward")
            self._add_text("[合并转发消息]")
            return
        if isinstance(comp, Comp.File):
            self._kind("File")
            name = str(getattr(comp, "name", "") or "").strip()
            self._add_text(f"[文件] {name}" if name else "[文件]")
            return
        if isinstance(comp, Comp.Record):
            self._kind("Record")
            text = str(getattr(comp, "text", "") or "").strip()
            self._add_text(f"[语音] {text}" if text else "[语音]")
            return
        if isinstance(comp, Comp.Video):
            self._kind("Video")
            self._add_text("[视频]")
            return
        if isinstance(comp, Comp.Reply):
            self._kind("Reply")
            quoted = str(getattr(comp, "message_str", "") or "").strip()
            if quoted:
                self._add_text(f"[引用] {quoted[:80]}")
            else:
                self._add_text("[引用消息]")
            return
        if isinstance(comp, Comp.Face):
            self._kind("Face")
            self._add_text("[表情]")
            return
        if isinstance(comp, Comp.Poke):
            self._kind("Poke")
            self._add_text("[戳一戳]")
            return

        share_cls = getattr(Comp, "Share", None)
        if share_cls and isinstance(comp, share_cls):
            self._kind("Share")
            title = str(getattr(comp, "title", "") or "").strip()
            content = str(getattr(comp, "content", "") or "").strip()
            self._add_text(f"[分享] {title} {content}".strip())
            return

        location_cls = getattr(Comp, "Location", None)
        if location_cls and isinstance(comp, location_cls):
            self._kind("Location")
            title = str(getattr(comp, "title", "") or "").strip()
            content = str(getattr(comp, "content", "") or "").strip()
            self._add_text(f"[位置] {title} {content}".strip())
            return

        name = type(comp).__name__
        if name not in self.unknown:
            self.unknown.append(name)

    def _walk_node(self, node: Any, depth: int) -> None:
        self._nodes += 1
        if self._nodes > self.max_nodes:
            if self._nodes == self.max_nodes + 1:
                self._add_text("[合并转发节点过多]")
            return
        name = str(getattr(node, "name", "") or "").strip()
        if name:
            self._add_text(f"[节点] {name}:")
        self.walk(getattr(node, "content", []) or [], depth + 1)

    def _json_text(self, data: Any, depth: int = 0) -> str:
        if depth > 3:
            return ""
        if isinstance(data, str):
            text = data.strip()
            if not text or text.startswith(_SKIP_JSON_VALUE_PREFIXES):
                return ""
            if text.startswith(("{", "[")):
                try:
                    return self._json_text(json.loads(text), depth + 1)
                except Exception:
                    pass
            return text[:200] + ("…" if len(text) > 200 else "")
        if isinstance(data, list):
            values = [self._json_text(item, depth + 1) for item in data[:10]]
            return " ".join(value for value in values if value)
        if not isinstance(data, dict):
            return ""

        values: list[str] = []
        for key in _JSON_KEYS:
            if key in data:
                values.append(self._json_text(data[key], depth + 1))
        for key in _JSON_CONTAINER_KEYS:
            if key in data and isinstance(data[key], (dict, list)):
                values.append(self._json_text(data[key], depth + 1))
        if not any(values):
            for key, value in data.items():
                if key in _JSON_KEYS or key in _JSON_CONTAINER_KEYS:
                    continue
                if isinstance(value, (dict, list)):
                    values.append(self._json_text(value, depth + 1))
        return " ".join(value for value in values if value).strip()


def extract_chain(
    chain: Iterable[Any] | None,
    *,
    max_chars: int = 2000,
    max_images: int = 20,
    max_nodes: int = 20,
    max_depth: int = 2,
) -> ExtractedContent:
    """解析消息链，返回文本、图片引用、组件类型和未知组件。"""

    extractor = _Extractor(
        max_chars=max_chars,
        max_images=max_images,
        max_nodes=max_nodes,
        max_depth=max_depth,
    )
    extractor.walk(chain)
    return extractor.result()
