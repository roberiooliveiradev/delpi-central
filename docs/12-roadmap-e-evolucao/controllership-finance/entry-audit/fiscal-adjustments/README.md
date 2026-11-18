# Entry audit — Ajustes pedidos pelo Fiscal

| Campo | Valor |
|---|---|
| Status | **READY** — [trilha de execução](./track.md) T15–T23, decisões FA-1 a FA-18 tomadas (2026-11-18) |
| Origem | análise do Fiscal sobre as entradas de 01–17/11/2026 (documento fora do repositório) |
| Autoridade | instruções oficiais do arquiteto e `.cursor` aplicáveis > [ADR-003](../../adr/ADR-003-entry-audit.md) > [track.md](./track.md) (esta frente) > [entry-audit/track.md](../track.md) (regras gerais) |
| Regra de dado | repositório público: nenhum CNPJ, nome de fornecedor, número de nota ou valor de documento nestes arquivos — só estrutura e contagens |

## Os cinco ajustes

1. Participante pelo cadastro de **clientes (SA1)** nas notas `F1_TIPO` B/D — hoje o motor só resolve o partido pela SA2 (fornecedores).
2. **IBS/CBS em todas as entradas** — o XML já traz o grupo `IBSCBS` e o Protheus calcula tributos genéricos na F2D; o motor e o leitor de XML não veem nada disso.
3. **TES de insumo fora de «Crédito de IPI em uso e consumo»** — TES de insumo que calcula/credita IPI em material marcado como uso e consumo.
4. **Uma ocorrência por causa** — hoje há ocorrências dependentes («Acompanha…») e documentos marcados como divergentes mesmo com todas as ocorrências resolvidas.
5. **Reverificação e indicadores ao vivo** — reverificar as pendências no Protheus sem nova análise, **sob demanda** (botão e CLARA; D10 mantida), com indicadores recalculados a cada mudança de status.

## Conteúdo

| Arquivo | O que tem |
|---|---|
| [track.md](./track.md) | **trilha de execução**: decisões FA-1 a FA-18, quadro de status, etapas T15–T23, paradas, registro |
| [plan.md](./plan.md) | ponteiro para o track |
| [inventory.md](./inventory.md) | inventário da T14 (I2–I4): premissas conferidas no código com arquivo:linha, estrutura Protheus (F2B/F2D/SFT/SF4/SA1) e grupo IBSCBS no cache de XML |

## Trilha

Quadro de status e registro em [track.md](./track.md) (Partes 2 e 5).
