from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.inference_engine import InferenceEngine
from src.knowledge_base import KnowledgeBase

DATA_PATH = Path(__file__).parent / "data" / "knowledge_base.json"

st.set_page_config(page_title="Akinator - Animais", page_icon="🐾", layout="wide")


def load_kb() -> KnowledgeBase:
    if "kb" not in st.session_state:
        st.session_state.kb = KnowledgeBase.load(DATA_PATH)
    return st.session_state.kb


def get_engine() -> InferenceEngine:
    kb = load_kb()
    if "engine" not in st.session_state:
        st.session_state.engine = InferenceEngine(kb)
    return st.session_state.engine


def init_session() -> None:
    engine = get_engine()
    st.session_state.session = engine.new_session()
    st.session_state.current_attr = engine.best_question(st.session_state.session.candidates, [])
    st.session_state.finished = False
    st.session_state.result = None


def page_game() -> None:
    kb = load_kb()
    engine = get_engine()

    st.title("🐾 Akinator — Descubra o Animal")
    st.write("Pense em um animal e responda as perguntas. Tentarei adivinhar!")

    if "session" not in st.session_state or st.button("🔄 Reiniciar", key="restart_top"):
        init_session()

    session = st.session_state.session

    col_left, col_right = st.columns([2, 1])

    with col_right:
        st.subheader("Status")
        st.metric("Candidatos restantes", len(session.candidates))
        st.metric("Perguntas feitas", len(session.asked))
        if session.candidates:
            st.caption("Animais possíveis:")
            for eid in session.candidates[:8]:
                entity = kb.entity_map().get(eid)
                if entity:
                    st.write(f"• {entity.nome}")
            if len(session.candidates) > 8:
                st.caption(f"...e mais {len(session.candidates) - 8}")

    with col_left:
        result = engine.check_result(session)

        if result == "__desconhecido__":
            st.error("Não consegui identificar o animal! Ele não está na minha base de conhecimento.")
            st.info("Histórico de perguntas:")
            for item in session.history:
                st.write(f"• {item['pergunta']} → **{item['resposta']}**")
            if st.button("🔄 Jogar novamente"):
                init_session()
            return

        if result:
            entity = kb.entity_map().get(result)
            st.success(f"🎉 Acertei! O animal é: **{entity.nome if entity else result}**!")
            st.balloons()
            st.subheader("Caminho de raciocínio:")
            for item in session.history:
                st.write(f"• {item['pergunta']} → **{item['resposta']}**")
            if st.button("🔄 Jogar novamente"):
                init_session()
            return

        attr_id = st.session_state.get("current_attr")
        if attr_id is None:
            attr_id = engine.best_question(session.candidates, session.asked)
            st.session_state.current_attr = attr_id

        if attr_id is None:
            st.warning("Não há mais perguntas distintas para fazer.")
            if session.candidates:
                entity = kb.entity_map().get(session.candidates[0])
                st.info(f"Meu melhor palpite é: **{entity.nome if entity else session.candidates[0]}**")
            if st.button("🔄 Jogar novamente"):
                init_session()
            return

        attr = kb.attribute_map().get(attr_id)
        pergunta = attr.pergunta if attr else f"{attr_id}?"

        st.subheader(f"Pergunta {len(session.asked) + 1}")
        st.markdown(f"### {pergunta}")

        col_a, col_b, col_c = st.columns(3)
        if col_a.button("✅ Sim", use_container_width=True, key=f"sim_{attr_id}_{len(session.asked)}"):
            engine.process_answer(session, attr_id, True)
            st.session_state.current_attr = engine.best_question(session.candidates, session.asked)
            st.rerun()
        if col_b.button("❌ Não", use_container_width=True, key=f"nao_{attr_id}_{len(session.asked)}"):
            engine.process_answer(session, attr_id, False)
            st.session_state.current_attr = engine.best_question(session.candidates, session.asked)
            st.rerun()
        if col_c.button("🤷 Não sei", use_container_width=True, key=f"ns_{attr_id}_{len(session.asked)}"):
            engine.process_answer(session, attr_id, None)
            st.session_state.current_attr = engine.best_question(session.candidates, session.asked)
            st.rerun()

        if session.history:
            st.divider()
            st.subheader("Histórico")
            for item in reversed(session.history):
                st.write(f"• {item['pergunta']} → **{item['resposta']}**")


def page_knowledge() -> None:
    kb = load_kb()
    st.title("Base de Conhecimento")
    st.metric("Entidades", len(kb.entities))
    st.metric("Atributos", len(kb.attributes))

    tab_entities, tab_attrs = st.tabs(["Entidades", "Atributos"])

    with tab_entities:
        rows = []
        for e in kb.entities:
            row = {"Animal": e.nome}
            row.update({k: ("✅" if v else "❌") for k, v in e.atributos.items()})
            rows.append(row)
        st.dataframe(rows, use_container_width=True)

    with tab_attrs:
        st.dataframe([a.to_dict() for a in kb.attributes], use_container_width=True)


def page_editor() -> None:
    kb = load_kb()
    st.title("Editor — Adicionar Animal")
    st.caption("Cadastre um novo animal e salve na base de conhecimento.")

    with st.form("add_entity"):
        entity_id = st.text_input("ID (sem espaços)", placeholder="baleia")
        nome = st.text_input("Nome", placeholder="Baleia")
        st.write("Atributos:")
        attr_values = {}
        cols = st.columns(4)
        for i, attr in enumerate(kb.attributes):
            attr_values[attr.id] = cols[i % 4].checkbox(attr.pergunta.replace("?", ""), key=f"attr_{attr.id}")
        if st.form_submit_button("Salvar animal"):
            if entity_id and nome:
                from src.models import Entity
                kb.entities.append(Entity(id=entity_id.strip(), nome=nome.strip(), atributos=attr_values))
                kb.save(DATA_PATH)
                del st.session_state["kb"]
                st.success(f"Animal '{nome}' adicionado!")
                st.rerun()
            else:
                st.error("Preencha ID e Nome.")


kb = load_kb()
st.sidebar.title("🐾 Akinator Animais")
page = st.sidebar.radio("Página", ["Jogar", "Base de Conhecimento", "Editor"])
st.sidebar.divider()
st.sidebar.metric("Animais", len(kb.entities))
st.sidebar.metric("Atributos", len(kb.attributes))

if page == "Jogar":
    page_game()
elif page == "Base de Conhecimento":
    page_knowledge()
else:
    page_editor()
