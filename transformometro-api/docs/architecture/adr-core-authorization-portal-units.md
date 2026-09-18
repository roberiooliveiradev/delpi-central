# ADR — Core autoriza; o Portal é dono da unidade

**Status:** SUPERSEDED_BY_BUSINESS_DECISION (2026-09-18). **Não implementar.**
**Desenho:** [`AUTHZ-FINAL-DESIGN.md`](../../../docs/12-roadmap-e-evolucao/transformometro-app/AUTHZ-FINAL-DESIGN.md)

## Contexto

O catálogo funcional alvo do Portal Transforma+ é `transformometro.access` e `transformometro.manage`. Unidade não pode continuar como permission por filial. A filial já existe em `transformometro.filiais`.

## Decisão superada

A decisão de gravar no Core um vínculo de unidades foi cancelada. O Portal não segrega autorização por filial. Quem tem `transformometro.access` vê todos os processos. Filial continua objeto do Transformômetro e filtro da Visão geral.

O texto abaixo registra o que foi proposto e não deve ser implementado.

## Decisão original, não vigente

1. Keycloak autentica. A Core API decidiria permissão e o vínculo de unidades.
2. O Transformômetro é dono do objeto unidade e das regras de domínio.
3. O Core guardaria `codigo_filial` opaco, sem FK.
4. Modos `none`, `units` e `all`.
5. Portal, TÉO, MCP e GPT Actions não autorizam.

## Consequências vigentes

- Não criar tabela, campo no `/me` nem contrato de unit scope.
- `manage` continua sem implicar `access`.
- O desenho vigente é [AUTHZ-FINAL-DESIGN.md](../../../docs/12-roadmap-e-evolucao/transformometro-app/AUTHZ-FINAL-DESIGN.md).
