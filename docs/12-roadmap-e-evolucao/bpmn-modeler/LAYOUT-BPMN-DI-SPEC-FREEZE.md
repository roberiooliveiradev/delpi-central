# BPMN Modeler — V1 Layout / BPMN-DI / Auto-Layout Specification Freeze

> Documento canônico da V1 para auto-layout, geração de BPMN-DI, proposta de geometria, roteamento de edges, preview, Accept/Cancel e qualidade de layout.
> Status alvo: `FROZEN` — ver seção 48.
> Sequência: **PROMPT 5/7** — depende de `V1-SCOPE-FREEZE.md`, `BACKEND-DOMAIN-SPEC-FREEZE.md`, `BPMN-INTEROPERABILITY-SPEC-FREEZE.md` e `FRONTEND-EDITOR-UX-SPEC-FREEZE.md`; não reabre nenhum deles.

## 1. Purpose

Fechar integralmente o HOW de geometria da V1: engine de layout, local de execução, contrato de entrada/saída, geração de BPMN-DI, tratamento de BPMN sem DI e DI parcial, comportamento de pools/lanes/subprocesses/boundary events, roteamento, labels, múltiplos `BPMNDiagram`, mecânica de preview, semântica de Accept/Cancel/Undo/Redo, eligibility/blocking, qualidade, determinismo e fixtures. Nenhuma decisão de layout pode ficar aberta ao implementador.

## 2. Frozen Inputs

| Documento | Decisões herdadas relevantes |
|---|---|
| `V1-SCOPE-FREEZE.md` | auto-layout `IN_V1`; BPMN sem DI = legítimo; desktop edição / tablet read-only |
| `BACKEND-DOMAIN-SPEC-FREEZE.md` | save explícito; backend não injeta DI; artefato opaco persistido |
| `BPMN-INTEROPERABILITY-SPEC-FREEZE.md` | BPMN-DI no mesmo XML canônico; DI validation rules (BPMNDI-*); `waypoint ≥ 2`; preservation; blank artifact já contém `BPMNDiagram`+`BPMNPlane` |
| `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` | `BpmnEditorAdapter`; preview UX (banner Aceitar/Cancelar); `Organizar diagrama`; Accept → DIRTY; `fitViewport`; multi-diagram (seletor, primeiro document order); sem save automático |

Princípios preservados: BPMN XML = semântica canônica; BPMN-DI = geometria canônica no mesmo artefato; layout calculado ≠ geometria persistida; preview ≠ save; viewport ≠ BPMN-DI; nenhum JSON visual persistido; save explícito; Accept → DIRTY → save explícito.

## 3. Prompt 4 Dirty-State Correction

`FROZEN` — correção aplicada neste prompt ao `FRONTEND-EDITOR-UX-SPEC-FREEZE.md`:

- Contrato corrigido: dirty/save-point tracking = **estado mantido pelo `BpmnEditorAdapter` a partir de APIs/eventos públicos** do command stack (`commandStack.changed` com `trigger` ∈ `execute | undo | redo | clear`; contador `position`/`savedPosition` interno ao adapter).
- **Proibido** acessar `commandStack._stack`, `commandStack._stackIdx` ou qualquer membro privado do vendor para determinar dirty state — nos docs e na implementação.
- O documento do Prompt 4 foi atualizado nesta mesma entrega (linhas do contrato de dirty, matriz de transições e assinatura `isDirty`).

## 4. Existing Layout Inventory

Inventário real do monorepo: **nenhuma** dependência de layout engine (`elkjs`, `dagre`, `graphviz`/`viz.js`, `gojs`, `yfiles`, `jointjs`) existe em nenhum `package.json` do repo — a escolha é dependência nova. Único canvas existente: `@xyflow/react` no `FlowchartEditor` (Transformômetro, `flowchart_v1` JSON — sem layout automático e fora de escopo). Runtime target: browsers modernos suportados pelo portal (Vite/React 19); Web Worker disponível; bpmn-js 18.x selecionado no Prompt 4.

## 5. Layout Engine Decision

`FROZEN`.

**SELECTED AUTO-LAYOUT ENGINE: `elkjs` — ELK Layered algorithm** (registry `0.12.0`, pacote `elkjs`, upstream Eclipse Layout Kernel).

Prova contra requisitos:

| Requirement | Evidência |
|---|---|
| Hierarchical/layered com direção | ELK `layered` (Sugiyama) é o algoritmo flagship — fluxo BPMN direcionado |
| Compound nodes (pools/lanes/subprocess expandido) | grafos hierárquicos nativos (children aninhados com bounds próprios) |
| Swimlanes | compound containment + layout options por nível |
| Ports / attachment | suporte a `ports` nativo — boundary events e endpoints em borda |
| Edge routing | `elk.edgeRouting: ORTHOGONAL` disponível no layered |
| Worker | `elk-worker.min.js` + `workerUrl` suportado out-of-box |
| Determinismo | engine determinística dada mesma entrada/opções; `randomSeed` configurável |
| Sem backend | JS puro (GWT-compiled) — roda no browser |
| Licença | EPL-2.0 OR GPL-3.0-or-later — **escolhemos o ramo EPL-2.0** (weak copyleft, amplamente usado em ferramentas comerciais); sem custo |

**REJECTED:**

