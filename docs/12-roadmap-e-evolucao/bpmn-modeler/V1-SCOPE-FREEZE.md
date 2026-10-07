# BPMN MODELER — V1 SCOPE FREEZE

> **Status:** FROZEN (set/2026)
> **Produto:** Meu Modelador de Processos / BPMN Modeler
> **Bounded context:** `bpmn-modeler/` (package `bpmn_modeler`)
> **Owner:** BPMN Modeler (autoridade do modelo BPMN canônico)
> **Natureza deste documento:** specification freeze de produto (WHAT). Decisões de implementação (HOW) pertencem aos Prompts 2–7 e estão mapeadas na seção 19.
> **Base aprovada:** commits `318ac9cb82` (domain foundation) e `5c8e8b6a66` (application validation contract).
> **AMENDMENT G0 (out/2026):** este arquivo é o **specification freeze histórico** da V1. Onde uma decisão foi substituída após implementação, o texto original foi preservado e marcado `SUPERSEDED (G0)`. Estado vigente e evidências: [`CURRENT-STATE.md`](CURRENT-STATE.md); divergências registradas: [`DOCUMENTATION-DRIFT-LEDGER.md`](DOCUMENTATION-DRIFT-LEDGER.md).

Vocabulário de decisão usado neste documento:

| Estado | Significado |
|---|---|
| `IN_V1` | Escopo decidido: entra na V1. |
| `OUT_OF_V1` | Decisão deliberada de não implementar na V1. |
| `FUTURE` | Pertence à evolução posterior da V1. |
| `DEPENDENT_ON_LATER_SPEC` | `IN_V1` quanto ao escopo; o contrato de implementação é fechado no prompt indicado. |

Para elementos BPMN, a granularidade de suporte usa:

| Estado | Significado |
|---|---|
| `CREATE_EDIT` | Criar, editar e remover via UI; sujeito a import/render/preserve/export completos. |
| `RENDER_PRESERVE_ONLY` | Reconhecido no import, renderizado e preservado no round-trip; não criável pela UI; edição limitada a propriedades genéricas quando aplicável. |
| `OUT_OF_V1` | Não precisa ser reconhecido; tratamento de elementos desconhecidos é definido no contrato de interoperabilidade (Prompt 3). |

---

## 1. Purpose

Responder de forma inequívoca: **o que precisa estar funcionando para afirmarmos que o BPMN Modeler V1 está pronto?**

Este documento fecha:

- o que entra na V1 (`IN_V1`);
- o que não entra na V1 (`OUT_OF_V1`);
- o que é evolução posterior (`FUTURE`);
- o que é escopo fechado com contrato de implementação pendente (`DEPENDENT_ON_LATER_SPEC`);
- a Definition of Done da V1.

Este documento **não** decide: schema de persistência, parser/validator concreto, biblioteca de editor, engine de auto-layout, códigos de permissão, endpoints OpenAPI. Essas decisões têm dono: Prompts 2–7 (seção 19).

## 2. Architectural Baseline

Decisões já congeladas — não se rediscutem:

| Decisão | Estado |
|---|---|
| Bounded context `bpmn-modeler/` (root sem sufixo `-api`; bounded context != HTTP adapter != deployment unit) | FROZEN |
| Ownership: BPMN Modeler é autoridade do modelo BPMN canônico; Keycloak = identidade/SSO; Core = RBAC/governança transversal; Transformômetro = autoridade de processos/melhorias/medições/custos | FROZEN |
| Nenhum compartilhamento de banco ou de entidades/repos/use cases com o Transformômetro | FROZEN |
| Fonte canônica: BPMN 2.0 XML (semântica) + BPMN-DI no mesmo artefato (geometria). SVG/PNG/PDF/previews/thumbnails/layouts temporários são derivados | FROZEN |
| Proibido criar modelo canônico paralelo: visual JSON, React Flow model, Mermaid, `flowchart_v1` | FROZEN — enforced por `bpmn-modeler/tests/test_architecture.py` |
| Domain foundation: `Model → WorkingCopy → CanonicalBpmnArtifact` (artefato opaco no domain; canonical != automaticamente válido) | FROZEN |
| Application validation contract: `BpmnArtifactValidationPort → ValidationReport` (`ValidationIssue`, `ValidationStage`, `ValidationSeverity`, `RuleSource`) | FROZEN |
| `ValidationReport` = evidência, não operation policy. Preservation risk != preservation proof | FROZEN |
| `flowchart_v1` permanece formato canônico **do Transformômetro** (ADR `transformometro-api/docs/architecture/adr-diagramas-processo.md`) — bounded context separado, sem autoridade compartilhada | FROZEN |

## 3. Product Definition

O BPMN Modeler V1 é um **modelador BPMN 2.0 profissional e governado**, standalone dentro da plataforma Minha DELPI:

- cria, edita, valida, versiona e exporta diagramas BPMN 2.0 com BPMN-DI;
- artefato único e canônico: arquivo `.bpmn` (XML semântico + DI);
- histórico governado por revisões imutáveis;
- save explícito com estados de concorrência.

O produto **não é**: engine de execução, simulador, ferramenta de workflow, BI, nem extensão embutida do Transformômetro.

## 4. V1 Users / Actors

