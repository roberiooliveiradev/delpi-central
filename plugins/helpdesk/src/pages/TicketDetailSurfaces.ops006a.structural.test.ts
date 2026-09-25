import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("HELPDESK-OPS-006A ticket detail surfaces", () => {
  it("exposes conversation, details and approvals surfaces only", () => {
    const actions = read("../presentation/ticketWorkspaceActions.ts");
    expect(actions).toContain('"conversation" | "details" | "approvals"');
    expect(actions).toContain('{ id: "approvals", label: "Aprovações" }');
    expect(actions).not.toMatch(/id:\s*"(history|items|kb|costs|problems|changes)"/);
  });

  it("hides TicketContextPanel aside outside conversation and uses Details/Approvals surfaces", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain('workspaceSurface === "conversation" ? (');
    expect(detail).toContain("helpdesk-ticket-workspace__aside");
    expect(detail).toContain("helpdesk-ticket-workspace__body--no-aside");
    expect(detail).toContain("TicketDetailsSurface");
    expect(detail).toContain("TicketApprovalsSurface");
    expect(detail).not.toMatch(
      /workspaceSurface === "details" \? \(\s*<TicketContextPanel/,
    );
    const asideBlock = detail.slice(
      detail.lastIndexOf("helpdesk-ticket-workspace__aside") - 80,
      detail.lastIndexOf("helpdesk-ticket-workspace__aside") + 400,
    );
    expect(asideBlock).toContain('workspaceSurface === "conversation"');
    expect(asideBlock).toContain("TicketContextPanel");
  });

  it("Details uses service-level name labels, not deadline wording", () => {
    const details = read("TicketDetailsSurface.tsx");
    expect(details).toContain("Nível de serviço para atendimento");
    expect(details).toContain("Nível de serviço para solução");
    expect(details).not.toContain("Tempo para atendimento");
    expect(details).not.toContain("Tempo para solução");
    expect(details).toContain("slaLevelName");
    expect(details).toContain("Nenhum observador.");
    expect(details).toContain("canAssign={ticket.can_assign === true}");
    expect(details).toContain("solved_at");
    expect(details).toContain("closed_at");
    expect(details).toContain("Ver aprovações");
    expect(details).toContain("approvalSummaryCounts");
    expect(details).not.toContain("ticket.validations.map");
    expect(details).not.toContain("Adicionar observador");
  });

  it("Approvals lists validations with capability-gated decide/request and no global status", () => {
    const approvals = read("TicketApprovalsSurface.tsx");
    expect(approvals).toContain("Nenhuma solicitação de aprovação neste chamado.");
    expect(approvals).toContain("ticket.validations");
    expect(approvals).toContain("mine_to_decide === true");
    expect(approvals).toContain("can_request_approval === true");
    expect(approvals).toContain("Pedir aprovação");
    expect(approvals).toContain("Aceitar aprovação");
    expect(approvals).toContain("Recusar aprovação");
    expect(approvals).toContain("validationStatusLabel");
    expect(approvals).not.toMatch(/status global|globalStatus|overall.?validation/i);
  });

  it("Pedir aprovação CTA routes to conversation + existing request_approval Action Card", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("function openRequestApproval");
    expect(detail).toContain('setWorkspaceSurface("conversation")');
    expect(detail).toContain('selectWorkspaceAction("request_approval")');
    expect(detail).toContain('data-action-variant="approval"');
    expect(detail).toContain("onRequestApproval={openRequestApproval}");
    expect(detail).not.toContain("TicketApprovalActionFields\n                    ticket=");
    const approvals = read("TicketApprovalsSurface.tsx");
    expect(approvals).not.toContain("TicketApprovalActionFields");
    expect(approvals).not.toContain("requestTicketApproval(");
  });

  it("keeps conversation action menu contracts intact", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain('activeAction === "reply"');
    expect(detail).toContain('activeAction === "create_solution"');
    expect(detail).toContain('activeAction === "create_task"');
    expect(detail).toContain('activeAction === "attach_file"');
    expect(detail).toContain('activeAction === "request_approval"');
    expect(detail).toContain("createFollowup");
    expect(detail).toContain("createTicketSolution");
    expect(detail).toContain("createTicketTask");
    expect(detail).toContain("uploadTicketAttachment");
    expect(detail).toContain("requestTicketApproval");
  });

  it("does not add new frontend API endpoints for Wave A", () => {
    const api = read("../api/helpdeskApi.ts");
    expect(api).not.toMatch(/\/tickets\/\$\{ticketId\}\/(observers|history|items|costs|pdf)/);
    expect(api).toContain("`/tickets/${ticketId}/validations`");
    expect(api).toContain("setTicketAssignee");
  });

  it("CSS full-width layout when aside is hidden", () => {
    const css = read("../index.css");
    expect(css).toContain(".helpdesk-ticket-workspace__body--no-aside");
    expect(css).toContain(".helpdesk-ticket-details");
    expect(css).toContain(".helpdesk-ticket-approvals");
  });
});
