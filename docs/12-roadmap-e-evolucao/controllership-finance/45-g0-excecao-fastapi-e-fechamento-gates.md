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
