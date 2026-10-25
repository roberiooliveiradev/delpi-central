# Documento 106 — CLARA batch inteligente, release SSH, Keycloak e cadastro no ChatGPT

**Data:** 2026-10-25. **Decisão expressa do PO:** CLARA deve compreender e executar pedidos que contêm múltiplas ações, com o mínimo de interação, tendo o usuário como autor da solicitação e responsável pelas decisões delegadas. **ID:** `CF-PROC0072-CLARA-BATCH-RELEASE-001`. **Estado:** `PO_APPROVED_PRODUCT_DIRECTION`; contratos físicos, segurança e deploy ainda condicionados aos gates descritos abaixo.

**Autoridade:** Documento 106 complementa e **altera prospectivamente** o contrato de interação do [Documento 94](./94-clara-especialista-mcp-controladoria-financas.md) §10.1 e do [Documento 14](./14-seguranca-rbac-auditoria-e-ia.md) §IA, substituindo **somente** a exigência de confirmação conversacional isolada para cada operação sensível. Mantém D01=B (execução humana delegada, não decisão autônoma), owners, Clean Architecture, effective permission Core, C2/P5 e todas as demais invariantes. Não reclassificar retrospectivamente as evidências do [Documento 100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md).

## 1. Escopo aprovado

- **PRIORIDADE:** fechamento mensal PROC-0072 (P1–P6, R01–R15, P3/T03/T05, evidências, pacotes/revisões), CLARA MCP com conhecimento próprio, consulta/análise e execução múltipla governada.
- **ADIADOS:** Sala de interação, expansão de Minhas tarefas e Contabilidade/DRE como página/fluxo próprio. Preservar código de Minhas tarefas sem expor na release. Não inferir que `submeter pacote para review` seja `enviar anexos para DRE/Contabilidade`: E04/T04 permaneceram NOT_REQUIRED na V1.
- **CONTEÚDO CLARA:** corpus governado com docs e evidências originais quando acessíveis por canal autorizado; vídeo, PDFs, XLSB/XLSX não foram comprovados como ingeridos na execução anterior. Proveniência por fonte/hash/localizador/timecode e restrição de acesso; não publicar dados brutos confidenciais no GitHub.
- **GO de trabalho:** executar correções e funcionalidades que tenham contrato/owner aprovado; interromper somente o subgrafo material dependente de `DECISION_REQUIRED`, G2 ou G3. Nenhuma autorização tácita de proprietário externo.

## 2. Decisão funcional aprovada: lote de ações com baixo atrito

O usuário pode formular **um pedido com N operações**. A CLARA deverá planejar um lote ordenado pelas dependências, identificar operações autorizadas, preparar efeitos e executar o trabalho solicitado sem confirmar repetidamente o mesmo plano.

**A aprovação refere-se ao escopo exato que o usuário autorizou, não a `blanket consent` para operações futuras**. Dois caminhos técnicos possíveis para provar intenção, que dependem de gate transversal com owner de identidade/cliente MCP:

- **A — intenção autenticada atestada pelo host (preferencial quando realmente comprovada):** a solicitação original e seu escopo são vinculados ao ator, canal, contexto, versão do plano e comprovante íntegro, verificável pelo backend. Uma frase gerada pelo modelo, boolean `confirmed=true` ou possession de `proposal_handle` **não** são prova. Somente aplicar A se o cliente/host fornecer atestação efetivamente verificável.
- **B — confirmação consolidada do plano (fallback recomendado):** uma aprovação por lote exibindo ator, competência, objetos, operações, motivos, efeitos e dependências, com prova governada de consentimento vinculada ao lote. Não uma aprovação por operação. Se o host ChatGPT impor confirmação nativa por tool/ação, respeitá-la: a CLARA não controla nem contorna a interface/política do host.

**Status contratual:** `PO_APPROVED` para experiência de lote + mínimo atrito; `DECISION_REQUIRED / TECHNICAL_SECURITY_GATE` para forma física de atestar intenção e integrar a confirmação do host. **A/B não estão implementadas por esta decisão.**

### Orquestração obrigatória