| Engine | Motivo |
|---|---|
| `@dagrejs/dagre` 3.x (MIT) | sem compound/hierarchical containers adequados a pools/lanes; sem ports; sem orthogonal routing nativo; sem worker oficial |
| Graphviz/viz.js | `dot` hierárquico mas sem compound/swimlanes/ports adequados a BPMN; integração WASM pesada |
| yFiles | comercial — sem requirement/custo aprovado |
| GoJS | comercial — idem |
| JointJS+ | comercial; core OSS não cobre routing/compound necessários |
| `@xyflow/react` | renderer, não engine de layout; modelo paralelo proibido |

## 6. Engine Decision Matrix

| ENGINE | LICENSE | BROWSER | HIERARCHICAL | COMPOUND | PORTS | EDGE ROUTING | SWIMLANES | INCREMENTAL/FIXED | DETERMINISM | BUNDLE IMPACT | BPMN AWARE | SELECTED |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `elkjs` 0.12.0 | EPL-2.0 (escolhido) OR GPL-3.0+ | sim | layered | sim | sim | orthogonal | via compound | posições fixas por constraints | determinístico + seed | alto (GWT bundle — justificado por worker + lazy load) | não (adapter BPMN-owned) | **YES** |
| `@dagrejs/dagre` 3.1.1 | MIT | sim | layered | limitado | não | polyline/spline | não | não | determinístico | baixo | não | NO |
| Graphviz/viz.js | MIT/CPL | wasm | dot | limitado | não | spline | não | não | sim | alto | não | NO |
| yFiles | comercial | sim | sim | sim | sim | sim | sim | sim | sim | alto | não | NO (licença) |
| GoJS | comercial | sim | sim | sim | sim | sim | sim | sim | sim | médio | não | NO (licença) |
| JointJS+ | comercial | sim | parcial | sim | sim | sim | parcial | sim | sim | médio | parcial | NO (licença) |

## 7. Layout Architecture

`FROZEN` — pipeline único, BPMN-aware nas pontas e engine genérica no meio:

```text
editor BPMN structure (active BPMNDiagram)
  → semantic extraction (BPMN semantic + containment + connections)
  → layout graph construction (ELK graph — ephemeral computation model)
  → ELK Layered (engine genérica — nunca canônica)
  → BPMN geometry reconstruction (bounds/waypoints/labels)
  → LayoutProposal (transient, derived, NOT persisted)
  → preview editor OR transient DI (BPMN sem DI)
```

`NO SECOND MODEL` `FROZEN`: o ELK graph existe apenas na memória do cálculo — proibido persistir, enviar ao backend como estado canônico ou armazenar JSON paralelo de nodes/edges. Nenhuma representação de layout vira canonical.

## 8. Layout Adapter Contract

`FROZEN` — boundary conceitual: **`BpmnLayoutAdapter`** (em `plugins/bpmn-modeler/src/layout/`; o Prompt 4 isolou vendor BPMN em `src/editor/` — layout também é vendor-boundary próprio).

```text
BpmnLayoutAdapter
  calculateLayout(input: LayoutInput): Promise<LayoutProposal>
    // input: estrutura semântica do diagrama ativo + DI existente
    // output: proposta transitória — nunca persistida nem enviada ao backend
```

- O adapter extrai a estrutura do artefato/diagrama ativo via `BpmnEditorAdapter` (moddle tree read-only) ou parse semântico leve (caso BPMN sem DI — seção 15); nunca muta semântica.
- Sem persistência, sem HTTP, sem Domain. Layout é geometry-only.
- `LayoutProposal` é o único artefato de saída — transient, derived, verificado (seção 36) antes de qualquer preview.

## 9. Execution Location / Worker

`FROZEN`:

- **Execution location: frontend/browser** — bpmn-js já possui a geometria editável, preview é interativo, layout é derivado e não requer autoridade de servidor. **Backend não tem nenhum papel de layout** (seção 42 do fluxo: sem `POST /layout`).
- **Worker decision: `elkjs` Web Worker = REQUIRED na V1.** ELK pode demorar em diagramas representativos; bloquear a main thread quebraria o requisito "editor must remain interactive" do Prompt 4.
- Worker contract: **input** = ELK graph JSON serializável; **output** = ELK graph com geometria (ou erro estruturado `LAYOUT_FAILED`); **cancellation** = abort do job corrente (usuário pode cancelar cálculo — seção 43); **timeout** = limite de runtime definido em P7 após benchmark (aqui fica congelado que existe timeout + cancelamento, sem número arbitrário). Se worker indisponível no ambiente → layout degradado não é oferecido: elegibilidade nega com diagnóstico (não fallback silencioso para main thread? — decisão: **fallback para main thread é permitido apenas quando worker indisponível no ambiente**, com o mesmo contrato e progresso visível; nunca silencioso).

## 10. Input Mapping

`FROZEN` — exatamente o que entra no cálculo (do diagrama ativo):

