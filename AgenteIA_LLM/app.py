from __future__ import annotations

import os

import streamlit as st

from src.agent import LLMAgent

st.set_page_config(page_title="Agente IA — Claude", page_icon="🤖", layout="wide")

SUGGESTED_QUESTIONS = [
    "O que é encadeamento para trás (backward chaining)?",
    "Como funciona uma Rede Bayesiana? Me dê um exemplo.",
    "Analise a regra: SE febre = alta E tosse = sim ENTÃO diagnostico = gripe",
    "Calcule a entropia de: {Gripe: 0.6, Resfriado: 0.3, Sinusite: 0.1}",
    "Qual a diferença entre forward e backward chaining?",
    "O que é Raciocínio Baseado em Casos (CBR)?",
    "Explique o teorema de Bayes com um exemplo médico.",
    "Como funciona o ganho de informação em árvores de decisão?",
]


def get_agent() -> LLMAgent:
    if "agent" not in st.session_state:
        api_key = st.session_state.get("api_key", "") or os.getenv("ANTHROPIC_API_KEY", "")
        st.session_state.agent = LLMAgent(api_key=api_key or None)
    return st.session_state.agent


def page_chat() -> None:
    st.title("🤖 Agente Educacional de IA")
    st.write(
        "Agente baseado em LLM para responder perguntas sobre Inteligência Artificial, "
        "sistemas especialistas, redes bayesianas e raciocínio baseado em casos. "
        "O agente possui ferramentas para analisar regras, calcular entropia e explicar conceitos."
    )

    agent = get_agent()

    if not agent.is_ready():
        st.warning("Configure a API key da Anthropic na barra lateral para usar o agente.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.subheader("Sugestões de perguntas")
    cols = st.columns(2)
    for i, suggestion in enumerate(SUGGESTED_QUESTIONS):
        if cols[i % 2].button(suggestion, key=f"sugg_{i}", use_container_width=True):
            st.session_state.pending_message = suggestion
            st.rerun()

    pending = st.session_state.pop("pending_message", None)
    user_input = st.chat_input("Digite sua pergunta sobre IA...") or pending

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            if agent.is_ready():
                response_placeholder = st.empty()
                full_response = ""
                for chunk in agent.chat(user_input):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            else:
                full_response = (
                    "**Agente não configurado.** "
                    "Insira sua API key da Anthropic na barra lateral e recarregue a página."
                )
                st.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})


def page_tools() -> None:
    st.title("Ferramentas do Agente")
    st.write(
        "O agente possui ferramentas especializadas que pode invocar automaticamente "
        "durante a conversa para realizar cálculos e análises."
    )

    tools_info = [
        {
            "nome": "analisar_regra",
            "descricao": "Analisa uma regra de produção SE...ENTÃO, decompondo condições e conclusão.",
            "exemplo": "SE febre = alta E tosse = sim ENTÃO diagnostico = gripe",
        },
        {
            "nome": "calcular_entropia",
            "descricao": "Calcula a entropia de Shannon de uma distribuição de probabilidades e interpreta o resultado.",
            "exemplo": '{"Gripe": 0.6, "Resfriado": 0.3, "Sinusite": 0.1}',
        },
        {
            "nome": "explicar_conceito",
            "descricao": "Gera explicação estruturada de um conceito de IA nos níveis básico, intermediário ou avançado.",
            "exemplo": "forward chaining — nível intermediário",
        },
    ]

    for tool in tools_info:
        with st.expander(f"🔧 `{tool['nome']}`", expanded=True):
            st.write(f"**Descrição:** {tool['descricao']}")
            st.write(f"**Exemplo de entrada:** `{tool['exemplo']}`")

    st.divider()
    st.subheader("Como o agente usa as ferramentas")
    st.write(
        "Quando o usuário faz uma pergunta, o LLM decide automaticamente se deve invocar "
        "uma ou mais ferramentas antes de responder. Após executar a ferramenta, o resultado "
        "é incorporado ao contexto e o agente continua a resposta. "
        "Esse ciclo pode se repetir (até 5 iterações) até o agente considerar a resposta completa."
    )
    st.code("""
Usuário → LLM → [decide usar ferramenta] → executa ferramenta
                                         → recebe resultado
                                         → continua resposta
         ← resposta final com análise incorporada
""", language="text")


def page_about() -> None:
    st.title("Sobre o Agente")
    st.markdown("""
## Arquitetura

O agente é construído sobre o modelo **Claude Haiku** da Anthropic, com as seguintes características:

### Componentes

| Componente | Descrição |
|------------|-----------|
| **LLM Base** | Claude Haiku (claude-haiku-4-5-20251001) |
| **Interface** | Streamlit com chat interativo |
| **Ferramentas** | 3 ferramentas especializadas em IA |
| **Histórico** | Mantido na sessão para conversa contínua |
| **Streaming** | Resposta gerada em tempo real |

### Ferramentas disponíveis

1. `analisar_regra` — Decomposição de regras de produção SE...ENTÃO
2. `calcular_entropia` — Cálculo de entropia de Shannon com interpretação
3. `explicar_conceito` — Explicação estruturada de conceitos de IA

### Ciclo de execução

```
1. Usuário envia mensagem
2. Agente (LLM) processa com histórico da conversa
3. LLM decide se usa ferramentas
4. Ferramentas são executadas localmente (Python)
5. Resultados retornam ao LLM
6. LLM gera resposta final incorporando os resultados
```

### Papel do LLM vs. lógica simbólica

O LLM **não substitui** o motor de inferência simbólico da Questão 1. Seu papel é:
- Interpretar perguntas em linguagem natural.
- Gerar explicações mais naturais e didáticas.
- Executar cálculos educacionais via ferramentas.
- Manter contexto de conversa de múltiplos turnos.

O raciocínio simbólico (regras, forward/backward chaining, redes bayesianas) permanece nos sistemas especializados.
""")


st.sidebar.title("🤖 Agente IA — Claude")

api_key_input = st.sidebar.text_input(
    "API Key da Anthropic",
    type="password",
    value=st.session_state.get("api_key", os.getenv("ANTHROPIC_API_KEY", "")),
    help="Obtenha sua chave em console.anthropic.com",
)
if api_key_input != st.session_state.get("api_key", ""):
    st.session_state.api_key = api_key_input
    if "agent" in st.session_state:
        del st.session_state.agent

agent = get_agent()
status = "✅ Conectado" if agent.is_ready() else "❌ Sem API key"
st.sidebar.write(f"**Status:** {status}")

if st.sidebar.button("🗑️ Limpar conversa"):
    st.session_state.messages = []
    agent.reset()
    st.rerun()

st.sidebar.divider()
page = st.sidebar.radio("Página", ["Chat", "Ferramentas", "Sobre"])

if page == "Chat":
    page_chat()
elif page == "Ferramentas":
    page_tools()
else:
    page_about()
