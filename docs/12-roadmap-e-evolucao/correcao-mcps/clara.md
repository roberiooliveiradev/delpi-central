# CLARA — Inventário preliminar da ficha técnica

**Data:** 2026-11-06  
**Estado:** TO_INVENTORY — revisão iniciada, sem mudança no runtime.

## PROVEN no MCP
- Nome: **CLARA — Especialista em Controladoria & Finanças**.
- Apresentação: auxilia a compreender números, acompanhar fechamento mensal, investigar divergências e encontrar evidências para decisões.
- Identidade narrativa publicada em `get_context(topic=persona)`, `agent_directives.character`; ainda não foi demonstrada expansão de todas as letras do acrônimo.
- Ferramentas MCP expostas: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`.
- Catálogo `clara-semantic-v1`: 42 ações read, 2 analyze, 3 knowledge, 48 operações governadas (não inferir que todas sejam write autorizadas para o usuário).
- Corpus de conhecimento: 2203 itens, 88 fontes, versão publicada em 2026-11-03 (metadados do catálogo; não prova conteúdo de identidade).

## Questões a investigar
| ID | Questão | Status |
|---|---|---|
| CLARA-01 | Qual é o significado/acróstico institucional do nome CLARA? | TO_INVENTORY; não inventar |
| CLARA-02 | Em qual fonte canônica mora a identidade e como consultá-la com latência/escopo mínimos? | TO_INVENTORY |
| CLARA-03 | As descrições das tools, políticas de execução e catálogo coincidem com runtime? | TO_INVENTORY |
| CLARA-04 | O GPT apresenta missão, capabilities, ferramentas e limites fielmente? | TEST_NOT_RUN |
| CLARA-05 | Ficha no compartilhamento Github é consumida por quais superfícies? | TO_INVENTORY |

## Aceite TARGET
Significado oficial aprovado, apresentação correta, distinção entre conhecimento e capability, tools por catálogo, AuthZ owner, respostas negativas honestas, testes de regressão. Nenhuma mudança de código/Builder até inventário de owner→source→consumers→contrato→runtime.
