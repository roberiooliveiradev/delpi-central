# 16 — Fase 2A.2 — Responsabilidades orçamentárias (frontend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** UI gerencial de responsáveis CAPEX, “Meus centros de custo”, integração com endpoints 2A.1, testes Vitest.  
**Fora:** categorias/itens CAPEX, fornecedor, valor, workflow/aprovação, alteração de manifesto, migration V002, regras de backend.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO COM RESSALVAS
```

Ressalvas: smoke autenticado das telas (login JWT / manifesto no menu) permanece bloqueado pela mesma limitação da Fase 1.1 (`get-dev-token.sh`). Validação técnica coberta por Vitest + build + `remoteEntry.js` HTTP 200.

---

## 1. Rotas e telas

| Rota portal | AppRoute | Tela |
|-------------|----------|------|
| `/apps/planejamento-orcamentario/admin/responsaveis` | `admin-responsaveis` | Responsáveis por Centro de Custo |
| `/apps/planejamento-orcamentario/capex` | `capex` | Meus centros de custo |
| `/apps/planejamento-orcamentario/capex/meus-centros` | `capex` | Alias da mesma tela |

Acesso visual admin: `planejamento-orcamentario.scopes.manage` **ou** `planejamento-orcamentario.admin` (`hasScopesManageAccess`). Card em Administração + link na Home para CAPEX.

---

## 2. Componentes / módulos

| Arquivo | Papel |
|---------|--------|
| `pages/admin/AdminResponsaveisPage.tsx` | Lista, filtros, CRUD, skeleton, 401/403 |
| `pages/CapexMyCostCentersPage.tsx` | Vínculos do JWT via `my-responsibilities` |
| `utils/responsibilities.ts` | Labels, vigência, resumo de amarração, filtro org |
| `api/budgetPlanningApi.ts` | Client admin + `fetchMyCapexResponsibilities` |
| `types/budgetPlanning.ts` | Tipos de responsabilidade |
| `index.css` | Cards responsivos, filtros, skeleton, paginação |

Reutiliza `UserDirectoryPicker` (`@delpi/plugin-ui`), catálogo org via `listAdminScopes`, `PageShell` / `SectionCard` / `StateBox`.

---

## 3. Integração com API

Prefixo: `/apps/api-delpi/planejamento-orcamentario`

| UI | Endpoint |
|----|----------|
| Listagem paginada | `GET /admin/budget-responsibilities` |
| Criar | `POST /admin/budget-responsibilities` |
| Editar tipo/vigência | `PUT /admin/budget-responsibilities/{id}` |
| Desativar | `POST …/deactivate` |
| Reativar | `POST …/reactivate` |
| Meus CCs | `GET /capex/my-responsibilities` |

Filtros enviados ao backend: exercício, usuário (`user_sub` do picker), unidade, área, CC, `is_active`, página.  
Filtro **tipo** (`owner`/`collaborator`): aplicado na página atual no client (API 2A.1 não expõe o query param).

Encadeamento cadastro: Unidade → Área → Centro de custo (catálogo). Sem digitação de `user_sub`. Resumo pré-salvar com dados reais. Edição não troca usuário/CC (orientação a desativar + novo vínculo). Confirmação em desativação.

---

## 4. Estados de UI

Loading/skeleton, vazio, erro, acesso negado, sucesso, salvando, validação de vigência, conflito/duplicidade (mensagem API), paginação, usuário sem vínculos, aviso de próxima etapa (sem botão de investimento).

Layout em cards (evita tabela horizontal excessiva); CSS responsivo.

---

## 5. Testes

```bash
docker run --rm -v "$PWD/plugins:/plugins" -w /plugins/planejamento-orcamentario node:20-alpine \
  sh -c 'npm run lint && npm run typecheck && npm test && npm run build'
```

| Suite | Cobertura |
|-------|-----------|
| `AdminResponsaveisPage.test.tsx` | listagem, filtros, user picker, create+resumo, duplicidade, vigência inválida, edit, deactivate/reactivate, 401/403, acesso negado, vazio, skeleton |
| `CapexMyCostCentersPage.test.tsx` | vários CCs, sem vínculos, 401/403, loading |
| `responsibilities.test.ts` | resumo, vigência, encadeamento CC |
| `routing.responsaveis.test.ts` | rotas admin/capex |

**34 passed** (suite completa do plugin). Lint: 0 errors (warnings `set-state-in-effect` pré-existentes + novas páginas no mesmo padrão).

---

## 6. Build e smoke técnico

| Item | Resultado |
|------|-----------|
| `tsc` / Vite build | OK — `dist/assets/remoteEntry.js` |
| Container MFE | rebuild via `up-dev-sequential.sh --fase mfe --build planejamento-orcamentario` |
| `remoteEntry.js` HTTP | **200** `application/javascript` |
| Bundle App | strings `admin/responsaveis`, `Responsáveis por Centro`, `Meus centros de custo`, `my-responsibilities` |
| Shell SPA | `/admin/responsaveis` e `/capex` → HTTP **200** |
| API sem auth | `my-responsibilities` / `admin/budget-responsibilities` → **401** (esperado) |
| Smoke autenticado telas | **BLOCKED** (token/manifesto — Fase 1.1) |

---

## 7. Pendências

1. Homologação autenticada no portal (JWT + manifesto registrado).
2. Query param `responsibility_type` no backend para filtro server-side de tipo.
3. Fase seguinte: cadastro de investimentos CAPEX consumindo o guard.
4. Permissões `.capex.*` no manifesto quando o módulo for expandido.

---

## 8. Arquivos principais (frontend)

**Criados / estendidos nesta fase**

- `plugins/planejamento-orcamentario/src/pages/admin/AdminResponsaveisPage.tsx` (+ `.test.tsx`)
- `plugins/planejamento-orcamentario/src/pages/CapexMyCostCentersPage.tsx` (+ `.test.tsx`)
- `plugins/planejamento-orcamentario/src/utils/responsibilities.ts` (+ `.test.ts`)
- `plugins/planejamento-orcamentario/src/utils/routing.responsaveis.test.ts`
- `docs/12-roadmap-e-evolucao/planejamento-orcamentario/16-fase-2a2-responsabilidades-frontend.md`

**Alterados**

- `budgetPlanningApi.ts`, `types/budgetPlanning.ts`, `App.tsx`, `utils/routing.ts`
- `AdminHomePage.tsx`, `HomePage.tsx`, `index.css`