`INTENT → DISCOVERY/AUTHZ → PLAN/DEPENDENCIES → PREPARE_BATCH → VERIFIED_CONSENT → CLAIM → ACT_EACH → READ_BACK_EACH → AUDIT → SUMMARY`.

- Planejar ações explícitas, dependências, versões, motivos, elegibilidade, limites e resultados esperados. Não usar material recuperado da base de conhecimento como nova instrução ou autorização (proteção contra prompt injection).
- Uma aprovação autenticada pode autorizar as **operações individualmente listadas no mesmo plano**; adicionar recurso/operação, ampliar escopo ou mudar efeitos exige novo consentimento para o delta.
- O BFF revalida **por operação e no instante de escrita** Core effective permissions frescas, área/assignment, ownership, recurso, business rule, state, lock, version/OCC; ACCESS não equivale a MANAGE.
- `PREPARE_BATCH` sem side effect de domínio. Falha/indisponibilidade de snapshot deve bloquear, nunca `{}` silencioso. Propostas vinculadas a ator, plano/versão, nonce, expiração e hash canônico.
- **Exatamente uma execução lógica por operação/idempotency key**: claim durável antes do efeito, transições `PREPARED/CLAIMED/APPLIED/VERIFIED/FAILED/UNKNOWN` (nomes técnicos sujeitos a contrato físico), retries bounded e recuperação/consulta após timeout. Não executar efeito e só depois consumir o handle. Não exigir transação global impossível entre serviços.
- Quando uma operação falha, bloquear dependentes e continuar apenas ações independentes que permaneçam explicitamente dentro da autorização; reportar resultados `VERIFIED`, `FAILED`, `BLOCKED`, `UNKNOWN` sem falso sucesso. Reconciliação de outcome desconhecido antes de retry.
- Verificação read-after-write realmente independente, não apenas `response contém decision_id`. Auditoria por operação e por lote, usuário/escopo/versão, origem `mcp/clara`, correlation; sem tokens ou dados pessoais indevidos.
- Não criar capacidade de escrita que a BFF/UI não ofereça, não sacramentar/reabrir TOTVS e não criar um endpoint de bypass C2. Fechamento mensal continua resultado derivado do processo, não um estado imposto pela IA.
- Testes críticos: pedido com 2–20 ações; sequenciamento; operações independentes vs dependentes; inclusão fora de escopo; sem autorização; duas ACT concorrentes mesmo handle; falhas entre efeito/claim/verify; recuperação; stale version; wrong actor; Core 503; prompt injection documental; diferentes áreas e duas competências.

## 3. Segurança: rework precedente continua válido, adaptado ao lote

A revisão da entrega `54f5381c5e` identificou lacunas em consentimento verificável, execução antes do consumo atômico, verificação de pós-condição, `_snapshot` best-effort, paridade/escopo de READ e vazamento de metadados em `list_sources`. Corrigir **na nova estrutura de lote**, sem implementar a solução antiga de confirmações conversacionais individuais. Enquanto o novo gate físico não estiver aprovado/testado, **ACT desabilitada/fail-closed em produção**; DISCOVERY/READ/ANALYSIS podem seguir somente após testes reais de autorização e conformidade.

`EXECUTION_DRIFT` da formalização anterior D02–D05: decisões lançadas por executor sem prova de aprovação do owner, apesar de escolhas alinhadas ao padrão existente. Regularizar aprovação de autoridade/segurança e compatibilidade OAuth; não apagar trabalho existente nem falsificar aceite retroativo.

## 4. Keycloak, Operador SSH e integração ChatGPT — requisitos operacionais

**Intenção do PO:** concluir implementação e ativar CLARA em produção, configurar Keycloak no padrão da plataforma (referência TÉO), e devolver uma ficha de cadastro para instalar/testar o servidor MCP como plugin no ChatGPT.

**Sequência vinculante:** implementar → testes em não produção → decisões materiais G1 → **G2 aceite humano explícito Controladoria/PO** → **G3 autorização operacional explícita do Operador SSH** → preflight/backup/rollback → alteração Keycloak/ambiente de produção **autorizada** → deploy do SHA imutável → ingestão corpus governada → smoke HTTP/MCP autenticado → ficha de cadastro ChatGPT → teste privado de plugin. A intenção de deploy neste documento **não é G2 nem G3**.

