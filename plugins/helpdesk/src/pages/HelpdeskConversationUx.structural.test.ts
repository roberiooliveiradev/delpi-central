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

  it("satisfaction lives inside the submit_satisfaction action card", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const start = detail.indexOf('{activeAction === "submit_satisfaction"');
    expect(start).toBeGreaterThan(-1);
    const end = detail.indexOf('activeAction === "create_solution" ? (');
    const block = detail.slice(start, end > start ? end : undefined);
    expect(block).toContain('actionId="submit_satisfaction"');
    expect(block).toContain('role="radiogroup"');
    expect(block).toContain("setSatisfactionScore");
    expect(block).toContain("runSatisfaction");
    expect(block).toContain("helpdesk-satisfaction__comment-toggle");
    expect(block).toContain("Enviar avaliação");
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
    expect(detail).toContain('label="Mensagem"');
    expect(detail).toContain('label="Descrição da solução"');
    expect(detail).toContain('label="Descrição da tarefa"');
    expect(detail).toContain('label="Comentário para aprovação (opcional)"');
    expect(detail).not.toContain('label="Responder"');
    expect(detail).not.toContain('label="Solução"');
    expect(detail).not.toContain('label="Tarefa"');
    expect(detail).toContain("helpTooltips.detailUi.actionFields");
    expect(css).toContain(".helpdesk-ticket-workspace__body");
    expect(css).toContain("grid-template-columns");
    expect(css).toContain('data-action-variant="task"');
    expect(css).toContain(".helpdesk-action-card");
    const actionMenu = read("TicketActionMenu.tsx");
    expect(actionMenu).toContain("AnchoredPanelPortal");
    expect(actionMenu).toContain('preferredPlacement="top"');
    expect(actionMenu).toContain('portalScopeClassName={HELPDESK_PORTAL_SCOPE}');
    expect(actionMenu).not.toContain("useClickOutside");
    expect(detail).toContain("TicketTaskActionFields");
    expect(detail).toContain("ticketTaskFormToBody");
    expect(detail).toContain("TicketReplyActionFields");
    expect(detail).toContain("TicketSolutionActionFields");
    expect(detail).toContain("TicketApprovalActionFields");
    expect(detail).toContain("approvalApproverType");
    expect(detail).toContain('approver_type: approvalApproverType');
    expect(detail).toContain("documentTitle");
    expect(detail).toContain("helpTooltips.detailUi.actionFields.attachment.title");
    expect(detail).toContain("document-remove");
    expect(detail).not.toContain('SectionHintLabel\n                                  label="Anexa arquivos');
    const approvalForm = detail.slice(
      detail.indexOf('{activeAction === "request_approval" ? ('),
      detail.indexOf('{activeAction === "attach_file" ? ('),
    );
    expect(approvalForm.match(/label="Aprovador"/g)?.length ?? 0).toBe(1);
    expect(approvalForm).toContain('placeholder="Buscar usuário…"');
    expect(approvalForm).toContain('emptyLabel="Nenhum usuário selecionado"');
    expect(approvalForm).not.toContain("helpdesk-ticket-workspace__field-label");
    const approvalFields = read("TicketApprovalActionFields.tsx");
    expect(approvalFields).toContain('value: "group"');
    expect(approvalFields).toContain("listGroups");
    expect(approvalFields).toContain("Grupo aprovador");
    expect(approvalFields).toContain("Nenhum grupo selecionado");
    expect(approvalFields).toContain("templates.length > 0");
    const taskFields = read("TicketTaskActionFields.tsx");
    expect(taskFields).toContain("Técnico responsável");
    expect(taskFields).toContain("Nenhum técnico selecionado");
    expect(taskFields).toContain("templates.length > 0");
    const replyFields = read("TicketReplyActionFields.tsx");
    expect(replyFields).toContain("templates.length > 0");
    expect(replyFields).toContain("requestTypes.length > 0");
    const api = read("../api/helpdeskApi.ts");
    expect(api).toContain("approver_type");
    expect(api).toContain("approver_id");
    expect(api).toContain("options?: { title?: string }");
    const view = read("../presentation/ticketView.ts");
    expect(view).toContain("timelineEntryHeadingText");
    expect(view).toContain("duration_seconds");
    const presentation = read("../presentation/ticketActionPresentation.ts");
    expect(presentation).toContain("Envie uma resposta neste chamado.");
    expect(presentation).not.toContain("status depende do helpdesk");
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

describe("HELPDESK-UNIFIED-RICH-TEXT-COMPOSER-V1 canonical editor", () => {
  it("accept/reject solution uses HelpdeskRichTextField, not a single-line input", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const start = detail.indexOf(
      '{activeAction === "accept_solution" ||',
    );
    const end = detail.indexOf('activeAction === "decide_validation" ? (');
    const block = detail.slice(start, end > start ? end : undefined);
    expect(block).toContain("HelpdeskRichTextField");
    expect(block).toContain("value={cycleNote}");
    expect(block).not.toContain("<input");
    expect(detail).toContain("hasVisibleRichText(cycleNote)");
  });

  it("validation decision comments share the canonical editor", () => {
    const page = read("HelpdeskPage.tsx");
    const surface = read("TicketApprovalsSurface.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const card = detail.slice(
      detail.indexOf('{activeAction === "decide_validation"'),
      detail.indexOf("helpdesk-satisfaction"),
    );
    expect(card).toContain("HelpdeskRichTextField");
    expect(card).not.toContain("<input");
    expect(surface).toContain("HelpdeskRichTextField");
    expect(surface).toContain("value={cycleNote}");
    expect(surface).not.toContain("<input");
  });

  it("validation decisions live inside the decide_validation action card", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const start = detail.indexOf('{activeAction === "decide_validation"');
    expect(start).toBeGreaterThan(-1);
    const end = detail.indexOf('activeAction === "submit_satisfaction"');
    const block = detail.slice(start, end > start ? end : undefined);
    expect(block).toContain('actionId="decide_validation"');
    expect(block).toContain("pendingValidations.map");
    expect(detail).toContain("item.mine_to_decide");
    expect(block).toContain("runValidationDecision(item.id, \"accept\")");
    expect(block).toContain("runValidationDecision(item.id, \"reject\")");
    expect(block).toContain("HelpdeskRichTextField");
    expect(block).toContain("submission_comment");
  });

  it("satisfaction comment stays plain text (GLPI field is TEXT) but multiline", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("HelpdeskTextArea");
    const sat = detail.slice(
      detail.indexOf("showSatisfactionComment ? ("),
      detail.indexOf("helpdesk-satisfaction__comment-toggle"),
    );
    expect(sat).toContain("HelpdeskTextArea");
    expect(sat).toContain("value={satisfactionComment}");
    expect(sat).toContain("maxLength={2000}");
    expect(sat).not.toContain("HelpdeskRichTextField");
    expect(sat).not.toContain("<input");
  });

  it("structured inputs stay structured; no free-text field uses ad-hoc editors", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    // Attachment title is short metadata — plain input is correct.
    expect(detail).toContain("value={documentTitle}");
    // No second editor implementation may appear.
    expect(detail).not.toContain("contentEditable");
    expect(detail).not.toContain("draft-js");
    expect(detail).not.toContain("react-quill");
    expect(detail).not.toContain("@tinymce");
  });
});

