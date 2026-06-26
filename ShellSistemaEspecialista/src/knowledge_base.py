from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import FactDefinition, Hypothesis, Rule


class KnowledgeBase:
    def __init__(
        self,
        domain: str = "Sem domínio",
        description: str = "",
        facts: Optional[List[FactDefinition]] = None,
        rules: Optional[List[Rule]] = None,
        hypotheses: Optional[List[Hypothesis]] = None,
        recommendations: Optional[Dict[str, str]] = None,
        initial_facts: Optional[Dict[str, str]] = None,
        inferred_facts: Optional[Dict[str, str]] = None,
        fired_rules_history: Optional[List[Dict[str, Any]]] = None,
        asked_questions_history: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.domain = domain
        self.description = description
        self.facts = facts or []
        self.rules = rules or []
        self.hypotheses = hypotheses or []
        self.recommendations = recommendations or {}
        self.initial_facts = initial_facts or {}
        self.inferred_facts = inferred_facts or {}
        self.fired_rules_history = fired_rules_history or []
        self.asked_questions_history = asked_questions_history or []

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeBase":
        return cls(
            domain=data.get("domain", "Sem domínio"),
            description=data.get("description", ""),
            facts=[FactDefinition.from_dict(item) for item in data.get("facts", [])],
            rules=[Rule.from_dict(item) for item in data.get("rules", [])],
            hypotheses=[Hypothesis.from_dict(item) for item in data.get("hypotheses", [])],
            recommendations=data.get("recommendations", {}),
            initial_facts=data.get("initial_facts", {}),
            inferred_facts=data.get("inferred_facts", {}),
            fired_rules_history=data.get("fired_rules_history", []),
            asked_questions_history=data.get("asked_questions_history", []),
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "description": self.description,
            "facts": [fact.to_dict() for fact in self.facts],
            "initial_facts": self.initial_facts,
            "inferred_facts": self.inferred_facts,
            "rules": [rule.to_dict() for rule in self.rules],
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "recommendations": self.recommendations,
            "fired_rules_history": self.fired_rules_history,
            "asked_questions_history": self.asked_questions_history,
        }

    def fact_map(self) -> Dict[str, FactDefinition]:
        return {fact.id: fact for fact in self.facts}

    def hypothesis_map(self) -> Dict[str, Hypothesis]:
        return {hypothesis.id: hypothesis for hypothesis in self.hypotheses}

    def rules_for_conclusion(self, fato: str, valor: str) -> List[Rule]:
        return [
            rule
            for rule in sorted(self.rules, key=lambda item: item.prioridade, reverse=True)
            if rule.conclusao.fato == fato and rule.conclusao.valor == valor
        ]

    def update_histories(self, fired_rules: List[Dict[str, Any]], asked_questions: List[Dict[str, Any]]) -> None:
        self.fired_rules_history = fired_rules
        self.asked_questions_history = asked_questions
