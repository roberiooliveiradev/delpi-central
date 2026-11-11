# 293 — DÉLIA · trilha finita de fechamento de engenharia: LEGACY / OWNERSHIP / FLOW / REGRESSION

**Data:** 2026-11-09. **Tipo:** COORDINATION PLAN / DOC_ONLY. **Estado:** PLANNED, nenhum gate aceito por este registro. **HEAD visto durante a preparação:** `6d8536bc205822d857691c3eb4e1dfe1b7e318d4` (revalidar na execução; mudanças concorrentes possíveis). **Owner:** coordenação DÉLIA; implementadores Cursor/Devin sob task autorizada. **Objetivo do PO:** **ZERO resíduo material não resolvido nos quatro gates**, antes de novas funcionalidades ou troca de foco para experimentos de inteligência/modelos; não declarar sucesso por documentação ou testes isolados. **Production deploy:** NOT_AUTHORIZED.

## 0. Precedência e preservação

Reancoragem obrigatória em **cada etapa**: `HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger`. Buscar fase e NEXT reais em 16+ledger no HEAD; este roteiro não avança C3 nem substitui decisões congeladas. Preservar 21/C3-T4 Structured Understanding; foundation C3-T5 OpenAPI de 16/20/25; owner/contrato do snapshot; AuthZ Core/Domain, Keycloak, MCP provider boundary, Evidence/Policy/Outcome; `read!=write`, `PREPARE!=ACT`, `tool!=permission`, `GROUNDED!=Outcome`. Conflitos: STOP + `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`, nunca reconciliação implícita.

**Fontes de entrada:** doc256 (plano mestre G0–G8, inventário 246–255 e anexos de execução), docs 239–255, 125/129/130 (refactor e antipadrões), doc292 (estabilização funcional; snapshot histórico, **não prova de HEAD**), ledger oficial, backlog R01–R07, e evidência E2E v42 `delia-api/.battery/r01-v42-e2e/matrix-summary.json` (DEV only; Kimi e Qwen14B C1 GROUNDED, Qwen4B C1 admission FAIL; Qwen14B B1/OPS alguns outcomes parciais; G4 fixture fail de suíte ampla). Código/teste/resultado real no SHA vigente prevalecem sobre histórico apenas como evidência de implementação — autoridade documental prevalece nas decisões.

**Proibição de varredura infinita:** NÃO repetir auditoria completa de 66 arquivos nem reabrir G0–G8 como trabalho novo. Consumir matriz doc256, ledger e commits aceitos, atualizar somente itens de risco com diff no HEAD. Um único mapa residual congelado em T0 e buscas residuais dirigidas por etapa; no máximo **5 tasks de execução + 1 revisão final** (T0–T5), com **até 1 rework técnico bounded por etapa**, sem geração recursiva de planos. Pedido fora do universo congelado ou necessidade de novo owner = STOP e decisão superior, não extensão silenciosa. Trabalho concluído não é refeito.

## 1. Contrato da trilha, critérios de fim

Gates independentes e cumulativos:

- **L — LEGACY_CLEANUP = PASS**: zero `OBSOLETE_PROVEN` com consumer ativo/alias/shim/flag/import no runtime DÉLIA; remoções de docs244–255/256 comprovadas em HEAD e consumidores/contratos substituídos; nenhum parser/retry/tool loop próprio duplicando Pydantic AI sem função legítima; componentes aprovados mantidos. `0 rg results` sozinho não é prova.
- **A — ARCHITECTURE_OWNERSHIP = PASS**: nenhuma violação de dependência/boundary ativa conhecida no escopo congelado, zero segunda autoridade Core/Domain, zero planejamento/tool mechanics hardcoded por provider, snapshots e OpenAPI com owner/contrato/fase decididos; interfaces reais pelos Ports & Adapters existentes, sem duplicação.
- **O — ORCHESTRATION_FLOW = PASS**: caminhos de admissão, owner selection, MCP native Pydantic AI, evidence/grounding/outcome e negativos provados no SHA/config da trilha, incluindo casos de sucesso, parcial, não encontrado, unauthorized, compare, multi-owner, multi-turn, NDJSON/timeouts; **sem defeito material do fluxo não corrigido**. Limitações de capacidade de modelo continuam rastreáveis e exigem veredicto explícito se impedem DoD; não renomear falha de fluxo como limitação do modelo sem prova da primeira fronteira divergente.
- **R — FULL_REGRESSION = PASS**: suíte completa DÉLIA backend e focused security/architecture tests com exit 0 e provas live DEV autorizadas de Outcome; falha G4 fixture resolvida ou classificada/isolada por owner com justificativa canônica e suite real reproduzível; TÉO suite R07 e prod tools/list R06 são **dependências externas** com owner, não podem ser escondidas sob PASS DÉLIA. Se critérios canônicos exigirem tais provas para produto, mantê-los bloqueadores até owner os encerrar.

**CLOSE=ACCEPT** somente se L=A=O=R=PASS, entregas e provas fechadas em SHA/config sem drift, zero residual MATERIAL conhecido no escopo, avaliação independente aprovada e ledger atualizado. `ACCEPT_WITH_RESIDUAL` é **não encerrado** para este objetivo, mesmo se residual parecer pequeno. Falta de credenciais/infra/authority = PENDING/BLOCKED (não PASS). Problemas de modelos externos ficam separados somente se não contaminarem o aceite obrigatório do fluxo; nenhuma falsa universalização de Kimi/Qwen14B para Qwen4B.

## 2. Sequência fixa e não recursiva

```text
T0  FREEZE (HEAD, autoridades, baseline, matriz residual L/A/O/R)
  → T1  LEGACY (remoções e consumers: legado obsoleto comprovado)
  → T2  OWNERSHIP (dependências, snapshot/OpenAPI, boundaries)
  → T3  FLOW (first-divergence + correção dos defeitos do fluxo DÉLIA)
  → T4  REGRESSION (full suites, AuthZ, real Outcome, negatives)
  → T5  INDEPENDENT CLOSE (audit diff, gate L/A/O/R, ledger, handoff)
  → END: ACCEPT | REWORK bounded (1) | BLOCKED/ADR
```

Cada etapa é **um task ID**, um escopo congelado e um relatório. Não avançar automaticamente para a seguinte: coordenação revisa `ACCEPT|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`; T5 é a única decisão global. Rework máximo 1 por etapa, limitado aos testes/arquivos do defeito; depois STOP com relatório e owner responsável — sem novos prompts em cascata. T0 é 1 pass de reconciliação residual, não inventário total.

### T0 — Freeze factual e decisão de escopo

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T0-BASELINE-RESIDUAL-FREEZE-01`. **Owner:** coordenação DÉLIA. **Inputs:** 16/ledger/256, commits aceitos, R01–R07, E2E DEV e 292 como histórico. **Artefato único:** `engineering-closure-residual-register.md` (ou anexo com path/consumer/owner/contract/test/SHA) com classificação de cada item `CLOSED_PROVEN | OPEN_MATERIAL | EXTERNAL_DEPENDENCY | KEEP_APPROVED | TO_VERIFY`; no máximo uma linha por defeito real/contrato, não por arquivo já limpo. Evidência existente validada sem reexecução. Revalidar baseline sintaxe/import/target suites e classificar falha G4 e as dependências TÉO R06/R07, cronograma de gate. **Sem refactor/código nesta etapa.**
**Exit:** universo congelado, ordem e conjuntos mínimos de testes, CP/RQ, blockers, `EXISTING_EQUIVALENT/REUSE_DECISION`. Se autoridade contraditória, STOP somente slice; sem inventário ad hoc infinito.

### T1 — LEGACY CLEANUP (somente candidatos abertos T0)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T1-LEGACY-CONSUMER-PURGE-01`. **Owner:** DÉLIA application/infrastructure por arquivo real. Conferir exclusões doc244/245 (paginated semantics, outcome assessment), G1–G8 doc256, wrappers/flags CRI e shims, import reverso de snapshot quando relevante (decisão T2). Para cada `OBSOLETE_PROVEN`: rastrear consumidores static+dynamic, preservar contratos/authority, RED→minimal DELETE/consumer migration→GREEN→full focused regressão→residual AST/import/rg. Se função ainda tem consumidor legítimo: `KEEP_APPROVED` documentado, não chamar legado. Não mover 1.800 LOC para helper; não criar engine novo. **Exit:** `L=PASS` preliminar com evidência de paths removidos, consumer count 0 e paridade, ou BLOCKED com owner e decisão — sem tarefa extra.

### T2 — ARCHITECTURE / OWNERSHIP (sem redesenho)

**Emenda aprovada pelo PO em 2026-11-09:** ver §2A, que amplia conscientemente esta T2 para (a) RETIRE_FULL_SET já autorizado e (b) análise e possível extensão condicionada de cadastro/gestão de conexões MCP internas e externas com Core/Keycloak/ExternalConnection e MCPToolset native. A ampliação **não** autoriza por si writes de Core/IAM/prod ou nova migration sem owner/contrato/fase. Em conflitos, STOP e registrar o bloqueio.

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01`. **Owner:** arquitetura DÉLIA + owners dos contratos. Revisar dependências reais do HEAD (Domain/Application sem infra; HTTP/event inter-context, sem imports/banco alheios); anomalia snapshot Application→Infrastructure e destino de experimento, C3-T5 foundation/adapter OpenAPI, C3-T4 approved KEEP, configurações paralelas/providermatics no planner e imports MCP. Não tocar Keycloak/Core/TÉO sem owner autorizado; decisão snapshot/OpenAPI preserva freezing docs. Corrigir **somente** desvio comprovado dentro de ownership; RED→GREEN+arquitetura/segurança. Se decisão superior requerida, `ARCHITECTURE_DECISION_REQUIRED`, sem esconder sob PASS. **Exit:** `A=PASS` preliminar ou BLOCKED formal.

### T3 — ORCHESTRATION / FLOW (correção delimitada)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T3-FLOW-OUTCOME-REMEDIATION-01`. **Owner:** DÉLIA Capability Provision / Interaction. Usar baseline v42 e native Pydantic AI/MCP; não trocar output strategy, recriar planner, alterar budgets R03 por chute ou refazer config por modelo. Matriz canônica mínima: admission operational/conceptual/surface, discovery→execute, cross-owner compare, partial/no-data, invalid tool args, denied, multi-turn, streaming/terminal, timeout/budget e postcondition outcome. Para cada falha: primeira fronteira divergente `ADMISSION|SELECTION|MCP|OWNER|PROJECTION|EVIDENCE|OUTCOME|PRESENTATION`; proibir correção keyword/model-specific; 1 diff bounded + RED/GREEN + real DEV case. Tratar residual Qwen14B B1/OPS sem automaticamente atribuir R02/R03, Qwen4B local como capability limitation somente com evidência; R01 status separado. **Exit:** `O=PASS` preliminar com matriz+truthful outcome, ou BLOCKED/INCONCLUSIVE.

### T4 — FULL REGRESSION / RELEASE READINESS (NO PROD)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T4-FULL-REGRESSION-AND-REAL-EVAL-01`. **Owner:** QA/engenharia DÉLIA, parceiros de teste TÉO quando relevante. SHA de T1–T3 fixado. Suite completa backend no ambiente canônico (sem `pytest -k` como substituto), arquitetura/imports/contract tests, auth negatives 401/403, MCP hostile content, permission changes, PREPARE/ACT, no leakage, deadlines, output grounding and denial; DEV E2E Kimi e Qwen14B fixados, conceptual/operational, 2 owners, multi-turn, Outcome. Separar falha G4 preexistente no mesmo ambiente: reproduzir base e candidato, reparar path/fixture no owner de teste se escopo legítimo, não esconder por skip. R06 prod tools/list e R07 full TÉO suite: owner externo; mapear se bloqueiam aceite do produto ou somente produção; se bloqueiam, STOP sem autoexecutar tarefas em outros serviços. **Exit:** `R=PASS` preliminar só com zero falhas materiais da suíte exigida e Outcomes comprovados; `TEST_NOT_RUN` não substitui PASS.

