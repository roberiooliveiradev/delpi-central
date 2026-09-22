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

  it("ciclo do solicitante: ações nativas H10 + validação + CTA GLPI residual", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("solicitanteLifecycleCue");
    expect(page).toContain("acceptTicketSolution");
    expect(page).toContain("rejectTicketSolution");
    expect(page).toContain("submitTicketSatisfaction");
    expect(page).toContain("acceptTicketValidation");
    expect(page).toContain("rejectTicketValidation");
    expect(page).toContain("glpiTicketFormUrl");
    expect(page).toContain("helpdesk-lifecycle-cue");
    expect(page).not.toMatch(/add_close|add_reopen/);
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

  it("atribuição: picker no create/detail gated por can_assign + API users/assignee", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("getSessionCapabilities");
    expect(page).toContain("listUsers");
    expect(page).toContain("setTicketAssignee");
    expect(page).toContain("canAssign");
    expect(page).toContain("ticket.can_assign");
    expect(page).toContain("helpdesk-assign-panel");
    expect(page).toContain("helpTooltips.createUi.assignee");
    expect(page).toContain("helpTooltips.detailUi.assignee");
    expect(page).toContain('assignee_id: canAssign && assigneeId ? Number(assigneeId) : undefined');
    const api = read("../api/helpdeskApi.ts");
    expect(api).toContain("/users");
    expect(api).toContain("/session/capabilities");
    expect(api).toContain("/assignee");
  });

  it("compose usa ConversationFileDropLayer do kit (sem onDrop ad hoc)", () => {
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("createDashboardConversationFileDropLayer");
    expect(ui).toContain("HelpdeskConversationFileDrop");
    expect(ui).toContain("HELPDESK_COMPOSE_DROP_OVERLAY");
    expect(ui).toContain("Solte o arquivo para anexar");
    expect(ui).toContain("overlayLabel={HELPDESK_COMPOSE_DROP_OVERLAY}");
    expect(ui).toMatch(/accept=\{accept\}/);
    // Ad-hoc image-only drop removed — kit layer owns DnD.
    expect(ui).not.toMatch(/onDrop=\{onDrop\}/);
    expect(ui).not.toMatch(/onDragOver=\{/);
    expect(ui).not.toMatch(/dataTransfer\?\.files/);
  });

  it("M-23 menção @: create/reply ligam enableMentions + listUsers no campo", () => {
    const page = read("HelpdeskPage.tsx");
    const createBlock = page.slice(
      page.indexOf('label="Descrição"'),
      page.indexOf('label="Categoria"'),
    );
    expect(createBlock).toContain("enableMentions");
    const replyBlock = page.slice(page.indexOf('label="Responder"'));
    expect(replyBlock).toContain("enableMentions");
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("enableMentions");
    expect(ui).toContain("listUsers");
    expect(ui).toContain("onMentionQueryChange");
    expect(ui).toContain("mentionHits");
    expect(ui).not.toContain("MentionComposer");
    expect(page).not.toContain("MentionComposer");
  });
});
