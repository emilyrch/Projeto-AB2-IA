# Shell Sistema Especialista

Shell genérica de sistema especialista em Python para criar aplicações baseadas em conhecimento, com regras de produção, diagnósticos, recomendações e explicação do raciocínio.

O domínio incluído é uma demonstração de suporte técnico de computadores. A ferramenta não é presa a esse domínio: uma nova aplicação pode ser criada editando ou substituindo `data/knowledge_base.json`.

## Objetivo

Permitir que especialistas cadastrem fatos, regras e hipóteses de diagnóstico sem alterar o código-fonte, usando uma interface simples em Streamlit e persistência em JSON.

## Tecnologias usadas

- Python
- Streamlit
- JSON
- Módulos próprios para base de conhecimento, inferência, editor de regras e explicações

## Como instalar dependências

```bash
pip install -r requirements.txt
```

## Como executar

```bash
streamlit run app.py
```

Depois, acesse o endereço exibido pelo Streamlit no navegador.

## Como editar a base de conhecimento

Use a página `Editor da Base de Conhecimento` para cadastrar, listar, editar e remover fatos, regras e hipóteses. Também é possível editar o JSON diretamente na página `Base JSON`.

As regras seguem o formato:

```text
SE condição1 E condição2 E ... ENTÃO conclusão
```

Exemplo:

```text
SE temperatura_alta = sim E computador_desliga_sozinho = sim ENTÃO diagnostico = superaquecimento
```

## Como realizar uma consulta

1. Abra a página `Consulta/Diagnóstico`.
2. Selecione fatos conhecidos e informe `Sim`, `Não` ou `Não sei`.
3. Escolha a estratégia de inferência.
4. Execute o diagnóstico.
5. Consulte a página `Explicações` para ver fatos usados, regras disparadas, hipóteses avaliadas e justificativas.

## Modos de inferência

- Encadeamento para frente: parte dos fatos iniciais e dispara regras cujas condições são satisfeitas.
- Encadeamento para trás: parte de uma hipótese e tenta prová-la verificando as regras que a concluem.
- Encadeamento híbrido: aplica forward chaining primeiro e depois usa backward chaining para confirmar a hipótese mais consistente.

## Interpretação dos resultados

O sistema só confirma um diagnóstico quando pelo menos uma regra de produção é totalmente satisfeita. Compatibilidade parcial não é diagnóstico confirmado.

- Regras disparadas: regras em que todas as condições foram satisfeitas. Elas podem confirmar diagnósticos e gerar recomendações.
- Regras avaliadas: regras testadas pelo motor de inferência, mesmo quando não foram disparadas.
- Regra satisfeita: todas as condições necessárias foram confirmadas.
- Regra falhou: pelo menos uma condição obrigatória foi respondida como `Não` ou tem valor incompatível.
- Regra inconclusiva: uma ou mais condições ficaram como `Não sei` ou desconhecidas.

Exemplo: compatibilidade de 50% com `Falha de memória RAM` significa apenas que parte das evidências combina com essa hipótese. A recomendação de RAM só aparece se uma regra for 100% satisfeita.

Quando o usuário informa apenas um fato, o sistema avalia as regras que contêm esse fato. Essas regras aparecem em `Regras avaliadas` mesmo quando não são disparadas. Por exemplo, se `computador_desliga_sozinho = sim` satisfaz uma de duas condições de uma regra de fonte, a hipótese pode aparecer com 50% de compatibilidade, mas continua não confirmada até que uma regra fique 100% satisfeita.

Na tela de consulta:

- `Regras disparadas` mostra somente regras totalmente satisfeitas.
- `Regras avaliadas` mostra regras relacionadas aos fatos informados, incluindo regras inconclusivas ou falhas.
- `Compatibilidade` mostra a maior compatibilidade entre as regras de cada hipótese.
- `Diagnóstico final` só aparece quando há regra disparada.

## Como executar os testes

```bash
python test_inference_manual.py
```

O script executa cinco cenários básicos, incluindo o caso em que `tela_azul = sim` e `reinicia_frequentemente = nao` não pode confirmar falha de memória RAM.

## Estrutura de pastas

```text
app.py
README.md
requirements.txt
data/
  knowledge_base.json
src/
  __init__.py
  knowledge_base.py
  inference_engine.py
  explanation_engine.py
  rule_editor.py
  models.py
  utils.py
reports/
  relatorio_tecnico.md
```

## Observação sobre vídeo

O vídeo ou apresentação não foi incluído porque será produzido separadamente.

## Checklist da Questão 1

