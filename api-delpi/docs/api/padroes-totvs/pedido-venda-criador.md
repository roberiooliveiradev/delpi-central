# Pedido de venda (SC5) — usuário criador

Discovery ago/2026 (Portal Comercial / ata follow-up): existe campo no Protheus que identifique **quem criou** o pedido de venda?

## Veredito

**Indisponível para produto.** Em `SC5010` (empresa 01) **não há** coluna `C5_USER*`, `C5_USR*`, `C5_USUARIO` nem equivalente de auditoria de inclusão mapeável a `SYS_USR` com nome legível.

## Evidência (probe)

Script: [`api-delpi/scripts/sql/sc5_order_creator_probe.py`](../../../scripts/sql/sc5_order_creator_probe.py)

| Achado | Detalhe |
|--------|---------|
| Colunas SC5010 | 213 campos; candidatos por substring USER/USR/UID → só `C5_MSUIDT` |
| SX3 `C5_MSUIDT` | Título **«Campo UUID»** — id técnico da linha (36 chars), não usuário |
| Preenchimento | ~100% nas amostras TOP 500 filiais `01` e `02` |
| Join `SYS_USR` | `USR_UUID` tipicamente em branco; join por UUID **não resolve** nome/`USR_CODIGO` |
| SX3 user-ish | Sem campo de «usuário inclusão» útil (hit falso: `C5_INCISS` = ISS incluso) |

## O que **não** fazer

- Expor `C5_MSUIDT` como «criador» na UI (UUID opaco, sem resolução humana).
- Prometer filtro «por usuário que criou o pedido» no Portal Comercial sem nova fonte (custom TOTVS / auditoria externa).
- Confundir `C5_VEND1`…`C5_VEND5` (vendedor do pedido) com usuário criador do sistema.

## Alternativas futuras (fora do padrão atual)

1. Campo custom Delpi em SC5 + rotina de preenchimento na inclusão.
2. Trilha de auditoria Protheus/SmartClient se a Delpi passar a gravar usuário de forma resolvível.
3. Usar **vendedor** (`C5_VEND*`) só quando a regra de negócio for «responsável comercial», não «login que digitou».

## Relacionado

- Lista abertos: view `VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` + `list_totvs_open_orders`
- Ata: `docs/12-roadmap-e-evolucao/commercial/ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md` §1.3
