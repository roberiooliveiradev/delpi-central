# 45 — G0: exceção arquitetural FastAPI e fechamento dos gates de implementação

> **Registro de decisões G0. O GO registrado em §13 vale somente para IMP-F0; não abrange rotas de negócio ou frontend.**
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


## 11. Manifestação expressa do PO — autorização condicionada de IMP-F0 (19/10/2026)

**Origem da decisão:** manifestação explícita do usuário na coordenação do Portal: *"autorizo, atualize o que tiver de ser atualiado e decidido no github. o prooximo prompt é de implementação"*. Esta seção registra a **vontade de implementação do PO** para o escopo de fundação descrito em §10.4, sem atribuir ao PO competências de aprovação técnica de terceiros nem declarar pré-condições que não foram comprovadas.

| Decisão | Registro | Efeito |
|---|---|---|
| PO / D-G0-04 — autorização específica IMP-F0 | **PO_AUTHORIZATION_RECORDED_CONDITIONAL**, 19/10/2026. Escopo §10.4: somente fundação FastAPI, Dockerfile, Compose/gateway, `/health`, `/ready`, testes; MFE/Home e rotas de negócio excluídos | **Não efetiva para runtime** até D-G0-01 `VALIDATED`, D-G0-02 quatro freezes `PASS` e D-G0-03 `PASS` estarem formalmente registrados |
| FastAPI | Escolha do PO reiterada, exceção documentada no §1 | `REGISTERED`; assinatura de Arquitetura permanece `PENDING` |
| Sequência de entrega | API → container validado → MFE/Home posterior | Planejamento aprovado, não exceção aos gates |
| Product Contract Freeze | Prioridade e escopo da fundação confirmados pelo PO; contratos globais exigem evidência e registro específico de freeze | `PENDING` no painel; não converter por inferência |
| D-G0-03 documentação | Corpus e inventários preparados | `NO` até assinatura explícita de fechamento **após** aprovações transversais |

**Gate atual: NO-GO.** A manifestação do PO é explícita e reaproveitável; não solicitar novamente a mesma autorização de escopo. O executor deve verificar e registrar aprovações dos owners restantes antes de alterar runtime. Sem autorização de Arquitetura, Design, Segurança e Qualidade comprovada, não criar scaffold, Compose nem gateway.

**Rastreabilidade:** este registro modifica apenas a classificação da **manifestação do PO** de "não expressa" para "registrada, condicional". O indicador de execução do README continua `IMPLEMENTATION_AUTHORIZED=NO` até o gate ter efeito. Não é assinatura dos outros owners.


## 12. Deliberação expressa do PO e encaminhamento dos gates (19/10/2026)

**Manifestação atual:** "faça aqui registrar as aprovações efetivas no documento 45 e atualizar o painel canônico do README, commit e push na main". Em conjunto com §11, constitui ordem de registrar decisões efetivamente sustentadas, **não comprovação de assinatura dos outros owners**.

| Controle | Decisão e evidência registrada | Estado |
|---|---|---|
| Priorização e contrato **restritos ao slice IMP-F0** | **PO APPROVED (escopo)**: fundação FastAPI, Docker/Compose/gateway, endpoints públicos `/health` e `/ready`, testes; sem frontend, persistência e endpoints de negócio. Evidência: manifestações do PO (§§11–12). | `PO_APPROVED / IMP-F0_SCOPE_ONLY` |
| D-G0-04 autorização do PO | **Assentimento do PO confirmado** para o conteúdo de §10.4, sujeito às precondições cumulativas expressas naquele texto. Não pedir nova confirmação de escopo. | `PO_AUTHORIZATION_RECORDED_CONDITIONAL` |
| D-G0-01 / Arquitetura | Exceção FastAPI documentada e recomendada; **sem aceite formal do owner** demonstrado. | `REGISTERED / PENDING` |
| D-G0-02 / Design, Produto, Segurança, Qualidade | Matriz documental §2 pronta. Aprovação do escopo reduzido pelo PO **não equivale** às assinaturas de Design, Security ou Quality, nem ao freeze transversal integral. | `PENDING` |
| D-G0-03 / Fechamento documental | A assinatura de fechamento integral exige prévias aprovações técnicas; não é correto declarar `PASS` antes delas. | `NO` |
| D-G0-05 stale RBAC | Residual antes da primeira rota protegida, conforme §10.2. | `PENDING / NON_BLOCKING_IMP-F0` |
| D-G0-06 `/ready` | Comportamento fundamentado pelo inventário do orquestrador §9; aceite formal de Arq/Ops ainda não localizado. | `TECHNICALLY_SUPPORTED / FORMAL_PENDING` |

