# Relatório Técnico - Shell Genérica de Sistema Especialista

## 1. Introdução

Este relatório descreve uma shell genérica de sistema especialista implementada em Python. A ferramenta permite criar aplicações baseadas em conhecimento para diagnóstico e recomendação de ações por meio de fatos, regras de produção e hipóteses.

O domínio de suporte técnico de computadores foi usado apenas como aplicação demonstrativa.

## 2. Objetivo da ferramenta

O objetivo é oferecer uma ferramenta reutilizável, semelhante conceitualmente ao Expert Sinta, na qual o especialista do domínio possa editar a base de conhecimento sem modificar o código-fonte.

## 3. Arquitetura implementada

A arquitetura segue a ideia de um agente baseado em conhecimento:

- Base de conhecimento: armazena fatos, regras, hipóteses, recomendações e históricos.
- Motor de inferência: aplica forward chaining, backward chaining e estratégia híbrida.
- Mecanismo de explicação: apresenta justificativas do tipo “Por quê?” e “Como?”.
- Interface: permite edição da base, consulta, visualização de explicações e manipulação do JSON.

## 4. Módulos do sistema

- `app.py`: interface Streamlit com as páginas exigidas.
- `src/models.py`: classes de fatos, condições, conclusões, regras, hipóteses e resultados.
- `src/knowledge_base.py`: carga, salvamento e acesso à base em JSON.
- `src/inference_engine.py`: implementação das três estratégias de inferência.
- `src/explanation_engine.py`: geração das explicações.
- `src/rule_editor.py`: operações de cadastro, edição e remoção.
- `src/utils.py`: funções auxiliares.

## 5. Estrutura de representação do conhecimento

A base `data/knowledge_base.json` possui:

- `facts`: fatos possíveis e perguntas associadas.
- `initial_facts`: fatos informados pelo usuário.
- `inferred_facts`: fatos concluídos pelo sistema.
- `rules`: regras de produção.
- `hypotheses`: objetivos ou diagnósticos possíveis.
- `recommendations`: recomendações por diagnóstico.
- `fired_rules_history`: histórico de regras disparadas.
- `asked_questions_history`: histórico de perguntas feitas.

## 6. Formato das regras

As regras seguem o padrão:

```text
SE condição1 E condição2 E ... ENTÃO conclusão
```

Cada regra contém `id`, `nome`, `condicoes`, `conclusao`, `recomendacao`, `explicacao` e `prioridade`.

## 7. Descrição da base de conhecimento

A base demonstrativa usa o domínio de suporte técnico de computadores. Ela contém 32 fatos possíveis, 22 regras e 9 hipóteses. Entre os diagnósticos estão superaquecimento, falha de memória RAM, problema no HD/SSD, malware, problema de fonte, problema de driver e falha de conexão com a internet.

## 8. Estratégia de inferência utilizada

O sistema permite que o usuário selecione a estratégia de inferência na interface: encadeamento para frente, encadeamento para trás ou estratégia híbrida.

## 9. Forward Chaining

O forward chaining parte dos fatos fornecidos pelo usuário. O motor percorre as regras por prioridade e dispara aquelas cujas condições são satisfeitas. Cada conclusão é adicionada à memória temporária da consulta como fato inferido. O processo se repete até que nenhuma nova regra possa ser disparada.

## 10. Backward Chaining

O backward chaining parte de uma hipótese. O motor localiza regras cuja conclusão corresponde à hipótese e tenta provar suas condições. Quando um fato necessário não é conhecido, a interface solicita a resposta do usuário. A hipótese é confirmada se uma regra concluir o diagnóstico com todas as condições satisfeitas.

## 11. Estratégia híbrida

A estratégia híbrida executa primeiro o forward chaining para descobrir conclusões prováveis. Depois aplica backward chaining sobre a hipótese mais consistente, ou sobre a hipótese escolhida pelo usuário, solicitando informações adicionais apenas quando necessário.

## 12. Implementação do mecanismo de explicação

O mecanismo de explicação usa o resultado da inferência, incluindo fatos usados, regras disparadas, hipóteses avaliadas e perguntas feitas. A explicação “Por quê?” justifica perguntas feitas durante backward chaining. A explicação “Como?” descreve quais fatos e regras levaram à conclusão final.

## 12.1 Prevenção de diagnóstico precipitado

O motor de inferência foi reforçado para evitar diagnóstico com evidência parcial. Uma hipótese só é confirmada quando pelo menos uma regra que conclui essa hipótese tem todas as suas condições satisfeitas. A seleção manual de uma hipótese pelo usuário não confirma o diagnóstico por si só.

