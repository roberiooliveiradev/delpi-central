# 45 — G0: exceção arquitetural FastAPI e fechamento dos gates de implementação

> **Documento de decisão e preparação de gate. Não declara PASS/YES.**
> HEAD de referência: `f8a07952868efd8e8e912b23020bd4c9063a3a81` (main, 2026-11-04).
> Escopo: somente documentação. Nenhum runtime, scaffold, manifest, permission ou wiring criado.

## 1. Registro da exceção arquitetural — FastAPI

**Decisão registrada:** `controllership-finance-api` será implementada em **FastAPI**.

| Campo | Valor |
|---|---|
| Escopo da exceção | **Exclusivamente** `controllership-finance-api`. Não altera o padrão global do projeto. |
| Aprovação | Product Owner, registrada nos briefs IMP-01 (framework selecionado pelo PO). |
| Autoridade divergente | `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md` declara *"Flask (padrão do projeto)"* como backend. |
| Estado | `REGISTERED` — **validação formal por Arquitetura ainda pendente.** |

### Evidência objetiva da divergência autoridade × runtime

| Fato medido no HEAD | Evidência |
|---|---|
| 16/20 serviços `*-api` usam FastAPI | inventário de runtime (CF-F0/IMP-00) |
| Primitive canônico de AuthZ com consumidores reais é FastAPI | `shared/delpi_auth/middleware/fastapi_auth.py`, `shared/delpi_auth/authorization.py`, `shared/delpi_auth/authz_core.py` + `shared/delpi_auth/tests/` |
| `flask_auth.py` é claims-only e órfão para este padrão | violaria a regra "JWT não é authority de permissions" (README §1) |
| BFFs de Portal referência (commercial, financial, purchase-requests) são FastAPI | `commercial_app/main.py`, `financial_app/main.py` |
| `require_permission` já implementa semântica fail-closed canônica | `_deny_missing_permission` → 503 quando `rbac_unavailable`, 403 quando sem permissão (`authorization.py`) |

### Condição de validação

A exceção fica `VALIDATED` quando Arquitetura registrar aceite — seja emendando a authority central, seja aceitando este documento como o registro formal do desvio escopado. **Este documento não edita a instrução global** por decisão de escopo: a autoridade para mudar o padrão do projeto não pertence a este registro.

## 2. Matriz de evidência dos quatro freezes

| Freeze | Evidência documental | Estado de evidência | Assinatura pendente |
|---|---|---|---|
| `PORTAL_DESIGN_FREEZE` | docs 24, 25–29, 30, 31, 32; reuse map com binding PROVEN (`createDashboardPortalUserProfilePage` + `PortalUserProfilePage.test.tsx` em `@delpi/plugin-ui`); padrão visual plataforma | `DOCUMENTED` | Design/PO declara PASS |
| `PRODUCT_CONTRACT_FREEZE` | README §1 identidade congelada; doc 31 contrato A01 (rotas, DTO, erros, estados); doc 23 ledger RQ/AC; docs 39–42 slices/roadmap; D1=B, D2=A aprovadas | `DOCUMENTED` | PO declara PASS |
| `SECURITY_MODEL_FREEZE` | doc 14; contratos Core S2S PROVEN no HEAD (effective-access dedicado, directory lookup com filtro `app`, person-profiles + photo); fail-closed provado contra middleware real (`rbac_unavailable`→503, permissions vazias em outage); tokens S2S separados por secret | `DOCUMENTED` + 1 residual (§4) | Security owner declara PASS |
| `TEST_STRATEGY_FREEZE` | doc 41 estratégia/gates; doc 23 matriz RQ/AC; matriz IMP-01 definida (positive/sibling/negative/security/integration/routes/operations/contract) | `DOCUMENTED` | Quality declara PASS |

> Evidência `DOCUMENTED` ≠ `PASS`. O freeze só fecha por declaração humana do owner competente, registrada no README canônico.

## 3. Bloqueios transversais × exclusivos de páginas futuras

### Transversais (bloqueiam qualquer implementação)

1. `FASTAPI_ARCHITECTURAL_EXCEPTION` → `REGISTERED`, validação Arquitetura pendente (§1).
2. Quatro freezes → evidência pronta (§2), assinatura pendente.
3. `DOCUMENTATION_CLOSURE_COMPLETE` → `NO`.
4. `IMPLEMENTATION_AUTHORIZED` → `NO`.

### Exclusivos de A01

