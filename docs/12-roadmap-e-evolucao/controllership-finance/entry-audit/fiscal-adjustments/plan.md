# Plano — Ajustes do Fiscal na auditoria de entradas

| Campo | Valor |
|---|---|
| Origem | plano anexo à T14 (arquiteto), transcrito **sem dado real** |
| Leitura de código do plano | HEAD `a6a7dedc88` — revalidada pela T14 em `784d7047a6` (nenhum diff no código da auditoria entre os dois) |
| Status | INVENTÁRIO FEITO — decisões DR-1..DR-7 pendentes do texto integral do anexo |

> **Nota de fidelidade:** este arquivo espelha a estrutura do plano anexo conforme
> descrita no prompt T14 (contexto, autoridade, seção 1 de premissas e existência
> das decisões DR-1 a DR-7). O texto integral do anexo — incluindo o corpo das
> decisões DR-1..DR-7 e as etapas de implementação — está no chat do arquiteto e
> deve ser colado aqui pelo owner quando disponível. Até lá, as DR ficam
> `TO_INVENTORY`; o inventário da T14 já confirma todas as premissas da seção 1.

## Contexto

O Fiscal pediu cinco ajustes na auditoria de entradas a partir da análise de
01–17/11/2026 (documento fora do repositório):

1. participante pelo cadastro de clientes (SA1) em notas `F1_TIPO` B/D;
2. IBS/CBS em todas as entradas;
3. TES de insumo fora de «Crédito de IPI em uso e consumo»;
4. uma ocorrência por causa;
5. reverificação automática e indicadores ao vivo.

## Autoridade

```text
instruções oficiais do arquiteto e .cursor aplicáveis
→ ADR-003
→ entry-audit/track.md (Parte 0, P1–P9, X1–X8)
→ este plano
```

## Seção 1 — Premissas (estado do código)

Verificadas na T14 — todas **PROVEN** (arquivo:linha em [inventory.md](./inventory.md)):

- a api-delpi devolve `invoice_type` (`F1_TIPO`) em `documents` e
  `documents_by_access_keys`; a BFF não usa;
- `key.supplier_mismatch` e `coherence.cfop_vs_state` usam SA2; a heurística
  «seen» de `_supplier_keys` agrupa por código/loja sem o tipo do participante;
- `coherence.ipi_on_consumption` por `F4_CONSUMO`/CFOP; existem regras de IPI
  acima do XML e de IPI sem destaque;
- `stable_occurrence_key` leva `item` e `field`;
  `header.icms_base_mismatch` «Acompanha…» é ocorrência própria;
  `summary.clean`/`divergent` não olha o status; não há fila entre análises;
- `xml_reader` sem grupo `IBSCBS`; `TesRecord` sem IBS/CBS; worker sem job
  periódico.

## Decisões do plano (DR-1 a DR-7)

`TO_INVENTORY` — pendentes do texto integral do anexo. O que a T14 já
estabelece para cada ajuste está no relatório da etapa e em
[inventory.md](./inventory.md) §5 (riscos e aberturas).

## Regras de execução (herdadas da T14)

- Somente leitura em Protheus, Questor, LNF e banco da BFF durante o inventário.
- Main sem branch; commits só dos arquivos da etapa.
- Nenhum CNPJ, nome de fornecedor ou valor de nota no repositório (ele é público).
