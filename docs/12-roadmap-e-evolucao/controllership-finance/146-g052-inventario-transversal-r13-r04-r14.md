# Gate 052 — Inventário transversal R13/R04/R14 (2026-11-02)

## Matriz de classificação — evidência no HEAD

| Item | Natureza | Fonte | Contrato runtime | Lacuna | Readiness |
|---|---|---|---|---|---|
| R13 | DOCUMENTAL externa | Bancos/corretoras | P2/P5 existem (documents_routes, admin_checklist, pendencies) | tipos + aplicabilidade por competência | TARGET — reuso P2/P5 |
| R04 | TOTVS candidata | SD3/MATR860 (não confirmado) | nenhum endpoint | artefato oficial + grão + owner | TO_INVENTORY — bloqueio fonte |
| R14 | DOCUMENTAL externa | importação/câmbio | P2/P5 existem | tipos + regra de aplicabilidade | TARGET — reuso P2/P5 |

## Runtime documental confirmado no HEAD
- documents_routes.py (upload/download/versionamento)
- admin_checklist_routes.py (tipos/vigência via controllership-finance.manage)
- pendencies_routes.py (pendências por competência)
- Fluxos P2 (anexação) e P5 (submissão/revisão) existem — R13/R14 não exigem API nova.

## Decisões necessárias (DECISION_REQUIRED para o PO)
- R13: lista real de instituições/tipos (não presumir XP+BB completa); obrigatoriedade condicional.
- R14: regra de aplicabilidade (quem declara operação de importação por competência).
- R04: owner funcional + artefato oficial MATR860 (sem ele, modelo/grão não são implementáveis honestamente).

## Não executado
Implementação G053-055 não iniciada — inventário/decisões do PO primeiro.
SEARCH_MISS != ABSENCE: MATR860/RPO não comprovado ainda.