Nenhum bloqueio técnico remanescente: todos os bindings Core S2S, plugin-ui e federation foram `PROVEN` em inventário (IMP-00). A01 aguarda apenas os gates transversais.

### Exclusivos de páginas futuras (NÃO bloqueiam A01)

- T05 elegibilidade de revisor corporativo (P5); vínculo de coordenador por competência;
- T01 `api-delpi` (P3); T03 fonte ERP/cutoff; T04 envio;
- T02 notificações; snapshots/DTO/OCC P5–P6.

## 4. Residual de segurança — política stale RBAC para A01 (registrado, NÃO aceito)

Comportamento medido em `shared/delpi_auth/middleware/fastapi_auth.py`:

| Cenário | Comportamento do primitive | Avaliação para A01 |
|---|---|---|
| Core `/me` falha **sem** cache | `rbac_unavailable=True`, `permissions=[]` → `require_permission` nega → **503** (`_deny_missing_permission` + `map_authz_exception`) | Fail-closed correto — autorização não é substituída por claims |
| Core `/me` falha **com** cache válido | serve RBAC até `RBAC_STALE_TTL` (default **900s**) | Staleness bounded; permissão revogada pode persistir até 15 min |
| Service token interno | mint `is_superadmin=True`, `principal_type="service"` | Rotas de usuário devem rejeitar `principal_type != "user"` (padrão financial-api, principal escopado) |
| `load_user_rbac(force_refresh=True)` | desabilita stale fallback, fail-closed para writes | Disponível se futuras rotas de escrita exigirem |

**Pendência de decisão (Security owner):** aceitar staleness ≤900s para reads de A01 **ou** exigir tratamento adicional no BFF (ex.: `force_refresh` também no read path, com custo de latência/disponibilidade). **Não declarar aceitação automática.** Qualquer alteração em `shared/delpi_auth` exige inventário de consumers e autorização separada.

## 5. Semântica operacional proposta para `/ready`

Coerente com o padrão `commercial-api` (`/ready` retorna 200 com `status: ready|degraded` e hint, em vez de 5xx incondicional):

| Elemento | Proposta |
|---|---|
| `/health` | `{status:"online", service:"controllership-finance-api"}` — liveness trivial, sem secrets |
| `/ready` | `{status:"ready"\|"degraded", service, config_ready, core_hint?}` |
| `config_ready` | `true` somente se `CORE_API_BASE_URL` + `CORE_API_INTEGRATIONS_SERVICE_TOKEN` + `CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN` + `KEYCLOAK_ISSUER`/`AUDIENCE`/`JWKS_URL` configurados |
| `core_hint` | mensagem de orientação quando dependência ausente/indisponível (sem valores de secrets) |
| DB check | **ausente** — A01 não possui persistência; não inventar dependência artificial |
| HTTP code | 200 com `status` honesto, espelhando o padrão da plataforma |

## 6. Proposta mínima de atualização do README canônico (aguardando aprovação)

```text
Na tabela "2. Estado vigente e gates", adicionar a linha:
| `FASTAPI_ARCHITECTURAL_EXCEPTION` | `REGISTERED` — doc 45; validação Arquitetura pendente |

E no mapa de fontes, linha adicional:
| Decisões de implementação G0 | [45 — Exceção FastAPI e gates](./45-g0-excecao-fastapi-e-fechamento-gates.md) |
```

Os demais valores do painel permanecem `NO`/`PENDING` até declaração humana.

## 7. Decisões humanas pendentes (GO/NO-GO)

| # | Decisão | Owner | Necessária para |
|---|---|---|---|
| D-G0-01 | Validar exceção FastAPI (`VALIDATED`) — aceitar doc 45 como registro formal ou emendar authority | Arquitetura | qualquer runtime |
| D-G0-02 | Declarar os quatro freezes `PASS` com base na matriz §2 | Design/PO/Security/Quality | qualquer runtime |
| D-G0-03 | `DOCUMENTATION_CLOSURE_COMPLETE = PASS` | PO / Product Master | qualquer runtime |
| D-G0-04 | `IMPLEMENTATION_AUTHORIZED = YES` para IMP-01 | PO | fundação da BFF |
| D-G0-05 | Aceitar ou condicionar a política stale-RBAC para reads A01 (§4) | Security owner | fundação da BFF |
| D-G0-06 | Confirmar semântica `/ready` proposta (§5) | Arquitetura/Ops | fundação da BFF |

**NO-GO permanece o estado vigente** até que D-G0-01..04 estejam resolvidas. D-G0-05 pode bloquear A01 especificamente se a política exigir tratamento adicional no BFF.