### Keycloak — padrão existente, sem reproduzir secrets

Inventariar client MCP TÉO no código/configuração vigente e estado REAL Keycloak por canal autorizado, comparando realm, issuer, discovery, URLs, PKCE, `offline_access`/refresh, scopes `openid profile email mcp:tools`, audience **URL exata do recurso CLARA**, bindings de client scope, `resource`, proteção de token, CORS/origins, redirects exigidos pelo host, client authentication e provisioning idempotente. **Não copiar client_id/secret/audience TÉO cegamente**. Revalidar D03 e URL pública real HTTPS antes de qualquer escrita. Não criar client administrativo privilegiado na superfície MCP. Alterações de Keycloak exigem autorização administrativa e rollback/documentação.

O ChatGPT admite conexão a servidor MCP por URL HTTPS pública (ou Secure MCP Tunnel quando aplicável); plugin customizado depende das permissões/plano do workspace e pode aplicar **confirmação nativa em gravações**, independente da política conversacional da CLARA. Não prometer remover essas confirmações do host. Referência externa: https://help.openai.com/pt-br/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

### Ficha de configuração a entregar — valores públicos/não secretos

Entregar somente valores confirmados por read-back real e sanear os demais:

```text
CLARA_PLUGIN_NAME=CLARA — Especialista em Controladoria & Finanças
CLARA_PUBLIC_MCP_URL=<HTTPS real /apps/controllership-finance-api/mcp>
CLARA_OAUTH_ISSUER=<KEYCLOAK_ISSUER real público>
CLARA_OAUTH_AUTHORIZATION_ENDPOINT=<do discovery>
CLARA_OAUTH_TOKEN_ENDPOINT=<do discovery>
CLARA_OAUTH_JWKS_URI=<do discovery>
CLARA_OAUTH_CLIENT_ID=<identificador público aprovado>
CLARA_OAUTH_SCOPES=<escopos efetivamente aceitos>
CLARA_OAUTH_REDIRECT_URIS=<URIs confirmadas do ChatGPT no Keycloak>
CLARA_OAUTH_PKCE_REQUIRED=<true/false provado>
CLARA_OAUTH_REFRESH_TOKEN_SUPPORTED=<true/false provado>
CLARA_OAUTH_PROTECTED_RESOURCE_METADATA_URL=<HTTPS real>
CLARA_OAUTH_RESOURCE_AUDIENCE=<URL exata pública exigida>
CLARA_MCP_TOOLS_DISCOVERED=<lista verificada na conexão autenticada>
CLARA_MCP_READ_SMOKE=<PASS/FAIL/TEST_NOT_RUN>
CLARA_MCP_ACT_SMOKE=<PASS/FAIL/TEST_NOT_RUN/BLOCKED>
CLARA_CORPUS_PUBLISHED_VERSION=<versão real ou NOT_RUN>
CLARA_RELEASE_SHA=<SHA implantado ou NOT_DEPLOYED>
CLARA_KEYCLOAK_CHANGE_EVIDENCE=<ref de auditoria sem credenciais>
CLARA_G2_EVIDENCE=<identificador de aceite humano ou PENDING>
CLARA_G3_EVIDENCE=<identificador de autorização do operador ou PENDING>
```

**Segredos:** não retornar `.env`, senhas de admin, tokens, refresh tokens, client secret, service token ou configurações sensíveis em chats, logs, docs, MCP responses ou relatórios. Se o cadastro exigir secret, retornar SOMENTE `SECRET_REQUIRED=true` e referência segura do cofre + instrução de transferência por canal protegido; não exibir o valor. O usuário configurará/instalará o plugin no ChatGPT por sua própria interface, após teste e disponibilidade.

### Deploy e rollback

