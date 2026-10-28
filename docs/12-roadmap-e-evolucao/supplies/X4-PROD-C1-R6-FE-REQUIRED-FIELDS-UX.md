# X4.PROD-C1.R6-FE — REQUIRED SUPPLIER FIELDS UX

Camada de experiência dos campos obrigatórios no cadastro de fornecedores
(`/apps/supplies/suppliers/new`), complementando a validação canônica
entregue em R6 (`12dd554eb2`).

- **Owner:** `plugins/supplies` — nenhum backend alterado.
- **Base:** R6 backend (`X4-PROD-C1-R6-SUPPLIER-VALIDATION-FIX.md`), RCA R5.

## 1. Campos obrigatórios (fonte contratual)

`SUPPLIER_FIELD_REGISTRY` (specs `post + required`) — 7 campos, mesma fonte
usada pela validação local e espelhada pelo normalizador da api-delpi:

| Campo | TOTVS | Seção |
|---|---|---|
| `supplier_store` | A2_LOJA | Identificação |
| `rohs_indicator` | A2_YROHS | Fiscal/tributário |
| `bacen_country_code` | A2_CODPAIS | Fiscal/tributário |
| `payment_condition_code` | A2_COND | Compras |
| `payment_method_code` | A2_FORMPAG | Compras |
| `accounting_account` | A2_CONTA | Compras |
| `financial_nature_code` | A2_NATUREZ | Compras |

## 2. Comportamento implementado

### 2.1 Identificação permanente

- `*` no rótulo de todos os obrigatórios — inclusive **campos de catálogo**
  (gap do R6: `SupplierCatalogField` não recebia `showRequiredMark`; preload
  select e search combo agora marcam `*`).
- Legenda «* Campos obrigatórios» no topo do formulário.
- `aria-required="true"` no controle via `SupplierFieldShell`.

### 2.2 Validação pré-submit

- `validateCreateDraft` (R6) agrega todos os erros; `handleReview` bloqueia a
  abertura da revisão e o POST — zero chamada HTTP.
- Resumo `role="alert"` com foco, lista **somente** os campos pendentes.

### 2.3 Navegação (novo no R6-FE)

- Cada item do resumo é um botão (`sp-supplier-create__validation-link`,
  `aria-label="Ir para o campo: <rótulo>"`) que:
  1. expande a seção que contém o campo (`supplierCreateFieldSection`);
  2. rola até a âncora estável `sp-supplier-field-anchor-<key>`;
  3. foca o primeiro controle focável do campo.
- `SupplierFieldShell` aplica `aria-invalid`, `aria-describedby` →
  `<p id>…</p>` de erro e `aria-required` por wiring imperativo — o kit
  federado `@delpi/plugin-ui` não encaminha `aria-*` aos controles nativos.

### 2.4 Seções com erro (novo no R6-FE)

- `SuppliesSectionCard` agora `collapsible` (abertas por padrão — o remote
  `plugin-ui` em produção já suporta `collapsible`/`open`/`onOpenChange`).
- Seção com pendências: badge «N pendência(s)» no cabeçalho + expansão
  automática em `applyFieldErrors`.

### 2.5 Erros do backend

- 422 estruturado: `err.fields` → erro por campo + resumo (herdado do R6).
- `PROTHEUS_SUPPLIER_WRITE_REJECTED` sem campos: mensagem segura genérica —
  nenhum campo inventado.
- Auth de integração: mensagem dedicada; indeterminado: sem sugestão de reenvio.

## 3. Compatibilidade

- **POST:** todos os 7 obrigatórios validados. **PUT:** inalterado — sem
  nenhuma obrigatoriedade nova em edição parcial.
- Três modos de entrada preservados (CNPJ assistido, busca por razão social,
  manual): validação roda sobre o `draft` final, independente da origem;
  sugestões externas não contam como preenchimento até o usuário aplicá-las.
- Catálogos canônicos reutilizados; zero auto-seleção; zeros à esquerda
  preservados (strings numéricas).

## 4. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `src/features/suppliers/query.ts` | `supplierFieldAnchorId`, `supplierCreateFieldSection` |
| `src/features/suppliers/SupplierFormFields.tsx` | `SupplierFieldShell` (âncora + ARIA + erro), `showRequiredMark` nos catálogos |
| `src/features/suppliers/SupplierCreatePage.tsx` | resumo navegável, seções colapsáveis + badge + auto-expansão |
| `src/features/suppliers/content.ts` | `validationGoToField`, `validationSectionError{One,Many}` |
| `src/shims/plugin-ui.d.ts` | props de colapso do SectionCard |
| `src/index.css` | link do resumo, badge de seção, ícone ⚠ no erro |
| `src/features/suppliers/suppliers.test.ts` | helpers + inventário de obrigatórios |
| `src/features/suppliers/creation/creation.structural.test.ts` | cobertura estrutural R6-FE |
| `src/content/helpTooltips.ts`, `src/content/userManualContent.ts` | Help sync |

## 5. Testes

- `vitest`: **522 pass (51 arquivos)** — helpers, inventário dos 7
  obrigatórios, seção por campo, estruturais de navegação/ARIA.
- `tsc --noEmit` e `tsc -b && vite build`: limpos.
- `eslint`: 0 erros (3 warnings pré-existentes em arquivos não tocados).

## 6. Residuais

- Smoke visual autenticado: fora do escopo desta execução headless —
  `AUTHENTICATED_SMOKE=INCONCLUSIVE`.
- `aria-*` via wiring imperativo é contido ao `SupplierFieldShell`; quando o
  kit expuser `invalid`/`ariaDescribedBy` nativamente, migrar para props.
