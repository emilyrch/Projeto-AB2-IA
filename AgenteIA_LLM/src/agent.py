from __future__ import annotations

import os
from typing import Any, Dict, Generator, List, Optional

import anthropic

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """Você é um assistente especializado em Inteligência Artificial, atuando como um agente educacional
que ajuda estudantes a entender conceitos de IA, sistemas especialistas, redes bayesianas e raciocínio baseado em casos.

Seu papel:
- Responder perguntas sobre IA de forma clara e didática em português brasileiro.
- Explicar algoritmos e técnicas de IA com exemplos práticos.
- Ajudar a debugar e entender sistemas baseados em conhecimento.
- Sugerir abordagens para problemas de IA.

Regras:
- Sempre responda em português brasileiro.
- Seja objetivo mas completo. Use exemplos quando útil.
- Se uma pergunta estiver fora do escopo de IA, gentilmente redirecione.
- Nunca invente informações. Se não souber, diga claramente."""

TOOLS = [
    {
        "name": "analisar_regra",
        "description": "Analisa uma regra de produção no formato SE...ENTÃO e explica seu funcionamento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "regra": {
                    "type": "string",
                    "description": "A regra de produção, ex: SE febre = alta E tosse = sim ENTÃO diagnostico = gripe",
                }
            },
            "required": ["regra"],
        },
    },
    {
        "name": "calcular_entropia",
        "description": "Calcula a entropia de Shannon de uma distribuição de probabilidades e explica o resultado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "distribuicao": {
                    "type": "object",
                    "description": "Dicionário com classe -> probabilidade, ex: {Gripe: 0.6, Resfriado: 0.4}",
                }
            },
            "required": ["distribuicao"],
        },
    },
    {
        "name": "explicar_conceito",
        "description": "Gera uma explicação detalhada de um conceito específico de IA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "conceito": {
                    "type": "string",
                    "description": "Nome do conceito, ex: 'forward chaining', 'rede bayesiana', 'CBR'",
                },
                "nivel": {
                    "type": "string",
                    "enum": ["basico", "intermediario", "avancado"],
                    "description": "Nível de profundidade da explicação",
                },
            },
            "required": ["conceito"],
        },
    },
]


def _execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    if tool_name == "analisar_regra":
        regra = tool_input.get("regra", "")
        parts = regra.upper().split("ENTÃO") if "ENTÃO" in regra.upper() else regra.upper().split("ENTAO")
        if len(parts) == 2:
            condicoes = parts[0].replace("SE", "").strip()
            conclusao = parts[1].strip()
            conds = [c.strip() for c in condicoes.split(" E ") if c.strip()]
            return (
                f"**Análise da Regra:**\n"
                f"- **Condições ({len(conds)}):** {', '.join(conds)}\n"
                f"- **Conclusão:** {conclusao}\n"
                f"- **Tipo:** Regra de produção SE-ENTÃO\n"
                f"- **Operador lógico:** E (conjunção — todas as condições devem ser verdadeiras)\n"
                f"- **Complexidade:** {len(conds)} condição(ões) na premissa"
            )
        return f"Regra recebida: {regra}\nNão foi possível identificar o padrão SE...ENTÃO esperado."

    if tool_name == "calcular_entropia":
        import math
        dist = tool_input.get("distribuicao", {})
        if not dist:
            return "Distribuição vazia."
        total = sum(dist.values())
        if total == 0:
            return "Soma das probabilidades é zero."
        normalized = {k: v / total for k, v in dist.items()}
        entropy = -sum(p * math.log2(p) for p in normalized.values() if p > 0)
        max_entropy = math.log2(len(dist))
        lines = [f"**Entropia de Shannon:** {entropy:.4f} bits"]
        lines.append(f"**Entropia máxima possível:** {max_entropy:.4f} bits ({len(dist)} classes)")
        lines.append(f"**Pureza relativa:** {(1 - entropy/max_entropy)*100:.1f}% (0% = máxima incerteza)")
        lines.append("\n**Distribuição normalizada:**")
        for classe, prob in sorted(normalized.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {classe}: {prob:.1%}")
        if entropy < 0.5:
            lines.append("\n*Interpretação: distribuição muito concentrada — pouca incerteza.*")
        elif entropy < max_entropy * 0.7:
            lines.append("\n*Interpretação: incerteza moderada — algumas classes se destacam.*")
        else:
            lines.append("\n*Interpretação: alta incerteza — classes muito equilibradas.*")
        return "\n".join(lines)

    if tool_name == "explicar_conceito":
        conceito = tool_input.get("conceito", "")
        nivel = tool_input.get("nivel", "basico")
        return f"[Ferramenta executada] Conceito solicitado: **{conceito}** (nível: {nivel}). O LLM complementará esta explicação com detalhes."

    return f"Ferramenta '{tool_name}' não reconhecida."


class LLMAgent:
    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=key) if key else None
        self.history: List[Dict[str, Any]] = []

    def is_ready(self) -> bool:
        return self.client is not None

    def reset(self) -> None:
        self.history = []

    def chat(self, user_message: str) -> Generator[str, None, None]:
        """Sends a message and yields response chunks (streaming). Handles tool use."""
        if not self.client:
            yield "**Erro:** API key da Anthropic não configurada. Defina a variável de ambiente `ANTHROPIC_API_KEY`."
            return

        self.history.append({"role": "user", "content": user_message})

        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            full_response = ""
            tool_uses = []
            stop_reason = None

            with self.client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            ) as stream:
                for event in stream:
                    if hasattr(event, "type"):
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                full_response += event.delta.text
                                yield event.delta.text
                        elif event.type == "message_delta":
                            if hasattr(event.delta, "stop_reason"):
                                stop_reason = event.delta.stop_reason

                final_msg = stream.get_final_message()
                for block in final_msg.content:
                    if block.type == "tool_use":
                        tool_uses.append(block)

            if not tool_uses:
                self.history.append({"role": "assistant", "content": full_response})
                break

            tool_results = []
            for tool_block in tool_uses:
                result_text = _execute_tool(tool_block.name, tool_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result_text,
                })
                yield f"\n\n---\n**Ferramenta usada:** `{tool_block.name}`\n{result_text}\n---\n\n"

            assistant_content = []
            if full_response:
                assistant_content.append({"type": "text", "text": full_response})
            for tb in tool_uses:
                assistant_content.append({"type": "tool_use", "id": tb.id, "name": tb.name, "input": tb.input})

            self.history.append({"role": "assistant", "content": assistant_content})
            self.history.append({"role": "user", "content": tool_results})