## 8. Revisão técnica de prontidão para IMP-F0 — 19/10/2026

> **TECHNICAL_REVIEW=DOCUMENTED / GATE_STATUS=NO-GO.** Esta revisão consolida critérios verificáveis e recomendações técnicas; não constitui assinatura de Arquitetura, Segurança, Qualidade ou PO. Não altera os estados do painel do README.

**Escopo revisado:** fundação inicial da `controllership-finance-api` (FastAPI, Docker, `GET /health`, `GET /ready`), antes do MFE/Home. Não inclui A01 perfil nem P1–P6, persistência, endpoints de negócio ou novas permissões.

| Critério | Evidência e decisão técnica proposta | Status |
|---|---|---|
| Framework e arquitetura | Comercial API e Financial API usam FastAPI; respeitar instrução oficial Flask por exceção específica registrada em §1, com aceite explícito de Arquitetura | `REGISTERED / PENDING VALIDATION` |
| AuthN/AuthZ | `.cursor/rules/platform-security-identity-authorization.mdc` exige shared `delpi_auth`, issuer/audience, Core effective permissions, fail-closed; serviço não deve herdar superadmin humano | `CONTRACT DOCUMENTED / TEST_NOT_RUN` |
| API/OpenAPI | `.cursor/rules/platform-api-contracts-integration.mdc`: `operation_id` literal e único, schemas/erros estáveis, teste de contrato, public-path coerente com middleware | `CONTRACT DOCUMENTED / TEST_NOT_RUN` |
| `/health` | Liveness explícito, público somente conforme middleware, sem secrets e sem acoplamento a Core/DB | `TARGET` |
| `/ready` | Semântica depende dos consumidores de healthcheck/gateway. `200 + degraded` não demonstra prontidão para receber tráfego; inspecionar orquestrador antes do aceite D-G0-06 | `DECISION_REQUIRED` |
| stale RBAC | Cache exposto em §4: comportamento de 900s não está automaticamente autorizado para reads protegidos. Definir política por Security owner; evitar aceitar stale como equivalente a autorização atual | `DECISION_REQUIRED` |
| Build e container | Seguir Dockerfile/Compose do commercial, `shared/delpi_auth`, gateway e configuração real; nenhuma prova de build, deploy ou smoke desta BFF | `TEST_NOT_RUN` |
| Validação | Testes AuthN/negação, public-path, config inválida, health/ready, build Docker e smoke gateway são obrigatórios após autorização | `TEST_NOT_RUN` |

**Ordem obrigatória para fechamento:** D-G0-01 Arquitetura; D-G0-05 Segurança e D-G0-06 Arquitetura/Ops; D-G0-02 aprovações de cada freeze com owner e evidência; D-G0-03 fechamento documental PO; **depois** D-G0-04 autorização explícita PO exclusivamente para IMP-F0. A escolha pelo PO de priorizar API → container → Home não é autorização automática de runtime.

**Condição de mudança do README:** registrar owner/decisão/data/referência para cada aprovação. Na falta de qualquer uma, manter `PENDING` / `NO`. Não inferir `PASS` de documentação, tests não executados, search miss ou HTTP 200. A tarefa de implantação deve revalidar HEAD e worktree antes de qualquer alteração.

## 9. Fechamento decisório — inspeção do orquestrador e matriz final (HEAD `1156cc7ce2`)

> Preparação para assinatura humana. Nenhum valor abaixo constitui aprovação; cada decisão exige declaração do owner registrada no README com evidência e data.

### 9.1 `/ready` — evidência do orquestrador (D-G0-06, resolvido para proposta)

A revisão §8 exigiu inspecionar consumidores de healthcheck/gateway. Resultado medido no HEAD:

| Fato | Evidência |
|---|---|
| Healthchecks Docker de **todos** os `*-api` consultam somente `/health` | `infra/docker-compose.yml` — `urllib.request.urlopen('http://127.0.0.1:8000/health')` em commercial-api e pares |
| `/ready` **não é consumido** por healthcheck de Compose nem scripts `up-*-sequential.sh` | grep `ready` nos compose/scripts: apenas `pg_isready` do Postgres |
| Gateway é nginx com `proxy_pass` estático por `location ^~ /apps/<svc>-api/` | `gateway/nginx.conf:465` (commercial-api), upstream `<svc>:8000`, rewrite do prefixo |
| Nginx resolve upstream no start/reload — serviço novo exige `gateway_reload_for_service` | `infra/scripts/gateway-static-upstreams.sh` |
| `/ready` da commercial retorna 200 + `status: ready|degraded` + hint | `commercial_app/main.py:165` |

