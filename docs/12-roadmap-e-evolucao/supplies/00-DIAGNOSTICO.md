# 00 — Diagnóstico: Suprimentos na Minha DELPI hoje

> **Data:** 2026-09-08 · **Escopo:** monorepo + evidência do Product Owner  
> **Implementação:** nenhuma

---

## Como Suprimentos trabalha hoje

Não existe um portal. O usuário entra na Minha DELPI e escolhe **vários apps** no launcher, com filtros, filiais e vocabulários diferentes.

```text
Usuário de Suprimentos
  ├── Dashboard Suprimentos          (KPIs CPV/OTD/estoque/giro/savings)
  ├── Solicitações de Compras        (SC operacional + escopo CC)
  ├── Estoque de Segurança           (saldo × ESTSEG + simulação)
  ├── Análise - Importações          (evidência PO · não está no git)
  ├── Onde o item é usado - BI       (evidência PO · não está no git)
  ├── Atraso de Fornecedores - SC    (evidência PO · não está no git)
  ├── Alçada de Compras - BI         (evidência PO · não está no git)
  ├── Controle de Estoques - SC - BI (evidência PO · não está no git)
  ├── Indicadores Sheets / IDD       (evidência PO · planilha também no dashboard)
  ├── Strategic Indicators           (metas departamento supplies)
  ├── Chat Minha DELPI               (produto, parents, purchases)
  └── Apps adjacentes                (Inspeções de Entrada, Frete, PCP)
```

**CONFIRMADO_NO_CODIGO:** os três primeiros + SI + chat + adjacentes.  
**CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER:** os seis nomes de BI/Sheets.  
**Ausência no git dos seis códigos `*.access`:** CONFIRMADO_NO_CODIGO.

---

## Personas

Não há seed de papéis «Comprador» / «Analista de Suprimentos» na Core do monorepo. Papéis são dinâmicos. O agrupamento abaixo combina evidência do PO + permissões dos manifests.

| Persona | Filial na evidência | O que faz hoje | Classificação |
|---------|---------------------|----------------|---------------|
| Analista de Suprimentos | SC e ES (perfis separados) | Dashboard + Importações | PO + código dashboard |
| Comprador | SC (evidência); ES **não evidenciado** | BIs operacionais (atraso, alçada, estoque, onde-usado) | PO |
| Solicitante / gestor de CC | Inferido pelo módulo SC | Vê só seus CCs | Código purchase-requests |
| Admin de compras | Inferido | Mapping Protheus, escopos, notificações | Código `purchase-requests.admin` |
| Gestor / diretoria | Inferido | SI + TV + dashboard KPIs | Código SI/TV/dashboard |
| Qualidade (entrada) | Ambas filiais | Inspeções — **não** é persona do Portal | Código inspecoes-entrada |

Diferença SC × ES é **estrutural** (TOTVS `01`/`02`), não cosmética. Permissões de filial já existem, mas com **nomes divergentes** (`filial-01/02` vs `filial-sc/es`). Ver DRIFT em [DUPLICIDADES](./DUPLICIDADES-E-SOBREPOSICOES.md).

Comprador ES: **não** aparece na evidência do PO. `HIPOTESE_A_VALIDAR` se o papel existe no Core prod.

---

## Apps nativos (plugins/)

| App | basePath | Permissão de entrada | Backend |
|-----|----------|----------------------|---------|
| Dashboard Suprimentos | `/apps/dashboard-supplies` | `dashboard-supplies.view` | api-delpi `/supplies/*` **direto** |
| Solicitações de Compras | `/apps/purchase-requests` | `purchase-requests.access` | purchase-requests-api → api-delpi |
| Estoque de Segurança | `/apps/estoque-seguranca` | `estoque-seguranca.access` | api-delpi `/supplies/safety-stock/*` **direto** |
| Materiais de Terceiros | `/apps/materiais-terceiros` | `materiais-terceiros.access` | api-delpi (beneficiamento SB6) |

`docs/08-plugins/README.md` **omite** `purchase-requests` na tabela principal. **DRIFT** documentação × Compose.

---

## BIs / iframe / Sheets

| Nome | No git? | Equivalente parcial |
|------|---------|---------------------|
| Análise - Importações | Não | Nenhum MFE |
| Onde o item é usado - BI | Não | `GET /products/{code}/parents` + chat |
| Atraso de Fornecedores - SC | Não | Seção ranking da página OTD |
| Alçada de Compras | Não | Campo `C7_APROV` no contrato SC (sem UI) |
| Controle de Estoques - SC | Não | Dashboard `/stock` + ESTSEG + `stock-balances` |
| Indicadores Sheets | Perm `idd-suprimentos.access` ausente; planilha **integrada** em savings | SI + `negotiation-savings` |

