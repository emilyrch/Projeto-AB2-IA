from __future__ import annotations

from typing import Dict, List

from .knowledge_base import KnowledgeBase
from .models import InferenceResult


class ExplanationEngine:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def explain_why_questions(self, result: InferenceResult) -> List[str]:
        explanations = []
        for question in result.asked_questions:
            fact = question.get("fato", "")
            hypothesis = question.get("hipotese", "")
            rule_id = question.get("regra", "")
            rule_name = question.get("nome_regra", rule_id)
            explanations.append(
                f"Perguntei sobre {fact} porque estava avaliando a hipótese {hypothesis}, "
                f"e a regra {rule_id} ({rule_name}) exige esse fato como condição."
            )
        return explanations or ["Nenhuma pergunta adicional foi necessária nesta consulta."]

    def explain_how_conclusion(self, result: InferenceResult) -> str:
        if not result.final_diagnosis:
            return "O sistema não confirmou nenhuma hipótese porque nenhuma regra teve todas as suas condições satisfeitas."

        diagnosis = result.final_diagnosis.get("nome", result.final_diagnosis.get("valor", "diagnóstico"))
        rule_ids = str(result.final_diagnosis.get("regras", "")).split(", ")
        fired = [rule for rule in result.fired_rules if rule["id"] in rule_ids]
        if fired:
            conditions = []
            for rule in fired:
                conditions.extend(f"{key} = {value}" for key, value in rule.get("fatos_usados", {}).items())
            return (
                f"O sistema concluiu {diagnosis} porque a regra {', '.join(rule['id'] for rule in fired)} "
                f"foi totalmente satisfeita. As condições {', '.join(conditions)} foram confirmadas."
            )
        return f"O sistema concluiu {diagnosis} porque houve regra totalmente satisfeita para essa hipótese."

    def build_summary(self, result: InferenceResult) -> Dict[str, object]:
        return {
            "fatos_usados": result.all_facts(),
            "regras_disparadas": result.fired_rules,
            "regras_avaliadas": result.evaluated_rules,
            "hipoteses_avaliadas": result.evaluated_hypotheses,
            "pontuacoes": result.hypothesis_scores,
            "compatibilidade": result.compatibility,
            "conclusao_final": result.final_diagnosis,
            "recomendacoes": result.recommendations,
            "por_que": self.explain_why_questions(result),
            "como": self.explain_how_conclusion(result),
            "caminho": result.reasoning_path,
            "mensagem": result.message,
            "status": result.status,
        }