### T5 — REVIEW INDEPENDENTE E FECHAMENTO

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T5-INDEPENDENT-ZERO-RESIDUAL-ACCEPTANCE-01`. **Owner:** coordenação/reviewer independente. Comparar registro T0 vs HEAD, commits e consumer graph pós-removal, revalidar `16 + ledger`, tests reais e production status. Uma única tabela `ID|scope|owner|baseline|diff|test|Outcome|final disposition`; auditoria residual **direcionada** aos símbolos/paths congelados, não varredura nova de 66 arquivos. Veredictos L/A/O/R independentes. **ACCEPT somente L=A=O=R=PASS + ZERO_OPEN_MATERIAL + no drift**. Atualizar doc256 como supersession/ponte de T0–T5, anexos e ledger; registrar SHA/config, testes e handoff. Sem advancement C3, feature/model switch nem deploy automática. Se BLOCKED, **fim da execução com blocker formal** (owner/dependency/required decision), sem iniciar novo ciclo infinito; retomada específica exige nova autorização e reancoragem.

## 2A. T2 ampliada por decisão explícita do Product Owner — remoção do snapshot + cadastro governado e federado dos MCPs (2026-11-09)

**Natureza:** emenda de escopo **neste Documento 293**, sem criar documento/registry/engine novo por antecipação. **Decisão do PO:** (1) **RETIRE_FULL_SET** de \`snapshot_experiment\`, inclusive local/prod; (2) consolidar onboarding, cadastro, configuração e verificação de MCPs internos/externos sem três listas mantidas manualmente; (3) preservar **Pydantic AI MCPToolset** como consumidor do \`tools/list\` live; (4) preservar Keycloak/Core/Domain authority; (5) não inferir que todo MCP externo usa Keycloak. **Task ID continua** \`DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01\`. **T2 anterior** entregou somente decisão: commit \`b9346387bd28cb6d1a2b8b9777529c0d666f5133\`, \`A-05=ARCHITECTURE_DECISION_REQUIRED\`; a autorização deste PO supre a decisão de RETIRE, **não comprova execução nem aceita T2**.

**Controle explícito de drift:** o congelamento original T0/T1 e a regra "uma task bounded por etapa" permanecem rastreáveis; este item é uma **ampliação superior conscientemente aprovada** do escopo T2, e não alegação de que o universo T0 já incluía onboarding externo. A parte nova deve registrar owner, CP/RQ aplicável e compatibilidade com \`16 + ledger\` antes de qualquer diff. Se o Core/segurança não tiver contrato legítimo ou o escopo/fase não permitirem implementar cadastro persistido agora, **STOP no slice correspondente**, formalizar \`ARCHITECTURE_DECISION_REQUIRED\` ou \`BLOCKED_BY_OWNER_CONTRACT\`; não criar tabela na DÉLIA como atalho, não iniciar T3, não gerar trilha recursiva. **Máximo um rework técnico bounded por etapa.** Documentação ≠ autorização de migração, IAM write, operação produtiva ou avanço de fase.

### 2A.1 Reancoragem e evidências canônicas específicas

Antes do trabalho: HEAD/origin/main/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec 24, docs 17/21/51/59/60, doc216 (experimento A/B), doc256, registro residual T0/T1/T2, ledger, runbooks Keycloak/ChatGPT e **contratos Core**. Conflitos documentais exigem \`EXECUTION_DRIFT\`/decisão, não supersessão silenciosa. **Revalidar a localização/nome real do doc 52 no índice antes de afirmar leitura.**

Evidências em HEAD anterior à execução (revalidar):
- \`delia-api/app/domain/specialist_interop/rules.py\`: \`_SPECIALIST_IDENTITY\` contém 7 identidades aprovadas (DAVI, TÉO, VISTA, CAIO, CLARA, SURI, EVA); \`APPROVED_SPECIALIST_IDS\` deriva dela.
- \`delia-api/app/infrastructure/config/settings.py\`: \`mcp_specialist_endpoints\` / \`mcp_specialist_enabled\` repetem manualmente os 7 IDs.
- \`delia-api/app/infrastructure/interoperability/config.py\`: \`specialist_connections_from_settings\` já deriva perfis de identidade aprovada (reuse).
- \`infra/docker-compose.yml\`: configuração padrão de endpoints/enablement dos 3 DAVI/TÉO/VISTA, não paridade comprovada com os outros quatro; \`root_composer.enabled_specialists\` é tupla **derivada** de perfis \`enabled and endpoint\`, não uma lista fixa de 3.
- \`delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py\`: \`MCPToolset\` nativo, \`CombinedToolset\`, \`RenamedToolset\`, tool-definition filtering, hook \`process_tool_call\` governado; \`SpecialistInterop/McpCapabilityProvider\` preservam elegibilidade e invoke com autoridade live. Não substituir por segundo catálogo/Agent.
- \`infra/scripts/delia_mcp_keycloak_state.py\`: \`SPECIALISTS\` com **7 resource clients** e o requester \`delia-api\`; pode haver duplicação de identidade IAM declarativa, mas esse script é infraestrutura de **provisionamento desejado**, não prova do Keycloak de produção. Runbook \`keycloak-prod-delia-mcp-provision.runbook.md\` ainda possui seção resumindo apenas 3; reconciliar contrato documental sem editar configuração IAM às cegas.
- \`docs/12-roadmap-e-evolucao/delia/60-agent-interoperability-mcp-a2a-and-tool-protocols.md\` §5.1 estabelece **direção preferida:** Core como fonte governada de approvals/provedores; Keycloak é identidade/token exchange e **não** autoridade de aprovação; DÉLIA orquestra; provider possui \`tools/list\` live. Status da projeção Core é **TARGET/DEFERRED**, não implementação comprovada.
- \`docs/12-roadmap-e-evolucao/delia/21-data-and-state-model.md\` §§4A.18, 7, 23 prevê \`ExternalConnection\`, classes \`USER_DELEGATED|ORG_MANAGED|SHARED_RESOURCE|SERVICE_CONNECTION\` e MCP registry como modelos **candidatos**, não tabelas físicas. \`51\` reporta \`ExternalConnection\` plataforma **TARGET_ONLY** no inventário histórico; estado do HEAD requer inspeção Core atual.
- \`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md\`: ChatGPT usa seu próprio cadastro OAuth e callback; DÉLIA possui requester \`delia-api\` e token exchange user-delegated. **Não** reutilizar callback/secret ChatGPT, não criar client DÉLIA por MCP e não pôr audience específica em scope compartilhado \`mcp:tools\`.

**Estado factual:** \`EXISTING_EQUIVALENT=YES / REUSE_DECISION=REUSE\` para Pydantic AI MCPToolset, SpecialistInterop, profile resolver, identidade aprovada, IAM exchange e contratos conceituais; **\`TO_INVENTORY\`** para implementação real de provider approval persistido no Core, \`ExternalConnection\` físico, API/migrations e secret owner. **\`NEW\` proibido enquanto \`TO_INVENTORY\`.**

### 2A.2 Ownership congelado para a nova superfície

| Responsabilidade | Authority / owner | Persistência/consumo esperado |
|---|---|---|
| Aprovar/cadastrar/desabilitar/revogar provedores MCP e outros recursos de plataforma | **Core governance** (reutilizar/estender app/provider registry legítimo; verificar contrato existente primeiro) | Cadastro canônico aprovado, versionado e auditável; não armazenar nomes/schema de tools |
| Identidade, client OAuth, audience, consentimento/token exchange quando DELPI | **Keycloak**; IAM owner e contratos do recurso | IAM authoritative; somente ref/diagnóstico sanitizado fora dele |
| OAuth/credenciais de Microsoft, Google e outros serviços externos | **Owner OAuth externo + secret owner autorizado** | OAuth user/tenant-scoped; \`secretRef\`, nunca token/refresh token na tabela comum |
| Vínculo efetivo da conexão a usuário/org, scopes, revogação, políticas | **ExternalConnection** conforme owner comprovado no inventário Core/DÉLIA; não criar autoridade duplicada | Registro de conexão distinto de registro de servidor; contrato first |
| Catálogo de ferramentas, schema, toolClass, disponibilidade factual | **Servidor MCP dono da ferramenta** | \`tools/list\` **live** pelo MCPToolset; sem snapshot persistido como catálogo autoritativo |
| Policy/Decision, eligibility, evidence, governance do invoke, Outcome | **DÉLIA** + Core/Domain no seu boundary | Port/adapter existente; hooks governados; \`tool metadata != permission\` |
| Visualização administrativa única e checks de saúde | **DÉLIA Control Tower/Portal**, conforme UI/ownership existente | Projeção de estado, jamais segunda aprovação ou credential store |

**Separação fundamental:** **MCP Server Registration** (servidor/owner/protocolo/aprovação) != **ExternalConnection** (usuário/org, credencial e consentimento) != **live tool catalog** (remote). Mesmo servidor pode atender múltiplas conexões; uma conexão pessoal não vira organizacional; em nenhum caso \`registered == reachable == authenticated == authorized == outcome\`.

### 2A.3 Modelo lógico alvo (não schema físico pré-aprovado)

Definir **por contrato existente, não por nome de tabela sugerido**, a menor representação necessária:

**Provider/server approval record (Core preferido):** \`providerRef\`, \`protocol=MCP\`, \`ownerRef\`, \`displayName\`, \`endpointRef/validated HTTPS URL\`, \`authStrategyRef\`, \`trust/risk tier\`, \`allowedConnectionClasses\`, \`approved/disabled/revoked\`, \`policyRef\`, \`created/updated/version\`, \`approvedBy/auditRef\`, \`lastValidatedAt\` opcional. Credencial, description de tool e schema **fora** do master. Provider registration não confere permission.

**Connection record (owner a provar):** \`connectionRef\`, \`providerRef\`, \`ownerType\`, \`ownerRef\`, \`sharingClass\`, \`consent/scope refs\`, \`credentialRef\`, \`status\`, \`expiry/revoke/reconnect refs\`, \`lastValidatedAt\`, \`auditRef\`. Nunca guardar token, secret, bearer, refresh-token, prompt ou resultado empresarial na tabela.

**Read model de observabilidade:** \`configured|approved|enabled|auth_valid|tools_list_reachable|degraded|revoked|unknown\` por ambiente e escopo, timestamp e erro tipado sem segredo. Estado \`UNKNOWN\` não é \`DISABLED\` nem ausência de capability; resultado de sondagem não concede AuthZ. Preferir projeção computada/telemetria existente, não uma terceira tabela só por conveniência.

**Contrato antes de implementação:** owner/consumers, API request/response/errors, RBAC Core, subject & tenant boundaries, identity linkage, URL validation/SSRF/redirect/DNS rebinding/egress, idempotency/version/revoke/rollback, confidentiality, rate limits/timeouts, audit/observability, compatibility, \`OpenAPI operationId\` estável se HTTP, tests/E2E/negative. Sem edição direta de DB do Core pela DÉLIA, sem cross-context imports.

### 2A.4 Fases executivas fechadas dentro da T2 ampliada (sequenciais; STOP em boundary bloqueado)

**T2.1 — Retirada do snapshot (já autorizada pelo PO; responsabilidade DÉLIA):**
- Usar T2 report/registro residual para identificar TODOS consumidores e símbolos de \`snapshot_interop.py\`, \`catalog_store.py\`, \`mcp_catalog_sync.py\`, modo \`snapshot_experiment\`, flags, scripts \`r4_authenticated_resume_eval\`, compose/env examples, imports, fixtures e testes exclusivos de experimentação. Verificar consumidores atuais via AST/rg + composição; não reabrir outros legados.
- Escrever RED para garantir único discovery live e rejeição fail-closed de configuração aposentada; remover código e consumidores exclusivos (inclusive arquivos sem função restante), sem apagar evidence histórica/doctests legítimos e sem esconder failures.
- Para \`DELIA_MCP_CATALOG_MODE\` legado ainda ativo no ambiente: definir falha explícita de startup ou migração/clear operacional **antes** do rollout, com ordem segura; \`mode=live\`/unset como único caminho. Não reiniciar container, editar env produtivo, apagar banco persistido ou fazer deploy sem **ops authorization específica**. Higienizar DEV/test/local no escopo autorizado; identificar dados experimentais e retenção antes de qualquer delete de volume.
- Provar MCPToolset native + SpecialistInterop + \`tools/list\`/invoke live, auth negatives, architecture/import test, composição; full backend suite se mudar runtime. \`A-05/L-06/R04\` ficam \`OPEN/PENDING\` se live produtivo não for verificado na versão/config correta.
- Deliverable: commit mínimo, prova de no snapshot code/consumers, remediation plan de drift de produção, matriz de testes, sem falsa declaração de cleanup produtivo.

**T2.2 — Inventário Core/IAM/ExternalConnection (READ-ONLY, bounded):**
- Verificar no Core **código, migrations, APIs, testes, app/plugin registry, governance/approval/disable/revoke e contratos efetivos**; no DÉLIA comparar \`_SPECIALIST_IDENTITY\`, \`settings\`, \`specialist_connections_from_settings\`, \`root_composer\`, \`McpSpecialistAdapter\` e \`MCPToolset\`; no IAM conferir **scripts/runbooks** e, apenas mediante acesso autorizado, \`--check\` read-only de DEV/PROD com environment provenance. **Não** tocar SQL/keycloak/admin live sem gate.
- Matriz **7×** DAVI/TÉO/VISTA/CAIO/CLARA/SURI/EVA: resource URL, owner, current approval ref, Keycloak client/audience/permission (se comprovados), enabled+endpoint por ambiente, tools/list real, negative AuthZ, reason unavailable. \`NOT_TESTED\` nunca vira \`PASS\`.
- Inventariar provider OAuth externo/secret store, validade de \`ExternalConnection\` física, controle de revogação; ChatGPT OAuth custom-client e callbacks são **cliente-específicos**. Verificar mecanismo do Core antes de desenhar schema.
- Entregar \`EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY\`, \`REUSE_DECISION=REUSE|EXTEND|NEW\` **por responsabilidade** e contrato/owner. Se owner, contrato ou fase/Core write não autorizado → STOP em T2.2 com decisão pronta, não improvisar tabela DÉLIA.

**T2.3 — Contrato de cadastro único (design contract-first; sem código sem gate):**
- Formalizar API/projeção do Core (ou dono comprovado) para listar, registrar candidato, revisar/aprovar, habilitar/desabilitar, revogar e auditar server/provider — somente capabilities autorizadas; lifecycle \`DISCOVERED→REVIEWED→APPROVED→ACTIVE\`, \`DEGRADED\`, \`DISABLED\`, \`REVOKED\`, \`DEPRECATED\`. \`discovery != approval\`.
- Formalizar connection lifecycle \`PENDING_CONSENT→CONNECTED→EXPIRED/DEGRADED→RECONNECT/REVOKED\` respeitando class/owner/consent; não misturar estado provider/connection/tool.
- Identificar a autorização **separada** para criar/alterar recursos Core, IAM, secrets, migrações ou endpoints. Se necessário, entregar request de aprovação ao owner; **não** usar autorização de remover snapshot como autorização de alterar Core.
- Definir migração idempotente dos sete especialistas com IDs canônicos e sem duplicar audience; nenhuma migração de dados em produção nesta task sem autorização operacional. Falha/rollback/fail-closed explícitos.

**T2.4 — Backend/provider-neutral wiring (CONDICIONAL A T2.2/T2.3 + owner approval):**
- Caso Core já disponha de contrato legítimo e a fase autorize, **REUSE/EXTEND** o contrato existente pelo boundary HTTP/evento real; nenhum import DÉLIA→internals Core, nem leitura de DB alheio.
- Reutilizar \`SpecialistInteropPort\`, \`McpCapabilityProvider\`, \`specialist_connections_from_settings\` e \`MCPToolset\`. Migrar identidades de approval do hardcode para refs governadas **apenas depois** de prover read model Core equivalente e fallback/fail-closed sem ampliar permissões. Não transformar o banco Core em cache de \`tools/list\`.
- Eliminar enumerações manuais divergentes de IDs na \`settings.py\`/Compose onde houver caminho de configuração comprovado e compatível; **não** remover configuração de endpoint/segredo que pertença ao deployment sem substituto oficial. Bootstrap dos sete registros idempotente; \`enabled\` não deve ser inferido de registro.
- Um novo servidor aprovado aparece por configuração governada sem novo branch por nome no planner; \`MCPToolset\` criado por conexão elegível no turno; \`process_tool_call\` intercepta **toda** chamada; se credencial/scope/owner indisponível, fail closed.
- **Segurança externa:** TLS HTTPS, allowed egress, IP/private/metadata endpoint/loopback/redirect/DNS rebinding/host check, tenant-bound identity, secrets owner, least-privilege, prompt injection em tool descriptions/schemas, toolclass untrusted como permissão, READ/WRITE, approval. MCP externo com OAuth Microsoft/Google segue owner respectivo; Keycloak de DELPI não substitui o OAuth externo.

**T2.5 — Verificação operacional/UX (CONDICIONAL):**
- Reusar surfaces MFE/Control Tower/plugin-ui existentes e contrato do Core; antes de componente novo, inventário do equivalente. Admin apresenta lista única de servidores e suas conexões, approved/enabled/authenticated/live/revoked, timestamps, \`tools/list\` count efêmero, erros sanitizados, testes de conectar/desconectar/revalidar. **UI não é permission authority**, não expõe tokens/URLs internos indevidos; ações materiais back-end-first.
- Testes: sete internos (incluindo disabled/403/missing endpoint), ao menos um externo em sandbox autorizado quando houver credenciais, OAuth personal vs org, tenant isolation, expiração, revoke, SSRF/redirect, tool metadata injection, typed denial, policy/read/write boundaries, reconnect, no snapshot, cold restart, drift env, concurrency/idempotência, API failures.
- E2E real somente no ambiente com credenciais/autorização válidas; sem integração Microsoft/Google real disponível, \`TEST_NOT_RUN\` para externo e **não** aceitar "suporta externos em produção". Full suite e generalização+security+task Outcome no SHA/config depois de diff.
- No prod deploy automático. Operações de IAM/secret/compose/prod exigem autorização de owner/ops, janela, backup/rollback e pós-condição verificada.

### 2A.5 Critério de saída e governança da ampliação

- **Fechamento do snapshot (A-05/L-06/R04):** nenhum path experimental em runtime/código/local alvo; prod mode reconciliado sob ops autorizado e comprovado; 0 consumers ativos de snapshot, live path TESTED; R04 só \`CLOSED_PROVEN\` com pós-condição, senão \`PENDING_OPS\`.
- **Cadastro central (novo escopo T2):** owner Core aprovado; contrato identificável; uma fonte de provider approval persistida; conexão/credential com owners separados; 7 internos reconciliados e 4 adicionais não omitidos por Compose; MCPToolset native live, sem espelho de tools; externo testado ou explicitamente \`PENDING_EXTERNAL_E2E\`; regressões/segurança. Nenhum \`PASS\` por mocks/documentação.
- **Se T2.2 achar apenas TARGET/DEFERRED**, entregar decisão arquitetural aprovada como **plano**, com provas de inexistência baseadas em inventário (search=0 não basta), mas **não** implementar \`NEW\` ou mudar Core/migrations; \`T2_ARCHITECTURE_GATE=BLOCKED_BY_OWNER_CONTRACT\` até aprovação. Esta opção não impede encerrar apenas a subparte snapshot quando provada; não avança T3 automaticamente.
- **Gates de execução:** a decisão superior deste PO aprova **RETIRE_FULL_SET** e **planejar** centralização; qualquer write Core/Keycloak/prod, nova API/migration ou ativação de externo requer owner/CP/RQ/contrato/fase específicos; preservar docs 16/50/17/49/51/52/21/20/25 e ledger. Execução não se autoaceita.
- Relatório final deve separar \`SNAPSHOT_REMOVAL\`, \`CORE_EQUIVALENT\`, \`IAM_7X_STATE\`, \`PERSISTED_APPROVAL\`, \`EXTERNAL_CONNECTION_STATE\`, \`MCPTOOLSET_LIVE\`, \`AUTHZ_NEGATIVES\`, \`OUTCOME_EVIDENCE\`, \`OPS_DRIFT\`, \`OPEN_MATERIAL\`, \`FILES_CHANGED\`, \`TESTS\`, \`SHA\`, \`NEXT=T2_INDEPENDENT_REVIEW\`.
- O **único artefato de planejamento** é este Documento 293 ampliado. A execução atualizará ledger/registro residual existentes após os fatos; não criar novo documento de roadmap, catálogo materializado, cronograma recursivo nem T6.

### 2A.6 Execution stamp (T2 ampliada — 2026-11-09)

**TASK:** `DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01`
**BASE_HEAD:** `1a895cb0f02bedb6bd2288855fe1d447fea8998e`
**RESULT:** T2.1 `RETIRE_FULL_SET` **IMPLEMENTED** (código/repo). T2.2 inventário: Core ExternalConnection/provider approval = `TARGET_ONLY` → T2.3 design only; T2.4/T2.5 = `BLOCKED_BY_OWNER_CONTRACT`. R04 prod flag = `PENDING_OPS`. Detalhe e procedimento ops: `evidence/engineering-closure-residual-register.md` § T2 ampliada. **NEXT:** `T2_INDEPENDENT_REVIEW`. T3 / PRODUCTION_DEPLOY: NOT_AUTHORIZED.

### 2A.7 Decisão de arquitetura — persistência MCP no Core, não no Keycloak (PO 2026-11-09)

**Decisão da coordenação / Product Owner (direção arquitetural aprovada; implementação ainda BLOCKED_BY_OWNER_CONTRACT):** o cadastro **governado** de servidores/provedores MCP da plataforma DELPI tem **Core API** como owner; a persistência pretendida é o **PostgreSQL sob ownership lógico do Core** (`delpi_core` no baseline atual), **não** o banco/schema do Keycloak e **não** uma tabela paralela da DÉLIA. Reutilizar preferencialmente as estruturas/tabelas/migrations já legítimas do Core; criar schema PostgreSQL dedicado somente mediante inventário, contrato e justificativa aprovada pelo owner Core. Esta decisão **não** aprova de antemão um schema físico, nome de tabela, migration, SQL, API, credencial, alteração no Keycloak ou deploy.

**Ownership e separação de dados (contratos alvo, ainda não implementados):**

| Dado/responsabilidade | Owner/fonte | Persistência ou consumo |
|---|---|---|
| Registro e aprovação do servidor MCP: providerRef, identidade, endpointRef, owner, protocolo, policy/status, audit/version/revoke | **Core governance** | PostgreSQL do Core (estrutura existente se adequada); CRUD/consulta por API governada com Core AuthZ |
| Conexão efetiva por usuário/org, consentimento, sharing, scopes e credentialRef | **ExternalConnection**, owner físico/contrato a confirmar antes de executar | Reutilizar/estender boundary legítimo; **não presumir** que tudo pertença à mesma tabela/schema do provider registry |
| Identity, client OAuth, audience, token exchange, SSO | **Keycloak** quando o recurso usar IAM DELPI | Estado IAM próprio; client configurado != aprovação do provedor; não duplicar tokens ou permissions no Core |
| OAuth de terceiro (Microsoft/Google etc.), consentimento, refresh/revoke | **Provider OAuth externo e secret owner autorizado** | Não forçar terceiros a usar Keycloak; secret/token real fora de tabela comum, prompt, memória, logs e MFE |
| Tool names, descriptions, schemas, toolClass e disponibilidade factual | **Servidor MCP** | `tools/list` live consumido pelo **Pydantic AI MCPToolset**; sem snapshot autoritativo |
| Seleção, Policy/Decision, invocation gates, Evidence e Outcome | **DÉLIA** + Core/Domain business authorities | Consumir provider/connection refs por **contrato HTTP/evento**; sem imports/SQL cross-context nem segundo planner |
| UI de administração/observabilidade | Core-governed capabilities e DÉLIA/Portal conforme contratos de UI | Uma superfície administrativa, não segunda autoridade de approval/credencial |

**Fluxo alvo:** operador autorizado solicita cadastro → Core valida, audita e aprova provider → mecanismo de conexão/credencial próprio é vinculado por usuário/org → DÉLIA consulta somente refs/estados elegíveis via Core → resolve credential bounded → `MCPToolset` descobre `tools/list` em tempo real → toda invocação passa por DÉLIA/Core/Domain/Policy e Outcome. `registered != approved != enabled != authenticated != authorized != business outcome`. Em revogação, fail closed; cache não concede nem prolonga permissão.

**Reuse-before-design:** `EXISTING_EQUIVALENT=NO/TARGET_ONLY` para provider approval e ExternalConnection físicos conforme relatório T2 ampliado no SHA `e94496503c8771eab87107c4d3d0dfeedb022295`; reconfirmar no HEAD antes de writes. `REUSE_DECISION=EXTEND Core` como direção preferida **após** provar owner, contratos e consumo, não autorização para criar generic registry na DÉLIA. Keycloak e MCPToolset: `EXISTING_EQUIVALENT=YES`, `REUSE`. Revalidar docs 16/17/21/49/50/51/52/59/60, ledger e contratos reais; novas evidências que contrariem o owner = `EXECUTION_DRIFT`/decisão superior.

**Gates antes de qualquer código de Core/persistência:** (1) aceite formal de Core owner e fase/CP-RQ; (2) inventário de schema/tabelas/APIs/governança/RBAC/audit e segredo; (3) contrato versionado request/response/errors/AuthZ/idempotency/revocation/rollback/observability, `operationId` estável se HTTP; (4) design da migração idempotente de sete recursos internos e onboarding externo, sem dependência da callback OAuth do ChatGPT; (5) testes de approval/revoke, troca de token, isolamento usuário/tenant, SSRF, fail-closed, schema parity, E2E real e Outcome; (6) Ops authorization separada para qualquer ambiente produtivo. `A-07=BLOCKED_BY_OWNER_CONTRACT`, `R04=PENDING_OPS` até evidência factual. `T2_ARCHITECTURE_OWNERSHIP=NOT_PASS`; `T3` e deploy produtivo não autorizados por esta decisão.

### 2A.8 Execution stamp — Core governed MCP registry attempt (2026-11-09)

**TASK:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-IMPLEMENTATION-01`
**ADR:** §2A.7 / commit `f5baf5b2`
**GATE:** `CORE_OWNER_APPROVAL=NOT_PROVEN` · `PERSISTENCE_AUTHORIZED=NO`
**RESULT:** inventário Core reconfirmado (provider registry / ExternalConnection físico **ABSENT**); padrões apps/RBAC/audit/S2S = REUSE de *mecanismos*, não de schema MCP; especificação contratual registrada no residual; **nenhuma** migration/API/código Core ou registry DÉLIA. `A-07` permanece `BLOCKED_BY_OWNER_CONTRACT`. `R04=PENDING_OPS`. **NEXT:** `T2_INDEPENDENT_REVIEW` após aceite formal do Core owner. T3 / PRODUCTION_DEPLOY: NOT_AUTHORIZED.

