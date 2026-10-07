# BPMN MODELER — V1 BPMN / VALIDATION / INTEROPERABILITY SPEC FREEZE

> **Status:** FROZEN (set/2026)
> **Produto:** Meu Modelador de Processos / BPMN Modeler
> **Bounded context:** `bpmn-modeler/` (package `bpmn_modeler`)
> **Base canônica:** `V1-SCOPE-FREEZE.md` (FROZEN, `1fa64cbe38`), `BACKEND-DOMAIN-SPEC-FREEZE.md` (FROZEN, `ba01d8b43d`)
> **Natureza:** autoridade única da V1 para BPMN recognition, validation, interoperability, round-trip, extensions, operation policy de conteúdo, validation adapter technology e fixtures. Frontend HOW → Prompt 4; geometry/layout HOW → Prompt 5; limites físicos/security/runtime → Prompt 6; transporte → Prompt 7.
> **AMENDMENT G0 (out/2026):** freeze histórico. Decisões substituídas após implementação estão marcadas `SUPERSEDED (G0)`. Estado vigente: [`CURRENT-STATE.md`](CURRENT-STATE.md); divergências: [`DOCUMENTATION-DRIFT-LEDGER.md`](DOCUMENTATION-DRIFT-LEDGER.md). O profile de escopo (seções 6–7 do Prompt 1 e regras deste documento) é **TARGET**, não prova de implementação — inventário capability-by-capability = gate G1.

Vocabulário de decisão: `FROZEN` | `DELEGATED_TO_PROMPT_4/5/6/7`.

Classificação de regras usada no catálogo: `PROVEN_NORMATIVE` (norma OMG/W3C), `PRODUCT_POLICY` (decisão de produto), `SECURITY_POLICY` (decisão de segurança), `INTEROPERABILITY_POLICY` (decisão de interop), `AMBIGUOUS`, `TO_INVENTORY`. Nenhuma regra de produto é atribuída à OMG.

---

## 1. Purpose

Fechar WHAT + HOW técnico de validação/interoperabilidade BPMN da V1: o que é reconhecido como BPMN, o que é válido/inválido/incompleto, o que pode ser importado/aberto/editado/salvo/exportado/revisionado, como stages funcionam, quais regras existem, como extensions e mustUnderstand se comportam, como preservation e round-trip são provados, qual tecnologia valida XML/BPMN no backend, como BPMN sem DI é tratado, como o blank artifact nasce e quais fixtures provam tudo isso.

## 2. Frozen Inputs

| Item | Estado |
|---|---|
| BPMN 2.0 XML = semântica canônica; BPMN-DI no mesmo artefato = geometria canônica | FROZEN |
| `CanonicalBpmnArtifact(content: str)` = representação, não validade | FROZEN |
| `BpmnArtifactValidationPort → ValidationReport` (`ValidationIssue`, `ValidationStage`, `ValidationSeverity`, `RuleSource`) | FROZEN para stage/report model; **mudança de contrato REQUIRED** na assinatura de validate — `InputSafetyEvidence` opcional (seção 24) |
| ValidationReport = evidência ≠ operation policy; preservation risk ≠ preservation proof | FROZEN |
| Domain não conhece parser; `flowchart_v1` = legado do Transformômetro; JSON visual paralelo proibido | FROZEN (enforced por `test_architecture.py`) |
| Save pipeline: validation → operation policy → persist/reject (`VALIDATION_BLOCKED`) | FROZEN (Prompt 2, seção 8) |
| CreateRevision não bloqueado por validation | FROZEN (Prompt 2, seção 11) |
| Editing profile `CREATE_EDIT`/`RENDER_PRESERVE_ONLY` | FROZEN (Prompt 1, seções 6–7) |
| Autosave OUT_OF_V1; save explícito | FROZEN |

> **SUPERSEDED (G0):** autosave do working copy foi implementado (`AutosaveController` + `SaveMachine`). O que permanece FROZEN e inalterado: o write path é `PUT working-copy` com validação/policy/read-back — o autosave apenas agenda esse mesmo write; nenhuma regra de validação/interoperabilidade muda por causa do gatilho de save.

## 3. Normative Sources

| Fonte | Uso | Referência |
|---|---|---|
| OMG BPMN 2.0.2 (formal/2013-12-09) | regras semânticas/estruturais, connection rules (Tabelas 7.3/7.4), extension mechanism (§8.2.3), exchange format (§15) | `omg.org/spec/BPMN/2.0.2/` |
| OMG machine-readable XSDs | validação estrutural | source files em `spec/BPMN/20100501/`: `BPMN20.xsd`, `Semantic.xsd`, `BPMNDI.xsd`, `DI.xsd`, `DC.xsd` (file id `dtc/10-05-04`). **Atenção: data do path dos arquivos (`20100501`) ≠ data dos XML namespaces (`20100524`)** — ver seção 37 |
| W3C XML 1.0 / XMLNS | well-formedness, namespaces | w3.org |
| Vendor docs (lxml, bpmn-moddle) | comportamento de biblioteca somente — nunca autoridade normativa | lxml.de, github.com/bpmn-io |

## 4. Recognition Model

Estados conceituais de intake (`FROZEN`):

| Estado | Significado | Cond |
|---|---|---|
| `INPUT_REJECTED_SECURITY` | input recusado na intake segura (antes ou durante) — oversize, DTD/doctype, XXE, profundidade, entity expansion | evidência de intake com check SEC-* falho; `CanonicalBpmnArtifact` nunca existe; BPMN recognition NOT_EVALUATED |
| `NON_XML` | conteúdo não pode produzir texto XML utilizável (binário, não-decodável, payload sem XML text) | falha de decode/intake antes de artifact existir — **não** é rejeição de segurança nem falha de well-formedness |
| `MALFORMED_XML` | é XML-aspirante mas falha well-formedness | XML_WELL_FORMEDNESS com issue fatal |
| `XML_NOT_BPMN` | XML bem-formado cujo root não é BPMN `definitions` no namespace BPMN 2.0 | recognition rules BPMN-REC-001/002 |
| `BPMN_RECOGNIZED_INCOMPLETE` | root é BPMN definitions mas estrutura mínima ausente/degradada (ex.: sem nenhum process/participant; falhas XSD graves) | recognized + issues estruturais |
| `BPMN_RECOGNIZED_WITH_ISSUES` | BPMN reconhecido, carrega issues (ERROR/WARNING/INFO) em stages avaliados | recognized + issues não-fatais |
| `BPMN_RECOGNIZED` | BPMN reconhecido sem issues acima de INFO | clean |

Distinções obrigatórias mantidas: `BPMN_RECOGNIZED_INCOMPLETE` ≠ `XML_NOT_BPMN` — falha XSD **não** rebaixa para "não BPMN" se root+namespace forem BPMN. Um documento é "BPMN" pela raiz expandida `{http://www.omg.org/spec/BPMN/20100524/MODEL}definitions`, não pela validade XSD.

**Rejeição de segurança não é recognition:** `INPUT_REJECTED_SECURITY` denota input recusado no intake seguro (antes ou durante). Nesse estado, BPMN recognition é `NOT_EVALUATED` — nunca afirmar `NON_XML` quando recognition não ocorreu. `NON_XML` fica restrito a conteúdo que não pode produzir texto XML utilizável (binário, não-decodável, payload sem XML text). `MALFORMED_XML` continua separado: texto XML + parse tentado + falha de well-formedness.

## 5. Validation Stage Contract

Stages congelados (contrato existente). Para cada um: o que avalia, quando EVALUATED, quando NOT_EVALUATED, prerequisitos fatais.

| Stage | Avalia | EVALUATED quando | NOT_EVALUATED quando | Prerequisito fatal |
|---|---|---|---|---|
| `INPUT_SAFETY` | checks de segurança do input original (byte size, encoding/decode, BOM, DTD/doctype, external entities, profundidade) — **consome `InputSafetyEvidence` produzida pelo input adapter** (seção 24) | evidência presente e suficiente para todas as checks habilitadas + checks executadas a termo | `InputSafetyEvidence` ausente ou insuficiente (ex.: artifact já persistido, validação de working copy/revision) — **NOT_EVALUATED por falta de evidência, não é falha nem sucesso**; falha interna do avaliador → INFRASTRUCTURE_FAILURE | stage independente — sem upstream |
| `XML_WELL_FORMEDNESS` | W3C well-formedness + namespace well-formedness sobre `CanonicalBpmnArtifact.content` | parse executado a termo (sucesso ou fatal issue) — **independe de INPUT_SAFETY**: `INPUT_SAFETY = NOT_EVALUATED` (falta de evidência) **não** impede avaliar se a str atual é XML well-formed | artifact inexistente (input rejeitado na intake, `INPUT_REJECTED_SECURITY`) ou falha interna do parser | artifact existir — é o único pré-requisito |
| `BPMN_STRUCTURE` | recognition (root/ns/targetNamespace), XSD conformance, resolução de referências estruturais (sourceRef/targetRef/endpoints/processRef/boundary attachedToRef/membership) | parse bem-sucedido + todas as regras habilitadas executadas | XML malformado (issue XML-WF fatal) | XML_WELL_FORMEDNESS fatal |
| `BPMN_SEMANTICS` | regras semânticas do profile (connection rules, gateway/boundary/default-flow/link) | índice de elementos construído + regras executadas | XML malformado; ou estrutura tão degradada que o índice semântico não pode ser construído — exige issue em BPMN_STRUCTURE avaliado explicando | fatal: índice de elementos não construível |
| `BPMN_DI` | presença de DI, referências bpmnElement/plane, cardinalidade de waypoints, cobertura de depiction | parse bem-sucedido + regras DI executadas (DI ausente conta como executada → emite BPMNDI-001) | XML malformado | XML_WELL_FORMEDNESS fatal |
| `PRODUCT_RULES` | regras de produto aprovadas (seção 28) | regras PROD-* executadas | depende do mesmo índice que BPMN_SEMANTICS → mesmas condições | índice não construível |
| `INTEGRATION_CONSTRAINTS` | regras de integração com outros contextos | nunca na V1 — **NOT_EVALUATED by design** (sem regras habilitadas) | sempre na V1 | n/a |

