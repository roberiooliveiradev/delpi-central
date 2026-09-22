import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(dir, relativePath), "utf8");
}

describe("Helpdesk list UX structural", () => {
  it("lista não monta FiltersRow; usa builder, SegmentToggle e Pagination do kit", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).not.toContain("HelpdeskFiltersRow");
    expect(page).toContain("TicketListFilterBuilder");
    expect(page).toContain("HelpdeskSegmentToggle");
    expect(page).toContain("TicketListCards");
    expect(page).toContain("HelpdeskListPaginationFooter");
    expect(page).not.toContain("HelpdeskCompactPagination");
    expect(page).not.toContain("HelpdeskTablePageSizeSelect");
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

  it("paginação usa kit + HintAction no rodapé (sem ícones ? do HelpTooltip)", () => {
    const pagination = read("../components/Pagination.tsx");
    expect(pagination).toContain("createDashboardPaginationKit");
    expect(pagination).not.toContain("hints:");
    expect(pagination).toContain("HintAction");
    expect(pagination).toContain("HelpdeskListPaginationFooter");
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain('from "../components/Pagination"');
    expect(ui).not.toContain("createCompactPagination");
    const css = read("../index.css");
    expect(css).toContain(".helpdesk-list-pagination");
    expect(css).toContain(".helpdesk-list-pagination__nav");
    expect(css).toMatch(
      /\.helpdesk-list-pagination[\s\S]*?pagination__action-help[\s\S]*?display:\s*none/,
    );
  });

  it("Enviar da resposta usa ActionButton primary como a abertura (não IconButton)", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toMatch(/align="end"[\s\S]*?Ajuda: Enviar resposta[\s\S]*?variant="primary"/);
    expect(page).toContain('aria-label={saving ? "Enviando" : "Enviar resposta"}');
    expect(page).toContain("{saving ? \"Enviando…\" : \"Enviar\"}");
    const replyBlock = page.slice(page.indexOf("label=\"Responder\""));
    expect(replyBlock).toContain("ActionButton");
    expect(replyBlock).not.toContain("HelpdeskIconButton");
  });

  it("ciclo do solicitante: aviso + CTA glpiTicketFormUrl sem inventar approve na HLAPI", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("solicitanteLifecycleCue");
    expect(page).toContain("glpiTicketFormUrl");
    expect(page).toContain("helpdesk-lifecycle-cue");
    expect(page).not.toMatch(/add_close|add_reopen|TicketSatisfaction/);
    const links = read("../presentation/glpiPublicLinks.ts");
    expect(links).toContain("helpdesk.centraldelpi.com.br");
    expect(links).toContain("ticket.form.php");
  });

  it("resposta e descrição têm help próprio + Anexar ao lado de Enviar", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("hint={helpTooltips.createUi.attach}");
    expect(page).toContain("hint={helpTooltips.detailUi.reply}");
    expect(page).toContain("hint={helpTooltips.detailUi.attach}");
    expect(page).toContain("HelpdeskAttachButton");
    expect(page).toContain("openAttachPicker");
    const replyBlock = page.slice(page.indexOf('label="Responder"'));
    expect(replyBlock).not.toContain("hint={helpTooltips.detail}");
    expect(replyBlock).toContain("HelpdeskAttachButton");
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("HelpdeskAttachButton");
    expect(ui).toContain('ariaLabel="Ajuda: Anexar arquivo"');
    expect(ui).toMatch(/Paperclip[\s\S]*Anexar/);
  });
});