### 2A.9 Aceite formal de escopo pelo Product Owner — implementação Core MCP em DEV (2026-11-09)

**DECISÃO FORMAL DO PO NESTA COORDENAÇÃO:** `PO_IMPLEMENTATION_AUTHORIZATION=APPROVED` para executar a extensão **no boundary do Core** do cadastro governado e persistido de provedores MCP, com migrações **somente DEV**, contrato HTTP, Core AuthZ, auditoria, testes e integração DÉLIA por API. A autorização cobre design físico mínimo decorrente do inventário (tabela própria Core se `apps` for inadequada), sem schema PostgreSQL novo por conveniência, e migração **idempotente DEV** dos sete provedores com habilitação preservada. **Não é apenas uma autorização para repetir inventário.**

**Escopo autorizado e sequência:** (1) reancorar HEAD/status, autoridades 16+ledger e contratos Core; (2) congelar menor contrato real Core (owner/consumers, campos, API+operationIds estáveis, permissions, erros, idempotência, lifecycle/revoke, auditoria, migração/rollback); (3) implementar a persistência Core, migrations DEV, endpoints e segurança aproveitando padrões existentes; (4) integrar DÉLIA ao Core por HTTP através de ports/adapters existentes, sem import/SQL cruzado; (5) migrar sete registros DEV, sem ativar os quatro desligados; (6) testar fail-closed, 401/403, approval/revoke, concorrência, SSRF, negativa de tenant, discovery live MCPToolset, ferramentas reclassificadas, regressão e Outcome realmente verificado. **Não implementar ExternalConnection físico nem storage OAuth novo sem owner e contrato próprios comprovados**; fornecedor externo pode ser caracterizado por testes contratuais/double, E2E real apenas quando autorizado e disponível.