O pipeline **não é linear forçado**: `BPMN_SEMANTICS` e `BPMN_DI` são independentes entre si (ambos dependem de parse bem-sucedido); `PRODUCT_RULES` depende do índice semântico. Ordem de execução é detalhe de implementação; a matriz de dependência (seção 6) é o contrato.

## 6. Stage Dependency Matrix

| Stage | Depende de | Tipo de dependência | Efeito de falha/ausência no prerequisito |
|---|---|---|---|
| INPUT_SAFETY | `InputSafetyEvidence` do input adapter | evidence stage independente | evidência ausente → NOT_EVALUATED (sem falha); evidência com check falho → EVALUATED com issues SEC-* → rejeição pela operation policy |
| XML_WELL_FORMEDNESS | existência de `CanonicalBpmnArtifact.content` | hard | sem artifact (rejeição na intake) → NOT_EVALUATED; **INPUT_SAFETY NOT_EVALUATED não afeta este stage** |
| BPMN_STRUCTURE | XML_WELL_FORMEDNESS | hard | malformado → NOT_EVALUATED |
| BPMN_SEMANTICS | XML_WELL_FORMEDNESS + índice de elementos | hard (parse) + soft (índice) | índice não construível → NOT_EVALUATED + issue em STRUCTURE |
| BPMN_DI | XML_WELL_FORMEDNESS | hard | malformado → NOT_EVALUATED |
| PRODUCT_RULES | índice semântico | soft | NOT_EVALUATED quando SEMANTICS NOT_EVALUATED |
| INTEGRATION_CONSTRAINTS | n/a (V1) | — | sempre NOT_EVALUATED |

**Distinção obrigatória `FROZEN`:** `NOT_EVALUATED` por **falta de evidência** (ex.: `InputSafetyEvidence` ausente num artifact persistido) ≠ stage **EVALUATED e rejeitado** por segurança (issues SEC-* presentes → operation policy rejeita). O primeiro é ausência de dados para avaliar; o segundo é avaliação concluída com resultado negativo. Não usar os dois como sinônimos.

**Invariante de evidência `FROZEN`:** um stage só pode ser `NOT_EVALUATED` por **bloqueio** se existir ao menos um issue em stage `EVALUATED` upstream explicando a causa. Exceções legítimas sem issue upstream: `NOT_EVALUATED` por design (sem regras habilitadas — INTEGRATION_CONSTRAINTS) e `NOT_EVALUATED` por falta de evidência (INPUT_SAFETY sem `InputSafetyEvidence`). Evidência nunca fica muda sobre o motivo.

## 7. Partial Evaluation Policy

`FROZEN` — **sem mudança de contrato**:

- `EVALUATED` = todas as regras habilitadas e aplicáveis do stage executaram a termo.
- Qualquer prerequisito que impeça execução completa → `NOT_EVALUATED` (conservador; evita falsa evidência).
- Regras "não aplicáveis" ao documento (ex.: regra de messageFlow sem messageFlows presentes) não afetam a marca do stage — aplicabilidade não é avaliação perdida.
- Diagnósticos parciais de um stage bloqueado não são inventados: a causa aparece como issue no stage upstream avaliado (invariante da seção 6).
- `ValidationReport` atual (`evaluated_stages` + `not_evaluated_stages` + issues) **é suficiente para o modelo de stages**: nenhuma mudança de contrato exigida pela partial-evaluation policy. Mudança de contrato necessária por outro motivo (evidência de input) está documentada na seção 24 → `APPLICATION CONTRACT CHANGE: REQUIRED`.

## 8. Validation Rule Catalog

Catálogo V1 versionável. `rule_id != message`. Severity default; operation policy referencia a seção 10. Nenhuma regra habilitada fica sem fixture (seção 33).

### INPUT_SAFETY — família `SEC-*` (source: `SECURITY`)

Todas as checks consomem `InputSafetyEvidence` (seção 24). Sem evidência → stage `NOT_EVALUATED`, não "passou". Issues destas regras resultam em `INPUT_REJECTED_SECURITY` (intake) ou `VALIDATION_BLOCKED` (save), nunca `NON_XML`.

| RULE_ID | CLASSIFICATION | CONDITION (sobre a evidência) | SEVERITY | PREREQ |
|---|---|---|---|---|
| SEC-SIZE-001 | `SECURITY_POLICY` | `original_byte_length` > `MAX_INPUT_BYTES` (valor físico → P6) — bytes originais do upload/input | ERROR | evidência presente |
| SEC-SIZE-002 | `SECURITY_POLICY` | `canonical_utf8_byte_length` > `MAX_INPUT_BYTES` — bytes UTF-8 da str canônica (check distinto de SEC-SIZE-001: tamanho do upload ≠ tamanho da representação canônica) | ERROR | evidência presente |
| SEC-DTD-001 | `SECURITY_POLICY` | `dtd_detected` — doctype/DTD presente no input original (internal ou external subset) | ERROR | evidência presente |
| SEC-EXT-001 | `SECURITY_POLICY` | `external_entity_declarations_detected` — declaração/referência de entidade externa (XXE) no input original | ERROR | evidência presente |
| SEC-DEPTH-001 | `SECURITY_POLICY` | `depth_within_limit == false` — profundidade > `MAX_XML_DEPTH` (P6) no scan guardado do intake | ERROR | evidência presente |
| SEC-ENT-001 | `SECURITY_POLICY` | `entity_expansion_beyond_builtins_detected` — expansão de entidade além dos builtins XML (`&amp;` etc.) | ERROR | evidência presente |
| SEC-ENC-001 | `PRODUCT_POLICY` | `decode_result` indica falha de decode do input original → rejeição na intake **antes de `CanonicalBpmnArtifact` existir** (classificação `NON_XML`, não issue sobre artifact); encode original não-UTF8 decodado com sucesso é registrado na evidência, sem issue | ERROR (intake) | intake path — **não diagnosticável a partir do artifact** (a str já está decodificada) |

### XML_WELL_FORMEDNESS — família `XML-WF-*` (source: `XML_W3C`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| XML-WF-001 | `PROVEN_NORMATIVE` | documento não é XML well-formed (parse fatal: tags, root único, nesting) | ERROR | INPUT_SAFETY passou |
| XML-WF-NS-001 | `PROVEN_NORMATIVE` | violação de namespace well-formedness (prefixo não declarado, QName inválido) | ERROR | idem |

### BPMN_STRUCTURE — famílias `BPMN-REC-*` e `BPMN-STRUCT-*` (source: `OMG_BPMN`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| BPMN-REC-001 | `PROVEN_NORMATIVE` | root localName != `definitions` | ERROR | WF passou |
| BPMN-REC-002 | `PROVEN_NORMATIVE` | root namespace URI != `http://www.omg.org/spec/BPMN/20100524/MODEL` | ERROR | WF passou |
| BPMN-REC-003 | `PRODUCT_POLICY` | definitions sem nenhum process/collaboration (nada modelável) | WARNING | REC-001/002 ok |
| BPMN-REC-004 | `PROVEN_NORMATIVE` | `definitions@targetNamespace` ausente (atributo obrigatório no XSD) | ERROR | REC-001/002 ok |
| BPMN-STRUCT-001 | `PROVEN_NORMATIVE` | violação do BPMN20.xsd oficial vendored (cada erro XSD → issue) | ERROR | REC-001/002 ok |
| BPMN-STRUCT-002 | `PROVEN_NORMATIVE` | `id` duplicado no escopo do documento (xsd:ID) | ERROR | REC ok |
| BPMN-STRUCT-010 | `PROVEN_NORMATIVE` | `sequenceFlow@sourceRef` não resolve para elemento existente | ERROR | REC ok |
| BPMN-STRUCT-011 | `PROVEN_NORMATIVE` | `sequenceFlow@targetRef` não resolve | ERROR | REC ok |
| BPMN-STRUCT-012 | `PROVEN_NORMATIVE` | endpoint de sequenceFlow não é FlowNode (regras Tabela 7.3) | ERROR | refs resolvidas |
| BPMN-STRUCT-013 | `PROVEN_NORMATIVE` | `boundaryEvent@attachedToRef` não resolve ou não é Activity | ERROR | REC ok |
| BPMN-STRUCT-014 | `PROVEN_NORMATIVE` | `participant@processRef` não resolve | ERROR | REC ok |
| BPMN-STRUCT-015 | `PROVEN_NORMATIVE` | `lane`/`laneSet`/`flowElement` referência container inexistente ou ambígua | ERROR | REC ok |
| BPMN-STRUCT-016 | `PROVEN_NORMATIVE` | `messageFlow@sourceRef`/`targetRef` não resolve | ERROR | REC ok |
| BPMN-STRUCT-017 | `PROVEN_NORMATIVE` | `association`/`dataAssociation` refs não resolvem | ERROR | REC ok |
| BPMN-STRUCT-018 | `PROVEN_NORMATIVE` | `dataOutputAssociation`/`dataInputAssociation`/`itemAwareElement` refs quebradas | ERROR | REC ok |

