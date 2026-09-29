# BPMN Modeler — V1 Frontend / Editor / UX Specification Freeze

> Documento canônico da V1 para arquitetura de frontend, editor BPMN, ownership de estado, páginas/fluxos de UX e comportamento do editor visual.
> Status alvo: `FROZEN` — ver seção 53.
> Sequência: **PROMPT 4/7** — depende de `V1-SCOPE-FREEZE.md`, `BACKEND-DOMAIN-SPEC-FREEZE.md` e `BPMN-INTEROPERABILITY-SPEC-FREEZE.md`; não reabre nenhum deles.

## 1. Purpose

Fechar o WHAT/HOW de frontend da V1 do Meu Modelador de Processos: onde o frontend vive, qual editor BPMN concreto é usado, como React se integra ao editor, quem possui cada pedaço de estado, como o XML canônico flui no cliente, quais telas existem, como salvar/conflitar/descartar, como revisions/validação/preservação/read-only aparecem, e como palette/properties/context pad/shortcuts/export/auto-layout se comportam. Ao final deste documento nenhuma decisão frontend crítica pode ficar aberta ao implementador.

## 2. Frozen Inputs

| Documento | Papel |
|---|---|
| `V1-SCOPE-FREEZE.md` (commit `1fa64cbe`) | escopo funcional, jornadas, editing profile, out-of-scope, DoD |
| `BACKEND-DOMAIN-SPEC-FREEZE.md` (commit `ba01d8b4`) | aggregate, WorkingCopy/Revision, save/restore/duplicate/archive, optimistic concurrency, use cases, erros |
| `BPMN-INTEROPERABILITY-SPEC-FREEZE.md` (commit `420f479a`) | recognition states, validation stages, rule catalog, preservation, round-trip, `InputSafetyEvidence`, blank artifact |

Decisões herdadas que este documento preserva sem reabrir:

- BPMN 2.0 XML = semântica canônica; BPMN-DI no mesmo XML = geometria canônica; **nenhum JSON visual persistido**.
- `WorkingCopy` = artefato canônico mutável; `Revision` = snapshot imutável; **SAVE ≠ CREATE REVISION**; save explícito; autosave `OUT_OF_V1`.
- `ValidationReport` = evidência; operation policy decide bloqueio.
- Layout calculado ≠ geometria persistida; backend nunca injeta DI.
- Constructs preserve-only / extensões desconhecidas / `mustUnderstand` seguem a política do Prompt 3.
- Colaboração em tempo real `OUT_OF_V1`; desktop = edição plena; tablet = read-only; mobile = `OUT_OF_V1`.
- `Model.version` = token de concorrência; nunca exposto como "revisão" na UI.

## 3. Existing Frontend Inventory

Inventário real do monorepo (evidência, não memória):

| Item | Evidência | Conclusão |
|---|---|---|
| Host shell | `portal/` — React `19.2.7`, `react-router-dom` `7.x`, `keycloak-js`, `vite` `7.x`, Module Federation via `@originjs/vite-plugin-federation` | host real: **Portal Minha DELPI** |
| Arquitetura de apps | `plugins/<id>/` + `<id>.manifest.json` (`schemaVersion`, `id`, `basePath: /apps/<id>`, `entry: remoteEntry.js`, `permissions[]`, `routes[]`); portal monta via `FederatedAppRouteGuard`/`ProtectedRoute` | plugins = **MFEs federados** com manifest declarativo |
| Design system | `plugins/plugin-ui` (`@delpi/plugin-ui`): actions, layout, navigation, feedback, data, forms, help, menu, preview, ribbon etc. | reutilizar; **não criar segundo design system** |
| Ícones | `lucide-react` no portal e plugins | ícones de produto = Lucide |
| State management | hooks + `useState`/`useReducer`/`Context` (`portalFavorites.ts`, `AuthContext.tsx`); **sem Redux/TanStack Query/Zustand** no host nem em `transformometro` | estratégia mínima = React state/Context; nenhuma lib nova |
| API client | convenção por plugin: `src/data/api/<context>Api.ts` com `fetch` + `<CONTEXT>_API_BASE` + `buildAuthHeaders` (ex.: `transformometroApiBase`) | seguir a mesma convenção |
| i18n | sem framework i18n; labels PT-BR em constantes (`*_LABELS_PT`) | UI V1 em **pt-BR** via constantes de labels |
| Testes frontend | `vitest` nos plugins; testes estruturais `*.test.ts(x)` | vitest = runner congelado |
| Diagrama legado | `plugin-ui/components/bpmn` = `FlowchartEditor` (`@xyflow/react` + `FlowchartV1` JSON) — **não é BPMN 2.0**; usado pelo Transformômetro | referência de shell/layout apenas; **proibido** como editor canônico |
| Imagens/PNG | `html-to-image` presente como peer dep do ecossistema | PNG client-side é viável |

## 4. Frontend Host / Boundary

`FROZEN`:

- **Source root:** `plugins/bpmn-modeler/` — novo pacote MFE do monorepo.
- **Manifest:** `plugins/bpmn-modeler/bpmn-modeler.manifest.json` — `id: "bpmn-modeler"`, `type: "microfrontend"`, `basePath: "/apps/bpmn-modeler"`, `entry: "/apps/bpmn-modeler/assets/remoteEntry.js"`, `permissions[]` e `routes[]` conforme schema dos manifests existentes.
- **Route mounting:** Portal monta o remote em `/apps/bpmn-modeler/*` via `FederatedAppRouteGuard` + `ProtectedRoute` (mesma convenção dos demais plugins).
- **Host integration:** keycloak via `AuthContext` do portal; headers de auth via `buildAuthHeaders`; API própria `bpmn-modeler` (bounded context backend existente em `bpmn-modeler/`).
- **Bounded context:** nenhum componente/hook/modelo de domínio do Transformômetro; o `FlowchartEditor`/`FlowchartV1` de `plugin-ui` **não** é usado pelo BPMN Modeler (modelo visual paralelo proibido).
- **Permission codes:** família `bpmn-modeler.*` — strings exatas delegadas ao Prompt 6; frontend consome capabilities `VIEW`/`EDIT`/`MANAGE` (seção 40).

## 5. Editor Technology Decision

`FROZEN`.

**SELECTED:** `bpmn-js` — classes `Modeler` (edição) e `NavigatedViewer` (read-only), sobre `bpmn-moddle` + `diagram-js`.

Prova contra os requisitos congelados:

| Requirement | Prova |
|---|---|
| BPMN import/export XML | `importXML`/`saveXML` nativos via bpmn-moddle — round-trip com `moddle-xml` preserva elementos/atributos desconhecidos no tree |
| BPMN-DI | `BPMNDiagram`/`BPMNPlane`/shapes/edges serializados no mesmo XML; renderer nativo |
| Editing profile `CREATE_EDIT` | modeling rules + palette/contextPad/replaceMenu customizáveis via modules (`additionalModules`) — perfil enforçado em §31 |
| Preservation (Prompt 3) | moddle-xml mantém elementos/atributos de namespaces desconhecidos no model tree e re-serializa; provado por fixtures FX-EXT no editor (§48) |
| Command stack / dirty | evento público `commandStack.changed` (trigger `execute`/`undo`/`redo`/`clear`) + posição mantida pelo adapter = save point confiável (§13) |
| Palette / context pad / keyboard / copy-paste / multi-select | módulos diagram-js/bpmn-js incluídos; todos customizáveis/substituíveis |
| Properties panel | `bpmn-js-properties-panel` oficial (seção 30) |
| Read-only | `NavigatedViewer` — sem módulos de mutação (seção 21) |
| React integration | biblioteca framework-agnostic; lifecycle controlado pelo adapter (seções 7/10) |
| Custom modules | `additionalModules`/`moddleExtensions` documentados — usamos modules, **não** moddleExtensions na V1 (seção 74 do contrato: registry vazio) |

