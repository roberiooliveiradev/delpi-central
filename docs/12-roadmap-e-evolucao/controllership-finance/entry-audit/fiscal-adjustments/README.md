# Entry audit — Ajustes pedidos pelo Fiscal

| Campo | Valor |
|---|---|
| Status | **INVENTÁRIO CONCLUÍDO** (T14, 2026-11-18) — implementação não iniciada |
| Origem | análise do Fiscal sobre as entradas de 01–17/11/2026 (documento fora do repositório) |
| Autoridade | instruções oficiais do arquiteto e `.cursor` aplicáveis > [ADR-003](../../adr/ADR-003-entry-audit.md) > [track.md](../track.md) > [plan.md](./plan.md) |
| Regra de dado | repositório público: nenhum CNPJ, nome de fornecedor, número de nota ou valor de documento nestes arquivos — só estrutura e contagens |

## Os cinco ajustes

1. Participante pelo cadastro de **clientes (SA1)** nas notas `F1_TIPO` B/D — hoje o motor só resolve o partido pela SA2 (fornecedores).
2. **IBS/CBS em todas as entradas** — o XML já traz o grupo `IBSCBS` e o Protheus calcula tributos genéricos na F2D; o motor e o leitor de XML não veem nada disso.
3. **TES de insumo fora de «Crédito de IPI em uso e consumo»** — TES de insumo que calcula/credita IPI em material marcado como uso e consumo.
4. **Uma ocorrência por causa** — hoje há ocorrências dependentes («Acompanha…») e documentos marcados como divergentes mesmo com todas as ocorrências resolvidas.
5. **Reverificação automática e indicadores ao vivo** — hoje a análise é só sob demanda (D10); não há re-execução agendada nem painel de evolução dos indicadores em tempo real.

## Conteúdo

| Arquivo | O que tem |
|---|---|
| [plan.md](./plan.md) | espelho do plano anexo (sem dado real): contexto, autoridade, premissas da seção 1 e decisões |
| [inventory.md](./inventory.md) | inventário da T14 (I2–I4): premissas conferidas no código com arquivo:linha, estrutura Protheus (F2B/F2D/SFT/SF4/SA1) e grupo IBSCBS no cache de XML |

## Trilha

| Etapa | Nome | Status |
|---|---|---|
| T14 | Inventário dos ajustes do Fiscal (somente leitura) | DONE — 2026-11-18, HEAD `784d7047a6` |
| T15+ | Implementação | TODO — aguarda decisão do owner sobre o relatório da T14 |