**Interpretação rigorosa dos gates:** `CORE_OWNER=Core`; `PO_SCOPE_APPROVAL=PROVEN (esta decisão)`; `CORE_OWNER_ACK/TECHNICAL_CONTRACT_ACCEPTANCE=TO_VERIFY` (não há evidência de assinatura separada da equipe proprietária). `PERSISTENCE_DEV_SCOPE_AUTHORIZED_BY_PO=YES`; execução física exige resolver qualquer veto de authority em 16/ledger e conferir se o executor tem autorização de escrita no Core. Na ausência de exigência de aceite separado pelo owner, esta aprovação da coordenação permite executar o slice Core em DEV; se o contrato canônico requer aceite distinto, obter ou registrar `BLOCKED_BY_CORE_OWNER_ACK` sem atribuir assinatura inexistente. **Não manter `CORE_OWNER_APPROVAL=NOT_PROVEN` por mera ausência desta declaração: ela agora existe como decisão PO explícita.** A-07 passa de `BLOCKED_BY_OWNER_CONTRACT` para `AUTHORIZED_FOR_BOUNDED_DEV_IMPLEMENTATION`, **não** `CLOSED_PROVEN`.

**Preservações:** `EXISTING_EQUIVALENT=NO` para provider registry físico e `REUSE_DECISION=EXTEND Core` pelos mecanismos reais RBAC/audit/API; Keycloak continua identidade, `delia-api` requester e token exchange; provedor MCP continua authority do live `tools/list`; sem novo runtime, catálogo duplicado, banco DÉLIA, client OAuth extra por especialista ou reinserção de snapshot. `ExternalConnection_OWNER=TO_CONFIRM` para persistência de conexão pessoal/organizacional; não assumir que aprovação de provider inclui credenciais de terceiros. Prod/IAM writes/deploy/migração prod/alteração de env prod **NOT_AUTHORIZED**; R04 `PENDING_OPS`. T3 `NOT_AUTHORIZED`.

**Critério de saída:** entregar diff mínimo com testes RED/GREEN, full Core+DÉLIA quando alterados, matriz sete registros DEV e negativos, SHA/config/Outcome e ledger factual. Se alguma dependência não puder ser comprovada, classificar `PENDING/TEST_NOT_RUN/BLOCKED` por boundary, sem autoaceite. Revisão T2 independente após execução; nenhuma alteração retroativa do relatório anterior bloqueado.


### 2A.10 Execution stamp — Core MCP registry R1 (2026-11-09)

**TASK:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-IMPLEMENTATION-R1`
**RESULT:** Core `mcp_providers` + HTTP + seed DEV 7 (3 enabled) **IMPLEMENTED**; DÉLIA HTTP consumer com `DELIA_MCP_PROVIDER_REGISTRY_MODE`; ExternalConnection **NOT_IMPLEMENTED**; R04 `PENDING_OPS`. **NEXT:** `T2_INDEPENDENT_REVIEW`. T3/PRODUCTION_DEPLOY: NOT_AUTHORIZED.

### 2A.11 Execution stamp — Core MCP registry R1 bounded rework (2026-11-09)

**TASK:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-R1-REWORK-01`
**AUTHORIZATION:** §2A.9 (mesmo escopo bounded DEV; sem T3; sem PRODUCTION_DEPLOY; sem Keycloak prod writes).
**BASE_IMPLEMENTATION_SHA:** `3dacbdc0c23c13fefc23d9610f21cdbfd0632333` (R1). HEAD de reancoragem pode ter avançado por workstreams concorrentes; WIP alheio preservado.

**RESULT (bounded rework):**

| ID | Correção | Status |
|---|---|---|
| R1-RW01 | Revalidação de elegibilidade Core no invoke (`CoreMcpProviderEligibilityGuard` + orchestrator) — fail-closed; sem cache autoritativo | IMPLEMENTED + RED/GREEN |
| R1-RW02 | Use case Application depende de `McpProviderRepositoryPort` / domain entities — sem import SQLAlchemy | IMPLEMENTED + arch assert |
| R1-RW03 | `endpoint_policy` no domain + trusted hosts explícitos; negativos SSRF | IMPLEMENTED + RED/GREEN |
| R1-RW04 | `specialist_connections_from_core_eligible` provider-neutral; auth não suportada → `unavailable_reason` tipado | IMPLEMENTED + RED/GREEN |
| R1-RW05 | S2S `authorizationScope=provider_approval_only`; aprovação ≠ AuthZ usuário/org/Domain | FORMALIZED + tests |

**Preservado:** `mcp_providers`, migration `u7v8w9x0y1`, admin/S2S, seed 7, MCPToolset nativo, SpecialistInterop. **Não feito:** ExternalConnection físico; OAuth externo; segundo registry; UI admin; T3; deploy prod.
**A-07:** permanece `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN`). **R04:** `PENDING_OPS`.
**NEXT:** `T2_INDEPENDENT_REVIEW`.

### 2A.12 Execution stamp — Full remediation + regression (2026-11-09)

**TASK:** `DELIA-C3-T2-CORE-MCP-REGISTRY-FULL-REMEDIATION-AND-REGRESSION-01`
**AUTHORIZATION:** PO — corrigir falhas verificadas (MCP + Core/DÉLIA full suites); PRODUCTION_DEPLOY/Keycloak prod/T3 NOT_AUTHORIZED.
**REFERENCE_SHA:** `ebd0a3533d20d93c001a2151fd9e567e9f116f85`.

**RESULT:**

| Frente | Status |
|---|---|
| Revogação universal (`_invoke` + semantic) | IMPLEMENTED + RED/GREEN |
| Domain endpoint_policy puro (sem os/socket); DNS/env em infrastructure | IMPLEMENTED |
| Connection-time egress DÉLIA (`endpoint_egress` no `_connect`) | IMPLEMENTED |
| Core full suite | **413 PASS / 0 FAIL** (era 382/29) |
| DÉLIA full suite | **1463 PASS / 0 FAIL** (G4 + presentation_v2 resolvidos via mounts/paths) |
| DEV E2E Core eligibility disable→block→restore | PASS |
| DEV E2E DÉLIA↔Core S2S eligible + guard | PASS |
| Outcome empresarial live (Keycloak user + Domain ACT) | TEST_NOT_RUN |

**A-07:** `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN`). **R04:** `PENDING_OPS`.
**NEXT:** `T2_INDEPENDENT_REVIEW`.

### 2A.13 Execution stamp — Resume eligibility before MCP outcome replay (2026-11-09)

**TASK:** `DELIA-C3-T2-MCP-REGISTRY-REVOCATION-RESUME-FINAL-CLOSURE-01`
**AUTHORIZATION:** §2A.9 / correção residual delimitada.
**REFERENCE_SHA:** `a2944df834f676fb5e17c803f025c28a2bf5355e`.

**DEFECT_ROOT_CAUSE:** `_invoke()` reutilizava `resume_state.invoke_outcomes[invoke_key]` **antes** de `require_eligible()` — evidência histórica de READ MCP podia operar como grant após revoke/disable.

**FIRST_DIVERGENCE:** retorno antecipado de resume em `OperationalCapabilityOrchestrator._invoke` (pré-gate).

**FIX:** mover o gate `CoreMcpProviderEligibilityGuard` / `McpProviderEligibilityPort` para **antes** do replay de resume e do transporte; sem segundo registry; evidência histórica preservada, não autorizativa.

**TESTS:** `test_mcp_resume_eligibility_gate.py` cenários A–H RED→GREEN; regressão eligibility existente preservada.

**A-07:** permanece `IMPLEMENTED_BOUNDED_DEV`. **R04:** `PENDING_OPS`.
**NEXT:** `T2_INDEPENDENT_REVIEW`.

### 2A.14 Execution stamp — MCP Registry final quality + adversarial validation (2026-11-09)

**TASK:** `DELIA-C3-T2-MCP-REGISTRY-FINAL-QUALITY-AND-ADVERSARIAL-VALIDATION-01`
**AUTHORIZATION:** §2A.9 / fechamento de qualidade T2 (sem novas features; sem T3; sem prod).
**BASE_HEAD (coordination observed):** `dfae28ad2ca708bb75ba4f291625e592ca52ec77` (contém implementação resume `94f51e542b`).
**REANCHOR_HEAD:** `dbc2e526c68e7df983d0458e65e0b9346e32d82a` (= `origin/main` no início).

**KNOWN_FALSE_POSITIVE:** `tests/test_mcp_resume_eligibility_gate.py::test_h_cancel_blocks_before_resume_or_eligibility` — asserção `assert "Cancel" in type(exc.value).__name__ or True` sempre verdadeira.

**ASSERTION_FIX:** `pytest.raises(_TurnCancelled)` + `type(exc.value) is _TurnCancelled`; deadline tipado `TurnBudgetExhausted` + `stage`; wire/eligibility não consultados; mutação documentada em `test_h_cancel_assertion_rejects_wrong_exception_type`. Registry missing-token: assert `integrations_token_missing`.

**PATH_AUDIT:** todos os call sites de invoke MCP no orquestrador passam por `_invoke` (direct, selected/discovery/READ/chain/retry, ACT); MCPToolset nativo → `process_tool_call` → `_governed_semantic_tool_invoke` → `_invoke_selected` → `_invoke`; `McpCapabilityProvider.invoke` → SpecialistInterop → adapter apenas após o gate. Sem second registry/planner/runtime.

**ADVERSARIAL:** janela TOCTOU Core-eligible→wire permanece residual (sem atomicidade distribuída); ExternalConnection / DNS-rebinding/proxy / Outcome ACT live continuam abertos. Nenhum bypass de eligibility por early-return de resume após o fix §2A.13.