Restrição material registrada: a licença bpmn.io exige o badge **"Powered by bpmn.io"** visível no container do diagrama — é requisito de licença, não opcional. Não esconder via CSS.

**REJECTED:**

| Alternativa | Motivo |
|---|---|
| `@xyflow/react` (React Flow) + serializer próprio | não serializa BPMN 2.0 XML nativamente; exigiria modelo visual paralelo — proibido pelo freeze; preservation de extensões desconhecidas não provada |
| Reusar `FlowchartEditor` de `plugin-ui` | serializa `FlowchartV1` JSON — modelo canônico errado (legado Transformômetro) |
| Apenas `NavigatedViewer` para tudo | não edita — falha o editing profile |
| Editor próprio sobre `diagram-js` | mesma stack-base, mas reescreve toda a camada BPMN (modeling, rules, palette BPMN) — custo sem ganho |
| Editors de engine (Camunda/Flowable/KIE suites) | acoplamento a engine fora de escopo; V1 é modelador, não executor |

## 6. Library Version Matrix

Versões avaliadas no momento da tarefa (registro npm). **Lock exato de versão e integridade = Prompt 6** (deploy/runtime); este freeze fixa família/linha e papel.

| PACKAGE | VERSION EVALUATED | PURPOSE | LICENSE | COMPATIBILITY | SELECTED/REJECTED | RATIONALE | KNOWN LIMITATIONS | PROOF SOURCE |
|---|---|---|---|---|---|---|---|---|
| `bpmn-js` | 18.x (registry `18.30.1`) | editor/viewer BPMN 2.0 | bpmn.io license (badge obrigatório) | React-agnostic; bundling via npm | **SELECTED** | única stack madura com BPMN import/export/DI/command stack completos | badge bpmn.io permanente; um `BPMNDiagram` visível por vez; múltiplos diagramas requerem `open()` | registry.npmjs.org/bpmn-js; bpmn.io/toolkit |
| `bpmn-moddle` | 10.x (registry `10.1.0`) | read/write BPMN 2.0 XML | MIT | interno do bpmn-js | **SELECTED** (via bpmn-js) | representação parseada do editor; preservation de extensões no tree | tree é transitório — nunca persistido como JSON | npmjs.com/bpmn-moddle |
| `bpmn-js-properties-panel` | 5.x (registry `5.65.x`, usa `@bpmn-io/properties-panel` 3.x) | painel de propriedades | MIT | compatível com bpmn-js 18.x | **SELECTED** | oficial, cobre o escopo de propriedades do Prompt 1 | providers engine-specific devem ser desligados | npmjs.com/bpmn-js-properties-panel |
| `@bpmn-io/properties-panel` | 3.x (transitivo) | UI base do painel | MIT | interno do pacote acima | SELECTED (transitivo) | — | — | idem |
| `htm`/`preact` internals do properties panel | transitivos | render do painel | MIT | — | aceito como dependência transitiva | não expostos ao código do produto | — | — |
| `react`/`react-dom` | 19.2.7 | UI | MIT | host | SELECTED (existente) | — | — | `portal/package.json` |
| `react-router-dom` | 7.x | rotas | MIT | host | SELECTED (existente) | — | — | idem |
| `lucide-react` | ^0.576.x | ícones | ISC | plugins | SELECTED (existente) | — | — | package.json dos plugins |
| `@xyflow/react` | ^12.11.x | canvas genérico | MIT | plugin-ui peer | **REJECTED** para o editor canônico | sem BPMN XML/DI nativo | — | plugin-ui package.json |
| `html-to-image` | ^1.11.x | rasterização | MIT | peer plugin-ui | aceito como mecanismo elegível para PNG | já no ecossistema | — | idem |

## 7. Editor Adapter Contract

`FROZEN` — única superfície por onde React conversa com o vendor. Nome congelado: **`BpmnEditorAdapter`** (interface TypeScript em `plugins/bpmn-modeler/src/editor/`).

```text
BpmnEditorAdapter
  mount(container: HTMLElement, mode: "edit" | "viewer"): void
  destroy(): void

  importXml(xml: string): ImportResult          // { ok } | { error: EditorImportFailure }
  exportXml(): Promise<string>                  // save candidate
  exportSvg(): Promise<string>

  listDiagrams(): DiagramRef[]                  // { id, name? } — multi-BPMNDiagram
  openDiagram(diagramId: string): void

  isDirty(): boolean                            // token no cursor vs savedToken (identidade branch-aware)
  markSaved(): void                             // fixa save point
  undo(): void
  redo(): void
  canUndo(): boolean
  canRedo(): boolean

  zoomIn(): void
  zoomOut(): void
  fitViewport(): void

  findElements(query: { name?: string; id?: string }): ElementRef[]
  selectElement(id: string): void               // select + center
  getElementSummary(id: string): ElementSummary // name/id/documentation/attrs p/ inspector

  subscribe(events: EditorSubscriptions): Unsubscribe
    // onChanged (commandStack.changed), onSelectionChanged,
    // onImportDone, onError
```

Regras do contrato:

- `mode` é decidido no `mount` — editável usa `Modeler`, read-only usa `NavigatedViewer` (seção 21). Trocar de modo = `destroy()` + novo `mount` (seção 10).
- `exportXml()` usa configuração de serialização **estável** da V1: `format: false` (XML compacto; formatação não é requirement canônico — diffs humanos ficam legíveis por chave/ordem estável; round-trip tests decidem se `format:true` é seguro antes de mudar).
- `importXml` falhando por limitação do vendor ⇒ `EDITOR_CAPABILITY_FAILURE` — nunca `INVALID_BPMN` (seção 29).
- Adapter não conhece HTTP, rotas, ValidationReport ou `Model` — recebe XML, devolve XML e eventos.
- Nenhum outro arquivo importa `bpmn-js`, `diagram-js`, `bpmn-moddle` ou acessa `modeler.get(...)`/`eventBus`/`elementRegistry`/`commandStack` (seção 11, Vendor Leakage).

## 8. React ↔ Editor Ownership

`FROZEN` — separação obrigatória:

**React/Application owns:**

- metadados do modelo (id, display_name, created/updated, archived)
- `version` token (concorrência), capabilities (`VIEW/EDIT/MANAGE`)
- save state machine (CLEAN/DIRTY/SAVING/SAVE_FAILED/CONFLICT)
- `authoritativeXml` (último artefato confirmado pelo backend)
- `ValidationReport` atual e resultado de intake/recognition
- lista de revisions e metadados de revisão selecionada
- route state, dialogs, toasts/notifications
- filtros/paginação/busca da library; estados de request ao servidor
- UI state efêmero (painel aberto, aba ativa, overlays)

