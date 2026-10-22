import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

describe("HELPDESK-MFE-UX ticket classification editing", () => {
  it("gates the edit affordance on the backend can_update_classification flag", () => {
    const surface = read("TicketDetailsSurface.tsx");
    expect(surface).toContain("ticket.can_update_classification === true");
    expect(surface).toContain("Editar classificação");
    // The page handler also fails closed — never trusts the UI flag alone.
    const page = read("HelpdeskPage.tsx");
    const begin = page.slice(page.indexOf("function beginClassificationEdit"));
    expect(begin).toContain("if (!ticket?.can_update_classification) return");
  });

  it("renders selects for every editable field and priority as derived read-only", () => {
    const surface = read("TicketDetailsSurface.tsx");
    const form = surface.slice(surface.indexOf("helpdesk-classification-form"));
    for (const label of ["Categoria", "Tipo", "Urgência", "Impacto", "Origem"]) {
      expect(form).toContain(`label="${label}"`);
    }
    // Priority is matrix-derived — label + hint only, never a select.
    expect(form).toContain("classificationPriorityDerived");
    expect(form).not.toContain('label="Prioridade"\n              hint=');
    const selects = form.match(/<HelpdeskSelect/g) ?? [];
    expect(selects.length).toBe(5);
  });

  it("sends only changed fields through the typed PATCH with idempotency key", () => {
    const surface = read("TicketDetailsSurface.tsx");
    expect(surface).toContain("patch[field] = next");
    expect(surface).toContain("!hasChanges");

    const api = read("../api/helpdeskApi.ts");
    expect(api).toContain("export function updateTicketClassification(");
    expect(api).toContain("`/tickets/${ticketId}/classification`");
    expect(api).toContain('method: "PATCH"');
    expect(api).toContain('"Idempotency-Key": idempotencyKey');

    const page = read("HelpdeskPage.tsx");
    const save = page.slice(
      page.indexOf("function saveClassification"),
      page.indexOf("function beginFollowupEdit"),
    );
    expect(save).toContain("updateTicketClassification(ticketId, patch, classificationKey)");
    // Success re-reads the authoritative GLPI state — no optimistic patch.
    expect(save).toContain("await load()");
    expect(save).not.toContain("setTicket(");
  });

  it("loads the real backend catalogs lazily on first edit", () => {
    const page = read("HelpdeskPage.tsx");
    const begin = page.slice(page.indexOf("function beginClassificationEdit"));
    expect(begin).toContain("listCategories()");
    expect(begin).toContain("listUrgencies()");
    expect(begin).toContain("listImpacts()");
    expect(begin).toContain("listTicketTypes()");
    expect(begin).toContain("listRequestTypes()");
  });

  it("keeps the draft on recoverable failure and rotates the key on success", () => {
    const page = read("HelpdeskPage.tsx");
    const save = page.slice(
      page.indexOf("function saveClassification"),
      page.indexOf("function beginFollowupEdit"),
    );
    // Error path: editing stays open — selection is not wiped.
    const errorBlock = save.slice(save.indexOf(".catch"));
    expect(errorBlock).toContain("setErrorText(");
    expect(errorBlock).not.toContain("setClassificationEditing(false)");
    // Fresh idempotency key per edit session, rotated after success.
    expect(save).toContain("setClassificationKey(newIdempotencyKey())");
  });

  it("documents the feature through the canonical helpTooltips content layer", () => {
    const tooltips = read("../content/helpTooltips.ts");
    const detail = tooltips.slice(tooltips.indexOf("detailUi:"));
    for (const key of [
      "classificationEdit",
      "classificationCategory",
      "classificationType",
      "classificationUrgency",
      "classificationImpact",
      "classificationRequestType",
      "classificationPriorityDerived",
      "classificationSave",
      "classificationCancel",
    ]) {
      expect(detail).toContain(`${key}:`);
    }
  });
});