No backward chaining, todas as regras relacionadas à hipótese alvo são avaliadas. Se uma condição obrigatória for respondida como “Não”, a regra é marcada como falha. Se alguma condição ficar como “Não sei” ou desconhecida, a regra é marcada como inconclusiva. Se nenhuma regra for totalmente satisfeita, o sistema informa que nenhuma regra confirmou completamente a hipótese selecionada com as evidências fornecidas.

## 12.2 Tratamento de “Não” e “Não sei”

A resposta “Não” nunca é usada como evidência positiva para uma condição esperada como `sim`. Ela torna a condição falsa para aquela regra. A resposta “Não sei” não confirma nem rejeita a condição; a regra fica inconclusiva quando depende dessa informação.

## 12.3 Status das regras avaliadas

As regras avaliadas podem ter três status:

- `satisfeita`: todas as condições foram confirmadas.
- `falhou`: pelo menos uma condição necessária foi negada ou ficou incompatível.
- `inconclusiva`: uma ou mais condições ficaram desconhecidas.

Esse registro é exibido na interface e usado pelo mecanismo de explicação.

## 12.4 Compatibilidade

A compatibilidade é calculada como:

```text
condições satisfeitas / total de condições avaliadas
```

Ela é apenas um apoio para interpretação. Uma hipótese com compatibilidade parcial, como 50% ou 66%, não é considerada diagnóstico confirmado. A confirmação exige regra 100% satisfeita.

No encadeamento para frente, quando nenhum diagnóstico é confirmado, o sistema ainda avalia regras relacionadas aos fatos iniciais. Se o usuário informa `computador_desliga_sozinho = sim`, uma regra que também exige `cheiro_queimado = sim` fica inconclusiva, pois possui evidência parcial. Nesse caso, a compatibilidade da regra é 1/2, ou 50%, e a hipótese relacionada exibe 50% de compatibilidade sem ser confirmada.

Assim, a diferença conceitual fica clara:

- Regras disparadas são regras 100% satisfeitas.
- Regras avaliadas são regras examinadas porque possuem alguma relação com os fatos da consulta.
- Compatibilidade parcial indica proximidade entre os fatos e uma hipótese, mas não autoriza recomendação como diagnóstico definitivo.

## 13. Exemplos de consultas realizadas

Exemplo 1:

- Fatos: `temperatura_alta = sim`, `computador_desliga_sozinho = sim`.
- Estratégia: forward chaining.
- Resultado: `diagnostico = superaquecimento`.
- Recomendação: limpar entradas de ar, verificar ventoinhas e trocar pasta térmica.

Exemplo 2:

- Fatos: `popups_estranhos = sim`, `navegador_redirecionando = sim`.
- Estratégia: forward chaining.
- Resultado: `diagnostico = malware`.
- Recomendação: executar antivírus, remover programas suspeitos e redefinir navegador.

Exemplo 3:

- Hipótese: falha de conexão com a internet.
- Fatos conhecidos: `sem_internet = sim`.
- Estratégia: backward chaining.
- Pergunta adicional: se o Wi-Fi não conecta ou se o cabo está desconectado.

## 14. Exemplos de explicação “Por quê?”

Pergunta: “Por que você perguntou sobre temperatura alta?”

Resposta esperada: “Perguntei sobre temperatura alta porque estava avaliando a hipótese de superaquecimento e a regra R01 possui esse fato como condição necessária.”

## 15. Exemplos de explicação “Como?”

Conclusão: superaquecimento.

Explicação esperada: “O sistema concluiu superaquecimento porque a regra R01 foi ativada com base nos fatos `temperatura_alta = sim` e `computador_desliga_sozinho = sim`.”

## 16. Limitações da solução

- As condições usam principalmente igualdade textual.
- Não há cálculo probabilístico ou fator de certeza.
- A interface de backward chaining coleta respostas durante a execução Streamlit, dependendo do estado da sessão.
- O sistema não importa bases em formatos externos além do JSON usado no projeto.

## 17. Possíveis melhorias

- Adicionar fator de certeza por regra.
- Permitir operadores comparativos para valores numéricos.
- Criar importação e exportação em CSV.
- Adicionar autenticação para edição da base.
- Melhorar a seleção automática da hipótese mais provável.

## 18. Conclusão

A solução implementa uma shell genérica de sistema especialista, com base de conhecimento editável, persistência em JSON, três estratégias de inferência, recomendações e explicações. O domínio de suporte técnico comprova o funcionamento da ferramenta, mas a estrutura permite reutilização em outros domínios por meio da edição da base de conhecimento.