### BPMN_SEMANTICS — família `BPMN-SEM-*` (source: `OMG_BPMN`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| BPMN-SEM-001 | `PROVEN_NORMATIVE` | sequenceFlow cruza boundary de Process (endpoints em flowElementContainers diferentes — "Message Flows" são o mecanismo inter-pool) | ERROR | índice construído |
| BPMN-SEM-002 | `PROVEN_NORMATIVE` | messageFlow conecta elementos dentro do mesmo Process/participant | ERROR | índice construído |
| BPMN-SEM-003 | `PROVEN_NORMATIVE` | `default` sequenceFlow em source que não é gateway/activity, ou default flow com `conditionExpression` | ERROR | índice construído |
| BPMN-SEM-004 | `PROVEN_NORMATIVE` | eventBasedGateway com outgoing para algo que não é intermediateCatchEvent/receiveTask | ERROR | índice construído |
| BPMN-SEM-005 | `PROVEN_NORMATIVE` | boundary event `cancelActivity=false` com eventDefinition sem variante non-interrupting (ex.: error non-interrupting não existe) | ERROR | índice construído |
| BPMN-SEM-006 | `PROVEN_NORMATIVE` | link catch event sem throw event de mesmo nome correspondente (par link quebrado) | WARNING | índice construído |
| BPMN-SEM-007 | `PROVEN_NORMATIVE` | messageFlow para/de elemento interno de pool sem process (black-box) — alvo inválido | ERROR | índice construído |
| BPMN-SEM-008 | `INTEROPERABILITY_POLICY` | sequenceFlow sem source/target em subprocess expandido vazio, ou flow orfanizado detectável | WARNING | índice construído |

### BPMN_DI — família `BPMNDI-*` (source: `OMG_BPMN_DI`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| BPMNDI-001 | `INTEROPERABILITY_POLICY` | documento sem nenhum `bpmndi:BPMNDiagram` | INFO | parse ok |
| BPMNDI-002 | `PROVEN_NORMATIVE` | `BPMNShape@bpmnElement` não resolve para BaseElement existente | ERROR | DI presente |
| BPMNDI-003 | `PROVEN_NORMATIVE` | `BPMNEdge@bpmnElement` não resolve | ERROR | DI presente |
| BPMNDI-004 | `PROVEN_NORMATIVE` | `BPMNEdge` com < 2 `di:waypoint` | ERROR | DI presente |
| BPMNDI-005 | `PROVEN_NORMATIVE` | `BPMNPlane@bpmnElement` não resolve ou aponta para tipo não-depictável (deve ser process/collaboration/subProcess/participant conforme spec) | ERROR | DI presente |
| BPMNDI-006 | `INTEROPERABILITY_POLICY` | `dc:Bounds` com width/height ≤ 0 ou coordenadas não-numéricas | WARNING | DI presente |
| BPMNDI-007 | `INTEROPERABILITY_POLICY` | elemento depictável sem shape/edge correspondente (partial depiction — legal por spec, reportado) | INFO | DI presente |
| BPMNDI-008 | `INTEROPERABILITY_POLICY` | múltiplos `BPMNDiagram` presentes (≥2) — listar ids | INFO | DI presente |
| BPMNDI-009 | `INTEROPERABILITY_POLICY` | `BPMNLabel` fora de edge/shape coerente ou sem bounds | WARNING | DI presente |

### PRODUCT_RULES — família `PROD-*` (source: `PRODUCT`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| PROD-001 | `PRODUCT_POLICY` | `subProcess` expandido sem nenhum flowElement | WARNING | índice construído |
| PROD-002 | `PRODUCT_POLICY` | `participant` sem `processRef` e com `bpmnElement` interno esperado inconsistente (black-box declarado mas com filhos de fluxo) | WARNING | índice construído |

Apenas regras com requirement V1 — sem enchimento. Preferências de UX não viram erros.

### EXTENSIONS — família `EXT-*` (source: `PRODUCT`)

| RULE_ID | CLASSIFICATION | CONDITION | SEVERITY | PREREQ |
|---|---|---|---|---|
| EXT-001 | `INTEROPERABILITY_POLICY` | `extensionElements` com elementos de namespace desconhecido | INFO | parse ok |
| EXT-002 | `INTEROPERABILITY_POLICY` | atributo namespaced (anyAttribute) desconhecido em elemento BPMN | INFO | parse ok |
| EXT-003 | `PRODUCT_POLICY` | `definitions/extension@mustUnderstand="true"` cuja `definition` QName não está no registry de extensões suportadas | WARNING | parse ok |
| EXT-004 | `INTEROPERABILITY_POLICY` | `definitions/extension` com mustUnderstand=false/ausente | INFO | parse ok |

### INTEGRATION_CONSTRAINTS

Nenhuma regra habilitada na V1 → stage `NOT_EVALUATED` by design (seção 29).

## 9. Diagnostic Semantics

`FROZEN`:

- Severities: `ERROR` | `WARNING` | `INFO` — sem `FATAL` público; "fatal" é conceito de execução de stage (prerequisito), não severity.
- `severity != operation policy`: bloqueio é por **condição/estado** (seção 10), não por threshold de severity.
- `rule_id` é identidade estável da regra; `message` é texto humano localizável — nunca usar message como identificador.
- Toda issue carrega `stage` ∈ evaluated_stages (invariante do contrato).

## 10. Operation Policy

`FROZEN` — a policy é **por condição**, não por severity:

| Condição | Effect |
|---|---|
| INPUT_SAFETY **evaluated com issue SEC-*** (evidência presente + check falho) | intake → `INPUT_REJECTED_SECURITY` (import REJECT antes de artifact); save → `VALIDATION_BLOCKED`; demais ops n/a |
| INPUT_SAFETY **NOT_EVALUATED** (evidência ausente/insuficiente) | sem efeito de bloqueio — não é falha nem sucesso; demais stages seguem seus próprios prerequisitos |
| NON_XML (input não-decodável/binário/sem texto XML) | import REJECT na intake (artifact nunca existe); save REJECT |
| MALFORMED_XML | import REJECT; save REJECT |
| XML_NOT_BPMN (root não-BPMN) | import REJECT; save REJECT |
| Reconhecido BPMN com issues estruturais/semânticas/DI (qualquer ERROR/WARNING/INFO dessas famílias) | **todas as operações permitidas** — issues são evidência, não bloqueio |
| `extension@mustUnderstand=true` não suportada (EXT-003) | import ALLOW; open/read-only ALLOW; edit DISABLED; save BLOCKED (`VALIDATION_BLOCKED`); export ALLOW; revision ALLOW |
| Stage NOT_EVALUATED por bloqueio upstream | se o upstream reconheceu BPMN (STRUCTURE avaliado, REC ok) → permitido como "recognized"; se não reconheceu → import/save REJECT |
| Stage NOT_EVALUATED by design (INTEGRATION) | sem efeito — não é bloqueio |

**Rationale `FROZEN`:** `severity == ERROR` como bloqueio universal foi rejeitado porque (a) canonical ≠ válido — o artefato pode conter issues e continuar canônico; (b) bloquear save de conteúdo com erros impediria o fluxo de reparo (import de arquivo com erro → corrigir no editor → salvar); (c) bloqueio existe para proteger o sistema (segurança), a capacidade de interpretar o que se persiste (recognition/capability) e o conteúdo do usuário (preservação), não para punir conteúdo defeituoso. `VALIDATION_BLOCKED` dispara somente por: falha de segurança, não-reconhecimento como BPMN, capability failure de mustUnderstand, ou perda de preservação detectada no save (seção 39).

## 11. Import / Open / Edit / Save / Export Matrix

`FROZEN` — nenhuma célula ambígua. `—` = não aplicável (não chega a existir model).

| Estado | IMPORT | OPEN RO | RENDER | EDIT | SAVE | EXPORT | CREATE REVISION |
|---|---|---|---|---|---|---|---|
| `INPUT_REJECTED_SECURITY` | REJECT (intake; artifact nunca existe) | — | — | — | — | — | — |
| `NON_XML` (não-decodável/binário/sem texto XML) | REJECT (intake; artifact nunca existe) | — | — | — | — | — | — |
| `MALFORMED_XML` | REJECT | — | — | — | — | — | — |
| `XML_NOT_BPMN` | REJECT | — | — | — | — | — | — |
| `BPMN_RECOGNIZED_INCOMPLETE` | ALLOW + issues | ALLOW | best-effort (definido: render do que parseou; elementos sem DI usam layout transitório) | ALLOW | ALLOW | ALLOW | ALLOW |
| `BPMN_VALID_NO_DI` | ALLOW + BPMNDI-001 | ALLOW | transient generated layout (não persistido) | ALLOW | ALLOW | ALLOW (exporta como está, sem DI se nenhum foi gerado) | ALLOW |
| `BPMN_WITH_STRUCTURAL_ERROR` | ALLOW + issues | ALLOW | best-effort (mesma policy definida em `BPMN_RECOGNIZED_INCOMPLETE`: render do que parseou + layout transitório) | ALLOW* | ALLOW | ALLOW | ALLOW |
| `BPMN_WITH_SEMANTIC_ERROR` | ALLOW + issues | ALLOW | normal | ALLOW | ALLOW | ALLOW | ALLOW |
| `BPMN_WITH_DI_ERROR` | ALLOW + issues | ALLOW | shapes/edges quebrados renderizados como conseguir; DI issues visíveis | ALLOW | ALLOW | ALLOW | ALLOW |
| `BPMN_WITH_UNKNOWN_EXTENSION` (mustUnderstand=false/ausente) | ALLOW + INFO | ALLOW | normal | ALLOW | ALLOW | ALLOW | ALLOW |
| `BPMN_WITH_UNSUPPORTED_MUSTUNDERSTAND` | ALLOW + WARNING | ALLOW | read-only render | **DENY** | **DENY** | ALLOW | ALLOW |
| `BPMN_FULLY_ACCEPTED` | ALLOW | ALLOW | normal | ALLOW | ALLOW | ALLOW | ALLOW |

*ALLOW em edit para structural error pressupõe que o editor consegue carregar; se o load do editor falhar, a UI degrada para read-only + diagnóstico (comportamento de editor → Prompt 4, sem mudar a policy).