**Editor owns (transient, dentro do adapter):**

- moddle tree parseado (representação interna)
- canvas state, viewport, seleção atual
- command stack, undo/redo
- geometria em memória
- manipulação de elementos

**Proibido:** duplicar o modelo BPMN completo em React state; persistir moddle tree/editor state; guardar instância do modeler em estado serializável global.

## 9. Canonical XML Client Contract

`FROZEN` — três papéis distintos de XML no cliente:

| Nome | Papel |
|---|---|
| `authoritativeXml` | último artefato **confirmado pelo backend** (read-back de load/save/restore); fonte para comparação e edição base |
| editor working state | representação in-memory do vendor (moddle tree) — nunca persiste, nunca é enviada como JSON |
| `saveCandidate` | `exportXml()` produzido no momento do Save — enviado ao backend, **não** confiável como autoridade |

Fluxo de save (seção 14): `saveCandidate` → backend write → **authoritative read-back** → `authoritativeXml = read-back` → `markSaved()` → CLEAN. Se read-back falhar: `OUTCOME_VERIFICATION_FAILED` (seção 39) — nunca declarar "salvo" pelo eco do request.

## 10. Editor Lifecycle

`FROZEN`:

- **Uma** instância de editor por workspace ativo. Criada no `mount` do `BpmnCanvasHost`; destruída no unmount/troca de rota/troca de modelo.
- `importXml` ocorre uma vez por instância com o `authoritativeXml` atual. **Replace model** (restore confirmado, conflict→reload latest) = `destroy()` + `mount` + `importXml` — não `importXML` por cima de edição viva.
- Troca de modo (editável ↔ read-only) = recreate da instância com a classe correta (`Modeler` ↔ `NavigatedViewer`).
- Nunca recriar o `Modeler` em re-render React; a instância vive em ref interno do adapter, não em state.

## 11. State Ownership Model

`FROZEN` — três buckets, sem overlap:

```text
SERVER STATE      → metadados, library, revisions, authoritativeXml, ValidationReport, version
                    (data/api client + hooks; mutations passam pela save state machine explícita)
EDITOR STATE      → moddle tree, canvas, seleção, command stack   (interno ao BpmnEditorAdapter)
EPHEMERAL UI      → painel ativo, dialogs, overlays, draft de dialogs (React local state/Context)
```

Vendor Leakage `FROZEN`: chamadas a APIs vendor (`modeler.get`, `eventBus`, `commandStack`, `elementRegistry`, `modeling`, `canvas`, `moddle`) só dentro de `src/editor/` (adapter + seus modules). Única exceção permitida: providers customizados bpmn-js dentro do mesmo diretório `src/editor/modules/` (palette/contextPad/rules/replace overrides) — são módulos do adapter, não componentes React.

## 12. Save State Machine

`FROZEN`:

```text
states principais: CLEAN | DIRTY | SAVING | SAVE_FAILED | CONFLICT
modo ortogonal:    READ_ONLY (substitui o conjunto de estados de save; nunca DIRTY)
boot:              LOADING (antes da primeira renderização do modelo)

transições:
LOADING   → load ok, editable          → CLEAN
LOADING   → load ok, read-only reason  → READ_ONLY
LOADING   → falha de load              → erro de página (seção 39)
CLEAN     → edição no editor           → DIRTY
DIRTY     → undo até save point        → CLEAN
DIRTY     → Save                       → SAVING
SAVING    → backend write + read-back verificado → CLEAN
SAVING    → VALIDATION_BLOCKED         → DIRTY (painel de validação aberto; edição preservada)
SAVING    → conflito de versão         → CONFLICT
SAVING    → falha de rede/backend      → SAVE_FAILED
SAVE_FAILED → retry Save               → SAVING
SAVE_FAILED → descartar (confirmação)  → READ_ONLY (reload authoritative)
CONFLICT  → Reload latest              → READ_ONLY→* (recarrega; volta a CLEAN se edição permitida) 
CONFLICT  → Export my local BPMN       → CONFLICT (exporta e permanece; usuário decide depois)
```

Não existe autosave; não existe merge.

## 13. Dirty State Contract

`FROZEN` — fonte da verdade = **command stack do editor** via **APIs/eventos públicos apenas**, não boolean React, e com **identidade de estado branch-aware** — profundidade numérica não basta (undo→undo→2 novas edições retornaria à mesma posição numérica com estado diferente; isso seria false CLEAN). O adapter mantém um histórico de identidade externo:

```text
stateTokens: token[]        // identidades de estado do editor
cursor: int                 // posição lógica corrente
savedToken: token           // token do último save verificado

load/import              → stateTokens = [newToken()], cursor = 0, savedToken = t0 → CLEAN
trigger = execute        → truncate(stateTokens após cursor); append novo token único; cursor += 1
                           (edição após undo cria branch de identidade distinta — nunca colide)
trigger = undo           → cursor -= 1
trigger = redo           → cursor += 1
trigger = clear          → reset conforme operação de load/import
dirty                    ⇔  stateTokens[cursor] ≠ savedToken
markSaved()              → savedToken = stateTokens[cursor]   (apenas após read-back verificado)
```

O `trigger` vem do evento público `commandStack.changed` (`execute | undo | redo | clear`). **Proibido** acessar internals privados do vendor (`commandStack._stack`, `commandStack._stackIdx` ou equivalentes). Se a versão lockada do diagram-js expuser API pública superior com a mesma semântica, ela pode substituir o mecanismo — mas a propriedade obrigatória permanece: **branch-aware state identity**, nunca stack depth. Correção aplicada neste documento pelo Prompt 6 (refinamento da correção do Prompt 5):

| Evento | Efeito no dirty |
|---|---|
| import/load inicial | save point fixado → CLEAN |
| edição que gera command (`execute`) | novo token no cursor ≠ savedToken → DIRTY (inclusive após undo — nova branch) |
| undo até o save point | CLEAN |
| redo além do save point | DIRTY |
| save verificado | `markSaved()` → CLEAN |
| restore confirmado | novo authoritative → CLEAN (instância recriada) |
| carregar revision | viewer read-only; não afeta dirty do working copy |
| trocar de modelo | guard de unsaved-changes (seção 16); nova instância CLEAN |
| auto-layout **preview** | transacional — não marca dirty |
| auto-layout **accept** | commands aplicados → DIRTY |

Backend-initiated changes (rename de metadado, archive) não passam pelo command stack e não afetam dirty.

## 14. Save UX

`FROZEN` — fluxo visual exato:

1. Usuário aciona `Salvar` (toolbar) ou `Ctrl/Cmd+S`.
2. `exportXml()` → `saveCandidate`; UI → `SAVING` (indicador "Salvando…", ações de write desabilitadas).
3. Request com `expected_version` (token) — contrato Prompt 2/7.
4. Backend write → authoritative read-back → verificação → `authoritativeXml` atualizado → `markSaved()` → `CLEAN` + confirmação textual "Salvo".
5. `VALIDATION_BLOCKED`: volta a `DIRTY`, painel de validação abre com resumo de issues; **edição local preservada**.
6. Conflito: `CONFLICT` (seção 15). Falha de rede/5xx: `SAVE_FAILED` com retry explícito.
7. `OUTCOME_VERIFICATION_FAILED`: estado de erro dedicado — a UI diz "não foi possível confirmar a gravação" e oferece `Recarregar estado autoritativo` / `Tentar verificar novamente`; **nunca** reenvia write automaticamente.

