import re
from pathlib import Path

from ppt_agent.state import State


MATERIAL_LIBRARY_DIR = Path(__file__).resolve().parents[2] / "materials"

INCLUDE_WORDS = {
    "引入",
    "导入",
    "需要",
    "要",
    "yes",
    "y",
    "ok",
    "确认",
    "好的",
}

EXCLUDE_WORDS = {
    "不引入",
    "不用",
    "不要",
    "不需要",
    "否",
    "no",
    "n",
    "跳过",
}

SKIP_WORDS = {"跳过", "没有", "暂无", "不用", "no", "skip"}


def collect_m_node(state: State) -> dict:
    """收集用户补充的 PPT 资料。"""
    messages = state.get("messages", [])

    if not messages:
        return {
            "material": _empty_material(),
            "status": "material_ready",
        }

    user_text = messages[-1].content.strip()

    if user_text.lower() in SKIP_WORDS:
        material = state.get("material", _empty_material())
        return {
            "material": material,
            "status": "material_ready",
        }

    old_material = state.get("material", _empty_material())
    old_materials = old_material.get("raw_texts", [])
    old_file_paths = old_material.get("file_paths", [])
    requirement = state.get("requirement", {})

    choice = _normalize_choice(user_text)

    if choice == "include":
        library_texts, library_paths = _load_material_library()
        if not library_texts:
            return {
                "material": old_material,
                "requirement": requirement,
                "status": "material_ready",
            }

        material_text = "\n\n".join(library_texts)
        material_summary = _extract_material_summary(material_text) if material_text else {}

        if (
            material_summary.get("topic")
            and not _is_bad_topic(material_summary.get("topic", ""))
            and _is_generic_topic(requirement.get("topic", ""))
        ):
            requirement = {
                **requirement,
                "topic": material_summary.get("topic"),
            }

        if material_summary.get("key_points"):
            requirement = {
                **requirement,
                "key_points": material_summary.get("key_points"),
            }

        return {
            "material": {
                "raw_texts": old_materials + library_texts,
                "file_paths": old_file_paths + library_paths,
                "summary": material_summary,
                "topic": material_summary.get("topic", ""),
                "keywords": material_summary.get("keywords", []),
                "key_points": material_summary.get("key_points", []),
            },
            "requirement": requirement,
            "status": "material_ready",
        }

    if choice == "exclude":
        return {
            "material": old_material,
            "requirement": requirement,
            "status": "material_ready",
        }

    return {
        "material": old_material,
        "requirement": requirement,
        "status": "material_ready",
    }


def _empty_material() -> dict:
    return {
        "raw_texts": [],
        "file_paths": [],
        "summary": {},
        "topic": "",
        "keywords": [],
        "key_points": [],
    }


def _normalize_choice(user_text: str) -> str:
    value = user_text.strip().lower()

    if value in EXCLUDE_WORDS or any(word in value for word in EXCLUDE_WORDS):
        return "exclude"

    if value in INCLUDE_WORDS or any(word in value for word in INCLUDE_WORDS):
        return "include"

    return ""


def _load_material_library() -> tuple[list[str], list[str]]:
    if not MATERIAL_LIBRARY_DIR.exists():
        return [], []

    texts = []
    file_paths = []

    for path in sorted(MATERIAL_LIBRARY_DIR.rglob("*")):
        if not path.is_file():
            continue

        if path.name == ".gitkeep":
            continue

        if path.suffix.lower() not in {".txt", ".md"}:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="gbk")

        texts.append(text)
        file_paths.append(str(path))

    return texts, file_paths


def _read_material_text(user_text: str) -> tuple[str, list[str]]:
    path = Path(user_text.strip('"'))

    try:
        is_file = path.exists() and path.is_file()
    except OSError:
        is_file = False

    if not is_file:
        return user_text, []

    if path.suffix.lower() not in {".txt", ".md"}:
        return user_text, [str(path)]

    try:
        return path.read_text(encoding="utf-8"), [str(path)]
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk"), [str(path)]


def _extract_material_summary(user_text: str) -> dict:
    """从用户补充资料里提取论文主题、关键词和核心内容。"""
    keywords = _extract_keywords(user_text)
    topic = _extract_topic(user_text, keywords)
    summary = _extract_summary(user_text)
    key_points = _extract_key_points(user_text, keywords)

    return {
        "topic": topic,
        "keywords": keywords,
        "key_points": key_points,
        "summary": summary,
    }


def _extract_keywords(user_text: str) -> list[str]:
    match = re.search(r"关键词[:：]\s*(.+)", user_text)

    if not match:
        return []

    value = match.group(1).strip()
    parts = re.split(r"[；;，,\s]+", value)

    return [part.strip() for part in parts if part.strip()]


def _extract_topic(user_text: str, keywords: list[str]) -> str:
    patterns = [
        r"(?:论文题目|题目)[:：]\s*(.+)",
        r"为(?:分析|研究|探讨)(.+?)[，,]本文",
        r"本文(?:采用|围绕|针对|以).{0,30}?对(.+?)(?:进行|开展)(?:研究|分析)",
        r"本文以(.+?)作为主要",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_text)
        if match:
            value = match.group(1).strip()
            return _clean_topic(value)

    if keywords:
        return "、".join(keywords[:3]) + "相关研究"

    first_sentence = _first_meaningful_sentence(user_text)

    if first_sentence and not _is_bad_topic(first_sentence):
        return first_sentence[:40]

    return ""


def _first_meaningful_sentence(user_text: str) -> str:
    for line in user_text.splitlines():
        value = line.strip(" ：:，,。；;")
        value = re.sub(r"^摘要[:：]?", "", value).strip()

        if not value or _is_bad_topic(value):
            continue

        return re.split(r"[。！？]", value)[0].strip()

    return ""


def _clean_topic(value: str) -> str:
    value = re.sub(r"^摘要[:：]?", "", value)
    value = re.sub(r"^(在|对|基于)", "", value)
    value = value.strip(" ，,。；;")

    return value


def _is_bad_topic(topic: str) -> bool:
    value = str(topic).strip(" ：:，,。；;").lower()
    bad_topics = {
        "",
        "摘要",
        "abstract",
        "关键词",
        "目录",
        "正文",
        "结论",
        "致谢",
    }

    return value in bad_topics


def _extract_summary(user_text: str) -> str:
    match = re.search(r"摘要\s*(.+?)\s*关键词[:：]", user_text, re.S)

    if match:
        return match.group(1).strip()[:1200]

    return user_text.strip()[:1200]


def _extract_key_points(user_text: str, keywords: list[str]) -> list[str]:
    key_points = []

    if keywords:
        key_points.append("关键词：" + "、".join(keywords))

    section_titles = re.findall(r"(?:第[一二三四五六七八九十]+章\s*[^\n]+|\d+\.\d+\s*[^\n]+)", user_text)

    for title in section_titles[:8]:
        key_points.append(title.strip())

    conclusion_matches = re.findall(r"（\d+）(.+)", user_text)

    for item in conclusion_matches[:5]:
        key_points.append(item.strip()[:120])

    return key_points


def _is_generic_topic(topic: str) -> bool:
    value = str(topic).strip()
    generic_topics = {
        "",
        "摘要",
        "毕业论文",
        "毕业论文答辩",
        "毕业答辩",
        "论文答辩",
        "ppt",
        "答辩ppt",
    }

    return value in generic_topics
