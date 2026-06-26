# Relatório Técnico — Diagnóstico Médico com Redes Bayesianas

## 1. Introdução

Este relatório descreve um sistema inteligente de diagnóstico médico baseado em Redes Bayesianas, desenvolvido em Python com interface Streamlit. O sistema modela relações probabilísticas entre doenças respiratórias e seus sintomas, permitindo realizar inferências diagnósticas a partir de evidências incompletas ou incertas.

O sistema tem finalidade exclusivamente educacional e não deve ser utilizado como ferramenta real de diagnóstico médico.

## 2. Objetivo

Aplicar os conceitos de representação do conhecimento sob incerteza por meio de uma Rede Bayesiana capaz de:

- Representar conhecimento médico de forma probabilística.
- Modelar relações de causa e efeito entre doenças e sintomas.
- Realizar inferência diagnóstica com evidências incompletas.
- Atualizar probabilidades à medida que novas evidências são fornecidas.

## 3. Domínio escolhido

O domínio é o diagnóstico de doenças respiratórias comuns. As doenças modeladas são:

- **Gripe** (Influenza): doença viral aguda com início súbito, febre alta e dores musculares.
- **Pneumonia**: infecção pulmonar grave com febre, tosse produtiva e falta de ar.
- **Resfriado Comum**: infecção viral leve caracterizada principalmente por corriza nasal.
- **COVID-19**: doença respiratória viral com febre, tosse seca e possível falta de ar.
- **Sinusite**: inflamação dos seios paranasais com corriza e pressão facial.

## 4. Módulos do sistema

- `app.py`: interface Streamlit com três páginas (diagnóstico interativo, experimentos, estrutura da rede).
- `src/bayesian_network.py`: construção da rede, definição das CPTs e função de inferência.

## 5. Modelagem da Rede Bayesiana

### 5.1 Variáveis

| Variável       | Tipo      | Estados                                         |
|----------------|-----------|------------------------------------------------|
| Doença         | Latente   | Gripe, Pneumonia, Resfriado, COVID19, Sinusite |
| Febre          | Observável| sim, nao                                        |
| Tosse          | Observável| sim, nao                                        |
| DorMuscular    | Observável| sim, nao                                        |
| CorrizaNasal   | Observável| sim, nao                                        |
| FaltaAr        | Observável| sim, nao                                        |

### 5.2 Estrutura causal

A rede possui estrutura em estrela (Naive Bayes), onde a variável `Doença` é a causa raiz que influencia todos os sintomas observáveis:

```
              ┌─────────────┐
              │   Doença    │
              └──────┬──────┘
    ┌─────────┬──────┼──────┬──────────┐
    ▼         ▼      ▼      ▼          ▼
  Febre     Tosse  Dor   Corriza    FaltaAr
                 Muscular  Nasal
```

Essa estrutura assume independência condicional dos sintomas dado o diagnóstico, o que é justificável no contexto educacional e é a base do classificador Naive Bayes Bayesiano.

### 5.3 Justificativa das probabilidades

As probabilidades foram definidas com base em conhecimento médico geral de domínio público, com fins educacionais:

- **Gripe** causa febre alta em 85% dos casos e dor muscular intensa em 75%.
- **Pneumonia** causa falta de ar em 80% dos casos e febre em 90%.
- **Resfriado** raramente causa febre alta (30%), mas provoca corriza em 85%.
- **COVID-19** causa febre em 80%, falta de ar em 70% e dor muscular em 70%.
- **Sinusite** é fortemente associada à corriza (90%), com febre moderada (40%).

## 6. Tabelas de Probabilidades Condicionais (CPTs)

### Distribuição a priori P(Doença)

| Doença     | P(Doença) | Justificativa                       |
|------------|-----------|-------------------------------------|
| Gripe      | 30%       | Doença sazonal comum                |
| Pneumonia  | 10%       | Menos frequente, mais grave         |
| Resfriado  | 35%       | Mais prevalente entre viroses       |
| COVID-19   | 15%       | Prevalência moderada considerada    |
| Sinusite   | 10%       | Condição crônica menos aguda        |

### P(Febre | Doença)

| Febre | Gripe | Pneumonia | Resfriado | COVID-19 | Sinusite |
|-------|-------|-----------|-----------|----------|----------|
| Sim   | 85%   | 90%       | 30%       | 80%      | 40%      |
| Não   | 15%   | 10%       | 70%       | 20%      | 60%      |

### P(Tosse | Doença)

| Tosse | Gripe | Pneumonia | Resfriado | COVID-19 | Sinusite |
|-------|-------|-----------|-----------|----------|----------|
| Sim   | 80%   | 85%       | 70%       | 75%      | 60%      |
| Não   | 20%   | 15%       | 30%       | 25%      | 40%      |

### P(DorMuscular | Doença)

| Dor Muscular | Gripe | Pneumonia | Resfriado | COVID-19 | Sinusite |
|--------------|-------|-----------|-----------|----------|----------|
| Sim          | 75%   | 50%       | 20%       | 70%      | 15%      |
| Não          | 25%   | 50%       | 80%       | 30%      | 85%      |

### P(CorrizaNasal | Doença)

