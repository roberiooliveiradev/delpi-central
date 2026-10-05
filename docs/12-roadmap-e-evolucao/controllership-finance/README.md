# Portal Controladoria & Finanças

> **Status:** TARGET / NOT_STARTED  
> **Produto:** Portal Controladoria & Finanças  
> **Primeira funcionalidade:** Central de Fechamento  
> **Primeiro processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria  
> **Snapshot TÉO:** 2026-10-05

## Objetivo

O **Portal Controladoria & Finanças** é o produto multi-macroprocesso da Minha DELPI para concentrar, ao longo do tempo, processos, automações, visões operacionais, evidências, pendências, decisões e capacidades de gestão do domínio de Controladoria & Finanças.

A **Central de Fechamento** é a primeira funcionalidade desenhada. O PROC-0072 é o primeiro processo dentro dela.

```text
Minha DELPI
└── Portal Controladoria & Finanças
    └── Central de Fechamento
        └── Fechamento Mensal / PROC-0072
```

## Estado atual

- Produto: **TARGET**
- Implementação: **NOT_STARTED**
- P1 / P2 / P4 / P6: **READY_FOR_IMPLEMENTATION_INVENTORY**
- P3: **READY**, com stop condition em T03
- P5: **PARTIALLY_READY**, pois Q22 depende de E04/T04
- Nome de UX não define automaticamente plugin id, slug, rota, BFF ou nome técnico.

## Relação com produtos e roadmaps existentes

- [Portal Financeiro P0](../financial/README.md) permanece PROVEN/runtime atual em `plugins/financial` + `financial-api`. Absorção, migração ou desativação **não estão decididas** aqui.
- [Financeiro / Controladoria — Transforma+](../financeiro-controladoria/README.md) permanece como discovery/roadmap histórico CTL-*.
- Este diretório registra o **TARGET atual** do novo produto.

Se evidência futura contradizer o TARGET, classificar `EXECUTION_DRIFT`; não reconciliar silenciosamente.

## Documentos desta pasta

| Documento | Papel |
|---|---|
| [AUTHORITY-INDEX.md](./AUTHORITY-INDEX.md) | Authority, naming e mapa documental |
| [IMPLEMENTATION-READINESS.md](./IMPLEMENTATION-READINESS.md) | Readiness por página, E/T e stop conditions |
| [EXISTING-PRODUCT-BOUNDARIES.md](./EXISTING-PRODUCT-BOUNDARIES.md) | Fronteiras com produtos/roadmaps existentes |
| [teo/README.md](./teo/README.md) | Política de sincronização/snapshot do TÉO |
| [teo/proc-0072/README.md](./teo/proc-0072/README.md) | Índice dos 42 documentos TÉO copiados |
| [teo/proc-0072/INSTANCE-SUMMARY.md](./teo/proc-0072/INSTANCE-SUMMARY.md) | Snapshot do resumo reconciliado da instância |

## Leitura recomendada

1. TÉO **31.19** — Naming Oficial e Escopo
2. TÉO **31.18** — Authority/Readiness
3. TÉO **31** — Desenho Funcional TO-BE
4. TÉO **31.1** — UX/Wireframes/Jornadas
5. TÉO **31.2** — RQ/AC/Estados/Auditoria
6. TÉO **31.3–31.17** — decisões/especificações P2–P6
7. TÉO **33** — decisões consolidadas
8. TÉO **34** — backlog da implementação

## Invariantes

- `STOCK_CLOSED != PACKAGE_SENT != MONTHLY_CLOSING_COMPLETED`
- `ATTACHED != VALIDATED`
- ausência/erro de fonte != zero
- pre-cutoff != final para dado dependente de cutoff
- último upload != envio automático
- Finalizar != Enviar
- pacote enviado não é sobrescrito
- snapshot aberto/histórico não muda por alteração mestre futura
- bancos/contas e catálogos operacionais são configuráveis; seed histórico não vira hardcode
- IA explica/sugere; humano executa atos de negócio
- ACCESS != MANAGE
- MANAGE approval != evidence validation
- sem SLA formal no TARGET atual
- Portal V1 não assume escrita ERP para sacramentação/classificação

## Governança

Esta documentação **não autoriza implementação global**.

```text
READ
→ INVENTORY
→ VERIFY OWNER / CONTRACT / AUTHZ
→ CLASSIFY
→ DECIDE
→ IMPLEMENT MINIMAL DIFF
→ TEST
→ VERIFY OUTCOME
→ RESIDUAL SEARCH
→ DOCUMENT
→ REPORT
```

O snapshot TÉO não é sincronização automática. Mudanças posteriores precisam ser reconciliadas explicitamente.