## 15. Conflict UX

`FROZEN`:

- `CONFLICT` exibe dialog bloqueante de fluxo (mas sem perder o canvas por trás): mensagem inequívoca "outro usuário/processo alterou este modelo enquanto você editava; sua versão local diverge da versão autoritativa".
- Opções permitidas: **Recarregar versão mais recente** (descarta edição local após confirmação), **Exportar meu BPMN local** (download do `saveCandidate`/estado atual), **Permanecer em conflito** (canvas congela em read-only de conflito; toolbar de edição desabilitada; usuário pode exportar local depois).
- **Sem merge automático. `force overwrite` = `OUT_OF_V1`.**
- Em CONFLICT, edição continua visualmente acessível em read-only até decisão — nunca descarte silencioso.

## 16. Unsaved Changes UX

`FROZEN`:

- Gatilhos cobertos: navegação interna (voltar à library, abrir outro modelo, abrir revision, mudar de rota) e saída do browser (refresh/close/logout).
- In-app (`DIRTY`): dialog de confirmação — **Continuar editando** | **Descartar alterações** | **Salvar e sair** (visível apenas se capability `EDIT` e sem CONFLICT; executa o fluxo de save e só navega após verificação; se save falhar, permanece).
- Browser exit/refresh/logout: `beforeunload` registrado enquanto `DIRTY` — o prompt nativo do browser é o comportamento máximo possível; a UI não promete texto customizado.
- `READ_ONLY`/`CLEAN`: navegação livre, sem confirmação.

## 17. Route / Page Map

`FROZEN` — superfícies V1 (URLs = recursos, não internals do editor):

| Route | Página | Modo |
|---|---|---|
| `/apps/bpmn-modeler` | **Model Library** | listagem/busca/paginação/archive filter |
| `/apps/bpmn-modeler/models/:modelId` | **Model Editor** | editor (Modeler) ou read-only conforme capability/estado |
| `/apps/bpmn-modeler/models/:modelId/revisions/:revisionNumber` | **Revision View** | read-only viewer de artefato histórico (seção 24) |

Decisões: **Create/Import são dialogs** dentro da Library (não rotas); **Revision History é painel lateral** no editor (seção 23); **Revision View é rota própria** (deep-linkável, inequivocamente distinta do working copy). Query params só para estado de UI não-canônico (filtro de library, aba do painel); nunca estado do modelo.

## 18. Model Library UX

`FROZEN`:

- **Desktop layout:** tabela (design system `data`/`layout` components), não cards.
- Colunas: **Nome** (display_name), **Atualizado em**, **Criado em**, **Estado** (badge `Arquivado`), **Revisões** (número). Ordenação default: mais recente atualizado.
- Busca por nome/id; filtro de arquivados (toggle `Incluir arquivados`, default off conforme list query); paginação server-side.
- Ações primárias de página: `Novo modelo`, `Importar BPMN`.
- Row actions: `Abrir`, `Exportar .bpmn`, `Duplicar` (EDIT/MANAGE), `Arquivar`/`Desarquivar` (MANAGE).
- Empty state: "Nenhum modelo ainda — crie ou importe um arquivo .bpmn" + CTAs; search-empty: "Nenhum resultado para a busca"; loading: skeleton/rows; error: mensagem + retry.
- Arquivado: badge visível + ações de edição ausentes.

## 19. Create Model UX

`FROZEN`:

- `Novo modelo` → **dialog** pedindo `display_name` (obrigatório, input do usuário) → criar → navega ao editor.
- Editor abre com o **blank artifact do Prompt 3** (canvas vazio, sem start event), `CLEAN`, `version` autoritativa do read-back.
- `display_name` ≠ nome do `bpmn:process` — nunca preencher o process name automaticamente a partir do nome do modelo.

## 20. Import UX

`FROZEN` — dialog multi-step na Library: `Escolher arquivo .bpmn` → intake/validação → **resultado por estado de recognition** → `display_name` (sugerido pelo filename, editável — filename nunca é autoridade) → criar quando permitido → abrir.

| Recognition | UX |
|---|---|
| `INPUT_REJECTED_SECURITY` | bloqueio com motivo de segurança ("arquivo rejeitado pela verificação de segurança" + categoria SEC-*); **não** dizer "XML inválido" |
| `NON_XML` | "o arquivo não contém XML legível" |
| `MALFORMED_XML` | "XML malformado" + posição `xml:{line}:{column}` quando presente |
| `XML_NOT_BPMN` | "XML válido, mas não é um diagrama BPMN 2.0" |
| `BPMN_RECOGNIZED_INCOMPLETE` | permitido; resumo de issues estruturais exibido antes de confirmar |
| `BPMN_RECOGNIZED_WITH_ISSUES` | permitido; resumo de issues exibido |
| `BPMN_RECOGNIZED` | fluxo limpo direto ao nome |

Rejeição nunca cria modelo; nenhum estado é colapsado em "arquivo inválido" genérico.

## 21. Read-only Architecture

`FROZEN` — **uma única estratégia** para todos os motivos read-only:

- Instância `NavigatedViewer` via `BpmnEditorAdapter.mount(mode:"viewer")` — sem módulos de mutação (palette/context pad/modeling direto não existem por construção; pan/zoom/fit/seleção/search/validação/export permitidos conforme policy).
- Motivos (mesmo pipeline, banners distintos): permissão `VIEW` sem `EDIT`; **revision histórica**; **modelo arquivado**; **`mustUnderstand` não suportado**; **preservation/capability failure** (incl. `EDITOR_CAPABILITY_FAILURE`); **tablet**.
- Painel de propriedades: em read-only o modo Properties exibe o **inspector product-owned** (name/id/documentation + atributos genéricos) — o `bpmn-js-properties-panel` só existe no modo editable.
- Não há cinco implementações: há um banner/param `readOnlyReason` sobre a mesma pilha viewer.

## 22. Archived Model UX

`FROZEN`:

- Badge `Arquivado` persistente no header + read-only (motivo `archived`).
- Permitido: view, pan/zoom, busca, validação, export, histórico, `Duplicar`, `Desarquivar` (MANAGE).
- Bloqueado: edit, save, create revision, restore, rename, archive novamente — conforme contrato backend; UI omite/desabilita.

## 23. Revision History UX

`FROZEN`:

- Aba **`Histórico`** no painel lateral direito (contextual panel, seção 43) — mantém contexto do modelo.
- Cada entrada: **número da revisão**, timestamp, autor, `origin` (save/restore/import), e `restore provenance` quando aplicável (ex.: "restaurada da Revisão 3").
- Ações por revisão: `Abrir` (→ rota read-only), `Exportar .bpmn`, `Restaurar` (capability EDIT + não arquivado).
- Empty state: "Ainda não há revisões deste modelo"; a revisão inicial criada no primeiro save/criação aparece normalmente.

## 24. Revision View UX

`FROZEN`:

