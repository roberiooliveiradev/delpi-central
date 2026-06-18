# Especificação — Views TOTVS Inspeções de Entrada

> Fonte operacional do plugin **inspecoes-entrada**.  
> Validação Fase 0: [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md).

---

## Objetivo

Expor no SQL Server dados consolidados de **inspeção de recebimento** (módulo qualidade Protheus), permitindo:

- KPIs por filial;
- Pendências FIFO;
- Agregações por fornecedor e ensaiador;
- Histórico laudado com filtros;
- Detalhe de ensaios via tabelas transacionais (`QER010`).

**Granularidade:**

| View | 1 linha = |
|------|-----------|
| `resumo_filial` | 1 filial |
| `pendentes` | 1 item aguardando laudo |
| `pendentes_fornecedor` | 1 fornecedor com contagem |
| `rejeitadas_ensaiador` | 1 ensaiador com contagem |
| `historico_tela` | 1 inspeção laudada |

**Filiais:** `01` (SC), `02` (ES). Coluna discriminadora: `Filial`.

---

## Inventário de views

| View SQL | Uso API |
|----------|---------|
| `dbo.vw_minha_delpi_inspecoes_entrada_resumo_filial` | `GET /resumo` |
| `dbo.vw_minha_delpi_inspecoes_entrada_pendentes` | `GET /pendentes` |
| `dbo.vw_minha_delpi_inspecoes_entrada_pendentes_fornecedor` | `GET /pendentes-fornecedor` |
| `dbo.vw_minha_delpi_inspecoes_entrada_rejeitadas_ensaiador` | `GET /rejeitadas-ensaiador` |
| `dbo.vw_minha_delpi_inspecoes_entrada_historico_tela` | `GET /historico`, `/rejeitadas-produto`, cabeçalho detalhe |

Script de validação: `api-delpi/scripts/validate_inspecoes_entrada_views.py`.

---

## Colunas por view (contrato repository)

### `resumo_filial`

| Coluna view | Campo API |
|-------------|-----------|
| `Filial` | `branch` |
| `Inspecoes_Pendentes` | `pending_inspections` |
| `Ja_Inspecionados` | `inspected` |
| `Inspecoes_Aprovadas` | `approved_inspections` |
| `Inspecoes_Rejeitadas` | `rejected_inspections` |
| `Taxa_Aprovacao` | `approval_rate` |
| `Qtde_Inspecoes_Com_Tempo` | `inspections_with_time` |
| `Tempo_Medio_Horas` | `average_time_hours` |
| `Tempo_Medio_Dias` | `average_time_days` |

### `pendentes`

| Coluna view | Campo API |
|-------------|-----------|
| `Data_Recebimento`, `Hora_Recebimento` | `received_date`, `received_time` |
| `Nota_Fiscal` | `invoice_number` |
| `Codigo_Fornecedor`, `Loja_Fornecedor` | `supplier_code`, `supplier_store` |
| `Nome_Fornecedor` | `supplier_name` |
| `Codigo_Produto` | `product_code` |
| `Quantidade`, `Unidade_Medida` | `quantity`, `unit` |
| `Codigo_Situacao`, `Status_Inspecao` | `status_code`, `inspection_status` |

Enriquecimento API: `Descricao_Produto` → `product_description` (join `SB1010`).

### `pendentes_fornecedor`

| Coluna view | Campo API |
|-------------|-----------|
| `Nome_Fornecedor` | `supplier_name` |
| `Qtde_Pendentes` | `pending_count` |

### `rejeitadas_ensaiador`

| Coluna view | Campo API |
|-------------|-----------|
| `Matricula_Ensaiador` | `inspector_registration` |
| `Nome_Ensaiador` | `inspector_name` |
| `Login_Ensaiador` | `inspector_login` |
| `Qtde_Inspecoes_Rejeitadas` | `rejected_count` |

### `historico_tela`

| Coluna view | Campo API (item) |
|-------------|------------------|
| `Id_Inspecao` | `inspection_id` |
| `Data_Laudo`, `Hora_Laudo` | `report_date`, `report_time` |
| `Serie_Nota_Fiscal`, `Item_Nota_Fiscal` | `invoice_series`, `invoice_item` |
| `Lote`, `Lote_Fornecedor` | `lot`, `supplier_lot` |
| `Resultado_Resumo` | `result` (`APROVADA` \| `REJEITADA`) |
| `Codigo_Laudo` | `report_code` |
| `Quantidade_Aprovada`, `Quantidade_Rejeitada` | `approved_quantity`, `rejected_quantity` |
| `Justificativa_Laudo` | `report_justification` |
| `Qtde_Ensaios`, `Qtde_Ensaios_Reprovados` | `tests_count`, `failed_tests_count` |
| `Eh_Aprovada`, `Eh_Rejeitada` | `is_approved`, `is_rejected` |

Filtros SQL suportados: ver `_build_historico_where` no repository.

---

## Detalhe de ensaios (fora das views)

Carregado de `dbo.QER010` com joins:

| Tabela | Finalidade |
|--------|------------|
| `QER010` | Resultados de ensaio por inspeção |
| `QE1010` | Descrição do ensaio |
| `QE7010` | Limites e nominal |
| `QE8010` | Especificação textual |
| `QEQ010` | Medição textual |
| `QES010` | Medição numérica |
| `QAA010` | Dados do ensaiador |

**Chave de correlação:** filial + fornecedor + loja + produto + lote + NF + série + item (campos do cabeçalho histórico).

**Prioridade de medição:**

```text
1. QES.QES_MEDICA (numérica) → measurement_source = 'QES'
2. QEQ.QEQ_MEDICA (textual)   → measurement_source = 'QEQ'
3. Sem valor inventado        → measured_value = null
```

---

## Literais validados

### `Resultado_Resumo` (histórico)

| Valor | Uso |
|-------|-----|
| `APROVADA` | Filtro e badge verde |
| `REJEITADA` | Filtro, lista rejeitadas, badge vermelho |

API rejeita outros valores no query param `result` (`422`).

---

## Responsabilidades DBA vs aplicação

| Responsabilidade | Onde |
|------------------|------|
| Definição e performance das views | DBA / Protheus |
| Regras de negócio de laudo | View SQL |
| Paginação, filtros dinâmicos, joins SB1/QER | api-delpi repository |
| Apresentação e certificado | MFE |

---

## Referências

- Repository: `api-delpi/app/infrastructure/persistence/totvs/inspecoes_entrada/inspecoes_entrada_repository.py`
- Validação: `api-delpi/scripts/validate_inspecoes_entrada_views.py`
