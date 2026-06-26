from __future__ import annotations

from typing import Any, Dict, List, Optional

from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork as BayesianNetwork


def build_network() -> BayesianNetwork:
    """
    Rede Bayesiana para diagnóstico de doenças respiratórias.

    Nós (variáveis):
      Doença         : Gripe | Pneumonia | Resfriado | COVID19 | Sinusite
      Febre          : sim | nao
      Tosse          : sim | nao
      DorMuscular    : sim | nao
      CorrizaNasal   : sim | nao
      FaltaAr        : sim | nao

    Estrutura causal:
      Doença → Febre
      Doença → Tosse
      Doença → DorMuscular
      Doença → CorrizaNasal
      Doença → FaltaAr
    """
    model = BayesianNetwork([
        ("Doenca", "Febre"),
        ("Doenca", "Tosse"),
        ("Doenca", "DorMuscular"),
        ("Doenca", "CorrizaNasal"),
        ("Doenca", "FaltaAr"),
    ])

    # P(Doenca) — distribuição a priori
    # ordem: Gripe, Pneumonia, Resfriado, COVID19, Sinusite
    cpd_doenca = TabularCPD(
        variable="Doenca",
        variable_card=5,
        values=[[0.30], [0.10], [0.35], [0.15], [0.10]],
        state_names={"Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"]},
    )

    # P(Febre | Doenca)
    # colunas: Gripe  Pneumonia  Resfriado  COVID19  Sinusite
    cpd_febre = TabularCPD(
        variable="Febre",
        variable_card=2,
        values=[
            [0.85, 0.90, 0.30, 0.80, 0.40],   # sim
            [0.15, 0.10, 0.70, 0.20, 0.60],   # nao
        ],
        evidence=["Doenca"],
        evidence_card=[5],
        state_names={
            "Febre": ["sim", "nao"],
            "Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"],
        },
    )

    # P(Tosse | Doenca)
    cpd_tosse = TabularCPD(
        variable="Tosse",
        variable_card=2,
        values=[
            [0.80, 0.85, 0.70, 0.75, 0.60],
            [0.20, 0.15, 0.30, 0.25, 0.40],
        ],
        evidence=["Doenca"],
        evidence_card=[5],
        state_names={
            "Tosse": ["sim", "nao"],
            "Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"],
        },
    )

    # P(DorMuscular | Doenca)
    cpd_dor = TabularCPD(
        variable="DorMuscular",
        variable_card=2,
        values=[
            [0.75, 0.50, 0.20, 0.70, 0.15],
            [0.25, 0.50, 0.80, 0.30, 0.85],
        ],
        evidence=["Doenca"],
        evidence_card=[5],
        state_names={
            "DorMuscular": ["sim", "nao"],
            "Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"],
        },
    )

    # P(CorrizaNasal | Doenca)
    cpd_corriz = TabularCPD(
        variable="CorrizaNasal",
        variable_card=2,
        values=[
            [0.50, 0.20, 0.85, 0.40, 0.90],
            [0.50, 0.80, 0.15, 0.60, 0.10],
        ],
        evidence=["Doenca"],
        evidence_card=[5],
        state_names={
            "CorrizaNasal": ["sim", "nao"],
            "Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"],
        },
    )

    # P(FaltaAr | Doenca)
    cpd_falta_ar = TabularCPD(
        variable="FaltaAr",
        variable_card=2,
        values=[
            [0.25, 0.80, 0.05, 0.70, 0.10],
            [0.75, 0.20, 0.95, 0.30, 0.90],
        ],
        evidence=["Doenca"],
        evidence_card=[5],
        state_names={
            "FaltaAr": ["sim", "nao"],
            "Doenca": ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"],
        },
    )

    model.add_cpds(cpd_doenca, cpd_febre, cpd_tosse, cpd_dor, cpd_corriz, cpd_falta_ar)
    assert model.check_model(), "Modelo Bayesiano inválido"
    return model


SYMPTOM_VARIABLES = {
    "Febre": {"label": "Febre alta", "states": ["sim", "nao"]},
    "Tosse": {"label": "Tosse", "states": ["sim", "nao"]},
    "DorMuscular": {"label": "Dor muscular", "states": ["sim", "nao"]},
    "CorrizaNasal": {"label": "Corriza nasal / nariz escorrendo", "states": ["sim", "nao"]},
    "FaltaAr": {"label": "Falta de ar", "states": ["sim", "nao"]},
}

DISEASES = ["Gripe", "Pneumonia", "Resfriado", "COVID19", "Sinusite"]

PRIOR = {
    "Gripe": 0.30,
    "Pneumonia": 0.10,
    "Resfriado": 0.35,
    "COVID19": 0.15,
    "Sinusite": 0.10,
}


def run_inference(model: BayesianNetwork, evidence: Dict[str, str]) -> Dict[str, float]:
    infer = VariableElimination(model)
    query = infer.query(variables=["Doenca"], evidence=evidence, show_progress=False)
    states = query.state_names["Doenca"]
    values = query.values
    return {state: float(values[i]) for i, state in enumerate(states)}