- Elementos BPMN renderizáveis do `BPMNPlane` ativo: flowNodes (events/tasks/gateways/subprocess), data objects/stores, text annotations, groups, participants(pools)/lanes com hierarquia, subprocess expandidos (containment).
- Conexões: sequenceFlow, messageFlow, association, dataInputAssociation/dataOutputAssociation.
- Hierarquia parent/child: pool→lanes→(nested lanes→)flowNodes; subprocess expandido→children; lanes aninhadas preservadas.
- Geometria existente: `BPMNShape.Bounds` válidos (sized hints) e sizes default da seção 31 para elementos sem DI.
- Labels: presença de `BPMNLabel` + dimensões de texto quando mensuráveis (seção 30/39).
- Flags: `fixed`/obstacle para elementos fora do profile ou não compreendidos pelo mapping (seção 21/22).
- **Não enviado:** metadados de produto (Model id, display_name, revisions), ValidationReport, extensions sem efeito visual (ignoradas para geometria, preservadas no XML — seção 22).

Ordem estável de construção (determinismo, seção 34): document order dos elementos, tie-break por BPMN `id` lexicográfico.

## 11. Output / LayoutProposal

`FROZEN` — exatamente o que a proposta contém:

```text
LayoutProposal (transient, derived, never persisted)
  shapes:   bpmnElementId → { x, y, width, height }        (Bounds — canvas coords)
  edges:    flowElementId → { waypoints: [{x,y}, ...≥2] }  (BPMNEdge waypoints)
  labels:   bpmnElementId → { x, y, width, height }?       (BPMNLabel quando calculada)
  containers: pool/lane/subprocess id → { x, y, width, height }
  diagramId: id do BPMNDiagram alvo
  metrics:  QualityMetrics (seção 37)
```

E **nada além** — sem elementos semânticos, sem ids novos de semântica, sem names/types/references/extensions.

## 12. Semantic Immutability

`FROZEN`: **auto-layout altera somente BPMN-DI.** Proibido adicionar/remover/modificar qualquer elemento semântico BPMN, id, tipo, nome, referência ou extensão. Prova: comparator before/after (teste §44) — o conjunto semântico do XML antes e depois de Accept deve ser `SEMANTICALLY_EQUIVALENT` (definição do Prompt 3). Layout nunca "conserta" semântica.

## 13. Active Diagram Scope

`FROZEN`: `Organizar diagrama` atua **somente no `BPMNDiagram` ativo/selecionado** (o mesmo que o seletor de diagrama do Prompt 4 exibe). Nenhuma geometria de outros `BPMNDiagram` é tocada. Semântica: uma proposta = um diagrama.

## 14. Multiple BPMNDiagrams

`FROZEN`: com N>1 diagramas, `Organizar diagrama` layouta apenas o diagrama ativo; os demais permanecem **byte/structuralmente inalterados** conforme o serializer permitir (geometria intacta). Não existe "organizar todos" na V1. Troca de diagrama durante preview: **bloqueada** — o usuário deve Aceitar ou Cancelar primeiro (seção 18).

## 15. BPMN Without DI

`FROZEN` — fluxo técnico exato (bpmn-js não gera DI sozinho):

```text
authoritativeXml sem BPMN-DI
  → BpmnLayoutAdapter: semantic parse leve (moddle — mesma stack do editor, não parser paralelo)
  → layout graph → ELK → proposta de geometria completa
  → TRANSIENT DI construída (seção 16) e injetada no XML da sessão
  → editor importa XML com DI transitória e renderiza
```

- A DI transitória **não substitui `authoritativeXml`**, **não é enviada ao backend** e **não marca dirty** (seção 20 do Prompt 4 mantém-se).
- Banner do Prompt 4 ("layout automático não salvo") permanece visível enquanto a DI for transitória.
- **Save sem edição**: persiste o artefato **original sem DI** — `exportXml()` em sessão sem edição devolve a representação sem DI transitória (o adapter marca a DI gerada como `transient` e a exclui da serialização de save enquanto `dirty=false`/`position==savedPosition`). Persistir DI só ocorre quando a geometria foi efetivamente adotada: primeira edição de geometria do usuário **ou** `Organizar diagrama` → Accept. Transição congelada: `transient DI + dirty=false → canonical-excluded`; `primeira mutação de geometria/Accept → DI torna-se candidata canônica → DIRTY`.

## 16. Transient DI Contract

`FROZEN`:

- Produzida **antes do import do bpmn-js** (seção 15), completa o suficiente para render: `BPMNDiagram` + `BPMNPlane` (ligada ao `bpmnElement` raiz), `BPMNShape` com `Bounds` para cada elemento visual, `BPMNEdge` com `waypoints ≥ 2` para cada conexão, `BPMNLabel` quando o layout a calcula.
- IDs transitórios: gerados por `IdGenerator` frontend estável (seção 31/regra de IDs abaixo), válidos como `xsd:ID`, únicos, estáveis **dentro da sessão** (mesmo elemento → mesmo id durante a sessão, para permitir seleção/navegação consistente).
- A flag `transient` é conceito do adapter/sessão — nunca atributo no XML.

## 17. Existing / Partial DI

`FROZEN`:

- **Abertura normal com DI parcial:** nenhum auto-layout automático — o vendor renderiza o que tem DI; o painel de validação mostra os issues BPMNDI-*; `Organizar diagrama` fica disponível como ação explícita (se elegível). Se o vendor não conseguir render → `EDITOR_CAPABILITY_FAILURE` (Prompt 4).
- **`Organizar diagrama` em DI parcial:** proposta cobre **o diagrama ativo inteiro** (full proposal — não existe "preencher só o que falta" na V1; previsibilidade > mistura parcial). Geometria manual existente é substituída somente após preview + Accept — nunca automaticamente.
- **Save comum nunca normaliza DI** — sem correção silenciosa de coordenadas no backend (seção 42).

