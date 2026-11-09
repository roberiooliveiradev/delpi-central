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
