# E11.S6 — Correção UX pós-deploy (evidência PO) — Estoque de Segurança

**Data:** 2026-10-24 · **Executor:** Cursor · **Owner:** `plugins/supplies` · **Tipo:** correção pós-deploy orientada por evidência visual

## Contexto

Capturas reais de produção (`/apps/supplies/safety-stock`) do Product Owner mostraram cinco problemas de experiência: sigla técnica `ESTSEG` na interface, `Filial all` na coluna Filial, cabeçalhos sem Ajuda contextual, toggles booleanos com «Incluir» duplicado/desalinhados e status com leitura comprometida na borda direita da tabela. Escopo autorizado: apenas correções de UX/terminologia/Ajuda — sem alterar cálculos, contratos, regras de estoque, manifest ou backend.

## Verificação de contrato (branch = `all`)

Investigado MFE → `supplies-api` → `api-delpi` antes de traduzir o rótulo:

- `materials_base_cte` (`safety_stock_sql.py`) produz **uma linha por produto** (SB1), com `BZ_ESTSEG = SUM` via `OUTER APPLY` sobre as filiais do escopo e saldos agregados pelo `stock_agg_cte` (`branch_filter_and` — `all` = sem predicado).
- `_map_item_row(row, branch)` grava o **escopo da consulta** no campo `branch` da linha.
- Conclusão: sob `branch=all`, cada linha é um **recorte consolidado legítimo** — os valores já agregam as filiais; não há identidade de filial perdida nem linha duplicada por filial. **Sem `EXECUTION_DRIFT`.**
- O detalhe continua exigindo filial concreta: `onOpenDetail` recusa `all` (comportamento contratual preservado — linha consolidada não abre ficha).
- Correção: `formatSuppliesUnitName` (formatador canônico já existente em `suppliesUnits.ts`) passa a traduzir o escopo `all` → **«Todas as Filiais»**, cobrindo tabela, select, modal e qualquer consumidor atual/futuro. Nenhum mapeamento duplicado criado; valores técnicos (`all`, `01`, `02`) intactos em URL/API.

## Correções aplicadas

### Terminologia (AC-01/02)

Removido `ESTSEG` de todos os textos visíveis: descrição da página, indicadores hero, coluna `Estoque de Segurança`, rótulo do detalhe, projeção, toggles (`Incluir materiais bloqueados` / `Incluir materiais sem estoque de segurança`), `SP_HELP`, Manual e FAQ. O **glossário** mantém a entrada `ESTSEG` como referência do campo Protheus (documentação, não UX da página). Status PT-BR completos já existiam em `SAFETY_STOCK_STATUS_LABELS` e foram preservados.

### Cabeçalhos com Ajuda (AC-06/07/08/09)

- Novo `safetyStockColumnHelp.ts` mapeia cada coluna → `SP_HELP` (padrão idêntico a `purchaseOrdersColumnHelp`).
- `DataTableColumn.headerHint` do kit (`HelpTooltip` wrap) aplicado às 11 colunas + coluna de ações (`Detalhes` + `safetyStockColActions`).
- Textos conferidos contra o contrato: nenhum redefine cálculo — apontam que classificação/déficit/saldos vêm do servidor.
- Ordenação intocada: `headerHint` é propriedade do kit, renderizada dentro do sort button sem interceptar clique; `onSortChange`/allowlist inalterados. Teclado: foco no cabeçalho abre o tooltip (focus bubble); Escape fecha.

### Filtros booleanos (AC-10/11)

Causa raiz: `FilterCheckboxField` compõe `FieldLabel(label)` + `NativeCheckboxControl(defaultCheckboxLabel="Incluir")` — duas linhas com «Incluir» repetido. Composição corrigida para `SuppliesFilterCheckbox` (novo wrapper em `suppliesUi.ts` sobre `NativeCheckboxControl` com `hintPlacement="tooltip"`): **um único rótulo** ao lado da caixa (`Incluir materiais bloqueados` / `Incluir materiais sem estoque de segurança`), explicação via tooltip no próprio rótulo, acessível por teclado (foco no checkbox abre a Ajuda). Célula `sp-field sp-field--filter-checkbox` preserva o slot da grade compartilhada. Valores, defaults, URL e semântica de filtro inalterados.

### Tabela (AC-12/13)

- `sp-safety-stock__col-status` na coluna Status: `min-width: 12.5rem` + badge `white-space: nowrap` — rótulo nunca corta/quebra.
- Região de scroll horizontal já existente (`sp-list-table-region`, `role=region`, focável) preservada — scroll continua restrito à tabela.
- CSS novo isolado sob `.dashboard-supplies-portal .sp-safety-stock*` — zero seletor global, zero alteração no kit.

## Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `features/safety-stock/content.ts` | Terminologia completa + `colDetails` |
| `features/safety-stock/safetyStockColumnHelp.ts` | **Novo** — mapa coluna → `SP_HELP` |
| `features/safety-stock/SafetyStockListTable.tsx` | `headerHint` ×12, header `Detalhes`, classe da coluna Status |
| `features/safety-stock/SafetyStockFilters.tsx` | Toggles → `SuppliesFilterCheckbox` single-label |
| `app/suppliesUi.ts` | Wrapper `SuppliesFilterCheckbox` (`NativeCheckboxControl` + hint tooltip) |
| `app/suppliesUnits.ts` | `formatSuppliesUnitName("all")` → «Todas as Filiais» |
| `shims/plugin-ui.d.ts` | Declaração `NativeCheckboxControl` (tsc do MFE) |
| `content/helpTooltips.ts` | ESTSEG removido; 7 novas chaves `safetyStockCol*` |
| `content/userManualContent.ts` | Manual/FAQ sincronizados sem a sigla |
| `index.css` | Bloco isolado: alinhamento dos toggles + coluna Status |
| `SafetyStock.structural.test.ts` | +2 testes (Ajuda nos cabeçalhos; veto ESTSEG); toggle atualizado |
| `app/suppliesUnits.test.ts` | +1 teste (`all` → «Todas as Filiais», valor técnico intacto) |

## Evidências

- **Testes MFE:** 433 pass (era 430; +3). **TypeScript:** PASS. **Build Vite:** PASS.
- **Lint:** `LINT_E11 = PASS` (escopo safety-stock zerado); baseline global 10 erros/22 warnings inalterada — `LINT_DELTA = 0`.
- **`git diff --check`:** limpo.
- **Busca residual:** `ESTSEG` resta apenas no glossário (intencional) e nos testes de veto; `Filial all` eliminado.
- **Contratos:** zero mudança em API, DTO, parâmetros, permissões, manifest, produtor, TOTVS. `SAFETY_STOCK_SORT_FIELDS`/sort/paginação/URL inalterados.
- **Visual autenticado:** `INCONCLUSIVE` — sem sessão real nesta execução; validação visual do PO permanece pendente (não fecha o gate).

## Pós-condições e gate

- `POSTCONDITION`: UI sem `ESTSEG`; `all` exibido como «Todas as Filiais»; 12 cabeçalhos com Ajuda via kit; toggles single-label; Status sem corte; contrato e regras intactos.
- `GATE-FEATURE E11`: permanece **INCONCLUSIVE** — depende da jornada autenticada + QA visual do PO (esta correção é de UX, não prova o gate).
- Deploy canônico do MFE `supplies` executado após push (ver relatório de execução).
