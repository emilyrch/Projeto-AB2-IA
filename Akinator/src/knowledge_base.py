from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Attribute, Entity


class KnowledgeBase:
    def __init__(
        self,
        domain: str = "Animais",
        description: str = "",
        attributes: Optional[List[Attribute]] = None,
        entities: Optional[List[Entity]] = None,
    ) -> None:
        self.domain = domain
        self.description = description
        self.attributes = attributes or []
        self.entities = entities or []

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        with Path(path).open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeBase":
        return cls(
            domain=data.get("domain", "Animais"),
            description=data.get("description", ""),
            attributes=[Attribute.from_dict(a) for a in data.get("attributes", [])],
            entities=[Entity.from_dict(e) for e in data.get("entities", [])],
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "description": self.description,
            "attributes": [a.to_dict() for a in self.attributes],
            "entities": [e.to_dict() for e in self.entities],
        }

    def attribute_map(self) -> Dict[str, Attribute]:
        return {a.id: a for a in self.attributes}

    def entity_map(self) -> Dict[str, Entity]:
        return {e.id: e for e in self.entities}