- Rota `/models/:modelId/revisions/:revisionNumber` — `NavigatedViewer` read-only + **header inequívoco**: "Revisão {n} de {modelo} — visualização histórica" + breadcrumb `Biblioteca → {modelo} → Revisão {n}` + ação `Voltar ao modelo atual`.
- Metadados da revisão visíveis (número, autor, data, origem, provenance).
- Nunca apresentar como working copy: sem Save, sem palette, sem edição; banner `READ_ONLY` com motivo `revision`.
- Renderer compartilhado com a estratégia read-only (seção 21) — sem renderer próprio.

## 25. Create Revision UX

`FROZEN`:

- Ação explícita **`Criar revisão`** no header (junto a Save, separada visualmente) e na aba Histórico. `Save` e `Create Revision` são ações distintas; não existe "Save & Create Revision" como única forma.
- Requer edição permitida e não-arquivado; confirmação leve informando que uma snapshot imutável será criada.
- `NO_CHANGES` (working copy ≡ última revisão): informação amigável "sem alterações desde a última revisão" — não erro.
- Após sucesso: histórico recarrega, nova revisão aparece com número visível.

## 26. Restore UX

`FROZEN`:

- `Restaurar` em uma revisão (lista ou Revision View) → dialog de confirmação explicando o efeito exato: **"o histórico não será apagado; uma nova revisão será criada e o conteúdo atual do modelo passará a ser o desta revisão."**
- Confirmação explícita → backend restore (append-only) → read-back verificado → editor recria com o novo authoritative → CLEAN → banner/toast "Restaurado — Revisão {n+1} criada".
- Falha de verificação → `OUTCOME_VERIFICATION_FAILED` (seção 39). Em CONFLICT prévio o usuário decide o conflito antes.

## 27. Validation Panel

`FROZEN` — aba **`Validação`** do painel lateral:

- Header: contagens por severidade (erros/avisos/info) + timestamp do último relatório + botão `Validar` (trigger explícita).
- Lista de issues: **severidade, stage, source, rule_id, mensagem, reference** — agrupadas por stage na ordem do enum, ordenação interna conforme Prompt 3 §31.
- Seção **"Estágios"** sempre visível: lista de `evaluated_stages` e `not_evaluated_stages` — `NOT_EVALUATED` nunca é escondido (ex.: `INPUT_SAFETY` sem evidência de intake mostra-se como não avaliado, com explicação textual, não como "ok").
- Empty state: "Nenhum problema encontrado" distinto de "validação ainda não executada".
- Trigger explícito `Validar` executa `ValidateWorkingCopy` (evidência efêmera — não persiste).

## 28. Issue Navigation / Canvas Diagnostics

`FROZEN`:

- `element:{bpmn-id}` → adapter `selectElement(id)`: select + center (zoom se necessário) + highlight da issue selecionada.
- `diagram:{bpmndi-id}` → navega para o diagrama/shape DI quando representável (resolve o `bpmnElement` do shape); se o elemento não tiver shape no diagrama atual, abre o diagrama que o contém (multi-diagram, seção 47).
- `xml:{line}:{column}` → painel mostra a posição textual como metadado ("linha 42, coluna 17") — **não** existe editor de XML na V1.
- `extension:{...}` → card contextual explicando a extensão (namespace, QName) e seu efeito (preservada / capability failure).
- Highlight no canvas = **overlay visual derivado** (`canvas.addMarker` equivalente via adapter): badge de erro/aviso por elemento + destaque da issue selecionada; shape/label não é alterado e **nenhum overlay escreve em BPMN-DI**. Nunca só cor: ícone + texto acessível.

## 29. Preservation / Capability Failure UX

`FROZEN` — três níveis visuais distintos:

| Condição | Tratamento |
|---|---|
| Extensões desconhecidas / preserve-only presentes | INFO/WARNING no painel + badge discreto "conteúdo preservado" — edição segue permitida |
| `mustUnderstand=true` não suportado | **banner persistente** "extensão obrigatória não suportada — modelo aberto em modo somente leitura para proteger o conteúdo" + OPEN read-only, EDIT deny, SAVE blocked, EXPORT allow |
| Preservation/capability failure detectado no editor (`EDITOR_CAPABILITY_FAILURE`, risco de perda) | read-only + save blocked + diagnóstico; artefato backend permanece intacto e exportável |

**Preservation Gate `FROZEN`:** ao abrir um artefato importado, editabilidade = `backend classification` (issues EXT-*/capability) **∩** `frontend import capability` (o vendor importou/serializou sem perda, provado por round-trip check `exportXml()` ↔ classificação estrutural no open). Se o gate indicar risco de perda → read-only + SAVE BLOCKED, sem destruição silenciosa.

`RENDER_PRESERVE_ONLY` elements: render normal quando o vendor suporta; selecionáveis e inspecionáveis (inspector genérico); **edição estrutural/de tipo desabilitada**; nunca aparecem na palette nem no replace menu; nunca apagados/convertidos silenciosamente.

## 30. Properties Panel

`FROZEN`:

- Tecnologia: `bpmn-js-properties-panel` (`@bpmn-io/properties-panel` interno), montado no painel lateral aba **Propriedades** no modo editable.
- Escopo V1 exposto (do Prompt 1): `name`, `id` (**read-only**, seção "Avançado"), `documentation`, `conditionExpression` (sequenceFlow), `default flow` (gateway/activity source), event configuration (eventDefinition do elemento conforme profile), linkage `participant`↔`process`, `lane` name, task type (via replace menu — seção 31), subprocess collapsed/expanded, `calledElement`.
- Providers engine-specific (Camunda/Zeebe/etc.) **desabilitados** — nenhuma propriedade de engine na V1.
- Todas as edições passam pelo command stack do editor (undo/redo cobrem — seção 33).

## 31. Palette / Context Pad / Replace Menu

`FROZEN`:

- **Palette** expõe **somente** o profile `CREATE_EDIT`, agrupada: `Eventos` | `Atividades` | `Gateways` | `Dados` | `Colaboração` | `Artefatos` (implementação via palette provider custom). Nenhum `RENDER_PRESERVE_ONLY`, nenhum elemento fora do profile.
- **Context pad** por elemento: `append` (somente targets do profile), `connect`, `replace` (matriz abaixo), `delete` (se permitido pelo tipo). Sem ações para constructs preserve-only/unsupported.
- **Replace menu — matriz congelada:** `Task ↔` tipos de task do profile; `Gateway ↔` gateways do profile; `Evento ↔` definitions válidas para a mesma posição (start/intermediate/boundary/end conforme contexto); `SubProcess` collapsed ↔ expanded; `Participant` só quando semanticamente válido. **Nunca** oferecer transformação que viole o profile ou a semântica só porque o vendor a lista — regra enforçada no replace provider.
- Vendor defaults fora do profile são desabilitados explicitamente (seção 95 do contrato: unsupported vendor features off).

## 32. Keyboard Shortcut Matrix

`FROZEN` (Windows/Linux | macOS):

