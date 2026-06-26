# Relatório Técnico — Agente Educacional Baseado em LLM

## 1. Introdução

Este relatório descreve um agente educacional de Inteligência Artificial construído sobre um Grande Modelo de Linguagem (LLM). O sistema utiliza a API da Anthropic com o modelo Claude Haiku para responder perguntas sobre IA, sistemas especialistas, redes bayesianas e raciocínio baseado em casos, por meio de uma interface de chat interativa em Streamlit.

O agente não substitui os mecanismos de raciocínio simbólico desenvolvidos nas questões anteriores. Seu papel é complementar: interpretar linguagem natural, gerar explicações didáticas e executar cálculos educacionais por meio de ferramentas.

## 2. Objetivo

Desenvolver uma aplicação envolvendo agentes baseados em LLM que:

- Responda perguntas sobre IA em linguagem natural.
- Utilize ferramentas especializadas para análise de regras, cálculo de entropia e explicação de conceitos.
- Mantenha histórico de conversa para interação de múltiplos turnos.
- Demonstre o ciclo de raciocínio com uso de ferramentas (tool use).

## 3. Arquitetura do agente

### 3.1 Componentes

| Componente         | Descrição                                                         |
|--------------------|-------------------------------------------------------------------|
| **LLM Base**       | Claude Haiku (`claude-haiku-4-5-20251001`) via Anthropic API     |
| **Interface**      | Streamlit com chat interativo e streaming de resposta             |
| **Ferramentas**    | 3 ferramentas Python executadas localmente                        |
| **Histórico**      | Lista de mensagens mantida na sessão Streamlit                    |
| **System Prompt**  | Define o papel do agente, escopo e idioma                         |

### 3.2 Módulos

- `app.py`: interface Streamlit com três páginas (Chat, Ferramentas, Sobre).
- `src/agent.py`: classe `LLMAgent` com chamada à API, execução de ferramentas e streaming.

## 4. Ciclo de execução (ReAct-style)

```
1. Usuário envia mensagem
2. Agente (LLM) processa com histórico + system prompt
3. LLM decide invocar ferramentas (tool_use) ou responder diretamente
4. Ferramentas são executadas localmente em Python
5. Resultados retornam ao LLM como tool_result
6. LLM gera resposta final incorporando os resultados
7. Ciclo repete até stop_reason = end_turn (máx. 5 iterações)
```

Esse padrão é conhecido como **ReAct** (Reason + Act), onde o modelo raciocina, age usando ferramentas e observa os resultados antes de concluir.

## 5. Ferramentas implementadas

### 5.1 `analisar_regra`

Recebe uma regra de produção no formato `SE...ENTÃO` e a decompõe em:

- Número e lista de condições.
- Conclusão.
- Tipo de operador lógico (E = conjunção).
- Complexidade da regra.

**Exemplo de entrada:**
```
SE febre = alta E tosse = sim ENTÃO diagnostico = gripe
```

**Saída:**
```
Análise da Regra:
- Condições (2): febre = alta, tosse = sim
- Conclusão: diagnostico = gripe
- Tipo: Regra de produção SE-ENTÃO
- Operador lógico: E (conjunção — todas as condições devem ser verdadeiras)
- Complexidade: 2 condição(ões) na premissa
```

### 5.2 `calcular_entropia`

Recebe uma distribuição de probabilidades e calcula:

- Entropia de Shannon (em bits).
- Entropia máxima possível.
- Pureza relativa.
- Interpretação qualitativa do resultado.

**Fórmula:**

```
H(X) = -Σ p(x) × log₂(p(x))
```

**Exemplo de entrada:**
```json
{"Gripe": 0.6, "Resfriado": 0.3, "Sinusite": 0.1}
```

**Saída:**
```
Entropia de Shannon: 1.2955 bits
Entropia máxima possível: 1.5850 bits (3 classes)
Pureza relativa: 18.3% (0% = máxima incerteza)
Distribuição normalizada:
  - Gripe: 60,0%
  - Resfriado: 30,0%
  - Sinusite: 10,0%
Interpretação: incerteza moderada — algumas classes se destacam.
```

### 5.3 `explicar_conceito`