Três atores funcionais. Esta distinção delimita comportamento; **não define códigos de permissão** (Prompt 6, com Core como owner de RBAC):

| Ator | Capacidades de uso |
|---|---|
| **Viewer** | listar/localizar modelos, abrir modelo e revisões em read-only, executar validação e visualizar issues, exportar `.bpmn`/SVG/PNG |
| **Editor** | tudo do Viewer + criar modelo, editar conteúdo e geometria, importar `.bpmn`, salvar, executar auto-layout |
| **Model Manager (Governed Maintainer)** | tudo do Editor + renomear, duplicar, arquivar/desarquivar, criar revisão (snapshot) e restaurar revisão |

Capacidades distinguíveis: **visualizar**, **editar**, **gerenciar modelo/revisão**. O mapeamento ator→permissão concreta é `DEPENDENT_ON_LATER_SPEC` → Prompt 6.

## 5. V1 User Journeys

| # | Jornada | V1 Status | Notas |
|---|---|---|---|
| A | Criar modelo: criar novo modelo BPMN → abrir no editor → modelar → salvar → reabrir | `IN_V1` | |
| B | Abrir modelo existente: listar/localizar → abrir → renderizar BPMN canônico → continuar edição quando autorizado | `IN_V1` | Autorização efetiva backend-first (Prompt 6) |
| C | Importar `.bpmn`: selecionar arquivo → intake/validation → visualizar problemas → abrir quando permitido → preservar conteúdo suportado | `IN_V1` | Parser/validator concreto: Prompt 3. Quais severidades bloqueiam a abertura: operation policy, Prompt 3 |
| D | Exportar `.bpmn`: exportar o artefato BPMN canônico (XML + DI) | `IN_V1` | |
| E | Salvar modelo: experiência completa `dirty → saving → saved`, com `error` e `conflict` explícitos | `IN_V1` | Contrato técnico: Prompts 2 e 7 |
| F | Visualizar sem editar: abrir modelo em modo read-only | `IN_V1` | Read-only é modo de sessão e também consequência de autorização |
| G | Revisões/histórico: working copy + revision snapshots imutáveis + histórico navegável + abrir revisão antiga read-only + identificar revisão atualmente selecionada | `IN_V1` | Schema, numeração e checksum: Prompt 2 |
| H | Restore: restaurar revisão antiga | `IN_V1` | Semântica fechada: restore **cria nova working copy/revisão a partir do conteúdo da revisão selecionada** — histórico é append-only, nunca reescrito. `view old revision != restore` |
| I | Duplicar modelo (duplicate / save as) | `IN_V1` | Cria novo modelo com novo id; conteúdo inicial = artefato canônico atual da origem |
| J | Arquivar modelo: `archive` e `unarchive` | `IN_V1` | `hard delete` é `OUT_OF_V1` (ver seção 17) |

## 6. BPMN Editing Profile

O produto não é um flowchart: a V1 suporta modelagem BPMN profissional ampla. Modelamos processos — **não há comportamento de engine**.

### 6.1 Activities

| Elemento | V1 Status |
|---|---|
| Task (genérica) | `CREATE_EDIT` |
| User Task | `CREATE_EDIT` |
| Service Task | `CREATE_EDIT` |
| Manual Task | `CREATE_EDIT` |
| Business Rule Task | `CREATE_EDIT` |
| Script Task | `CREATE_EDIT` |
| Send Task | `CREATE_EDIT` |
| Receive Task | `CREATE_EDIT` |
| Call Activity | `CREATE_EDIT` |
| SubProcess collapsed | `CREATE_EDIT` |
| SubProcess expanded | `CREATE_EDIT` |
| Ad-hoc SubProcess | `RENDER_PRESERVE_ONLY` (criação `FUTURE`) |
| Transaction | `RENDER_PRESERVE_ONLY` (criação `FUTURE`) |
| Event SubProcess | `RENDER_PRESERVE_ONLY` (criação `FUTURE`) |

### 6.2 Events

`CREATE_EDIT` = criável/editável via UI na posição indicada, com event definition correspondente. Demais definições na mesma posição = `RENDER_PRESERVE_ONLY` (criação `FUTURE`).

| Posição | `CREATE_EDIT` (definitions) | `RENDER_PRESERVE_ONLY` (definitions) |
|---|---|---|
| Start Event (top-level) | None, Message, Timer, Signal | Conditional, Multiple, Parallel Multiple |
| Start Event (em Event SubProcess) | — (Event SubProcess é preserve-only) | Error, Escalation, Compensation, Signal, Message, Timer, Conditional, Multiple |
| Intermediate Catch (fluxo) | Message, Timer, Signal, Link | Conditional, Multiple, Parallel Multiple |
| Boundary Event (interrupting e non-interrupting) | Message, Timer, Error, Signal, Escalation | Conditional, Compensation, Cancel, Multiple, Parallel Multiple |
| Intermediate Throw | None, Message, Signal, Escalation, Link | Compensation, Multiple |
| End Event | None, Message, Error, Signal, Escalation, Terminate | Compensation, Cancel, Multiple |

Estados `RENDER_PRESERVE_ONLY` exigem import + render + preservação em round-trip; prova de preservação é contrato do Prompt 3.

### 6.3 Gateways

