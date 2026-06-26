from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Attribute:
    id: str
    pergunta: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attribute":
        return cls(id=data["id"], pergunta=data["pergunta"])

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class Entity:
    id: str
    nome: str
    atributos: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        return cls(id=data["id"], nome=data["nome"], atributos=data.get("atributos", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "nome": self.nome, "atributos": self.atributos}


@dataclass
class Session:
    candidates: List[str] = field(default_factory=list)
    answers: Dict[str, Optional[bool]] = field(default_factory=dict)
    asked: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    finished: bool = False
    result: Optional[str] = None