describe("HELPDESK-UNIFIED-ACTION-MENU-V1 single action menu", () => {
  it("accept/reject live in the selector menu, pinned first when pending", () => {
    const presentation = read("../presentation/ticketActionPresentation.ts");
    const actions = read("../presentation/ticketWorkspaceActions.ts");
    expect(presentation).toMatch(
      /SELECTOR_ACTION_IDS[\s\S]*?"accept_solution"[\s\S]*?"reject_solution"[\s\S]*?"reply"/,
    );
    expect(presentation).toContain("PENDING_DECISION_ACTION_IDS");
    expect(actions).toContain("ticketWorkspaceSelectorActions");
  });

  it("pending decision gets visual highlight and a discrete trigger indicator", () => {
    const menu = read("TicketActionMenu.tsx");
    const css = read("../index.css");
    expect(menu).toContain("PENDING_DECISION_ACTION_IDS.includes");
    expect(menu).toContain('data-pending-decision={isPendingDecision ? "true" : undefined}');
    expect(menu).toContain("helpdesk-action-menu__item--pending");
    expect(menu).toContain("helpdesk-action-menu__pending-dot");
    expect(menu).toContain("decisão pendente");
    expect(css).toContain(".helpdesk-action-menu__item--pending");
    expect(css).toContain(".helpdesk-action-menu__pending-dot");
    expect(css).toContain('.helpdesk-action-menu__trigger[data-pending-decision="true"]');
  });

  it("no redundant accept/reject buttons outside the menu", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const cueBlock = detail.slice(
      detail.indexOf("cue.showNativeActions"),
      detail.indexOf("cue.showValidationActions"),
    );
    expect(cueBlock).not.toContain("selectWorkspaceAction(");
    expect(cueBlock).not.toContain("<ActionButton");
    // The menu is the single entry point.
    expect(detail.match(/TicketActionMenu/g)?.length ?? 0).toBe(1);
    expect(detail).toContain('idleLabel="Ações do chamado"');
  });
});