| Gateway | IMPORT/RENDER/PRESERVE | CREATE_EDIT |
|---|---|---|
| Exclusive | sim | `IN_V1` |
| Parallel | sim | `IN_V1` |
| Inclusive | sim | `IN_V1` |
| Event-Based | sim | `IN_V1` |
| Complex | sim | `OUT_OF_V1` — `RENDER_PRESERVE_ONLY`, criação `FUTURE` |

As três capacidades (import/preserve, render, create/edit) não são colapsadas: Complex entra em import+render+preserve, não entra na paleta.

### 6.4 Connecting Objects

| Elemento | V1 Status |
|---|---|
| Sequence Flow | `CREATE_EDIT` |
| Message Flow | `CREATE_EDIT` |
| Association | `CREATE_EDIT` |
| Data Association | `CREATE_EDIT` |

### 6.5 Collaboration

| Elemento | V1 Status |
|---|---|
| Pool / Participant | `CREATE_EDIT` |
| Lane | `CREATE_EDIT` |
| Múltiplos Pools | `CREATE_EDIT` |
| Múltiplas Lanes | `CREATE_EDIT` |
| LaneSets aninhados (nested lanes) | `CREATE_EDIT` |
| Message Flow entre Pools | `CREATE_EDIT` |
| Black-box Pool (participant sem process) | `CREATE_EDIT` |

Pools/Lanes fazem parte da experiência profissional da V1.

### 6.6 Data / Artifacts

| Elemento | V1 Status |
|---|---|
| Data Object / Data Object Reference | `CREATE_EDIT` |
| Data Store Reference | `CREATE_EDIT` |
| Data Input | `RENDER_PRESERVE_ONLY` (criação `FUTURE`) |
| Data Output | `RENDER_PRESERVE_ONLY` (criação `FUTURE`) |
| Text Annotation | `CREATE_EDIT` |
| Group | `CREATE_EDIT` |

## 7. Import / Render / Preserve / Create / Edit Matrix

O perfil de import **não é** o perfil de edição. Capacidades são ortogonais:

| Construção | IMPORT | RENDER | PRESERVE | CREATE | EDIT |
|---|---|---|---|---|---|
| Elementos `CREATE_EDIT` (seção 6) | sim | sim | sim | sim | sim |
| Elementos `RENDER_PRESERVE_ONLY` (seção 6) | sim | sim | sim | não | parcial: propriedades genéricas (ex.: documentação) quando aplicável; não altera tipo/estrutura |
| Construção BPMN válida desconhecida/fora do profile | `DEPENDENT_ON_LATER_SPEC` → Prompt 3 | render best-effort definido no Prompt 3 | preservar sempre que o parser conseguir carregar o artefato (contrato do Prompt 3) | não | não |
| Extension elements/attributes desconhecidos | reconhecer | n/a (não visuais) | preservar — requirement de interoperabilidade, Prompt 3 | não | não |
| Arquivo não-XML / XML malformado / XML não-BPMN | intake falho com estado distinto (seção 11.2) | n/a | n/a | n/a | n/a |

**Regra fechada:** construção desconhecida ou não editável **não é automaticamente rejeitada**. O default de interoperabilidade é `recognized → preserved → rendered (best-effort) → not directly editable`, desde que o round-trip prove preservação. Os limites exatos (o que bloqueia import, abertura, save ou export) são **operation policy** → Prompt 3.

## 8. Editor Capability Matrix

Decisão de capability, não de implementação React nem de biblioteca (Prompt 4):

| Capability | V1 Status |
|---|---|
| Canvas | `IN_V1` |
| Palette (criação de elementos do profile `CREATE_EDIT`) | `IN_V1` |
| Context pad | `IN_V1` |
| Properties panel | `IN_V1` (escopo na seção 8.1) |
| Selection | `IN_V1` |
| Multi-selection | `IN_V1` |
| Drag/drop (palette → canvas; mover elementos) | `IN_V1` |
| Resize (shapes, pools, lanes onde semântico) | `IN_V1` |
| Connect | `IN_V1` |
| Delete | `IN_V1` |
| Copy / Paste / Cut | `IN_V1` |
| Undo / Redo | `IN_V1` |
| Keyboard shortcuts (conjunto núcleo: save, undo, redo, copy, cut, paste, delete, select all, zoom, fit; mapa exato → Prompt 4) | `IN_V1` |
| Pan | `IN_V1` |
| Zoom (in/out/reset) | `IN_V1` |
| Fit-to-screen | `IN_V1` |
| Search/find dentro do diagrama (por name/id → localizar, selecionar, destacar) | `IN_V1` |
| Busca na palette | `IN_V1` |
| Snap/grid (configuração fixa do produto) | `IN_V1` |
| Mini-map | `FUTURE` |
| Alignment/distribution (align, distribute) | `FUTURE` |
| Grid configurável pelo usuário | `FUTURE` |

### 8.1 Properties Panel — nível funcional da V1