Salvar **sempre** re-executa validation no conteúdo submetido: se o novo conteúdo não for reconhecido como BPMN ou falhar safety → `VALIDATION_BLOCKED`. Ou seja: um model pode conter issues, nunca pode conter não-BPMN.

## 12. Revision × Validation Policy

`FROZEN` (consistente com Prompt 2):

- CreateRevision **não** é bloqueado por validation — snapshot registra o estado atual, incluindo estados com issues.
- Consequência: revisões **podem** conter BPMN reconhecido com issues estruturais/semânticas/DI e extensions desconhecidas.
- Revisões **não podem** conter INPUT_REJECTED_SECURITY/NON_XML/MALFORMED/XML_NOT_BPMN na V1, porque nenhum caminho de persistência (import/save) admite esses estados — invariante de intake. Se conteúdo assim aparecer, é evidência de bypass do pipeline, não estado legítimo.
- Revisão com conteúdo mustUnderstand-unsupported pode existir (importada) e pode ser restaurada — restore replica exatamente o snapshot (edit/save subsequente cai na policy da seção 11).

## 13. BPMN Without DI Contract

`FROZEN` — sequência única:

```text
IMPORT BPMN sem DI
→ INPUT_SAFETY + WF + recognition
→ persiste artefato ORIGINAL exatamente como recebido (semântica íntegra, sem DI)
→ BPMN_DI stage avaliado → issue BPMNDI-001 (INFO: nenhum BPMNDiagram)
→ OPEN: backend entrega artefato original; editor calcula geometria transitória em memória (proposed layout não persistido) para render
→ EDIT: edições produzem DI no serializer do editor → save persiste artefato agora com DI
→ alternativa: auto-layout explícito (CALCULATE→PREVIEW→ACCEPT→SAVE) também produz DI
```

Decisões fechadas:

- DI ausente **não** bloqueia import/open/edit/save/export.
- Backend **nunca** injeta DI server-side: geração de geometria é mecânica do editor/layout (Prompt 5), persistida somente via save explícito.
- Export de model sem DI exporta sem DI (fiel ao canônico).
- `layout calculation != persisted geometry` — nada geométrico vira canônico sem save.
- Editor precisa suportar carregar BPMN sem DI (gera layout transitório) — requirement do contrato de frontend (seção 36).

> **SUPERSEDED (G0):** "persistida somente via save explícito" — na implementação vigente a persistência de DI ocorre via autosave do working copy após edições/Accept de layout. O invariante preservado é: nenhum write de geometria sem comando do editor (Accept de layout ou edição de usuário); preview e layout transitório de open **nunca** escrevem. Ver `CURRENT-STATE.md` §7.

## 14. Blank BPMN Artifact Contract

`FROZEN` — o adapter de `BlankArtifactFactoryPort` gera um documento com exatamente:

```text
XML declaration: <?xml version="1.0" encoding="UTF-8"?>
root: <bpmn:definitions>
  id="Definitions_<generated-id>"
  xmlns:xsi   = http://www.w3.org/2001/XMLSchema-instance
  xmlns:bpmn  = http://www.omg.org/spec/BPMN/20100524/MODEL
  xmlns:bpmndi= http://www.omg.org/spec/BPMN/20100524/DI
  xmlns:dc    = http://www.omg.org/spec/DD/20100524/DC
  xmlns:di    = http://www.omg.org/spec/DD/20100524/DI
  targetNamespace="urn:delpi:bpmn-modeler"
  exporter="Minha DELPI BPMN Modeler" exporterVersion="1.0"

children (nesta ordem):
  <bpmn:process id="Process_<generated-id>" isExecutable="false"/>
  <bpmndi:BPMNDiagram id="BPMNDiagram_<generated-id>">
    <bpmndi:BPMNPlane id="BPMNPlane_<generated-id>" bpmnElement="Process_<same-id>"/>
  </bpmndi:BPMNDiagram>
```

Decisões:

- Canvas nasce **vazio** (sem start event) — o usuário adiciona elementos.
- `isExecutable="false"` — produto é modelador, não engine.
- `targetNamespace` = `urn:delpi:bpmn-modeler` (URN interna estável; não é URL de rede).
- `exporter`/`exporterVersion`: metadados normativos do formato BPMN — permitidos (não são extension proprietária nem metadado de produto fora do padrão).
- IDs gerados via `IdGeneratorPort` (forma física → P6); nunca colidem.
- Um `BPMNDiagram` inicial com `BPMNPlane` ligada ao process — canvas pronto para DI.
- Template é artefato versionado do adapter (constante/template de teste); Domain nunca constrói XML.
- Blank artifact passa validação limpa (BPMN_RECOGNIZED, zero issues acima de INFO — fixture FX-BLANK-001 prova).

## 15. Extension Policy

`FROZEN` — taxonomy e comportamento por classe:

| Classe | Reconhecimento | Diagnóstico | Preservação | Edit | Save | Export | Round-trip |
|---|---|---|---|---|---|---|---|
| `extensionElements` elementos de ns desconhecido | EXT-001 INFO | listar QName+count | MUST_PRESERVE completo (seção 17) | elementos BPMN editáveis; conteúdo da extensão não é editável estruturalmente | permitido (preserva) | preserva | EXTENSION_EQUIVALENT |
| atributo namespaced desconhecido em elemento BPMN | EXT-002 INFO | listar QName | MUST_PRESERVE | idem | permitido | preserva | EXTENSION_EQUIVALENT |
| `definitions/extension` mustUnderstand=false | EXT-004 INFO | declaração listada | preservar elemento `extension` | idem | permitido | preserva | EXTENSION_EQUIVALENT |
| `definitions/extension` mustUnderstand=true suportada | — | suporte declarado (nenhuma na V1 — registry vazio) | preservar | normal | normal | normal | EXTENSION_EQUIVALENT |
| `definitions/extension` mustUnderstand=true **não** suportada | EXT-003 WARNING | PROCESSING_CAPABILITY_FAILURE | preservar | **DENY** | **DENY** | preserva | EXTENSION_EQUIVALENT |

Registry de extensões suportadas da V1: **vazio** (nenhuma extensão DELPI criada nem adotada — Prompt 1). Toda extensão namespaced desconhecida cai na política de preservação.

## 16. mustUnderstand Policy

`FROZEN`:

- `mustUnderstand="true"` + `definition` não suportada → `PROCESSING_CAPABILITY_FAILURE` — **não** é INVALID_BPMN e não é rejection de import.
- Operações (seção 11): import ALLOW (preservação é dever), open read-only ALLOW, render ALLOW, **edit DISABLED**, **save BLOCKED** (`VALIDATION_BLOCKED`), export ALLOW, revision ALLOW.
- Rationale: sem compreender a semântica exigida, mutar o artefato pode violar invariantes que o produto não enxerga — bloquear edição é a postura segura; leitura/export/preservação continuam disponíveis.
- UI comunica capability failure explicitamente (Prompt 4): "este arquivo declara extensão obrigatória não suportada — aberto somente leitura".

## 17. Preservation Contract

`FROZEN` — o que precisa sobreviver ao round-trip:

| Categoria | MUST_PRESERVE | Não exigido |
|---|---|---|
| Estrutura semântica | todo elemento BPMN reconhecido (incl. `RENDER_PRESERVE_ONLY`): QName, id, atributos normativos, conteúdo, hierarquia, ordem significativa | indentação, whitespace entre elementos |
| Referências | toda referência QName/ID resolvível (sourceRef, targetRef, processRef, bpmnElement, attachedToRef, incoming/outgoing, lane refs, associações) | forma lexical do QName quando equivalente |
| BPMN-DI | diagrams, planes, shapes, edges, labels, bounds, waypoints, bpmnElement links | precisão decimal além da representação double |
| Extensions desconhecidas | namespace URI, element QName, atributos (QName+valor), text content, children, contenção relativa (elemento dentro de extensionElements do mesmo parent) | prefix spelling, ordem de atributos, whitespace |
| Extension declarations | `definitions/extension` elements (definition QName, mustUnderstand) | — |
| XML comments | BEST_EFFORT — preservar se o serializer do editor os mantém; perda de comments não é violação de preservation | — |
| Processing instructions | OUT_OF_SCOPE — raros em BPMN; não exigidos | — |

`exact textual preservation` (bytes idênticos) é exigida **somente** no caminho de persistência opaca do backend (import→store, save→store, export→bytes). Dentro do ciclo parse→edit→serialize do editor, exige-se equivalência das categorias acima, não bytes.

## 18. Round-trip Equality Model

`FROZEN` — categorias de comparação (comparator é ferramenta de evidência, nunca modelo canônico):

| Categoria | Definição | Onde exigida |
|---|---|---|
| `TEXT_EQUAL` | bytes idênticos | backend store/export (import→read-back, save→read-back, export) |
| `SEMANTICALLY_EQUIVALENT` | mesmo conjunto de elementos BPMN com QNames, ids, atributos normativos e referências iguais, ignorando whitespace/ordem de atributos/prefix spelling | todo round-trip de editor |
| `DI_EQUIVALENT` | mesmo conjunto de diagrams/planes/shapes/edges/labels com bounds+waypoints equivalentes (tolerância float) e mesmos links bpmnElement | todo round-trip de editor |
| `EXTENSION_EQUIVALENT` | mesmo conjunto de elementos/atributos de extensão por parent, com namespace URI, QName, valores e text content iguais | fixtures com extension |
| `STRUCTURALLY_EQUIVALENT` | superset de SEMANTICALLY_EQUIVALENT + EXTENSION_EQUIVALENT + DI_EQUIVALENT | cenários mistos |

