/** MYREQ-HELPDESK-PLUGIN-UI-CROSS-MFE-UX-IMPLEMENTATION-HML-01 —
 * regressão estrutural da paridade de listagem: as duas páginas
 * (Minhas / Fila) compõem o MESMO shell sobre componentes do kit
 * Plugin UI — sem popover/DataTable local, com URL state,
 * ordenação consciente da fonte, cards e preferências isoladas. */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const mine = readFileSync(resolve(dir, "MinePage.tsx"), "utf-8");
const queue = readFileSync(resolve(dir, "WorkQueuePage.tsx"), "utf-8");
const shell = readFileSync(
  resolve(dir, "../components/RequestListShell.tsx"),
  "utf-8",
);
const urlHook = readFileSync(
  resolve(dir, "../hooks/useRequestListUrlState.ts"),
  "utf-8",
);
const sortDomain = readFileSync(
  resolve(dir, "../domain/requestListSort.ts"),
  "utf-8",
);
const mrUi = readFileSync(resolve(dir, "../ui/mrUi.tsx"), "utf-8");
const dataTableUi = readFileSync(
  resolve(dir, "../ui/dataTableUi.tsx"),
  "utf-8",
);

describe("Shell compartilhado — componentes do kit, não locais", () => {
  it("compõe hero, chips e a seção DataTable do kit", () => {
    for (const token of [
      "MyRequestsPageHero",
      "MyRequestsScopeChipBar",
      "MyRequestsDataTableSection",
      "MyRequestsListToolbarPopover",
      "MyRequestsFilterRulesBuilder",
      "MyRequestsSortLevelsBuilder",
    ]) {
      expect(shell).toContain(token);
    }
  });

  it("usa a seção bound do MFE (createDashboardDataTableKit) — nunca DataTable cru", () => {
    expect(shell).toContain('from "../ui/dataTableUi"');
    expect(shell).not.toMatch(/<DataTable[\s>]/);
    expect(dataTableUi).toContain("createDashboardDataTableKit");
  });

  it("popovers vêm do binding compartilhado — sem portal/popover local", () => {
    expect(shell).not.toContain("AnchoredPanelPortal");
    expect(shell).not.toContain("document.body");
    expect(shell).not.toMatch(/createPortal/);
    /* o binding passa o escopo do portal do MFE */
    expect(mrUi).toContain('portalScopeClassName: MR_PORTAL_SCOPE');
    expect(mrUi).toContain('"dashboard-my-requests"');
  });

  it("busca com debounce 300ms preservada e page reset em mudança", () => {
    expect(shell).toContain("REQUEST_LIST_SEARCH_DEBOUNCE_MS");
    expect(shell).toContain("window.setTimeout");
  });
});

describe("Hero × grade — controles dentro do hero, sem card redundante", () => {
  it("toolbar da seção renderiza no body do hero via portal do kit", () => {
    expect(shell).toContain("toolbarPortalTarget");
    expect(shell).toContain("setToolbarHost");
    expect(shell).toContain("delpi-ui-list-toolbar-host");
    expect(shell).toContain('toolbarLayout="hero"');
    /* mesma instância — nunca controles duplicados na página */
    expect(mrUi).not.toContain("TableColumnVisibilityMenu(");
  });

  it("grade embedded logo após o hero — sem card externo duplicado", () => {
    expect(shell).toContain("embedded");
    /* chips migram para a faixa do hero (toolbarLeading), não toolbarFilters */
    expect(shell).toContain("toolbarLeading");
    expect(shell).not.toContain("toolbarFilters");
  });

  it("caminho clicável acima do hero (PagePath do kit)", () => {
    expect(shell).toContain("MyRequestsPagePath");
    expect(shell).toContain('label: "Início"');
    expect(mrUi).toContain("createDashboardPagePath");
  });

  it("só colunas do contrato ganham affordance de sort", () => {
    expect(shell).toContain("sortable: true");
    expect(shell).toContain("columnSortMap[column.key]");
  });
});

