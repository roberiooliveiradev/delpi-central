# MyWEG → Production Control — Necessidades (Etapa 1)

> **Status:** contrato + normalização (sem importação produtiva)  
> **Escopo:** filial **02** (ES) apenas · empresa MyWEG **1009** · centro **1106**  
> **Owner do contrato/normalização:** `production-control-api`  
> **Owner TOTVS/SB1:** `api-delpi` (resolução futura; sem SQL paralelo no BFF)  
> **Fora desta etapa:** tabelas históricas, tela nova, POST persistente, resolução SB1 automática, alteração de ETL Linux/Windows/PDFs/tarefas

## 1. Inventário (reancoragem)

| Conceito | Owner real | Evidência |
|----------|------------|-----------|
| UI Portal PCP | `plugins/production-control` | README PC |
| BFF / regra PCP | `production-control-api` | README + schema `production_control` |
| SQL TOTVS / SB1 | `api-delpi` | PC README § Ownership |
| S2S inbound canônico no PC | `/integrations/mes/*` + `X-Delpi-Service-Token` (`API_DELPI_INTERNAL_SERVICE_TOKEN`) | `auth_middleware.py`, `integration_mes_routes.py`, `shared/delpi_auth/service_token.py` |
| Demanda atual do PCP | `GET /demand` (carteira TOTVS via gateway) | **não** é necessidade MyWEG |
| MyWEG no monorepo | inexistente antes desta etapa | grep zero |

**Decisão de reutilização (travada):**

1. Contrato e normalização vivem no bounded context `production-control-api` (domínio puro + doc de contrato).
2. Transporte futuro Linux → PC reutiliza o padrão S2S de `/integrations/mes/*` (shared-secret interno), **não** o S2S JWT de `external-data-api`.
3. Protheus/SB1 continua exclusivamente via `api-delpi` (`DelpiProductionGateway`); E1 só reserva campos de resolução `pending`.
4. Não misturar com `GET /demand` (carteira TOTVS) nem com Factory Supply.

## 2. Origem homologada (Linux — somente leitura nesta etapa)

Artefatos já produzidos pelo ETL homologado (não alterar em produção nesta etapa):

| Arquivo | Papel |
|---------|--------|
| `necessidades_tratadas.csv` | fonte tabular canônica das linhas |
| `necessidades_tratadas.xlsx` | espelho humano |
| `para_conferencia_pcp.csv` | conferência PCP |
| `resumo.json` | totais / metadados da coleta |

O contrato HTTP abaixo **preserva** os campos semânticos desses arquivos; a API não substitui o ETL.

## 3. Contrato canônico do lote — `myweg.needs.batch.v1`

### 3.1 Envelope

| Campo | Tipo | Obrigatório | Notas |
|-------|------|-------------|-------|
| `contract_version` | string | sim | literal `myweg.needs.batch.v1` |
| `collection_id` | string | sim | id estável da coleta no Linux (idempotência natural) |
| `branch` | string | sim | **somente** `"02"` |
| `myweg_company_code` | string | sim | `"1009"` |
| `myweg_work_center` | string | sim | `"1106"` |
| `collected_at` | datetime ISO-8601 c/ timezone | sim | instante da coleta na origem |
| `exported_at` | datetime ISO-8601 c/ timezone | sim | instante da montagem do lote |
| `source_files` | object | sim | nomes/hashes dos artefatos de origem |
| `payload_sha256` | string hex 64 | sim | SHA-256 do canônico das `records` (ver §5) |
| `record_count` | int | sim | deve igualar `len(records)` |
| `totals` | object | sim | `quantidade_original_un`, `quantidade_mi` (strings decimais) |
| `records` | array | sim | linhas normalizadas |

`source_files` (mínimo):

```json
{
  "necessidades_tratadas_csv_sha256": "...",
  "necessidades_tratadas_xlsx_sha256": "...",
  "para_conferencia_pcp_csv_sha256": "...",
  "resumo_json_sha256": "..."
}
```

### 3.2 Registro (`records[]`)

Campos preservados da origem (nomes estáveis do ETL):

| Campo | Obrigatório | Semântica |
|-------|-------------|-----------|
| `material_weg_tratado` | sim | material WEG já tratado |
| `codigo_referencia_weg` | sim | referência WEG |
| `origem_material_weg` | sim | origem do material na WEG |
| `quantidade_original_un` | sim | quantidade em UN (Decimal exato, string no JSON) |
| `unidade` | sim | unidade de origem; esperado `"UN"` no corpus homologado |
| `data_remessa` | sim | data de remessa (`YYYY-MM-DD`) |
| `documento` | não | documento opcional |
| `rastreabilidade` | sim | trilha de origem da linha |

