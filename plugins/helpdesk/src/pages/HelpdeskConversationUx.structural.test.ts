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
    expect(detail).toContain('className="helpdesk-detail"');
    expect(detail).toContain('className="helpdesk-detail__summary"');
    expect(detail).toContain('className="helpdesk-detail__conversation"');
    expect(detail).toContain('className="helpdesk-detail__conversation-inner"');
    expect(detail).not.toContain('title="Conversa"');
    expect(detail).toContain("HelpdeskMessageThread");
    expect(detail).toContain("helpdesk-reply-form");
    expect(detail).toContain("can_followup !== false");
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
    expect(view).toContain('kind === "followup" || entry.kind === "solution"');
  });

  it("composer starts compact without fill and keeps attach/send + rich text", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const replyBlock = detail.slice(detail.indexOf('label="Responder"'));
    expect(replyBlock).toContain("minHeight={72}");
    expect(replyBlock).not.toMatch(/\bfill\b/);
    expect(replyBlock).toContain("enableMentions");
    expect(replyBlock).toContain("HelpdeskAttachButton");
    expect(replyBlock).toContain("openAttachPicker");
    expect(replyBlock).toContain('aria-label={saving ? "Enviando" : "Enviar resposta"}');
    expect(replyBlock).toContain("helpdesk-reply-form__actions");
    expect(detail).toContain("createFollowup");
    expect(detail).toContain('className="helpdesk-reply-form"');
  });

  it("technician control stays permission-gated; summary always shows técnico", () => {
    const page = read("HelpdeskPage.tsx");
    const assign = read("HelpdeskAssignPopover.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("HelpdeskAssignPopover");
    expect(detail).toContain("canAssign={ticket.can_assign === true}");
    expect(detail).toContain('variant="inline"');
    expect(detail).toContain("setTicketAssignee");
    expect(assign).toContain("canAssign");
    expect(assign).toMatch(/canAssign \? \(/);
    expect(assign).toContain("HelpdeskAssigneePicker");
    expect(assign).toContain('variant === "inline"');
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
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("ticket.can_followup !== false");
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
    expect(css).toMatch(/\.helpdesk-reply-form[\s\S]*?min-height:\s*4\.5rem/);
    expect(css).toContain(".helpdesk-satisfaction__score");
    expect(css).not.toMatch(/helpdesk-detail__conversation[\s\S]{0,200}100vh\s*-/);
  });

  it("keeps mine alignment and compact composer unchanged", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const replyBlock = detail.slice(detail.indexOf('label="Responder"'));
    expect(detail).toContain("mine: message.mine");
    expect(replyBlock).toContain("minHeight={72}");
    expect(replyBlock).not.toMatch(/\bfill\b/);
  });
});
