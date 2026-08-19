"""Stage 3: dedup overlapping OCR results (e.g. an English pass and an Arabic
pass reading the same glyph region, or a noisy engine emitting the same line
twice) using normalized-text similarity plus spatial (bounding-box) overlap
when available — degrading gracefully to text+reading-order when it isn't.
"""
import difflib
from typing import Optional

from extraction.types import BoundingBox, OcrLine

_BBOX_IOU_MERGE = 0.5
_BBOX_IOU_WITH_TEXT_MERGE = 0.2
_BBOX_IOU_WITH_TEXT_MIN_SIM = 0.6
_TEXT_ONLY_MIN_SIM = 0.85
_TEXT_ONLY_MAX_ORDER_SPAN = 2


def _text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _bbox_iou(a: Optional[BoundingBox], b: Optional[BoundingBox]) -> Optional[float]:
    if a is None or b is None:
        return None
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    inter = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _union_bbox(boxes: list[BoundingBox]) -> Optional[BoundingBox]:
    if not boxes:
        return None
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _pass_key(line: OcrLine) -> str:
    if line.words:
        w = line.words[0]
        return f"{w.source_pass}:{w.lang}"
    return "unknown"


def _local_reading_ranks(lines: list[OcrLine]) -> dict[int, int]:
    """Ranks each line within its own OCR pass (0..N-1), independent of any
    other pass's absolute reading_order numbering, so cross-pass position
    proximity can be compared fairly."""
    by_pass: dict[str, list[OcrLine]] = {}
    for ln in lines:
        by_pass.setdefault(_pass_key(ln), []).append(ln)
    ranks: dict[int, int] = {}
    for group in by_pass.values():
        for rank, ln in enumerate(sorted(group, key=lambda l: l.reading_order)):
            ranks[id(ln)] = rank
    return ranks


def _should_merge(a: OcrLine, b: OcrLine, order_span: int) -> bool:
    iou = _bbox_iou(a.bounding_box, b.bounding_box)
    text_sim = _text_similarity(a.text, b.text)
    if iou is not None:
        if iou >= _BBOX_IOU_MERGE:
            return True
        return iou >= _BBOX_IOU_WITH_TEXT_MERGE and text_sim >= _BBOX_IOU_WITH_TEXT_MIN_SIM
    return text_sim >= _TEXT_ONLY_MIN_SIM and order_span <= _TEXT_ONLY_MAX_ORDER_SPAN


def dedupe_lines(lines: list[OcrLine]) -> list[OcrLine]:
    n = len(lines)
    if n == 0:
        return []

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    ranks = _local_reading_ranks(lines)
    for i in range(n):
        for j in range(i + 1, n):
            span = abs(ranks[id(lines[i])] - ranks[id(lines[j])])
            if _should_merge(lines[i], lines[j], span):
                union(i, j)

    clusters: dict[int, list[int]] = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)

    merged: list[OcrLine] = []
    for idxs in clusters.values():
        if len(idxs) == 1:
            merged.append(lines[idxs[0]])
            continue
        members = [lines[k] for k in idxs]
        survivor = max(members, key=lambda l: l.confidence)
        all_words = tuple(w for m in members for w in m.words)
        bbox = _union_bbox([m.bounding_box for m in members if m.bounding_box is not None]) or survivor.bounding_box
        merged.append(
            OcrLine(
                text=survivor.text,
                words=all_words,
                confidence=survivor.confidence,
                bounding_box=bbox,
                page=survivor.page,
                reading_order=min(m.reading_order for m in members),
            )
        )
    merged.sort(key=lambda l: l.reading_order)
    return merged
