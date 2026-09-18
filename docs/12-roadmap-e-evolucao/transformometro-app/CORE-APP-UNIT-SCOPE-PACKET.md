# Core app unit scope — CANCELLED_BY_BUSINESS_DECISION

> **Não é work item.** Não implementar.
> Criado em `ce458acf2`. Cancelado neste desenho.

Premissa antiga: o Core guardaria quais unidades do Portal cada principal pode usar.

Premissa nova: o Portal Transforma+ é multiunidade e não segrega autorização por unidade. Quem tem `transformometro.access` vê todos os processos. Filial é objeto do Transformômetro e filtro da Visão geral.

Não haverá tabela de unit scope, campo no `/me`, auditoria de assignment de unidade, dual-read de filial nem contrato Core ↔ Transformômetro para autorização.

O histórico do pacote permanece no Git, no commit que o criou. A autoridade vigente é [AUTHZ-FINAL-DESIGN.md](./AUTHZ-FINAL-DESIGN.md).
