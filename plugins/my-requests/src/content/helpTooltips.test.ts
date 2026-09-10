import { describe, expect, it } from "vitest";

import { MY_REQUESTS_HELP_TOOLTIPS } from "./helpTooltips";

const REQUIRED_SECTIONS = [
  "shell",
  "mine",
  "workQueue",
  "new",
  "invoiceWizard",
  "rawMaterialForm",
  "detail",
  "actions",
  "timeline",
  "comments",
  "attachments",
  "artifacts",
  "admin",
] as const;

describe("MY_REQUESTS_HELP_TOOLTIPS", () => {
  it("cobre mine, work-queue, new, detail e painéis", () => {
    for (const key of REQUIRED_SECTIONS) {
      expect(MY_REQUESTS_HELP_TOOLTIPS[key]).toBeTruthy();
    }
  });

  it("textos principais não vazios e sem jargão técnico óbvio", () => {
    expect(MY_REQUESTS_HELP_TOOLTIPS.mine.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.workQueue.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.new.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.actions.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.progress.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.type.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.status.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.branch.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.comments.newComment.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.comments.section).toMatch(/conversa/i);
    expect(MY_REQUESTS_HELP_TOOLTIPS.actions.start.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.actions.return.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.actions.complete.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.attachments.upload.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.attachments.create.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.attachments.pending.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.attachments.upload).toMatch(/Salvar documentos/);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.returnReason.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.correctionTargets.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.artifacts.kind.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.artifacts.pending.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.artifacts.upload).toMatch(/Salvar documentos/);
    expect(MY_REQUESTS_HELP_TOOLTIPS.timeline.section.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.rawMaterialForm.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.admin.section).not.toMatch(/my-requests\.manage/);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.section).not.toMatch(/allowed_actions/);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.progress).not.toMatch(
      /WorkflowEngine|artifact_kind|requests-api|operationId/i,
    );
    for (const key of [
      "progress",
      "recipient",
      "invoiceType",
      "items",
      "freight",
      "extras",
      "review",
      "partySearch",
      "productSearch",
      "carrierSearch",
      "partyType",
      "itemQuantity",
      "itemUnitPrice",
      "weightKg",
      "volumeCount",
      "observation",
    ] as const) {
      expect(MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard[key].length).toBeGreaterThan(10);
      expect(MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard[key]).not.toMatch(
        /lookup|requests-api|WorkflowEngine|operationId/i,
      );
    }
  });
});
