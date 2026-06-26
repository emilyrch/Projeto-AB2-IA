from __future__ import annotations

import math
from typing import Dict, List, Optional

from .knowledge_base import KnowledgeBase
from .models import Session


class InferenceEngine:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def new_session(self) -> Session:
        return Session(candidates=[e.id for e in self.kb.entities])

    def filter_candidates(self, session: Session) -> List[str]:
        remaining = []
        for entity_id in session.candidates:
            entity = self.kb.entity_map().get(entity_id)
            if entity is None:
                continue
            compatible = True
            for attr_id, answer in session.answers.items():
                if answer is None:
                    continue
                entity_val = entity.atributos.get(attr_id, False)
                if entity_val != answer:
                    compatible = False
                    break
            if compatible:
                remaining.append(entity_id)
        return remaining

    def best_question(self, candidates: List[str], asked: List[str]) -> Optional[str]:
        """Picks the attribute that maximises information gain (most evenly splits candidates)."""
        best_attr: Optional[str] = None
        best_score = float("inf")
        entity_map = self.kb.entity_map()

        for attr in self.kb.attributes:
            if attr.id in asked:
                continue
            yes_count = sum(1 for eid in candidates if entity_map[eid].atributos.get(attr.id, False))
            no_count = len(candidates) - yes_count
            if yes_count == 0 or no_count == 0:
                continue
            score = abs(yes_count - no_count)
            if score < best_score:
                best_score = score
                best_attr = attr.id

        if best_attr is None:
            for attr in self.kb.attributes:
                if attr.id not in asked:
                    return attr.id
        return best_attr

    def entropy(self, candidates: List[str], attr_id: str) -> float:
        entity_map = self.kb.entity_map()
        yes = sum(1 for eid in candidates if entity_map[eid].atributos.get(attr_id, False))
        no = len(candidates) - yes
        total = len(candidates)
        if total == 0:
            return 0.0
        result = 0.0
        for count in (yes, no):
            if count > 0:
                p = count / total
                result -= p * math.log2(p)
        return result

    def process_answer(self, session: Session, attr_id: str, answer: Optional[bool]) -> None:
        session.answers[attr_id] = answer
        session.asked.append(attr_id)
        attr = self.kb.attribute_map().get(attr_id)
        session.history.append({
            "pergunta": attr.pergunta if attr else attr_id,
            "atributo": attr_id,
            "resposta": "Sim" if answer is True else ("Não" if answer is False else "Não sei"),
        })
        session.candidates = self.filter_candidates(session)

    def check_result(self, session: Session) -> Optional[str]:
        if len(session.candidates) == 1:
            return session.candidates[0]
        if len(session.candidates) == 0:
            return "__desconhecido__"
        return None
