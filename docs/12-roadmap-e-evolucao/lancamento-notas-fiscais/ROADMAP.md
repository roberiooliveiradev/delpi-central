# Roadmap — Lançamento de Notas Fiscais

> Atualizado: 2026-07-24 · Detalhe operacional: [PLAYBOOK.md](./PLAYBOOK.md)

| Etapa | Escopo | Status |
|-------|--------|--------|
| 0 | Descoberta / alinhamento de negócio | Feito |
| 1A | Homologação TOTVS (SA2, SF1, chave, filiais) | Feito |
| 1B | Spec funcional/técnica | Feito (manter alinhada ao código) |
| 2A | Schema Postgres (V001) | Feito |
| 2B | API + use cases + conciliação | Feito |
| 2C | Cooldown refresh (V002) + pad documento 9 (V003) | Feito |
| 3 | MFE (fila, form, detalhe, RBAC UI) | Feito |
| 4 | UX (header marca, Já lançada, valor BR, layout detalhe) | Feito |
| 5 | Job agendado de conciliação | Backlog |
| 6 | Permissões por filial | Feito |
| 7 | KPI/resumo de fila + exposição chat | Backlog |

## Critérios de “pronto” do MVP

- [x] Criar / listar / detalhar solicitação
- [x] Start / block / resume / cancel / comment
- [x] `post-manual` para atendente (`process`)
- [x] Refresh de conciliação sem travar UI
- [x] Documentação plugin + API + playbook + índices monorepo
