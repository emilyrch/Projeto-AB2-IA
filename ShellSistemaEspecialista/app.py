from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import streamlit as st

from src.explanation_engine import ExplanationEngine
from src.inference_engine import InferenceEngine
from src.knowledge_base import KnowledgeBase
from src.rule_editor import (
    parse_conditions,
    remove_fact,
    remove_hypothesis,
    remove_rule,
    upsert_fact,
    upsert_hypothesis,
    upsert_rule,
)
from src.utils import DEFAULT_KB_PATH, facts_to_rows


st.set_page_config(page_title="Shell Sistema Especialista", page_icon="IA", layout="wide")


def load_kb() -> KnowledgeBase:
    if "kb" not in st.session_state:
        st.session_state.kb_path = str(DEFAULT_KB_PATH)
        st.session_state.kb = KnowledgeBase.load(DEFAULT_KB_PATH)
    return st.session_state.kb


def save_kb() -> None:
    st.session_state.kb.save(st.session_state.kb_path)
    st.success("Base de conhecimento salva em JSON.")


def fact_label(kb: KnowledgeBase, fact_id: str) -> str:
    fact = kb.fact_map().get(fact_id)
    return fact.nome if fact else fact_id


def format_list(values: List[str]) -> str:
    return ", ".join(values) if values else "-"


def display_value(value: str) -> str:
    return {"sim": "Sim", "nao": "Não", "nao_sei": "Não sei"}.get(value, value)


def rule_rows(kb: KnowledgeBase):
    return [
        {
            "id": rule.id,
            "nome": rule.nome,
            "regra": rule.production_text(),
            "prioridade": rule.prioridade,
            "recomendacao": rule.recomendacao,
        }
        for rule in kb.rules
    ]


def fired_rule_rows(rules):
    return [
        {
            "id": rule.get("id", ""),
            "nome": rule.get("nome", ""),
            "conclusao": rule.get("conclusao", ""),
            "explicacao": rule.get("explicacao", ""),
        }
        for rule in rules
    ]


def evaluated_rule_rows(rules):
    return [
        {
            "id": rule.get("id", ""),
            "nome": rule.get("nome", ""),
            "hipotese": rule.get("hipotese", ""),
            "etapa": rule.get("etapa", "-"),
            "status": rule.get("status", ""),
            "compatibilidade": f"{rule.get('compatibilidade', 0):.0f}%",
            "condicoes_satisfeitas": format_list(rule.get("condicoes_satisfeitas", [])),
            "condicoes_falsas": format_list(rule.get("condicoes_falsas", [])),
            "condicoes_desconhecidas": format_list(rule.get("condicoes_desconhecidas", [])),
            "explicacao": rule.get("explicacao", ""),
        }
        for rule in rules
    ]


def show_table_or_message(rows, message: str) -> None:
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info(message)


def compatibility_rows(kb: KnowledgeBase, result) -> List[Dict[str, str]]:
    rows = []
    for hypothesis_id, value in getattr(result, "compatibility", {}).items():
        if value <= 0:
            continue
        hypothesis = kb.hypothesis_map().get(hypothesis_id)
        confirmed = bool(getattr(result, "final_diagnosis", None)) and result.final_diagnosis.get("id") == hypothesis_id
        rows.append(
            {
                "hipotese": hypothesis.nome if hypothesis else hypothesis_id,
                "compatibilidade": f"{value:.0f}%",
                "status": "Confirmada" if confirmed else "Compatibilidade parcial",
                "observacao": "Hipótese confirmada por regra totalmente satisfeita."
                if confirmed
                else "Compatibilidade parcial, hipótese não confirmada.",
            }
        )
    return rows


def fallback_reasoning_path(result) -> List[str]:
    facts = getattr(result, "initial_facts", {})
    if facts:
        fact_text = ", ".join(f"{key} = {value}" for key, value in facts.items())
        return [
            f"O sistema recebeu os fatos: {fact_text}.",
            "Em seguida, avaliou as regras que utilizam esses fatos.",
            "Nenhuma regra foi totalmente satisfeita, pois faltam condições complementares. Por isso, nenhum diagnóstico foi confirmado.",
        ]
    return ["Nenhum fato inicial foi informado para a consulta."]


