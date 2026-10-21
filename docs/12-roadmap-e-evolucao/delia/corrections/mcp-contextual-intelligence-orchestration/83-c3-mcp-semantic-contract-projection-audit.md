# 83 — Auditoria da Projeção Semântica dos Contratos MCP

**Task:** `DELIA-C3-MCP-SEMANTIC-CONTRACT-PROJECTION-AUDIT-01`
**Tipo:** auditoria arquitetural e funcional baseada em evidências (READ-only).
**Base:** `origin/main` `6538e04265…` (inclui `34a75d12a7` + revisões `2ed55ba47a`, `7b08e97e37`).
**Estado preservado:** `CRI_DEV_ENABLED=YES_PERSISTENT`, `CRI_PRODUCTION_ON=NOT_AUTHORIZED`, `SELECTION_ONLY=FROZEN`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`. Nenhuma alteração de runtime, nenhum código tocado.

## 1. Resumo executivo

A hipótese de perda de informação na projeção é **parcialmente confirmada e precisamente localizada**:

- `tools/list` é projetado **sem perda material** até `ProviderCapability` — exceto `title` e `annotations`, descarte intencional documentado.
- O modelo recebe o `input_schema` **completo** no estágio de argumentos — não é o schema que falta.
- O que nunca chega ao caminho READ: a saída de **DISCOVERY do próprio owner** (`get_catalog` → `capability_surface.entities[].filterable_fields`, `server_owned_fields`, VISTA `sortable_fields`). O gatilho do passo DISCOVERY é *vocabulário opaco no schema* (`_requires_owner_vocabulary`), não "owner publica contrato de entidade". `record_read` é totalmente tipado → `get_catalog` nunca é invocado → a admissibilidade por entidade (`date_field` só em `instance`/`revision`) nunca é consultada.
- Dois fatos simplesmente **não existem** em nenhum contrato owner publicado: (a) semântica campo→evento (`updated_at` = modificação); (b) contrato de ordenação server-side ("resultados ordenados por X"). Isso é lacuna do **owner**, não da projeção — e é a fronteira exata que bloqueia a prova de extremo global e a redação "alterado".

## 2. Inventário dos contratos (live, autenticado, READ-only)

`tools/list` + `tools/call` via `McpSpecialistAdapter` real com credencial delegada (RFC 8693 exchange, audiências canônicas). Nenhum dado sensível, nenhum ACT.

### TÉO (`transformometro-api`) — 23 tools

`record_read` (READ): `input_schema` plano com 20 propriedades; `date_field`/`date_from`/`date_to`/`page`/`page_size`/`q` são `anyOf[string|null]` **sem restrição por entidade** e **sem descriptions** (títulos pydantic gerados). `entity` é um enum fechado de 20 valores. A description menciona em prosa que `date_field/date_from/date_to` aplicam a "instances/revisions" — único sinal, não verificável deterministicamente.

`get_catalog` (DISCOVERY) → `data.capability_surface.entities[]`:

| entidade | `filterable_fields` | `server_owned_fields` |
|---|---|---|
| `process` | `familia_processo, filial_id, has_improvement, page, page_size, q, setor_id, status` — **sem `date_field`** | `created_at, deletado, processo_id, updated_at` |
| `instance` | `date_field, date_from, date_to, fase_melhoria, …` | `created_at, deletado, instancia_id, updated_at` |
| `revision` | `cenario_tipo, date_field, date_from, date_to, instance_id, parent_id, revisao_ativa` | `created_at, deletado, revisao_id, updated_at` |

`capability_surface` também carrega `workflows`, `analyses`, `agent_directives` (postura operacional live), `rules`, `mcp_only_capabilities`, `exposure_classification` e **`delia_projection_hint`: `{status: "PLANNED", consume: "capability_surface entities/workflows/analyses"}`** — o próprio owner declara que o consumo dessa superfície pela DÉLIA é trabalho planejado, não corrente.

`registration_guide.entity_schemas` = schema **write-side** (required/optional/enums/defaults/notes para criar/alterar) — não semântica de leitura.

Busca textual exaustiva no catálogo (598 KB): `updated_at` aparece **apenas** como nome em `server_owned_fields`. Nenhuma declaração de "ordenado por", `sortable_fields`, ou semântica de evento. **O contrato de ordenação e a semântica de campo não existem na superfície TÉO.**

### VISTA (`tv-dashboard-api`) — 12 tools

`get_catalog` → `capabilities`, `operations` (write ops), `operationSchemas`, `displayFormatCatalog`, `allowedOps`, `sideEffectHintCatalog`, `capability_surface.entities[]` com shape **mais rico** que TÉO: `filterable_fields`, **`sortable_fields`**, `server_owned_fields`, `required_permission_metadata`, `read_back_policy`. `playlist.sortable_fields = []` — a chave existe mas está vazia. `agent_directives`, `designIntelligence`, `expressions` presentes. Sem declaração temporal/ordenação populada.

### DAVI (`api-delpi/mcp`) — 2 tools

`discover_delpi_information` (DISCOVERY) retorna candidatos tipados: `description`, `argument_schema` (JSON Schema completo — types, enums, patterns, defaults, `additionalProperties: false`), `semantic_hints` (`entity`, `shape` ex. `paged_list`, `tags`), `pagination_hints` (`supports_page`, `supports_page_size`), `candidate_token`. `capability_surface.agent_directives` (postura READ governada) no envelope. Consulta "último processo alterado" → `candidate_count=0`, `eligible_action_count=95` — discovery miss não é prova de ausência (preservado).

## 3. Caminho real de projeção (HEAD `6538e04265`)

```text
tools/list JSON {name,title,description,inputSchema,annotations,_meta.delpi/toolClass}
 → RemoteToolDescriptor               [mcp/adapter.py:list_remote_tools — PRESERVA TUDO]
 → SpecialistCapabilityDescriptor     [interop: DROPS title, annotations]
 → ProviderCapability                  [mcp_provider.py:102 — {remote_name, owner, operation_class,
                                        description, input_schema, binding}]
 → contexto do modelo:
     group-select: {capability_id, remote_name, operation_class, description ≤240→32c}
     goal+capability (_capability_payload): {remote_name, description ≤240→0c,
                   operation_class, argument_keys (só nomes), required, role}
     arguments (_build_arguments): {capability, description ≤240c,
                   input_schema COMPLETO, owner_vocabulary (só envelope opaco),
                   business_subject}
 → validate_arguments (argument_validation.py): JSON Schema plano — enum/anyOf/
   required/additionalProperties; ORCHESTRATED_FIELDS negados; sem admissibilidade
   por entidade
 → invoke → SpecialistOutcome {content_text, structured, is_error, is_complete}
 → extract_pagination_envelope {items,page,page_size,has_more,total_count}
 → EvidenceFacts {records, has_business_evidence, explicit_empty, is_complete,
                  coverage_complete, total_count}
 → assess_outcome + verified_ordering_event(facts, requirements,
                  descriptor.description)