Recebe um conceito de IA e um nível (básico/intermediário/avançado) e sinaliza ao LLM para gerar uma explicação estruturada naquele nível. O LLM utiliza o resultado da ferramenta como guia para calibrar a profundidade da resposta.

## 6. System Prompt

O system prompt define:

- **Papel:** assistente especializado em IA com foco educacional.
- **Escopo:** IA, sistemas especialistas, redes bayesianas, CBR, algoritmos de busca.
- **Idioma:** português brasileiro obrigatório.
- **Restrições:** não inventar informações; redirecionar perguntas fora do escopo.

## 7. Streaming de resposta

O agente utiliza a API de streaming da Anthropic para exibir a resposta em tempo real, caractere a caractere. Isso melhora a experiência do usuário, especialmente para respostas longas, e torna visível o processo de geração.

## 8. Tratamento do ciclo de ferramentas

Quando o LLM decide usar uma ferramenta (`stop_reason = tool_use`):

1. Os blocos `tool_use` são coletados da resposta do LLM.
2. Cada ferramenta é executada localmente.
3. O histórico é atualizado com a resposta do assistente (incluindo os blocos tool_use).
4. Uma nova mensagem do tipo `tool_result` é adicionada ao histórico.
5. O LLM é chamado novamente com o histórico atualizado.

Esse ciclo garante que o modelo tenha acesso ao resultado da ferramenta antes de concluir a resposta.

## 9. Papel do LLM versus raciocínio simbólico

Conforme exigido pelo enunciado, o LLM **não substitui** o motor de inferência baseado em regras.

| Responsabilidade                       | LLM        | Motor simbólico          |
|----------------------------------------|------------|--------------------------|
| Interpretação de linguagem natural     | ✅         | ❌                       |
| Geração de explicações didáticas       | ✅         | ❌                       |
| Forward/Backward Chaining              | ❌         | ✅ (ShellSistemaEsp.)    |
| Inferência bayesiana                   | ❌         | ✅ (RedesBayesianas)     |
| Identificação por ganho de informação  | ❌         | ✅ (Akinator)            |
| Cálculo de entropia                    | via tool   | pode ser simbólico       |

## 10. Exemplos de interação

### Exemplo 1 — Pergunta direta

**Usuário:** Qual a diferença entre forward chaining e backward chaining?

**Agente:** *(resposta didática explicando as duas estratégias com exemplo de sistema especialista)*

### Exemplo 2 — Uso de ferramenta (analisar_regra)

**Usuário:** Analise a regra: SE temperatura_alta = sim E computador_desliga_sozinho = sim ENTÃO diagnostico = superaquecimento

**Agente:** *(invoca `analisar_regra`, recebe decomposição, gera explicação complementar)*

### Exemplo 3 — Uso de ferramenta (calcular_entropia)

**Usuário:** Calcule a entropia de: Gripe 0.7, Pneumonia 0.2, Resfriado 0.1

**Agente:** *(invoca `calcular_entropia`, exibe cálculo, interpreta o resultado em contexto médico)*

## 11. Limitações

- Depende de chave de API da Anthropic (não funciona sem ela).
- O histórico cresce com a conversa; sessões muito longas aumentam o custo de tokens.
- As ferramentas são determinísticas; o LLM pode decidir não usá-las em algumas situações.
- Sem persistência: o histórico é perdido ao recarregar a página.

## 12. Possíveis melhorias

- Integrar o agente diretamente com o motor de inferência da Questão 1, permitindo que o usuário descreva sintomas em linguagem natural e o LLM converta para fatos estruturados.
- Adicionar memória persistente entre sessões.
- Implementar recuperação de contexto (RAG) sobre a base de conhecimento da shell.
- Adicionar ferramenta para exportar os resultados da conversa.

## 13. Conclusão

O agente demonstra como LLMs podem ser integrados a sistemas de IA simbólica sem substituir o raciocínio estruturado. O uso de ferramentas (tool use) amplia as capacidades do modelo com lógica Python determinística, enquanto o LLM trata a camada de linguagem natural e geração de explicações. A arquitetura é extensível para integrar os demais sistemas desenvolvidos no projeto.