| Propriedade | V1 Status |
|---|---|
| Element name (edição) | `IN_V1` |
| Element id (visualização read-only) | `IN_V1` |
| Element id (edição pelo usuário) | `OUT_OF_V1` — `FUTURE` (ids são referenciados por flows e DI) |
| Documentation | `IN_V1` |
| Condition expression em Sequence Flow | `IN_V1` |
| Default flow em Gateway | `IN_V1` |
| Event definition: seleção/troca de tipo dentro do perfil `CREATE_EDIT` | `IN_V1` |
| Event definition: campos da definição suportada (ex.: name/reference de message/error/signal/escalation; expressão de timer como texto) | `IN_V1` |

> **SUPERSEDED (G0):** `Element id (edição pelo usuário)` foi entregue — o entry `id`/`processId` do properties panel do vendor é realocado para o grupo "Configurações avançadas" e passa pelo command stack (undo/redo/read-back, refs atualizadas). `Model.id` da API permanece autoridade separada e imutável. Ver `CURRENT-STATE.md` §8 e `e2e/specs/bpmn-id-governance.spec.ts`.
| Participant ↔ Process linkage | `IN_V1` |
| Lane naming | `IN_V1` |
| Propriedades específicas dos elementos suportados (task type, collapsed/expanded de SubProcess, called element de Call Activity como referência textual) | `IN_V1` |
| Campos de binding de engine (listeners, delegates, async, retry, execução) | `OUT_OF_V1` |
| Edição de extension elements/attributes | `OUT_OF_V1` |
| Edição de ioSpecification / Data Input-Output | `OUT_OF_V1` |

## 9. Model Lifecycle

| Operação | V1 Status | Notas |
|---|---|---|
| create | `IN_V1` | |
| list/find | `IN_V1` | seção 14 |
| open (edit ou read-only) | `IN_V1` | |
| rename | `IN_V1` | ator: Model Manager |
| duplicate / save as | `IN_V1` | novo modelo, novo id |
| archive / unarchive | `IN_V1` | ator: Model Manager |
| hard delete | `OUT_OF_V1` | `FUTURE` sob política de governança; não assumir existência |
| export `.bpmn` | `IN_V1` | |
| import `.bpmn` | `IN_V1` | cria novo modelo a partir do intake |

## 10. Revision / History Scope

`IN_V1` — capability-level (schema, algoritmo de numeração e checksum: Prompt 2):

| Capability | V1 Status |
|---|---|
| Working copy (estado mutável corrente) | `IN_V1` — já existe no domain (`WorkingCopy`) |
| Revision = snapshot imutável | `IN_V1` |
| List revisions | `IN_V1` |
| Revision identifier visível | `IN_V1` |
| Creation timestamp | `IN_V1` |
| Author identity quando disponível | `IN_V1` |
| Open revision read-only | `IN_V1` |
| Compare metadata entre revisões (id, timestamp, autor) | `IN_V1` |
| Select revision / identificar revisão corrente selecionada | `IN_V1` |
| Create snapshot/revision explícito | `IN_V1` |
| Restore = nova revisão a partir de revisão antiga (append-only) | `IN_V1` |
| Diff visual/XML entre revisões | `FUTURE` |

## 11. Validation UX Scope

### 11.1 Capabilities

| Capability | V1 Status |
|---|---|
| Executar validação sob demanda (ação explícita) | `IN_V1` |
| Executar validação no intake de import | `IN_V1` |
| Executar validação no fluxo de save (se issues bloqueiam save = operation policy → Prompts 2/3) | `IN_V1` (capability) / `DEPENDENT_ON_LATER_SPEC` (policy) |
| Exibir lista de issues | `IN_V1` |
| Distinguir severity (`error`/`warning`/`info`) | `IN_V1` |
| Distinguir stages avaliados de não avaliados | `IN_V1` — espelha `ValidationReport.evaluated_stages`/`not_evaluated_stages` |
| Exibir stage e rule source por issue | `IN_V1` |
| Navegar issue → elemento no canvas quando `reference` resolve para elemento com DI | `IN_V1` |

Implementação do validator: Prompt 3. Apresentação exata do painel: Prompt 4.

### 11.2 Import failure states — a UX distingue obrigatoriamente

| Estado detectado no intake | UX da V1 |
|---|---|
| Arquivo não-XML | erro distinto, sem render |
| XML malformado | erro distinto com evidência de well-formedness |
| XML bem-formado mas não-BPMN | erro distinto (não é `definitions` BPMN 2.0) |
| BPMN reconhecido incompleto/parcial | estado distinto; issues reportados |
| BPMN com issues (errors vs warnings) | lista de issues com severity |
| BPMN sem DI | estado distinto — `DEPENDENT_ON_LATER_SPEC`: geração de DI/layout no intake é decidida nos Prompts 3/5 |
| BPMN com extensions desconhecidas | estado distinto de aviso; preservação exigida (seção 7) |

Quais desses estados bloqueiam quais operações (abrir, salvar, exportar) = **operation policy** → Prompt 3. O que está fechado aqui: a UX precisa representar cada estado de forma distinguível.

## 12. Auto-layout Scope

`IN_V1` — comando "Organizar diagrama" com o fluxo arquitetural fechado:

```text
CALCULATE → PREVIEW → ACCEPT / CANCEL → SAVE explícito
```

Regra fechada: `layout calculation != persisted geometry`. Nada é persistido sem save explícito. Algoritmo/biblioteca (ELK, yFiles, outro): `DEPENDENT_ON_LATER_SPEC` → Prompt 5.

