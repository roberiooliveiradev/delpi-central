# ADR — Core autoriza; o Portal é dono da unidade

**Status:** aceito como desenho (2026-09-18). **Não implementado.**  
**Desenho:** [`AUTHZ-FINAL-DESIGN.md`](../../../docs/12-roadmap-e-evolucao/transformometro-app/AUTHZ-FINAL-DESIGN.md)

## Contexto

O catálogo funcional alvo do Portal Transforma+ é `transformometro.access` e `transformometro.manage`. Unidade não pode continuar como permission por filial. A filial já existe em `transformometro.filiais`.

## Decisão

1. Keycloak autentica. A Core API decide permissão e o vínculo de quais unidades da aplicação o principal pode usar.
2. O Transformômetro é dono do objeto unidade e das regras de processo, instância, revisão, medição, melhoria, ata e evidência. Pode negar operação autorizada pelo Core. Não pode permitir operação que o Core negou.
3. O Core não replica o catálogo de filiais, não cria FK e não lê o schema `transformometro`. Guarda `codigo_filial` como identificador opaco.
4. Modos do vínculo: `none`, `units`, `all`. Ausência não é `all`. `units` com `01` e `02` não inclui unidade futura. `all` inclui.
5. Portal, TÉO, MCP e GPT Actions não autorizam. Não há tool nem Action nova por causa desta decisão.

## Consequências

- A fase 1 é só o vínculo no Core. O manifesto de 21 códigos permanece até o escopo estar provado em runtime.
- Referência a código inexistente ou filial inativa não autoriza. As demais unidades da mesma lista continuam válidas.
- `manage` não implica `access`. O resolver atual não tem hierarquia de permission.
