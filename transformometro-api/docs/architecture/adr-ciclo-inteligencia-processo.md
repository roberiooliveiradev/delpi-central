# ADR — Ciclo de inteligência e melhoria de processo

**Status:** TARGET documentado (2026-09-18). **Não implementado.**  
**Documento mestre:** [`CICLO-INTELIGENCIA-DE-PROCESSO.md`](../../../docs/12-roadmap-e-evolucao/transformometro-app/CICLO-INTELIGENCIA-DE-PROCESSO.md)

Documentação não prova runtime. Nenhuma capability abaixo é PROVEN só por este ADR.

## Contexto

O Transformômetro já persiste processo-mestre, instância, revisão, medição, diagrama `flowchart_v1`, árvore `decomposition_tree_v1`, matriz impacto×esforço, evidência, ata e timeline. O TÉO já expõe métodos (SIPOC, Lean, Ishikawa, 5 Porquês, CTP, TDR, KPI, SWOT, AS-IS, TO-BE) como **guia READ-only**, não como entidades.

A lacuna de produto está entre mapeamento e melhoria: resultados de negócio desses métodos não têm destino canônico persistido.

## Decisão

1. **Método ≠ entidade.** SIPOC, Lean, Ishikawa, 5 Porquês, CTP, TDR, KPI e SWOT não viram tabela, repositório nem tool só porque existem no guia.
2. **Persistir o resultado de negócio**, com estado epistemológico (`OBSERVED/INFORMED`, `CALCULATED`, `INFERRED`, `PROPOSED`, `UNKNOWN`). `INFERRED` não é fato. `PROPOSED` não é salvo/ativo. `TO-BE` não é estado de produção.
3. **Reusar o que já é fonte de verdade** antes de criar agregado:
   - AS-IS calculável → revisão baseline + medição + overlays;
   - TO-BE → revisão cenário + overlays + investimento, até ativação governada e read-back;
   - priorização de revisão → `impact_effort_matrix` (não cobre sozinha criticidade do problema versus implementabilidade da solução);
   - escopo organizacional (unidades/departamentos) → `ProcessoEscopoRepository`. **Não** é SIPOC.
4. **Escopo/interfaces (SIPOC)** é capability TARGET distinta do escopo organizacional. Preferência: artefato estruturado ou projeção, não `SipocEntity`.
5. **Achados e hipóteses causais** não entram como colunas do processo-mestre nem como nós obrigatórios da árvore. Se a fase 2 provar a lacuna, o agregado é do diagnóstico, ligado por referência ao processo/instância/revisão/nó.
6. **Arquitetura corporativa** (cadeia de valor → macroprocesso → processo-chave) não reutiliza a árvore de um processo individual. A árvore atual usa `processo_chave` como nível **dentro** do mestre.
7. **Exposição TÉO:** capability parity ≠ route parity ≠ tool count. CRUD novo, se um dia existir, prefere `search_records` / `get_record` / prepare-create-update-delete e as Actions genéricas. Não criar `get_sipoc`, `create_finding`, `gpt_create_kpi` sem operação de domínio que não caiba no contrato genérico.
8. MCP e GPT Actions permanecem adapters. GPT Actions lifecycle atual: `GOVERNED_PREPARE_COMMIT_V2`. MCP: `CAPABILITY_GOVERNED_V2`.

## Consequências

- Implementação fica **não autorizada** por este ADR.
- Cada fase do documento mestre precisa repetir Abstraction Gate, AuthZ backend-first e migrations imutáveis.
- Nome de campo novo (`semantic_ref`, `decomposition_node_id`, etc.) não está decidido. O vínculo atual documentado é `flowchart_v1.nodes[].meta.decomposition_id` (opcional).

## Não decidido (TO_INVENTORY)

- Se o enriquecimento semântico da atividade vive em metadata do `decomposition_tree_v1` ou em agregado complementar.
- Se definição de KPI é conceito novo ou evolução de `measurement` (hoje: valor da revisão, não definição).
- Se plano de ação existe em algum artefato já persistido. Busca no bounded context não achou entidade canônica. Planos de ação de Qualidade (`api-delpi`) são outro contexto e não são owner.