def render_reasoning(result) -> None:
    steps = getattr(result, "reasoning_path", []) or fallback_reasoning_path(result)
    strategy = getattr(result, "strategy", "")
    evaluated = getattr(result, "evaluated_rules", [])
    fired = getattr(result, "fired_rules", [])

    if strategy == "hybrid":
        forward_rules = [rule.get("id", "") for rule in evaluated if rule.get("etapa") == "Forward"]
        backward_rules = [rule.get("id", "") for rule in evaluated if rule.get("etapa") == "Backward"]
        st.markdown("**Etapa 1 - Forward Chaining**")
        st.write("Fatos recebidos:")
        for fact, value in getattr(result, "initial_facts", {}).items():
            st.write(f"- {fact} = {value}")
        st.write("Regras avaliadas:")
        st.write(", ".join(forward_rules) if forward_rules else "Nenhuma regra forward foi avaliada.")
        st.write("Resultado:")
        fired_ids = {rule.get("id", "") for rule in fired}
        st.write("Houve regra totalmente satisfeita no forward." if fired_ids.intersection(forward_rules) else "Nenhuma regra totalmente satisfeita no forward.")

        st.markdown("**Etapa 2 - Backward Chaining**")
        st.write("Regras verificadas:")
        st.write(", ".join(backward_rules) if backward_rules else "Nenhuma regra backward foi avaliada.")
        st.write("Resultado:")
        st.write(getattr(result, "message", "") or "Hipótese não confirmada por regra totalmente satisfeita.")
        return

    title = "Forward Chaining" if strategy == "forward" else "Backward Chaining" if strategy == "backward" else "Inferência"
    st.markdown(f"**Etapa 1 - {title}**")
    st.write("Fatos recebidos:")
    facts = getattr(result, "initial_facts", {})
    if facts:
        for fact, value in facts.items():
            st.write(f"- {fact} = {value}")
    else:
        st.write("Nenhum fato inicial foi informado.")
    st.write("Regras avaliadas:")
    rule_ids = [rule.get("id", "") for rule in evaluated]
    st.write(", ".join(rule_ids) if rule_ids else "Nenhuma regra foi avaliada.")
    st.write("Resultado:")
    if getattr(result, "final_diagnosis", None):
        st.write(f"Hipótese confirmada: {result.final_diagnosis['nome']}.")
    else:
        st.write(getattr(result, "message", "") or steps[-1])


def ask_fact(fact_id: str, expected_value: str, hypothesis_name: str, rule, hypothesis) -> str:
    fact = load_kb().fact_map().get(fact_id)
    label = fact.pergunta if fact and fact.pergunta else f"{fact_id}?"
    key = f"ask_{hypothesis.id}_{rule.id}_{fact_id}"
    return st.radio(
        f"{label} (necessário para avaliar {hypothesis_name})",
        ["nao_sei", "sim", "nao"],
        index=0,
        format_func=display_value,
        horizontal=True,
        key=key,
    )


