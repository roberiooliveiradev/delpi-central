# 28 — Fase 3A.2: Filiais e centros de custo (frontend)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** MFE — administração de CC via ERP + telas branch-aware  
**Manifesto:** `0.2.1`  
**Status:** CONCLUÍDO COM RESSALVAS (smoke autenticado pendente)

---

## 1. Tela administrativa

Rota: `/apps/planejamento-orcamentario/admin/centros-de-custo`  
Título: **Centros de Custo**  
Permissão: `scopes.manage` ou `admin`

Fluxo: filial → consulta ERP → adicionar ao planejamento → lista interna.

Sem digitação de código/descrição.

Estados: filial não selecionada, carregando ERP, nenhum encontrado, erro, cadastrando, cadastro concluído, já cadastrado, acesso negado (401/403).

---

## 2. Contratos consumidos

| Ação | Endpoint |
|------|----------|
| Lista ERP | `GET /planejamento-orcamentario/org/erp-cost-centers?branch=` |
| Cadastro | `POST /planejamento-orcamentario/admin/org/cost-centers/from-erp` |
| Catálogo interno | via `GET /admin/scopes` → `catalog.cost_centers` |

Consulta ERP carrega **uma filial por vez**.

---

## 3. Identificação visual

Formato canônico: `Filial 01 · 1234 — Produção`  
Helpers: `src/utils/orgCostCenters.ts` (`formatCostCenterLabel`, `costCenterKey`).

Keys/selects usam `id:` UUID, `branch:code` ou `unit|code` — nunca só o código.

---

## 4. Responsáveis e escopos

- Fluxo **Filial → Área (opcional) → Centro**  
- Troca de filial limpa o centro  
- Select filtrado pela filial  
- Listagens exibem filial no rótulo do CC  
- Escopos: formulário manual de CC removido; link para a tela administrativa ERP

---

## 5. CAPEX

Ajustes mínimos em: meus centros, formulário, workflow, fila, detalhe, consolidação — filial visível; links/query com `unit_id` + `cost_center_id`; `resolve` envia `unit_id`.  
Consolidação: opções de CC só após selecionar filial (evita colisão de código).

---

## 6. Validação executada

| Gate | Resultado |
|------|-----------|
| ESLint | 0 errors (19 warnings pré-existentes de `set-state-in-effect`) |
| Typecheck | OK |
| Vitest | 24 arquivos / 142 testes OK |
| `npm run build` | OK (`remoteEntry.js` gerado) |
| Rebuild MFE | `./infra/scripts/up-dev-sequential.sh --fase mfe --build planejamento-orcamentario` |
| `remoteEntry.js` HTTP | **200** em `http://localhost/apps/planejamento-orcamentario/assets/remoteEntry.js` |
| Smoke autenticado UI | Pendente (requer login no portal) |

---

## 7. Testes cobertos

- `orgCostCenters.test.ts` — label, key, busca, identidade branch+code  
- `AdminCentrosCustoPage.test.tsx` — filiais 01/02, busca, cadastro, já cadastrado, erro ERP, 401/403, sem permissão  
- `AdminScopesPage.test.tsx` / `AdminResponsaveisPage.test.tsx` — filtro por filial, limpeza ao trocar  
- CAPEX: labels com filial, `unit_id` no resolve, selects compostos, fila/consolidação  

---

## 8. Pendências

- Smoke autenticado no portal (depende de login)  
- Pessoal (fora do escopo desta fase)  
- Não alterar V007 / backend / workflow / consolidação de negócio  
