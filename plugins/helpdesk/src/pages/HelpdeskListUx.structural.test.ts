import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(dir, relativePath), "utf8");
}

describe("Helpdesk list UX structural", () => {
  it("lista usa PageHero, busca compacta, chips e popovers (sem drawer)", () => {
    const page = read("HelpdeskPage.tsx");
    const ui = read("../ui/helpdeskUi.tsx");
    expect(page).not.toContain("HelpdeskFiltersRow");
    expect(page).toContain("HelpdeskPageHero");
    expect(page).toContain("HelpdeskScopeChipBar");
    expect(page).toContain("helpdesk-list-primary-bar");
    expect(page).toContain("TicketListFilterPopover");
    expect(page).toContain("TicketListSortPopover");
    expect(page).toContain("TicketListCards");
    expect(page).toContain("HelpdeskListPaginationFooter");
    expect(page).toContain("shouldForceTicketCards");
    expect(page).toContain("TICKET_STATUS_FILTERS");
    expect(page).not.toContain("HelpdeskHostDrawer");
    expect(page).not.toContain("HelpdeskFilterBarShell");
    expect(page).not.toContain("HelpdeskCompactPagination");
    expect(page).not.toContain("HelpdeskTablePageSizeSelect");
    expect(page).toContain("HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY");
    expect(page).toContain("usePersistedViewLayout");
    expect(ui).toContain("createDashboardPageHero");
    expect(ui).toContain("createDashboardScopeChipBar");
  });

  it("CTA Abrir chamado na listagem usa ActionButton com texto (não só ícone +)", () => {
    const page = read("HelpdeskPage.tsx");
    const marker = 'ariaLabel="Ajuda: Abrir chamado"';
    const start = page.indexOf(marker);
    expect(start).toBeGreaterThan(-1);
    const openBlock = page.slice(start, start + 450);
    expect(openBlock).toContain('className="helpdesk-open-ticket"');
    expect(openBlock).toContain('variant="primary"');
    expect(openBlock).toContain("Abrir chamado");
    expect(openBlock).toContain("<Plus");
    expect(openBlock).not.toContain("HelpdeskIconButton");
    const css = read("../index.css");
    expect(css).toContain(".helpdesk-open-ticket");
    expect(css).toContain(".helpdesk-list-shell");
    expect(css).toContain(".helpdesk-anchored-popover");
  });

  it("cards usam DataCardsGrid + RecordCard com href interno e meta responsiva", () => {
    const cards = read("TicketListCards.tsx");
    expect(cards).toContain("HelpdeskDataCardsGrid");
    expect(cards).toContain("HelpdeskRecordCard");
    expect(cards).toContain("ticketDetailPath");
    expect(cards).toContain("relativeTimeLabel");
    expect(cards).toContain("showRequester");
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

  it("ao exigir vínculo GLPI, inicia autorização automaticamente (com fallback de botão)", () => {
    const page = read("HelpdeskPage.tsx");
    expect(page).toContain("shouldAutoStartGlpiLink");
    expect(page).toContain("startGlpiAuthorization");
    expect(page).toContain("markGlpiAutoLinkAttempted");
    expect(page).toContain("clearGlpiAutoLinkAttempt");
    expect(page).toContain('view !== "link"');
    expect(page).toContain("Autorizar no helpdesk");
    const gate = read("../presentation/glpiAutoLink.ts");
    expect(gate).toContain("HELPDESK_GLPI_AUTO_LINK_KEY");
  });

  it("atribuição: create usa picker; detalhe colapsa em popover gated por can_assign", () => {
    const page = read("HelpdeskPage.tsx");
    const picker = read("../components/HelpdeskAssigneePicker.tsx");
    const assignPopover = read("HelpdeskAssignPopover.tsx");
    expect(page).toContain("getSessionCapabilities");
    expect(page).toContain("HelpdeskAssigneePicker");
    expect(page).toContain("HelpdeskAssignPopover");
    expect(page).toContain("setTicketAssignee");
    expect(page).toContain("canAssign");
    expect(page).toContain("ticket.can_assign");
    expect(page).toContain("helpTooltips.createUi.assignee");
    expect(page).toContain("assignee_id: canAssign === true && assignee?.id ? Number(assignee.id) : undefined");
    expect(page).toContain("canAssign !== true");
    expect(page).toContain("assigneeFromCreateDraft");
    expect(page).not.toMatch(/canAssign \? \([\s\S]*HelpdeskAssigneePicker[\s\S]*HelpdeskSelect/);
    expect(assignPopover).toContain("HelpdeskAssigneePicker");
    expect(assignPopover).toContain("helpdesk-assign-summary");
    expect(assignPopover).toContain("aria-expanded");
    const detailSlice = page.slice(page.indexOf("HelpdeskAssignPopover"));
    expect(detailSlice).not.toContain('className="helpdesk-assign-panel"');
    expect(picker).toContain("listUsers");
    expect(picker).toContain('purpose: "assignee"');
    expect(picker).toContain("UserDirectoryPicker");
    expect(picker).toContain("createInitialsAvatar");
    expect(picker).toContain("useDirectoryUserPhotoUrls");
    expect(picker).toContain("directoryUserId");
    expect(picker).toContain("hasPhoto");
    expect(picker).toContain("onSearchingChange");
    expect(picker).not.toContain("FieldLabel");
    expect(picker).toContain("Buscar por nome ou e-mail");
    const api = read("../api/helpdeskApi.ts");
    expect(api).toContain("/users");
    expect(api).toContain("directory_user_id");
    expect(api).toContain("downloadDirectoryUserPhoto");
    expect(api).toContain("/person-profiles/");
    expect(api).toContain("/session/capabilities");
    expect(api).toContain("/assignee");
    expect(api).toContain("email?: string");
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("createDashboardLoadingActivityCard");
    expect(ui).toContain("HelpdeskLoadingCard");
    expect(ui).not.toContain("createDashboardScreenLoading");
    expect(page).toContain("HelpdeskLoadingCard");
    expect(page).toContain("Carregando chamado");
  });

  it("compose usa ConversationFileDropLayer do kit (sem onDrop ad hoc)", () => {
    const ui = read("../ui/helpdeskUi.tsx");
    expect(ui).toContain("createDashboardConversationFileDropLayer");
    expect(ui).toContain("HelpdeskConversationFileDrop");
    expect(ui).toContain("HELPDESK_COMPOSE_DROP_OVERLAY");
    expect(ui).toContain("Solte o arquivo para anexar");
    expect(ui).toContain("overlayLabel={HELPDESK_COMPOSE_DROP_OVERLAY}");
    expect(ui).toMatch(/accept=\{accept\}/);
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

  it("filtros e ordenação usam popover contextual (não HostContainedDrawer)", () => {
    const filter = read("TicketListFilterPopover.tsx");
    const sort = read("TicketListSortPopover.tsx");
    const assign = read("HelpdeskAssignPopover.tsx");
    const page = read("HelpdeskPage.tsx");
    expect(filter).toContain('role="dialog"');
    expect(filter).toContain("aria-expanded");
    expect(filter).toContain("TicketListFilterBuilder");
    expect(filter).toContain("Escape");
    expect(filter).toContain("useClickOutside");
    expect(filter).not.toContain("onBeforeOpen");
    expect(sort).toContain('role="dialog"');
    expect(sort).toContain("TicketListSortBuilder");
    expect(sort).toContain("useClickOutside");
    expect(sort).not.toContain("onBeforeOpen");
    expect(assign).toContain("useClickOutside");
    expect(page).not.toContain("onBeforeOpen");
    expect(page).toContain("setBuilderGroup(ticketListViewModelFromFilters(filters).filterRoot)");
    expect(page).toContain("setSortDraft(parseTicketSortLevels(filters.sort))");
    expect(page).not.toContain("HelpdeskHostDrawer");
    expect(filter).not.toContain("Drawer");
    expect(sort).not.toContain("Drawer");
  });
});