describe("HELPDESK-UNIFIED-LIFECYCLE-ACTIONS-V1 lifecycle in menu", () => {
  it("satisfaction and validation decision are selector actions gated by BFF capabilities", () => {
    const actions = read("../presentation/ticketWorkspaceActions.ts");
    const presentation = read("../presentation/ticketActionPresentation.ts");
    expect(actions).toContain('"decide_validation"');
    expect(actions).toContain('"submit_satisfaction"');
    expect(actions).toContain("can_decide_validation");
    expect(actions).toContain("can_submit_satisfaction");
    expect(presentation).toMatch(
      /SELECTOR_ACTION_IDS[\s\S]*?"decide_validation"[\s\S]*?"submit_satisfaction"/,
    );
    expect(presentation).toMatch(
      /PENDING_DECISION_ACTION_IDS[\s\S]*?"decide_validation"/,
    );
    expect(presentation).not.toMatch(
      /PENDING_DECISION_ACTION_IDS[\s\S]*?"submit_satisfaction"/,
    );
  });

  it("top cue has no interactive lifecycle controls — hints point to the menu", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const cueStart = detail.indexOf("cue.showValidationActions");
    const cueEnd = detail.indexOf("</HelpdeskStateBanner>", cueStart);
    const validationBlock = detail.slice(cueStart, cueEnd);
    expect(validationBlock).not.toContain("<ActionButton");
    expect(validationBlock).not.toContain("<input");
    expect(validationBlock).not.toContain("type=\"radio\"");
    expect(validationBlock).not.toContain("runValidationDecision(");
    expect(validationBlock).not.toContain("runSatisfaction");
    expect(validationBlock).not.toContain("HelpdeskRichTextField");
    expect(validationBlock).not.toContain("HelpdeskTextArea");
    expect(validationBlock).toContain("menu de ações");
  });

  it("lifecycle flags still project pending state into the cue as information", () => {
    const page = read("HelpdeskPage.tsx");
    const lifecycle = read("../presentation/solicitanteLifecycle.ts");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("cue.showValidationActions");
    expect(detail).toContain("cue.showSatisfactionForm");
    expect(detail).toContain("cue.showNativeActions");
    expect(lifecycle).toContain("showValidationActions");
    expect(lifecycle).toContain("showSatisfactionForm");
    expect(lifecycle).toContain("showNativeActions");
  });

  it("menu stays available when only lifecycle actions remain (closed ticket)", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain(
      "selectorActions.length > 0 || workspaceActions.length > 0",
    );
    // Satisfaction/validation cards render inside the composer, not the cue.
    const composerStart = detail.indexOf(
      'className="helpdesk-ticket-workspace__composer"',
    );
    expect(composerStart).toBeGreaterThan(-1);
    const composer = detail.slice(composerStart);
    expect(composer).toContain('activeAction === "decide_validation"');
    expect(composer).toContain('activeAction === "submit_satisfaction"');
  });

  it("draft guard covers the new lifecycle cards", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    const dirty = detail.slice(
      detail.indexOf("function isActiveActionDirty"),
      detail.indexOf("function confirmDiscardDraft"),
    );
    expect(dirty).toContain('"decide_validation"');
    expect(dirty).toContain('"submit_satisfaction"');
    const cancel = detail.slice(
      detail.indexOf("function cancelActiveActionForm"),
      detail.indexOf("function closeActionAfterSuccess"),
    );
    expect(cancel).toContain('"decide_validation"');
    expect(cancel).toContain('"submit_satisfaction"');
  });
});