Prova de preservation (formal):
- **No-op round-trip:** IMPORT → PARSE → SERIALIZE (sem edição) → REIMPORT → COMPARE = `STRUCTURALLY_EQUIVALENT`.
- **Safe-edit round-trip:** IMPORT → EDIT propriedade conhecida → SERIALIZE → REIMPORT → COMPARE = `STRUCTURALLY_EQUIVALENT` exceto o delta editado (delta verificado separadamente).
- **Read-back de persistência:** IMPORT/SAVE → READ autoritativo → `TEXT_EQUAL` (checksum SHA-256, Prompt 2 §20).
- Preservação só é provada com round-trip — `preservation risk` reportado via EXT-*/BPMNDI-007 não é prova.

## 19. Serialization Responsibility

`FROZEN`:

```text
EDITOR (frontend)          BACKEND                         PERSISTENCE
canonical XML load    →    CanonicalBpmnArtifact (opaque) → store bytes exatos
edit in editor        →    validate (lxml + rules)         read-back checksum
serialize BPMN XML    →    operation policy → persist
                           export = bytes exatos persistidos
```

- Backend **não** resserializa XML em save/export — persistência é opaca (Prompt 2 §19).
- Parser backend existe **somente** para validation (e futura geração de evidência) — nunca para reescrever o artefato.
- Blank artifact: adapter gera via template (seção 14) — não é serializer.
- DI-less open: editor computa layout transitório; backend permanece opaco.
- Prompt 4 não pode violar: editor deve serializar BPMN 2.0 XML completo (semântica + DI) a cada save.

## 20. Selected Backend XML/BPMN Validation Stack

`FROZEN` — stack da V1:

| Papel | Tecnologia | Versão avaliada |
|---|---|---|
| XML parser | `lxml` (libxml2) — `etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, dtd_validation=False, recover=False, huge_tree=False, ns_clean=False)` | lxml 6.x (baseline avaliado set/2026; lock exato → P6) |
| XSD validator | `lxml.etree.XMLSchema` sobre XSDs OMG vendored (seção 22) — `error_log` para diagnósticos com linha/coluna | idem |
| Semantic validator | **internal rule engine próprio** sobre árvore lxml (regras BPMN-SEM-*, STRUCT refs, PROD-*, EXT-*) — Application-owned | n/a |
| DI validator | XSD (BPMNDI/DI/DC) **+** regras cross-reference/geometry próprias (BPMNDI-*), mesmo rule engine | n/a |
| Serializer backend | nenhum para o fluxo canônico (opaque persistence); lxml `tostring` apenas para evidências internas se necessário | n/a |
| Comparator (testes) | funções de comparação em código de teste (QName-set diff), sem nova dependência | n/a |

Rationale lxml: XSD 1.0 nativo (obrigatório pelos XSDs OMG), `error_log` com `line`/`column`/`domain`/`type` (alimenta `reference` e `message`), `no_network` default, proteções anti-XXE/billion-laughs em libxml2 com parser configurado, wheels multiplataforma, BSD license, manutenção ativa (lxml.de). Deploy impact: 1 dependência binária nova — monorepo não possui lxml/xmlschema em nenhum requirements (verificado).

## 21. Library Decision Matrix

| Candidata | Papel avaliado | Decisão | Motivo |
|---|---|---|---|
| `lxml` | parser + XSD validator | **SELECTED** | XSD 1.0 nativo, diagnósticos com linha/coluna, controles de segurança explícitos, performance, BSD, ativo |
| `xmlschema` (sissaschool) | XSD validator puro-Python | REJECTED | duplicaria stack de parsing; validação pura-Python mais lenta; resolução de schemaLocation precisa de hardening adicional; não cobre navegação/retenção necessária para extensions |
| `defusedxml` | parser hardening (stdlib ET) | REJECTED | sem XSD; subconjunto de proteções já cobertas pela configuração lxml escolhida; módulo `defusedxml.lxml` é exemplo, não pacote mantido |
| `xml.etree.ElementTree` (stdlib) | parser | REJECTED | sem XSD, sem `no_network`, diagnósticos pobres, manipulação de entities limitada |
| `bpmn-moddle` (JS) | backend validation | REJECTED | JS runtime inexistente no backend Python; candidato relevante apenas no frontend (Prompt 4) |
| `saxon`-like/XSD 1.1 engines | validator | REJECTED | XSD 1.0 é suficiente (OMG publica XSD 1.0); dependência JVM injustificada |

## 22. XSD Strategy

`FROZEN` — **usar XSD oficial OMG**:

- Arquivos vendored no repo do produto (recursos do validation adapter, versionados): `BPMN20.xsd`, `Semantic.xsd`, `BPMNDI.xsd`, `DI.xsd`, `DC.xsd` (de `spec/BPMN/20100501/`, OMG file id `dtc/10-05-04`) + `xml.xsd` (W3C, para o import de `http://www.w3.org/XML/1998/namespace` presente nos XSDs BPMN).
- Proveniência: cada arquivo registra separadamente no manifesto do diretório de schemas (`schemas/MANIFEST` — criado na implementação, formato → P6/P7 conforme owner): `source_url`/`source_path` oficial (`BPMN/20100501/*.xsd`), OMG `file_id`, `sha256` **e** o `targetNamespace` que o schema serve (`.../20100524/...`). A distinção path-vs-namespace é obrigatória no manifesto.
- Runtime: **zero acesso a rede** — resolver custom mapeia namespaces/schemaLocations para arquivos locais vendored; `xsi:schemaLocation` do documento do usuário é **ignorado** (validação sempre contra schemas vendored).
- Cache: schema compilado (`XMLSchema`) construído uma vez no startup/warm-up do adapter; build do schema em teste CI prova resolução offline.
- Falha de import/include na construção do schema → `INFRASTRUCTURE_FAILURE` no startup (fail closed).

## 23. XML Parser Security Requirements

`FROZEN` — requirements que a stack deve cumprir (lxml config da seção 20 cumpre; Prompt 6 ratifica limites numéricos e controles de runtime):

| Requirement | Config/Regra |
|---|---|
| External entities (XXE) | `resolve_entities=False` + SEC-EXT-001 detecta declarações — fail closed |
| DTD | `load_dtd=False`, `dtd_validation=False` + SEC-DTD-001 rejeita doctype |
| Network resolution | `no_network=True` + resolver bloqueia qualquer fetch — nunca implícito |
| XInclude | não habilitado (parser sem `xinclude`); documento com `<xi:include>` vira conteúdo desconhecido, não executado |
| Entity expansion / billion laughs | libxml2 protection ativa (sem `huge_tree`) + SEC-ENT-001 |
| Resource exhaustion | `huge_tree=False` (depth/text limits nativos) + SEC-SIZE-001/002 + SEC-DEPTH-001 (via `InputSafetyEvidence`); limites físicos exatos → P6 |
| Encoding | decodabilidade avaliada na intake (`SEC-ENC-001`, sobre `InputSafetyEvidence`): input não-decodável → `NON_XML` antes de artifact; encoding não-UTF8 decodado com sucesso é normalizado para str e registrado na evidência; BOM UTF-8 aceito e removido no decode |
| schemaLocation | usuário nunca influencia schema de validação |

## 24. Input Safety Evidence Contract

`FROZEN` — **APPLICATION CONTRACT CHANGE: REQUIRED.**

### Problema epistêmico

`CanonicalBpmnArtifact(content: str)` é uma str **já decodificada**. Ela não prova: bytes originais do upload, tamanho original em bytes, encoding original, BOM original, origem de upload/stream nem metadados de transporte. `len(content.encode("utf-8"))` mede apenas o tamanho da representação UTF-8 **atual** — nunca o `original_byte_length` do input recebido. São checks distintos (SEC-SIZE-001 vs SEC-SIZE-002); um não serve de prova do outro.

### Conceito adicionado: `InputSafetyEvidence`

`Input Adapter`
`    │`
`    ├── produz InputSafetyEvidence (antes/junto de CanonicalBpmnArtifact)`
`    ▼`
`Application validation orchestration`
`    ▼`
`BpmnArtifactValidationPort.validate(artifact, evidence)`

| Decisão | Valor `FROZEN` |
|---|---|
| Tipo/conceito | `InputSafetyEvidence` — value/contrato de evidência imutável |
| Layer | Application (contrato de aplicação), ao lado de `BpmnArtifactValidationPort` |
| Ownership | Application-owned; **produzida pelo input adapter** no boundary de intake |
| Port signature impact | `validate(artifact: CanonicalBpmnArtifact, evidence: InputSafetyEvidence \| None = None) -> ValidationReport` (ou equivalente mínimo: `ValidationContext` contendo a evidência) |
| Quem cria | input adapter, durante intake do upload/arquivo — **antes** de construir o `CanonicalBpmnArtifact` |
| Quem consome | orquestração de validação → `BpmnArtifactValidationPort` (stage INPUT_SAFETY) |
| Quando disponível | caminho de import/intake (upload). Evidência produzida mesmo quando intake falha — a falha é classificada na intake, não como issue de artifact |
| Quando indisponível | validação de artifact já persistido (working copy, revision, revalidação) — bytes originais não existem mais |
| Classificação no report | evidência ausente/insuficiente → `INPUT_SAFETY = NOT_EVALUATED` (sem issue; não é falha nem sucesso); evidência presente → stage EVALUATED, checks SEC-* emitem issues normalmente |
| Por que necessário | sem evidência o validator não pode provar nada sobre o input original — tratar como passou seria falsa evidência |
| Por que Domain não muda | `CanonicalBpmnArtifact` permanece opaco (`content: str`), sem metadata de upload — evidência é conceito de intake/validação, não de domínio |

### Campos mínimos de `InputSafetyEvidence`

Cobrem todas as checks SEC-* habilitadas — sem campos inventados:

