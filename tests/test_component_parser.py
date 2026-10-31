"""消息链组件解析测试。"""

import importlib.util
import sys
from pathlib import Path

import astrbot_stub

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))
astrbot_stub.install()

spec = importlib.util.spec_from_file_location(
    "reply_visible_component_parser", PLUGIN_DIR / "component_parser.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
extract_chain = mod.extract_chain

from astrbot.api import message_components as C  # noqa: E402


def _run() -> None:
    chain = [
        C.Plain("签到成功"),
        C.At(qq="123", name="张三"),
        C.Image(url="http://example.com/a.png"),
        C.Json(
            {
                "app": "com.tencent.miniapp",
                "prompt": "购买成功",
                "meta": {"detail_1": {"title": "护灵丹", "desc": "数量 x1"}},
            }
        ),
        C.Nodes(
            [
                C.Node(
                    name="战报",
                    content=[C.Plain("伤害 100"), C.Image(url="http://example.com/b.png")],
                )
            ]
        ),
        C.File(name="log.txt"),
        C.Record(text="语音文本"),
        C.Video(file="v.mp4"),
        C.Reply(message_str="原消息"),
        C.Face(),
        C.Poke(),
        C.Share(title="分享标题", content="分享内容"),
        C.Location(title="位置", content="地址"),
    ]
    result = extract_chain(chain, max_chars=2000)
    for expected in (
        "签到成功",
        "@张三",
        "购买成功",
        "护灵丹",
        "伤害 100",
        "log.txt",
        "语音文本",
        "[视频]",
        "[引用] 原消息",
        "[表情]",
        "[戳一戳]",
        "[分享] 分享标题 分享内容",
        "[位置] 位置 地址",
    ):
        assert expected in result.text, expected
    assert result.image_refs == [
        "http://example.com/a.png",
        "http://example.com/b.png",
    ]
    assert "Json" in result.kinds and "Nodes" in result.kinds
    assert result.unknown == []

    unknown = extract_chain([C.Unknown("神秘组件")])
    assert unknown.unknown == ["Unknown"]

    truncated = extract_chain([C.Plain("x" * 50)], max_chars=20)
    assert "已截断" in truncated.text
    assert len(truncated.text) <= 30

    empty = extract_chain([])
    assert empty.text == "" and empty.image_refs == []

    print("component parser OK")


if __name__ == "__main__":
    _run()