Consultar `infra/README-ambiente.md`, `infra/scripts/up-prod-sequential.sh` e a authority SSH antes de escolher comandos. Operador confirma backup PostgreSQL, uploads e corpus, Keycloak config export/rollback, migrations V004–V011, schema, health do gateway, planos de falha, migrações irreversíveis e read-back. Proibir alteração de produção ou Keycloak sem G2/G3. Smoke inclui permissões Core, portal, data persistente, OAuth discovery, MCP transporte, conhecimentos e ACT somente em cenário autorizado de teste. HTTP 200 sozinho não comprova outcome.

## 5. Contratos de aceitação

- P1–P6, R01–R15 e T03/T05 reais: estados honestos; relatórios oficiais só quando paridade e validação do owner forem demonstradas. MP4/transcrição e arquivos brutos não alegados como ingeridos sem acesso real.
- CLARA: paridade READ com a BFF do mesmo ator/escopo; corpus com fonte/hash/citação; instruções não confiáveis de arquivos não viram comandos; lotes sem confirmações redundantes mas com consentimento verificável e guardrails; capabilities anunciadas somente quando fisicamente operantes.
- 0 nova permission além de `controllership-finance.access` e `controllership-finance.manage`.
- G1 resolve decisões materiais; G2/G3 ficam `PENDING` até evidência real. `NO_DEPLOY` se qualquer preflight obrigatório falhar. ChatGPT plugin cadastro/teste: após deployment real, sujeito a disponibilidade/plano do ChatGPT.
- Próxima documentação runtime deve linkar SHAs, testes, matriz RQ/AC, evidências G1–G3 e riscos, sem declarar PASS por smoke não executado.

## 6. Execução solicitada ao Devin

Rodar **um programa contínuo**: inventário único HEAD/status/rules + Plano 106 → documento de contrato de lote e G1 focado → corrigir READ/ACT + implementar lote e testes → terminar integrações autorizadas do fechamento e conhecimento CLARA → gates G2/G3 → Operador SSH/Keycloak/deploy autorizado → ficha ChatGPT e smoke. Documentar `DECISION_REQUIRED` real e continuar tarefas independentes. Não retornar um plano em lugar de executar as etapas autorizadas. No entanto, **não** aprovar o próprio gate, tomar decisão de owner externo ou simular acesso/configuração produtiva.

---

## Adendo — evidência de implementação (CF-PROC0072-CLARA-BATCH-RELEASE-001)

Registro do executor sobre o que foi construído e provado nesta execução.
Tudo abaixo deriva de código versionado e testes PostgreSQL reais; gates
humanos permanecem `PENDING` até evidência externa.

### Implementado e verificado