---

## APIs

| API | Papel hoje |
|-----|------------|
| **api-delpi** | Dona do SQL TOTVS `/supplies/*`, `/products/*` compra/estoque/pais, frete links |
| **purchase-requests-api** | Único BFF de compras; schema `purchase_requests` |
| **strategic-indicators-api** | Metas/realizado dept. `supplies` |
| **financial-api** | Frete das compras (SF8/SF1) |
| **production-control-api** | Consome `open-coverage` (não é dono) |
| **tv-dashboard-api** | Telas nativas `supplies_stock_value`, `supplies_stock_alert` |
| **minha-delpi-ai-api** | Tools domínio supplies |
| **supplies-api** | **Não existe** |

---

## Dados (TOTVS)

| Área | Tabelas |
|------|---------|
| SC / PC / entrada | SC1, SC7, SD1, CTT, SYS_USR |
| Estoque segurança | SB1, SBZ, SB2, SC7, SC1, SD4, SD3, SA5, SA2, SD1 |
| CPV | SD3 classificado como CPV |
| Valor estoque | SB9 (help do dashboard) |
| OTD compras | Linhas MP ou código `3019*`; recebimento ≤ prometida |
| Savings | Google Sheets IDD (não tabela Protheus) |
| Terceiros | SB6 / `VW_PD3_BENEF_RETORNOS` |
| Frete | SF8010, SF1010 |
| Inspeção | views `vw_minha_delpi_inspecoes_entrada_*` |

---

## Dores de fragmentação

1. **Launcher de pedaços** — o trabalho diário exige 5–8 apps.
2. **Filtros diferentes** — dashboard usa `branch` consolidado; SC exige filial; ESTSEG usa `filial-sc/es`.
3. **Mesmo conceito, duas telas** — atraso (BI vs OTD); estoque (BI vs dashboard vs ESTSEG); indicadores (Sheets vs SI).
4. **Onde-usado isolado** do saldo, ESTSEG e última compra.
5. **Sem Fornecedor 360** nem Produto 360 nativos.
6. **Sem worklist** do comprador (aging SC/PC, follow-up) além da lista de SC por CC.
7. **MFEs maduros chamam api-delpi direto** — incompatível com Portal + API própria.
8. **BIs invisíveis no git** — risco de cutover cego.

---

## Duplicidades (resumo)

Ver [DUPLICIDADES-E-SOBREPOSICOES.md](./DUPLICIDADES-E-SOBREPOSICOES.md).

| Par | Relação |
|-----|---------|
| BI atraso × OTD dashboard | Complementar / possivelmente especializado SC — **não** declarado duplicado até dump |
| BI estoque × dashboard `/stock` × ESTSEG | Conceitos diferentes (físico/valor vs segurança vs giro) |
| Sheets IDD × SI savings | Duas superfícies; meta canônica deve ser SI |
| Chat parents × BI onde-usado | Mesma pergunta de negócio, superfícies distintas |

---

## Gaps (não existem hoje no Portal unificado)

- Home de ação + Overview gerencial no mesmo produto.
- Pedidos de compra como jornada (há OTD de PC na api-delpi, sem MFE dedicado).
- Importações, alçadas, scorecard de fornecedor.
- Notas internas / tarefas / alertas persistidos (exceto notificações de SC).
- Capability-driven hub (hoje cada app é um launcher item).
- Ajuda única do domínio (cada MFE tem helps locais).

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Depreciar BI sem paridade | ADR-005 + dump Core |
| Absorver SC com falha de fail-closed | ADR-002 C1 gateway antes de C2 |
| CSS colidir com dashboard legado | ADR-004 `.dashboard-supplies-portal` |
| Copiar TOTVS para Postgres | DATA-MODEL: só estado Delpi |
| Acoplar Qualidade/Financeiro/PCP | MATRIZ-BOUNDARIES: HTTP projeção / deep link |
| Inventar fórmula de KPI | Fichas + status NECESSITA_VALIDACAO |
| Permission PT nova | Aliases; catálogo novo em inglês |

---

## Oportunidade do Portal

Unir **trabalho do dia** (SC, atrasos, ESTSEG, follow-up) com **gestão** (OTD, CPV, giro, savings, SI) e **360** (fornecedor e item), no padrão visual do Comercial, sem roubar SQL da api-delpi nem processo da Qualidade.

Isso é exatamente o que o Comercial já provou: coexistir → paridade → redirect → remover.
