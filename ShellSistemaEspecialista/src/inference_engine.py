from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from .knowledge_base import KnowledgeBase
from .models import Condition, Hypothesis, InferenceResult, Rule
from .utils import join_unique, normalize_answer

QuestionCallback = Callable[[str, str, str, Rule, Hypothesis], str]


class InferenceEngine:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def forward_chain(self, initial_facts: Dict[str, str]) -> InferenceResult:
        result = InferenceResult(strategy="forward", initial_facts=self._clean(initial_facts))
        working_facts = dict(result.initial_facts)
        fired_ids = set()
        changed = True

        while changed:
            changed = False
            for rule in sorted(self.kb.rules, key=lambda item: item.prioridade, reverse=True):
                if rule.id in fired_ids:
                    continue
                if self._conditions_satisfied(rule.condicoes, working_facts):
                    fired_ids.add(rule.id)
                    result.fired_rules.append(self._rule_trace(rule, working_facts))
                    result.reasoning_path.append(f"Regra {rule.id} disparada: {rule.production_text()}.")
                    conclusion = rule.conclusao
                    inferred_key = conclusion.fato
                    if inferred_key == "diagnostico":
                        inferred_key = f"diagnostico_{conclusion.valor}"
                    if working_facts.get(conclusion.fato) != conclusion.valor:
                        working_facts[conclusion.fato] = conclusion.valor
                    result.inferred_facts[inferred_key] = conclusion.valor
                    changed = True

        self._collect_forward_evaluations(result, working_facts, fired_ids)
        self._collect_forward_diagnoses(result)
        self.kb.update_histories(result.fired_rules, result.asked_questions)
        return result

    def backward_chain(
        self,
        initial_facts: Dict[str, str],
        target_hypothesis_id: Optional[str] = None,
        question_callback: Optional[QuestionCallback] = None,
    ) -> InferenceResult:
        result = InferenceResult(strategy="backward", initial_facts=self._clean(initial_facts))
        working_facts = dict(result.initial_facts)
        hypotheses = self._selected_hypotheses(target_hypothesis_id)

        for hypothesis in hypotheses:
            result.reasoning_path.append(f"Avaliando hipótese: {hypothesis.nome}.")
            rules = self.kb.rules_for_conclusion(hypothesis.fato, hypothesis.valor)
            if not rules:
                result.evaluated_hypotheses.append(
                    self._hypothesis_eval(hypothesis, False, 0.0, "Nenhuma regra conclui esta hipótese.")
                )
                continue

            hypothesis_confirmed = False
            best_compatibility = 0.0
            supporting_rules: List[str] = []

            for rule in rules:
                evaluated = self._evaluate_rule_for_backward(rule, hypothesis, working_facts, result, question_callback)
                result.evaluated_rules.append(evaluated)
                best_compatibility = max(best_compatibility, evaluated["compatibilidade"])
                result.reasoning_path.append(evaluated["explicacao"])

                if evaluated["status"] == "satisfeita":
                    hypothesis_confirmed = True
                    supporting_rules.append(rule.id)
                    result.fired_rules.append(self._rule_trace(rule, working_facts))
                    working_facts[hypothesis.fato] = hypothesis.valor
                    result.inferred_facts[hypothesis.fato] = hypothesis.valor

            result.compatibility[hypothesis.id] = best_compatibility
            if hypothesis_confirmed:
                payload = self._diagnosis_payload(hypothesis, supporting_rules, best_compatibility)
                result.conclusions.append(payload)
                result.final_diagnosis = payload
                result.recommendations = join_unique([payload.get("recomendacao", "")])
                result.status = "diagnostico_confirmado"
                result.message = f"Hipótese confirmada por regra totalmente satisfeita: {hypothesis.nome}."
            else:
                result.evaluated_hypotheses.append(
                    self._hypothesis_eval(
                        hypothesis,
                        False,
                        best_compatibility,
                        "Nenhuma regra confirmou completamente a hipótese selecionada com as evidências fornecidas.",
                    )
                )
                if target_hypothesis_id:
                    result.message = "Nenhuma regra confirmou completamente a hipótese selecionada com as evidências fornecidas."

            if target_hypothesis_id or hypothesis_confirmed:
                if hypothesis_confirmed:
                    result.evaluated_hypotheses.append(
                        self._hypothesis_eval(hypothesis, True, best_compatibility, "Ao menos uma regra foi totalmente satisfeita.")
                    )
                break

        if not result.final_diagnosis:
            result.status = "sem_diagnostico"
            result.recommendations = []
            if not result.message:
                result.message = "Nenhuma regra confirmou completamente a hipótese selecionada com as evidências fornecidas."

        self.kb.update_histories(result.fired_rules, result.asked_questions)
        return result

    def hybrid_chain(
        self,
        initial_facts: Dict[str, str],
        target_hypothesis_id: Optional[str] = None,
        question_callback: Optional[QuestionCallback] = None,
    ) -> InferenceResult:
        forward = self.forward_chain(initial_facts)
        likely = target_hypothesis_id or self._best_forward_hypothesis(forward)
        merged_facts = {**forward.initial_facts, **self._diagnostic_facts_from_forward(forward)}
        backward = self.backward_chain(merged_facts, likely, question_callback)

        result = InferenceResult(strategy="hybrid", initial_facts=forward.initial_facts)
        result.inferred_facts = {**forward.inferred_facts}
        if backward.final_diagnosis:
            result.inferred_facts.update(backward.inferred_facts)
        result.fired_rules = self._unique_rules(forward.fired_rules + backward.fired_rules)
        result.evaluated_rules = forward.evaluated_rules + backward.evaluated_rules
        result.asked_questions = backward.asked_questions
        result.evaluated_hypotheses = backward.evaluated_hypotheses or forward.evaluated_hypotheses
        result.hypothesis_scores = forward.hypothesis_scores
        result.compatibility = {**forward.compatibility, **backward.compatibility}
        result.conclusions = backward.conclusions
        result.recommendations = backward.recommendations
        result.final_diagnosis = backward.final_diagnosis
        result.status = backward.status
        result.message = backward.message
        result.reasoning_path = (
            ["Etapa 1: encadeamento para frente com os fatos iniciais."]
            + forward.reasoning_path
            + ["Etapa 2: encadeamento para trás para confirmar a hipótese candidata."]
            + backward.reasoning_path
        )
        if not result.final_diagnosis:
            result.reasoning_path.append("A etapa backward não confirmou a hipótese candidata por regra totalmente satisfeita.")
        self.kb.update_histories(result.fired_rules, result.asked_questions)
        return result

    def _evaluate_rule_for_backward(
        self,
        rule: Rule,
        hypothesis: Hypothesis,
        working_facts: Dict[str, str],
        result: InferenceResult,
        question_callback: Optional[QuestionCallback],
    ) -> Dict[str, object]:
        satisfied: List[str] = []
        false: List[str] = []
        unknown: List[str] = []

        for condition in rule.condicoes:
            actual = working_facts.get(condition.fato)
            if actual is None and question_callback:
                answer = normalize_answer(question_callback(condition.fato, condition.valor, hypothesis.nome, rule, hypothesis))
                working_facts[condition.fato] = answer
                actual = answer
                result.asked_questions.append(
                    {
                        "fato": condition.fato,
                        "valor_esperado": condition.valor,
                        "resposta": answer,
                        "hipotese": hypothesis.nome,
                        "regra": rule.id,
                        "nome_regra": rule.nome,
                    }
                )

            if actual is None or actual == "nao_sei":
                unknown.append(condition.label())
            elif self._condition_satisfied(condition, working_facts):
                satisfied.append(condition.label())
            else:
                false.append(f"{condition.fato} = {actual}")

        total = len(rule.condicoes)
        compatibility = round((len(satisfied) / total) * 100, 2) if total else 0.0
        if false:
            status = "falhou"
            reason = f"a condição {false[0]} não satisfez a regra"
        elif unknown:
            status = "inconclusiva"
            reason = "existem condições desconhecidas"
        else:
            status = "satisfeita"
            reason = "todas as condições foram satisfeitas"

        explanation = self._rule_explanation(rule, hypothesis, status, reason, satisfied, false, unknown)
        return {
            "id": rule.id,
            "nome": rule.nome,
            "hipotese": hypothesis.nome,
            "etapa": "Backward",
            "status": status,
            "condicoes_satisfeitas": satisfied,
            "condicoes_falsas": false,
            "condicoes_desconhecidas": unknown,
            "compatibilidade": compatibility,
            "explicacao": explanation,
        }

    def _evaluated_rule(self, rule: Rule, facts: Dict[str, str], status: Optional[str] = None) -> Dict[str, object]:
        hypothesis = self._hypothesis_by_value(rule.conclusao.valor)
        satisfied = []
        false = []
        unknown = []
        for condition in rule.condicoes:
            actual = facts.get(condition.fato)
            if actual is None or actual == "nao_sei":
                unknown.append(condition.label())
            elif self._condition_satisfied(condition, facts):
                satisfied.append(condition.label())
            else:
                false.append(f"{condition.fato} = {actual}")
        total = len(rule.condicoes)
        compatibility = round((len(satisfied) / total) * 100, 2) if total else 0.0
        if status is None:
            if false:
                status = "falhou"
            elif unknown:
                status = "inconclusiva"
            else:
                status = "satisfeita"
        return {
            "id": rule.id,
            "nome": rule.nome,
            "hipotese": hypothesis.nome if hypothesis else rule.conclusao.valor,
            "etapa": "Forward",
            "status": status,
            "condicoes_satisfeitas": satisfied,
            "condicoes_falsas": false,
            "condicoes_desconhecidas": unknown,
            "compatibilidade": compatibility,
            "explicacao": self._forward_rule_explanation(rule, hypothesis, status, satisfied, false, unknown),
        }

    def _collect_forward_evaluations(self, result: InferenceResult, working_facts: Dict[str, str], fired_ids: set) -> None:
        initial_fact_ids = set(result.initial_facts.keys())
        result.evaluated_rules = []
        for rule in sorted(self.kb.rules, key=lambda item: item.id):
            has_initial_evidence = any(condition.fato in initial_fact_ids for condition in rule.condicoes)
            if rule.id not in fired_ids and not has_initial_evidence:
                continue
            status = "satisfeita" if rule.id in fired_ids else None
            result.evaluated_rules.append(self._evaluated_rule(rule, working_facts, status))

    def _collect_forward_diagnoses(self, result: InferenceResult) -> None:
        scores: Dict[str, Dict[str, object]] = {}
        for fired in result.fired_rules:
            if fired["conclusao_fato"] != "diagnostico":
                continue
            value = str(fired["conclusao_valor"])
            hypothesis = self._hypothesis_by_value(value)
            if not hypothesis:
                continue
            current = scores.setdefault(
                hypothesis.id,
                {
                    "id": hypothesis.id,
                    "nome": hypothesis.nome,
                    "valor": hypothesis.valor,
                    "pontuacao": 0,
                    "maior_prioridade": 0,
                    "regras": [],
                    "confirmada": True,
                },
            )
            current["pontuacao"] = int(current["pontuacao"]) + 1
            current["maior_prioridade"] = max(int(current["maior_prioridade"]), int(fired.get("prioridade", 0)))
            current["regras"].append(fired["id"])

        result.hypothesis_scores = scores
        for hypothesis in self.kb.hypotheses:
            score = scores.get(hypothesis.id)
            confirmed = bool(score)
            compatibility = self._best_hypothesis_compatibility(hypothesis, result.evaluated_rules)
            if confirmed:
                compatibility = 100.0
            result.compatibility[hypothesis.id] = compatibility
            result.evaluated_hypotheses.append(
                self._hypothesis_eval(
                    hypothesis,
                    confirmed,
                    compatibility,
                    "Confirmada por regra disparada no forward chaining."
                    if confirmed
                    else (
                        f"Compatibilidade parcial de {compatibility:.0f}% sem regra totalmente satisfeita."
                        if compatibility > 0
                        else "Nenhuma regra relacionada foi satisfeita para esta hipótese."
                    ),
                )
            )
            if confirmed and score:
                result.conclusions.append(self._diagnosis_payload(hypothesis, score["regras"], compatibility))

        if result.conclusions:
            result.conclusions.sort(
                key=lambda item: (
                    scores[item["id"]]["pontuacao"],
                    scores[item["id"]]["maior_prioridade"],
                ),
                reverse=True,
            )
            result.final_diagnosis = result.conclusions[0]
            result.recommendations = join_unique(item.get("recomendacao", "") for item in result.conclusions)
            result.status = "diagnostico_confirmado"
            result.message = f"Hipótese principal: {result.final_diagnosis['nome']}."
        else:
            result.status = "sem_diagnostico"
            if any(value > 0 for value in result.compatibility.values()):
                result.message = "Nenhuma regra foi totalmente satisfeita. No entanto, algumas hipóteses apresentaram compatibilidade parcial com os fatos informados."
            else:
                result.message = "Nenhuma regra foi totalmente satisfeita com os fatos fornecidos."
        self._ensure_forward_reasoning_path(result)

    def _best_hypothesis_compatibility(self, hypothesis: Hypothesis, evaluated_rules: List[Dict[str, object]]) -> float:
        values = [
            float(rule.get("compatibilidade", 0.0))
            for rule in evaluated_rules
            if rule.get("hipotese") == hypothesis.nome
        ]
        return max(values) if values else 0.0

    def _ensure_forward_reasoning_path(self, result: InferenceResult) -> None:
        facts = ", ".join(f"{key} = {value}" for key, value in result.initial_facts.items()) or "nenhum fato inicial"
        prefix = f"O sistema recebeu os fatos: {facts}."
        if not result.reasoning_path:
            result.reasoning_path.append(prefix)
        else:
            result.reasoning_path.insert(0, prefix)

        if result.evaluated_rules:
            result.reasoning_path.append("Em seguida, avaliou as regras que contêm pelo menos um desses fatos.")
        else:
            result.reasoning_path.append("Nenhuma regra da base contém os fatos informados.")

        if result.final_diagnosis:
            result.reasoning_path.append(f"A hipótese {result.final_diagnosis['nome']} foi confirmada por regra totalmente satisfeita.")
            return

        partials = [(hypothesis_id, value) for hypothesis_id, value in result.compatibility.items() if value > 0]
        if partials:
            best_id, best_value = max(partials, key=lambda item: item[1])
            hypothesis = self.kb.hypothesis_map().get(best_id)
            name = hypothesis.nome if hypothesis else best_id
            result.reasoning_path.append(
                f"Nenhuma regra foi totalmente satisfeita, pois ainda faltam condições complementares. "
                f"A hipótese {name} apresentou compatibilidade parcial de {best_value:.0f}%."
            )
        else:
            result.reasoning_path.append("Nenhuma regra foi totalmente satisfeita com os fatos fornecidos.")

    def _diagnosis_payload(self, hypothesis: Hypothesis, rule_ids: List[str], compatibility: float) -> Dict[str, object]:
        recommendation = hypothesis.recomendacao or self.kb.recommendations.get(hypothesis.valor, "")
        return {
            "id": hypothesis.id,
            "nome": hypothesis.nome,
            "fato": hypothesis.fato,
            "valor": hypothesis.valor,
            "recomendacao": recommendation,
            "regras": ", ".join(rule_id for rule_id in rule_ids if rule_id),
            "compatibilidade": compatibility,
        }

    def _hypothesis_eval(self, hypothesis: Hypothesis, confirmed: bool, compatibility: float, justification: str) -> Dict[str, object]:
        return {
            "id": hypothesis.id,
            "hipotese": hypothesis.nome,
            "valor": hypothesis.valor,
            "confirmada": confirmed,
            "compatibilidade": f"{compatibility:.0f}%",
            "justificativa": justification,
        }

    def _forward_rule_explanation(
        self,
        rule: Rule,
        hypothesis: Optional[Hypothesis],
        status: str,
        satisfied: List[str],
        false: List[str],
        unknown: List[str],
    ) -> str:
        hypothesis_name = hypothesis.nome if hypothesis else rule.conclusao.valor
        if status == "satisfeita":
            return f"A regra {rule.id} foi totalmente satisfeita e confirmou {hypothesis_name}."
        if false:
            return (
                f"A regra {rule.id} não confirmou {hypothesis_name} porque há condição incompatível: "
                f"{', '.join(false)}."
            )
        if satisfied and unknown:
            return (
                f"A regra possui evidência parcial, mas não foi totalmente satisfeita porque ainda falta a condição "
                f"{', '.join(unknown)}."
            )
        if unknown:
            return f"A regra {rule.id} ficou inconclusiva porque suas condições ainda não são conhecidas."
        return f"A regra {rule.id} foi avaliada, mas não confirmou {hypothesis_name}."

    def _rule_explanation(
        self,
        rule: Rule,
        hypothesis: Hypothesis,
        status: str,
        reason: str,
        satisfied: List[str],
        false: List[str],
        unknown: List[str],
    ) -> str:
        if status == "satisfeita":
            return f"A regra {rule.id} confirmou {hypothesis.nome} porque todas as condições foram satisfeitas: {', '.join(satisfied)}."
        details = []
        if false:
            details.append("condições falsas: " + ", ".join(false))
        if unknown:
            details.append("condições desconhecidas: " + ", ".join(unknown))
        return f"A regra {rule.id} não confirmou {hypothesis.nome} porque {reason}. " + "; ".join(details) + "."

    def _conditions_satisfied(self, conditions: List[Condition], facts: Dict[str, str]) -> bool:
        return all(self._condition_satisfied(condition, facts) for condition in conditions)

    def _condition_satisfied(self, condition: Condition, facts: Dict[str, str]) -> bool:
        actual = facts.get(condition.fato)
        if actual is None or actual == "nao_sei":
            return False
        if condition.operador == "!=":
            return actual != condition.valor
        return actual == condition.valor

    def _rule_trace(self, rule: Rule, facts: Dict[str, str]) -> Dict[str, object]:
        return {
            "id": rule.id,
            "nome": rule.nome,
            "producao": rule.production_text(),
            "condicoes": [condition.to_dict() for condition in rule.condicoes],
            "fatos_usados": {condition.fato: facts.get(condition.fato) for condition in rule.condicoes},
            "conclusao": rule.conclusao.label(),
            "conclusao_fato": rule.conclusao.fato,
            "conclusao_valor": rule.conclusao.valor,
            "recomendacao": rule.recomendacao,
            "explicacao": rule.explicacao,
            "prioridade": rule.prioridade,
        }

    def _selected_hypotheses(self, target_hypothesis_id: Optional[str]) -> List[Hypothesis]:
        hypotheses = sorted(self.kb.hypotheses, key=lambda item: item.id)
        if not target_hypothesis_id:
            return hypotheses
        selected = [item for item in hypotheses if item.id == target_hypothesis_id]
        return selected or hypotheses

    def _best_forward_hypothesis(self, result: InferenceResult) -> Optional[str]:
        if result.final_diagnosis:
            return str(result.final_diagnosis.get("id"))
        if not result.hypothesis_scores:
            return self.kb.hypotheses[0].id if self.kb.hypotheses else None
        best = sorted(
            result.hypothesis_scores.values(),
            key=lambda item: (item["pontuacao"], item["maior_prioridade"]),
            reverse=True,
        )[0]
        return str(best["id"])

    def _hypothesis_by_value(self, value: str) -> Optional[Hypothesis]:
        for hypothesis in self.kb.hypotheses:
            if hypothesis.valor == value:
                return hypothesis
        return None

    def _diagnostic_facts_from_forward(self, result: InferenceResult) -> Dict[str, str]:
        facts = {}
        for fired in result.fired_rules:
            if fired["conclusao_fato"] != "diagnostico":
                facts[fired["conclusao_fato"]] = str(fired["conclusao_valor"])
        return facts

    def _unique_rules(self, rules: List[Dict[str, object]]) -> List[Dict[str, object]]:
        seen = set()
        unique = []
        for rule in rules:
            if rule["id"] in seen:
                continue
            seen.add(rule["id"])
            unique.append(rule)
        return unique

    def _clean(self, facts: Dict[str, str]) -> Dict[str, str]:
        return {key: normalize_answer(value) for key, value in facts.items() if value}
