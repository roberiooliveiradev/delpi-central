# ADR-003 — Coexistência e cutover dos dashboards de Engenharia

- **Status:** Accepted
- **Data:** 2026-09-11

## Contexto

`dashboard-engineering` e `dashboard-lmps` já possuem usuários, permissions, rotas e funcionalidades. Removê-los no mesmo release que cria o Portal aumenta risco de perda de acesso, divergência de dados e deep links quebrados.

## Decisão

Adotar migração target-first em quatro movimentos:

```text
C1 coexistência
→ C2 soft cutover
→ C3 redirects compatíveis
→ C4 hard cutover
```

O Portal nasce ao lado dos legados. Cada legado só avança após `GATE-PARITY` próprio.

## Regras

- `dashboard-engineering` migra para a Visão geral após paridade de indicadores/IDD/permissions;
- `dashboard-lmps` migra para LMPs após paridade de lista, detalhe, histórico, Gantt e NCs;
- permissions legadas não são removidas antes do mapping de usuários/grupos;
- deep links antigos recebem destino explícito;
- hard cutover não acontece no mesmo passo da primeira implementação do target;
- rollback restaura menu/redirect/manifest sem apagar estado novo do Portal.

## Fora desta decisão

`controle-mp` segue o roadmap próprio para `my-requests`. Transformômetro permanece owner do TRANSFORMA+.

## Evidência necessária para GO

- personas positivas/negativas;
- comparação quantitativa;
- smoke federado;
- redirects testados;
- observabilidade ativa;
- rollback ensaiado;
- autorização explícita do Product Owner.
