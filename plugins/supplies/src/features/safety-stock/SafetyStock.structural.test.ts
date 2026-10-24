import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { SAFETY_STOCK_STATUS_LABELS } from "./content";
import { SAFETY_STOCK_SORT_FIELDS } from "./types";

const dir = dirname(fileURLToPath(import.meta.url));

function collectSourceFiles(root: string): string[] {
  const entries = readdirSync(root);
  const files: string[] = [];
  for (const entry of entries) {
    const full = join(root, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      files.push(...collectSourceFiles(full));
      continue;
    }
    if (/\.(ts|tsx)$/.test(entry) && !/\.(test|spec)\.(ts|tsx)$/.test(entry)) {
      files.push(full);
    }
  }
  return files;
}

describe("Safety stock feature (E11.S2/S3)", () => {
  it("App liga SafetyStockPage e remove o placeholder de safety_stock", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/SafetyStockPage/);
    expect(app).toMatch(/view === "safety_stock"/);
    expect(app).not.toMatch(/safety_stock:\s*\{\s*title/);
  });

  it("cliente fala só com supplies-api /safety-stock (3 endpoints, read-only)", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/\/safety-stock\/filters/);
    expect(api).toMatch(/\/safety-stock\/summary/);
    expect(api).toMatch(/\/safety-stock\/items/);
    // E11.S3/S7 — detalhe e fornecedores, somente sob interação (página).
    expect(api).toMatch(/\/details/);
    expect(api).toMatch(/\/suppliers/);
    expect(api).toMatch(/suppliesApiUrl/);
    expect(api).not.toMatch(/api-delpi/);
    expect(api).not.toMatch(/apiDelpiUrl/);
    expect(api).not.toMatch(/httpPost|httpPut|httpPatch|httpDelete/);
  });

  it("feature não acessa api-delpi, legado nem permission por filial", () => {
    for (const file of collectSourceFiles(dir)) {
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(/api-delpi/);
      expect(text).not.toMatch(/apiDelpiUrl/);
      expect(text).not.toMatch(/estoque-seguranca/);
      expect(text).not.toMatch(/supplies\.unit/);
      expect(text).not.toMatch(/authorized_branches/);
    }
  });

  it("página kit-first: hero, filtros, resumo, tabela e estados completos", () => {
    const page = readFileSync(join(dir, "SafetyStockPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("SuppliesPagePath");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("SafetyStockFilters");
    expect(page).toContain("SafetyStockListTable");
    expect(page).toContain("SuppliesEmptyState");
    expect(page).toContain("SuppliesLoadingCard");
    expect(page).toContain("SuppliesStateBanner");
    expect(page).toContain("getSafetyStockFilters");
    expect(page).toContain("getSafetyStockSummary");
    expect(page).toContain("listSafetyStockItems");
    expect(page).toContain("SP_HELP.safetyStock");
    // Estados parciais: canais independentes.
    expect(page).toContain("summaryError");
    expect(page).toContain("itemsError");
    expect(page).toContain("filtersError");
    // branch=all = uma única chamada, sem loop por filial.
    expect(page).not.toMatch(/for .*of .*01.*02/s);
  });

  it("tabela usa kit, sort/paginação server-side e badge de status", () => {
    const table = readFileSync(join(dir, "SafetyStockListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("SuppliesStatusBadge");
    expect(table).toContain("nextServerSort");
    expect(table).toContain("safetyStockRowKey");
    expect(table).toContain("formatQuantity");
    expect(table).not.toMatch(/onSelectRow/);
    // E11.S3 — ação de detalhe por linha (botão acessível + onRowClick).
    expect(table).toMatch(/onRowClick/);
    expect(table).toMatch(/onOpenDetail/);
    expect(table).toMatch(/openActionLabel/);
    expect(table).not.toMatch(/\.sort\(/); // zero ordenação local
  });

  it("filtros usam campos do contrato: branch, status, grupo, UM, busca, toggles", () => {
    const filters = readFileSync(join(dir, "SafetyStockFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesSelectField");
    expect(filters).toContain("SuppliesTextField");
    // Toggle compacto do kit: um único rótulo (sem «Incluir» duplicado).
    expect(filters).toContain("SuppliesFilterCheckbox");
    expect(filters).not.toContain("SuppliesFilterCheckboxField");
    expect(filters).toContain("useCommittedTextFilter");
    expect(filters).toContain("branch");
    expect(filters).toContain("productGroup");
    expect(filters).toContain("includeBlocked");
    expect(filters).toContain("includeWithoutSafetyStock");
  });

  it("todos os cabeçalhos têm Ajuda contextual via headerHint do kit", () => {
    const table = readFileSync(join(dir, "SafetyStockListTable.tsx"), "utf8");
    const help = readFileSync(join(dir, "safetyStockColumnHelp.ts"), "utf8");
    const tooltips = readFileSync(join(dir, "../../content/helpTooltips.ts"), "utf8");
    expect(table).toContain("headerHint: safetyStockColumnHelp(key)");
    expect(table).toContain("headerHint: SP_HELP.safetyStockColActions");
    for (const key of [
      "safetyStockColProduct",
      "safetyStockColDescription",
      "safetyStockColBranch",
      "safetyStockColType",
      "safetyStockColGroup",
      "safetyStockColUnit",
      "safetyStockSafetyStock",
      "safetyStockPrimaryStock",
      "safetyStockWorkInProcess",
      "safetyStockDeficit",
      "safetyStockStatus",
      "safetyStockColActions",
    ]) {
      // Cada chave é referenciada no mapeamento da coluna ou na coluna de ações.
      expect(help + table).toContain(`SP_HELP.${key}`);
      expect(tooltips).toContain(`${key}:`);
    }
  });

  it("nenhum texto visível da feature usa a sigla técnica ESTSEG", () => {
    for (const file of [
      join(dir, "content.ts"),
      join(dir, "../../content/helpTooltips.ts"),
      join(dir, "../../content/userManualContent.ts"),
    ]) {
      const text = readFileSync(file, "utf8");
      expect(text).not.toMatch(/ESTSEG/);
    }
    // Glossário mantém a sigla documentada como campo do Protheus — não é UX da página.
  });

  it("os nove campos de ordenação do contrato são a allowlist", () => {
    expect([...SAFETY_STOCK_SORT_FIELDS].sort()).toEqual(
      [
        "deficit_quantity",
        "primary_stock",
        "product_code",
        "product_description",
        "product_group",
        "safety_stock",
        "status",
        "unit",
        "work_in_process_stock",
      ].sort(),
    );
  });

  it("status canônicos têm rótulo PT-BR (não só cor)", () => {
    for (const [code, label] of Object.entries(SAFETY_STOCK_STATUS_LABELS)) {
      expect(code).toMatch(/safety_stock/);
      expect(label.length).toBeGreaterThan(3);
    }
    expect(Object.keys(SAFETY_STOCK_STATUS_LABELS)).toHaveLength(4);
  });
});

describe("Safety stock item detail (E11.S3/S7 — página própria)", () => {
  it("página de detalhe consome só os dois endpoints BFF com filial concreta", () => {
    const page = readFileSync(join(dir, "SafetyStockDetailPage.tsx"), "utf8");
    expect(page).toContain("getSafetyStockItemDetails");
    expect(page).toContain("getSafetyStockItemSuppliers");
    // Sem prefetch: os fetchers são chamados só dentro da página.
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/items\/\$\{encodeURIComponent/);
    expect(api).toMatch(/params\.set\("branch", target\.branch\)/);
    // Guardas de contrato (residual de envelope E11.S1).
    expect(api).toContain("isSafetyStockItemDetail");
    expect(api).toContain("isSafetyStockSuppliersResponse");
    // Cancelamento por troca de item/filial.
    expect(page).toContain("AbortController");
    expect(page).toContain("controller.abort()");
    // Estados independentes detalhe × fornecedores.
    expect(page).toContain("detailState.status");
    expect(page).toContain("suppliersState.status");
    // Seções do contrato real do produtor.
    for (const section of [
      "open_purchase_orders",
      "open_purchase_requests",
      "open_commitments",
      "stock_projection",
      "monthly_consumption",
      "annual_comparison",
      "purchase_coverage",
    ]) {
      expect(page).toContain(section);
    }
    // Identidade composta do fornecedor.
    expect(page).toContain("supplier_code");
    expect(page).toContain("supplier_store");
    // Sem N+1: cada fetcher é chamado exatamente uma vez por item aberto.
    expect(page.match(/getSafetyStockItemDetails\(target/g)).toHaveLength(1);
    expect(page.match(/getSafetyStockItemSuppliers\(target/g)).toHaveLength(1);
  });

  it("detalhe é página completa — nunca modal/drawer/overlay", () => {
    const page = readFileSync(join(dir, "SafetyStockDetailPage.tsx"), "utf8");
    expect(page).not.toMatch(/SuppliesModal|ModalShell|drawer/i);
    expect(page).toContain("SuppliesPagePath");
    expect(page).toContain("SuppliesPageHero");
    // Voltar para a listagem com o recorte preservado (?from=).
    expect(page).toContain("navigatePluginPath");
    expect(page).toContain('get("from")');
    // Filial concreta obrigatória — `all`/inválido → sem target, sem request.
    expect(page).toMatch(/SAFETY_STOCK_ALL_SCOPE\) return null/);
    expect(page).toContain("invalidBranchTitle");
    // Nenhum componente da feature renderiza o modal de detalhe removido.
    for (const file of collectSourceFiles(dir)) {
      expect(readFileSync(file, "utf8")).not.toContain("SafetyStockDetailModal");
    }
    expect(() =>
      readFileSync(join(dir, "SafetyStockDetailModal.tsx")),
    ).toThrow();
  });

  it("rota canônica do detalhe: safety-stock/{branch}/{code} sem manifest novo", () => {
    const routes = readFileSync(join(dir, "../../app/pluginRoutes.ts"), "utf8");
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(routes).toContain('"safety_stock_detail"');
    expect(routes).toMatch(/safety-stock\\\/\(\[\^\/\]\+\)\\\//);
    expect(routes).toContain("buildSafetyStockDetailPath");
    expect(app).toContain('view === "safety_stock_detail"');
    expect(app).toContain("SafetyStockDetailPage");
  });

  it("listagem navega: filial concreta direto; `all` abre seletor explícito", () => {
    const page = readFileSync(join(dir, "SafetyStockPage.tsx"), "utf8");
    expect(page).toContain("SafetyStockBranchChoiceDialog");
    expect(page).toContain("buildSafetyStockDetailPath");
    expect(page).toContain("navigatePluginPath");
    expect(page).toContain("parseDetailTargetFromSearch"); // redirect legado
    // branch=all abre a escolha — não navega nem consulta detalhe.
    expect(page).toMatch(/SAFETY_STOCK_ALL_SCOPE\)[\s\S]{0,200}setBranchChoiceCode/);
    // A listagem nunca chama os endpoints de detalhe diretamente.
    expect(page).not.toContain("getSafetyStockItemDetails");
    expect(page).not.toContain("getSafetyStockItemSuppliers");
    // O recorte consolidado da lista não é substituído pela filial escolhida.
    expect(page).not.toMatch(/setQuery\([^)]*branch[^)]*branchChoice/);
  });

  it("seletor de filial: sem default, sem fetch de detalhe, com cancelar", () => {
    const dialog = readFileSync(
      join(dir, "SafetyStockBranchChoiceDialog.tsx"),
      "utf8",
    );
    // Nenhum request antes da escolha.
    expect(dialog).not.toContain("getSafetyStockItemDetails");
    expect(dialog).not.toContain("getSafetyStockItemSuppliers");
    // Opções concretas apenas (01/02) — `all` é filtrado fora.
    expect(dialog).toContain("SAFETY_STOCK_ALL_SCOPE");
    // Começa sem escolha (estado chaveado pelo material) e confirma fica
    // desabilitado até selecionar — nunca pré-seleciona 01.
    expect(dialog).toContain("setPicked(null)");
    expect(dialog).toMatch(/picked\?\.key === productCode/);
    expect(dialog).toMatch(/disabled=\{!selected\}/);
    expect(dialog).not.toMatch(/useState[^)]*"0[12]"/);
    expect(dialog).toContain("chooseBranchCancel");
    expect(dialog).toContain("chooseBranchConfirm");
  });

  it("query: detalhe não é serializado na listagem; legado ainda resolve", () => {
    const query = readFileSync(join(dir, "query.ts"), "utf8");
    expect(query).not.toMatch(/params\.set\("item"/);
    expect(query).not.toMatch(/params\.set\("itemBranch"/);
    expect(query).toContain("parseDetailTargetFromSearch");
    // Recusa filial `all` no detalhe.
    expect(query).toMatch(/branch === SAFETY_STOCK_ALL_SCOPE\) return null/);
  });
});