**Decisão de segurança documental:** não substituir assinatura identificável de Arquitetura, Design, Segurança ou Qualidade por endosso presumido do PO ou pelo preenchimento automático de uma tabela. O README deve continuar com `IMPLEMENTATION_AUTHORIZED=NO` enquanto os requisitos de §10.4 não forem satisfeitos. **Não implementar runtime sobre esta atualização.**

**Saída objetiva para os responsáveis:** registrar owner identificável, papel, data, decisão e referência de evidência para (1) Arquitetura / D-G0-01, (2) Design, (3) Segurança, (4) Qualidade e (5) escopo transversal de Produto se aplicável; somente então o PO declara D-G0-03 PASS e o painel torna eficaz a autorização IMP-F0 já registrada. Os testes e runtime seguem `TEST_NOT_RUN` / `NOT_IMPLEMENTED`.


## 13. Aprovações efetivas multi-owner e GO exclusivo IMP-F0 — 19/10/2026

**Declaração expressa de autoridade:** em resposta à pergunta "Você tem autoridade formal para aprovar também Arquitetura, Design, Segurança e Qualidade neste projeto, além de atuar como Product Owner?", o responsável pela condução do projeto respondeu **"sim"**. A declaração é registrada como manifestação do **PO/Product Master, também atuando como autoridade formal dos papéis de Arquitetura, Design, Segurança e Qualidade para este gate**. A identidade nominal não foi informada nesta conversa; a atribuição dos papéis é autodeclarada, não verificada por sistema corporativo. Esta seção é o registro de aprovação funcional, sem fabricar assinaturas pessoais ou documentos externos.

**Regra de alcance:** todas as aprovações abaixo são **exclusivas do recorte IMP-F0** (BFF vazia, dois endpoints públicos de infraestrutura, Docker/Compose/gateway e testes); não certificam interfaces, AuthZ de negócio, integrações, persistência ou pages de slices futuros.

| Ordem | Decisão | Owner declarado nesta manifestação | Resultado para IMP-F0 | Evidência técnica |
|---|---|---|---|---|
| 1 | D-G0-01 — exceção FastAPI, sem modificar regra Flask global | Responsável pelo projeto no papel **Arquitetura** | **VALIDATED / IMP-F0_ONLY** | §1, Commercial API FastAPI, `shared/delpi_auth`, regras `.cursor` |
| 2 | D-G0-06 — `/ready` é diagnóstico, Docker observa `/health` | Mesmo responsável no papel **Arquitetura/Ops** | **APPROVED / IMP-F0_ONLY** | §§5, 9, 10 |
| 3 | `PORTAL_DESIGN_FREEZE` | Mesmo responsável no papel **Design** | **PASS / IMP-F0_ONLY** | §2; nenhuma tela ou MFE no slice |
| 4 | `PRODUCT_CONTRACT_FREEZE` | Mesmo responsável no papel **Produto/PO** | **PASS / IMP-F0_ONLY** | README §1, §10.4, §§11–12 |
| 5 | `SECURITY_MODEL_FREEZE` | Mesmo responsável no papel **Segurança** | **PASS / IMP-F0_ONLY** | §4, §8; apenas paths públicos explícitos; não autoriza stale RBAC para rotas protegidas |
| 6 | `TEST_STRATEGY_FREEZE` | Mesmo responsável no papel **Qualidade** | **PASS / IMP-F0_ONLY** | Doc 41, §8, testes de bootstrap, paths públicos, config, Docker/gateway |
| 7 | D-G0-03 — fechamento documental do slice | Mesmo responsável no papel **PO/Product Master** | **PASS / IMP-F0_ONLY** | Aprovações 1–6, docs 41, 45, README |
| 8 | D-G0-04 — efetivar autorização já manifestada em §§10–12 | Mesmo responsável no papel **PO/Product Master** | **YES / IMP-F0_ONLY** | Declaração de autoridade + autorização expressa em §11 |

**Assinatura funcional e proveniência:** manifestação de autoridade do declarante nesta conversa em 19/10/2026; assinatura nominal e auditoria independente de identidade **não disponíveis**. A aprovação registrada pelo PO acumulando os papéis não é apresentada como manifestação de pessoas distintas.