| Ação | Atalho |
|---|---|
| Save | `Ctrl+S` \| `Cmd+S` |
| Undo | `Ctrl+Z` \| `Cmd+Z` |
| Redo | `Ctrl+Shift+Z` ou `Ctrl+Y` \| `Cmd+Shift+Z` |
| Copy | `Ctrl+C` \| `Cmd+C` |
| Cut | `Ctrl+X` \| `Cmd+X` |
| Paste | `Ctrl+V` \| `Cmd+V` |
| Delete selection | `Delete` / `Backspace` |
| Select all no canvas | `Ctrl+A` \| `Cmd+A` (quando foco no canvas) |
| Zoom in / out | `+` / `-` (toolbar também expõe) |
| Fit viewport | `Ctrl+0` \| `Cmd+0` |
| Search in diagram | `Ctrl+F` \| `Cmd+F` (overlay do produto — intercepta o find do browser enquanto o editor está focado) |
| Cancelar tool/seleção | `Esc` |
| Direct editing (label) | `Enter` ou duplo-clique sobre o elemento |

Atalhos de escopo de canvas não disparam quando o foco está em input/dialog do produto.

## 33. Undo / Redo / Clipboard / Multi-select

`FROZEN`:

- **Undo/redo** cobre: comandos de modeling no canvas, edições de propriedades roteadas pelo command stack, geometria. **Não cobre** ações de aplicação (rename de modelo, archive, create/restore revision, duplicate).
- **Clipboard:** copy/cut/paste **dentro do mesmo modelo** = `IN_V1` (vendor copyPaste). **Cross-model clipboard = `OUT_OF_V1`** — preservation cross-model não provada; nenhum localStorage/clipboard paralelo vira fonte canônica.
- **Multi-select:** `Shift+click` aditivo + box selection (lasso do vendor); bulk move/delete/copy suportados; **sem bulk property editing** na V1.

## 34. Search UX

`FROZEN`:

- `Ctrl/Cmd+F` abre **overlay de busca do produto** (não confundir com find do browser): campo único buscando por nome/id/tipo de elemento.
- Resultados em lista com contexto (nome + tipo + pool/lane); `Enter`/next/previous navega; item ativo = `selectElement` (center + highlight).
- Funciona em read-only; busca opera sobre o element registry do editor — **sem reparse de XML**.
- **Palette search:** campo de filtro na palette filtrando entradas por nome — `IN_V1` (exigência do Prompt 1 atendida por filtro, não por comando separado).

## 35. Zoom / Pan / Fit / Viewport Contract

`FROZEN`:

- Mouse wheel = pan vertical; `Shift+wheel` = pan horizontal; `Ctrl/Cmd+wheel` = zoom; trackpad segue gestos nativos do vendor (pan/zoom).
- Toolbar: `zoom out` / `% atual` / `zoom in` / `fit` (`Ctrl/Cmd+0`).
- **Viewport é estado transiente de UI — nunca persiste em BPMN-DI** e nunca marca dirty.
- `fitViewport` aplicado uma vez após import quando o diagrama excede a tela; nunca como relayout automático destrutivo (seção 47/91).

## 36. Export UX

`FROZEN`:

- Menu `Exportar` no header + row action na library: **`.bpmn`** (artefato canônico do backend — download do authoritative, não do editor), **SVG** (gerado pelo renderer via `exportSvg()`), **PNG** (rasterização **client-side** do SVG via canvas; mecanismo `html-to-image` ou canvas nativo — decisão interna, resultado equivalente).
- SVG/PNG nunca persistem — artefatos derivados por download.
- Em read-only/revision/archived: export permanece disponível conforme policy (incl. mustUnderstand — EXPORT allow).
- Nome de arquivo sugerido = `display_name` sanitizado + extensão; sanitização/headers finais → Prompt 7. Filename não é metadado canônico.

## 37. Auto-layout UX Contract

`FROZEN` (algoritmo → Prompt 5; UX congelada aqui):

- Ação `Organizar diagrama` no header (editable, BPMN com ou sem DI).
- Fluxo: calculando (estado de progresso não-modal) → **preview mode** com banner "Pré-visualização do layout — Aceitar ou Cancelar" + contexto visual before/after → `Aceitar` aplica como commands (DIRTY) / `Cancelar` reverte ao estado exato anterior.
- Preview **reversível por contrato**: mecânica (snapshot/command stack/re-import) → Prompt 5, mas o requisito de reversibilidade exata é deste freeze.
- Sem save automático após Aceitar — `DIRTY`, usuário salva explicitamente.
- **BPMN sem DI:** abertura usa layout transitório com indicador "layout automático não salvo" (não-bloqueante); a geometria transitória **não** marca dirty — dirty só nasce de edição do usuário ou Aceitar de Organizar diagrama.

## 38. Editor Header / Toolbar

`FROZEN` — composição lógica (esquerda→direita):

```text
[Voltar à biblioteca] [Nome do modelo + badges (Arquivado/Read-only/Somente leitura motivo)]
[Save status textual]                                    [Salvar] [Validar] [Criar revisão]
[Desfazer][Refazer] [zoom -/+/fit] [Buscar] [Organizar diagrama] [Exportar ▾] [Mais ▾]
   Mais ▾: Renomear | Duplicar | Arquivar/Desarquivar | Histórico (abre aba do painel)
```

Ações de write aparecem apenas conforme capability/estado; nenhuma ação duplicada em dois lugares sem razão (Histórico também acessível pela aba do painel).

## 39. Loading / Error / Empty States

`FROZEN`:

- **Loading states distintos:** library loading; model loading; "importando diagrama" (vendor parse); "validando…"; "salvando…"; revision loading; "calculando layout…"; "gerando exportação…". Ações não-modais não bloqueiam o canvas inteiro quando seguras.
- **Categorias de erro visíveis (nunca só "algo deu errado"):** rejeição de validação (com painel); conflito; autorização (`Acesso negado — capability insuficiente`); not found; falha de rede/infraestrutura (retry explícito); `OUTCOME_VERIFICATION_FAILED` ("não foi possível confirmar a operação — recarregar estado autoritativo ou tentar verificar novamente", sem re-write automático); rejeição de segurança no import.
- **Erros vendor mapeados:** import/serialization/render/command failures viram `EDITOR_CAPABILITY_FAILURE` ou erro de página — **nunca** stack trace do bpmn-js ao usuário; logging técnico → Prompt 6.
- **Empty states:** sem modelos; sem resultados de busca; sem revisões; "nenhum problema encontrado" (validação); canvas vazio = estado legítimo (não erro nem loading).

## 40. Authorization UX

`FROZEN`:

- Backend entrega capabilities por modelo/contexto: **`VIEW` / `EDIT` / `MANAGE`** (strings de permissão → Prompt 6).
- Frontend oculta/desabilita ações sem capability, mas **frontend não é autoridade** — toda write é autorizada no backend; a UI reflete, não decide.
- `VIEW` sem `EDIT` → open read-only (motivo `permission`). `MANAGE` → archive/unarchive/duplicate/etc.

## 41. Accessibility

`FROZEN` — requisitos implementáveis, sem claim WCAG formal:

**Shell-level garantido (product-owned):**

- todas as ações de header/toolbar/dialogs/painéis acessíveis por teclado; foco visível; botões com nomes acessíveis (tooltips não são label único); dialogs prendem/restauram foco; lista de issues navegável por teclado; navegação issue→elemento por teclado; status (Salvo/Conflito/etc.) comunicado por texto, não só cor/ícone; mensagens de estado via `aria-live` onde aplicável.

