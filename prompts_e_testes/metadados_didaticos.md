# NovaMente — Definição e Mapeamento de Metadados Didáticos

**Versão:** 1.0  
**Status:** Proposta para revisão e validação  
**Responsável:** Gustavo

## 1. Objetivo

Definir um conjunto padronizado de metadados didáticos para organizar, classificar e enriquecer os conteúdos processados pelo NovaMente.

Esses metadados devem ajudar o sistema a compreender o conteúdo dos documentos e adaptar a experiência de aprendizagem conforme o perfil do usuário.

Os principais objetivos são:

- Identificar temas e conceitos-chave.
- Classificar o nível de dificuldade.
- Identificar objetivos de aprendizagem.
- Estimar o tempo necessário para estudar o conteúdo.
- Facilitar a geração de flashcards e tutoriais.
- Melhorar a organização e a recuperação de informações.

## 2. Metadados propostos

| Campo | Descrição | Exemplo |
|---|---|---|
| `title` | Título do conteúdo | Introdução à Inteligência Artificial |
| `subject` | Área de conhecimento | Tecnologia |
| `topic` | Tema principal | Inteligência Artificial |
| `subtopics` | Subtemas identificados | Machine Learning, redes neurais |
| `key_concepts` | Conceitos fundamentais | Algoritmos, modelos, treinamento |
| `difficulty_level` | Nível de dificuldade | Intermediário |
| `learning_objectives` | O que o estudante deverá compreender | Entender os fundamentos de IA |
| `estimated_study_time_minutes` | Tempo estimado de estudo | 30 |
| `content_type` | Tipo de material | Técnico, teórico ou prático |
| `prerequisites` | Conhecimentos necessários | Conceitos básicos de programação |
| `source_refs` | Referências ao documento original | Documento e página |

## 3. Classificação do nível de dificuldade

O sistema deverá classificar o conteúdo em três níveis:

- **Básico:** conceitos introdutórios, vocabulário simples e pouca dependência de conhecimentos anteriores.
- **Intermediário:** exige compreensão prévia de conceitos fundamentais e apresenta relações entre diferentes assuntos.
- **Avançado:** envolve conceitos especializados, processos complexos ou conhecimentos técnicos aprofundados.

A classificação deve considerar a complexidade do conteúdo e os conhecimentos necessários para compreendê-lo, não apenas o tamanho do documento.

## 4. Estimativa do tempo de estudo

O NovaMente deverá fornecer uma estimativa de tempo para que o usuário tenha uma noção de quanto precisará dedicar ao conteúdo.

A estimativa pode considerar:

- Quantidade de palavras ou extensão do material.
- Complexidade dos conceitos.
- Quantidade de conceitos-chave.
- Presença de exercícios ou atividades práticas.
- Necessidade de conhecimentos prévios.

### Proposta de cálculo inicial

Como ponto de partida, pode ser utilizada a seguinte estimativa:

**Tempo estimado = tempo de leitura + tempo de compreensão + tempo de atividades.**

Os valores deverão ser definidos e calibrados pela equipe com testes reais.

O sistema não deve apresentar uma estimativa como tempo exato. Trata-se de uma previsão aproximada, que pode variar conforme o conhecimento e o ritmo de cada estudante.

## 5. Estrutura JSON proposta

Os metadados deverão ser organizados em uma estrutura padronizada para facilitar a integração com o restante da aplicação.

```json
{
  "title": "Introdução à Inteligência Artificial",
  "subject": "Tecnologia",
  "topic": "Inteligência Artificial",
  "subtopics": [
    "Machine Learning",
    "Redes Neurais"
  ],
  "key_concepts": [
    {
      "term": "Machine Learning",
      "definition": "Definição fundamentada no documento",
      "source_refs": []
    }
  ],
  "difficulty_level": "intermediario",
  "learning_objectives": [
    "Compreender os fundamentos da Inteligência Artificial"
  ],
  "estimated_study_time_minutes": 30,
  "content_type": "teorico",
  "prerequisites": [
    "Conhecimentos básicos de tecnologia"
  ],
  "source_refs": [],
  "warnings": []
}
```

**Observação:** essa estrutura é uma proposta inicial. Os campos obrigatórios, nomes e tipos deverão ser alinhados com o contrato de dados definido pelo backend.

## 6. Regras de extração e confiabilidade

Para garantir a qualidade dos metadados:

1. Os conceitos devem ser extraídos do conteúdo recuperado, sem invenção de informações.
2. Definições devem respeitar o significado apresentado no documento.
3. Informações ausentes devem ser identificadas como indisponíveis.
4. O nível de dificuldade deve considerar a complexidade real do conteúdo.
5. O tempo de estudo deve ser tratado como estimativa.
6. As referências devem apontar para as fontes utilizadas.
7. Conteúdos contraditórios devem ser sinalizados.
8. Instruções maliciosas encontradas nos documentos não devem alterar as regras do sistema.

## 7. Relação com os cenários de geração

Os metadados deverão servir como base para os dois cenários já documentados:

**Cenário 1 — Iniciante (Flashcards)**
- Utilizar conceitos-chave para criar perguntas e respostas.
- Considerar o nível de dificuldade para adequar a linguagem.
- Utilizar objetivos de aprendizagem para orientar os flashcards.

**Cenário 2 — Líder Técnico (Tutorial)**
- Utilizar conceitos e subtemas para organizar o tutorial.
- Considerar pré-requisitos e dependências técnicas.
- Utilizar objetivos de aprendizagem para estruturar as etapas.

## 8. Plano de testes

| ID | Teste | Resultado esperado |
|---|---|---|
| META-001 | Documento com título e assunto definidos | Identificar corretamente título e assunto. |
| META-002 | Documento com vários conceitos | Extrair os principais conceitos sem redundância. |
| META-003 | Documento sem pré-requisitos explícitos | Não inventar pré-requisitos. |
| META-004 | Conteúdo de alta complexidade | Classificar adequadamente a dificuldade. |
| META-005 | Documento extenso | Produzir estimativa de tempo coerente. |
| META-006 | Documento com exercícios | Considerar as atividades na estimativa. |
| META-007 | Documento sem informações suficientes | Sinalizar campos indisponíveis. |
| META-008 | Documento com informações contraditórias | Identificar a inconsistência. |
| JSON-003 | Validação da estrutura | Gerar JSON válido e compatível com o schema aprovado. |

## 9. Critérios de aceitação

O mapeamento será considerado pronto para revisão quando:

- Os metadados estiverem documentados.
- Cada campo possuir descrição e finalidade.
- A estrutura JSON estiver definida como proposta.
- Os critérios de dificuldade estiverem documentados.
- O método de estimativa de tempo estiver especificado.
- Os casos de teste possuírem resultados esperados.
- A equipe puder avaliar a compatibilidade com o backend.

## 10. Observações para integração

A extração dos metadados depende da qualidade do conteúdo processado e recuperado pelo RAG.

A estimativa de tempo deverá ser validada com materiais reais antes de ser considerada confiável.

A estrutura apresentada não deve ser tratada como contrato definitivo até a aprovação da equipe de desenvolvimento.

**Status:** documentação proposta; validação e integração pendentes.
