# DECISOES_FUNCIONAIS_PENDENTES

Só o que o repositório não responde. Não bloqueia o desenho, mas pode bloquear implementação/cutover conforme o impacto.

| ID | Pergunta | Impacto | Estado E1 | Subetapa |
|---|---|---|---|---|
| P-01 | URLs, ids e tipo dos 6 apps/BIs do PO | menu, paridade, redirects | **BLOQUEADO_COM_EVIDENCIA** — Core local 2026-09-08: 0/6; falta dump prod | E1.S1 → reabrir com Core prod |
| P-02 | Comprador ES existe no Core? | papel + unit-02 | **FECHADO_PARA_DESENHO** — Core local sem papéis supplies; sem evidência PO de comprador ES; **sem permission nova**; smoke prod fica para E3.S5 (`HIPOTESE_A_VALIDAR` operacional) | E1.S2 |
| P-03 | Regra do BI Atraso SC = OTD nativo? | WF-07/paridade | **BLOQUEADO_COM_EVIDENCIA** — BI id/path desconhecido até dump prod; OTD nativo documentado no help | E1.S1 + E7.S1 |
| P-04 | Regra do BI Controle Estoques SC | WF-15/paridade | **BLOQUEADO_COM_EVIDENCIA** — mesmo motivo P-01 | E1.S1 + E8 |
| P-05 | Existe processo de importação/TOTVS já mapeado? | WF-08 | **BLOQUEADO_COM_EVIDENCIA** — app não no Core local; nenhuma rota nativa confirmada no monorepo | E1.S1 |
| P-06 | Alçada é consulta ou workflow de aprovação? | permission/SoD futura | **BLOQUEADO_COM_EVIDENCIA** — sem app no Core local; não criar `approvals.manage` | E1.S1 + E20.S3 |
| P-07 | Quem edita IDD/Sheets e o app deve permanecer? | manter externo vs integrar | **BLOQUEADO_COM_EVIDENCIA** — app não no Core local; leitura savings via api-delpi não resolve editor | E1.S1 |
| P-08 | Cobertura = meses de giro ou cobertura ESTSEG? | KPI bloqueado | **FECHADO** — fora do Overview P0 (`BLOQUEADO`); ver KPI-FICHAS E1.S3 | E1.S3 |
| P-09 | Threshold aging SC/PC | worklist | aberto | homologação antes de nomear buckets |
| P-10 | Estratégia/janela de transição C2 | reconciliação SC | aberto | E6.S4 + E16 |
| P-11 | Quais campos de Qualidade podem aparecer no Supplier 360? | RBAC cruzado | aberto | E9 |
| P-12 | Owner formal de cada KPI | status final das fichas | **FECHADO** — owner = área Suprimentos; aceite nominal PO pendente na Assinatura | E1.S3 |
| P-13 | Identificador canônico de usuário persistido no schema supplies | data model | **FECHADO** — Core `/me.id` UUID; `keycloak_sub` opcional; ver DATA-MODEL §2 | E2.S4 |

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
- P-13 fechado: Core `/me.id` (UUID) é o identificador persistido.
