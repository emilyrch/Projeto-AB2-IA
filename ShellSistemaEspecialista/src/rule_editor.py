from __future__ import annotations

from typing import Dict, List

from .knowledge_base import KnowledgeBase
from .models import Condition, Conclusion, FactDefinition, Hypothesis, Rule


def upsert_fact(kb: KnowledgeBase, data: Dict[str, str]) -> None:
    fact = FactDefinition.from_dict(data)
    kb.facts = [item for item in kb.facts if item.id != fact.id]
    kb.facts.append(fact)
    kb.facts.sort(key=lambda item: item.id)


def remove_fact(kb: KnowledgeBase, fact_id: str) -> None:
    kb.facts = [fact for fact in kb.facts if fact.id != fact_id]


def upsert_hypothesis(kb: KnowledgeBase, data: Dict[str, str]) -> None:
    hypothesis = Hypothesis.from_dict(data)
    kb.hypotheses = [item for item in kb.hypotheses if item.id != hypothesis.id]
    kb.hypotheses.append(hypothesis)
    kb.hypotheses.sort(key=lambda item: item.id)
    if hypothesis.recomendacao:
        kb.recommendations[hypothesis.valor] = hypothesis.recomendacao


def remove_hypothesis(kb: KnowledgeBase, hypothesis_id: str) -> None:
    kb.hypotheses = [item for item in kb.hypotheses if item.id != hypothesis_id]


def upsert_rule(kb: KnowledgeBase, data: Dict) -> None:
    rule = Rule(
        id=data["id"],
        nome=data.get("nome", data["id"]),
        condicoes=[Condition.from_dict(item) for item in data.get("condicoes", [])],
        conclusao=Conclusion.from_dict(data["conclusao"]),
        recomendacao=data.get("recomendacao", ""),
        explicacao=data.get("explicacao", ""),
        prioridade=int(data.get("prioridade", 0)),
    )
    kb.rules = [item for item in kb.rules if item.id != rule.id]
    kb.rules.append(rule)
    kb.rules.sort(key=lambda item: (item.id, item.prioridade))


def remove_rule(kb: KnowledgeBase, rule_id: str) -> None:
    kb.rules = [rule for rule in kb.rules if rule.id != rule_id]


def parse_conditions(raw_text: str) -> List[Dict[str, str]]:
    conditions = []
    for part in raw_text.splitlines():
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError(f"Condição inválida: {part}")
        fact, value = part.split("=", 1)
        conditions.append({"fato": fact.strip(), "operador": "=", "valor": value.strip()})
    return conditions