**Conclusão técnica:** `/ready` é **diagnóstico operacional**, não gate de tráfego — o orquestrador confia em `/health`. A proposta do §5 (HTTP 200 + `ready|degraded` + `config_ready` + `core_hint`, sem DB artificial, sem secrets) é **coerente com o precedente e não cria semântica falsa**. Resta apenas o aceite formal de Arquitetura/Ops.

### 9.2 Wiring operacional confirmado para IMP-F0

Quando autorizado, a integração exige exatamente: (a) entry em `infra/docker-compose.yml` seguindo o padrão `commercial-api` (env_file `.env`, envs `*_ROOT_PATH`, `DELPI_AUTH_CORE_API_URL`, `KEYCLOAK_*`, `CORE_API_*_SERVICE_TOKEN`, healthcheck `/health`); (b) bloco `location ^~ /apps/controllership-finance-api/` em `gateway/nginx.conf` e `nginx.dev.conf` com o padrão de rewrite/headers/rate-limit; (c) reload do gateway via `gateway_reload_for_service` (operacional, `local-first-deploy.mdc`).

### 9.3 Matriz decisória final

| ID | Decisão | Owner | Evidência pronta | Condição de aprovação | Estado |
|---|---|---|---|---|---|
| D-G0-01 | Validar exceção FastAPI escopada | Arquitetura | §1 + runtime 16/20 FastAPI + primitive `delpi_auth` FastAPI | Declaração `VALIDATED` no README ou aceite explícito do doc 45 | **PENDING** |
| D-G0-02 | Quatro freezes | Design / Produto / Segurança / Qualidade | §2 por freeze | Quatro `PASS` com owner+data no painel | **PENDING** |
| D-G0-03 | `DOCUMENTATION_CLOSURE_COMPLETE` | PO / Product Master | corpus 00–45 consolidado | `PASS` no painel | **PENDING** |
| D-G0-04 | `IMPLEMENTATION_AUTHORIZED` — **escopo reduzido a IMP-F0** | PO | este documento | `YES` explícito limitado a: BFF FastAPI + Dockerfile + `/health` + `/ready` + testes + wiring compose/gateway. **MFE/Home/A01 continuam bloqueados** | **PENDING** |
| D-G0-05 | Política stale-RBAC | Segurança | §4 + §8 | Para IMP-F0 a decisão é **não-bloqueante**: `/health` e `/ready` são rotas públicas sem dados protegidos — staleness não aplica. Decisão exigida antes da **primeira rota protegida** (Home/A01) | **PENDING — não bloqueia IMP-F0** |
| D-G0-06 | Semântica `/ready` | Arquitetura/Ops | §9.1 — proposta validada contra orquestrador real | Aceite da proposta §5 | **PENDING — proposta pronta** |

### 9.4 Gate final proposto ao PO

```text
Ordem de fechamento (preserva §8):
1. Arquitetura: D-G0-01 VALIDATED
2. Arquitetura/Ops: D-G0-06 aprovado (proposta já evidenciada)
3. Owners: D-G0-02 — 4 freezes PASS
4. PO: D-G0-03 PASS
5. PO: D-G0-04 YES — escopo exclusivo IMP-F0 (BFF + Docker + health/ready + testes)

D-G0-05 permanece aberta e bloqueia somente rotas protegidas futuras.
```

**Estado vigente: NO-GO.** Todas as decisões acima aguardam declaração humana; este documento não as substitui.

## 10. Registro final de aprovação — 2026-10-19 (HEAD `45721cedec`)

### 10.1 Manifestação do PO registrada

> **"Aceito com residuais o fechamento técnico apresentado"** — PO, 2026-10-19, sobre §8–§9.

Efeitos registrados da manifestação (não é assinatura de gates):

| Item | Posição do PO | Efeito |
|---|---|---|
| D-G0-06 | **Tecnicamente sustentada** pela evidência do orquestrador (§9.1) | Proposta aprovada em revisão técnica; **formal de Arquitetura/Ops continua pendente** |
| D-G0-05 | **Não bloqueia IMP-F0** enquanto não houver endpoints protegidos | `/health` e `/ready` públicos, sem leitura RBAC; decisão de Segurança permanece **obrigatória antes da primeira rota autenticada** |
| Escopo IMP-F0 | Confirmado: FastAPI + Dockerfile + Compose/gateway + `/health` + `/ready` + testes | Frontend, endpoints de negócio, A01 e P1–P6 **fora de escopo** |