**GO / AUTORIZAÇÃO EFETIVA APENAS PARA IMP-F0:** criar `controllership-finance-api` FastAPI mínima, `GET /health`, `GET /ready`, config e middleware com rotas públicas intencionais, Dockerfile, wiring Compose e gateway, testes unitários/contratuais/smoke e documentação operacional. Aplicar padrão da `commercial-api` e `.cursor`, preservar worktree alheio e evidenciar Docker/gateway. Não criar MFE, páginas, endpoints de negócio, banco, migrações, novas permissions ou integração ERP.

**Residuais mandatórios para slices posteriores:** D-G0-05 política stale RBAC e proteção de service principals **antes** da primeira rota autenticada; revalidar freezes e autorização para cada novo slice; Help e UX somente junto da feature correspondente. `PASS` de aprovação documental não significa `PASS` de teste, deploy ou serviço operacional. Esses estados continuam `TEST_NOT_RUN / NOT_IMPLEMENTED` até evidência do executor.

**Precedência temporal:** esta decisão formal de §13 substitui os estados preparatórios §§1–12 **somente para o recorte IMP-F0**. Não generalizar seu efeito para G0 de todo o Portal.

## 14. Decisões D1/D2/D3 e preparação do gate IMP-MFE-HOME — 2026-10-19

**Manifestação expressa do responsável:** "Aprovo para o Portal Controladoria & Finanças as decisões D1=A, D2=A, D3=A. Registre essas decisões e prepare o gate específico IMP-MFE-HOME para implementação, com verificação dos contratos e testes obrigatórios."

**Alcance:** decisão de produto e segurança para o **slice proposto IMP-MFE-HOME (IMP-02/A02 — MFE, shell e Início)**; não estende automaticamente a autorização IMP-F0 de §13, nem autoriza outros módulos, P1–P6, deploy ou cadastro.

| Decisão | Estado | Contrato aprovado | Restrições e testes exigidos |
|---|---|---|---|
| **D1=A / D-G0-05** | **APPROVED / IMP-MFE-HOME_ONLY / SECURITY POLICY** | Para leituras, reaproveitar **apenas** snapshot de effective permissions previamente validado no Core, respeitando o limite stale de **até 900s** do `delpi_auth`; sem snapshot válido ou erro que impeça verificação, negar (*fail-closed*). Writes futuros exigem consulta atualizada (*force_refresh*) e aprovação própria. Rotas humanas exigem `principal_type == "user"`. | Validar duração efetiva do cache, expiração, revogação/invalidação, 200 com lista vazia, Core 503, token expirado, serviço em lugar de humano, ACCESS sem MANAGE e MANAGE sem ACCESS. **Nunca** derivar capabilities diretamente do JWT. A decisão não autoriza aplicação global de stale a outras APIs. |
| **D2=A** | **APPROVED / IMP-MFE-HOME_ONLY / CONTRACT TARGET** | BFF do produto expõe `GET /viewer-context` (prefixo publicado da BFF `/apps/controllership-finance-api`), com `firstName` e `capabilities: {access, manage}`; somente usuário humano autorizado com effective `controllership-finance.access`. Identidade e autorização vêm dos owners existentes (Core); não criar banco/usuário espelho. | Verificar contrato de identidade existente, envelope e naming REST do projeto, mapeamento/normalização do nome e comportamento 401/403/503. Token service, MANAGE-only, Core indisponível e snapshot ausente não podem autorizar. Sem chamada direta do MFE ao Core ou à api-delpi para contratos do produto. |
| **D3=A / H01** | **APPROVED / DEFERRED** | Favoritos **fora do primeiro slice**, até provar capability compartilhada, owner e contrato. | Não criar persistência BFF-local, não exibir estrela/botão sem ação ou catálogo futuro navegável. Registrar como residual de evolução, não como teste FAIL do escopo reduzido. |

### Gate específico: IMP-MFE-HOME / G1 READY_TO_EXECUTE

**Estado documental:** `DECISIONS_APPROVED / GATE_PREPARATION`. **IMPLEMENTATION_AUTHORIZED = NO para IMP-MFE-HOME** até confirmação explícita de gate e GO específico; a presente manifestação autoriza o registro das escolhas e a **preparação** do gate, não substitui a autorização de execução.

