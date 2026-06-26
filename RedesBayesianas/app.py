from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

from typing import Dict, Optional

import pandas as pd
import streamlit as st

from src.bayesian_network import (
    DISEASES,
    PRIOR,
    SYMPTOM_VARIABLES,
    build_network,
    run_inference,
)

st.set_page_config(page_title="Diagnóstico Bayesiano", page_icon="🏥", layout="wide")


def get_model():
    if "model" not in st.session_state:
        with st.spinner("Construindo rede bayesiana..."):
            st.session_state.model = build_network()
    return st.session_state.model


DISEASE_COLORS = {
    "Gripe": "#4e79a7",
    "Pneumonia": "#f28e2b",
    "Resfriado": "#59a14f",
    "COVID19": "#e15759",
    "Sinusite": "#76b7b2",
}

DISEASE_DESCRIPTIONS = {
    "Gripe": "Doença viral aguda, com início rápido, febre alta e dores musculares intensas.",
    "Pneumonia": "Infecção pulmonar grave; causa febre alta, tosse produtiva e falta de ar.",
    "Resfriado": "Infecção viral leve; nariz escorrendo é o principal sintoma. Raramente causa febre alta.",
    "COVID19": "Doença respiratória viral; pode causar febre, tosse seca e falta de ar.",
    "Sinusite": "Inflamação dos seios paranasais; corriza nasal e pressão facial são comuns.",
}


def render_bar(prob: float, color: str) -> str:
    width = int(prob * 200)
    return f"<div style='background:{color};width:{width}px;height:14px;border-radius:4px;display:inline-block'></div>"


