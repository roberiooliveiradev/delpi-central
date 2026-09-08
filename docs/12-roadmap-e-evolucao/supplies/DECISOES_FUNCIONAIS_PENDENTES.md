# DECISOES_FUNCIONAIS_PENDENTES

Só o que o repositório não responde. Não bloqueia o desenho, mas pode bloquear implementação/cutover conforme o impacto.

| ID | Pergunta | Impacto | Subetapa atual |
|---|---|---|---|
| P-01 | URLs, ids e tipo dos 6 apps/BIs do PO | menu, paridade, redirects | E1.S1 |
| P-02 | Comprador ES existe no Core? | papel + unit-02 | E1.S2 |
| P-03 | Regra do BI Atraso SC = OTD nativo? | WF-07/paridade | E1.S1 + E7.S1 |
| P-04 | Regra do BI Controle Estoques SC | WF-15/paridade | E1.S1 + E8 |
| P-05 | Existe processo de importação/TOTVS já mapeado? | WF-08 | E1.S1 |
| P-06 | Alçada é consulta ou workflow de aprovação? | permission/SoD futura | E1.S1 + backlog E20.S3 |
| P-07 | Quem edita IDD/Sheets e o app deve permanecer? | manter externo vs integrar | E1.S1 |
| P-08 | Cobertura = meses de giro ou cobertura ESTSEG? | KPI bloqueado | E1.S3 |
| P-09 | Threshold aging SC/PC | worklist | homologação antes de nomear buckets |
| P-10 | Estratégia/janela de transição C2 | reconciliação SC | E6.S4 + E16 |
| P-11 | Quais campos de Qualidade podem aparecer no Supplier 360? | RBAC cruzado | E9 |
| P-12 | Owner formal de cada KPI | status final das fichas | E1.S3 |
| P-13 | Identificador canônico de usuário persistido no schema supplies | data model | antes de E2.S4 |

## Decisões fechadas pelo PO / arquitetura

- Unidade = eixo ortogonal `supplies.unit.filial-{TOTVS}` — ADR-006.
- Permission catalog deve ser mínimo; não espelhar CRUD — ADR-007.
- Tasks/notas não recebem permissions read/write separadas na P0 sem evidência de risco/público distinto.
- Framework supplies-api = Flask pela precedência oficial — ADR-001.
- JWT não é fonte final de permissions; Core resolve effective permissions — ADR-001/006.
- C2 ocorre antes de C3 — ADR-002 + IMPLEMENTATION-PLAN.

## Gates

- P-01/P-03/P-04/P-07 não podem chegar ao cutover ainda como `LEGADO_A_VALIDAR`.
- P-06 só cria `supplies.approvals.manage` se houver aprovação/rejeição real ou segregação material.
- P-13 precisa estar fechado antes da primeira migration que persista referência de usuário.