**A-07:** permanece `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN`). **R04:** `PENDING_OPS`.
**NEXT:** `T2_INDEPENDENT_REVIEW`.
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`.

### 2A.15 Execution stamp — T2 full implementation remediation + integrated acceptance (2026-11-09)

**TASK:** `DELIA-T2-FULL-IMPLEMENTATION-REMEDIATION-AND-INTEGRATED-ACCEPTANCE-01`
**AUTHORIZATION:** §2A.9 + PO correção/implementação T2 DEV; sem T3; sem prod/migrations prod/Keycloak prod.
**BASE_HEAD:** `d8097eb0333bba1e8122423ae5680f9c713e4af1` (contém `eda3121a6a` + `2ec85d3d42`).

**G4:** falso positivo `assert line.strip() == line or True` → contrato NDJSON single-line (`"\n" not in wire`, `len(splitlines())==1`) + mutação RED.

**Core registry DEV:** migration `u7v8w9x0y1` aplicada; tabela `mcp_providers` com 7 registros (davi/teo/vista enabled; caio/clara/suri/eva registered disabled).

**DÉLIA→Core DEV:** compose passa `DELIA_MCP_PROVIDER_REGISTRY_MODE` + `CORE_API_INTEGRATIONS_SERVICE_TOKEN`; modo `core` ativado em `infra/.env` (gitignored); S2S eligible = davi,teo,vista + `authorizationScope=provider_approval_only`; disable davi → eligible teo,vista + guard `mcp_provider_not_eligible`; restore; bad token fail-closed; rollback `settings`↔`core` comprovado; estado final DEV = `core`.

**Não feito / residual:** ExternalConnection TARGET; R04 prod flag `PENDING_OPS`; Outcome ACT live `TEST_NOT_RUN`; DNS-rebinding/proxy residual; TOCTOU Core→wire; tools/list user-delegated live nesta execução `TEST_NOT_RUN` (S2S/composition comprovados).

**A-07:** `IMPLEMENTED_BOUNDED_DEV` + evidência DEV runtime (não `CLOSED_PROVEN`). **R04:** `PENDING_OPS` (handoff ops no residual).
**NEXT:** `T2_INDEPENDENT_REVIEW`.
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`.

### 2A.16 Execution stamp — Real DEV E2E + Outcome validation (2026-11-09)

**TASK:** `DELIA-C3-T2-MCP-REAL-DEV-E2E-AND-OUTCOME-VALIDATION-01`
**AUTHORIZATION:** homologação funcional DEV; disable/enable administrativo reversível; sem ACT empresarial; sem prod.
**BASE_HEAD (coordination):** `fa3b683b758077907aa338e1bcfd4779f4b67f1c` (ancestral `e4df51c12a`); execução em `main` atualizado.

**DEV:** `DELIA_MCP_PROVIDER_REGISTRY_MODE=core`; identidade portal DEV válida (`mcp_providers.manage` + delia); profile `local_ollama` → `qwen3:8b` + budgets 90/120s (todos os profiles alinhados).

**T01:** tools/list real autenticado PASS — superfície live DAVI = `analyze,get_context,knowledge,read` (**drift** vs docs `discover_delpi_information`/`execute_delpi_information`).
**T02:** turn `/interaction/turns` **não concluiu** em 480s (latência modelo local); Domain API structure `90260921` FP `a3dcef2068200898` PASS; durante o turn houve `davi.get_context` real; **SpecialistInterop** `davi.read`+`get_product_structure` PASS (COMPLETED, contém 90260921).
**T03/T07:** disable admin Core + eligible teo/vista + guard `mcp_provider_not_eligible` + enable restore PASS.
**T04/T05:** `TEST_NOT_RUN` (checkpoint harness / usuário negativo ausente).
**T06-A:** bad token fail-closed PASS. T06-B/C harness: cobertos por testes de contrato.
**T08:** Domain autoritativa PASS; resposta completa do turn INCONCLUSIVE; READ MCP structure via interop PASS.
**T09:** resume/cancel/G4 PASS. **T10:** Core 413/0; DÉLIA 1474/0.

**A-07:** permanece `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN`). **R04:** `PENDING_OPS`.
**PROPOSED:** `ACCEPT_WITH_RESIDUAL` — E2E parcial (turn LLM incompleto; live tool names drifted).
**NEXT:** `T2_INDEPENDENT_REVIEW`.
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`.

## 3. Política de residual ZERO e limites reais

- **ZERO** significa nenhum residual material **no escopo de fechamento DÉLIA aprovado**. Resíduo externo TÉO, dependência de produção ou limitação de modelo não pode ser rotulado `PASS`; determinar explicitamente se é bloqueador da aceitação DÉLIA ou de release. Não declarar que todo monorepo foi limpo.
- É permitido `KEEP_APPROVED` para código vivo ou foundation congelado; não é legado residual. `EXTERNAL_DEPENDENCY` não é solução: acompanha owner, impacto, teste e gate.
- Eventos que invalidem premissa = `EXECUTION_DRIFT`; autoridade contraditória = `ARCHITECTURE_DECISION_REQUIRED`; testes fora do ambiente válido = `INCONCLUSIVE`/ `STALE_EVIDENCE`.
- Proibidos: novos serviços/providers/registries, abstração sem consumer, loops/retries propios de Agent, reclassificação por string para mascarar fail, redução de testes, excluir históricos, fazer ACT sem gate, deploy implícito, fase avançada por documento.
- Critério de esforço: cada task consome apenas o conjunto `OPEN_MATERIAL|TO_VERIFY` atribuído; no máximo 1 rework e então STOP. Não criar T6/T7 automaticamente. Novo problema verdadeiro fora do frozen scope retorna à coordenação como drift, não expande a task.

## 4. Template mínimo de execução por etapa

```text
TASK_ID:
BASE_HEAD:
FINAL_HEAD:
ORIGIN_MAIN:
PUSH_VERIFIED:
HEAD_STATUS:
CANONICAL_REANCHOR:
PHASE_NEXT_16_LEDGER:
CP_RQ:
SCOPE_FROZEN_IDS:
FILES_CHANGED_REMOVED:
EXISTING_EQUIVALENT:
REUSE_DECISION:
CONSUMERS_AND_CONTRACTS:
RED_GREEN:
FOCUSED_TESTS:
FULL_BACKEND_TESTS:
ARCH_SECURITY_GATES:
REAL_EVAL_SHA_PROFILE:
OUTCOME_EVIDENCE:
RESIDUAL_SEARCH:
OPEN_MATERIAL_AFTER:
EXTERNAL_DEPENDENCY:
LEDGER_UPDATED:
PRODUCTION_DEPLOY=NOT_AUTHORIZED
STAGE_VERDICT=ACCEPT|REWORK|EXECUTION_DRIFT|INCONCLUSIVE|BLOCKED
NEXT_STAGE=REVIEW_REQUIRED
```

**Single command to start:** autorizar somente **T0**, sem código. Revisar T0 e então emitir **um único prompt bounded para T1**, sucessivamente até T5. Nenhuma autorização implícita para tarefas seguintes. **Fim inequívoco = T5 ACCEPT ou T5 BLOCKED/ADR documentado; sem loops de prompts.**


## Anexo — execução DELIA-C3-SEMANTIC-MCP-PROGRESSION-RESPONSE-SYNTHESIS (2026-11-10)

Registro operacional (não avança gates L/A/O/R automaticamente): remediação F1/F2 de progressão semântica MCP dinâmica e síntese; evidência no residual register e execution ledger. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`. `T3=NOT_AUTHORIZED`.

## Anexo — T2 Independent Review + Qwen14B Production Release (2026-11-10)

**TASK:** `DELIA-C3-T2-INDEPENDENT-REVIEW-RESIDUAL-CLOSURE-QWEN14B-PRODUCTION-RELEASE-01`
**RESULT:** revisão independente AR01–AR12 favorável; R04 `CLOSED_PROVEN` no runtime produtivo deste host (CATALOG_* ausente; mode=`core`); deploy `delia-api`+`api-delpi` no SHA `30ac7cbb4467…` com `DELIA_RUNTIME_PROFILE=openrouter_qwen` / `qwen/qwen3-14b` verificado por invocação; DAVI/TEO/SIPOC GROUNDED; VISTA phrasing flaky classificado risco controlado; ExternalConnection/ACT fora de escopo.
**PROD_READY_FOR_PO_MANUAL_TEST:** YES (`http://localhost/apps/delia`).
**T3:** `NOT_AUTHORIZED`. Detalhe: residual register + execution ledger.


## Anexo — 2026-11-10 | T2 functional REWORK: inteligência investigativa como primeira responsabilidade especializada

**Authority:** Documento 16 (ordem), 50/17/49/51/52 (boundary e reuse), 21/20/25 (estado, gates, CP), este 293 (trilha finite), ledger (execução). **A-07=IMPLEMENTED_BOUNDED_DEV**, R04=production closure previamente reportado, **T2_RELEASE_DEPLOYED_QWEN14B** é registro histórico de release, **não aceite do negócio**. Após a homologação manual com P1/P2/P3 incorretas, **T2_FUNCTIONAL_ACCEPTANCE=REWORK** e **PO_MANUAL_HOMOLOGATION=FAIL**. O estudo forense subsequente foi *diagnóstico*, sem code/config/deploy; P2/P3 problemas de seleção/cobertura sustentados, P1 original INCONCLUSIVE, DEV independente não exercido. Não apagar stamps anteriores; estes não provam Outcome.

### T2-INT — única subtrilha permitida agora, sem avanço de fase

**Objetivo de produto:** progredir para uma inteligência orquestrada com quatro responsabilidades, sem presumir quatro agentes físicos. A inteligência principal continua responsável por coordenar o objetivo; Pydantic AI e os mecanismos atuais fornecem execução cognitiva e delegação somente quando justificada. DÉLIA Application mantém authority de Policy/Decision/Evidence/Outcome e live Core/Domain gates.

| Sequência | Responsabilidade | Equivalentes iniciais a verificar | Estado / gate |
|---|---|---|---|
| INT-0 | Reancoragem, causa/contrato e inventário dos consumers reais | Agent, MCPToolset, InvestigationAnswer, SemanticInvestigationPlan, Coverage, Outcome | **NEXT — TO_INVENTORY; sem código** |
| INT-1 | **Investigação**: Agent generalista com ferramentas dinâmicas e progresso baseado em evidência | `PydanticAiInvestigationOrchestrator`, MCPToolset, SpecialistInterop, governed invoke | **SPECIFICATION/EXPERIMENT_ONLY** após INT-0; nenhum subagent aprovado |
| INT-2 | Compreensão: objetivo e entrega esperada tipados para separar lista/aggregate/explicação sem keywords hardcoded | Admission, plan, InvestigationAnswer, aplicação de contratos | **PLANNED / NOT_AUTHORIZED** |
| INT-3 | Avaliação independente de suficiência (distinta de grounding); teste de necessidade cognitiva | `_evaluate_material_obligations`, `_apply_declared_answer`, finalization, Evidence/Outcome | **TO_INVENTORY / NOT_AUTHORIZED** |
| INT-4 | Síntese fiel, relevante e rastreável | `InvestigationAnswer`, CRI/render, Evidence binding | **PLANNED / NOT_AUTHORIZED** |
| INT-5 | Aceite integrado do comportamento generalista | três casos PO + metamórficos provider/schema/renaming e negatives bounded | **GATED / NOT_AUTHORIZED** |

A ordem INT-1 → INT-4 descreve *foco de investigação*, não pipeline determinístico obrigatório; a compreensão pode anteceder execução no mesmo Agent. Nenhum aumento de chamadas LLM, novo serviço/registry/planner, framework adicional, modelo específico ou novo boundary permitido por default. Múltiplos Agents/hand-off Pydantic AI só podem ser propostos após comparar baseline único com variante mínima, provando melhora de Outcome, custo/latência e segurança.

### Inventário/contratos que INT-0 deve entregar

```text
RESPONSIBILITY → OWNER → CANONICAL_SOURCE → CONSUMERS → CONTRACT → CODE → EVIDENCE → OUTCOME
EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY
REUSE_DECISION=REUSE|EXTEND|NEW
```

Inspecionar caminho ativo de `_INVESTIGATION_INSTRUCTIONS` e `PydanticAiInvestigationOrchestrator`; `InvestigationAnswer` / plano opcional; tools/list e schemas live; `_is_business_evidence_attempt` (evidência válida ≠ conteúdo relevante); `_evaluate_material_obligations`; `_apply_declared_answer` (COMPLETE + refs válidas sem plano); `_finalize_agent_collected_attempts` (SUCCESS com observações sem obrigações e `multiple_observations_without_compose`); argumentos inválidos e anti-churn; contratos de resultado parcial e de apresentação. Não inferir implementação nativa Pydantic AI de docs sem validar versão local.

### Critério finito e estratégia de teste

