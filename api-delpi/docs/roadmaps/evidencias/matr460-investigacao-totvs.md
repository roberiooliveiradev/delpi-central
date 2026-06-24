# Investigação TOTVS — MATR460 vs. fontes SQL

**Gerado em:** 2026-06-24T19:37:30.409056Z

Referência MATR460 (prints maio/2026): EM ESTOQUE + EM PROCESSO + TOTAL GERAL.

## Alinhamento por filial

| Filial | MATR EM ESTOQUE | SB9 28/02 | SB9 31/05 | SB2 atual | SC2 WIP proxy | SB2 vs EM EST. |
|--------|-----------------|-----------|-----------|-----------|---------------|----------------|
| 01 | R$ 3.598.312,40 | R$ 3.474.907,58 | — | R$ 3.565.793,29 | R$ 39.292,83 | 99.1% |
| 02 | R$ 9.737.043,62 | R$ 9.635.115,44 | — | R$ 10.158.352,06 | R$ 117.966,53 | 104.33% |

## Achados

- SB9010 **não possui** fechamento em `20260531` — MATR460 EM ESTOQUE de maio/2026 não está refletido como SB9 nessa data.
- Filial 01: último fechamento SB9 em 2026 é **20260228** (anterior a maio/2026).
- Filial 02: último fechamento SB9 em 2026 é **20260228** (anterior a maio/2026).
- Filial 01: **SB2 atual** (R$ 3.565.793,29) ≈ MATR460 EM ESTOQUE (R$ 3.598.312,40) — saldo corrente é boa referência quando SB9 de maio ausente.
- Filial 01: proxy SC2 WIP (R$ 39.292,83) **subestima** EM PROCESSO (R$ 263.790,57) — MATR460 usa outra fonte além de SC2 simples.
- Filial 02: **SB2 atual** (R$ 10.158.352,06) ≈ MATR460 EM ESTOQUE (R$ 9.737.043,62) — saldo corrente é boa referência quando SB9 de maio ausente.
- Filial 02: proxy SC2 WIP (R$ 117.966,53) **subestima** EM PROCESSO (R$ 311.465,89) — MATR460 usa outra fonte além de SC2 simples.
- Encontradas 2 view(s) customizadas relacionadas a inventário — revisar com DBA/Protheus antes de W3.

## Datas SB9 em 2026

| Filial | Data | Valor | Registros |
|--------|------|-------|-----------|
| 01 | 20260228 | R$ 3.474.907,58 | 4435 |
| 01 | 20260131 | R$ 3.468.259,86 | 4372 |
| 02 | 20260228 | R$ 9.635.115,44 | 3097 |
| 02 | 20260131 | R$ 9.699.692,57 | 2938 |

## Objetos SQL (amostra)

| Tipo | Schema | Nome |
|------|--------|------|
| USER_TABLE | dbo | BKPSB9_01_20210127 |
| USER_TABLE | dbo | ESTOQUEF01_202402 |
| USER_TABLE | dbo | ESTOQUEF02_202402 |
| USER_TABLE | dbo | SB9010 |
| USER_TABLE | dbo | SB9010_201902 |
| USER_TABLE | dbo | SB9010_20201218_FL01 |
| USER_TABLE | dbo | SB9010_20201218_FL01_02 |
| USER_TABLE | dbo | SB9010_20230906 |
| USER_TABLE | dbo | SB9010_BKPGDA_201907 |
| USER_TABLE | dbo | SB9010_BKP_20210115 |
| USER_TABLE | dbo | SB9010_BKP_20220224 |
| USER_TABLE | dbo | SB9010_BKP_GDA20220524 |
| USER_TABLE | dbo | SB9010_TTAT_LOG |
| USER_TABLE | dbo | SB9030 |
| USER_TABLE | dbo | SB9040 |
| USER_TABLE | dbo | SB9040_BKP_202010 |
| USER_TABLE | dbo | SB9050 |
| USER_TABLE | dbo | SB9122013 |
| VIEW | dbo | VW_PBI_ESTOQUE_OBSOLETO_MP_FIL02 |
| VIEW | dbo | VW_PBI_ESTOQUE_OBSOLETO_PA_FIL02 |
