import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("HELPDESK-MFE-UX-001-R3 conversation detail", () => {
  it("separates summary, banners, conversation column and composer", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("helpdesk-detail");
    expect(detail).toContain("helpdesk-ticket-workspace");
    expect(detail).toContain('className="helpdesk-detail__summary"');
    expect(detail).toContain("helpdesk-detail__conversation");
    expect(detail).toContain("helpdesk-detail__conversation-inner");
    expect(detail).not.toContain('title="Conversa"');
    expect(detail).toContain("HelpdeskMessageThread");
    expect(detail).toContain("helpdesk-reply-form");
    expect(detail).toContain("ticketWorkspaceActions");
  });

  it("keeps message ordering, mine alignment and authorSrc from contract only", () => {
    const page = read("HelpdeskPage.tsx");
    const view = read("../presentation/ticketView.ts");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("conversationMessages(ticket, new Date())");
    expect(detail).toContain("mine: message.mine");
    expect(detail).toContain("conversationAuthorSrc(message.mine, myPhotoUrl)");
    expect(detail).not.toMatch(/role\s*===\s*["']support/);
    expect(detail).not.toMatch(/isTechnician|isRequester|participantRole/);
    expect(view).toContain("mine: ticket.requester_mine === true");
    expect(view).toContain("mine: entry.mine === true");
    expect(view).toContain('entry.kind === "followup" || entry.kind === "solution" || entry.kind === "task"');
  });

  it("composer starts compact without fill and keeps attach/send + rich text", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const replyStart = detail.indexOf('actionId="reply"');
    const replyEnd = detail.indexOf('activeAction === "accept_solution"');
    const replyBlock = detail.slice(replyStart, replyEnd > replyStart ? replyEnd : undefined);
    expect(replyBlock).toContain("minHeight={144}");
    expect(replyBlock).not.toMatch(/HelpdeskRichTextField[\s\S]*?\bfill\b/);
    expect(replyBlock).toContain("enableMentions");
    expect(replyBlock).toContain("HelpdeskAttachButton");
    expect(replyBlock).toContain("openAttachPicker");
    expect(replyBlock).toContain("Enviar resposta");
    expect(replyBlock).toContain("helpdesk-reply-form__actions");
    expect(replyBlock).toContain("TicketActionCard");
    expect(detail).toContain("createFollowup");
    expect(detail).toContain('className="helpdesk-reply-form"');
    expect(detail).toContain("useState<TicketWorkspaceActionId | null>(null)");
  });

  it("technician control stays permission-gated; summary always shows técnico", () => {
    const page = read("HelpdeskPage.tsx");
    const assign = read("HelpdeskAssignPopover.tsx");
    const context = read("TicketContextPanel.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("TicketContextPanel");
    expect(context).toContain("canAssign={ticket.can_assign === true}");
    expect(detail).toContain("setTicketAssignee");
    expect(assign).toContain("canAssign");
    expect(assign).toMatch(/canAssign \? \(/);
    expect(assign).toContain("HelpdeskAssigneePicker");
  });

  it("closed satisfaction uses radiogroup 1–5 and same submit contract", () => {
    const page = read("HelpdeskPage.tsx");
    const lifecycle = read("../presentation/solicitanteLifecycle.ts");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("submitTicketSatisfaction");
    expect(detail).toContain("{ satisfaction: satisfactionScore, comment: satisfactionComment }");
    expect(detail).toContain('role="radiogroup"');
    expect(detail).toContain('aria-label="Nota de 1 a 5"');
    expect(detail).toContain('type="radio"');
    expect(detail).toContain("helpdesk-satisfaction");
    expect(detail).toContain("Adicionar comentário");
    expect(detail).toContain("satisfactionCommentOpen");
    expect(detail).not.toMatch(/showSatisfactionForm[\s\S]*?<select/);
    expect(lifecycle).toContain("showSatisfactionForm: true");
    expect(lifecycle).toContain("Chamado encerrado");
  });

  it("does not invent response capability on closed tickets", () => {
    const page = read("HelpdeskPage.tsx");
    const actions = read("../presentation/ticketWorkspaceActions.ts");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(actions).toContain("can_followup !== false");
    expect(detail).toContain("ticketWorkspaceActions(ticket)");
    expect(detail).not.toMatch(/status_id\s*===\s*6[\s\S]{0,80}can_followup/);
    expect(detail).not.toMatch(/statusId\s*===\s*6[\s\S]{0,80}reply/);
  });
});

describe("HELPDESK-MFE-UX-001-R4 conversation density", () => {
  it("uses compact summary rail with all metadata fields", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("helpdesk-ticket-summary-rail");
    expect(detail).toContain("helpdesk-ticket-summary-rail__lead");
    expect(detail).toContain("ticketRecordFields");
    expect(detail).toContain('"sla_tto"');
    expect(detail).toContain('"sla_ttr"');
    expect(detail).toContain('"created_at"');
    expect(detail).toContain('"updated_at"');
    expect(detail).toContain("HelpdeskStatusBadge");
    expect(detail).not.toContain("HelpdeskRecordCard");
    expect(detail).not.toContain("detailRecordHeading");
  });

  it("removes thread max-width 72rem while keeping bubble bounds", () => {
    const css = read("../index.css");
    expect(css).toContain(".helpdesk-detail__conversation-inner");
    expect(css).toContain("max-width: none");
    expect(css).not.toMatch(
      /\.helpdesk-detail__conversation-inner \{[^}]*max-width:\s*min\(72rem/,
    );
    expect(css).toMatch(
      /\.helpdesk-detail__conversation-inner \.delpi-ui-message-thread__row \{[^}]*max-width:\s*min\(65%,\s*48rem\)/,
    );
    expect(css).toContain(".helpdesk-ticket-summary-rail");
    expect(css).toContain(".helpdesk-reply-form");
    expect(css).toMatch(/\.helpdesk-reply-form[\s\S]*?min-height:\s*9rem/);
    expect(css).toContain(".helpdesk-satisfaction__score");
    expect(css).not.toMatch(/helpdesk-detail__conversation[\s\S]{0,200}100vh\s*-/);
  });

  it("keeps mine alignment and comfortable composer height", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const replyStart = detail.indexOf('actionId="reply"');
    const replyEnd = detail.indexOf('activeAction === "accept_solution"');
    const replyBlock = detail.slice(replyStart, replyEnd > replyStart ? replyEnd : undefined);
    expect(detail).toContain("mine: message.mine");
    expect(replyBlock).toContain("minHeight={144}");
    expect(replyBlock).not.toMatch(/HelpdeskRichTextField[\s\S]*?\bfill\b/);
  });
});

describe("HELPDESK-MFE-UX-001-R5 composer + message media", () => {
  it("reply composer writing area is materially taller than R4 baseline", () => {
    const page = read("HelpdeskPage.tsx");
    const css = read("../index.css");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const replyStart = detail.indexOf('actionId="reply"');
    const replyEnd = detail.indexOf('activeAction === "accept_solution"');
    const replyBlock = detail.slice(replyStart, replyEnd > replyStart ? replyEnd : undefined);
    expect(replyBlock).toContain("minHeight={144}");
    expect(replyBlock).not.toContain("minHeight={72}");
    expect(css).toMatch(/\.helpdesk-reply-form[\s\S]*?min-height:\s*9rem/);
    expect(css).not.toMatch(/\.helpdesk-reply-form[\s\S]*?min-height:\s*4\.5rem/);
    expect(replyBlock).toContain("HelpdeskAttachButton");
    expect(replyBlock).toContain("TicketActionCard");
    expect(replyBlock).toContain("Enviar resposta");
    expect(replyBlock).toContain("enableMentions");
    expect(replyBlock).toContain("Cancelar");
  });

  it("message rich body contains images and wide content inside the bubble", () => {
    const css = read("../index.css");
    expect(css).toMatch(
      /\.delpi-ui-message-thread__body--rich[\s\S]*?overflow-wrap:\s*anywhere/,
    );
    expect(css).toMatch(
      /\.delpi-ui-message-thread__body--rich img[\s\S]*?max-width:\s*100%/,
    );
    expect(css).toMatch(
      /\.delpi-ui-message-thread__body--rich img[\s\S]*?height:\s*auto/,
    );
    expect(css).toMatch(
      /\.delpi-ui-message-thread__bubble[\s\S]*?overflow:\s*hidden/,
    );
    expect(css).toMatch(
      /\.delpi-ui-message-thread__body--rich table[\s\S]*?overflow-x:\s*auto/,
    );
    expect(css).toMatch(
      /\.delpi-ui-message-thread__body--rich pre[\s\S]*?overflow-x:\s*auto/,
    );
  });

  it("does not reopen assignment contract or invent roles", () => {
    const page = read("HelpdeskPage.tsx");
    const context = read("TicketContextPanel.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(context).toContain("canAssign={ticket.can_assign === true}");
    expect(detail).not.toMatch(/isTechnician|participantRole|role\s*===\s*["']support/);
    expect(detail).toContain("submitTicketSatisfaction");
    expect(detail).toContain("{ satisfaction: satisfactionScore, comment: satisfactionComment }");
  });
});

describe("HELPDESK-MFE-UX-002 ticket workspace", () => {
  it("exposes workspace shell with capability-aware action menu", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const css = read("../index.css");
    expect(detail).toContain("helpdesk-ticket-workspace");
    expect(detail).toContain("TicketActionMenu");
    expect(detail).toContain("TicketActionCard");
    expect(detail).toContain("TicketContextPanel");
    expect(detail).toContain("ticketWorkspaceActions");
    expect(detail).toContain("useState<TicketWorkspaceActionId | null>(null)");
    expect(detail).toContain('activeAction === "reply"');
    expect(detail).toContain('activeAction === "attach_file"');
    expect(detail).toContain('activeAction === "create_solution"');
    expect(detail).toContain('activeAction === "create_task"');
    expect(detail).toContain('activeAction === "request_approval"');
    expect(detail).toContain("createTicketSolution");
    expect(detail).toContain("createTicketTask");
    expect(detail).toContain("requestTicketApproval");
    expect(detail).toContain("TicketTimelineFilterPopover");
    expect(detail).toContain("helpTooltips.detailUi.actionMenu");
    expect(detail).toContain("helpTooltips.detailUi.createSolution");
    expect(detail).toContain("helpTooltips.detailUi.createTask");
    expect(detail).toContain("helpTooltips.detailUi.requestApproval");
    expect(css).toContain(".helpdesk-ticket-workspace__body");
    expect(css).toContain("grid-template-columns");
    expect(css).toContain('data-action-variant="task"');
    expect(css).toContain(".helpdesk-action-card");
    const actionMenu = read("TicketActionMenu.tsx");
    expect(actionMenu).toContain("AnchoredPanelPortal");
    expect(actionMenu).toContain('preferredPlacement="top"');
    expect(actionMenu).toContain('portalScopeClassName={HELPDESK_PORTAL_SCOPE}');
    expect(actionMenu).not.toContain("useClickOutside");
  });

  it("wires proven operational actions from BFF capabilities", () => {
    const actions = read("../presentation/ticketWorkspaceActions.ts");
    expect(actions).toContain('"reply"');
    expect(actions).toContain('"attach_file"');
    expect(actions).toContain('"create_solution"');
    expect(actions).toContain('"create_task"');
    expect(actions).toContain('"request_approval"');
    expect(actions).toContain('"accept_solution"');
    expect(actions).toContain('"reject_solution"');
    expect(actions).toContain("can_create_solution");
    expect(actions).toContain("can_create_task");
    expect(actions).toContain("can_request_approval");
    expect(actions).not.toContain('"add_document"');
  });
});