| Item | Estado | Evidência |
|---|---|---|
| Fluxo `USER REQUEST → DISCOVERY → PLAN → PREPARE_BATCH → VERIFIED CONSENT → EXECUTE → VERIFY → REPORT` | IMPLEMENTED | `application/clara/batch_orchestrator.py` (`plan_batch`/`prepare_batch`/`confirm_batch`/`execute_batch`/`batch_status`) |
| Consentimento consolidado único (Modo B) | IMPLEMENTED + TESTED | `confirm_batch` vincula `plan_hash` exato; `CLARA_BATCH_CONFIRMED` na auditoria |
| Host attestation (Modo A) | CONTRACT IMPLEMENTED / MECHANISM `NOT_CONFIGURED` | HMAC `plan_hash|actor_sub|expires_at` sob `CLARA_HOST_ATTESTATION_SECRET`; sem segredo → `host_attestation_unavailable` (fail-closed 503). Gate Segurança/Plataforma `PENDING` |
| Claim durável antes do efeito (S1) | IMPLEMENTED + TESTED | `clara_proposal.claimed_at` + `execution_state`; dois ACTs concorrentes → um vencedor (`test_two_concurrent_acts_single_winner`) |
| Snapshot fail-closed (S2) | IMPLEMENTED + TESTED | `SnapshotUnavailable` (503); recurso inexistente/indisponível bloqueia PREPARE/PLAN |
| Read-back independente (S3) | IMPLEMENTED + TESTED | `postcondition` por capability relê o recurso (`closing_review_decision`, `closing_clarification`, item state) |
| Autorização efetiva (S4) | PRESERVED | execução delega aos repositórios canônicos — `reviewer_not_assigned` tipado provado em lote |
| Escopo do corpus (S5) | FIXED + TESTED | `list_sources` só enumera fontes com ≥1 item visível ao escopo do chamador |
| Prompt-injection (S6) | DESIGNED | instruções MCP tratam conhecimento/tool results como dados não confiáveis; plano só aceita `operations` explícitas do chamador |
| Lote: 2/5/20 operações | TESTED | `test_batch_two/five/twenty_*` — `COMPLETED`, idempotency keys únicas |
| Dependentes/independentes | TESTED | falha → dependentes `BLOCKED`, independentes `VERIFIED` (`COMPLETED_WITH_FAILURES`) |
| Execução concorrente | TESTED | segundo `execute_batch` sem `resume` → `BatchTerminal`; perda de claim por operação reporta estado observado |
| Retomada/efeito desconhecido | TESTED | `resume=True` reconcilia CLAIMED por read-back → `VERIFIED` ou `UNKNOWN` (nunca repete efeito) |
| Schema | V012 | `clara_batch`, `clara_batch_operation`, `clara_proposal.claimed_at`/`execution_state`/`batch_operation_id` |
| Tools MCP | 18 | `prepare_batch`(PREPARE), `confirm_batch`(PREPARE), `execute_batch`(ACT, destructive), `get_batch_status`(READ) |
| Keycloak `mcp-clara` | PROVISION PATH READY / `NOT_CONFIGURED` | specialist adicionado ao engine compartilhado `delia_mcp_keycloak_state.py` (`--check`/`--apply` pelo Operador pós-G3); runbook `controllership-finance-api/docs/integrations/keycloak-mcp-client-runbook.md` |

### Testes executados

- `tests/test_pg_clara_batch.py` — 23 testes PostgreSQL reais (plano, consent, execução, concorrência, retomada, falhas, relatório).
- Suíte completa `controllership-finance-api`: **569 passed** (546 anteriores + 23 lote).
- `infra/scripts/tests/test_delia_mcp_keycloak_state.py`: **27 passed** com `mcp-clara`.
- `tests/test_clara_mcp_surface.py`: **13 passed** (18 tools, taxonomia, securitySchemes, instruções multiação).

### Pendente de gates externos (não simuláveis)

- G1: contrato físico Modo A (Segurança/Plataforma); T03; fontes oficiais R04+; T05; seeds/catálogos; OVW.
- G2: aceite humano — `PENDING`.
- G3: autorização do operador — `PENDING`. Deploy, `--apply` Keycloak, ingestão de corpus prod e smoke autenticado somente após G2+G3.
- `OAUTH_REDIRECT_URIS` / `MCP_PUBLIC_URL` verificados / ficha ChatGPT final: `NOT_CONFIGURED` — redirect URI só existe após o fluxo real de cadastro no ChatGPT.

## Adendo 2 — consentimento por superfície confiável (V013, step-up)

Registro da segunda etapa da execução
`CF-PROC0072-FULL-IMPLEMENTATION-RELEASE-001`: o bypass de
consentimento identificado na seção §3.1 foi encerrado — a chamada
MCP autenticada **deixou de ser** prova de consentimento.

### Decisão arquitetural aplicada

O Portal/MFE autentica na BFF por Bearer token puro (sem cookie+CSRF).
O access token MCP do assistente antecede o PREPARE e não se renova;
o refresh token vive na sessão Keycloak do Portal. Logo, a evidência
fisicamente verificável adotada é **step-up por token fresco**: a
página de consentimento do Portal re-emite a sessão Keycloak e a BFF
exige `iat >= created_at` do artefato selado — credencial que o canal
do assistente não consegue produzir.

### Implementado e verificado