## 18. Preview Architecture

`FROZEN` — **Estratégia A: preview em editor/modeler transitório separado** (não polui command stack do editor principal):

```text
main editor (inalterado, hidden/disabled)
preview modeler (NavigatedViewer) ← XML com proposta aplicada (transient)
   banner: "Pré-visualização do layout — Aceitar | Cancelar"
   usuário: pan/zoom apenas — sem edição (seção 19)
Accept → aplica proposta no main editor como um logical command batch → DIRTY → destroy preview
Cancel → destroy preview → main editor intacto
```

Decisão sobre alternativas: **B (apply + undo de command group)** rejeitada — polui o command stack e arrisca "undo além do ponto"; **A** é a única provada a deixar o main editor bit-a-bit intacto no Cancel. XML do preview = `exportXml()` do main + proposta aplicada fora do main (serialize + patch DI + import no preview viewer).

- Durante preview: edição normal do canvas desabilitada; somente Aceitar/Cancelar/pan/zoom.
- Troca de diagrama, abrir outro modelo/revision ou navegar fora ⇒ exige Aceitar/Cancelar primeiro (guarda equivalente à de unsaved-changes); saída forçada ⇒ Cancel automático (proposta descartada — não é estado canônico).
- Diff visual avançado (overlay before/after animado): `OUT_OF_V1` — o preview já mostra a proposta; o "antes" permanece acessível via Cancel.

## 19. Accept / Cancel Semantics

`FROZEN` — acceptance requirements:

**Accept:**
- aplica a proposta no diagrama ativo do main editor como **um único logical command batch** (implementação pode gerar vários commands internos — devem compor um único passo de undo);
- `position` avança → `DIRTY`;
- banner de preview fecha; `fitViewport` aplicado uma vez (efeito visual, não persistido — seção 33);
- sem save automático; sem backend round-trip;
- DI sanity check local pós-aplicação (seção 36); falha ⇒ proposal rejeitada retroativamente, estado anterior restaurado, diagnóstico `LAYOUT_FAILED`.

**Cancel:**
- destroi a proposta e o preview viewer;
- canonical/editor model **inalterado**; dirty state **inalterado**; undo history **inalterado**; seleção do main restaurada.

## 20. Undo / Redo Contract

`FROZEN`:

- Um `Ctrl/Cmd+Z` após Accept ⇒ restaura exatamente a geometria anterior do diagrama (o command batch é um único logical step).
- Um redo ⇒ reaplica a proposta.
- Accept nunca limpa o histórico anterior do command stack.
- Teste obrigatório: Accept→undo→serialize ≡ geometria pré-layout (dentro da tolerância DI_EQUIVALENT).

## 21. Layout Eligibility

`FROZEN` — `Organizar diagrama` habilitado somente quando **todas** as condições:

- capability `EDIT` e modo editable (não read-only/archived/revision/tablet/conflict/mustUnderstand/preservation failure);
- um `BPMNDiagram` ativo existe;
- preview não está em curso;
- o mapping suporta **todos** os constructs visuais necessários do diagrama (nenhum topo/containment não-representável — seção 22);
- adapter disponível (worker ou fallback).

Não elegível ⇒ botão desabilitado + motivo legível ("somente leitura", "extensão obrigatória não suportada", "estrutura não suportada pelo layout", etc.).

## 22. Layout Blocking Rule Matrix

`FROZEN` — bloqueio por condição/rule, **não** por severity genérica:

| Condição / Rule | Layout? | Motivo |
|---|---|---|
| modelo válido | ALLOW | — |
| BPMN sem DI (`BPMNDI-001`) | ALLOW | gera proposta completa |
| DI parcial (`BPMNDI-007`) | ALLOW | proposta full-diagram |
| issues semânticos ERROR com topologia representável (SEM-002 same-pool messageFlow, SEM-004, SEM-005, SEM-006, PROD-*) | ALLOW | layout é geometria; a violação permanece para reparo |
| `BPMN-STRUCT-010` sourceRef quebrado / `011` targetRef quebrado | BLOCK (elemento afetado) | edge sem endpoint não roteável com segurança — adapter retorna `UNSUPPORTED_CONSTRUCT` |
| `BPMN-STRUCT-012` endpoint não-FlowNode | BLOCK | idem |
| sequenceFlow cruzando pool (SEM-001) | ALLOW (a edge é excluída do routing primário; preservada como obstáculo fixo no último DI conhecido ou relayout mínimo direto) | não agravar violação existente |
| DI validation ERROR (`BPMNDI-002`.. refs DI quebradas) | ALLOW (a proposta substitui a DI quebrada) | layout repara geometria |
| unknown extension sem efeito visual (`EXT-001/002/003`) | ALLOW | preservada, ignorada para geometria |
| `mustUnderstand` não suportado (`EXT-004`) | BLOCK | editor já read-only por capability |
| preservation failure / `EDITOR_CAPABILITY_FAILURE` | BLOCK | risco de perda |
| read-only (permissão/archived/revision/tablet/conflict) | BLOCK | modo não editable |
| elemento visual no DI que o mapping não compreende | `fixed obstacle` se geometria conhecida; **BLOCK** se topology/containment não representável | política segura, sem exclusão silenciosa |