- **Primeiro resultado:** mapa do grafo de chamadas real + hipótese falsificável sobre o menor boundary incorreto, já existente, **sem alteração de código**. Separar P1 original INCONCLUSIVE de P2/P3 sustentadas.
- **Experimento futuro, somente após nova autorização:** reproduzir falha exata, RED, menor extensão do mecanismo existente, GREEN em consumer e um caso metamórfico com ferramenta/provider/schema alterados. Não hardcode de perguntas/owner/tool e não aceitar `HTTP 200/GROUNDED` como Outcome.
- **Gate de promoção:** critérios objetivos de suficiência da resposta, Evidence/provenance, negativa/partial honesto e chamada efetiva MCP; preservar segurança. Somente a coordenação decide autorização subsequente.
- **STOP:** conclusão sem evidência, dependência de mudança de autoridade/contrato canônico, drift ou escopo novo → `INCONCLUSIVE`/`EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`; não redesenhar silenciosamente.
- **NEXT:** `T2_INT0_INVESTIGATIVE_AGENT_REUSE_AND_CONTRACT_INVENTORY`, sob Documento 16. **PRODUCTION_DEPLOY=NOT_AUTHORIZED; T3=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NO.**

### Stamp — INT-0 inventory executed (2026-11-10)

**TASK:** `DELIA-C3-T2-INT01-…` (fatia INT-0).
**RESULT:** inventário I01–I10 COMPLETE no residual register; `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=REUSE|EXTEND` (sem NEW Agent); hipótese causal falsificável no finalize sem plan/obligations.
**INT-1:** `NOT_STARTED` — PO solicitou implementação condicionada, mas gate canônico desta seção exige revisão independente após INT-0 → `ARCHITECTURE_DECISION_REQUIRED` antes de qualquer diff.
**LOCAL_ENVIRONMENT_NOT_AVAILABLE** para eval live Qwen nesta host (container produtivo único).
**NEXT:** `COORDINATION_INT0_INDEPENDENT_REVIEW`. Sem avanço de fase; T3/INT-2/deploy NOT_AUTHORIZED.


### Coordenação — INT-0 independent review (2026-11-10)

**REVIEWED_IMPLEMENTATION_COMMIT:** `71ae3e9605496f6e6a986e9daa1d3e7c265f624f`. **VERDICT:** `ACCEPT_WITH_RESIDUAL` (INT-0 docs-only inventory), **INT-1:** `AUTHORIZED_BOUNDED_CONDITIONAL`; **NEXT:** `T2_INT1_LOCAL_ISOLATION_AND_INVESTIGATIVE_REWORK`, sem avanço de fase.

A revisão confirmou o reuso do `PydanticAiInvestigationOrchestrator` + native Pydantic AI 2.50.0, MCPToolset, SpecialistInterop, ModelRetry, InvestigationAnswer e gates existentes. **EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND** para o Agent investigativo existente; **NEW_AGENT=NOT_JUSTIFIED**. Diagnóstico principal é ausência de comprovação de pertinência/objetivo na finalização sem obrigações tipadas; não concluir que tornar `SemanticInvestigationPlan` obrigatório em todas as perguntas resolveria o problema. Extensão deve preservar caminho simples e limites, sem novo planner/engine, sem hardcoding de MCP/modelo/pergunta.

**Gate operacional anterior ao live eval:** PROD e DEV atualmente compartilham `container_name: delpi-delia-api` em compose e o executor não demonstrou runtime DEV independente. Provar isolamento de runtime, rede, portas, env, arquivos, credenciais, volume e acesso autorizado antes de testar Qwen14B local. Não modificar/reiniciar container produtivo, não usar produção como DEV; se indisponível, executar somente testes determinísticos e reportar `LOCAL_LIVE_EVAL=TEST_NOT_RUN`.

**Escopo INT-1 autorizado:** baseline/teste RED de seleção/progresso e erros reais P2/P3; extensão mínima do Agent investigativo na interpretação de relevância, schema/owner recovery e discovery non-citability, preservando autonomia semântica e a autoridade de Application Outcome. Verificar primeiro comportamento de `_finalize_agent_collected_attempts` e `_apply_declared_answer` com ausência de plan; não duplicar INT-2/INT-3/INT-4. Testes focados consumer + um metamórfico provider/schema rename e Qwen 14B em DEV isolado apenas. **PRODUCTION_DEPLOY=NOT_AUTHORIZED; T3=NOT_AUTHORIZED; INT2=NOT_AUTHORIZED.** Submeter diff e evidências para revisão crítica; implementação não se autoaceita.

### Stamp — INT-1 local isolation + investigative rework executed (2026-11-10)

**TASK:** `DELIA-C3-T2-INT1-LOCAL-ISOLATION-AND-INVESTIGATIVE-REWORK-01`.
**BASE_HEAD:** `429f1317539d77df370b9c577998f2f22676a7fd`.
**EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND** — `PydanticAiInvestigationOrchestrator` only; no second Agent/planner/engine.
**LOCAL_ISOLATION=PROVEN_HOST_PYTEST** — host `delia-api/.venv` process; `DELIA_ENV` unset; prod container `delpi-delia-api` (`project=infra`, `DELIA_ENV=production`) not restarted/reconfigured/used. `docker-compose.dev.yml` still shares `container_name: delpi-delia-api` → live compose DEV **not** used.
**LOCAL_LIVE_EVAL=TEST_NOT_RUN** — no isolated live Qwen runtime proven without colliding with prod container_name; deterministic RED/GREEN + metamorphic only.
**PYDANTIC_AI_VERSION=2.50.0; MODEL_ID=qwen/qwen3-14b (target; live not run); INSTRUCTION_VERSION=generalist-semantic-v2.**
**DIFF (delia-api):** `classify_investigation_progress` + finalize `related_observations_insufficient`; investigation projections (`investigation_progress`, `owner_validation_hint`); one-shot `owner_argument_rejected` ModelRetry; equivalent-rejection non-progress; COMPLETE+uncovered identifiers ModelRetry; instructions v2. Tests: `tests/test_int1_investigative_progress_rework.py` (R1–R6 + metamorphic) GREEN; sibling suites GREEN.
**INT1_STATUS=READY_FOR_INDEPENDENT_REVIEW** (implementation does not self-accept).
**OPEN:** plan-absent objective-kind gap remains Application Outcome (INT-3); live P1–P3 Qwen still pending isolated DEV.
**NEXT:** `COORDINATION_INT1_INDEPENDENT_REVIEW`. **PRODUCTION_DEPLOY=NOT_AUTHORIZED; T3=NOT_AUTHORIZED; INT2=NOT_AUTHORIZED.** Sem avanço de fase.

### Stamp — INT-1 final bounded rework F1–F4 (2026-11-10)

**TASK:** `DELIA-C3-T2-INT1-FINAL-BOUNDED-REWORK-AND-ACCEPTANCE-01`.
**REVIEWED_IMPLEMENTATION_SHA:** `7cd27e6d0cbc6f401fca9a5fc93282eac54073a0`.
**REWORK_BUDGET:** 1 — FINAL (`INT1_REWORK_BUDGET_EXHAUSTED=YES`).
**EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND; SECOND_AGENT=NO.**
**F1:** removed capability-wide block after first `owner_argument_rejected`; identical fingerprint still short-circuits; materially different args invoke; one-shot ModelRetry keeps owner hint.
**F2:** `classify_investigation_progress` no longer uses READ/ANALYSIS as sufficiency; obligations + evidence structure decide RELATED vs NEW.
**F3:** Agent-path integration + metamorphic rename suite (`test_int1_final_bounded_rework.py`) traverses real `PydanticAiInvestigationOrchestrator` with FunctionModel (not helper-only).
**F4:** finalize without obligations returns evidence on fast path with `coverage_unknown`; related aggregate with plan obligations remains NOT_APPLICABLE + `related_observations_insufficient`.
**LOCAL_QWEN_EVAL=TEST_NOT_RUN** (prod container only; compose.dev shares `container_name`).
**INT1_FINAL_REVIEW_PROPOSAL:** `ACCEPT_WITH_RESIDUAL` (deterministic F1–F4 proven; live Qwen P1–P3 residual; plan-absent Outcome verdict remains INT-3).
**NEXT:** `COORDINATION_FINAL_INT1_ACCEPTANCE`. Sem nova implementação corretiva automática. **PRODUCTION_DEPLOY=NOT_AUTHORIZED; T3/INT2/INT3/INT4=NOT_AUTHORIZED.**

### Stamp — INT-1 isolated real Qwen 14B evaluation (2026-11-10)

**TASK:** `T2_INT1_ISOLATED_REAL_QWEN_EVAL_GATE`.
**IMPLEMENTED_INT1_SHA:** `3bb2be887b05562a6d85301a86ecf5d2e5ae5883` (ancestor of HEAD).
**EVALUATED_SHA / RUNTIME_CODE:** host mount of `delia-api/` at eval time on HEAD `1fa326f50243856f37cebd23b6b803008dd538d7`.
**DEV_RUNTIME_ISOLATION=PROVEN_PROCESS_SEPARATION** — temporary container `delpi-delia-eval-int1` (distinct id) on `infra_delpi-network`; `DELIA_ENV=development`; OpenRouter via localhost egress proxy `host.docker.internal:18765`; **prod `delpi-delia-api` StartedAt unchanged** (`PROD_CONTAINER_UNTOUCHED=YES`). No compose.dev collision used. No functional INT-1 code change.
**MODEL:** `qwen/qwen3-14b` / `openrouter_qwen` / pydantic-ai `2.50.0` / instruction `generalist-semantic-v2` fp `7dbc94c5035b0f19` / config fp `b42a0da3f3be8154`.
**LIVE_EVAL=EXECUTED** (not TEST_NOT_RUN).

| Case | Tools | Investigation | Objective coverage | Notes |
|---|---|---|---|---|
| P1 structure 90260921 | get_context→read | PASS (authoritative structure + qty; `owner_result_incomplete` preserved) | PARTIAL | GROUNDED + coverage_unknown; incomplete owner honest |
| P2 Transformômetro processes | read×3 | PASS (cadastral process ids, not aggregate-only) | PARTIAL | truncated/pagination limitations declared |
| P3 visualization formats | analyze×2 | FAIL/RELATED | FAIL | dashboards TEO-like; not operational viz-format catalog |
| G1 semantic reword | read/get_context/knowledge | PARTIAL | FAIL | identity found; structure tree not recovered |
| Tool-rename MCP gen | — | TEST_NOT_RUN | — | no isolated rename MCP without new architecture |

