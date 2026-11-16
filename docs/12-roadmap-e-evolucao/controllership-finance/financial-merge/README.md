# Fusão do Portal Financeiro no Portal Controladoria & Finanças (doc 172)

> **Status (16/11/2026):** `PLANNED` — fase documental. Nenhuma mudança de runtime, permissão ou rota está autorizada por este documento. Próximo passo: inventário M0 (somente leitura) e decisões do owner D1–D7.

**Objetivo do owner:** o Portal Financeiro passa a viver dentro do Portal Controladoria & Finanças, com as permissões do Portal (`controllership-finance.access` e `controllership-finance.manage`). Precedente de método: a migração do Lançamento de Notas Fiscais ([163](../163-plano-migracao-lancamento-notas-fiscais.md), [164](../164-runbook-corte-lancamento-notas-fiscais.md), [165](../165-trilha-execucao-migracao-lnf-ate-clara.md), [ADR-001](../adr/ADR-001-hospedagem-lancamento-notas-fiscais.md)).

| Documento | Conteúdo |
|---|---|
| [plan.md](./plan.md) | AS-IS conferido no código, alvo, sobreposições, decisões D1–D7 com opções e recomendação, fases M0–M7, riscos |
| [prompts/M0-inventario.md](./prompts/M0-inventario.md) | prompt do Cursor para o inventário somente leitura, com o verificador |