## 23. Pools

`FROZEN`:

- Direção principal: **fluxo left→right**; **pools empilhados top→bottom** (ordem estável por document order + id).
- Cada pool = compound container com bounds próprios; conteúdo layoutado dentro dos bounds com padding da seção 32.
- Múltiplos pools não se sobrepõem (hard gate); message flows entre pools roteados preferencialmente **fora** dos conteúdos dos pools intermediários e cruzando fronteiras apenas conforme a semântica.
- **Black-box pool:** sem processo interno — shape atômico com bounds próprios (size default de pool vazio ou bounds existentes válidos); suporta message flows; nenhum conteúdo inventado.

## 24. Lanes / Nested Lanes

`FROZEN`:

- Lanes horizontais dentro de pool horizontal; cada lane **spana o extent do pool/processo** (comprimento total), permanece **contígua e não-sobreposta** às irmãs.
- Nested lanes = compound aninhado (lane→lane→elementos) com ownership explícita no layout graph; bounds reconstruídos bottom-up (children layoutados primeiro; lane ajusta bounds aos children + padding; pool soma as lanes).
- Engine nunca trata lane como node livre desconectado — lanes são containers, não participam do ordering do fluxo.
- Ordem das lanes preserva a ordem documental do XML.

## 25. SubProcesses / Call Activities

`FROZEN`:

- **SubProcess expandido:** compound container — children participam de nested layout com a mesma direção; bounds ajustados aos children + padding.
- **SubProcess collapsed:** shape atômico no diagrama pai; children invisíveis **não** entram no layout do pai. Se a subprocess expandida possui DI própria em outro `BPMNPlane`, ela só é layoutada quando aquela diagram/plane for o ativo.
- **CallActivity / `calledElement`:** shape atômico; o processo chamado **nunca** entra no layout do diagrama corrente.

## 26. Boundary Events

`FROZEN`:

- Boundary event **permanece anexado à fronteira da Activity** — nunca node livre.
- Mapeamento: no layout graph o boundary event é **port/attachment** da activity (constraint de posição na borda) — ELK suporta ports; onde a engine não puder fixar, o boundary event é `fixed obstacle` posicionado pelo adapter na borda da activity layoutada (reconstrução pós-engine determinística).
- **Distribuição determinística de múltiplos boundary events na mesma activity:** bottom edge, left→right, na ordem documental/id — sem overlap (hard gate).
- Edges saindo de boundary events roteam normalmente a partir do ponto de anexo.

## 27. Primary Flow Layout

`FROZEN` — o grafo primário que dirige o ranking hierárquico = **sequenceFlows + flowNodes** (events/tasks/gateways + subprocess containers). Ranking de preferências do algoritmo, em ordem:

1. direção do fluxo forward (start events próximos à origem, end events ao término — aesthetic policy, não regra BPMN);
2. minimizar crossings;
3. minimizar bends/backtracking desnecessário;
4. aspect ratio prático (ver §32 — sem hard width limit);
5. compactação.

- **Loops/back edges:** suportados pelo layered (cycle breaking interno da engine — back edges roteam como retorno, sem "remover o ciclo" nem reordenar semântica).
- **Gateways:** nodes normais de fluxo, topologia in/out preservada — o layout não inventa branching semantics.

## 28. Secondary Objects

`FROZEN` — data objects/stores, text annotations, groups **não** dirigem o ranking do fluxo principal:

- `dataObjectReference`/`dataStoreReference`: secondary node posicionado próximo ao elemento associado (dataAssociation roteia como edge secundária — seção 29), preferencialmente ao lado/oposto ao fluxo principal.
- `textAnnotation`: próxima ao alvo da `association`; sem associação = secondary node comum.
- `group`: boundary visual preservada — **não** é container semântico; geometria ajustada para englobar seus membros sem quebrar o ranking (membros layoutados no fluxo; bounds do group recalculados para envolver, respeitando padding).

## 29. Edge Routing

`FROZEN`:

- Estilo padrão: **orthogonal routing** (`elk.edgeRouting: ORTHOGONAL`) — padrão profissional BPMN.
- `BPMNEdge` ≥ 2 waypoints (hard gate); endpoints calculados como **interseções na borda** dos shapes (ports/anchor da engine) — nunca center-to-center.
- **Sequence flows:** roteiam dentro do mesmo container; dirigem o grafo primário (§27); preferência: direção forward, mínimo de bends, sem cruzar nodes, sem backtracking desnecessário; **nunca** roteados como cross-pool (violação existente tratada pela matriz §22).
- **Message flows:** edges secundárias entre pools — roteiam preferencialmente por fora do conteúdo, visualmente distinguíveis; a engine sabe que `messageFlow ≠ sequenceFlow` (edges marcadas por classe no layout graph).
- **Associations / data associations:** roteadas **depois** do fluxo principal como edges secundárias — não deformam o ordering (peso menor/rotas pós-hierárquicas).
- Labels de edge: posições calculadas pela engine quando suportadas; caso contrário o adapter posiciona deterministicamente sobre o segmento médio (owner: adapter — seção 30).

## 30. Labels

`FROZEN`:

