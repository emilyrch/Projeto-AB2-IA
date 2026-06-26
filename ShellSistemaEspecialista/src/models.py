from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FactDefinition:
    id: str
    nome: str
    pergunta: str = ""
    tipo: str = "booleano"
    opcoes: List[str] = field(default_factory=lambda: ["sim", "nao", "nao_sei"])
    categoria: str = "geral"
    descricao: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactDefinition":
        return cls(
            id=data["id"],
            nome=data.get("nome", data["id"]),
            pergunta=data.get("pergunta", ""),
            tipo=data.get("tipo", "booleano"),
            opcoes=data.get("opcoes", ["sim", "nao", "nao_sei"]),
            categoria=data.get("categoria", "geral"),
            descricao=data.get("descricao", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class Condition:
    fato: str
    operador: str = "="
    valor: str = "sim"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        return cls(
            fato=data["fato"],
            operador=data.get("operador", "="),
            valor=str(data.get("valor", "sim")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

    def label(self) -> str:
        return f"{self.fato} {self.operador} {self.valor}"


@dataclass
class Conclusion:
    fato: str
    valor: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conclusion":
        return cls(fato=data["fato"], valor=str(data["valor"]))

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

    def label(self) -> str:
        return f"{self.fato} = {self.valor}"


@dataclass
class Rule:
    id: str
    nome: str
    condicoes: List[Condition]
    conclusao: Conclusion
    recomendacao: str = ""
    explicacao: str = ""
    prioridade: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=data["id"],
            nome=data.get("nome", data["id"]),
            condicoes=[Condition.from_dict(item) for item in data.get("condicoes", [])],
            conclusao=Conclusion.from_dict(data["conclusao"]),
            recomendacao=data.get("recomendacao", ""),
            explicacao=data.get("explicacao", ""),
            prioridade=int(data.get("prioridade", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "condicoes": [condition.to_dict() for condition in self.condicoes],
            "conclusao": self.conclusao.to_dict(),
            "recomendacao": self.recomendacao,
            "explicacao": self.explicacao,
            "prioridade": self.prioridade,
        }

    def production_text(self) -> str:
        conditions = " E ".join(condition.label() for condition in self.condicoes)
        return f"SE {conditions} ENTÃO {self.conclusao.label()}"


@dataclass
class Hypothesis:
    id: str
    nome: str
    fato: str = "diagnostico"
    valor: str = ""
    recomendacao: str = ""
    descricao: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        return cls(
            id=data["id"],
            nome=data.get("nome", data["id"]),
            fato=data.get("fato", "diagnostico"),
            valor=data.get("valor", data["id"]),
            recomendacao=data.get("recomendacao", ""),
            descricao=data.get("descricao", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class InferenceResult:
    strategy: str
    initial_facts: Dict[str, str]
    inferred_facts: Dict[str, str] = field(default_factory=dict)
    fired_rules: List[Dict[str, Any]] = field(default_factory=list)
    evaluated_rules: List[Dict[str, Any]] = field(default_factory=list)
    asked_questions: List[Dict[str, Any]] = field(default_factory=list)
    evaluated_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    hypothesis_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    compatibility: Dict[str, float] = field(default_factory=dict)
    conclusions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    final_diagnosis: Optional[Dict[str, Any]] = None
    reasoning_path: List[str] = field(default_factory=list)
    status: str = "sem_diagnostico"
    message: str = ""

    def all_facts(self) -> Dict[str, str]:
        facts = dict(self.initial_facts)
        facts.update(self.inferred_facts)
        return facts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "initial_facts": self.initial_facts,
            "inferred_facts": self.inferred_facts,
            "fired_rules": self.fired_rules,
            "evaluated_rules": self.evaluated_rules,
            "asked_questions": self.asked_questions,
            "evaluated_hypotheses": self.evaluated_hypotheses,
            "hypothesis_scores": self.hypothesis_scores,
            "compatibility": self.compatibility,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
            "final_diagnosis": self.final_diagnosis,
            "reasoning_path": self.reasoning_path,
            "status": self.status,
            "message": self.message,
        }
