# Fontes de dados — medições do painel

**Última atualização:** 2026-05-25

O painel SI **não** armazena valores realizados no Postgres (exceto cache `period_scores`). Os realizados vêm de fontes operacionais por `source_key` / departamento.

## Ausência vs. zero nas fontes

| Comportamento esperado | Quem implementa |
|------------------------|-----------------|
| Sem registro no período → medição com `value: null` | Coletor / `FinancialMetricsSnapshotService` |
| Registro com 0 na fonte → `value: 0.0` | Coletor (zero é realizado válido) |
| UI e API expõem **Sem dados preenchidos** | `StrategicIndicatorsCalculator` + MFE |

| Departamento | Status (2026-05) |
|--------------|------------------|
| Financeiro (Sheets EBITDA / custos fixos) | Alinhado — `null` sem linhas no período |
| RH | Parcial — satisfação/PDI só entram no snapshot se existirem; demais métricas usam `null` na resolução |
| Comercial | Repassa `null` do snapshot quando aplicável |
| Qualidade | PPM ainda pode usar `default_value=0.0` quando falta dado |
| Produção | `_build_measurement` ainda converte ausência em `0.0` |
| Suprimentos / Engenharia | Depende do snapshot upstream |

## Resumo por departamento

| Departamento | Fontes principais | Acesso | Coletor (si_app) |
|--------------|-------------------|--------|------------------|
| Financeiro | ROL, EBITDA, custo fixo, PMR | `api-delpi` HTTP | `financial_indicators_snapshot_provider` |
| Comercial | ROL por segmento, taxa fechamento, OTD pedidos, % novos negócios | `api-delpi` HTTP | `commercial_indicators_snapshot_provider` |
| Produção | OTD, OEE, MO, custo e depreciação | `api-delpi` HTTP | `production_indicators_snapshot_provider` |
| Qualidade | PPM, NC, Kaizen e 5S | `api-delpi` HTTP | `quality_indicators_snapshot_provider` |
| Suprimentos | CPV, giro de estoque, OTD, estoque, economia em negociações | `api-delpi` HTTP | `supplies_indicators_snapshot_provider` |
| Engenharia | LMP (TOTVS), Transforma+ (Sheets) | `api-delpi` HTTP + Sheets | `engineering_indicators_snapshot_provider` |
| RH | Portal RH (Postgres) | via api-delpi HTTP | `DelpiHrGateway` → `hr_indicators_snapshot_provider` |

Composição: `real_indicator_measurements_provider.py` — paraleliza departamentos na visão consolidada.

## Migração para HTTP (api-delpi)

A partir de maio/2026, o SI **não acessa mais o TOTVS/SQL Server diretamente**. Todas as medições operacionais TOTVS são obtidas via HTTP da api-delpi, usando o client compartilhado `shared/delpi_api_client`.

Os repositórios TOTVS originais foram **removidos** (fase 1 em [LEGACY_CLEANUP.md](./LEGACY_CLEANUP.md)). Medições operacionais passam por gateways HTTP (`si_app/infrastructure/gateways/delpi_*_gateway.py`). Os ports de domínio não mudaram — a troca é transparente para use cases e services.

**Fase 2 (concluída jun/2026):** todas as planilhas do SI passam pela api-delpi (`DelpiFinancialSheetsGateway`, `DelpiProductionSheetsGateway`, gateways de qualidade e suprimentos).

## api-delpi (HTTP)

- Client compartilhado: `shared/delpi_api_client/client.py` (`DelpiApiClient`)
- Variáveis: `DELPI_API_URL`, `DELPI_API_TIMEOUT`, `DELPI_KNOWN_BRANCHES`
- Autenticação: `bearer_authorization_from_context()` propaga o token do request original

## Google Sheets

Variáveis em `si_app/config.py` (prefixos `QUALITY_*`, `TRANSFORMA_MAIS_*`, `FINANCIAL_*`, `PRODUCTION_*`, etc.).

Transforma+: cache TTL de `load_raw_data` no coletor de engenharia.

## RH (api-delpi)

`GET /hr/snapshot` — absenteísmo, turnover, treinamento, PDI, satisfação e avaliações. Leitura Portal RH permanece na api-delpi (`PORTAL_RH_DB_*` só no serviço `api-delpi`).

## Dados diretos na api-delpi

Consultas pontuais (ex.: **ROL** bruto) permanecem em:

```text
GET /apps/api-delpi/finacial/financial/rol
```

Essas rotas **não** substituem o painel SI; servem integrações e outros módulos.

## Metas e catálogo

Sempre **Postgres** (`strategic_indicators.*`). Alterações em admin invalidam cache in-process (`invalidate_strategic_indicators_snapshot_cache`).