- `BPMNLabel` existente **nunca é descartada** silenciosamente: se a engine calcula posição de label, a proposta a inclui; senão o adapter deriva posição determinística (centro do segmento médio para edges; external label abaixo do shape para events/gateways conforme convenção BPMN).
- Shape labels internas (tasks, subprocess) — posição implícita no shape, sem `BPMNLabel` separado.
- **Text size:** medida no browser com a fonte real do renderer quando o texto influencia layout (label external de evento/gateway, lane headers); método consistente com o render do bpmn-js — medição vive no adapter frontend (nunca no Domain/Application). Aproximação permitida somente quando medida indisponível, documentada no config.

## 31. Default Size Catalog

`FROZEN` — origem dos tamanhos: **defaults do vendor bpmn-js** (mesmos tamanhos que modeling/render usa) extraídos para uma tabela central única em `src/layout/` (layout config — seção 35). Proibido espalhar números; proibido inventar tamanho por uso.

| Elemento | Size source |
|---|---|
| Task / Task types | vendor default (100×80) |
| Start/Intermediate/End Events | vendor default (36×36) |
| Gateways | vendor default (50×50) |
| SubProcess collapsed | vendor default (100×80) |
| SubProcess expandido | bounds derivados dos children + padding (não tamanho fixo) |
| Participant/Pool | vendor default width (150 header lane) + extent dos children; pool vazio = default vendor |
| Lane | vendor default height (140) ajustada aos children; span = extent do pool |
| DataObject/DataStore | vendor default |
| TextAnnotation | vendor default (100×30) |
| Group | bounds derivados dos membros + padding |

IDs de DI gerados: `IdGenerator` frontend do adapter (prefixo `bpmndi_` + contador/UUID estável) — únicos, sem colisão com ids existentes, não derivados de display names, nunca sobrescrevem ids semânticos BPMN.

## 32. Spacing / Direction

`FROZEN`:

- **Direção default: `RIGHT`** (horizontal). Usuário não escolhe direção na V1; subprocess herda `RIGHT`. Import com DI vertical: preservado no open normal; `Organizar diagrama` aplica o profile padrão.
- **Layout units:** coordenadas BPMN-DI = unidade do canvas do editor (números, sem mm/px físicos; sem relação com CSS pixel/zoom).
- **Spacing centralizado** no layout config (`layout-profile-v1`), categorias: `nodeNodeSpacing`, `nodeEdgeSpacing`, `lanePadding`, `poolPadding`, `subprocessPadding`, `rankSpacing` (`layerSpacing`/`spacing.nodeNodeBetweenLayers` ELK). Valores iniciais = defaults ELK ajustados à escala dos vendor sizes; refinamento numérico permitido **somente neste config** com rationale registrado — nunca hardcode disperso.
- Sem painel de customização por usuário (`OUT_OF_V1`).

## 33. Viewport Contract

`FROZEN`:

- Zoom/scroll/center/seleção **nunca** entram em BPMN-DI nem na proposta. Auto-layout não grava viewport.
- `fitViewport` automático acontece **exatamente** em: (a) após primeiro load quando o diagrama excede a tela; (b) após `Organizar diagrama` → Accept; (c) ao trocar de `BPMNDiagram` no seletor. Fora isso, nenhum re-fit automático (não quebrar contexto do usuário).
- Layout interno usa coordenadas do model, ignorando zoom corrente.

## 34. Determinism

`FROZEN`:

- Mesma entrada + mesma `layout-profile-v1` ⇒ mesma geometria (dentro de tolerância numérica).
- Garantias: ordenação estável de nodes/edges no layout graph = **document order, tie-break por `id`**; `elk.layered` é determinístico por construção; opção `randomSeed` fixada no config para qualquer fase estocástica da engine.
- Iteração de objetos JS nunca define a ordem — o adapter serializa arrays ordenados explicitamente.
- Dois runs idênticos do mesmo artifact devem produzir `DI_EQUIVALENT` (teste §44).

## 35. Layout Profile Version

`FROZEN`:

- Toda config de layout vive em `layout-profile-v1` — objeto versionado em `src/layout/` no repositório do plugin (não em Transformômetro, não em `Model` metadata, **não** dentro do BPMN XML).
- Bump de profile (mudança de spacing/direction/options) ⇒ nova versão `layout-profile-v2` para reprodutibilidade; a proposta registra qual profile a gerou (campo interno da `LayoutProposal`, não persistido).

## 36. Geometry Verification

`FROZEN` — verificação antes do preview (proposal gate) e pós-Accept:

**Proposal gate (antes de exibir preview):**
- coordenadas finitas; width/height > 0; todo shape do diagrama mapeado; nenhum DI id gerado duplicado; toda edge com ≥2 waypoints; containers contêm seus children; 0 overlaps ilegais (hard gates §38).
- Proposta inválida ⇒ `LAYOUT_FAILED` — nunca chega ao preview nem ao main editor.

**Pós-Accept (antes de concluir Accept):**
- serialization local + DI sanity check (refs válidas, waypoints, bounds) — sem backend round-trip; validação completa permanece explícita/save.

**Normalização da proposta:** origem normalizada para coordenadas não-negativas + margem (proposals only; DI importada com coordenadas negativas válidas não é "corrigida" no open).

## 37. Quality Metrics

`FROZEN` — métricas registradas na `LayoutProposal` como evidência de teste/aceitação (não estado canônico):

