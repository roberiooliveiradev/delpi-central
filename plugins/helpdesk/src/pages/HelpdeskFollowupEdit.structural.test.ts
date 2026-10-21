import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("HELPDESK-MFE-UX follow-up editing", () => {
  it("exposes Editar only for own follow-up entries, never for other kinds", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("resolveActions=");
    const actionsBlock = detail.slice(detail.indexOf("resolveActions="));
    expect(actionsBlock).toContain('message.kind !== "followup" || message.mine !== true');
    expect(actionsBlock).toContain('id: "edit"');
    expect(actionsBlock).toContain('label: "Editar"');
    // Solutions/tasks/opening never carry the affordance through this guard.
    expect(actionsBlock).not.toContain('message.kind === "solution"');
  });

  it("renders the kit edit slot inside the thread with save/cancel states", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function TicketDetailPage"));
    expect(detail).toContain("editingId={followupEditingId}");
    expect(detail).toContain("renderEditSlot=");
    expect(detail).toContain('className="helpdesk-followup-edit"');
    expect(detail).toContain('aria-label="Editar acompanhamento"');
    expect(detail).toContain("HelpdeskRichTextField");
    expect(detail).toContain('className="helpdesk-followup-edit__error"');
    expect(detail).toContain('role="alert"');
    expect(detail).toContain('"Salvando…"');
    expect(detail).toContain("Cancelar");
    expect(detail).toContain("cancelFollowupEdit");
  });

  it("calls the typed BFF PUT with idempotency key, then authoritative reload", () => {
    const api = read("../api/helpdeskApi.ts");
    expect(api).toContain("export function updateFollowup(");
    expect(api).toContain("`/tickets/${ticketId}/followups/${followupId}`");
    expect(api).toContain('method: "PUT"');
    expect(api).toContain('"Idempotency-Key": idempotencyKey');

    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function saveFollowupEdit"));
    expect(detail).toContain("updateFollowup(");
    expect(detail).toContain("followupEditKey");
    // No optimistic timeline patch — success only shows GLPI re-read content.
    expect(detail).toContain("load();");
    expect(detail).not.toContain("setTicket((current)");
  });

  it("keeps the draft on recoverable failure and blocks empty submits", () => {
    const page = read("HelpdeskPage.tsx");
    const detail = page.slice(page.indexOf("function saveFollowupEdit"));
    expect(detail).toContain("hasVisibleRichText(followupEditContent)");
    expect(detail).toContain("setFollowupEditError(");
    // On error the editor stays open — typed text is not wiped.
    const errorBlock = detail.slice(detail.indexOf(".catch"));
    expect(errorBlock).not.toContain("setFollowupEditContent(");
  });

  it("shim mirrors the kit edit contract (editingId + renderEditSlot)", () => {
    const shim = read("../shims/plugin-ui.d.ts");
    expect(shim).toContain("editingId?: string | null");
    expect(shim).toContain("renderEditSlot?: (message: MessageThreadItem) => ReactNode");
    expect(shim).toContain("icon?: ReactNode");
  });

  it("does not introduce a second follow-up write path", () => {
    const api = read("../api/helpdeskApi.ts");
    const followupRoutes = api.match(/\/followups/g) ?? [];
    // One POST (create) + one PUT (update) — no duplicate update route.
    expect(followupRoutes.length).toBe(2);
    expect(api).toContain('method: "POST"');
    expect(api).toContain('method: "PUT"');
    expect(api).not.toContain("followups/${followupId}/content");
  });
});
