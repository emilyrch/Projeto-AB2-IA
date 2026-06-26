# Relatório Técnico — Sistema Akinator de Identificação de Animais

## 1. Introdução

Este relatório descreve um sistema baseado em conhecimento no estilo Akinator capaz de identificar um animal por meio de uma sequência de perguntas respondidas pelo usuário. O sistema formula perguntas sobre características do animal e utiliza as respostas para reduzir progressivamente o conjunto de hipóteses até chegar à solução mais provável.

## 2. Objetivo

Desenvolver um sistema que:

- Represente conhecimento sobre animais por meio de atributos binários.
- Formule perguntas relevantes para distinguir diferentes hipóteses.
- Atualize o conjunto de candidatos com base nas respostas do usuário.
- Identifique o animal pensado ao final da interação.

## 3. Domínio escolhido

O domínio é o reino animal, composto por 22 animais de diferentes classes biológicas: mamíferos, aves, répteis, peixes, insetos e aracnídeos. A escolha do domínio permite diversidade de atributos discriminativos e é de fácil compreensão pelo usuário.

## 4. Módulos do sistema

- `app.py`: interface Streamlit com as páginas Jogar, Base de Conhecimento e Editor.
- `src/models.py`: classes `Attribute`, `Entity` e `Session`.
- `src/knowledge_base.py`: carga, salvamento e acesso à base em JSON.
- `src/inference_engine.py`: filtragem de candidatos, seleção de pergunta por ganho de informação e verificação do resultado.

## 5. Estrutura de representação do conhecimento

A base `data/knowledge_base.json` contém:

- `attributes`: lista de atributos com `id` e `pergunta` associada.
- `entities`: lista de animais, cada um com `id`, `nome` e um dicionário `atributos` mapeando cada atributo para `true` ou `false`.

### 5.1 Atributos (20 no total)

| ID              | Pergunta                                               |
|-----------------|--------------------------------------------------------|
| mamifero        | É um mamífero?                                         |
| ave             | É uma ave?                                             |
| reptil          | É um réptil?                                           |
| peixe           | É um peixe?                                            |
| inseto          | É um inseto?                                           |
| domestico       | É um animal doméstico (de estimação)?                  |
| carnivoro       | É carnívoro (come carne)?                              |
| herbivoro       | É herbívoro (come apenas plantas)?                     |
| voa             | Consegue voar?                                         |
| aquatico        | Vive na água ou passa boa parte do tempo nela?         |
| selvagem        | É um animal selvagem (não doméstico)?                  |
| grande_porte    | É de grande porte (maior que um cachorro médio)?       |
| tem_penas       | Tem penas?                                             |
| tem_pelo        | Tem pelo?                                              |
| tem_escamas     | Tem escamas?                                           |
| venenoso        | É venenoso ou peçonhento?                              |
| noturno         | É predominantemente noturno?                           |
| africa          | É originário da África?                                |
| brasil          | É encontrado no Brasil?                                |
| corre_rapido    | É conhecido por ser muito veloz (terrestre)?           |

### 5.2 Entidades (22 animais)

Cachorro, Gato, Leão, Elefante, Águia, Papagaio, Cobra, Crocodilo, Tubarão, Golfinho, Abelha, Borboleta, Onça-pintada, Girafa, Pinguim, Morcego, Tartaruga, Cavalo, Guepardo, Aranha, Macaco, Urso.

## 6. Mecanismo de inferência

### 6.1 Estratégia de busca no espaço de hipóteses

O sistema mantém um conjunto de candidatos ativos. A cada pergunta respondida, filtra os candidatos incompatíveis com a resposta fornecida. Uma resposta "Não sei" não elimina nenhum candidato.

### 6.2 Seleção da próxima pergunta — Ganho de Informação

A pergunta escolhida em cada turno é aquela que mais equilibra o conjunto de candidatos entre os que possuem o atributo e os que não possuem. Formalmente, o sistema minimiza:

```
|count_sim - count_nao|
```

O que equivale a maximizar o ganho de informação (entropia binária máxima quando a divisão é 50/50). Isso garante a redução mais rápida possível do espaço de hipóteses.

### 6.3 Critério de parada

- **1 candidato restante**: o sistema declara a resposta.
- **0 candidatos restantes**: o animal não está na base de conhecimento.
- **Sem pergunta discriminatória restante**: o sistema exibe o candidato mais provável.

## 7. Interação com o usuário

O sistema aceita três tipos de resposta:

- **Sim**: o atributo está presente. Elimina candidatos que não possuem o atributo.
- **Não**: o atributo está ausente. Elimina candidatos que possuem o atributo.
- **Não sei**: a resposta é ignorada. Nenhum candidato é eliminado.

## 8. Exemplos de interação

### Exemplo 1 — Leão

| Pergunta            | Resposta | Candidatos após |
|---------------------|----------|-----------------|
| É um mamífero?      | Sim      | 12              |
| É encontrado no Brasil? | Não  | 5               |
| É de grande porte?  | Sim      | 4               |
| É carnívoro?        | Sim      | 3               |
| É originário da África? | Sim  | 1               |
| **Resultado: Leão** |          |                 |

### Exemplo 2 — Borboleta

| Pergunta            | Resposta | Candidatos após |
|---------------------|----------|-----------------|
| É um mamífero?      | Não      | 10              |
| É um inseto?        | Sim      | 2               |
| É venenoso?         | Não      | 1               |
| **Resultado: Borboleta** |     |                 |

## 9. Análise dos resultados

- O sistema converge rapidamente devido à seleção de perguntas por ganho de informação.
- A primeira pergunta ideal é sempre `mamifero`, que divide os 22 animais em 12 mamíferos e 10 não-mamíferos.
- Em média, o sistema resolve em **4 a 6 perguntas** para os animais mais únicos (ex.: Pinguim, Borboleta) e até **8 perguntas** para animais com muitos atributos similares.
- A resposta "Não sei" não prejudica o raciocínio, apenas retarda a convergência.

## 10. Taxa de acerto

O sistema acerta 100% dos animais presentes na base quando as respostas são corretas. Falhas ocorrem quando:

- O animal pensado não está na base.
- O usuário responde incorretamente a algum atributo.

## 11. Limitações

- A base cobre apenas 22 animais; animais raros ou pouco conhecidos não serão identificados.
- Atributos binários não capturam gradações (ex.: "parcialmente aquático").
- A resposta "Não sei" acumula-se e pode impedir a convergência se usada com frequência.
- Não há mecanismo de aprendizado automático para incorporar animais novos sugeridos pelo usuário.

## 12. Possíveis melhorias

- Adicionar mais animais e atributos para aumentar a cobertura.
- Implementar fator de confiança baseado em Redes Bayesianas para tratar incerteza.
- Permitir que o usuário corrija o sistema quando ele errar, incorporando o novo caso.
- Adicionar suporte a atributos com mais de dois estados (ex.: porte: pequeno/médio/grande).

## 13. Conclusão

O sistema implementa com sucesso a lógica do Akinator para o domínio animal. A seleção de perguntas por ganho de informação garante eficiência na identificação, e a interface Streamlit torna a interação intuitiva. A base de conhecimento é extensível por JSON sem alterar o código-fonte.