| Item | Estado | Evidência |
|---|---|---|
| Bypass `CONSOLIDATED` auto-conferido pela chamada MCP | **CLOSED** | `confirm_batch` sem attestation agora exige `consent_record` `portal_step_up` gravado pela BFF; ausente ⇒ `consent_required` (403) + `confirmation_url` (`test_direct_mcp_confirm_without_portal_consent_rejected`) |
| `consent_required` com deep link | IMPLEMENTED | `prepare`/`prepare_batch` retornam `confirmation_url` = `/apps/controllership-finance/closing/clara-consent?batch=<id>\|proposal=<id>` |
| Step-up service | IMPLEMENTED + TESTED | `application/clara/step_up_consent.py` — ator, `plan_hash`/`capability` exatos, `iat` posterior ao PREPARE (±skew), `iat` futuro rejeitado |
| Rotas BFF confiáveis | IMPLEMENTED | `interface/http/routes/clara_consent_routes.py` — `GET /clara/batches/{id}`, `POST /clara/batches/{id}/consent`, `GET /clara/proposals/{id}`, `POST /clara/proposals/{id}/consent`; revalida Bearer via `validate_token` canônico + `authorized_user` |
| `commit_proposal` sem consent | **CLOSED** | `governed_writes.commit` exige `consent_record` portal_step_up antes do claim; proposta de lote rejeitada fora do `execute_batch` |
| `resume` em proposta CLAIMED | IMPLEMENTED + TESTED | `commit(resume=True)` reconcilia por read-back: pós-condição provada ⇒ `VERIFIED`; não provada ⇒ `UNKNOWN` terminal — nunca repete efeito (`test_commit_resume_*`) |
| Schema | **V013** | `clara_proposal.consent_record`/`consented_at`; `clara_batch.consent_record`/`confirmed_at` (colunas já existentes reutilizadas) |
| Superfície Portal/MFE | IMPLEMENTED | `AuthContext.getFreshAccessToken()` (Keycloak `updateToken(60)`) → `AppHost` → `httpClient.httpPostStepUp`; `ClaraConsentPage` (rota `closing/clara-consent` no manifest, oculta da navegação) com Help contextual |
| Boolean/texto como consentimento | NEVER | nenhum parâmetro de confirmação nas tools; `confirm_batch(batch_handle, plan_hash, attestation)` e `commit_proposal(proposal_handle, resume)` — schemas sem flag de consentimento |
| plan_hash divergente pós-consent | TESTED | `test_plan_expansion_rejected` — `plan_hash divergente` tipado; hash correto confirma |
| Attestation (Modo A) | PRESERVED | contrato HMAC inalterado, fail-closed sem segredo |

### Testes executados nesta etapa

- PostgreSQL real (container efêmero, `pgvector/pgvector:pg15`):
  **920 passed** — `test_pg_clara.py` (incl. 6 testes novos de
  consent/step-up/UNKNOWN) + `test_pg_clara_batch.py` (incl.
  `test_direct_mcp_confirm_without_portal_consent_rejected`) + toda a
  regressão P1–P6 com migrations V001–V013.
- `test_clara_mcp_surface.py`: **13 passed**.
- MFE `controllership-finance`: **715 vitest + 52 tsx/test.mjs**
  (`ClaraConsentPage` 5 testes; manifest contract com rota nova) e
  `npm run build` verde.
- Portal: `tsc -b` limpo (AuthContext/AppHost).

### Notas de contrato

- O token step-up é verificado por `iat` (não por claim inventado):
  só a sessão Portal com refresh consegue `iat >= created_at`.
- `record_consent` é escrita exclusiva da superfície BFF — repositório
  rejeita consentimento em proposta já claimed/consumed ou vinculada
  a lote (consentimento consolidado pelo lote).
- Execução segue revalidando autorização canônica (Core/eligibility/
  assignment/scope/business rules) — consentimento nunca substitui
  autorização.


## Adendo 3 — prioridade de aceite real no ChatGPT, 25/10/2026

A decisão posterior do PO está em [Documento 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md): priorizar disponibilização do MCP **em ambiente de teste autorizado**, após corrigir prova de consentimento/visualização do plano, para que o usuário teste a CLARA no ChatGPT **antes** de G2/G3 de produção. Isso não altera a exigência de G2 humano e G3 Operador SSH para configuração e deploy produtivos. A ficha ChatGPT deve separar valores de TESTE e PROD, com verificações reais, sem secrets. O prazo de hoje é meta, não autorização inferida nem PASS. Nova decisão material/alteração de estado deve atualizar a documentação do GitHub antes de ser declarada encerrada.
## Adendo 4 — Consent challenge V014 (R-CLARA-01/R-CLARA-02)

