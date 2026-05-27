# Fase 0 — Validação TOTVS (Eficiência Fabril)

> Gerado em: `2026-05-27T20:52:18`
> View: `dbo.vw_Apontamentos_Eficiencia`
> Status: **✅ Pronto para Fase 1**

Checks: 10/10 OK | Amostra com dados: sim

## Resultados por check

### Amostra TOP 100

Linhas: **100**

| FILIAL | OP | DATA_PRODUCAO | CENTRO_TRABALHO | NOME_OPERADOR | TEMPO_REAL_HORAS | TEMPO_PREVISTO_HORAS | EFICIENCIA_PERCENTUAL | RESULTADO_MOD | STATUS_REGISTRO |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 02 | 10312301005 | 2026-05-27 | CT-01B | DANIELI FERREIRA DOS SANTOS | 2.0833333333333335 | 1.07 | 51.36 | -76.1 | OK |
| 02 | 10312401005 | 2026-05-27 | CT-01A | SAULO DOS REIS CRISTO | 1.4333333333333333 | 1.169 | 81.56 | -19.85 | OK |
| 02 | 10466501008 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.03333333333333333 | 0.09 | 270.0 | 3.95 | OK |
| 02 | 10466501007 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.05 | 0.09 | 180.0 | 2.79 | OK |
| 02 | 10466501003 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.03333333333333333 | 0.09 | 270.0 | 3.95 | OK |
| 02 | 10452401004 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.18333333333333332 | 0.18 | 98.18 | -0.23 | OK |
| 02 |  | 2026-05-27 | CT-11A | ELIANA DE JESUS ANDRADE | 0.9833333333333333 |  |  |  | OP NAO ENCONTRADA |
| 02 | 10452401003 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 1.15 | 0.18 | 15.65 | -67.65 | OK |
| 02 | 10452401002 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.2 | 0.12000000000000001 | 60.0 | -5.58 | OK |
| 02 | 10452401007 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.25 | 0.12000000000000001 | 48.0 | -9.07 | OK |
| 02 | 10401201003 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.1 | 0.06 | 60.0 | -2.79 | OK |
| 02 | 10138101005 | 2026-05-27 | CT-01C | RANIA B. MILDEMBERG | 1.6833333333333333 | 1.66 | 98.61 | -1.75 | OK |
| 02 | 10401201002 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.18333333333333332 | 0.06 | 32.73 | -8.6 | OK |
| 02 | 10418101001 | 2026-05-27 | CT-99 | IVONE SILVA DA ROCHA | 0.016666666666666666 | 0.01 | 60.0 | 0.0 | OK |
| 02 | 10457801001 | 2026-05-27 | CT-02B | ALEXANDRA DA ROCHA SANTOS | 0.2 | 0.14 | 70.0 | -4.18 | OK |
| 02 | 10299201001 | 2026-05-27 | CT-99 | BRENDA MAURICIO PONTINI | 0.05 | 0.02 | 40.0 | 0.0 | OK |
| 02 | 10274101001 | 2026-05-27 | CT-99 | BRENDA MAURICIO PONTINI | 0.16666666666666666 | 0.02 | 12.0 | 0.0 | OK |
| 02 | 10411301001 | 2026-05-27 | CT-99 | BRENDA MAURICIO PONTINI | 0.16666666666666666 | 0.08 | 48.0 | 0.0 | OK |
| 02 | 10441401001 | 2026-05-27 | CT-11A | ELIANA DE JESUS ANDRADE | 2.1333333333333333 | 0.73 | 34.22 | -140.45 | OK |
| 02 | 10452501001 | 2026-05-27 | CT-99 | BRENDA MAURICIO PONTINI | 0.16666666666666666 | 0.02375 | 14.25 | 0.0 | OK |

_… mais 80 linha(s)._

### Literais STATUS_REGISTRO

Linhas: **7**

