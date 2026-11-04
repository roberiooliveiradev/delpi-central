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

Campos preservados da origem (nomes estáveis do ETL / planilha real):

| Campo | Obrigatório | Semântica |
|-------|-------------|-----------|
| `material_weg_tratado` | sim | material WEG já tratado |
| `codigo_referencia_weg` | **não** | referência WEG; **vazio/nulo é válido** — não descartar a necessidade nem inventar código; permanece `null` no lote com `sb1_resolution.status=pending` |
| `origem_material_weg` | sim | origem do material na WEG |
| `quantidade_original_un` | sim | quantidade em UN (Decimal exato, string no JSON); origem real usa frequentemente `quantidade` |
| `unidade` | sim | unidade de origem; esperado `"UN"` no corpus homologado |
| `data_remessa` | sim | data de remessa (`YYYY-MM-DD`; origem pode vir `DD/MM/YYYY`) |
| `documento` | não | documento opcional |
| `linha_fonte` | não* | linha da planilha de origem; usada para montar/preservar rastreabilidade |
| `assinatura_registro` | não* | assinatura da linha na coleta; entra na rastreabilidade, **não** é identidade entre coletas |
| `rastreabilidade` | sim | trilha estável da linha (explícita ou derivada de `linha_fonte` + `assinatura_registro`) |

\*Na planilha real homologada, `linha_fonte` e `assinatura_registro` estão presentes e alimentam `rastreabilidade` quando esta não vem preenchida.

Campos derivados / contrato PC:

| Campo | Obrigatório | Semântica |
|-------|-------------|-----------|
| `quantidade_mi` | sim | `quantidade_original_un / 1000` com `Decimal` (ROUND_HALF_UP em 6 casas na apresentação; aritmética exata na soma) |
| `line_fingerprint` | sim | fingerprint de deduplicação **dentro do lote** (inclui `linha_fonte`; não usar `assinatura_registro` como id entre coletas) |
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
- Amostra homologada (fixture): **532** registros · **745746 UN** · **745.746 MI** · refs `9*`=528 · `8*`=2 · vazias=2.
- Esses totais/distribuição **não** são restrições permanentes de coletas futuras.
- Compatibilidade: CSV/XLSX existentes continuam em UN (`quantidade`); o lote versionado carrega `quantidade_original_un` + `quantidade_mi`.

## 5. Duas fases: origem × lote pronto para ingestão

| Fase | API de domínio | Exige |
|------|----------------|-------|
| Normalização de origem | `normalize_source_records` | linhas da planilha/CSV (`quantidade`, `data_remessa`, `linha_fonte`, `assinatura_registro`, ref opcional) |
| Validação de ingestão | `validate_ingest_batch` | envelope completo `myweg.needs.batch.v1` + hashes obrigatórios |

`normalize_and_validate_batch` permanece como atalho da fase de ingestão (compatibilidade).

### 5.1 Regras de validação do lote pronto

| Regra | Comportamento |
|-------|----------------|
| Campos obrigatórios do envelope | `contract_version`, `collection_id`, `branch`, `myweg_company_code`, `myweg_work_center`, `collected_at`, `exported_at`, `source_files` (4 SHA-256), `payload_sha256`, `record_count`, `totals` → ausência = `missing_required_field` |
| Filial | `branch != "02"` → `branch_not_allowed` |
| Proteção filial 01 | sinal de `"01"` no envelope ou linhas → `filial_01_forbidden` |
| Empresa / centro | ≠ `1009` / `1106` → rejeição |
| Lote completo | `record_count == len(records)`; totais batem com soma das linhas |
| SHA-256 | `payload_sha256` **obrigatório** e deve bater com o canônico das records |
| Deduplicação | `line_fingerprint` duplicado no mesmo lote → `duplicate_line` |
| Linha inválida / malformada | material/origem/data/unidade/qty/rastreabilidade inválidos → `invalid_record` (**sem** exceção inesperada) |
| Referência vazia | **válida**; `codigo_referencia_weg=null` + SB1 `pending` |
| Idempotência (futuro POST) | chave = `collection_id` + `payload_sha256` (não `assinatura_registro`) |

Códigos de erro estáveis (domínio): `branch_not_allowed`, `filial_01_forbidden`, `company_mismatch`, `work_center_mismatch`, `record_count_mismatch`, `totals_mismatch`, `payload_sha256_mismatch`, `duplicate_line`, `invalid_record`, `contract_version_unsupported`, `missing_required_field`, `invalid_source_files`.

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
| `production_control_app/domain/services/myweg_needs_normalization.py` | `normalize_source_records` + `validate_ingest_batch` |
| `tests/fixtures/myweg/planilha_real_sanitizada.json` | 532 linhas no formato real (refs 9/8/vazias) |
| `tests/fixtures/myweg/resumo_referencia.json` | metadados da **amostra** (não regra permanente) |
| `tests/test_myweg_needs_normalization.py` | positive + sibling + negative + empty-ref |

## 9. Condições de parada / o que E1 **não** entrega

- Não há endpoint HTTP montado nem migração Postgres.
- Não há tela no MFE.
- Não há escrita no Protheus nem lookup SB1.
- Não há alteração do ETL Linux/Windows.
- Importação produtiva só após etapa dedicada com persistência e gates de deploy.