`EXECUTION_ID: CF-PROC0072-CLARA-CONSENT-FINAL-REWORK-001` —
rework final do consentimento solicitado pelo PO após revisão
independente da entrega `d59e972a`. Duas falhas corrigidas na
mesma entrega, sem reconstruir MCP, orquestrador, Keycloak engine
ou fluxo P1–P6.

### Problema anterior e causa raiz

| Falha | Causa raiz |
|---|---|
| **R-CLARA-01** — consentimento excessivamente inferido do JWT | `record_*_consent` aceitava como prova de aprovação humana um `iat` posterior ao `created_at` do artefato (±skew ~10s). Um JWT recém-emitido prova apenas **sessão fresca**, não manifestação humana sobre um plano específico — qualquer superfície capaz de obter token fresco poderia "consentir" sem exibir o plano. |
| **R-CLARA-02** — apresentação incompleta | `ClaraConsentPage` exibia capability/tipo/UUID/estado — insuficiente para o usuário compreender o que autorizava. |

### Contrato adotado (authority: este documento + Doc 14)

Separação explícita de provas:

```text
identidade autenticada   → Bearer canônico (validate_token) + authorized_user
sessão válida            → middleware FastAPI canônico
frescor de autenticação  → iat do token step-up ≥ challenge.created_at
aprovação humana         → clara_consent_challenge APPROVED (só via BFF)
vínculo ao plano         → challenge.actor_sub + batch_id/proposal_id +
                           plan_hash + plan_version exatos
consumo único            → challenge CONSUMED na mesma transação do claim
```

**`clara_consent_challenge` (V014)** é o artefato de autorização:
`challenge_id` aleatório emitido no PREPARE, `actor_sub`,
`batch_id`/`proposal_id`, `plan_hash`, `plan_version`, `created_at`,
`approved_at`, `expires_at`, `consumed_at`, `status`
(`PENDING→APPROVED→CONSUMED`, `EXPIRED`), `origin`,
`correlation_id`, `approved_by`, `approved_jti`. Nenhum boolean ou
texto no chat autoriza; o modelo não recebe nem pode produzir o
challenge — ele vive entre PREPARE (servidor) → Portal (BFF) →
consumo (transação de claim).

### Fluxo físico

```text
PREPARE (prepare/prepare_batch)
  → selo do plano (plan_hash + plan_version)
  → issue_challenge(actor, artefato, plan_hash, version, ttl)
  → resposta: challenge_id + confirmation_url + apresentação
Portal (clara-consent?batch|proposal=<id>)
  → GET /clara/{batches|proposals}/{id} → plano completo + challenge
  → usuário lê descrição funcional de CADA operação + bloqueadas
  → getFreshAccessToken() (Keycloak updateToken) + POST consent
    {challenge_id}
BFF (clara_consent_routes)
  → validate_token canônico (iat/jti) + authorized_user
  → approve_atomically: valida ator, artefato, plan_hash,
    plan_version, origem, expiração, status; 1ª aprovação vence
    corrida (idempotente no mesmo challenge+ator)
confirm_batch / commit (MCP)
  → lê consent_record do artefato + challenge
  → claim transacional consome o desafio (FOR UPDATE, single-use)
  → execução segue revalidando permissões/regras por operação
```

Permissão revogada entre aprovação e execução continua falhando —
consentimento **nunca** substitui autorização canônica.

### Implementação