bounding width · bounding height · aspect ratio · shape overlaps · edge crossings · number of bends · backward edges · pool/lane violations · runtime (medido, para benchmark P7).

## 38. Hard Quality Gates

`FROZEN`:

| Métrica | Hard gate? | Objetivo |
|---|---|---|
| shape overlap (ilegal) | sim | 0 — attachment semântico (boundary event) é exceção permitida |
| pool overlap | sim | 0 |
| lane containment violation | sim | 0 |
| invalid DI refs (shape/edge/plane→bpmnElement) | sim | 0 |
| edge com <2 waypoints | sim | 0 |
| edge crossings | não | minimizar |
| bends | não | minimizar |
| bounding area | não | compacto |
| aspect ratio | não | prático — preferência a moderar largura excessiva sem destruir legibilidade do fluxo |
| runtime | medido | benchmark em P7 |

## 39. Layout Fixture Catalog

`FROZEN` — catálogo de casos de layout (specification only; fixtures físicas derivadas do catálogo do Prompt 3 na implementação):

| ID | Propósito | DI inicial | Diagram | Constructs | Eligibility | Propriedades esperadas | Gates | Métricas | Round-trip |
|---|---|---|---|---|---|---|---|---|---|
| L01 | linear start→task→end | completa | 1 | start, task, end | ALLOW | ordem L→R | todos | w/h, bends=0 | DI_EQUIVALENT pós-accept |
| L02 | exclusive branch/merge | completa | 1 | gateway XOR | ALLOW | merge simétrico | todos | crossings | idem |
| L03 | parallel branch/merge | completa | 1 | gateway AND | ALLOW | ramos paralelos | todos | crossings | idem |
| L04 | loop/back edge | completa | 1 | seq flow retorno | ALLOW | back edge roteada | todos | backward=1 | idem |
| L05 | pools + messageFlow | completa | 1 | 2 pools | ALLOW | pools empilhados, msg externa | todos | pool overlap=0 | idem |
| L06 | pool multi-lanes | completa | 1 | 3 lanes | ALLOW | lanes contíguas full-span | todos | lane violations=0 | idem |
| L07 | nested lanes | completa | 1 | lane→lane | ALLOW | nesting preservado | todos | idem | idem |
| L08 | subprocess expandido | completa | 1 | sub + children | ALLOW | nested layout | todos | overlaps=0 | idem |
| L09 | subprocess collapsed | completa | 1 | sub collapsed | ALLOW | shape atômico | todos | — | idem |
| L10 | boundary events | completa | 1 | activity + 2 boundary | ALLOW | anexo bottom L→R | todos | sem overlap | idem |
| L11 | annotations/data | completa | 1 | dataObj, annotation | ALLOW | proximidade ao associado | todos | — | idem |
| L12 | BPMN sem DI | **nenhuma** | 1 | processo completo | ALLOW | DI transitória completa | todos | — | sem edição: artifact sem DI; pós-accept: DI persistida |
| L13 | DI parcial | parcial | 1 | mix | ALLOW | full proposal | todos | — | idem |
| L14 | multi-BPMNDiagram | 2 diagrams | ativo=#1 | — | ALLOW no ativo | diagram#2 intacto | todos | — | #2 TEXT/structural igual |
| L15 | black-box pool | completa | 1 | participant vazio | ALLOW | shape atômico | todos | — | idem |
| L16 | processo representativo | completa | 1 | 30–60 elementos | ALLOW | legível | todos | runtime | idem |

## 40. Fixture Acceptance Matrix

`FROZEN` — para cada fixture L01–L16 a suíte de teste registra: eligibility esperada, hard gates (§38) zerados, métricas coletadas (§37), round-trip esperado (§41), e para L12 a prova dupla (sem-edição ⇒ original sem DI; com-edição/accept ⇒ DI candidata persistida).

## 41. Round-trip Geometry Contract

`FROZEN`:

- Após Accept + serialize + re-import: `DI_EQUIVALENT` (mesmo conjunto de diagrams/planes/shapes/edges/labels, bounds+waypoints equivalentes na tolerância float do Prompt 3, mesmos links `bpmnElement`).
- Coordenadas negativas: proposta normalizada a origem ≥0 + margem; DI importada com negativos não é reescrita no open.
- Precisão float: sem arredondamento agressivo — serialização delegada ao serializer do vendor; tolerância conforme `DI_EQUIVALENT` (sem formatter geométrico paralelo).
- Backend nunca normaliza/repara coordenadas no save.
- Rerun de `Organizar diagrama`: nova proposta a partir do **grafo semântico corrente** — não acumula deltas do layout anterior; edições manuais pós-Accept são geometria livre normal (sem "layout ownership" escondido).

## 42. Failure Handling

`FROZEN` — categorias de erro, todas deixando o main editor intacto:

| Falha | Resultado |
|---|---|
| `UNSUPPORTED_CONSTRUCT` (topologia não representável) | elegibilidade nega / proposta rejeitada + diagnóstico |
| `LAYOUT_FAILED` (engine exception, saída inválida, proposal verification) | preview não exibido ou revertido; diagnóstico |
| timeout | cancela job, diagnóstico, editor intacto |
| usuário cancela cálculo | aborta worker job, sem efeito |
| worker indisponível | fallback main thread permitido (seção 9) ou negação com diagnóstico |