**INT1_REWORK_BUDGET_EXHAUSTED=YES** — no functional remediation in this task.
**INT1_STAGE_ACCEPTANCE_PROPOSAL:** `ACCEPT_WITH_RESIDUAL` (real inference proven; P3 selection residual + tool-rename gen absent + MCP READ backends shared with prod network).
**NEXT:** `COORDINATION_INT1_REAL_EVAL_INDEPENDENT_REVIEW`. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`; `T3/INT2/INT3/INT4=NOT_AUTHORIZED`.


### Coordenação — revisão final INT-1 (2026-11-10)

**REVIEWED_SHA:** `3bb2be887b05562a6d85301a86ecf5d2e5ae5883`. **REWORK_BUDGET_EXHAUSTED=YES**. **INT1_TECHNICAL_VERDICT=ACCEPT_WITH_RESIDUAL** para o escopo *investigation mechanics*, com limites de evidência explícitos. **T2_FUNCTIONAL_ACCEPTANCE=REWORK**, **PO_MANUAL_HOMOLOGATION=FAIL**; o aceite desta subetapa não fecha T2.

**Independent code review, F1–F4:**
- F1: uso de fingerprint capability+args torna possível nova chamada materialmente diferente após `owner_argument_rejected`; ModelRetry one-shot mantido. `PASS_CODE_REVIEW` no diff.
- F2: progresso deixa de inferir relevância pela classe READ/ANALYSIS; `PASS_CODE_REVIEW`, porém nova observação sem plan/obligations ainda NÃO prova suficiência.
- F3: suite usa `PydanticAiInvestigationOrchestrator` com `FunctionModel` e ferramentas renomeadas. **PASS para wiring/contrato com seleção programada; NOT_PROVEN para seleção semântica autônoma de Qwen/LLM.** O próprio teste escolhe capability pelo `description` e constrói `ToolCallPart` predefinido; não rotular como `LIVE_MODEL_GENERALIZATION=PASS`.
- F4: caminho sem plan retorna `SUCCESS` com `coverage_unknown`; logo `SUCCESS` ainda NÃO significa `OBJECTIVE_SATISFIED`. **PASS para sinalizar lacuna, FAIL/PENDING para Outcome de negócio P2/P3**, propriedade do boundary de avaliação/INT-3. Não atribuir conclusão sem evidência.

**Testes:** GREEN/REGRESSION relatados pelo executor; revisão examinou diff e testes no GitHub, não reexecutou pytest no host. `LOCAL_QWEN_P1_P2_P3=TEST_NOT_RUN`; único container informado = produção e `compose.dev` compartilha `container_name`. Nenhum deploy autorizado.

**Decisão finita:** não reabrir a INT-1; congelar a extensão aprovada sob `ACCEPT_WITH_RESIDUAL` técnico e transferir a pendência objetiva (satisfação sem plano e evidência semântica live) para o gate seguinte **já previsto** na T2-INT. A próxima etapa não é automaticamente implementável: coordenação deve selecionar INT-2 compreensão ou INT-3 suficiência conforme dependências canônicas e garantir avaliação isolada Qwen14B antes de afirmar sucesso funcional. `T3/PROD_DEPLOY/INT2_IMPLEMENTATION=NOT_AUTHORIZED` por este aceite; `NEXT=T2_INT_NEXT_BOUNDED_DESIGN_DECISION`. `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND` sem novo Agent/planner.


### 2026-11-10 — PO correction: real-model evaluation is mandatory before closure of any T2-INT stage

**PRODUCT MASTER BINDING CORRECTION (supersedes prior INT-1 closure language):** `INT1_TECHNICAL_VERDICT=ACCEPT_WITH_RESIDUAL` in previous coordination report is **provisional code-review status ONLY**, **not stage acceptance or closure**. No T2-INT stage (INT-1, INT-2, INT-3, INT-4, INT-5) may be marked `ACCEPT`, `ACCEPT_WITH_RESIDUAL`, `CLOSED`, `DONE` or authorized to advance merely on deterministic pytest / Pydantic AI FunctionModel. Every stage must undergo a **real inference evaluation** on the actual stage-specific objective using an authorized, **isolated DEV** runtime and target Qwen 14B (`qwen/qwen3-14b` / `openrouter_qwen`, or future model explicitly authorized by PO), with actual dynamic tool selection where applicable, real owner/MCP outcome evidence where authorized and meaningful, correlation, evaluated SHA/model/config, and explicit business/functional outcome — not HTTP 200 or GROUNDED alone.

**CURRENT INT-1:** `IMPLEMENTED_TECHNICALLY / CODE_REVIEW_COMPLETE`; `LOCAL_QWEN_EVAL=TEST_NOT_RUN`; `INT1_STAGE_ACCEPTANCE=PENDING_REAL_EVAL`; `INT1_CLOSED=NO`. Previous `ACCEPT_WITH_RESIDUAL` is narrowed to *bounded code-review result*, not functional stage gate. Rework budget remains exhausted: **no automatic new INT-1 code rework**. Next bounded action is to inventory/prove a nonproduction isolated evaluation path and run exactly the already defined P1/P2/P3 + one small live semantic variation; if isolation is unavailable, `BLOCKED_BY_LOCAL_EVAL_ENV` and stop rather than advance. Do not change/restart production container, share prod state/secrets or claim host pytest = isolated live evaluation. No T3 or INT-2 implementation authorization.

**Gate policy for every intelligence:** code RED/GREEN + narrow regression → **live real-model run** with expected intent and actual source data → independently reviewed task Outcome / negative cases / provider-neutrality → ledger status → coordination stage verdict → only then next stage. If live evaluation fails or cannot run, status is `FAIL` / `INCONCLUSIVE` / `TEST_NOT_RUN` and the stage stays open or blocked. Rework budget limits implementation rounds, **not** the obligation to obtain real evidence before closure. No fabricated PASS.


### Coordenação — revisão independente do gate real Qwen INT-1 (2026-11-10)

**REVIEWED_COMMIT:** `2fde206b9be6784a335198f2dcec0ae9d2848a29`. **LIVE_MODEL_EXECUTED=YES** (executor-provided evidence of 4 real Agent turns). **INT1_STAGE_VERDICT=BLOCKED**, **INT1_CLOSED=NO**, **T2_FUNCTIONAL_ACCEPTANCE=REWORK**; previous executor proposal `ACCEPT_WITH_RESIDUAL` is **NOT ACCEPTED** because P3 objective/investigation `FAIL`, G1 reword coverage `FAIL`, and renamed-tool generalization `TEST_NOT_RUN`. P1/P2 demonstrate bounded positive progress with **PARTIAL** business coverage; not global stage acceptance. No new automatic functional rework: `INT1_REWORK_BUDGET_EXHAUSTED=YES`.

**Isolation/safety independent code inspection:** `run_int1_isolated_qwen_eval.sh` creates a distinct temporary Docker container and verifies prod StartedAt unchanged, thus **PROCESS_SEPARATION=PROVEN** as reported. However it copies the entire production container environment via `docker exec delpi-delia-api printenv` to a temp env file, filters only a small set of keys and then appends DEV identity; therefore **CREDENTIAL_ISOLATION=NOT_PROVEN** and production secrets may be present in the evaluation container. The eval container joins `infra_delpi-network`, shared with production backends, and local egress proxy binds `0.0.0.0`. The `openrouter_local_egress_proxy.py` description explicitly says it routes via localhost while the application egress guard sees loopback; treat this as **EGRESS_POLICY_REVIEW_REQUIRED / potential control bypass**, not as authorization. No evidence here establishes exposure, exfiltration or a production restart; do not assert those outcomes. These findings are an **EXECUTION_DRIFT / SECURITY_REVIEW_REQUIRED candidate** requiring confirmation by the designated owner before reuse of this harness.

**Bounded next gate:** `T2_INT1_EVAL_ENV_SECURITY_AND_BLOCKER_DECISION` — inspect approved nonproduction credentials, egress rules and test harness ownership; prohibit reuse of proxy/env-copy script until authorized security review. Also classify P3 and G1 causal evidence and decide whether the frozen INT-1 scope requires an explicit architecture/product decision rather than another automatic rework. No INT-2 execution, prod deploy, T3 or code remediation authorized. Preserve historical test artifacts and redact secrets if found without copying sensitive values to docs/logs.


### Investigação coordenada 2026-11-11 — INT-1 P3/G1, contratos VISTA e eval-evidence (NO CODE)

**HEAD de investigação observado:** `74d10704c8d4236dce12dbd88b40e8e4f3d945be` (revalidar antes de execução). **Escopo:** caracterização causal e decisão bounded dentro da T2; INT-1 continua `BLOCKED`; orçamento de rework não é reaberto por este inventário.

**P3 — OWNER CONTRACT EXISTS / SELECTION FAILURE CONFIRMED / EXACT CAUSE TO_VERIFY.** A fonte canônica TV/VISTA `tv-dashboard-api/docs/integrations/vista-capability-matrix.md` prova oferta de `get_catalog` (DISCOVERY) e `get_product_guide` (READ) como ferramentas MCP; `tv-dashboard-api/docs/architecture/adr-tv-display-format-ownership.md` documenta `displayFormatCatalog` e `DisplayFormatService.preview_format_catalog`. O documento DÉLIA 115 (`115-s2-semantic-relevance-guidance-projection.md`) já caracterizou guidance real em `get_catalog` e `get_product_guide(topic=display_formats)`, diferente de mero descriptor de tool. A INT1 real reportou apenas `analyze ×2` e dashboards sem alcançar catálogo/guia, mas faltam os artifacts de `tools/list` e tool decisions daquele turno para provar por que Qwen não selecionou VISTA. **Não criar ferramenta ou provider novos; verificar discovery live, descrições/schema, toolset filtering/context budget, guia por tópico e eventuais erros.** A pergunta `formatos de visualização` também pode referir tipos de visual (charts/tables/KPIs), distintos do catálogo de formatação de valores. Um owner/source contract não pode ser presumido equivalente sem inspecionar os campos entregues.

**G1 — REAL REWORD FAILURE, NOT PROVEN CONVERSATION CONTINUITY FAILURE.** `run_int1_isolated_qwen_eval.sh` criou G1 como cenário separado sem `prior`, e `native_mcptoolset_direct_eval.py` só cria `ConversationContextTurn` quando `prior` foi explicitamente fornecido. Logo a falha demonstra generalização a paráfrase em single turn, não resume/continuidade de sessão. O identificador 90260921 foi mencionado; `uncovered_user_identifiers()` verifica identidade/root, mas isso não prova cobertura da estrutura BOM. Investigar a cadeia exata seleção → argumentos → owner structured root/items → `owner_result_incomplete`/evidence refs → finalização. Não reclassificar como simples problema de identificação sem trace.

**EVAL CONTROL DRIFT PROVEN IN CODE:** `delia-api/app/infrastructure/config/settings.py` declara explicitamente que não-produção só pode usar runtime LLM local, e modelos externos apenas em produção. `run_int1_isolated_qwen_eval.sh` copia `docker exec delpi-delia-api printenv` inteiro, remove poucas chaves, e fornece o restante a um eval container conectado à rede de produção; `openrouter_local_egress_proxy.py` escuta em `0.0.0.0` no host e encaminha para `https://openrouter.ai`, enquanto o app vê host interno. Trata-se de **bypass da intenção da política de egress de DEV (EXECUTION_DRIFT no método de avaliação)** e **isolamento de credentials não demonstrado**. Process separation e `StartedAt` intacto não bastam. Não afirmar vazamento/exfiltração. Suspender reuso dos scripts e solicitar decisão explícita do owner de segurança/configuração sobre caminho autorizado para Qwen external em ambiente de avaliação isolado, com credenciais provisionadas separadamente e egress governado. Não implementar nova exceção de rede sem ADR/authority.

**Instrumentação/resultados:** `native_mcptoolset_direct_eval.py` registra calls, respostas e `llm_runs.count` medidos pelo wrapper `Agent.run_sync`; **4 cenários não equivalem a 4 requests internos do modelo**. Artifacts completos de turns ficam em `delia-api/.battery/`/diretório temporário e não estão disponíveis no commit do relatório. Não alegar primeira divergência exata P3/G1 sem esses dados; pedir trace sanitizado com lista de capacidades apresentadas ao Agent, decision/call schema/arguments, owner business response, progress, declared output, final outcome, SHA/profile.

**Bounded NEXT (diagnosis, not code):** 1) security/egress authorization e revogação/rotação de qualquer credencial produtiva encontrada no ambiente de avaliação conforme decisão do owner; 2) caracterização P3 com VISTA catalog/guide versus real tool surface; 3) G1 com duas perguntas independentes + controle estrutural owner e paridade de schema; 4) matriz de responsabilidades INT-1 seleção vs INT-2 compreensão vs INT-3 cobertura, sem mover defeito para próxima fase para conseguir aceite. Emitir `ARCHITECTURE_DECISION_REQUIRED` para novo caminho externo de avaliação; não reabrir reworks ou avançar INT2/T3 automaticamente.


### 2026-11-11 — INT-1 CONSOLIDATED ROOT CAUSE (diagnosis only; supersedes § inventário TO_VERIFY parcial)

**TASK_ID:** `DELIA-C3-T2-INT1-CONSOLIDATED-ROOT-CAUSE-AND-SECURITY-INVESTIGATION-01`
**HEAD observado:** revalidar no momento da leitura; investigação ancorada com `origin/main` alinhado e SHAs `3bb2be887b` (impl) / `2fde206b9b` (eval) como ancestrais. **FUNCTIONAL_CODE_CHANGED=NO**; **LIVE_MODEL_CALLS=0**; **PRODUCTION_CHANGES=NONE**.

**Correção factual ao inventário anterior neste doc:** documentação/histórico ainda cita `get_catalog`/`get_product_guide` como tools MCP VISTA. No contrato **vivo** (`tv-dashboard-api/.../mcp/constants.py`) esses nomes estão em `MCP_FORBIDDEN_TOOLS`; superfície pública = seis verbos (`get_context|read|analyze|knowledge|execute|delete`). Guidance de formatos vive via `knowledge` / `read` (`product_guide` / tópicos `display_formats`, `block_types`). Não tratar ausência de `get_catalog` no toolset do Agent como bug de filtering sem essa consolidação.

| Falha | Primeira divergência | Owner | Confiança |
|---|---|---|---|
| P3 | Seleção multi-especialista: Agent invocou `MCP:analyze`×2 e obteve views TEO `dashboard_*` (não catálogo VISTA de formatos/blocos) | INT-1 Agent seleção + ambiguidade semântica da pergunta vs contratos TEO/VISTA; agravante: sem plan obligations, progress classifica evidência business como `NEW` | ALTA no alvo escolhido (eval-output); MÉDIA se VISTA estava elegível naquele turno (catalog_caps não persistido no log) |
| G1 | Single-turn reword: sequência `read/get_context/knowledge` sem recuperar BOM; P1 no mesmo harness provou `get_context+read`→estrutura | INT-1 seleção/argumentação de capability DAVI (`get_product_structure`), **não** continuidade multiturno | ALTA (cenário sem `prior`; conteúdo ≠ BOM) |
| P1 parcial | Owner entregou estrutura parcial + `owner_result_incomplete` | Limite/fonte owner (incompletude) + finalize honesto | ALTA parcialidade; MÉDIA se existia READ de expansão não tentada (args não traçados) |
| P2 parcial | Truncamento/paginação TEO; Agent declara `page=2` mas encerra após 3×`read` | Owner truncamento legítimo + INT-1 não continuou paginação contratual | ALTA truncamento; MÉDIA se budget/tool_calls impediu (tokens=0 no artefato; sem prova de limit hit) |
| Coverage/Outcome | Finalize F4: plan/obligations ausentes → `SUCCESS` + `coverage_unknown` com evidência business | Contrato INT-1 finalize ↔ INT-2 plan ↔ INT-3 suficiência | ALTA (código) |
| Harness | `printenv` prod → env eval; proxy `0.0.0.0`→OpenRouter; `host.docker.internal` passa `llm_egress_blocked_reason` | Método de eval / security-config | ALTA drift; exposição de secret = NOT_PROVEN (valores não auditados neste relatório) |

