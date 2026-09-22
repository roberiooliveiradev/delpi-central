import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(dir, relativePath), "utf8");
}

describe("Helpdesk list UX structural", () => {
  it("lista não monta FiltersRow; usa builder, SegmentToggle e CompactPagination", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).not.toContain("HelpdeskFiltersRow");
    expect(page).toContain("TicketListFilterBuilder");
    expect(page).toContain("HelpdeskSegmentToggle");
    expect(page).toContain("TicketListCards");
    expect(page).toContain("HelpdeskCompactPagination");
    expect(page).toContain("HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY");
    expect(page).toContain("usePersistedViewLayout");
  });

  it("cards usam DataCardsGrid + RecordCard com href interno", () => {
    const cards = read("TicketListCards.tsx");
    expect(cards).toContain("HelpdeskDataCardsGrid");
    expect(cards).toContain("HelpdeskRecordCard");
    expect(cards).toContain("ticketDetailPath");
    expect(cards).toContain("detailRecordSubtitle");
  });

  it("CSS escuro scoped no host do MFE", () => {
    const css = read("../index.css");
    expect(css).toContain(':root[data-theme="dark"] .dashboard-helpdesk');
    expect(css).toContain("--helpdesk-muted");
    expect(css).not.toContain("#64748b");
  });

  it("lista de regras do builder tem teto de altura com scroll", () => {
    const css = read("../index.css");
    expect(css).toMatch(
      /\.helpdesk-filter-builder__rules[\s\S]*?max-height:\s*min\(12\.5rem,\s*32vh\)/,
    );
    expect(css).toMatch(/\.helpdesk-filter-builder__rules[\s\S]*?overflow-y:\s*auto/);
  });

  it("paginação compacta usa ChevronLeft/Right com aria-label", () => {
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("ChevronLeft");
    expect(ui).toContain("ChevronRight");
    expect(ui).toContain('previousAriaLabel: "Página anterior"');
    expect(ui).toContain('nextAriaLabel: "Próxima página"');
    const css = read("../index.css");
    expect(css).toContain(".helpdesk-pagination__actions");
  });
});