**Escopo candidato mínimo:** `plugins/controllership-finance` (manifest schema 1.0.0, bootstrap federado, shell, rota raiz Início, adapter fino `@delpi/plugin-ui/index`, catálogo apenas de rotas implementadas, navegação e Help contextual), BFF `GET /viewer-context` protegido, Compose dev da BFF/MFE, Compose prod do MFE e testes pertinentes. Não criar páginas futuras, KPIs falsos, favorites, regras P1–P6, endpoint Home agregado, banco ou novas permissões. Seguir `plugins/commercial`, Doc 24/30/32 e padrão visual vigente.

**Condições cumulativas para GO específico (verificar contra HEAD atual, não inferir do inventário):**
1. HEAD, branch e git status, instruções oficiais e `.cursor` aplicáveis; preservação de worktree concorrente.
2. Contratos reais de `delpi_auth` (900s, 60s, revogação e comportamento 503), Core effective-access/identidade, subject humano, `AppHost`, `plugin-ui`, manifest e gateway reconciliados com producers/consumers.
3. DTO e envelope da BFF `/viewer-context` fechados; autorização `access` ≠ `manage`, escopo, falta/expiração de identidade e segurança do principal validados.
4. RQ/AC mínimos do ledger 23 e doc 32 mapeados ao slice; estados vazios/indisponíveis honestos e nenhuma navegação para página não implementada.
5. Matriz positive/sibling/negative: acesso autorizado, MANAGE-only negado, ausência de ACCESS, principal service negado, Core 503/sem snapshot, stale dentro/fora da janela, revogação, rotas futuras ocultas, `?q=`, recentes locais sem dados sensíveis, Help sincronizada, F5, mobile/desktop, tema claro/escuro, teclado/foco, build e testes de contrato.
6. CI, owner, instalação/registro de manifest e smoke definidos; autorização de deploy separada.
7. **GO humano e expresso para IMP-MFE-HOME**, após review das evidências do gate. Uma decisão técnica aprovada não é prova de PASS de execução.

**Classificação atual:** decisões `TARGET / APPROVED`; contratos MFE/BFF `TARGET`; runtime MFE `NOT_IMPLEMENTED`; testes de implementação `TEST_NOT_RUN`. Se contrato real invalidar premissa, `EXECUTION_DRIFT` e STOP. Sem inventar evidência.

### 14.1 GO expresso — IMP-MFE-HOME (2026-10-20)

**Manifestação do responsável pelo projeto:** diante do G1 FINAL VERIFICATION com recomendação `READY_FOR_GO` e da solicitação expressa de autorização `"Autorizo a implementação IMP-MFE-HOME"`, o usuário respondeu **"autorizo"** em 2026-10-20. Esta declaração é autorização funcional **apenas** para o recorte IMP-MFE-HOME já aprovado em §14 (D1=A, D2=A, D3=A). Não atribuir novas identidades ou assinaturas independentes.

**G1:** `READY_FOR_GO / EVIDENCE_REVIEW_ACCEPT_WITH_RESIDUAL` conforme Execution Report no HEAD `6cfb4ea7c3`; implementar requer revalidar HEAD/status e contratos críticos se a main avançar.

**IMPLEMENTATION_AUTHORIZED = YES / IMP-MFE-HOME_ONLY.**

**Dentro do GO:** MFE `plugins/controllership-finance` (manifest schema 1.0.0; shell/Module Federation; somente rota Home implementada; componentes `@delpi/plugin-ui/index`; busca, recentes, ajuda contextual e estados honestos), endpoint humano protegido `GET /viewer-context` na BFF, configuração mínima de Compose dev BFF+MFE e prod MFE, testes unitários/contratuais/structural/build/smoke locais. Capabilities derivadas do Core; D1 restringe stale validado ≤900s para read, service principals negados explicitamente, `access` distinto de `manage`. D3 favoritos deferred.

**Fora do GO:** deploy/restart de produção, manifest registration em Core de produção ou grants reais, novas permissions, banco/migrations, favoritos persistentes, rotas futuras, P1–P6, ERP, mensagens/tarefas/indicadores simulados. Todos exigem gates específicos.

**Condições de execução:** preservar worktree concorrente, conferir producers/consumers no HEAD, não transformar auth ausente em bypass; Help na mesma entrega; G2/G3/G4 com testes positivos/negativos/sibling e evidência de SHA. Qualquer divergência material = `EXECUTION_DRIFT`/STOP. Testes ainda `TEST_NOT_RUN` até execução.