> **SUPERSEDED (G0):** a V1 implementada usa **autosave do working copy** (`AutosaveController`, debounce + read-back verify). O gesto explícito obrigatório passa a ser **ACCEPT/CANCEL** do preview: ACCEPT → DIRTY → autosave pode persistir; CANCEL → zero write. `layout calculation != persisted geometry` permanece invariante — preview nunca escreve. Engine implementada: ELK em Web Worker (sem fallback main thread). Ver `CURRENT-STATE.md` §4/§7.

## 13. BPMN-DI Scope

BPMN-DI é a geometria canônica. `IN_V1`:

| Capability | V1 Status |
|---|---|
| Read DI | `IN_V1` |
| Render DI | `IN_V1` |
| Edit geometry (move/resize/re-route persistidos como DI) | `IN_V1` |
| Persist DI no mesmo artefato `.bpmn` | `IN_V1` |
| Export DI | `IN_V1` |
| Segunda fonte visual persistida | proibida — `OUT_OF_V1` permanente |

## 14. Model Library / Search Scope

| Capability | V1 Status |
|---|---|
| List models | `IN_V1` |
| Search por name/id | `IN_V1` |
| Sort (updated, created, name) — default: recentes primeiro | `IN_V1` |
| Pagination | `IN_V1` |
| Archive filter (ativos default; incluir/somente arquivados) | `IN_V1` |
| Colunas de metadata created/updated | `IN_V1` |
| "Recent models" como visão dedicada | `IN_V1` — realizado pelo sort default updated-desc; sem view separada |

Endpoints/contratos: Prompt 7.

### Model metadata visível ao usuário

| Campo | V1 Status |
|---|---|
| model id | `REQUIRED_V1` |
| display name | `REQUIRED_V1` |
| created at | `REQUIRED_V1` |
| updated at | `REQUIRED_V1` |
| revision indicator (revisão corrente/selecionada) | `REQUIRED_V1` |
| updated by / author | `REQUIRED_V1` quando identidade disponível |
| archive state | `REQUIRED_V1` |
| nomes exatos de campos/schema | `DEPENDENT_ON_LATER_SPEC` → Prompt 2 |

## 15. Accessibility / Device Scope

Accessibility — `IN_V1` (baseline, sem promessa de certificação WCAG específica):

- keyboard operability onde aplicável (navegação de UI, ações do conjunto de shortcuts da seção 8);
- focus visibility;
- accessible labels;
- contraste compatível com o padrão da plataforma;
- comunicação de status não exclusiva por cor (severity/estados de save com texto/ícone).

Devices — decisão fechada:

| Device | V1 Status |
|---|---|
| Desktop | `IN_V1` — target primário (desktop-first professional modeler, edição completa) |
| Tablet | `IN_V1` limitado a visualização read-only; edição `FUTURE` |
| Mobile | `OUT_OF_V1` — sem garantia de suporte |

## 16. Derived Outputs

Derivados nunca são canônicos (seção 2):

| Derivado | V1 Status |
|---|---|
| SVG export | `IN_V1` |
| PNG export | `IN_V1` |
| PDF export | `OUT_OF_V1` — `FUTURE` |
| Thumbnail na library | `FUTURE` |

## 17. Explicit Out-of-Scope

O executor final **não deve** implementar nada abaixo na V1:

| Item | Estado |
|---|---|
| Autosave (silencioso ou periódico) | `OUT_OF_V1` — V1 usa explicit canonical save; reintroduzir autosave exige decisão formal nova |
| Real-time collaborative editing (presence, live cursors, live merge) | `OUT_OF_V1` — concurrent update detection (jornada E) continua `IN_V1` e não é edição colaborativa |
| Comments, mentions | `OUT_OF_V1` — `FUTURE` |
| Review workflow / approval workflow | `OUT_OF_V1` — `FUTURE` |
| BPMN process execution engine / workflow execution | `OUT_OF_V1` — o produto é modelador, não engine |
| Token simulation / process simulation / performance simulation | `OUT_OF_V1` |
| Process deployment | `OUT_OF_V1` |
| Migração `flowchart_v1` → BPMN | `FUTURE` — não contaminar V1 antes do editor estabilizar; `flowchart_v1` segue canônico do Transformômetro |
| Criação de BPMN extensions proprietárias DELPI | `OUT_OF_V1` — sem requirement explícito; **preservação** de extensions desconhecidas é requirement (Prompt 3) |
| Integração profunda Transformômetro (process↔model reference, open model from Transformômetro, selected revision reference) | `OUT_OF_V1` — `FUTURE` increment; a V1 funciona standalone |
| Hard delete de modelo | `OUT_OF_V1` — `FUTURE` sob política de governança |
| PDF export | `OUT_OF_V1` — `FUTURE` |
| Thumbnails na library | `FUTURE` |
| Mini-map | `FUTURE` |
| Alignment/distribution | `FUTURE` |
| Grid configurável | `FUTURE` |
| Edição de element id | `FUTURE` |
| Criação de: Complex Gateway, Ad-hoc/Transaction/Event SubProcess, Data Input/Output, event definitions `RENDER_PRESERVE_ONLY` | `FUTURE` |
| Diff visual/XML entre revisões | `FUTURE` |
| Edição em tablet / qualquer uso mobile | `OUT_OF_V1` / `FUTURE` (edição em tablet) |
| Certificação WCAG formal | `OUT_OF_V1` — baseline de acessibilidade da seção 15 permanece `IN_V1` |

