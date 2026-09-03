import { describe, expect, it } from "vitest";

import { MY_REQUESTS_HELP_TOOLTIPS } from "./helpTooltips";

const REQUIRED_SECTIONS = [
  "shell",
  "mine",
  "workQueue",
  "new",
  "invoiceWizard",
  "detail",
  "timeline",
  "comments",
  "attachments",
  "artifacts",
] as const;

describe("MY_REQUESTS_HELP_TOOLTIPS", () => {
  it("cobre mine, work-queue, new, detail e painéis", () => {
    for (const key of REQUIRED_SECTIONS) {
      expect(MY_REQUESTS_HELP_TOOLTIPS[key]).toBeTruthy();
    }
  });

  it("textos principais não vazios", () => {
    expect(MY_REQUESTS_HELP_TOOLTIPS.mine.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.workQueue.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.new.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.section.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.detail.actions.length).toBeGreaterThan(20);
    expect(MY_REQUESTS_HELP_TOOLTIPS.timeline.section.length).toBeGreaterThan(10);
    expect(MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.section.length).toBeGreaterThan(20);
  });
});