| Corriza Nasal | Gripe | Pneumonia | Resfriado | COVID-19 | Sinusite |
|---------------|-------|-----------|-----------|----------|----------|
| Sim           | 50%   | 20%       | 85%       | 40%      | 90%      |
| Não           | 50%   | 80%       | 15%       | 60%      | 10%      |

### P(FaltaAr | Doença)

| Falta de Ar | Gripe | Pneumonia | Resfriado | COVID-19 | Sinusite |
|-------------|-------|-----------|-----------|----------|----------|
| Sim         | 25%   | 80%       | 5%        | 70%      | 10%      |
| Não         | 75%   | 20%       | 95%       | 30%      | 90%      |

## 7. Implementação

O sistema utiliza a biblioteca `pgmpy` (versão ≥ 1.1) com a classe `DiscreteBayesianNetwork`. A inferência é realizada pelo algoritmo de **Eliminação de Variáveis** (`VariableElimination`), exato e eficiente para redes pequenas.

A função principal de inferência recebe um dicionário de evidências `{variável: estado}` e retorna a distribuição de probabilidade posterior sobre `Doença`:

```python
posterior = run_inference(model, {"Febre": "sim", "Tosse": "sim"})
```

## 8. Exemplos de inferência

### Experimento 1 — Apenas febre

| Doença     | A priori | A posteriori | Δ       |
|------------|----------|--------------|---------|
| Gripe      | 30%      | 35,4%        | +5,4%   |
| Pneumonia  | 10%      | 12,5%        | +2,5%   |
| Resfriado  | 35%      | 14,6%        | -20,4%  |
| COVID-19   | 15%      | 16,7%        | +1,7%   |
| Sinusite   | 10%      | 5,6%         | -4,4%   |

A febre reduz a probabilidade de Resfriado (baixa prevalência de febre) e aumenta a de Gripe e Pneumonia.

### Experimento 2 — Febre + Tosse

| Doença     | A posteriori |
|------------|--------------|
| Gripe      | 43,6%        |
| COVID-19   | 19,2%        |
| Pneumonia  | 16,3%        |
| Resfriado  | 15,7%        |
| Sinusite   | 5,1%         |

### Experimento 3 — Febre + Tosse + Dor Muscular

| Doença     | A posteriori |
|------------|--------------|
| Gripe      | 56,1%        |
| COVID-19   | 23,1%        |
| Pneumonia  | 14,0%        |
| Resfriado  | 5,4%         |
| Sinusite   | 1,3%         |

A adição da dor muscular aumenta significativamente a probabilidade de Gripe, pois esse sintoma é muito mais característico dela do que de Resfriado ou Sinusite.

### Experimento 4 — Corriza + Tosse (sem febre)

Ao negar febre e confirmar corriza, Resfriado e Sinusite passam a liderar, enquanto Gripe e Pneumonia são fortemente penalizadas.

### Experimento 5 — Febre + Falta de Ar + Tosse

Pneumonia e COVID-19 sobem fortemente, pois ambas possuem alta associação com falta de ar.

## 9. Análise dos resultados

- A rede captura bem a diferenciação entre doenças a partir da combinação de sintomas.
- Sintomas discriminativos como **falta de ar** (alta em Pneumonia/COVID) e **corriza nasal** (alta em Resfriado/Sinusite) têm forte impacto na inferência.
- A atualização sequencial de evidências (teorema de Bayes aplicado iterativamente) é demonstrada claramente nos experimentos.

## 10. Independências condicionais

Na estrutura adotada, os sintomas são condicionalmente independentes entre si, dado o diagnóstico. Isso significa que `P(Febre, Tosse | Doença) = P(Febre | Doença) × P(Tosse | Doença)`. Essa suposição simplifica o modelo e é aceitável para fins educacionais, mas em cenários reais sintomas como febre e dor muscular podem ser correlacionados mesmo dado o diagnóstico.

## 11. Vantagens das Redes Bayesianas sobre sistemas baseados em regras

| Critério                | Sistema de regras | Rede Bayesiana               |
|-------------------------|-------------------|------------------------------|
| Incerteza               | Não representa    | Representa explicitamente    |
| Evidências incompletas  | Não raciocina     | Raciocina com o que há       |
| Atualização incremental | Não suportada     | Via teorema de Bayes         |
| Interpretabilidade      | Alta              | Moderada (via CPTs e grafos) |

## 12. Limitações

- A estrutura Naive Bayes assume independência condicional dos sintomas, o que não é sempre verdadeiro na medicina.
- As probabilidades foram definidas de forma educacional, sem validação clínica.
- O modelo não cobre comorbidades nem fatores de risco como idade e histórico.
- A rede não aprende automaticamente: as CPTs são fixas.

## 13. Possíveis melhorias

- Incorporar variáveis de risco (idade, vacinação, histórico) como nós pais adicionais.
- Aprender as CPTs a partir de dados clínicos reais.
- Adicionar mais doenças e sintomas para ampliar a cobertura.
- Implementar inferência aproximada (amostragem) para redes maiores.

## 14. Conclusão

O sistema demonstra com clareza os princípios de representação probabilística do conhecimento e de inferência bayesiana. A interface permite selecionar sintomas e observar como as probabilidades são atualizadas em tempo real, e os experimentos documentados mostram o comportamento esperado da rede para diferentes combinações de evidências.
