# Projeto AB2 Inteligência Artificial 2026.1

**Disciplina:** Inteligência Artificial  
**Período:** 2026.1  
**Professor:** Evandro Costa  
**Instituição:** UFAL

**Equipe:**
- Emily Vitória
- Francys Samuel
- Leonardo Lucca
- Júllya Cabral
- Evaldo Braz

**Drive com apresentação**
- https://drive.google.com/drive/u/4/folders/1bc-JjubgqO_KEKDUId386tRBZL1WN6UG

---

## Estrutura do repositório

```
Projeto-AB2-IA/
│
├── ShellSistemaEspecialista/   ← Questão 1 (0–5 pts)
├── Akinator/                   ← Questão 2.1 (parte dos 0–3 pts)
├── RedesBayesianas/            ← Questão 2.2 (parte dos 0–3 pts)
└── AgenteIA_LLM/               ← Questão 3 (0–2 pts)
```

---

## Questão 1 Shell Genérica de Sistema Especialista

> **Pasta:** [ShellSistemaEspecialista/](ShellSistemaEspecialista/)

### Descrição

Ferramenta genérica para construção de aplicações de sistemas baseados em conhecimento voltados a diagnóstico e recomendação de ações. Permite que especialistas de domínio construam aplicações definindo apenas a base de conhecimento em JSON, sem alterar o código-fonte.

### O que foi implementado

| Módulo | Descrição |
|--------|-----------|
| **Editor da Base** | Cadastro, edição e remoção de fatos, regras e hipóteses via interface |
| **Base de Conhecimento** | Fatos, regras de produção, hipóteses e recomendações persistidas em JSON |
| **Motor de Inferência** | Forward Chaining, Backward Chaining e estratégia híbrida |
| **Mecanismo de Explicação** | Responde "Por quê?" e "Como?" para cada consulta |
| **Interface Web** | Aplicação Streamlit com múltiplas páginas |

### Base demonstrativa

Domínio de **suporte técnico de computadores**:
- 32 fatos possíveis
- 22 regras de produção
- 9 hipóteses de diagnóstico (superaquecimento, malware, falha de RAM, etc.)

### Como executar

```bash
cd ShellSistemaEspecialista
pip install -r requirements.txt
streamlit run app.py
```

### Relatório técnico

[ShellSistemaEspecialista/reports/relatorio_tecnico.md](ShellSistemaEspecialista/reports/relatorio_tecnico.md)

---

## Questão 2.1 Sistema Akinator de Identificação de Animais

> **Pasta:** [Akinator/](Akinator/)

### Descrição

Sistema baseado em conhecimento no estilo Akinator capaz de identificar um animal por meio de uma sequência de perguntas sim/não. O sistema seleciona as perguntas que maximizam o ganho de informação (divisão mais equilibrada dos candidatos), reduzindo o espaço de hipóteses rapidamente.

### O que foi implementado

| Componente | Descrição |
|------------|-----------|
| **Base de Conhecimento** | 22 animais × 20 atributos em JSON |
| **Motor de Inferência** | Busca no espaço de hipóteses com ganho de informação |
| **Filtragem de Candidatos** | Elimina animais incompatíveis a cada resposta |
| **Interface Web** | Jogo interativo, visualização da base e editor de animais |

### Base de conhecimento

- **22 entidades:** Cachorro, Gato, Leão, Elefante, Águia, Papagaio, Cobra, Crocodilo, Tubarão, Golfinho, Abelha, Borboleta, Onça-pintada, Girafa, Pinguim, Morcego, Tartaruga, Cavalo, Guepardo, Aranha, Macaco, Urso
- **20 atributos:** mamífero, ave, réptil, peixe, inseto, doméstico, carnívoro, herbívoro, voa, aquático, selvagem, grande porte, tem penas, tem pelo, tem escamas, venenoso, noturno, África, Brasil, corre rápido

### Mecanismo de inferência

A cada turno, o sistema escolhe o atributo que minimiza `|count_sim - count_nao|` entre os candidatos restantes, equivalente a maximizar a entropia binária (ganho de informação máximo). A resposta "Não sei" não elimina candidatos.

### Como executar

```bash
cd Akinator
pip install -r requirements.txt
streamlit run app.py
```

### Relatório técnico

[Akinator/reports/relatorio_tecnico.md](Akinator/reports/relatorio_tecnico.md)

---

## Questão 2.2 Diagnóstico Médico com Redes Bayesianas