Campos derivados / contrato PC:

| Campo | Obrigatório | Semântica |
|-------|-------------|-----------|
| `quantidade_mi` | sim | `quantidade_original_un / 1000` com `Decimal` (ROUND_HALF_UP em 6 casas na apresentação; aritmética exata na soma) |
| `line_fingerprint` | sim | fingerprint estável para deduplicação |
| `sb1_resolution` | sim | reserva para resolução futura via api-delpi |

`sb1_resolution` (E1 — sempre pending):

```json
{
  "status": "pending",
  "protheus_product_code": null,
  "matched_by": null,
  "resolved_at": null
}
```

Nenhuma resolução SB1 é executada nesta etapa.

## 4. Conversão UN → MI

```text
quantidade_mi = quantidade_original_un / 1000
```

- Aritmética com `decimal.Decimal` (nunca `float`).
- Referência homologada: **532** registros · **745746 UN** · **745.746 MI**.
- Compatibilidade: CSV/XLSX existentes continuam em UN; o lote versionado carrega ambos os campos.

## 5. Validação, deduplicação, erros e idempotência

| Regra | Comportamento |
|-------|----------------|
| Filial | `branch != "02"` → rejeição (`branch_not_allowed`) |
| Proteção filial 01 | qualquer sinal de filial `"01"` no envelope ou linhas → rejeição (`filial_01_forbidden`) |
| Empresa / centro | ≠ `1009` / `1106` → rejeição |
| Lote completo | `record_count == len(records)`; totais batem com soma das linhas |
| SHA-256 | `payload_sha256` deve bater com hash canônico das records |
| Deduplicação | `line_fingerprint` duplicado no mesmo lote → erro `duplicate_line` |
| Linha inválida | material/ref/origem/data/unidade/qty ausentes ou qty ≤ 0 → `invalid_record` |
| Idempotência (futuro POST) | chave = `collection_id` + `payload_sha256`; header `Idempotency-Key` espelha essa chave |

Códigos de erro estáveis (domínio): `branch_not_allowed`, `filial_01_forbidden`, `company_mismatch`, `work_center_mismatch`, `record_count_mismatch`, `totals_mismatch`, `payload_sha256_mismatch`, `duplicate_line`, `invalid_record`, `contract_version_unsupported`.

## 6. Transporte proposto (não implementado em E1)

```text
Linux connector (homologado)
  → HTTPS interno / rede Delpi
  → POST /apps/production-control-api/integrations/myweg/need-batches
     Headers:
       X-Delpi-Service-Token: <API_DELPI_INTERNAL_SERVICE_TOKEN>
       X-Delpi-Caller-App: myweg-linux-connector
       Idempotency-Key: <collection_id>:<payload_sha256>
     Body: myweg.needs.batch.v1
```

Alinhamento ao padrão existente:

- estender `_is_internal_integration` para `/integrations/myweg/` (espelho de MES);
- handler com `request_has_valid_internal_service_token`;
- envelope de resposta PC `{ success, message, data }`;
- **persistência e aceite produtivo ficam para etapa posterior**.

## 7. Atividades manuais no Linux (responsável da origem)

Não executadas por este repositório:

1. Confirmar path estável dos quatro artefatos após cada coleta.
2. Publicar/gerar `collection_id` estável por corrida.
3. Calcular SHA-256 dos quatro arquivos e do payload canônico de records.
4. Homologar conector HTTP S2S **somente** após etapa de importação (pós-E1), sem mudar ETL Windows/PDFs/tarefas.
5. Entregar amostra anonimizada dos CSVs reais se o corpus sintético de teste precisar ser substituído por fixture fiel linha a linha.

## 8. Evidência de código (E1)

| Artefato | Papel |
|----------|--------|
| `production_control_app/domain/myweg_needs_contract.py` | constantes + fingerprints + hash |
| `production_control_app/domain/services/myweg_needs_normalization.py` | normalização Decimal + validação de lote |
| `tests/fixtures/myweg/resumo_referencia.json` | totais 532 / 745746 / 745.746 |
| `tests/test_myweg_needs_normalization.py` | positive + sibling + negative |

## 9. Condições de parada / o que E1 **não** entrega

- Não há endpoint HTTP montado nem migração Postgres.
- Não há tela no MFE.
- Não há escrita no Protheus nem lookup SB1.
- Não há alteração do ETL Linux/Windows.
- Importação produtiva só após etapa dedicada com persistência e gates de deploy.