> **SUPERSEDED (G0):** três linhas desta tabela foram substituídas pela implementação aceita:
> - `Autosave` → **entregue** como autosave do working copy (debounce + write + authoritative read-back + verify); `Ctrl+S` permanece como flush manual. `AUTOSAVE != REVISION`.
> - `Edição de element id` → **entregue** via grupo "Configurações avançadas" do properties panel (entry vendor, command stack, refs atualizadas).
> - `Thumbnails na library` → **entregue** (`BpmnModelThumb` renderiza SVG do working copy na biblioteca, cache por `model@version`). Também `FUTURE` na seção 8.
> Demais linhas permanecem conforme congelado. Detalhes: `CURRENT-STATE.md` §4/§8 e `DOCUMENTATION-DRIFT-LEDGER.md` DRIFT-BPMN-003/006/011.
| Campos de binding de engine (listeners/delegates/async) | `OUT_OF_V1` |
| Edição de extension elements e ioSpecification | `OUT_OF_V1` |

## 18. Capability Matrix

Convenção de IDs: `CAP-<AREA>-<NNN>`, estável para rastreabilidade nos Prompts 2–7 e no DoD.

| CAPABILITY_ID | CAPABILITY | USER VALUE | V1 STATUS | USER/JOURNEY | EDIT SUPPORT | IMPORT SUPPORT | PRESERVATION REQUIREMENT | OWNER | LATER SPEC PROMPT | NOTES |
|---|---|---|---|---|---|---|---|---|---|---|
| CAP-LIFE-001 | Create model | Iniciar modelagem nova | `IN_V1` | Editor / A | n/a | n/a | n/a | BPMN Modeler | 2, 7 | |
| CAP-LIFE-002 | List/find/open model | Retomar trabalho | `IN_V1` | todos / B | n/a | n/a | n/a | BPMN Modeler | 2, 7 | read-only quando não autorizado |
| CAP-LIFE-003 | Rename model | Organização | `IN_V1` | Manager | n/a | n/a | n/a | BPMN Modeler | 2, 7 | |
| CAP-LIFE-004 | Duplicate / save as | Reuso de modelo | `IN_V1` | Manager / I | n/a | n/a | n/a | BPMN Modeler | 2, 7 | novo id; origem = artefato canônico atual |
| CAP-LIFE-005 | Archive/unarchive | Governança de catálogo | `IN_V1` | Manager / J | n/a | n/a | n/a | BPMN Modeler | 2, 7 | sem hard delete |
| CAP-LIFE-006 | Export `.bpmn` | Interoperabilidade | `IN_V1` | todos / D | n/a | n/a | artefato canônico completo | BPMN Modeler | 3, 7 | XML + DI |
| CAP-LIFE-007 | Import `.bpmn` | Interoperabilidade | `IN_V1` | Editor / C | n/a | intake+validation | profile da seção 7 | BPMN Modeler | 3, 7 | blocking policy → Prompt 3 |
| CAP-EDIT-001 | Canvas/palette/context pad | Modelagem core | `IN_V1` | Editor / A,B | `CREATE_EDIT` profile | sim | sim | BPMN Modeler | 4 | biblioteca → Prompt 4 |
| CAP-EDIT-002 | Properties panel | Configuração de elementos | `IN_V1` | Editor | seção 8.1 | n/a | n/a | BPMN Modeler | 4 | |
| CAP-EDIT-003 | Selection/multi/drag/resize/connect/delete/clipboard | Edição fluida | `IN_V1` | Editor | sim | n/a | n/a | BPMN Modeler | 4 | |
| CAP-EDIT-004 | Undo/redo + keyboard shortcuts | Produtividade | `IN_V1` | Editor | n/a | n/a | n/a | BPMN Modeler | 4 | mapa de teclas → Prompt 4 |
| CAP-EDIT-005 | Pan/zoom/fit + snap/grid | Navegação/precisão | `IN_V1` | Editor | n/a | n/a | n/a | BPMN Modeler | 4 | |
| CAP-EDIT-006 | Search in diagram + palette search | Localização em diagramas grandes | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 4 | |
| CAP-BPMN-001 | Activities profile (tasks 8 tipos, call activity, sub-processes collapsed/expanded) | Modelagem profissional | `IN_V1` | Editor | `CREATE_EDIT` | sim | sim | BPMN Modeler | 3, 4 | ad-hoc/transaction/event-subprocess preserve-only |
| CAP-BPMN-002 | Events profile (seção 6.2) | Semântica de eventos | `IN_V1` | Editor | profile 6.2 | sim | sim | BPMN Modeler | 3, 4 | |
| CAP-BPMN-003 | Gateways profile (excl/par/incl/event-based) | Decisão/paralelismo | `IN_V1` | Editor | `CREATE_EDIT` | sim | sim | BPMN Modeler | 3, 4 | Complex preserve-only |
| CAP-BPMN-004 | Flows (sequence/message/association/data assoc.) | Conexão de elementos | `IN_V1` | Editor | `CREATE_EDIT` | sim | sim | BPMN Modeler | 3, 4 | |
| CAP-BPMN-005 | Collaboration (pools, lanes aninhadas, black-box, msg flow) | Diagramas inter-áreas | `IN_V1` | Editor | `CREATE_EDIT` | sim | sim | BPMN Modeler | 3, 4 | |
| CAP-BPMN-006 | Artifacts (data object, data store, annotation, group) | Documentação do processo | `IN_V1` | Editor | `CREATE_EDIT` | sim | sim | BPMN Modeler | 3, 4 | Data Input/Output preserve-only |
| CAP-BPMN-007 | Preserve-only constructs + unknown extensions | Round-trip sem perda | `IN_V1` | Editor / C | preserve | sim | obrigatório (prova → Prompt 3) | BPMN Modeler | 3 | |
| CAP-VALID-001 | Run validation (demand/import/save) | Qualidade do modelo | `IN_V1` | todos | n/a | sim | n/a | BPMN Modeler | 3 | policy de bloqueio → Prompt 3 |
| CAP-VALID-002 | Issues list + severity + stages (evaluated/not-evaluated) + source | Diagnóstico | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 3, 4 | |
| CAP-VALID-003 | Issue → element navigation | Correção guiada | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 3, 4 | quando reference resolve |
| CAP-REV-001 | Working copy + immutable revisions + history list | Governança | `IN_V1` | todos / G | n/a | n/a | snapshot canônico | BPMN Modeler | 2 | |
| CAP-REV-002 | Open revision read-only + current revision indicator | Auditoria | `IN_V1` | todos / G | n/a | n/a | n/a | BPMN Modeler | 2, 4 | |
| CAP-REV-003 | Create snapshot/revision | Versionamento explícito | `IN_V1` | Manager / G | n/a | n/a | n/a | BPMN Modeler | 2 | |
| CAP-REV-004 | Restore revision (append-only) | Recuperação | `IN_V1` | Manager / H | n/a | n/a | histórico nunca reescrito | BPMN Modeler | 2 | |
| CAP-SAVE-001 | Explicit save com dirty/saving/saved/error/conflict | Confiança de persistência | `IN_V1` | Editor / E | n/a | n/a | n/a | BPMN Modeler | 2, 4, 7 | **SUPERSEDED (G0):** entregue como autosave do working copy + flush `Ctrl+S`; estados dirty/saving/saved/error/conflict observáveis conforme especificado |
| CAP-SAVE-002 | Concurrent update detection | Proteção contra overwrite | `IN_V1` | Editor | n/a | n/a | n/a | BPMN Modeler | 2, 6 | mecanismo → Prompts 2/6 |
| CAP-LAYOUT-001 | Auto-layout CALCULATE→PREVIEW→ACCEPT/CANCEL→SAVE | Diagrama legível | `IN_V1` | Editor | n/a | n/a | sem persistência sem save | BPMN Modeler | 5 | algoritmo → Prompt 5 |
| CAP-DI-001 | BPMN-DI read/render/edit/persist/export | Geometria canônica | `IN_V1` | Editor | sim | sim | sim | BPMN Modeler | 5 | sem segunda fonte visual |
| CAP-LIB-001 | Library list/search/sort/pagination/archive filter | Catálogo | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 7 | |
| CAP-OUT-001 | SVG export | Derivado visual | `IN_V1` | todos | n/a | n/a | derivado não-canônico | BPMN Modeler | 4, 7 | |
| CAP-OUT-002 | PNG export | Derivado visual | `IN_V1` | todos | n/a | n/a | derivado não-canônico | BPMN Modeler | 4, 7 | |
| CAP-A11Y-001 | Accessibility baseline (keyboard/focus/labels/contrast/non-color status) | Usabilidade inclusiva | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 4 | sem claim WCAG formal |
| CAP-DEV-001 | Device scope (desktop full, tablet read-only) | Clareza de suporte | `IN_V1` | todos | n/a | n/a | n/a | BPMN Modeler | 4 | mobile `OUT_OF_V1` |
| CAP-AUTH-001 | Read-only vs edit vs manage enforcement | Segurança backend-first | `IN_V1` | todos | n/a | n/a | n/a | Core (RBAC) + BPMN Modeler (enforcement) | 6 | códigos de permissão → Prompt 6 |

