# F3-R — evidências e resíduos (2026-11-12)

## R1 — Segurança de produção

### R1a — CI/CD deploy automático?

**PASS (não automático).** Não há workflow GitHub Actions que faça deploy da `controllership-finance-api` no `push` da `main`. Workflows em `.github/workflows/` com `push:` são CI de qualidade/build de outros pacotes (architecture-enforcement, AI, etc.). Deploy canônico é **manual** via `infra/scripts/up-prod-sequential.sh` (lista inclui `controllership-finance-api` na fase api).

Implantação de `155e0cc4de` em produção: **INCONCLUSIVE** — sem evidência de workflow run / tag de imagem no servidor neste passo; revisor já conferiu em 2026-11-12 que a BFF de prod não expõe rotas LNF (OpenAPI 112 paths).

### R1b — Build imagem PROD

Comando: `docker compose -f infra/docker-compose.yml build controllership-finance-api`  
Resultado: **PASS** (elapsed ≈ 9.11s com cache de layers ODBC).

| Imagem | Tamanho (docker images) | Bytes (`inspect.Size`) |
|---|---|---|
| `pre-odbc` (Dockerfile @ `857b17ce03`) | 377MB | 90 233 072 |
| `latest` (Dockerfile F3 com pyodbc+msodbcsql18) | 781MB | 195 667 646 |
| Delta | +404MB aparente / +105.4 MB compactado | +105 434 574 |

### R1c — Envs PROD/HML sem flag on

**PASS.** `rg LNF_HOSTED_ENABLED|LNF_MIGRATIONS_MODE` só encontra defaults em `infra/docker-compose.dev.yml` e `infra/.env.dev.example` (`false` / `verify`). Compose prod/hml e `.env.prod.example` / `env.hml.example` **não** definem `LNF_HOSTED_ENABLED=true` nem `LNF_MIGRATIONS_MODE=apply`.

Default no código: `controllership_finance_app/config.py:115-116` → `default="false"`.  
`LNF_MIGRATIONS_MODE` default `"verify"` em `config.py:118-120`.

### R1d — Import tardio com flag off

**PASS.** `main.py:247-252` só importa o router quando `LNF_HOSTED_ENABLED`. Processo fresco com flag false:

```
pyodbc_loaded False
totvs_pool False
router_loaded False
lnf_routes []
```

Se o driver ODBC falhasse na imagem, o impacto com flag off é nulo no startup (módulo não importado). Com flag on, falha apareceria na primeira query TOTVS.

## R2 — Notificações

### R2a — Caixa-preta P6→P6B

**INCONCLUSIVE.** Suite ajustada (`test_notifications_cross_user.py`): block/comentário cross-user executam 200, mas o Core rejeita o dispatch:

`no recipients have access to the source application (assign app permission in Minha DELPI RBAC)`

mesmo após conceder `lancamento-notas-fiscais.access` a P6B no provisionamento. Inbox de P6B permanece só com `welcome`.

### R2b — Unitário payload api-delpi × BFF

**PASS.** `test_notification_payload_parity.py` — payloads `send_lnf_portal_notification` e kwargs de `notify_block_assignee` idênticos campo a campo.

## R3 — timed_sql_query

**PASS (explicado + teste).**

- api-delpi: `timed_sql_query(repository: str, query: str) -> _TimedQuery` (`sql_query_telemetry_service.py:81`).
- Port F3 inicial errou com stub keyword-only (`*, repository=...`) → `takes 0 positional arguments but 2 were given` nos call sites `timed_sql_query(self._telemetry_repo(), query)`.
- Correção: stub posicional no-op em `sql_query_telemetry.py` (assinatura alinhada; sem telemetria de domínio — aceitável no BFF dark).
- `test_totvs_sql_call_parity.py`: SQL+params de `TotvsSupplierRepository.search_suppliers` idênticos nas duas implementações.

## R4 — Evidências F3

Ver relatório de execução F3-R (chat) e artefatos em `golden` / `golden-bff` / `results/outcomes.json` após reexecução AuthZ.