| STATUS_REGISTRO | total |
| --- | --- |
| OPERADOR SEM VINCULO | 213905 |
| OK | 139889 |
| OP NAO ENCONTRADA | 7897 |
| TEMPO PREVISTO INVALIDO | 6869 |
| PRODUTO MOD NAO ENCONTRADO NA SBZ | 3491 |
| TEMPO REAL ZERADO | 812 |
| TEMPO REAL INVALIDO | 308 |

### Literais STATUS_MOD

Linhas: **3**

| STATUS_MOD | total |
| --- | --- |
| OK | 368963 |
| PRODUTO MOD NAO ENCONTRADO NA SBZ | 4206 |
| RECURSO NAO ENCONTRADO NA SH1 | 2 |

### Literais STATUS_RESULTADO_MOD

Linhas: **7**

| STATUS_RESULTADO_MOD | total |
| --- | --- |
| PREJUIZO | 176827 |
| LUCRO | 160142 |
| NEUTRO | 16752 |
| TEMPO PREVISTO INVALIDO | 14230 |
| SEM VALOR MOD | 4208 |
| TEMPO REAL ZERADO | 809 |
| TEMPO REAL INVALIDO | 203 |

### Filiais

Linhas: **3**

| FILIAL | total | data_min | data_max |
| --- | --- | --- | --- |
|  | 2 | 1900-01-01 | 1900-01-01 |
| 01 | 158309 | 2006-12-14 | 2026-05-27 |
| 02 | 214860 | 2022-05-20 | 2026-05-27 |

### Volume — últimos 30 dias

Linhas: **31**

| DATA_PRODUCAO | linhas_dia |
| --- | --- |
| 2026-05-27 | 314 |
| 2026-05-26 | 366 |
| 2026-05-25 | 285 |
| 2026-05-24 | 12 |
| 2026-05-23 | 40 |
| 2026-05-22 | 275 |
| 2026-05-21 | 417 |
| 2026-05-20 | 451 |
| 2026-05-19 | 429 |
| 2026-05-18 | 415 |
| 2026-05-17 | 17 |
| 2026-05-16 | 36 |
| 2026-05-15 | 423 |
| 2026-05-14 | 415 |
| 2026-05-13 | 426 |
| 2026-05-12 | 539 |
| 2026-05-11 | 417 |
| 2026-05-10 | 5 |
| 2026-05-09 | 61 |
| 2026-05-08 | 256 |

_… mais 11 linha(s)._

### Volume — últimos 12 meses

Linhas: **13**

| ano | mes | linhas_mes |
| --- | --- | --- |
| 2026 | 5 | 6953 |
| 2026 | 4 | 6822 |
| 2026 | 3 | 9039 |
| 2026 | 2 | 7855 |
| 2026 | 1 | 7656 |
| 2025 | 12 | 7388 |
| 2025 | 11 | 9470 |
| 2025 | 10 | 10314 |
| 2025 | 9 | 9506 |
| 2025 | 8 | 9794 |
| 2025 | 7 | 10048 |
| 2025 | 6 | 8206 |
| 2025 | 5 | 1702 |

### KPI referência (7 dias, STATUS_REGISTRO = OK)

Linhas: **1**

| appointment_count | invalid_record_count | weighted_efficiency_pct | total_mod_result |
| --- | --- | --- | --- |
| 1701 | 0 | 73.77 | -27458.38 |

### Sanidade — CT-00 ausente

Linhas: **1**

| ct00_count |
| --- |
| 0 |

### Sanidade — tempo real zero

Linhas: **3**

| STATUS_REGISTRO | total |
| --- | --- |
| TEMPO REAL ZERADO | 812 |
| TEMPO REAL INVALIDO | 308 |
| OP NAO ENCONTRADA | 2 |

## Como regenerar

```bash
docker exec delpi-api-delpi python scripts/validate_eficiencia_fabril_view.py \
  --markdown docs/12-roadmap-e-evolucao/eficiencia-fabril/FASE0-VALIDACAO.md
```