### 10.2 Residuais isolados por slice

| Residual | Bloqueia IMP-F0? | Bloqueia |
|---|---|---|
| D-G0-01 exceção FastAPI (`VALIDATED`) | **Sim** — runtime não pode existir sem a exceção validada | qualquer código da BFF |
| D-G0-02 quatro freezes | **Sim** — gate transversal | qualquer runtime do Portal |
| D-G0-03 fechamento documental | **Sim** | qualquer runtime do Portal |
| D-G0-04 autorização de implementação | **Sim** — aguarda assinatura do PO (§10.4) | IMP-F0 especificamente |
| D-G0-05 política stale-RBAC | **Não** (PO confirmou §10.1) | primeira rota autenticada (Home data, A01, P1) |
| D-G0-06 `/ready` formal | **Não** — aceito tecnicamente; registro formal residual | nenhum bloqueio de implementação; só fechamento formal |
| `is_superadmin` de service token em rotas humanas | **Não** — não há rotas humanas em IMP-F0 | design obrigatório já especificado (`principal_type=="user"`) |
| Path canônico do Cockpit P1 | **Não** | slice P1 |
| Producers T01/T03/T05, P2/P3/P5 | **Não** | dados reais do Cockpit P1 |

### 10.3 Quadro de assinaturas — registro formal

| Owner | Assina | Referência de evidência | Assinatura |
|---|---|---|---|
| Arquitetura | D-G0-01 (`VALIDATED`) + D-G0-06 (aceite formal) | §1, §9.1 | ☐ PENDENTE |
| Design | `PORTAL_DESIGN_FREEZE` = PASS | §2 (docs 24, 30, 31, 32 + plugin-ui PROVEN) | ☐ PENDENTE |
| Produto | `PRODUCT_CONTRACT_FREEZE` = PASS | §2 (README §1, doc 31, doc 23, 39–42) | ☐ PENDENTE |
| Segurança | `SECURITY_MODEL_FREEZE` = PASS + D-G0-05 (condição: antes da 1ª rota autenticada) | §2, §4, §8, §10.1 | ☐ PENDENTE |
| Qualidade | `TEST_STRATEGY_FREEZE` = PASS | §2 (docs 41, 23 + matriz IMP-F0) | ☐ PENDENTE |
| PO / Product Master | D-G0-03 `DOCUMENTATION_CLOSURE_COMPLETE` = PASS | corpus 00–45 | ☐ PENDENTE |
| PO / Product Master | D-G0-04 — autorização IMP-F0 (§10.4) | §10.4 | ☐ PENDENTE |

**Regra:** cada linha vira `PASS/YES` no README somente com owner identificado + data + referência. Manifestação em chat é registrada aqui com data; a virada do painel exige a declaração explícita.

### 10.4 Texto de autorização IMP-F0 — aguardando assinatura do PO

```text
AUTORIZAÇÃO DE IMPLEMENTAÇÃO — IMP-F0 (FUNDAÇÃO DA BFF)

Eu, PO/Product Master do Portal Controladoria & Finanças, autorizo a
implementação EXCLUSIVA do slice IMP-F0:

  - controllership-finance-api em FastAPI (exceção escopada — doc 45 §1);
  - Clean Architecture mínima, sem camadas vazias e sem persistência;
  - GET /health (liveness) e GET /ready (semântica §5/§9.1);
  - Dockerfile padrão plataforma + entry Compose + bloco gateway nginx
    /apps/controllership-finance-api/ + reload operacional;
  - testes de bootstrap, health/ready, config inválida e middleware;
  - logging sem secrets; CORS restritivo; operationId literal.

EXPRESSAMENTE FORA DE ESCOPO: plugins/controllership-finance (MFE),
Home e demais páginas, A01 Página do usuário, P1–P6, endpoints de
negócio, novas permissions, migrations, integrações ERP.

PRECONDICÕES CUMULATIVAS (o runtime só é alterado se todas valerem):
  D-G0-01 VALIDATED; D-G0-02 quatro freezes PASS; D-G0-03 PASS.

Assinatura PO: ____________________  Data: __________  HEAD: ________
```

**Estado vigente: NO-GO para IMP-F0.** Assinatura PO de §10.4 torna-se efetiva somente com D-G0-01, D-G0-02 e D-G0-03 já registrados como PASS/VALIDATED.