| Item | Estado |
|---|---|
| Migration | **V014** `clara_consent_challenge` — constraints de vínculo (exactly-one de batch/proposal), status enum, índices (pendentes por ator/artefato, correlation) |
| Repositório | `clara_consent_challenge_repository.py` — `issue`, `get`, `approve_atomically` (UPDATE condicional `status='PENDING' AND expires_at>now`), `consume` (FOR UPDATE na tx do claim) |
| Apresentação (R-CLARA-02) | `operation_presentation.py` — descrição funcional PT por capability (resumo/efeito/motivo/labels de domínio); operações indescritíveis viram `blocked` com impedimento "apresentação indisponível" |
| `step_up_consent` | `record_*_consent` exige `challenge_id`; `iat` verificado **contra o desafio**, não como prova isolada; idempotência honesta (mesmo challenge+ator ⇒ estado vigente); GETs devolvem plano selado + challenge |
| `batch_orchestrator` | emite desafio no `prepare_batch`; `confirm_batch` exige challenge `APPROVED` vinculado ao `plan_hash` exato; consumo no claim do `execute_batch` |
| `governed_writes` | emite desafio no `prepare` single-op; `commit` verifica consent_record + challenge e consome no claim atômico; resume/UNKNOWN preservado |
| Rotas BFF | POST consent aceita `{challenge_id}` (400 sem ele); GET devolve `operations[].presentation`, `totals`, `challenge`, `consentable`, `expires_at` |
| MCP | schemas inalterados — nenhum parâmetro de confirmação; `confirm_batch`/`commit_proposal` nunca recebem flag do modelo |
| Attestation (Modo A) | PRESERVED — contrato HMAC inalterado, fail-closed sem segredo |
| Frontend | `ClaraConsentPage` reescrita: resumo do lote (competência, ator, totais, expiração, plan_hash/version), uma linha por operação com descrição funcional + efeito + motivo + dependências + estado, bloqueadas com impedimento, **um único botão** «Autorizar N operações», estados loading/erro/expirado/recusa/sucesso/já-confirmado acessíveis; `claraConsentApi` envia `{challenge_id}` via `httpPostStepUp` |
| Ajuda | `helpTooltips` atualizado no mesmo commit |

### Testes executados

PostgreSQL real (container efêmero `pgvector/pgvector:pg15`,
migrations V001–V014):

- **61/61** `test_pg_clara.py` + `test_pg_clara_batch.py`,
  incluindo os novos: criação/binding do desafio, ator errado,
  lote errado, plan_hash divergente, versão divergente, expiração,
  reutilização pós-consumo, confirmação MCP direta sem consent do
  Portal, ACT de lote sem consent, injection `confirmed=true`
  rejeitada, idempotência de dupla submissão, concorrência de
  aprovação (1 vencedor), consumo single-use no claim, permissão
  revogada entre aprovação e execução, lotes 2/5/20 operações com
  dependências e falha parcial, reconciliação `CLAIMED→UNKNOWN`.
- **Contrato HTTP real** (`TestClient` sobre a app FastAPI,
  middleware de auth efetivo — só a assinatura JWT é substituída
  pelo validator canônico em teste): GET com plano+challenge, POST
  sem `challenge_id` ⇒ 400, token anterior ao desafio ⇒ 403,
  happy path ⇒ CONFIRMED + APPROVED, ator alheio ⇒ 403.
- **Regressão completa `tests/`**: 595 passed.
- `test_clara_mcp_surface.py`: 13 passed (18 tools, schemas sem
  flag de consentimento).
- MFE: 177 vitest + 25 tsx/mjs — `ClaraConsentPage` 7 testes
  (resumo, descrições, bloqueada, expirado, sessão, recusa,
  sucesso, consentimento único, ator divergente); `npm run build`
  verde; Portal `tsc -b` limpo.

Não executado (honesto): E2E no ChatGPT real e deploy produtivo —
aguardam G2/G3.

### Residual conhecido

- `iat` segue como evidência auxiliar de frescor de sessão
  (janela de segundos); a prova de aprovação é o desafio —
  um token fresco sem aprovação registrada não autoriza nada.
- O `challenge_id` é um bearer secret de curta duração vinculado
  ao ator+sessão; não é secret de plataforma e nunca sai para o
  canal MCP.
- Modo A (HMAC host attestation) preservado sem alteração de
  contrato — gate físico do host segue pendente de owner.

SHA: `FINAL_HEAD` do commit desta entrega em `main`
(registrado no relatório CF-PROC0072-CLARA-CONSENT-FINAL-REWORK-001).