| Campo | Prova para |
|---|---|
| `original_byte_length: int` | SEC-SIZE-001 (bytes originais do input) |
| `canonical_utf8_byte_length: int` | SEC-SIZE-002 (UTF-8 da str canônica) |
| `declared_encoding: str \| None` + `detected_encoding: str \| None` + `bom_present: bool` + `decode_result` | SEC-ENC-001 (encoding/decode do input original; falha de decode → rejeição na intake antes de artifact) |
| `dtd_detected: bool` | SEC-DTD-001 |
| `external_entity_declarations_detected: bool` | SEC-EXT-001 |
| `entity_expansion_beyond_builtins_detected: bool` | SEC-ENT-001 |
| `depth_within_limit: bool` | SEC-DEPTH-001 (scan guardado do intake contra `MAX_XML_DEPTH` → P6) |

`MAX_INPUT_BYTES`, `MAX_XML_DEPTH` e demais limites físicos continuam delegados ao Prompt 6.

### Validação de artifact persistido

É legítimo e esperado validar artifact persistido sem `InputSafetyEvidence`: `INPUT_SAFETY = NOT_EVALUATED` coexistindo com `XML_WELL_FORMEDNESS`, `BPMN_STRUCTURE`, `BPMN_SEMANTICS` e `BPMN_DI` avaliados conforme seus prerequisitos próprios. Sem nova estrutura/field em `ValidationIssue` ou `ValidationReport` — a evidência entra via parâmetro de validação, e sua ausência é expressa pelo `NOT_EVALUATED` do stage.

## 25. Structural Validation Strategy

`FROZEN`: **XSD + custom rules** — nem XSD-only nem rules-only:

- `BPMN-STRUCT-001` consome `XMLSchema.error_log` (vendored OMG schemas) → issues com linha/coluna.
- Referências QName (sourceRef/targetRef/processRef/bpmnElement/attachedToRef/etc.) **não** são verificadas pelo XSD (são `xsd:QName`, não `IDREF`) → custom rules BPMN-STRUCT-01x/02x sobre índice id→elemento construído na árvore lxml.
- Índice construído uma vez por validação e compartilhado com SEMANTICS/DI/PRODUCT.

## 26. Semantic Validation Strategy

`FROZEN`: **internal rule catalog sobre XML parseado** (sem vendor semantic validator — não existe validator semântico BPMN adequado em Python):

- Rule engine mínimo (Application-owned adapter internals, não framework): cada regra é função `rule(index) -> Iterable[ValidationIssue]` registrada com `rule_id`, `stage`, `source`, `severity` default, `applies_to` predicate.
- Execução por stage: dependências da seção 6; ordem determinística = ordem de registro por `rule_id`.
- Cada issue recebe `reference` conforme convenção da seção 30.
- Nenhuma lógica BPMN no Domain; rule engine vive no adapter de validation atrás do `BpmnArtifactValidationPort`.

## 27. BPMN-DI Validation Strategy

`FROZEN`: **XSD + cross-reference rules + geometry rules**:

- XSD cobre cardinalidades/tipos de DI (`waypoint` minOccurs=2, Bounds doubles, refs QName).
- Custom rules cobrem o que XSD não prova: resolução de `bpmnElement` (shape/edge/plane), cobertura de depiction (BPMNDI-007), múltiplos diagramas (BPMNDI-008), sanidade de bounds (BPMNDI-006/009).
- Distinção preservada: `XSD-valid DI` ≠ `DI references resolvable` — ambos verificados por caminhos diferentes.

## 28. Product Rules

`FROZEN`: somente `PROD-001` (subProcess expandido vazio → WARNING) e `PROD-002` (black-box participant inconsistente → WARNING). Nenhuma outra regra de produto na V1; preferências de UX não viram erros.

## 29. Integration Constraints

`FROZEN`: `INTEGRATION_CONSTRAINTS` = `NOT_EVALUATED` permanente na V1 standalone — sem regras habilitadas, sem catálogo inventado. Transformômetro não é integração da V1 inicial (Prompt 1 §17).

## 30. Validation Reference Convention

`FROZEN` — `ValidationIssue.reference: str | None` é suficiente; convenção obrigatória:

| Forma | Uso | Exemplo |
|---|---|---|
| `element:{bpmn-id}` | issue ligada a um elemento BPMN → navegação issue→shape | `element:Task_1a2b3` |
| `diagram:{bpmndi-id}` | issue ligada a construct DI → navegar ao diagrama/shape | `diagram:BPMNShape_9x` |
| `xml:{line}:{column}` | issue de parser/XSD com posição | `xml:42:17` |
| `extension:{prefix}:{ns-uri-hash}` ou `extension:{definition-qname}` | issue de extensão/mustUnderstand | `extension:camunda:properties` |
| `null` | issue sem localização (ex.: SEC-SIZE-001) | — |

UI resolve `element:*`/`diagram:*` para seleção no canvas quando o id existe; `xml:*` mostra posição textual. Sem hierarquia complexa.

## 31. Diagnostic Ordering

`FROZEN` — ordenação determinística de issues no `ValidationReport` (contrato de saída do adapter):

```text
stage (ordem do enum: INPUT_SAFETY → XML_WELL_FORMEDNESS → BPMN_STRUCTURE → BPMN_SEMANTICS → BPMN_DI → PRODUCT_RULES → INTEGRATION_CONSTRAINTS)
→ source (ordem do enum RuleSource)
→ rule_id (lexicográfico)
→ reference (lexicográfico, nulls last)
```

Adapters nunca devolvem ordem arbitrária — testes e UX dependem de determinismo.

## 32. Fixture Catalog

`FROZEN` — matriz de fixtures a criar na implementação (não criados neste prompt). Convenção: `FX-<GROUP>-<NNN>`.