## 19. Decision Dependency Map — Prompts 2–7

Tudo `IN_V1` aqui tem escopo fechado; o que segue é apenas o **HOW** e seu dono.

| Prompt | Dono de | Decisões pendentes |
|---|---|---|
| **PROMPT 2 — Backend & Domain freeze** | persistência, revisions, lifecycle, concorrência | schema de model/revision; algoritmo de numeração de revisão; checksum; contratos de create/rename/duplicate/archive/restore; mecanismo de concurrency detection; metadata fields exatos (seção 14); política de save vs validation (com Prompt 3) |
| **PROMPT 3 — BPMN / validation / interoperability / libraries** | parser, validator, round-trip | parser XML concreto; implementação de `BpmnArtifactValidationPort`; regras por `ValidationStage`; operation policy de import/save/export (o que bloqueia o quê); critérios de prova de preservação/round-trip; tratamento de extensions desconhecidas; intake de BPMN sem DI (com Prompt 5) |
| **PROMPT 4 — Frontend & Editor UX freeze** | editor, properties, painéis, estados | biblioteca/framework de editor BPMN; implementação do properties panel; painel de validação; wiring de dirty/saving/saved/error/conflict; mapa de keyboard shortcuts; export SVG/PNG client-side; tablet read-only |
| **PROMPT 5 — Layout & BPMN-DI freeze** | auto-layout, DI | engine/algoritmo de auto-layout; geração de DI para import sem DI; mecânica de edição de geometria → DI |
| **PROMPT 6 — Security + persistence + runtime freeze** | AuthZ, storage, runtime | códigos de permissão e mapeamento ator→RBAC (Core); tecnologia de storage e migrations; mecanismo físico de concorrência; deploy/runtime/observability |
| **PROMPT 7 — API + E2E + acceptance + docs finais** | contratos HTTP, aceite | OpenAPI completo; endpoints de lifecycle/import/export/revisions; harness E2E; execução da Definition of Done; documentação final |