describe("Header-sort — aplicação atômica, sem closure sobre estado antigo", () => {
  it("clique aplica o novo nível por extenso (regressão UX-V2-HEADER-01)", () => {
    expect(shell).toContain("sort.onApply([{ field, direction }])");
    /* proibido o padrão setState + apply no mesmo tick */
    expect(shell).not.toMatch(
      /sort\.onChange\(\[[^\]]*\]\);\s*\n?\s*sort\.onApply\(\)/,
    );
  });

  it("direção segue o estado aplicado + convenção *_at desc / texto asc", () => {
    expect(shell).toContain("sortKey === columnKey");
    expect(shell).toContain("headerSortDirection");
    expect(sortDomain).toContain('field.endsWith("_at")');
  });

  it("applySort nas páginas recebe os níveis explicitamente", () => {
    expect(mine).toMatch(/applySort[\s\S]{0,200}\(levels: DashboardSortLevel\[\]\)/);
    expect(mine).toContain("patchFilters({ sort: serializeListSortLevels(levels), page: 1 })");
    expect(queue).toMatch(/applySort[\s\S]{0,200}\(levels: DashboardSortLevel\[\]\)/);
    expect(queue).toContain("patchFilters({ sort: serializeListSortLevels(levels), page: 1 })");
  });
});

describe("MinePage — merge honesto e contratos multi-fonte", () => {
  it("usa o shell e o estado de URL (não useState solto para filtros)", () => {
    expect(mine).toContain("useRequestListUrlState");
    expect(mine).not.toMatch(
      /useState<RequestListFiltersState>/,
    );
  });

  it("mantém janela de merge, direction-aware e include PRC por tipo", () => {
    expect(mine).toContain("MERGE_WINDOW_MAX");
    expect(mine).toContain("mergeUnifiedRows(reqRows, prcRows, primary.direction)");
    expect(mine).toContain("PRC_TYPE_CODE");
    expect(mine).toContain("listMyPrcRequests");
    expect(mine).toContain("sortBy:");
    expect(mine).toContain("sortDir:");
  });

  it("propaga sort serializado ao requests-api", () => {
    expect(mine).toContain("sort: requestsSort");
    expect(mine).toContain("serializeListSortLevels(appliedLevels)");
  });

  it("catálogo de ordenação muda com a fonte efetiva", () => {
    expect(sortDomain).toContain("MERGED_SORT_FIELDS");
    expect(sortDomain).toContain("REQUESTS_SORT_FIELDS");
    expect(sortDomain).toContain("PRC_SORT_FIELDS");
    expect(mine).toContain("sortCatalogForSource");
  });

  it("preferências de coluna/layout isoladas por página", () => {
    expect(mine).toContain('"my-requests.mine.columns.v1"');
    expect(mine).toContain('"my-requests.mine.view-layout.v1"');
    expect(queue).toContain('"my-requests.work-queue.columns.v1"');
    expect(queue).toContain('"my-requests.work-queue.view-layout.v1"');
  });
});

describe("WorkQueuePage — contrato de atendimento preservado", () => {
  it("mantém mineScope, completed_by e solicitante", () => {
    expect(queue).toContain("mineScope");
    expect(urlHook).toContain("mine_scope");
    expect(queue).toContain("completed_by");
    expect(queue).toContain("requester");
    expect(queue).toContain('"assigned_to_me"');
    expect(queue).toContain('"completed_by_me"');
  });

  it("ordenção requests-api completa (3 níveis) via contrato sort", () => {
    expect(queue).toContain("REQUESTS_SORT_FIELDS");
    expect(queue).toContain("sort: serializeListSortLevels(appliedLevels)");
  });
});

describe("URL state — deep link e back/forward", () => {
  it("serializa sem defaults e reparsa no popstate", () => {
    expect(urlHook).toContain("URLSearchParams");
    expect(urlHook).toContain("popstate");
    expect(urlHook).toContain("replace: true");
    expect(urlHook).toContain("navigateMyRequestsPath");
  });

  it("itens por página é controle real — estado + contrato page_size", () => {
    expect(urlHook).toContain("page_size");
    expect(mine).toContain("onPageSizeChange");
    expect(queue).toContain("onPageSizeChange");
    expect(mine).toContain("pageSize={filters.pageSize}");
    expect(queue).toContain("pageSize={filters.pageSize}");
  });
});

describe("Cards — href sempre interno ao host", () => {
  it("nunca passa destination vazio ao RecordCard (crash em cards view)", () => {
    // Regression UX-V2-E2E-01: toUnifiedRow.destination = "" para rows
    // requests-api → href="" → isSafeNavigationHref throw → página em branco
    // no modo cards (default mobile). O href resolve a origem no render.
    expect(mine).not.toMatch(/href=\{row\.destination\}/);
    expect(mine).toContain('row.source === "engineering-prc"');
    expect(queue).toContain("myRequestsPath({ requestId: row.id })");
  });
});
