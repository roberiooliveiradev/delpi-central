# Playbook — Despesas de Viagem (P0)

> **Status:** implementação P0 (cadastro + cupons + pacote)  
> **Data:** 2026-08-22

## Decisões

| Tema | Escolha |
|------|---------|
| Bounded context | Plugin `travel-expenses` + API `travel-expenses-api` |
| Clone | CIPA (FastAPI + MFE federado + kit) |
| Status operacional | Só `draft`. Enum já prevê envio/aprovação |
| Completeness | Serviço de domínio; não bloqueia salvar rascunho |
| Moeda | BRL |
| Numeração | `TE-YYYY-NNNN` por unidade/ano |
| Upload | JPEG/PNG/WebP/PDF em volume persistente |
| Pacote | `DocumentReader` no MFE + PDF ReportLab na API |
| Menu | Grupo Financeiro, ícone `plane`, order 44 |

## Aceite P0

Colaborador com `view`+`write`+unidade cria prestação, lança despesas, anexa foto/PDF, vê preview e baixa o PDF. `manage` vê a unidade. Recreate do container não apaga cupons.

## Fora do P0

Envio ao financeiro, aprovação, OCR, TOTVS, adiantamento, multi-moeda, tetos, cartão corporativo, clone, Excel.