| FIXTURE_ID | PURPOSE | INPUT CHARACTERISTICS | EXPECTED RECOGNITION | EVALUATED STAGES | NOT_EVAL STAGES | EXPECTED RULE_IDS | SEVERITIES | IMPORT | OPEN/EDIT | SAVE | EXPORT | ROUND-TRIP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FX-BLANK-001 | blank artifact | saída de BlankArtifactFactoryPort | BPMN_RECOGNIZED | todos exceto INTEGRATION | INTEGRATION | BPMNDI-007 (elementos ainda não existem → nenhuma issue além de possíveis INFO) | ≤INFO | n/a (create) | sim | sim | sim | TEXT_EQUAL no store; STRUCTURALLY_EQUIVALENT editor |
| FX-VALID-001 | happy path | processo 1 pool, 3 tasks, seq flows, DI completo | BPMN_RECOGNIZED | todos exceto INTEGRATION | INTEGRATION | nenhuma | — | ALLOW | ALLOW | ALLOW | ALLOW | STRUCTURALLY_EQUIVALENT |
| FX-VALID-002 | collaboration | 2 pools, message flow, lanes aninhadas, black-box | BPMN_RECOGNIZED | todos exceto INTEGRATION | INTEGRATION | nenhuma | — | ALLOW | ALLOW | ALLOW | ALLOW | STRUCTURALLY_EQUIVALENT |
| FX-NODI-001 | sem DI | FX-VALID-001 sem bloco bpmndi | BPMN_RECOGNIZED | todos exceto INTEGRATION | INTEGRATION | BPMNDI-001 | INFO | ALLOW | ALLOW | ALLOW | ALLOW (sem DI) | semântico preservado; DI gerado pelo editor |
| FX-NODI-002 | DI parcial | parte dos elementos sem shape | BPMN_RECOGNIZED_WITH_ISSUES | idem | idem | BPMNDI-007 | INFO | ALLOW | ALLOW | ALLOW | ALLOW | STRUCTURALLY_EQUIVALENT |
| FX-BADXML-001 | malformado | tag não fechada | MALFORMED_XML | INPUT_SAFETY, XML_WELL_FORMEDNESS | demais | XML-WF-001 | ERROR | REJECT | — | — | — | n/a |
| FX-BADXML-002 | truncado | documento cortado | MALFORMED_XML | idem | idem | XML-WF-001 | ERROR | REJECT | — | — | — | n/a |
| FX-NOTBPMN-001 | XML não-BPMN | root `<note>` | XML_NOT_BPMN | até BPMN_STRUCTURE | demais | BPMN-REC-001 | ERROR | REJECT | — | — | — | n/a |
| FX-NS-001 | ns BPMN errado | definitions com ns diverso | XML_NOT_BPMN | idem | idem | BPMN-REC-002 | ERROR | REJECT | — | — | — | n/a |
| FX-NS-002 | sem targetNamespace | definitions BPMN sem targetNamespace | BPMN_RECOGNIZED_WITH_ISSUES | todos exceto INTEGRATION | INTEGRATION | BPMN-REC-004 (+XSD) | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-SEC-001 | doctype | `<!DOCTYPE>` no input | INPUT_REJECTED_SECURITY | INPUT_SAFETY | demais (artifact nunca existe) | SEC-DTD-001 | ERROR | REJECT | — | — | — | n/a |
| FX-SEC-002 | XXE | `<!ENTITY xxe SYSTEM ...>` | INPUT_REJECTED_SECURITY | INPUT_SAFETY | demais (artifact nunca existe) | SEC-EXT-001, SEC-DTD-001 | ERROR | REJECT | — | — | — | n/a |
| FX-SEC-003 | oversize | > MAX_INPUT_BYTES | INPUT_REJECTED_SECURITY | INPUT_SAFETY | demais (artifact nunca existe) | SEC-SIZE-001 (+SEC-SIZE-002 se str canônica também exceder) | ERROR | REJECT | — | — | — | n/a |
| FX-SEC-004 | profundidade | aninhamento > MAX_XML_DEPTH (gerado no teste) | INPUT_REJECTED_SECURITY | INPUT_SAFETY | demais (artifact nunca existe) | SEC-DEPTH-001 | ERROR | REJECT | — | — | — | n/a |
| FX-SEC-005 | encoding inválido | bytes não-decodáveis como XML text (gerado no teste) | NON_XML | INPUT_SAFETY | demais (artifact nunca existe) | SEC-ENC-001 | ERROR | REJECT | — | — | — | n/a |
| FX-SEC-006 | entity expansion | expansão além de builtins (gerado no teste) | INPUT_REJECTED_SECURITY | INPUT_SAFETY | demais (artifact nunca existe) | SEC-ENT-001 | ERROR | REJECT | — | — | — | n/a |
| FX-REF-001 | sourceRef quebrado | seq flow → id inexistente | BPMN_RECOGNIZED_WITH_ISSUES | todos exceto INTEGRATION | INTEGRATION | BPMN-STRUCT-010 (+XSD possível) | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-REF-002 | targetRef quebrado | idem target | idem | idem | idem | BPMN-STRUCT-011 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-REF-003 | endpoint inválido | seq flow → elemento não-FlowNode | idem | idem | idem | BPMN-STRUCT-012 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-REF-004 | processRef quebrado | participant → process inexistente | idem | idem | idem | BPMN-STRUCT-014 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-REF-005 | attachedToRef inválido | boundary → não-Activity | idem | idem | idem | BPMN-STRUCT-013 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-FLOW-001 | seq flow entre pools | tasks em 2 pools ligadas por sequenceFlow | idem | idem | idem | BPMN-SEM-001 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-FLOW-002 | messageFlow mesmo pool | dentro de um process | idem | idem | idem | BPMN-SEM-002 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-GW-001 | eventBased inválido | outgoing → task | idem | idem | idem | BPMN-SEM-004 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-GW-002 | default flow inválido | default em task comum sem condições + conditionExpression no default | idem | idem | idem | BPMN-SEM-003 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-DI-001 | shape bpmnElement quebrado | BPMNShape → id inexistente | idem | idem | idem | BPMNDI-002 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-DI-002 | edge bpmnElement quebrado | BPMNEdge → id inexistente | idem | idem | idem | BPMNDI-003 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-DI-003 | edge 1 waypoint | BPMNEdge com 1 waypoint | idem | idem | idem | BPMNDI-004 | ERROR | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-DI-004 | múltiplos diagramas | 2 BPMNDiagram válidos | BPMN_RECOGNIZED_WITH_ISSUES | idem | idem | BPMNDI-008 | INFO | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-DI-005 | partial depiction | 2 tasks, 1 sem shape | idem | idem | idem | BPMNDI-007 | INFO | ALLOW | ALLOW | ALLOW | ALLOW | preservado |
| FX-EXT-001 | ext desconhecida (elements) | extensionElements com ns vendor | BPMN_RECOGNIZED_WITH_ISSUES | idem | idem | EXT-001 | INFO | ALLOW | ALLOW | ALLOW | ALLOW | EXTENSION_EQUIVALENT |
| FX-EXT-002 | ext attr desconhecido | atributo ns vendor em task | idem | idem | idem | EXT-002 | INFO | ALLOW | ALLOW | ALLOW | ALLOW | EXTENSION_EQUIVALENT |
| FX-EXT-003 | mustUnderstand=true | definitions/extension mustUnderstand + extensionElements do vendor | BPMN_RECOGNIZED_WITH_ISSUES | idem | idem | EXT-003 | WARNING | ALLOW | RO only | DENY | ALLOW | EXTENSION_EQUIVALENT |
| FX-EXT-004 | mustUnderstand=false | declaração + uso | idem | idem | idem | EXT-004 (+EXT-001) | INFO | ALLOW | ALLOW | ALLOW | ALLOW | EXTENSION_EQUIVALENT |
| FX-PRESERVE-001 | preserve-only constructs | complex gateway, ad-hoc/transaction/event subprocess, data input/output | BPMN_RECOGNIZED_WITH_ISSUES | idem | idem | nenhuma ERROR (profile respeita) | ≤WARNING | ALLOW | ALLOW (render-only nesses elementos) | ALLOW | ALLOW | STRUCTURALLY_EQUIVALENT |
| FX-RT-001 | no-op round-trip | FX-VALID-002 | — | — | — | — | — | — | — | — | — | STRUCTURALLY_EQUIVALENT |
| FX-RT-002 | safe-edit round-trip | FX-VALID-001 + rename task + add extension fixture | — | — | — | — | — | — | — | — | — | STRUCTURALLY_EQUIVALENT + delta verificado |

## 33. Rule-to-Fixture Matrix

Cobertura 100% das regras habilitadas. Grupo `→` fixture(s):

| Stage/Rules | Fixtures |
|---|---|
| SEC-SIZE-001 | FX-SEC-003 (original_byte_length > limite) |
| SEC-SIZE-002 | FX-SEC-003 (mesmo input; check independente sobre canonical_utf8_byte_length) |
| SEC-DTD-001 | FX-SEC-001, FX-SEC-002 |
| SEC-EXT-001 | FX-SEC-002 |
| SEC-DEPTH-001 | FX-SEC-004 (gerado no teste) |
| SEC-ENC-001 | FX-SEC-005 (gerado no teste — classificação `NON_XML`, intake-only) |
| SEC-ENT-001 | FX-SEC-006 (gerado no teste) |
| XML-WF-001 | FX-BADXML-001/002 |
| XML-WF-NS-001 | fixture prefixo não declarado (FX-NS-003) |
| BPMN-REC-001/002 | FX-NOTBPMN-001, FX-NS-001 |
| BPMN-REC-003 | fixture definitions vazio de processos (FX-REC-001) |
| BPMN-REC-004 | FX-NS-002 |
| BPMN-STRUCT-001 | FX-REF-*, FX-DI-003, FX-NS-002 (qualquer violação XSD) |
| BPMN-STRUCT-002 | fixture id duplicado (FX-DUP-001) |
| BPMN-STRUCT-010/011/012 | FX-REF-001/002/003 |
| BPMN-STRUCT-013/014 | FX-REF-005/004 |
| BPMN-STRUCT-015 | fixture lane flowElementRef quebrado (FX-REF-006) |
| BPMN-STRUCT-016/017/018 | fixtures refs quebradas de message/association/dataAssociation (FX-REF-007/008/009) |
| BPMN-SEM-001/002 | FX-FLOW-001/002 |
| BPMN-SEM-003 | FX-GW-002 |
| BPMN-SEM-004 | FX-GW-001 |
| BPMN-SEM-005 | fixture boundary error non-interrupting (FX-BND-001) |
| BPMN-SEM-006 | fixture link catch órfão (FX-LINK-001) |
| BPMN-SEM-007 | fixture messageFlow para nó interno de black-box pool (FX-FLOW-003) |
| BPMN-SEM-008 | FX-PRESERVE-001 (event subprocess) + fixture orfão (FX-FLOW-004) |
| BPMNDI-001 | FX-NODI-001 |
| BPMNDI-002/003/004 | FX-DI-001/002/003 |
| BPMNDI-005 | fixture plane bpmnElement inválido (FX-DI-006) |
| BPMNDI-006/009 | fixture bounds degenerado/label órfão (FX-DI-007) |
| BPMNDI-007 | FX-DI-005 |
| BPMNDI-008 | FX-DI-004 |
| PROD-001 | fixture subprocess expandido vazio (FX-PROD-001) |
| PROD-002 | fixture participant sem processRef com filhos (FX-PROD-002) |
| EXT-001/002/003/004 | FX-EXT-001/002/003/004 |

Fixtures "gerados no teste" (FX-SEC-004..006 — EXPECTED_* explícitos na tabela da seção 32; FX-NS-003, FX-REC-001, FX-DUP-001, FX-REF-006..009, FX-BND-001, FX-LINK-001, FX-FLOW-003/004, FX-DI-006/007, FX-PROD-001/002) são variantes mínimas derivadas dos arquivos-base — mesmos EXPECTED_* da linha correspondente da família.

## 34. BPMN Element-to-Fixture Matrix

Todo construct `CREATE_EDIT`/`RENDER_PRESERVE_ONLY` (Prompt 1) mapeado para fixture que prova round-trip:

| Construct (profile) | Fixture |
|---|---|
| Task, User/Service/Manual/BusinessRule/Script/Send/Receive Task | FX-PROFILE-ACT (fixture composto: um processo com todos os task types) |
| Call Activity | FX-PROFILE-ACT |
| SubProcess collapsed + expanded | FX-PROFILE-ACT (expanded contém elementos internos) |
| Start (None/Message/Timer/Signal), Catch (Message/Timer/Signal/Link), Boundary (Message/Timer/Error/Signal/Escalation int+non-int), Throw (None/Message/Signal/Escalation/Link), End (None/Message/Error/Signal/Escalation/Terminate) | FX-PROFILE-EVT (fixture composto cobrindo todas as posições CREATE_EDIT) |
| Gateways Exclusive/Parallel/Inclusive/Event-Based | FX-PROFILE-GW (com outgoing válidos) |
| Sequence/Message/Association/DataAssociation flows | FX-PROFILE-FLOW + FX-VALID-002 |
| Pool/Participant, múltiplos pools, nested lanes, black-box pool | FX-VALID-002 |
| Data Object/Data Store/Annotation/Group | FX-PROFILE-ART |
| Complex Gateway (preserve-only) | FX-PRESERVE-001 |
| Ad-hoc/Transaction/Event SubProcess (preserve-only) | FX-PRESERVE-001 |
| Data Input/Data Output (preserve-only) | FX-PRESERVE-001 |
| Preserve-only event definitions (conditional/compensation/cancel/multiple/parallel-multiple) | FX-PRESERVE-002 |

FX-PROFILE-* e FX-PRESERVE-002 são arquivos `.bpmn` compostos a criar na implementação; cada construct listado tem presença garantida na fixture indicada — a coverage matrix do teste falha se um construct do profile estiver ausente.

## 35. Library Proof Matrix