## 20. V1 Definition of Done

A V1 só pode ser declarada pronta quando **todos** os gates abaixo passarem, com evidência:

### DoD-1 — Model lifecycle

- [ ] create, list/find, open (edit + read-only), rename, duplicate, archive, unarchive funcionam end-to-end.
- [ ] hard delete **não existe** na superfície.

### DoD-2 — BPMN lifecycle

- [ ] import `.bpmn` → intake/validation → render → edit (profile `CREATE_EDIT`) → validate → save → reopen → export `.bpmn` funciona end-to-end.
- [ ] reabertura reproduz fielmente o diagrama (semântica + geometria).

### DoD-3 — Canonical integrity

- [ ] BPMN 2.0 XML + BPMN-DI no mesmo artefato é a única fonte persistida; nenhuma segunda fonte visual persistida existe.
- [ ] Round-trip do profile aprovado no Prompt 3 prova preservação (incluindo elementos `RENDER_PRESERVE_ONLY` e extensions desconhecidas).

### DoD-4 — Editor

- [ ] Todas as capabilities `IN_V1` da seção 8 e todos os elementos `CREATE_EDIT` da seção 6 estão operacionais (create/edit/delete/connect/undo/redo/persistir).
- [ ] Auto-layout executa CALCULATE→PREVIEW→ACCEPT/CANCEL e nada persiste sem save explícito.
  - **SUPERSEDED (G0):** o persist pós-ACCEPT é feito pelo autosave do working copy (ACCEPT → DIRTY → autosave → read-back verify). O critério de segurança continua sendo: nenhum write canônico sem ACCEPT, e CANCEL nunca escreve.

### DoD-5 — State

- [ ] Estados `clean/saved`, `dirty`, `saving`, `save failed`, `conflict` são observáveis e corretos.
- [ ] Concurrent update detection impede overwrite silencioso.

### DoD-6 — Validation

- [ ] O validation profile do Prompt 3 é executável nas superfícies `IN_V1` (demand/import/save).
- [ ] Issues exibem severity, stage, source; stages não avaliados são distinguíveis; issue→element navega quando há referência.

### DoD-7 — Revisions

- [ ] Snapshot explícito, lista, metadados (id/timestamp/autor), open read-only, indicador de revisão corrente e restore append-only funcionam.
- [ ] Histórico nunca é reescrito (restore cria nova revisão).

### DoD-8 — Security & runtime

- [ ] Autorização backend-first por capability (view/edit/manage) conforme spec do Prompt 6 — frontend nunca é autoridade.
- [ ] Acceptance de runtime/observability conforme spec do Prompt 6.

### DoD-9 — Acceptance

- [ ] Contratos OpenAPI e E2E do Prompt 7 passam.
- [ ] Nenhum item da seção 17 foi implementado.
- [ ] Documentação final do Prompt 7 reflete o que foi entregue.

## 21. Open Questions

Não há questão funcional (WHAT) aberta dentro do escopo deste prompt. As questões abaixo são exclusivamente de HOW, com dono já atribuído na seção 19:

1. Schema/numeração/checksum de revisões e contratos de lifecycle → Prompt 2.
2. Mecanismo de concurrent update detection → Prompts 2 e 6.
3. Parser/validator concretos, conjunto de regras por stage e operation policy de bloqueio → Prompt 3.
4. Biblioteca de editor BPMN e implementação dos painéis → Prompt 4.
5. Engine de auto-layout e geração/edição de BPMN-DI → Prompt 5.
6. Códigos de permissão, storage, migrations, runtime → Prompt 6.
7. OpenAPI, endpoints e harness de aceite E2E → Prompt 7.

## 22. Specification Freeze Status

- [x] Todas as capabilities relevantes classificadas (`IN_V1`/`OUT_OF_V1`/`FUTURE`/`DEPENDENT_ON_LATER_SPEC`)
- [x] User journeys fechadas (seção 5)
- [x] Editing profile fechado (seção 6) com distinção create vs preserve (seção 7)
- [x] Out-of-scope explícito (seção 17)
- [x] Definition of Done existe (seção 20)
- [x] Nenhuma decisão funcional crítica deixada para o implementador inferir

```text
V1 PRODUCT SCOPE STATUS:
FROZEN
```
