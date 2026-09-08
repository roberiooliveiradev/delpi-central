# PERSONA × EXPERIÊNCIA — Portal Suprimentos

> Personas **orientam UX**. Autorização = **permission codes**. Sem `if role == comprador` no MFE.

Frequência: `diária` · `semanal` · `mensal` · `eventual` — presumida (INFERENCIA) quando não há telemetria.

---

## Tabela principal

| Persona | Filial | App atual | Capacidade | Permission | Fonte | Frequência presumida | Portal alvo | Decisão | Evidência |
|---------|--------|-----------|------------|------------|-------|----------------------|-------------|---------|-----------|
| Analista de Suprimentos | ES | Análise - Importações | Acessar importações | `importados.access` | PO visual | semanal | Compras → Importações (WF-08) | LEGADO_A_VALIDAR + INCORPORAR se dump confirmar | CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER |
| Analista de Suprimentos | ES | Dashboard Suprimentos | Ver KPIs | `dashboard-supplies.view` | manifest | diária | Visão Geral + Gestão | INCORPORAR | CONFIRMADO_NO_CODIGO |
| Analista de Suprimentos | SC | Análise - Importações | Acessar importações | `importados.access` | PO | semanal | WF-08 | LEGADO_A_VALIDAR | PO |
| Analista de Suprimentos | SC | Dashboard Suprimentos | Ver KPIs | `dashboard-supplies.view` | manifest | diária | Visão Geral | INCORPORAR | CONFIRMADO_NO_CODIGO |
| Comprador | SC | Onde o item é usado - BI | Estrutura / pais do item | `onde-e-usado.access` | PO | diária | Produto 360 → Onde é usado (WF-14) | LEGADO_A_VALIDAR; API `get_product_parents` já existe | PO + CONFIRMADO_NO_CODIGO (API) |
| Comprador | SC | Atraso de Fornecedores - SC - BI | Matriz atraso | `matriz_atraso-fornecedores.access` | PO | diária | Entregas/Atrasos + OTD (WF-07/11) | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Alçada de Compras - BI | Alçadas | `alcada-compras.access` | PO | semanal | Compras → Alçadas (hipótese P1) | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Controle de Estoques - SC - BI | Estoque SC | `controle-estoque-sc.access` | PO | diária | Controle de Estoques (WF-15) | LEGADO_A_VALIDAR | PO |
| Comprador | SC | Análise Estoque / Estoque de Segurança | ESTSEG | `estoque-seguranca.access` + `view.filial-sc` | PO nome + manifest | diária | WF-16 | INCORPORAR | PO (nome) + CONFIRMADO_NO_CODIGO (plugin) |
| Analista / gestão | * | Indicadores Sheets | IDD | `idd-suprimentos.access` | PO | mensal | Indicadores + Savings | LEGADO_A_VALIDAR; dado já no dashboard | PO + composer |
| Solicitante / gestor CC | 01 e/ou 02 | Solicitações de Compras | Ver SC do escopo | `purchase-requests.access` + `unit.filial-*` | manifest | diária | WF-04 | INCORPORAR | CONFIRMADO_NO_CODIGO |
| Comprador / visão ampla | 01 e/ou 02 | Solicitações de Compras | Ver todas SC da filial | `purchase-requests.view-all` | manifest | diária | WF-04 | INCORPORAR | CONFIRMADO_NO_CODIGO + PO labels |
| Admin compras | * | Solicitações — admin | Mapping / escopos / notif | `purchase-requests.admin` | manifest | eventual | WF-21 | INCORPORAR | CONFIRMADO_NO_CODIGO |
| Exportador SC | * | Solicitações | Exportar | `purchase-requests.export` | manifest | semanal | WF-04 ação | INCORPORAR | CONFIRMADO_NO_CODIGO |
| Qualidade entrada | 01/02 | Inspeções de Entrada | Pendências / histórico | `inspecoes-entrada.view` + filial | manifest | diária | **não** é persona do Portal; Fornecedor 360 projeta | INTEGRAR | CONFIRMADO_NO_CODIGO |
| Financeiro | 01/02 | Frete | Rateio frete compras | `financial.freight.view` | manifest | semanal | DEEP_LINK | DEEP_LINK | CONFIRMADO_NO_CODIGO |
| Gestor / TV | * | Strategic Indicators / TV | Metas supplies | perms SI/TV | catalog | mensal | WF-02 WF-20 | INTEGRAR | CONFIRMADO_NO_CODIGO |
| Superadmin | * | todos | bypass | `is_superadmin` | código SC/ESTSEG | eventual | todas | manter | CONFIRMADO_NO_CODIGO |

---

## Outros perfis pesquisados no RBAC do git

Busca por roles nomeadas `comprador`, `suprimentos`, `almoxarifado`, `importacao`: **nenhum seed**. **CONFIRMADO_NO_CODIGO** (ausência).

Permissões extras relacionadas:

| Code | Módulo | Relação com Portal |
|------|--------|-------------------|
| `materiais-terceiros.*` | Beneficiamento cliente | FORA_DO_ESCOPO |
| `estoque-seguranca.view.filial-es` | ESTSEG ES | alias futuro `supplies.unit.filial-02` |
| `dashboard-supplies.view` | KPIs | alias `supplies.analytics.view` |

---

## SC vs ES — o que a evidência mostra

| Tema | SC (01) | ES (02) |
|------|---------|---------|
| Analista de Suprimentos | Evidenciado (dashboard + importações) | Evidenciado (dashboard + importações) |
| Comprador | Evidenciado (5 BIs + ESTSEG) | **Não evidenciado** — HIPOTESE_A_VALIDAR no Core |
| Contrato SC | Fill rate `C7_COMPRA` baixo na fil 01 (doc Fase 0.2) | Mesmo contrato; número de PC reutilizado entre filiais |
| Perms nativas | `filial-01` / `filial-sc` | `filial-02` / `filial-es` |
| Dashboard KPIs | Filtro `branch` consolidado **sem** split de perm | idem — uma perm `dashboard-supplies.view` |

**Não assumir** que as necessidades são iguais. O Hub esconde Importações/Alçadas se a capability não existir. O backend **valida filial**; o MFE só oculta navegação.

---

## Experiência alvo por persona (capability-driven)

### Analista

Home com KPIs de atenção + catálogo Gestão + Importações se cap. Overview com 6–8 indicadores. Pouca worklist de SC (a menos que tenha `purchase-requests.*`).

### Comprador

Home = worklist (SC, atrasos, críticos ESTSEG) + busca de item/fornecedor. Produto 360 e Fornecedor 360 como destinos primários. Overview opcional.

### Solicitante

Home mostra só Solicitações + ajuda. Sem CPV/savings se não tiver analytics.

### Admin

Administração: mappings, escopos CC, preferências de notificação, settings do portal.

Mapeamento codes × papéis sugeridos: [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md).
