# PERSONA × EXPERIÊNCIA — Portal Suprimentos

> Personas orientam UX. Autorização real = **effective permissions do Core + unit scope + resource scope/ownership + regra de negócio**. Sem `if role == comprador` no MFE.

Frequência: diária · semanal · mensal · eventual — presumida quando não há telemetria.

---

## Tabela principal

| Persona | Filial | App atual | Capacidade | Permission atual/evidenciada | Portal alvo | Capability canônica alvo | Decisão | Evidência |
|---|---|---|---|---|---|---|---|---|
| Analista de Suprimentos | ES | Análise - Importações | importações | `importados.access` | WF-08 | a definir após dump; não criar code prematuro | LEGADO_A_VALIDAR | PO |
| Analista de Suprimentos | ES | Dashboard Suprimentos | KPIs | `dashboard-supplies.view` | Overview/Gestão | `supplies.analytics.access` | INCORPORAR | código/manifest |
| Analista de Suprimentos | SC | Análise - Importações | importações | `importados.access` | WF-08 | a definir após dump | LEGADO_A_VALIDAR | PO |
| Analista de Suprimentos | SC | Dashboard Suprimentos | KPIs | `dashboard-supplies.view` | Overview | `supplies.analytics.access` | INCORPORAR | código/manifest |
| Comprador | SC | Onde o item é usado - BI | estrutura do item | `onde-e-usado.access` | Produto 360 / WF-14 | `supplies.operations.access` | LEGADO_A_VALIDAR + reusar API | PO + API existente |
| Comprador | SC | Atraso de Fornecedores - SC - BI | atraso | `matriz_atraso-fornecedores.access` | WF-07/WF-11 | operations para ação; analytics para OTD gerencial | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Alçada de Compras - BI | alçada | `alcada-compras.access` | `/approvals` se validado | não criar permission até saber se é consulta ou aprovação | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Controle de Estoques - SC - BI | estoque | `controle-estoque-sc.access` | WF-15 | `supplies.operations.access` | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Estoque de Segurança | ESTSEG | `estoque-seguranca.access` + filial | WF-16/17 | `supplies.operations.access` + unit | INCORPORAR | plugin atual |
| Analista / gestão | * | Indicadores Sheets | IDD/savings | `idd-suprimentos.access` | WF-18/WF-20 | `supplies.analytics.access` se confirmado | LEGADO_A_VALIDAR | PO + composer |
| Solicitante / gestor CC | 01/02 | Solicitações de Compras | SC no escopo | `purchase-requests.access` + unit | WF-04 | `supplies.purchase-requests.access` + unit | INCORPORAR | código |
| Comprador / visão ampla | 01/02 | Solicitações de Compras | ampliar CC | `purchase-requests.view-all` | WF-04 | `supplies.purchase-requests.view-all` | INCORPORAR | código |
| Admin compras | * | Solicitações — admin | mapping/scopes | `purchase-requests.admin` | WF-21 | `supplies.administration.manage` | INCORPORAR | código |
| Exportador SC | * | Solicitações | exportar | `purchase-requests.export` | WF-04 | `supplies.purchase-requests.export` enquanto segregação justificar | INCORPORAR | código |
| Qualidade entrada | 01/02 | Inspeções de Entrada | inspeções | perms Qualidade | projeção Supplier 360 | permanece no contexto Qualidade | INTEGRAR | código |
| Financeiro | 01/02 | Frete | frete compras | perms Financeiro | deep link | permanece no Financeiro | DEEP_LINK | código |
| Gestor / TV | * | SI / TV | metas/visualização | perms SI/TV | WF-02/WF-20 | `supplies.analytics.access` para o Portal; SI continua owner | INTEGRAR | código |
| Superadmin | * | todos | bypass governado | effective `is_superadmin` resolvido pelo Core | conforme política | não vira permission comum | manter | Core/API |

---

## SC vs ES

| Tema | SC (01) | ES (02) |
|---|---|---|
| Analista | evidenciado | evidenciado |
| Comprador | evidenciado | não evidenciado; validar E1.S2 |
| Unit canônica futura | `supplies.unit.filial-01` | `supplies.unit.filial-02` |
| Legados | `filial-01` / `filial-sc` | `filial-02` / `filial-es` |

Não assumir necessidades idênticas. O Portal não cria telas “versão SC/ES”; usa unit scope.

---

## Experiência alvo por persona

### Analista

- Home;
- Overview e indicadores;
- operações somente se `supplies.operations.access` também estiver presente;
- Importações apenas após confirmação do contrato.

### Comprador

- Home orientada a exceções;
- PC/entregas;
- Supplier 360;
- Produto/MP 360;
- estoque/ESTSEG;
- SC se também tiver `supplies.purchase-requests.access`.

### Solicitante

- Home reduzida;
- Solicitações de Compras;
- Ajuda;
- sem analytics/operations sem capability correspondente.

### Admin

- Administração;
- não recebe automaticamente acesso a todas as units;
- demais capabilities somente quando necessárias.

---

## Regra de permission minimization

Uma persona não gera uma permission por tela. Novo botão/CRUD não cria code automaticamente. Preferir capability funcional + unit + ownership. Só separar permission quando houver diferença material de risco, público, segregação, exportação sensível, operação em massa ou administração.
