import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

function read(relativePath: string): string {
  return readFileSync(join(root, relativePath), "utf8");
}

function cssRule(css: string, selector: string): string {
  const start = css.indexOf(selector);
  expect(start, `selector ${selector} must exist`).toBeGreaterThanOrEqual(0);
  const openBrace = css.indexOf("{", start);
  const closeBrace = css.indexOf("}", openBrace);
  return css.slice(openBrace, closeBrace);
}

const POPOVER_FILES = [
  "HelpdeskAssignPopover.tsx",
  "TicketListFilterPopover.tsx",
  "TicketListSortPopover.tsx",
  "TicketTimelineTools.tsx",
];

describe("HELPDESK-MFE-UX-007 composer height ownership", () => {
  const css = read("../index.css");

  it("conversation inner is a shrinkable flex column (not unbounded auto grid rows)", () => {
    const rule = cssRule(css, ".helpdesk-detail__conversation-inner {");
    expect(rule).toContain("display: flex");
    expect(rule).toContain("flex-direction: column");
    expect(rule).toContain("overflow: hidden");
    expect(rule).not.toContain("grid-template-rows: minmax(0, 1fr) auto");
  });

  it("idle composer never collapses; open-card composer bounds and clips", () => {
    const idle = cssRule(css, ".helpdesk-ticket-workspace__composer {");
    expect(idle).toContain("flex: 0 0 auto");
    const open = cssRule(
      css,
      ".helpdesk-ticket-workspace__composer:has(> .helpdesk-action-card) {",
    );
    expect(open).toContain("flex: 0 1 auto");
    expect(open).toContain("min-height: 0");
    expect(open).toContain("overflow: hidden");
    const card = cssRule(
      css,
      ".helpdesk-ticket-workspace__composer > .helpdesk-action-card {",
    );
    expect(card).toContain("flex: 0 1 auto");
    expect(card).toContain("min-height: 0");
  });

  it("action card is bounded: body carries scroll, header/footer stay pinned", () => {
    const card = cssRule(css, ".dashboard-helpdesk .helpdesk-action-card {");
    expect(card).toContain("min-height: 0");
    expect(card).toContain("max-height: 100%");
    const body = cssRule(css, ".helpdesk-action-card__body {");
    expect(body).toContain("overflow-y: auto");
    expect(body).toContain("min-height: 0");
    expect(body).toContain("flex: 0 1 auto");
    const footer = cssRule(css, ".helpdesk-action-card__footer {");
    expect(footer).toContain("flex: 0 0 auto");
    const header = cssRule(css, ".helpdesk-action-card__header {");
    expect(header).toContain("flex: 0 0 auto");
  });

  it("TicketActionCard renders footer as sibling AFTER the scrollable body", () => {
    const card = read("TicketActionCard.tsx");
    const bodyIdx = card.indexOf('className="helpdesk-action-card__body"');
    const footerIdx = card.indexOf('className="helpdesk-action-card__footer"');
    expect(bodyIdx).toBeGreaterThanOrEqual(0);
    expect(footerIdx).toBeGreaterThan(bodyIdx);
  });

  it("timeline extras are bounded and scroll — never collapse to a sliver", () => {
    const rule = cssRule(css, ".helpdesk-timeline-extras {");
    expect(rule).toContain("flex: 0 0 auto");
    expect(rule).toContain("max-height:");
    expect(rule).toContain("overflow-y: auto");
  });

  it("workspace main keeps min-width: 0 so aside never causes horizontal overflow", () => {
    const rule = cssRule(css, ".helpdesk-ticket-workspace__main {");
    expect(rule).toContain("min-width: 0");
  });
});

describe("HELPDESK-MFE-UX-007 overlays use the canonical portal", () => {
  it("every anchored popover renders through AnchoredPanelPortal with helpdesk scope", () => {
    for (const file of POPOVER_FILES) {
      const src = read(file);
      expect(src, file).toContain("AnchoredPanelPortal");
      expect(src, file).toContain('portalScopeClassName="dashboard-helpdesk"');
      expect(src, file).toContain("onDismiss");
      expect(src, file).not.toContain("useClickOutside(");
    }
  });

  it("panel CSS no longer carries absolute positioning or a local z-index bandaid", () => {
    const css = read("../index.css");
    const panel = cssRule(css, ".helpdesk-anchored-popover__panel {");
    expect(panel).not.toContain("position: absolute");
    expect(panel).not.toContain("z-index");
    expect(panel).toContain("overflow: auto");
    expect(panel).toContain("max-height:");
  });

  it("assign popover keeps picker, confirm action and dismiss semantics", () => {
    const src = read("HelpdeskAssignPopover.tsx");
    expect(src).toContain("HelpdeskAssigneePicker");
    expect(src).toContain("onConfirm");
    expect(src).toContain("aria-expanded={open}");
    expect(src).toContain('role="dialog"');
    expect(src).toContain('preferredPlacement="bottom"');
  });
});