| Requirement | Library capability | Evidence | Proving fixture/test |
|---|---|---|---|
| Secure XML parse | lxml parser flags (`resolve_entities=False`, `no_network`, `load_dtd=False`) | lxml.de parsing docs | FX-SEC-* |
| XSD 1.0 validation | `etree.XMLSchema` + `error_log` | lxml.de validation docs | FX-REF-* + valid fixtures |
| Line/column diagnostics | `error_log.line/.column` | lxml docs | issues `xml:*` |
| QName/namespace handling | `etree.QName`, `nsmap`, expanded names | lxml docs | FX-EXT-*, FX-NS-* |
| Unknown extension retention (backend compare) | árvore preserva elementos/atributos de ns arbitrários | comportamento XML | FX-EXT-001/002 + comparator |
| Multiple diagrams | regra BPMNDI-008 + tree nav | spec + rules | FX-DI-004 |
| Vendored schema offline build | Resolver + `no_network` | config | teste CI schema build sem rede |
| Frontend extension round-trip | bpmn-moddle: moddle-xml preserva elementos genéricos + `extensionElements`; descriptors registráveis via `moddleExtensions` | bpmn-moddle docs/issues (#15) e KIE parity note — **a provar**, não assumido | FX-EXT-001..004 round-trip test no editor (P4) |
| DI-less render | editor gera layout transitório | requirement de contrato | FX-NODI-001 open test (P4) |

Gaps declarados: nenhuma biblioteca backend sozinha prova preservação de extensão pelo **editor** — isso é responsabilidade do frontend (Prompt 4) verificada por fixtures de round-trip.

## 36. Frontend Interoperability Contract

`FROZEN` — qualquer editor escolhido no Prompt 4 DEVE:

1. Carregar BPMN 2.0 XML canônico (texto) — inclusive **sem DI** (gera geometria transitória).
2. Renderizar DI suportada fielmente (shapes, edges, waypoints, labels, pools, lanes).
3. Serializar BPMN 2.0 XML completo: semântica + BPMN-DI + namespaces, em cada save.
4. Preservar todos os constructs `RENDER_PRESERVE_ONLY` do profile (seção 34) — round-trip `STRUCTURALLY_EQUIVALENT`.
5. Preservar extensions desconhecidas conforme seção 17 (elementos+atributos+texto+contenção) — round-trip `EXTENSION_EQUIVALENT`.
6. Emitir DI nova/atualizada após qualquer edição geométrica (move/resize/connect/auto-layout).
7. Não reordenar semanticamente elementos de forma que mude significado (ordem de serialização deve respeitar o schema para manter XSD-valid).
8. Não injetar namespaces/elementos proprietários (sem extensão DELPI na V1).
9. Passar as fixtures de round-trip da seção 32 (no-op + safe-edit).
10. Degradar para read-only quando o load falha parcialmente (sem perda silenciosa — seção 39).

Candidato esperado: **bpmn-js + bpmn-moddle** — capabilities documentadas indicam adequação (moddle-xml preserva extensionElements/atributos genéricos; serializer emite BPMN 2.0 completo; layout transitório viável via auto-layout plugin ou equivalente). Não promovido por expectativa: a seleção final é do Prompt 4 e deve cumprir 1–10 com evidência de fixture.

## 37. Namespace Policy

`FROZEN`:

| Namespace | URI | Papel |
|---|---|---|
| BPMN | `http://www.omg.org/spec/BPMN/20100524/MODEL` | semântica — recognition exige esta URI no root |
| BPMNDI | `http://www.omg.org/spec/BPMN/20100524/DI` | diagram interchange |
| DC | `http://www.omg.org/spec/DD/20100524/DC` | bounds/waypoint types |
| DI | `http://www.omg.org/spec/DD/20100524/DI` | diagram element base |
| XSI | `http://www.w3.org/2001/XMLSchema-instance` | schema instance |
| Extensions | qualquer URI | namespaces de extensão são dados, não código |

- Comparação e recognition usam **expanded QName** (namespace URI + localName) — nunca prefix textual. `bpmn:`/`bpmn2:` etc. são equivalentes desde que a URI seja a normativa.
- Prefixo específico nunca é exigido; serializers podem escolher prefixos.
- Unknown construct policy separada:
  - root definitions em **namespace desconhecido** → `XML_NOT_BPMN`;
  - elemento **desconhecido no namespace BPMN** → reconhecido + issue estrutural (XSD inválido provável) → preserve;
  - elemento BPMN **válido fora do editing profile** → `RENDER_PRESERVE_ONLY` (Prompt 1);
  - elemento/atributo em **namespace de extensão** → política da seção 15.

## 38. XML Formatting / Comments / PI Policy

`FROZEN` — não fazem parte da semântica canônica: indentation, attribute order, namespace prefix spelling, quote style, XML declaration formatting, line endings. Podem mudar após serialize sem indicar drift semântico.

XML comments: `BEST_EFFORT` — preservados se o serializer do editor os mantiver; perda não é violação (comments não carregam semântica BPMN). Processing instructions: `OUT_OF_SCOPE` — raros em BPMN; não exigidos nem rejeitados; passam pelo round-trip se o serializer os emitir.

## 39. Preservation Failure Policy

`FROZEN` — nenhum save destrutivo silencioso:

| Classe de falha | Policy |
|---|---|
| Conteúdo que o **editor não consegue carregar** (parse/estrutura fatal no editor) | `OPEN_READ_ONLY` — edição desabilitada; diagnóstico explícito; export sempre disponível (artefato intacto no backend) |
| Construct que o editor carrega mas **não consegue preservar** no serialize (perda detectada por round-trip check pós-serialize no save) | `SAVE_BLOCKED` + diagnóstico `preservation-risk` — o fluxo de save compara o artifact serializado contra as categorias da seção 17; perda detectada → `VALIDATION_BLOCKED` com evidência |
| Perda **possível mas não detectada** (risco residual, ex.: serializer ignora silenciosamente) | mitigado por fixtures de round-trip que cobrem 100% do profile (seção 34) + EXTENSION_EQUIVALENT — qualquer gap é bug do adapter, não policy |

Mecanismo de detecção: o save já valida o conteúdo submetido (pipeline Prompt 2); a checagem de preservação compara o **submetido** contra o **anterior** quando a sessão começou de um import com constructs conhecidos-problemáticos — implementação da comparação no adapter de validation (mesmo rule engine), acionada quando EXT-* ou BPMNDI issues existiam no intake. Detalhes de wiring → P6/P7; policy fechada aqui: perda detectada = bloqueio; perda não detectável = bug coberto por fixtures.

## 40. Delegations to Prompts 4/5/6/7

| Prompt | Delegado |
|---|---|
| **4** | escolha/composição do editor frontend; render de diagnósticos/painel; UX de read-only/capability failure; wiring do save-flow com evidência; navegação issue→elemento; preview mechanics de auto-layout (com P5) |
| **5** | engine/algoritmo de auto-layout; geração de DI para artefato sem DI; routing/geometry rules; qualidade de layout |
| **6** | limites físicos exatos (`MAX_INPUT_BYTES`, `MAX_XML_DEPTH`), rate limits, packaging dos XSDs vendored, versão lock de lxml, sandboxing/runtime, auditoria |
| **7** | transporte (upload/download multipart/headers), status codes, OpenAPI, filename sanitization no header, E2E das fixtures via API |

## 41. Open Questions

Nenhuma questão de WHAT/validação/interoperabilidade aberta — parser, XSD strategy, operation policy, BPMN-sem-DI, extensions, mustUnderstand, preservation, round-trip, equality e reference convention estão resolvidos. Pendentes são exclusivamente HOW de outras camadas com dono (seção 40).

## 42. Specification Freeze Status

- [x] Recognition fechado (7 estados: INPUT_REJECTED_SECURITY + NON_XML + MALFORMED_XML + XML_NOT_BPMN + 3 BPMN_RECOGNIZED_*; security rejection ≠ NON_XML)
- [x] Rule catalog V1 (47 rules: 7 SEC, 2 XML-WF, 4 REC, 11 STRUCT, 8 SEM, 9 BPMNDI, 2 PROD, 4 EXT, 0 INTEGRATION) com fontes/classificação
- [x] Stages fechados com prerequisitos e matriz de dependência (XML_WELL_FORMEDNESS independente de INPUT_SAFETY NOT_EVALUATED)
- [x] Partial evaluation fechado (binário conservador, sem mudança de contrato no stage model)
- [x] Input Safety Evidence Contract fechado (`InputSafetyEvidence` — APPLICATION CONTRACT CHANGE: REQUIRED, seção 24)
- [x] Operation policy fechada por condição (severity ≠ policy, rationale registrado)
- [x] Import/Open/Edit/Save/Export/Revision matrix fechada
- [x] BPMN sem DI fechado (persist original, layout transitório, DI via editor/save)
- [x] Extensions e mustUnderstand fechados
- [x] Preservation contract fechado (o que deve sobreviver, por categoria)
- [x] Round-trip + equality model fechados (TEXT/SEMANTIC/DI/EXTENSION/STRUCTURAL)
- [x] Stack escolhida: lxml (parse+XSD vendored) + rule engine próprio; alternativas rejeitadas com motivo
- [x] XSD strategy: vendored OMG XSDs + manifesto com checksums, zero rede
- [x] Fixtures especificadas (30+ com coverage matrices)
- [x] Rule coverage: 100% das rules habilitadas mapeadas a fixtures
- [x] Editing profile coverage: 100% CREATE_EDIT + RENDER_PRESERVE_ONLY mapeados
- [x] Reference convention + diagnostic ordering fechados
- [x] Nenhuma decisão BPMN crítica aberta ao implementador

```text
BPMN / VALIDATION / INTEROPERABILITY SPEC STATUS:
FROZEN
```