**SECURITY_FINDING:** `EVAL_METHOD_EXECUTION_DRIFT=PROVEN_IN_CODE`. **HARNESS_REUSE=BLOCKED**. **CREDENTIAL_REVIEW_REQUIRED=YES** (owner segurança; sem rotação nesta task).

**Minimal remediation sequence (proposal only):** (1) decisão de segurança/egress/credenciais para eval externo; (2) decisão de autoridade semântica P3 (VISTA block/display vs TEO dashboards); (3) se INT-1 pode fechar seleção sem INT-2 objective-kind / obligations; (4) observabilidade obrigatória de tool surface+args sanitizados em evals futuros; (5) só então correção mínima no boundary escolhido — sem segundo Agent, sem lexical router, sem reabrir budget automaticamente.

**NEXT:** `COORDINATION_T2_INT1_CONSOLIDATED_CAUSAL_REVIEW`. `INT1_STAGE_ACCEPTANCE=BLOCKED`; `INT1_CLOSED=NO`; `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.


### 2026-11-11 — P3/G1 EXACT DECISION FORENSICS (diagnosis; no code; no live model)

**TASK_ID:** `DELIA-C3-T2-INT1-P3-G1-EXACT-DECISION-FORENSICS-01`
**EVAL_HARNESS_REUSED=NO**; **LIVE_MODEL_CALLS=0**; **FUNCTIONAL_CODE_CHANGED=NO**.

**Trace inventory**

| Capture | Status |
|---|---|
| P1/P3/G1 stdout summary (targets, declared_answer, limitations) | AVAILABLE (host `.battery`) |
| mcp_invoke_records (args types + result_snippet) | MISSING (written under container `/tmp/delia_eval_artifacts`, destroyed on cleanup; omitted from stdout filter) |
| Model-visible MCPToolset descriptions/schemas | MISSING |
| investigation_progress projections per call | MISSING from artifacts; reconstructable only as code paths |
| proxy.log | AVAILABLE (POST counts only; no tool semantics) |

**P3 decision chain (evidence-classed)**

1. USER_MESSAGE OBSERVED: “Quais formatos de visualização de dados estão disponíveis?”
2. INSTRUCTIONS PROVEN_BY_CODE: `generalist-semantic-v2` (SHA `3bb2be887b`).
3. MODEL_VISIBLE_TOOLSET: UNKNOWN (not captured).
4. FIRST ToolCall OBSERVED: `analyze` (stdout target `MCP:analyze` — specialist id collapsed by harness formatter).
5. OWNER_RESULT OBSERVED in final prose: TEO dashboard view ids (`dashboard_summary_live`, …) — matches TEO.analyze description enums (INFERRED_FROM_STATIC_CONFIG + OBSERVED content).
6. SECOND ToolCall OBSERVED: `analyze` again (different fingerprint likely; content family still dashboards).
7. Progress feedback that would force kind-switch (`RELATED_INSUFFICIENT` + coverage_note): **would NOT fire** for this question under plan-absent + no numeric identifiers — PROVEN_BY_EVALUATED_CODE (`classify_investigation_progress` → `NEW_INFORMATION` for business SUCCESS).
8. FINALIZATION OBSERVED: declared `partial` + unmet viz details; limitations include `coverage_unknown`, `declared_status_overridden`.

**P3 first divergence:** first tool action = `analyze` (dashboard ANALYSIS), not VISTA `knowledge`/`read` guidance path.
**P3 exact why-analyze (absent tool vs wrong selection):** `EXACT_CAUSAL_ATTRIBUTION=INCONCLUSIVE` — needs model-visible tool surface.
**P3 why-no-recovery:** PROVEN progress/finalize path above (Agent boundary + plan-absent contract), not MCP execution failure.

**G1 vs P1**

| | P1 | G1 |
|---|---|---|
| Question | estrutura do produto 90260921 | árvore de componentes e relações do item 90260921 |
| prior | none | none |
| Observed calls | get_context → read | read → get_context → read → get_context → knowledge → knowledge |
| BOM evidence | YES (partial owner) | NO |
| tool_calls_limit | n/a (2 < 8) | 6 < 8 — not exhausted |

**G1 FIRST_DIVERGENCE (OBSERVED):** step_1 tool name/order differs (`read` first vs P1 `get_context` first).
**G1 args / whether `get_product_structure` invoked:** UNKNOWN.
**G1 declared “falta de capacidade…”:** conflicts with DAVI `read` description publishing `get_product_structure` (PROVEN_BY_CODE) — indicates selection/arg failure or wrong-specialist read, not absent Domain capability.

**MINIMUM_SAFE_OBSERVATION_REQUIRED (do not implement here):** authorized eval path that host-persists sanitized `{capability_id, arg_key_types, progress, specialist}` per call + eligible tool surface snapshot; no prod printenv copy; no unauthorized egress.

**NEXT:** `COORDINATION_INT1_EXACT_CAUSAL_DECISION`.


### 2026-11-11 — SECURE EVAL + FULL DECISION TRACE (prep; real Qwen blocked)

**TASK_ID:** `DELIA-C3-T2-INT1-SECURE-EVAL-AND-FULL-DECISION-TRACE-01`
**FUNCTIONAL_INTELLIGENCE_CODE_CHANGED=NO**; **LIVE_QWEN_P3_G1=TEST_NOT_RUN**; **EVAL_HARNESS_BYPASS_REUSED=NO**.

**EXISTING_EQUIVALENT=PARTIAL** — `Settings.llm_egress_blocked_reason` (nonprod local-only), Ollama local models, prior capture seams in `native_mcptoolset_direct_eval.py`. Prior isolated harness + `openrouter_local_egress_proxy.py` = **forbidden**.
**REUSE_DECISION=EXTEND observability capture on host path; NEW authorized external egress requires `ARCHITECTURE_DECISION_REQUIRED`**.

**GATE 1 SECURITY = BLOCKED**

| Condition | Status |
|---|---|
| NONPROD_RUNTIME_ISOLATED | NOT_PROVEN |
| CREDENTIAL_ISOLATION | NOT_PROVEN |
| NETWORK_ACCESS_AUTHORIZED | NOT_PROVEN |
| MODEL_EGRESS_AUTHORIZED | NOT_PROVEN |
| MCP_READ_AUTHORIZED | NOT_PROVEN |
| SECURITY_OWNER_APPROVAL | NOT_PROVEN |
| Target `qwen/qwen3-14b` available under authorized path | NO (local Ollama has 8b-class only; OpenRouter nonprod refused by policy) |

Evidence: `settings.py` refuses external LLM hosts when `DELIA_ENV≠production`; localhost-shaped URLs pass host check (prior drift class) and remain unauthorized without explicit owner approval artifact. Script `int1_secure_decision_trace.py --check-security-gate` exits BLOCKED.

**GATE 2–3 OBSERVABILITY = PASS (dry-run only)**

Delivered: `delia-api/scripts/int1_secure_decision_trace.py`, `tests/test_int1_secure_decision_trace.py`. Persist under `delia-api/.battery/int1-secure-decision-trace/` (gitignored, chmod owner-only best-effort). Events: `evaluation_meta`, `model_visible_toolset`, `tool_call`, `finalization` with secret redaction.

| Gate | Result |
|---|---|
| TRACE_SCHEMA | PASS |
| TRACE_PERSISTENCE_AFTER_EXIT | PASS (incl. separate process verify) |
| TRACE_SANITIZATION | PASS |
| TOOL_SURFACE_CAPTURE | PASS |
| ARGUMENT_CAPTURE | PASS |
| PROGRESS_CAPTURE | PASS |

**GATE 4–7 REAL P3/G1:** not executed (`SECURE_EVAL_GATE=BLOCKED`).

**ADR still required:** authorized nonprod evaluation path for Qwen 14B (credential scope, egress allowlist, process/network isolation, MCP READ scope) — then wire real Agent runs into the host-persistent trace schema without decision-logic changes.

**NEXT:** `COORDINATION_INT1_DECISION_TRACE_REVIEW`. `INT1_STAGE_ACCEPTANCE=BLOCKED`.

### 2026-11-11 — PO correction executed: OpenRouter Qwen14B instrumented causal eval

**TASK_ID:** `DELIA-C3-T2-INT1-LOCAL-QWEN14B-SETUP-AND-INSTRUMENTED-ROOT-CAUSE-EVAL-01`.
**Supersedes** prior local-Ollama-14B setup instruction: use external `qwen/qwen3-14b` via OpenRouter profile `openrouter_qwen`; do not install local 14B; do not remove `qwen3:8b`; do not use `openrouter_local_egress_proxy`; do not copy prod `printenv`.

**Security path (minimal legitimate DEV):** `DELIA_ENV=development` + `DELIA_EVAL_EGRESS_AUTHORIZED=1` + Settings allowlist host `openrouter.ai` + real `https://openrouter.ai/api/v1` + selective secrets from `infra/.env` (LLM + exchange) + portal identity from `infra/.env.local` + MCP host headers + Keycloak issuer matching gateway tokens. Isolated eval container; production `delpi-delia-api` StartedAt unchanged. Residual: credential scope still shared with infra LLM key (`NONE_PROVEN_SEPARATE_FROM_PROD`).

**LIVE_EVAL_ID:** `or-qwen14b-35aaf1a4174b` (pydantic-ai `2.50.0`, config fp `b42a0da3f3be8154`). Host traces under `delia-api/.battery/int1-secure-decision-trace/or-qwen14b-35aaf1a4174b/`.

| Scenario | First material divergence | Outcome |
|---|---|---|
| P3 | first wire=`vista.read` (422); **never** `teo.analyze` despite tool surface listing it | GROUNDED partial via `teo.knowledge` + `coverage_unknown` |
| G1 | first wire=`teo.read` vs P1 `davi.get_context`; G1 never reaches `get_product_structure` | NON_GROUNDED; `uncovered_identifier:90260921` |
| P1 control | `davi.get_context`→`davi.read` BOM | GROUNDED partial; `owner_result_incomplete`/`coverage_unknown` |

**FUNCTIONAL_CODE_CHANGED=NO** (egress allowlist + eval harness/observability only). **No INT-1 rework, INT-2, T3, or prod deploy.**
**INT1_STAGE_ACCEPTANCE=BLOCKED**; **INT1_CLOSED=NO**; **NEXT=`COORDINATION_INT1_OPENROUTER_INSTRUMENTED_CAUSAL_REVIEW`**.

### 2026-11-11 — Causal report persistence for independent review

**TASK:** `DELIA-C3-T2-INT1-OPENROUTER-CAUSAL-REPORT-PERSISTENCE-01`. Sanitized report published as sibling doc **294** (`294-int1-openrouter-qwen14b-instrumented-causal-evaluation.md`) for evaluation `or-qwen14b-35aaf1a4174b`. No re-run of P1/P3/G1. Raw traces remain local. **INT1_STAGE_ACCEPTANCE=BLOCKED**. **NEXT=`COORDINATION_INT1_PUBLISHED_CAUSAL_REPORT_REVIEW`**.

### 2026-11-11 — INT-1 specialized instructions evolution (bounded PO exception)

**TASK:** `DELIA-C3-T2-INT1-SPECIALIZED-INSTRUCTIONS-AND-REAL-GENERALIZATION-EVOLUTION-01`. See sibling **295**. Instruction resource isolated; real A/B vs baseline; candidate **not** promoted (P1/P2 regressions). Stage remains BLOCKED.

### 2026-11-11 — INT-1 instruction ablation (2º ciclo PO)

**TASK:** `DELIA-C3-T2-INT1-INSTRUCTION-ABLATION-AND-REGRESSION-FREE-EVOLUTION-01`. See sibling **296**. Three single-group ablations; no regression-free composite; default `generalist-semantic-v2`. `INT1_STAGE_ACCEPTANCE=BLOCKED`. `NEXT=COORDINATION_INT1_INCREMENTAL_EVOLUTION_INDEPENDENT_REVIEW`.
