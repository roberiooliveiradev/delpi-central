# Portal Controladoria & Finanças

> **Status:** TARGET consolidado / implementação não iniciada  
> **Produto:** Portal Controladoria & Finanças  
> **Primeira funcionalidade:** Central de Fechamento  
> **Primeiro processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria  
> **Consolidação:** 05/10/2026

## Objetivo

O **Portal Controladoria & Finanças** é o produto multi-macroprocesso da Minha DELPI para concentrar processos, automações, visões operacionais, evidências, pendências, decisões e capacidades de gestão do domínio de Controladoria & Finanças.

A primeira funcionalidade é a **Central de Fechamento**. O primeiro processo especificado é o **PROC-0072 — Gestão do Fechamento Mensal da Controladoria**.

```text
Minha DELPI
└── Portal Controladoria & Finanças
    ├── Central de Fechamento
    │   └── Fechamento Mensal / PROC-0072
    └── futuros macroprocessos
```

O portal não deve ser tratado como aplicação exclusiva de fechamento. A arquitetura deve permitir novos macroprocessos sem renaming do produto.

## Estado

- AS-IS PROC-0072: **CLOSED / ACCEPTED**
- baseline: **1 fechamento/mês; 960 min INFORMED**
- TO-BE: **TARGET consolidado**
- implementação: **NOT_STARTED**
- ROI: **não calculado**
- P1/P2/P4/P6: **READY_FOR_IMPLEMENTATION_INVENTORY**
- P3: **READY com stop condition em T03**
- P5: **PARTIALLY_READY**, canal de envio depende E04/T04

## Documentação

| Documento | Finalidade |
|---|---|
| [00-governanca-e-authorities.md](./00-governanca-e-authorities.md) | autoridades, evidência e drift |
| [01-visao-produto-naming-e-escopo.md](./01-visao-produto-naming-e-escopo.md) | naming, escopo e fronteiras |
| [02-proc-0072-as-is-e-baseline.md](./02-proc-0072-as-is-e-baseline.md) | processo atual e baseline |
| [03-evidencias-proveniencia-e-rastreabilidade.md](./03-evidencias-proveniencia-e-rastreabilidade.md) | fontes e proveniência |
| [04-regras-de-negocio-consolidadas.md](./04-regras-de-negocio-consolidadas.md) | GAP-RULE-01 a 07 |
| [05-diagnostico-gaps-e-oportunidades.md](./05-diagnostico-gaps-e-oportunidades.md) | diagnóstico e oportunidades |
| [06-arquitetura-funcional-to-be.md](./06-arquitetura-funcional-to-be.md) | modelo funcional |
| [07-ux-jornadas-e-estados-de-experiencia.md](./07-ux-jornadas-e-estados-de-experiencia.md) | UX transversal |
| [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md) | P1 |
| [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md) | P2 |
| [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md) | P3 |
| [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md) | P4 |
| [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md) | P5 |
| [13-p6-administracao-e-configuracao.md](./13-p6-administracao-e-configuracao.md) | P6 |
| [14-seguranca-rbac-auditoria-e-ia.md](./14-seguranca-rbac-auditoria-e-ia.md) | AuthZ, auditoria e IA |
| [15-requisitos-criterios-de-aceite-e-testes.md](./15-requisitos-criterios-de-aceite-e-testes.md) | RQ/AC e testes |
| [16-configuracoes-catalogos-e-notificacoes.md](./16-configuracoes-catalogos-e-notificacoes.md) | configurações e notificações |
| [17-backlog-de-confirmacoes-e-inventarios.md](./17-backlog-de-confirmacoes-e-inventarios.md) | E01–E06 e T01–T05 |
| [18-readiness-e-handoff-de-implementacao.md](./18-readiness-e-handoff-de-implementacao.md) | readiness e handoff |
| [19-rastreabilidade-teo.md](./19-rastreabilidade-teo.md) | mapa dos registros TÉO |

## Invariantes

1. `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`
2. `ATTACHED != VALIDATED`
3. ausência/erro de source != zero
4. pre-cutoff dependente != final
5. último upload != auto-send
6. Finalizar != Enviar
7. PACKAGE_SENT é imutável
8. mudança mestre não altera snapshot
9. listas operacionais são configuráveis
10. IA sugere/explica; humano decide
11. `ACCESS != MANAGE`
12. aprovação administrativa != validação
13. sem SLA formal
14. V1 sem escrita ERP para sacramentação/classificação
15. paridade monetária da conciliação tripla exige exatamente R$ 0,00; não existe tolerância de centavos

## Produtos existentes

`plugins/financial` + `financial-api` e o roadmap `financeiro-controladoria` continuam distintos. O novo portal não absorve nem remove esses contextos automaticamente.

## Execução

```text
READ → INVENTORY → VERIFY → CLASSIFY → DECIDE
→ IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME
→ RESIDUAL SEARCH → DOCUMENT → REPORT
```