**Editor-vendor dependent (documentado honestamente):**

- navegação/interação dentro do canvas SVG do bpmn-js tem acessibilidade limitada do vendor; o produto garante alternativa: toda operação do canvas tem caminho não-canvas (busca por nome/id + selecionar + properties panel + atalhos). Canvas não é o único meio de inspeção/edição assistível — Properties Panel cobre edição de propriedades; ligações/criação puramente gráficas reconhecidamente dependem do vendor na V1.

## 42. Tablet Read-only

`FROZEN`:

- Detecção por **layout**, não user-agent: `max-width < 1024px` **ou** (coarse pointer + viewport < 1024px) ⇒ read-only obrigatório (motivo `tablet`).
- Permitido em tablet: abrir, pan, zoom, fit, busca, painel de validação, histórico de revisões, export.
- Sem editing tools (palette/context pad/edição de propriedades ausentes por construção — `NavigatedViewer`).
- Mobile (< ~768px / viewport muito pequena): `OUT_OF_V1` — exibe mensagem de suporte "edição disponível em desktop" mantendo visualização mínima possível ou bloqueio elegante conforme design system; nunca tenta editor.

## 43. Panel / Responsive Layout

`FROZEN`:

```text
┌──────────────────────────────────────────────────────────────┐
│ Header/Toolbar (seção 38)                                    │
├──────────┬─────────────────────────────────────┬─────────────┤
│ Palette  │            Canvas (BPMN)            │ Painel      │
│ (edit)   │                                     │ lateral     │
│          │                                     │ ┌─────────┐ │
│          │                                     │ │Propried.│ │
│          │                                     │ │Validação│ │
│          │                                     │ │Histórico│ │
│          │                                     │ └─────────┘ │
└──────────┴─────────────────────────────────────┴─────────────┘
```

- **Um painel lateral direito contextual com abas**: `Propriedades` (ou Inspector em read-only), `Validação`, `Histórico` — não drawers múltiplos competindo.
- Painel colapsável; largura segue tokens/layout do design system (sem pixels arbitrários inventados aqui); canvas ocupa o restante.
- Em read-only, palette não existe; painel mantém Inspector/Validação/Histórico.
- Layout responsivo desktop ≥1024px; abaixo disso → tablet read-only (seção 42).

## 44. State Management Technology

`FROZEN`:

- **Nenhuma biblioteca nova**: React `useState`/`useReducer` + Context conforme convenção do host. `data/api/bpmnModelerApi.ts` (fetch + `BPMN_MODELER_API_BASE` + `buildAuthHeaders`) para server state — convenção existente dos plugins.
- Save state machine = `useReducer` explícito (seção 12); **mutations de save/conflict nunca escondidas em cache mágico**.
- `authoritativeXml`/`saveCandidate`/instância do editor **nunca** em store global serializável — adapter em ref, XML em estado do editor-page não-serializado para persistência.

## 45. Design System Integration

`FROZEN`:

- Reuso obrigatório de `@delpi/plugin-ui` para: buttons, dialogs, inputs, tabelas, banners, state messages, tabs, tooltips, layout shell, ícones (Lucide).
- Ícones do vendor BPMN (glyphs de elementos na palette/canvas) permanecem — são intrínsecos à notação; não duplicar nem substituir.
- **Isolamento CSS:** CSS do bpmn-js importado apenas dentro do pacote do plugin e contido ao subtree do editor (classes vendor `.bjs-*` e afins têm baixo risco de colisão; BEM do produto segue convenção existente). Nenhum CSS global novo do produto vaza para o portal.
- Nenhum segundo design system, nenhum tema paralelo.

## 46. Terminology

`FROZEN` — vocabulário pt-BR da UI (termos técnicos BPMN mantidos quando tradução prejudicaria interoperabilidade):

| Conceito | Termo na UI |
|---|---|
| Model / modelo | **Modelo** |
| WorkingCopy | **Modelo atual** / "alterações não salvas" — nunca "WorkingCopy" |
| Revision | **Revisão** |
| `Model.version` token | nunca exibido; **não** chamar de "revisão" |
| Save | **Salvar** |
| Validate | **Validar** |
| Auto-layout | **Organizar diagrama** |
| Archive | **Arquivar** / Desarquivar |
| Import/Export | **Importar** / **Exportar** BPMN |
| `bpmn:process` name | **Nome do processo** (distinto de "Nome do modelo" — seção 58 do fluxo: rename de modelo não toca process name) |
| Gateway types, Task, Event… | notação BPMN pt-BR: "Gateway exclusivo", "Tarefa", "Evento de início" — terminologia consistente na palette/replace/painel |

## 47. Multiple BPMNDiagrams Strategy

`FROZEN` — decisão crítica:

- bpmn-js exibe **um `BPMNDiagram`/`BPMNPlane` por vez**; `modeler.open(bpmnDiagram)` troca o diagrama visível; os demais permanecem no moddle tree e são **preservados na serialização** (prova: fixtures multi-diagram, seção 48).
- Regra determinística de abertura: **primeiro `BPMNDiagram` em document order** que referencie um `bpmnElement` existente; fallback = primeiro document order.
- Quando `listDiagrams().length > 1`: **seletor de diagrama** visível (dropdown no header: "Diagrama: {name|id}") + aviso informativo "este arquivo contém N diagramas — os demais são preservados".
- Edição aplica-se ao diagrama selecionado; trocar de diagrama mantém o mesmo save point/command stack global do artefato (undo/redo seguem o artefato inteiro).
- **Criação de novos `BPMNDiagram` pela UI = `OUT_OF_V1`** (vendor não oferece nativamente; sem requirement). Import de multi-diagrama: preservar todos — nunca descartar.

## 48. Frontend Interoperability Fixture Matrix

`FROZEN` — mapeamento dos fixtures do Prompt 3 para o editor (o catálogo não é redefinido; cada família recebe outcome frontend esperado):

| Fixture family (P3) | CAN IMPORT | CAN RENDER | CAN EDIT | READ_ONLY | CAN SERIALIZE | PRESERVATION EXPECTED | UI DIAGNOSTIC |
|---|---|---|---|---|---|---|---|
| FX-BLANK-001 | n/a (create) | sim | sim | — | sim | — | canvas vazio |
| FX-VALID-001/002 | sim | sim | sim | — | sim | TEXT_EQUAL opaco / STRUCTURALLY_EQUIVALENT | — |
| FX-NODI-001/002 | sim | sim (layout transitório) | sim | — | sim | semântica preservada | banner "layout não salvo"; BPMNDI-001/007 no painel |
| FX-BADXML-001/002 | intake rejeita | n/a | — | — | — | — | erro MALFORMED_XML + posição |
| FX-NOTBPMN-001 | intake rejeita | — | — | — | — | — | erro XML_NOT_BPMN |
| FX-NS-001/002/003 | rejeita ou reconhece c/ issues | conforme caso | conforme caso | — | — | — | BPMN-REC-002/004 |
| FX-SEC-001..006 | `INPUT_REJECTED_SECURITY` / `NON_XML` (005) | n/a | — | — | — | — | diagnóstico de segurança específico |
| FX-REF-* (broken refs) | sim | sim | sim (reparo permitido) | — | sim | preservado | issues STRUCT-010..015 navegáveis |
| FX-FLOW/GW/BND/LINK-* | sim | sim | sim | — | sim | preservado | issues SEM-* |
| FX-DI-* | sim | sim | sim | — | sim | preservado | issues BPMNDI-* |
| FX-EXT-001/002 (unknown ext) | sim | sim | sim | — | sim | **extensões preservadas** | INFO "conteúdo preservado" |
| FX-EXT-003 (`mustUnderstand`) | sim | sim | **não** | **sim** | sim (export) | preservado | banner capability failure; EDIT deny/SAVE blocked |
| FX-PRESERVE-* (constructs preserve-only) | sim | sim quando vendor suporta | edição estrutural negada; artefato editável se gate passar | parcial | sim | preserve-only intacto | badges + inspector genérico |
| FX-PROFILE-* (CREATE_EDIT families) | sim | sim | sim | — | sim | round-trip no editor | — |
| Multi-`BPMNDiagram` (derivado de FX-DI) | sim | sim (seletor) | sim no selecionado | — | sim | **todos os diagramas preservados** | seletor + aviso N diagramas |
| Editor incapaz de importar artefato reconhecido | — | falha | — | **sim (fallback)** | backend export | backend preserva | `EDITOR_CAPABILITY_FAILURE` |