def page_diagnosis() -> None:
    model = get_model()
    st.title("🏥 Diagnóstico Médico — Rede Bayesiana")
    st.write(
        "Selecione os sintomas observados. O sistema atualiza as probabilidades de cada doença "
        "em tempo real usando inferência bayesiana."
    )

    st.subheader("Sintomas")
    evidence: Dict[str, str] = {}
    cols = st.columns(len(SYMPTOM_VARIABLES))
    for i, (var, meta) in enumerate(SYMPTOM_VARIABLES.items()):
        choice = cols[i].radio(
            meta["label"],
            ["Não informado", "Sim", "Não"],
            key=f"symptom_{var}",
        )
        if choice == "Sim":
            evidence[var] = "sim"
        elif choice == "Não":
            evidence[var] = "nao"

    st.divider()
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Probabilidades")

        prior_df = pd.DataFrame(
            [{"Doença": d, "A priori": f"{v:.1%}"} for d, v in PRIOR.items()]
        )

        if evidence:
            posterior = run_inference(model, evidence)
        else:
            posterior = {d: v for d, v in PRIOR.items()}

        posterior_sorted = sorted(posterior.items(), key=lambda x: x[1], reverse=True)

        rows = []
        for disease, prob in posterior_sorted:
            prior_val = PRIOR.get(disease, 0)
            delta = prob - prior_val
            delta_str = f"+{delta:.1%}" if delta >= 0 else f"{delta:.1%}"
            rows.append({
                "Doença": disease,
                "A priori": f"{prior_val:.1%}",
                "A posteriori": f"{prob:.1%}",
                "Variação": delta_str,
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        best_disease, best_prob = posterior_sorted[0]
        if evidence:
            if best_prob > 0.50:
                st.success(f"**Diagnóstico mais provável:** {best_disease} ({best_prob:.1%})")
            elif best_prob > 0.30:
                st.warning(f"**Candidato principal:** {best_disease} ({best_prob:.1%}) — probabilidade moderada")
            else:
                st.info("Nenhum diagnóstico com probabilidade dominante. Mais sintomas são necessários.")
        else:
            st.info("Selecione sintomas para obter diagnóstico.")

    with col_right:
        st.subheader("Distribuição posterior")
        bar_data = pd.DataFrame(
            {"Probabilidade": list(posterior.values())},
            index=list(posterior.keys()),
        )
        st.bar_chart(bar_data)

        st.subheader("Evidências informadas")
        if evidence:
            for var, val in evidence.items():
                label = SYMPTOM_VARIABLES[var]["label"]
                icon = "✅" if val == "sim" else "❌"
                st.write(f"{icon} {label}: **{val}**")
        else:
            st.caption("Nenhum sintoma selecionado ainda.")


def page_experiments() -> None:
    model = get_model()
    st.title("Experimentos de Inferência")
    st.write(
        "Demonstração de como a probabilidade de cada doença é atualizada "
        "à medida que novas evidências são inseridas."
    )

    experiments = [
        {
            "titulo": "Experimento 1 — Apenas Febre",
            "evidencia": {"Febre": "sim"},
        },
        {
            "titulo": "Experimento 2 — Febre + Tosse",
            "evidencia": {"Febre": "sim", "Tosse": "sim"},
        },
        {
            "titulo": "Experimento 3 — Febre + Tosse + Dor Muscular",
            "evidencia": {"Febre": "sim", "Tosse": "sim", "DorMuscular": "sim"},
        },
        {
            "titulo": "Experimento 4 — Corriza + Tosse (sem febre)",
            "evidencia": {"CorrizaNasal": "sim", "Tosse": "sim", "Febre": "nao"},
        },
        {
            "titulo": "Experimento 5 — Febre + FaltaAr + Tosse",
            "evidencia": {"Febre": "sim", "FaltaAr": "sim", "Tosse": "sim"},
        },
    ]

    for exp in experiments:
        with st.expander(exp["titulo"], expanded=True):
            posterior = run_inference(model, exp["evidencia"])
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Evidências:**")
                for var, val in exp["evidencia"].items():
                    label = SYMPTOM_VARIABLES.get(var, {}).get("label", var)
                    st.write(f"• {label} = **{val}**")

                rows = []
                for disease in DISEASES:
                    prior_val = PRIOR[disease]
                    post_val = posterior[disease]
                    delta = post_val - prior_val
                    rows.append({
                        "Doença": disease,
                        "A priori": f"{prior_val:.1%}",
                        "A posteriori": f"{post_val:.1%}",
                        "Δ": f"{delta:+.1%}",
                    })
                st.dataframe(rows, use_container_width=True, hide_index=True)

            with col2:
                best = max(posterior.items(), key=lambda x: x[1])
                st.metric("Diagnóstico mais provável", best[0], f"{best[1]:.1%}")
                bar_data = pd.DataFrame(
                    {"Prob. posterior": list(posterior.values())},
                    index=list(posterior.keys()),
                )
                st.bar_chart(bar_data)


def page_network() -> None:
    st.title("Estrutura da Rede Bayesiana")

    st.subheader("Grafo causal")
    st.markdown("""
```
            ┌─────────────────┐
            │     Doença      │
            │ (Gripe|Pneumonia│
            │ Resfriado|COVID │
            │  |Sinusite)     │
            └────────┬────────┘
       ┌─────────────┼─────────────────────┐
       ▼             ▼           ▼         ▼         ▼
    Febre          Tosse    DorMuscular CorrizaNasal FaltaAr
```
""")

    st.subheader("Probabilidades condicionais (CPTs)")
    cpd_data = {
        "Sintoma": ["Febre", "Tosse", "Dor Muscular", "Corriza Nasal", "Falta de Ar"],
        "P(sim|Gripe)":     ["85%", "80%", "75%", "50%", "25%"],
        "P(sim|Pneumonia)": ["90%", "85%", "50%", "20%", "80%"],
        "P(sim|Resfriado)": ["30%", "70%", "20%", "85%", "5%"],
        "P(sim|COVID19)":   ["80%", "75%", "70%", "40%", "70%"],
        "P(sim|Sinusite)":  ["40%", "60%", "15%", "90%", "10%"],
    }
    st.dataframe(cpd_data, use_container_width=True, hide_index=True)

    st.subheader("Distribuição a priori das doenças")
    prior_df = pd.DataFrame(
        [{"Doença": d, "Probabilidade a priori": f"{v:.0%}", "Interpretação": "Prevalência estimada na população"} for d, v in PRIOR.items()]
    )
    st.dataframe(prior_df, use_container_width=True, hide_index=True)

    st.subheader("Descrição clínica das doenças")
    for disease, desc in DISEASE_DESCRIPTIONS.items():
        st.write(f"**{disease}:** {desc}")


model = get_model()
st.sidebar.title("🏥 Diagnóstico Bayesiano")
page = st.sidebar.radio("Página", ["Diagnóstico Interativo", "Experimentos", "Rede Bayesiana"])
st.sidebar.divider()
st.sidebar.write("**Doenças modeladas:**")
for d in DISEASES:
    st.sidebar.write(f"• {d}")

if page == "Diagnóstico Interativo":
    page_diagnosis()
elif page == "Experimentos":
    page_experiments()
else:
    page_network()