- **Sem `POST /layout`**: backend não possui autoridade de layout; backend só persiste o artefato enviado no save.
- **Save nunca reorganiza**: nem validação nem import nem save executam layout silencioso.
- **Sem conversão de formato**: pools nunca viram lanes, lanes nunca são flatten, subprocess nunca é substituído, gateways inalterados — geometry only.

## 43. Performance / Cancellation

`FROZEN`:

- Sem números inventados: runtime é **medido** (métrica §37) e benchmark/thresholds → P7.
- Requisitos qualitativos congelados: cálculo roda em worker (main thread responsiva); usuário pode **cancelar** um cálculo em andamento (botão Cancelar durante "calculando layout"); existe **timeout** configurado no profile (valor numérico → P7 após benchmark); UI mostra estado "calculando layout…" não-modal.

## 44. Test Contract

`FROZEN` — suites futuras:

- **layout unit mapping:** BPMN semântico → layout graph (sem browser quando possível): containment, ownership, classes de edge, fixed obstacles, ordem estável.
- **adapter/engine:** input ELK → saída → `LayoutProposal` válida; worker contract (in/out/cancel/timeout).
- **geometry reconstruction / DI generation:** shapes, waypoints ≥2, labels, transient DI para L12.
- **preview:** Cancel exact (editor bit-igual), Accept DIRTY, Accept = um undo, redo, sem save canônico, guards de navegação/diagrama, falha não toca main.
- **pools/lanes/subprocess/boundary:** fixtures L05–L10, L15.
- **routing:** orthogonal, endpoints em borda, msg flow externa, back edges.
- **round-trip:** DI_EQUIVALENT pós-accept; multi-diagram intacto; L12 dupla prova.
- **determinism:** mesmo input 2× ⇒ DI_EQUIVALENT.
- **performance benchmark:** L16 — registro de runtime para P7.

## 45. Package / Licensing Impact

`FROZEN` — impacto para lock no Prompt 6:

| Package | Avaliado | Licença | Nota |
|---|---|---|---|
| `elkjs` | `0.12.0` | EPL-2.0 OR GPL-3.0-or-later → **ramo EPL-2.0** | único layout package novo; `elk-worker.min.js` empacotado como asset do worker; bundle grande → lazy load sob demanda (Organizar/abertura de sem-DI) |
| nenhum outro layout package | — | — | sem dagre/graphviz/yfiles/gojs/jointjs |

Worker CSP (`worker-src`/blob), integridade de pacote e config de bundler → Prompt 6.

## 46. Delegations to Prompts 6/7

| Prompt | Escopo delegado |
|---|---|
| **6** | lock exato de `elkjs` + assets de worker, bundler/worker CSP, resource limits, observabilidade de erro de layout, integridade de dependência |
| **7** | E2E de Organizar diagrama, benchmark de performance, thresholds numéricos (timeout, runtime) — somente se evidência permitir |

## 47. Open Questions

Nenhuma questão crítica de layout/BPMN-DI aberta: engine, local de execução, worker, input/output, imutabilidade semântica, escopo por diagrama, BPMN sem DI, DI transitória/parcial, pools/lanes/subprocess/boundary, routing, preview, Accept/Cancel/Undo, eligibility/blocking, qualidade e determinismo estão decididos. Pendentes são exclusivamente de P6/P7 (seção 46).

## 48. Specification Freeze Status

- [x] Engine selecionada (elkjs 0.12.x, ELK Layered, ramo EPL-2.0)
- [x] Licença conhecida e registrada
- [x] Execution location fechada (frontend/browser; backend sem papel)
- [x] Worker decidido (REQUIRED; contrato in/out/cancel/timeout)
- [x] Layout adapter fechado (`BpmnLayoutAdapter` → `LayoutProposal` transitória)
- [x] Input/output fechados (semantic extraction → bounds/waypoints/labels/containers apenas)
- [x] Geometry-only invariant (semantic immutability + comparator)
- [x] Current diagram scope (ativo apenas; demais intactos)
- [x] BPMN sem DI fechado (transient DI pré-import; save sem edição = original sem DI)
- [x] Transient DI fechado (ids estáveis de sessão, completo para render)
- [x] Partial DI fechado (open sem auto-layout; Organizar = full proposal)
- [x] Pool/lane behavior fechado (L→R, pools T→B, lanes full-span, nested compound)
- [x] Subprocess/boundary behavior fechado (expanded compound, collapsed atômico, boundary como port/bottom-edge)
- [x] Routing fechado (orthogonal, endpoints em borda, seq primária, msg/data/assoc secundárias)
- [x] Preview implementation fechada (modeler transitório separado — Estratégia A)
- [x] Accept/Cancel fechado (logical batch único / bit-igual intacto)
- [x] Undo/redo fechado (um logical step)
- [x] Layout eligibility fechada (gate de 5 condições)
- [x] Blocking rules fechadas (matriz por condição, não severity)
- [x] Quality gates fechados (hard gates + métricas comparativas)
- [x] Determinism fechado (ordem estável + seed + arrays explícitos)
- [x] Fixtures fechadas (L01–L16 + acceptance matrix)
- [x] Nenhuma decisão crítica aberta ao implementador

```text
LAYOUT / BPMN-DI SPEC STATUS:
FROZEN
```