Cobertura: 100% das famílias de fixtures frontend-relevantes do Prompt 3 mapeadas.

## 49. Component Boundary Map

`FROZEN` — composição mínima (Abstraction Gate aplicado; nomes de trabalho, podem refinar mantendo boundaries):

```text
plugins/bpmn-modeler/src/
  manifest + App.tsx + routes                    → entry MFE (convenção dos plugins)
  pages/
    ModelLibraryPage                             → seção 18
    ModelEditorPage                              → shell do editor (seções 43/38)
    RevisionViewPage                             → seção 24
  components/
    EditorToolbar, SaveStatus, ReadOnlyBanner,
    ConflictDialog, UnsavedChangesGuard,
    ImportDialog, CreateModelDialog, ExportMenu,
    SearchOverlay, DiagramSelector,
    SidePanel (Properties | Validation | History)
    ValidationPanel, IssueList, RevisionHistoryList
  editor/
    BpmnEditorAdapter                            → seção 7 (única porta vendor)
    modules/ (palette/contextPad/rules/replace/readonly providers)
    inspector/ (read-only properties viewer)
  data/api/bpmnModelerApi.ts                     → convenção existente
  state/ (saveMachine, capabilities, reports)    → seções 11/12/44
```

Anti-padrões vedados: um componente por botão; um hook por campo; um Context por concern sem benefício; qualquer componente fora de `editor/` tocando APIs vendor.

## 50. Frontend Test Contract

`FROZEN` — suites a implementar (vitest + testes de integração; E2E global → Prompt 7):

- **unit:** save state machine (todas as transições §12), dirty contract (save point/undo), route guards de unsaved-changes, mapeamento de erros vendor→produto.
- **component:** library (empty/loading/error/rows/actions), dialogs (create/import/conflict/restore), painéis (validation list, history), banners read-only.
- **editor integration (browser/harness):** mount/destroy; importXml/exportXml; dirty/save point; undo/redo; read-only (NavigatedViewer sem mutações); properties change; issue→element navigation; **unknown extension preservation (FX-EXT round-trip no editor)**; preserve-only intacto; BPMN sem DI com layout transitório; **multi-diagrama: abrir, selecionar, preservar todos**; serialization estável (`format:false`); `markSaved`/`isDirty` corretos.
- **keyboard:** matriz da seção 32 executável.
- **accessibility smoke:** foco, nomes acessíveis, navegação de issues por teclado, estados textuais.
- **E2E:** import→edit→save→reopen→export; conflict; restore — escopo E2E final → Prompt 7.

## 51. Delegations to Prompts 5/6/7

| Prompt | Escopo delegado (não decidido aqui) |
|---|---|
| **5** | engine/algoritmo de auto-layout, geração de geometria DI, routing, métricas de qualidade, **mecânica interna do preview** (snapshot vs command vs re-import) |
| **6** | permission strings exatas, CSP/security headers, limites de upload físicos, runtime env, logging/observabilidade, **lock de versões** dos packages, packaging/deploy |
| **7** | rotas/DTOs HTTP, status codes, representação de concorrência no transporte, filename headers/sanitização, E2E final e aceitação |

## 52. Open Questions

Nenhuma questão frontend/editor/UX crítica aberta — host, editor, adapter, ownership, XML flow, dirty/save/conflict, page map, read-only, revisions, validação, preservação, properties/palette/shortcuts, export, auto-layout UX, acessibilidade, tablet e multi-diagrama estão decididos. Pendentes são exclusivamente HOW com dono em Prompts 5/6/7 (seção 51).

## 53. Specification Freeze Status

- [x] Host frontend identificado (`plugins/bpmn-modeler` MFE no portal federado)
- [x] Editor selecionado (bpmn-js 18.x `Modeler` + `NavigatedViewer`; licença/badge registrada)
- [x] Packages principais selecionados (bpmn-js, bpmn-moddle, properties-panel — matriz §6)
- [x] Vendor boundary fechado (`BpmnEditorAdapter`; leakage confinado a `src/editor/`)
- [x] State ownership fechado (React/App vs Editor vs Backend)
- [x] Canonical XML flow fechado (authoritativeXml / working state / saveCandidate + read-back)
- [x] Dirty semantics fechado (command stack + save point)
- [x] Save state machine fechada (CLEAN/DIRTY/SAVING/SAVE_FAILED/CONFLICT/READ_ONLY/LOADING)
- [x] Conflict UX fechado (reload latest / export local / permanecer — sem merge, sem force overwrite)
- [x] Unsaved-change UX fechado (dialog + beforeunload)
- [x] Page map fechado (library / editor / revision view; dialogs para create/import; painel para histórico)
- [x] Library UX fechado (tabela, colunas, ações, estados)
- [x] Create/Import UX fechado (display_name explícito; recognition states)
- [x] Read-only fechado (NavigatedViewer único; motivos parametrizados)
- [x] Revision UX fechado (painel histórico + rota read-only + restore append-only)
- [x] Validation UX fechado (painel, estágios visíveis, navegação por referência, overlays)
- [x] Preservation UX fechado (INFO → banner capability → read-only gate)
- [x] Properties/palette/context pad/replace fechados (profile CREATE_EDIT enforced)
- [x] Shortcuts fechados (matriz Win/Linux/macOS)
- [x] Export UX fechado (.bpmn backend; SVG renderer; PNG client-side)
- [x] Auto-layout UX fechado (preview reversível; accept→DIRTY; sem auto-save)
- [x] Accessibility/device behavior fechado (shell-level garantido; vendor-dependent honesto; tablet read-only por layout)
- [x] Multiple BPMNDiagrams fechado (seletor; primeiro document order; preservar todos; criar novo = OUT_OF_V1)
- [x] Fixture compatibility mapeada (§48, 100% das famílias frontend-relevantes)
- [x] Nenhuma decisão frontend crítica aberta ao implementador

```text
FRONTEND / EDITOR / UX SPEC STATUS:
FROZEN
```