def page_home(kb: KnowledgeBase) -> None:
    st.title("Shell Genérica de Sistema Especialista")
    st.write(
        "Ferramenta baseada em regras de produção para construir aplicações de diagnóstico e recomendação "
        "sem alterar o código-fonte. A base carregada pode ser substituída por outro domínio em JSON."
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Domínio", kb.domain)
    col2.metric("Fatos", len(kb.facts))
    col3.metric("Regras", len(kb.rules))
    col4.metric("Hipóteses", len(kb.hypotheses))
    st.subheader("Descrição")
    st.info(kb.description)


def page_editor(kb: KnowledgeBase) -> None:
    st.title("Editor da Base de Conhecimento")
    st.caption("Cadastre fatos, regras e hipóteses. Todas as alterações podem ser salvas no arquivo JSON.")

    tab_facts, tab_rules, tab_hypotheses = st.tabs(["Fatos", "Regras", "Hipóteses"])

    with tab_facts:
        st.subheader("Fatos possíveis")
        st.dataframe([fact.to_dict() for fact in kb.facts], use_container_width=True)
        with st.form("fact_form"):
            fact_id = st.text_input("ID do fato", placeholder="temperatura_alta")
            name = st.text_input("Nome", placeholder="Temperatura alta")
            question = st.text_input("Pergunta ao usuário", placeholder="O computador está com temperatura alta?")
            category = st.text_input("Categoria", value="geral")
            description = st.text_area("Descrição")
            submitted = st.form_submit_button("Salvar fato")
            if submitted and fact_id:
                upsert_fact(kb, {"id": fact_id.strip(), "nome": name or fact_id, "pergunta": question, "categoria": category, "descricao": description})
                save_kb()
        remove_id = st.selectbox("Remover fato", [""] + [fact.id for fact in kb.facts])
        if st.button("Remover fato selecionado", disabled=not remove_id):
            remove_fact(kb, remove_id)
            save_kb()

    with tab_rules:
        st.subheader("Regras de produção")
        st.dataframe(rule_rows(kb), use_container_width=True)
        with st.form("rule_form"):
            rule_id = st.text_input("ID da regra", placeholder="R21")
            name = st.text_input("Nome da regra", placeholder="Diagnóstico por sintomas")
            conditions_text = st.text_area("Condições, uma por linha, no formato fato=valor", placeholder="temperatura_alta=sim\ncomputador_desliga_sozinho=sim")
            conclusion_fact = st.text_input("Fato da conclusão", value="diagnostico")
            conclusion_value = st.text_input("Valor da conclusão", placeholder="superaquecimento")
            recommendation = st.text_area("Recomendação associada")
            explanation = st.text_area("Explicação textual")
            priority = st.number_input("Prioridade", min_value=0, max_value=100, value=0)
            submitted = st.form_submit_button("Salvar regra")
            if submitted and rule_id and conclusion_value:
                try:
                    upsert_rule(
                        kb,
                        {
                            "id": rule_id.strip(),
                            "nome": name or rule_id,
                            "condicoes": parse_conditions(conditions_text),
                            "conclusao": {"fato": conclusion_fact.strip(), "valor": conclusion_value.strip()},
                            "recomendacao": recommendation,
                            "explicacao": explanation,
                            "prioridade": int(priority),
                        },
                    )
                    save_kb()
                except ValueError as exc:
                    st.error(str(exc))
        remove_id = st.selectbox("Remover regra", [""] + [rule.id for rule in kb.rules])
        if st.button("Remover regra selecionada", disabled=not remove_id):
            remove_rule(kb, remove_id)
            save_kb()

    with tab_hypotheses:
        st.subheader("Hipóteses ou diagnósticos")
        st.dataframe([hypothesis.to_dict() for hypothesis in kb.hypotheses], use_container_width=True)
        with st.form("hypothesis_form"):
            hypothesis_id = st.text_input("ID da hipótese", placeholder="superaquecimento")
            name = st.text_input("Nome da hipótese", placeholder="Superaquecimento")
            fact = st.text_input("Fato objetivo", value="diagnostico")
            value = st.text_input("Valor objetivo", placeholder="superaquecimento")
            recommendation = st.text_area("Recomendação")
            description = st.text_area("Descrição")
            submitted = st.form_submit_button("Salvar hipótese")
            if submitted and hypothesis_id:
                upsert_hypothesis(
                    kb,
                    {"id": hypothesis_id.strip(), "nome": name or hypothesis_id, "fato": fact, "valor": value or hypothesis_id, "recomendacao": recommendation, "descricao": description},
                )
                save_kb()
        remove_id = st.selectbox("Remover hipótese", [""] + [hypothesis.id for hypothesis in kb.hypotheses])
        if st.button("Remover hipótese selecionada", disabled=not remove_id):
            remove_hypothesis(kb, remove_id)
            save_kb()


def collect_initial_facts(kb: KnowledgeBase) -> Dict[str, str]:
    st.subheader("Fatos iniciais")
    selected = st.multiselect(
        "Selecione os fatos conhecidos para esta consulta",
        [fact.id for fact in kb.facts],
        format_func=lambda item: fact_label(kb, item),
        key="selected_initial_facts",
    )
    facts = {}
    for fact_id in selected:
        fact = kb.fact_map()[fact_id]
        facts[fact_id] = st.radio(
            fact.pergunta or fact.nome,
            ["sim", "nao", "nao_sei"],
            horizontal=True,
            format_func=display_value,
            key=f"initial_{fact_id}",
        )
    return facts


def current_query_signature(initial_facts: Dict[str, str], strategy: str, target: str) -> str:
    return json.dumps({"facts": initial_facts, "strategy": strategy, "target": target}, sort_keys=True, ensure_ascii=False)


def pending_question_ids(kb: KnowledgeBase, initial_facts: Dict[str, str], strategy: str, target: str) -> List[str]:
    if strategy == "forward" or not target:
        return []
    hypothesis = kb.hypothesis_map().get(target)
    if not hypothesis:
        return []
    needed = []
    for rule in kb.rules_for_conclusion(hypothesis.fato, hypothesis.valor):
        for condition in rule.condicoes:
            if condition.fato not in initial_facts and condition.fato not in needed:
                needed.append(condition.fato)
    return needed

    st.subheader("Perguntas adicionais para a hipótese alvo")
    answers = {}
    for fact_id in needed:
        fact = kb.fact_map().get(fact_id)
        answers[fact_id] = st.radio(
            fact.pergunta if fact else f"{fact_id}?",
            ["nao_sei", "sim", "nao"],
            index=0,
            horizontal=True,
            format_func=display_value,
            key=f"target_question_{target}_{fact_id}",
        )
    return answers


def render_pending_questions(kb: KnowledgeBase, target: str, question_ids: List[str]) -> Dict[str, str]:
    if not question_ids:
        return {}
    st.subheader("Perguntas adicionais")
    st.info("Responda às perguntas adicionais e clique em Finalizar diagnóstico.")
    answers = {}
    for fact_id in question_ids:
        fact = kb.fact_map().get(fact_id)
        answers[fact_id] = st.radio(
            fact.pergunta if fact else f"{fact_id}?",
            ["nao_sei", "sim", "nao"],
            index=0,
            horizontal=True,
            format_func=display_value,
            key=f"pending_question_{target}_{fact_id}",
        )
    return answers


def clear_consultation_state() -> None:
    for key in ["last_result", "pending_consultation", "last_signature"]:
        st.session_state.pop(key, None)


def page_consultation(kb: KnowledgeBase) -> None:
    st.title("Consulta e Diagnóstico")
    engine = InferenceEngine(kb)
    initial_facts = collect_initial_facts(kb)

    col1, col2 = st.columns(2)
    strategy = col1.selectbox(
        "Estratégia de inferência",
        ["forward", "backward", "hybrid"],
        format_func=lambda item: {"forward": "Encadeamento para frente", "backward": "Encadeamento para trás", "hybrid": "Encadeamento híbrido"}[item],
        key="strategy",
    )
    target = col2.selectbox(
        "Hipótese alvo para backward/híbrido",
        [""] + [hypothesis.id for hypothesis in kb.hypotheses],
        format_func=lambda item: "Avaliar automaticamente" if item == "" else kb.hypothesis_map()[item].nome,
        key="target_hypothesis",
    )
    signature = current_query_signature(initial_facts, strategy, target)
    if st.session_state.get("last_signature") != signature:
        clear_consultation_state()
        st.session_state.last_signature = signature

    pending = st.session_state.get("pending_consultation")
    if st.button("Executar diagnóstico", type="primary"):
        questions = pending_question_ids(kb, initial_facts, strategy, target)
        if questions:
            st.session_state.pending_consultation = {
                "initial_facts": initial_facts,
                "strategy": strategy,
                "target": target,
                "questions": questions,
            }
            st.session_state.pop("last_result", None)
            pending = st.session_state.pending_consultation
        else:
            if strategy == "forward":
                result = engine.forward_chain(initial_facts)
            elif strategy == "backward":
                result = engine.backward_chain(initial_facts, target or None, None)
            else:
                result = engine.hybrid_chain(initial_facts, target or None, None)
            st.session_state.last_result = result
            st.session_state.pending_consultation = None
            kb.initial_facts = result.initial_facts
            kb.inferred_facts = result.inferred_facts
            save_kb()

    if pending:
        answers = render_pending_questions(kb, pending["target"], pending["questions"])
        if st.button("Finalizar diagnóstico", type="secondary"):
            query_facts = {**pending["initial_facts"], **answers}
            if pending["strategy"] == "forward":
                result = engine.forward_chain(query_facts)
            elif pending["strategy"] == "backward":
                result = engine.backward_chain(query_facts, pending["target"] or None, None)
            else:
                result = engine.hybrid_chain(query_facts, pending["target"] or None, None)
            st.session_state.last_result = result
            st.session_state.pending_consultation = None
            kb.initial_facts = result.initial_facts
            kb.inferred_facts = result.inferred_facts
            save_kb()
            st.rerun()

    result = st.session_state.get("last_result")
    if not result:
        return

    st.subheader("Resultado")
    if result.final_diagnosis:
        st.success(f"Diagnóstico final confirmado: {result.final_diagnosis['nome']}")
    else:
        st.warning(getattr(result, "message", "") or "Nenhuma regra confirmou completamente a hipótese selecionada com as evidências fornecidas.")

    st.subheader("Compatibilidade")
    compatibility = compatibility_rows(kb, result)
    show_table_or_message(compatibility, "Nenhuma hipótese apresentou compatibilidade com os fatos informados.")

    st.subheader("Recomendações")
    if result.final_diagnosis:
        show_table_or_message(
            [{"recomendação": item} for item in result.recommendations],
            "Diagnóstico confirmado, mas nenhuma recomendação foi cadastrada para esta hipótese.",
        )
    else:
        st.info("Sem recomendação, pois nenhuma hipótese foi confirmada.")

    st.subheader("Outras hipóteses possíveis")
    conclusions = getattr(result, "conclusions", [])
    other = [item for item in conclusions if not result.final_diagnosis or item["id"] != result.final_diagnosis["id"]]
    show_table_or_message(other, "Nenhuma hipótese alternativa foi confirmada.")

    st.subheader("Regras disparadas")
    fired_rules = fired_rule_rows(getattr(result, "fired_rules", []))
    show_table_or_message(fired_rules, "Nenhuma regra foi totalmente satisfeita com os fatos fornecidos.")

    st.subheader("Regras avaliadas")
    evaluated_rules = evaluated_rule_rows(getattr(result, "evaluated_rules", []))
    show_table_or_message(evaluated_rules, "Nenhuma regra relacionada aos fatos informados foi encontrada.")

    col_facts1, col_facts2 = st.columns(2)
    with col_facts1:
        st.subheader("Fatos informados pelo usuário")
        show_table_or_message(facts_to_rows(result.initial_facts), "Nenhum fato inicial foi informado.")
    with col_facts2:
        st.subheader("Fatos inferidos")
        show_table_or_message(facts_to_rows(result.inferred_facts), "Nenhum fato foi inferido nesta consulta.")

    st.subheader("Caminho de inferência")
    render_reasoning(result)


def page_explanations(kb: KnowledgeBase) -> None:
    st.title("Explicações")
    result = st.session_state.get("last_result")
    if not result:
        st.info("Execute uma consulta primeiro para visualizar as explicações.")
        return

    explanation = ExplanationEngine(kb).build_summary(result)
    st.subheader("Como o sistema chegou à conclusão?")
    st.write(explanation["como"])

    st.subheader("Por que o sistema fez determinadas perguntas?")
    for item in explanation["por_que"]:
        st.write(item)

    st.subheader("Regras avaliadas")
    show_table_or_message(
        evaluated_rule_rows(explanation["regras_avaliadas"]),
        "Nenhuma regra relacionada aos fatos informados foi encontrada.",
    )

    st.subheader("Regras disparadas")
    show_table_or_message(
        fired_rule_rows(explanation["regras_disparadas"]),
        "Nenhuma regra foi totalmente satisfeita com os fatos fornecidos.",
    )

    st.subheader("Hipóteses avaliadas")
    show_table_or_message(explanation["hipoteses_avaliadas"], "Nenhuma hipótese foi avaliada nesta consulta.")

    st.subheader("Fatos usados")
    show_table_or_message(facts_to_rows(explanation["fatos_usados"]), "Nenhum fato foi registrado nesta consulta.")

    st.subheader("Caminho de inferência")
    render_reasoning(result)


def page_json(kb: KnowledgeBase) -> None:
    st.title("Base JSON")
    raw = json.dumps(kb.to_dict(), ensure_ascii=False, indent=2)
    edited = st.text_area("Conteúdo bruto da base de conhecimento", value=raw, height=560)
    col1, col2 = st.columns(2)
    if col1.button("Salvar JSON editado"):
        try:
            st.session_state.kb = KnowledgeBase.from_dict(json.loads(edited))
            save_kb()
        except json.JSONDecodeError as exc:
            st.error(f"JSON inválido: {exc}")
    col2.download_button("Exportar JSON", data=raw, file_name="knowledge_base.json", mime="application/json")


kb = load_kb()
st.sidebar.title("Navegação")
page = st.sidebar.radio("Página", ["Início", "Editor da Base de Conhecimento", "Consulta/Diagnóstico", "Explicações", "Base JSON"])
st.sidebar.divider()
st.sidebar.write(f"Arquivo: `{Path(st.session_state.kb_path).as_posix()}`")
if st.sidebar.button("Recarregar JSON"):
    st.session_state.kb = KnowledgeBase.load(st.session_state.kb_path)
    st.session_state.pop("last_result", None)
    st.rerun()

if page == "Início":
    page_home(kb)
elif page == "Editor da Base de Conhecimento":
    page_editor(kb)
elif page == "Consulta/Diagnóstico":
    page_consultation(kb)
elif page == "Explicações":
    page_explanations(kb)
else:
    page_json(kb)