> **Pasta:** [RedesBayesianas/](RedesBayesianas/)

### Descrição

Sistema inteligente de diagnóstico de doenças respiratórias baseado em Redes Bayesianas. Modela relações probabilísticas entre doenças e sintomas, realiza inferência bayesiana a partir de evidências fornecidas pelo usuário e atualiza as probabilidades em tempo real.

> **Aviso:** sistema de finalidade exclusivamente educacional. Não deve ser usado como ferramenta real de diagnóstico médico.

### O que foi implementado

| Componente | Descrição |
|------------|-----------|
| **Rede Bayesiana** | Estrutura em estrela com 6 variáveis (1 latente + 5 observáveis) |
| **CPTs** | Tabelas de Probabilidade Condicional definidas com base em conhecimento médico geral |
| **Inferência** | Eliminação de Variáveis via `pgmpy` (`DiscreteBayesianNetwork`) |
| **Interface Web** | Diagnóstico interativo, experimentos documentados e visualização da rede |

### Doenças modeladas

| Doença | P(a priori) |
|--------|-------------|
| Resfriado | 35% |
| Gripe | 30% |
| COVID-19 | 15% |
| Pneumonia | 10% |
| Sinusite | 10% |

### Sintomas observáveis

Febre, Tosse, Dor Muscular, Corriza Nasal, Falta de Ar

### Como executar

```bash
cd RedesBayesianas
pip install -r requirements.txt
streamlit run app.py
```

### Relatório técnico

[RedesBayesianas/reports/relatorio_tecnico.md](RedesBayesianas/reports/relatorio_tecnico.md)

---

## Questão 3 Agente Educacional Baseado em LLM

> **Pasta:** [AgenteIA_LLM/](AgenteIA_LLM/)

### Descrição

Agente educacional de IA construído sobre o modelo Claude Haiku da Anthropic. Responde perguntas sobre IA em linguagem natural e possui ferramentas especializadas para análise de regras de produção, cálculo de entropia e explicação de conceitos de IA. Mantém histórico de conversa para interação de múltiplos turnos.

O LLM **não substitui** o raciocínio simbólico das questões anteriores. Seu papel é interpretar linguagem natural, gerar explicações didáticas e executar cálculos educacionais via ferramentas.

### O que foi implementado

| Componente | Descrição |
|------------|-----------|
| **LLM Base** | Claude Haiku via Anthropic API com streaming |
| **Tool Use** | Ciclo ReAct: LLM decide, ferramenta executa, resultado integrado |
| **Ferramentas** | `analisar_regra`, `calcular_entropia`, `explicar_conceito` |
| **Interface Web** | Chat interativo com Streamlit, sugestões de perguntas |

### Ferramentas do agente

| Ferramenta | Função |
|------------|--------|
| `analisar_regra` | Decompõe uma regra SE...ENTÃO em condições e conclusão |
| `calcular_entropia` | Calcula entropia de Shannon de uma distribuição de probabilidades |
| `explicar_conceito` | Gera explicação estruturada de conceitos de IA em níveis básico/intermediário/avançado |

### Como executar

```bash
cd AgenteIA_LLM
pip install -r requirements.txt
# Configure a variável de ambiente com sua chave da Anthropic:
export ANTHROPIC_API_KEY="sua-chave-aqui"
streamlit run app.py
```

Ou insira a API key diretamente na interface, na barra lateral.

### Relatório técnico

[AgenteIA_LLM/reports/relatorio_tecnico.md](AgenteIA_LLM/reports/relatorio_tecnico.md)

---

## Dependências gerais

Todos os projetos utilizam Python 3.11+. As dependências específicas estão em cada `requirements.txt`.

| Biblioteca | Uso |
|------------|-----|
| `streamlit` | Interface web (todos os projetos) |
| `pgmpy` | Rede Bayesiana (Q2.2) |
| `anthropic` | API do Claude (Q3) |
| `pandas`, `numpy` | Manipulação de dados (Q2.2) |

---

## Resumo das entregas

| Questão | Pasta | Pontuação máxima | Status |
|---------|-------|-----------------|--------|
| Q1 Shell Sistema Especialista | `ShellSistemaEspecialista/` | 5 pts | ✅ |
| Q2.1 Akinator | `Akinator/` | parte de 3 pts | ✅ |
| Q2.2 Redes Bayesianas | `RedesBayesianas/` | parte de 3 pts | ✅ |
| Q3 Agente LLM | `AgenteIA_LLM/` | 2 pts | ✅ |
