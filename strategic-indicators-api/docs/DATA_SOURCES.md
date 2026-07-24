# Fontes de dados — medições do painel

**Última atualização:** 2026-06-08

O painel SI **não** armazena valores realizados no Postgres (exceto cache `period_scores`). Os realizados vêm de fontes operacionais por `source_key` / departamento, sempre via **api-delpi HTTP**.

## Ausência vs. zero nas fontes

| Comportamento esperado | Quem implementa |
|------------------------|-----------------|
| Sem registro no período → medição com `value: null` | Coletores / `*MetricsSnapshotService` |
| Registro com 0 na fonte → `value: 0.0` | Coletor (zero é realizado válido) |
| UI e API expõem **Sem dados preenchidos** | `StrategicIndicatorsCalculator` + MFE |

| Departamento | Status (jun/2026) |
|--------------|-------------------|
| Financeiro (Sheets EBITDA / custos fixos) | Alinhado — `null` sem linhas no período |
| RH | Parcial — satisfação/PDI só entram no snapshot se existirem |
| Comercial | Repassa `null` do snapshot quando aplicável |
| Qualidade | PPM / perdas × ROL usam `null` quando a api-delpi não retorna dado (ex.: ROL = 0) |
| Produção | Gateways retornam `null`; provider não força `0.0` |
| Suprimentos / Engenharia | Depende do snapshot upstream (api-delpi) |

## Resumo por departamento

| Departamento | Fontes principais | Acesso | Coletor (si_app) |
|--------------|-------------------|--------|------------------|
| Financeiro | ROL, EBITDA, custo fixo, PMR | `api-delpi` HTTP | `financial_indicators_snapshot_provider` |
| Comercial | ROL por segmento, taxa fechamento, OTD pedidos, % novos negócios | `api-delpi` HTTP | `commercial_indicators_snapshot_provider` |
| Produção | OTD, OEE, MO, custo e depreciação | `api-delpi` HTTP | `production_indicators_snapshot_provider` |
| Qualidade | PPM, perdas (refugo/retrabalho × ROL), NC, Kaizen e 5S | `api-delpi` HTTP | `quality_indicators_snapshot_provider` |
| Suprimentos | CPV, giro de estoque, OTD, estoque, economia em negociações | `api-delpi` HTTP | `supplies_indicators_snapshot_provider` |
| Engenharia | LMP, Transforma+ | `api-delpi` HTTP (`/engineering/*`) | `engineering_indicators_snapshot_provider` |
| RH | Portal RH | `api-delpi` HTTP (`/hr/snapshot`) | `DelpiHrGateway` → `hr_indicators_snapshot_provider` |

Composição: `real_indicator_measurements_provider.py` — paraleliza departamentos na visão consolidada.

## api-delpi (HTTP)

- Client: `shared/delpi_api_client/client.py` (`DelpiApiClient`)
- Variáveis: `DELPI_API_URL`, `DELPI_API_TIMEOUT`, `DELPI_KNOWN_BRANCHES`
- Autenticação: `bearer_authorization_from_context()` propaga o token do request original
- Retry: 3 tentativas em falha de conexão (`ConnectError`)

O SI **não** acessa TOTVS, Sheets, Portal RH nem Transformometro diretamente. Toda leitura operacional passa por gateways `delpi_*_gateway.py`.

## RH

`GET /hr/snapshot` — absenteísmo, turnover, treinamento, PDI, satisfação e avaliações. Postgres Portal RH permanece só na api-delpi.

## Metas e catálogo

Sempre **Postgres** (`strategic_indicators.*`). Alterações em admin invalidam cache in-process (`invalidate_strategic_indicators_snapshot_cache`).

## Referências

- [LEGACY_CLEANUP.md](./LEGACY_CLEANUP.md) — fases de remoção de legado
- [ARCHITECTURE.md](./ARCHITECTURE.md) — gateways e pipeline de snapshot
