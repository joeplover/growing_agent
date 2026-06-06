import re
from dataclasses import dataclass


SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}
MAX_FILE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class UploadedMaterial:
    filename: str
    text: str


def decode_material_bytes(filename: str, content: bytes) -> UploadedMaterial:
    """Decode an uploaded text/markdown material file."""
    suffix = _suffix(filename)
    if suffix not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"仅支持 {supported} 资料文件。")

    if len(content) > MAX_FILE_BYTES:
        raise ValueError("单个资料文件不能超过 2MB。")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk")

    text = text.strip()
    if not text:
        raise ValueError("资料文件内容不能为空。")

    return UploadedMaterial(filename=filename, text=text)


def summarize_materials(raw_texts: list[str]) -> dict:
    """Build a small deterministic summary for uploaded materials."""
    joined = "\n\n".join(raw_texts)
    keywords = _extract_keywords(joined)
    topic = _extract_topic(joined, keywords)
    key_points = _extract_key_points(joined, keywords)

    return {
        "topic": topic,
        "keywords": keywords,
        "key_points": key_points,
        "summary": joined[:1200],
    }


def _suffix(filename: str) -> str:
    match = re.search(r"(\.[^.]+)$", filename.lower())
    return match.group(1) if match else ""


def _extract_keywords(text: str) -> list[str]:
    match = re.search(r"(?:关键词|keywords?)[:：]\s*(.+)", text, re.I)
    if not match:
        return []

    parts = re.split(r"[；;，,\s]+", match.group(1).strip())
    return [part.strip() for part in parts if part.strip()][:12]


def _extract_topic(text: str, keywords: list[str]) -> str:
    patterns = [
        r"(?:论文题目|题目|title)[:：]\s*(.+)",
        r"^#\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.M)
        if match:
            return match.group(1).strip(" ，,。；;#")[:80]

    if keywords:
        return "、".join(keywords[:3]) + "相关内容"

    for line in text.splitlines():
        value = line.strip(" ：:，,。；;#")
        if value:
            return value[:80]

    return ""


def _extract_key_points(text: str, keywords: list[str]) -> list[str]:
    key_points = []
    if keywords:
        key_points.append("关键词：" + "、".join(keywords))

    headings = re.findall(r"^(?:#{1,3}\s+.+|\d+(?:\.\d+)*\s+.+)$", text, re.M)
    for heading in headings[:10]:
        key_points.append(heading.strip(" #")[:120])

    return key_points