| Item exigido | Status | Arquivos principais |
|---|---:|---|
| Shell genérica de sistema especialista | Atendido | `app.py`, `src/knowledge_base.py`, `src/inference_engine.py` |
| Uso de Python | Atendido | Todo o projeto |
| Interface Streamlit organizada | Atendido | `app.py` |
| Persistência em JSON | Atendido | `data/knowledge_base.json`, `src/knowledge_base.py` |
| Construção de bases com fatos e regras | Atendido | `app.py`, `src/rule_editor.py` |
| Diagnóstico a partir de informações do usuário | Atendido | `app.py`, `src/inference_engine.py` |
| Recomendações associadas | Atendido | `data/knowledge_base.json`, `src/inference_engine.py` |
| Explicação do raciocínio | Atendido | `src/explanation_engine.py`, `app.py` |
| Reutilização em diferentes domínios | Atendido | `data/knowledge_base.json`, `src/knowledge_base.py` |
| Cadastro/listagem/edição/remoção de fatos | Atendido | `app.py`, `src/rule_editor.py` |
| Cadastro/listagem/edição/remoção de regras | Atendido | `app.py`, `src/rule_editor.py` |
| Cadastro/listagem/edição/remoção de hipóteses | Atendido | `app.py`, `src/rule_editor.py` |
| Modelo de regra com id, nome, condições, conclusão, recomendação, explicação e prioridade | Atendido | `src/models.py`, `data/knowledge_base.json` |
| Fatos possíveis, iniciais, inferidos e históricos no JSON | Atendido | `data/knowledge_base.json` |
| Forward chaining | Atendido | `src/inference_engine.py` |
| Backward chaining | Atendido | `src/inference_engine.py` |
| Estratégia híbrida | Atendido | `src/inference_engine.py` |
| Solicitação de informações adicionais | Atendido | `app.py`, `src/inference_engine.py` |
| Explicação “Por quê?” | Atendido | `src/explanation_engine.py` |
| Explicação “Como?” | Atendido | `src/explanation_engine.py` |
| Página Início | Atendido | `app.py` |
| Página Editor da Base | Atendido | `app.py` |
| Página Consulta/Diagnóstico | Atendido | `app.py` |
| Página Explicações | Atendido | `app.py` |
| Página Base JSON | Atendido | `app.py` |
| Domínio suporte técnico de computadores | Atendido | `data/knowledge_base.json` |
| Pelo menos 20 regras | Atendido: 22 regras | `data/knowledge_base.json` |
| Pelo menos 30 fatos | Atendido: 32 fatos | `data/knowledge_base.json` |
| Pelo menos 5 diagnósticos | Atendido: 9 hipóteses | `data/knowledge_base.json` |
| Diagnósticos obrigatórios | Atendido | `data/knowledge_base.json` |
| Relatório técnico em Markdown | Atendido | `reports/relatorio_tecnico.md` |
| README claro | Atendido | `README.md` |
| Não criar vídeo/apresentação | Atendido | Este README |

## Tabela de conformidade

| Requisito da Questão 1 | Conformidade | Onde foi implementado |
|---|---:|---|
| Objetivo geral: shell genérica baseada em conhecimento | Sim | `src/knowledge_base.py`, `src/models.py`, `app.py` |
| Especialista cria aplicações sem alterar código | Sim | `app.py`, `data/knowledge_base.json` |
| Tecnologias desejadas | Sim | `requirements.txt`, `app.py` |
| Editor da base de conhecimento | Sim | `app.py`, `src/rule_editor.py` |
| Representação explícita do conhecimento | Sim | `data/knowledge_base.json`, `src/models.py` |
| Motor de inferência com três estratégias | Sim | `src/inference_engine.py` |
| Perguntas adicionais ao usuário | Sim | `app.py`, `src/inference_engine.py` |
| Mecanismo de explicação | Sim | `src/explanation_engine.py`, `app.py` |
| Prevenção de diagnóstico precipitado | Sim | `src/inference_engine.py`, `test_inference_manual.py` |
| Compatibilidade parcial sem confirmação automática | Sim | `src/inference_engine.py`, `app.py` |
| Interface com cinco páginas | Sim | `app.py` |
| Aplicação demonstrativa obrigatória | Sim | `data/knowledge_base.json` |
| Relatório técnico obrigatório | Sim | `reports/relatorio_tecnico.md` |
| README obrigatório | Sim | `README.md` |
| Critérios de qualidade e persistência | Sim | `src/`, `data/knowledge_base.json`, testes de sintaxe descritos na entrega |