```

### O passo DISCOVERY — condição exata

`orchestration.py:5132-5137`: `discovery` só é agendado quando `_requires_owner_vocabulary(descriptor)` — i.e., o schema contém envelope opaco (`object` sem `properties` / `array` sem `items` tipado, `_is_open_vocabulary:872`). `record_read` é 100% tipado → condição falsa → **nenhuma chamada a `get_catalog` em turnos READ TÉO/VISTA**. O catálogo só entra quando (a) o modelo seleciona o próprio `get_catalog` para consulta de cobertura, ou (b) no fluxo PREPARE/ACT onde `changes` é envelope opaco → `_extract_owner_entity_schemas` + `_argument_completeness_gaps` (`:1897-1987`, consumido em `:5632`, `:5714`) validam o payload interno contra `entity_schemas` do owner — consumo write-side existente e bounded.

DAVI é o único path onde DISCOVERY alimenta argumentos: `owner_vocabulary` = projeção bounded breadth-first do `structured` do discovery (`_bound_owner_evidence:1636`) — `argument_schema`, `semantic_hints`, `pagination_hints` do candidato chegam ao modelo dessa forma.

## 4. Matriz origem → destino

| Informação | MCP publica | DÉLIA recebe | LLM vê | Runtime verifica | Classificação |
|---|---|---|---|---|---|
| nome da capability | sim (`name`) | sim | sim (`remote_name`) | sim | PRESERVED |
| descrição da capability | sim | sim | sim (≤240c, pode encolher a 0c sob budget) | sim (alvo do quote em `verified_ordering_event`, texto integral) | PRESERVED (truncamento bounded intencional) |
| `inputSchema` (tipos/enums) | sim | sim | **goal: só nomes+required; arguments: completo** | sim (`validate_arguments`) | PRESERVED |
| `title`, `annotations` | sim | recebe (adapter) | não | não | DROPPED — projeção bounded intencional (`delpi/toolClass` cobre a classificação) |
| filtros por entidade (`filterable_fields`) | **sim (capability_surface.entities, TÉO+VISTA)** | **não no path READ** | não | não | **DROPPED — PROJECTION_GAP real** |
| semântica campo→evento | **não publicado por nenhum owner** | — | — | — | **NOT_EXPOSED — lacuna owner** |
| ordenação server-side | não (`sortable_fields` existe vazio em VISTA; ausente em TÉO) | — | — | — | **NOT_EXPOSED — lacuna owner** |
| paginação (has_more/total/page) | sim (envelope de resposta; `pagination_hints` DAVI) | sim | schema tem page/page_size | sim (`extract_pagination_envelope`, `coverage_complete`) | PRESERVED |
| cobertura | sim (`has_more`, `total_count`) | sim | não | sim (conservador: `coverage_complete=None→unproven`) | PRESERVED |
| proveniência (owner/classe) | sim (`delpi/toolClass`, owner_ref) | sim | sim (`operation_class`, `role`) | sim (class gate) | PRESERVED |
| `agent_directives` (postura) | sim | só via `owner_vocabulary` no path DAVI | parcial, bounded | não (é postura, não autoridade — correto não verificar) | NOT_CONSUMED nos paths TÉO/VISTA — bounded, não autoridade |
| candidatos DAVI (`argument_schema`, `semantic_hints`, `pagination_hints`) | sim | sim (`owner_vocabulary` + `discovery_structured`) | sim (bounded) | sim (schema do candidato revalida) | PRESERVED (único path com contrato de catálogo no modelo) |

## 5. Avaliação dos argumentos — casos obrigatórios

### Caso A — `date_field` em `entity=process`

- **Schema publicado:** `date_field` é propriedade plana `anyOf[string|null]`, sem vínculo a `entity`.
- **Informação visível ao modelo:** o schema completo (admissibilidade plana) + description com pista em prosa ("instances/revisions").
- **Validação DÉLIA:** `validate_arguments` aprova — o campo é declarado e a instância é válida.
- **Rejeição do owner:** o filtro por entidade vive em `capability_surface.entities[process].filterable_fields` — publicado, **nunca consultado** no path READ porque o passo DISCOVERY exige envelope opaco.
- **Causa raiz:** PROJECTION_GAP — a admissibilidade por entidade existe numa superfície owner tipada e legítima, mas o canal de consumo (passo DISCOVERY) tem gatilho estrutural que `record_read` não satisfaz. O owner falha fechado corretamente; o custo é um turno desperdiçado e `NON_GROUNDED` honesto.
- **Não é defeito de segurança:** o owner é o validador final e rejeitou; o gap é de qualidade/eficiência da proposta.

### Caso B — superlativo com `page_size=1`

- O modelo escolhe `page_size` sem nenhum contrato que declare ordenação server-side — `record_read` não anuncia "resultados ordenados por X".
- `_temporal_proofs` exige ≥2 registros com o mesmo campo temporal monotônico; `single_complete` exige `coverage_complete=True`. Com `page_size=1` + `has_more=True` → `ordering_unproven`/`coverage_unproven` → insuficiência honesta.
- **Gap composto:** (a) nem o modelo nem o runtime têm um contrato de ordenação para invocar corretamente; (b) mesmo com N registros, extremo *global* exige ordenação-declarada + cobertura — a lógica atual está correta em hesitar. Falta ao owner publicar `sortable_fields`/ordenação padrão e ao runtime poder verificá-la.

## 6. Verificação semântica — `verified_ordering_event`

Revisão `2ed55ba47a` confirmada por inspeção do código (`outcome_assessment.py:167-200`): o verificador prova **proveniência textual + vínculo de campo** (quote verbatim ∈ description e campo proposto = campo que prova a ordenação), **não implicação semântica**. Uma descrição que mencione `updated_at` sem atribuir-lhe evento de modificação — ou que o negue — satisfaz o check se o modelo citá-la com `event=modification`. O vocabulário limitado contém o dano, mas a prova de significado exige **declaração tipada do owner** (ex.: `field_semantics`/`sortable_fields` populados ou seção tipada em `capability_surface`), verificada deterministicamente — a recomendação da revisão independente é correta e este audit confirma a ausência do artefato.

Risco secundário medido: sob compactação de budget (`description→24→0c`), o modelo não pode produzir quote verbatim → abstém-se — fail-safe, mas cobre o caminho positivo apenas com folga de contexto.

## 7. Respostas objetivas (critério §12)

1. **Os MCPs publicam o necessário?** Parcialmente: admissibilidade por entidade sim (`filterable_fields`); semântica campo→evento e ordenação server-side **não**.
2. **O que a DÉLIA consome?** Todo `tools/list` (menos title/annotations); catálogo só no path envelope-opaco (DAVI) e no path write (entity_schemas); nada do `capability_surface` no path READ TÉO/VISTA.
3. **O que se perde?** `filterable_fields`/`sortable_fields`/`server_owned_fields` (existe, não consumido); `title`/`annotations` (intencional); `agent_directives` nos paths não-DAVI (bounded, postura — não autoridade).
4. **Intencional ou defeito?** Perda de `filterable_fields` = **gap de projeção** (gatilho de DISCOVERY não cobre o caso); demais = projeção bounded intencional ou lacuna owner real.
5. **Contexto LLM suficiente?** Para argumentos planos, sim; para admissibilidade por entidade e semântica de campo, não — por falta de dado na janela, não por truncamento.
6. **Runtime valida contra autoridade?** Schema plano sim; admissibilidade por entidade não (sem fonte carregada); prova de evento = vínculo textual, não implicação.
7. **O que corrigir na DÉLIA?** Somente *consumo*: canal para o `filterable_fields` por entidade chegar à proposta/validação de argumentos READ — decisão de canal pendente (ver §8).
8. **Lacuna do owner?** Sim, duas: (a) declaração tipada campo→evento; (b) ordenação server-side/cobertura (`sortable_fields` populado ou contrato equivalente). Ambas evolução de contrato do owner — não improvisar na DÉLIA.
9. **Menor pacote justificável:** owner publica (a)+(b) na `capability_surface` existente → DÉLIA consome via projeção bounded existente (mesmo padrão `_bound_owner_evidence`/`entity_schemas`). Nenhuma infra nova, nenhum registry, nenhum estágio de modelo.

## 8. Equivalentes existentes e reuse gate

| Lacuna | Equivalente existente | REUSE_DECISION |
|---|---|---|
| admissibilidade por entidade | `capability_surface.entities[].filterable_fields` (publicado TÉO+VISTA); consumidor bounded `_extract_owner_entity_schemas`/`_bound_owner_evidence`; gatilho `_requires_owner_vocabulary` | REUSE — estender o gatilho ou projetar subset bounded; canal é a decisão pendente: (a) invocar catálogo no path READ tem custo de latência/orçamento; (b) projetar subset em `ProviderCapability` exige evolução do contrato `ProviderCapability`; (c) owner move a restrição para o `inputSchema` (anyOf por entidade) — zero custo de runtime para DÉLIA |
| campo→evento | `server_owned_fields` (só nomes); `sortable_fields` (vazio); nenhum artefato tipado | TO_DECIDE_AFTER_OWNER_CONTRACT — sem artefato owner não há o que reutilizar |
| ordenação/cobertura | `sortable_fields` (VISTA, vazio); `pagination_hints` DAVI; `has_more`/`total_count` no envelope | EXTEND owner-side; consumo DÉLIA via `EvidenceFacts` já existe |
| verificação de evento | `verified_ordering_event` + `ProviderCapability.description` | EXTEND quando owner publicar declaração tipada — o quote-substring permanece como prova de proveniência, não de significado |

## 9. Recomendação

`ACCEPT_WITH_RESIDUAL` — auditoria completa, achados verificados em live + código, sem implementação nesta tarefa.

**Itens que devem permanecer como estão:** projeção `ProviderCapability` bounded; descarte de `title`/`annotations`; gatilho `_requires_owner_vocabulary` como proteção de budget; `validate_arguments` plano + owner como validador final; hesitação conservadora de cobertura.

**Decisão de arquitetura requerida (não implementar sem escopo):** canal de consumo do `filterable_fields` por entidade no path READ — opção (a) DISCOVERY extra no READ (custo: chamada+latência), opção (b) evoluir `ProviderCapability` com subset bounded da superfície (custo: contrato interno), opção (c) owner expressa a restrição no `inputSchema` (custo: owner-side, zero latência para DÉLIA). Preferência técnica: **(c) primeiro, (b) como complemento se o catálogo virar fonte de mais de um consumo** — e sempre REUSE das superfícies bounded existentes.

**Lacunas owner (separadas, coordenação):** declaração tipada campo→evento; ordenação server-side. Sem elas, "último alterado" permanece honestamente hedge — comportamento correto, não defeito.

```text
AUDIT_VERDICT=ACCEPT_WITH_RESIDUAL
PROJECTION_HYPOTHESIS=CONFIRMED_SCOPED (filterable_fields only)
CONTRACT_GAPS=field_event_semantics + server_ordering (owner-side)
PROJECTION_GAPS=entity_filterable_fields_not_consumed_on_read
INTENTIONAL_FILTERING=title, annotations, directive posture outside discovery path
MINIMAL_PACKAGE=owner typed declarations + bounded consumer reuse
RUNTIME_CODE_CHANGED=NO
I04_ACCEPTED=NO
C3_EXECUTED=NO
```

**Lineage note:** authored against `origin/main` `6538e04265…`; this document's own commit SHA is recorded in the ledger, never inside the file.
