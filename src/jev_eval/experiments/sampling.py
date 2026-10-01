"""Stratified --limit sampling shared by every dataset: round-robin across groups so a
small limit still covers every condition, and the same limit always picks the same rows.
"""
from __future__ import annotations

from typing import Any, Callable, Hashable


def stratified_sample(
    rows: list[dict[str, Any]], limit: int | None, group_key: Callable[[dict[str, Any]], Hashable]
) -> list[dict[str, Any]]:
    if limit is None or limit >= len(rows):
        return rows

    groups: dict[Hashable, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(group_key(row), []).append(row)
    ordered_keys = sorted(groups)

    picked: list[dict[str, Any]] = []
    idx = 0
    while len(picked) < limit:
        round_start = len(picked)
        for gk in ordered_keys:
            if idx < len(groups[gk]):
                picked.append(groups[gk][idx])
                if len(picked) == limit:
                    return picked
        if len(picked) == round_start:
            break  # every group exhausted
        idx += 1
    return picked
