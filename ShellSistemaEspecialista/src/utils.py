from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_KB_PATH = DATA_DIR / "knowledge_base.json"


def normalize_answer(answer: str) -> str:
    value = (answer or "").strip().lower()
    mapping = {
        "sim": "sim",
        "s": "sim",
        "yes": "sim",
        "não": "nao",
        "nao": "nao",
        "n": "nao",
        "no": "nao",
        "não sei": "nao_sei",
        "nao sei": "nao_sei",
        "nao_sei": "nao_sei",
    }
    return mapping.get(value, value)


def facts_to_rows(facts: Dict[str, str]) -> List[Dict[str, str]]:
    return [{"fato": key, "valor": value} for key, value in sorted(facts.items())]


def join_unique(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
