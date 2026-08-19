import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(dir, "../../index.css"), "utf8");

describe("interaction room fill CSS", () => {
  it("preenche viewport só com --fill e um scroller em __msgs", () => {
    expect(css).toMatch(/\.dashboard-commercial\.dashboard-page--fill \{/);
    expect(css).toMatch(/--cm-page-padding:\s*16px/);
    expect(css).toMatch(/\.dashboard-page--fill \.cm-view-transition--page/);
    expect(css).toMatch(/\.cm-room-thread__stage \{[\s\S]*?position:\s*relative;/);
    expect(css).toMatch(/\.cm-room-thread__msgs \{[\s\S]*?overflow-y:\s*auto;/);
    const fillChunk = css.split("Sala: fill viewport")[1]?.slice(0, 2500) ?? "";
    expect(fillChunk).not.toMatch(/\.delpi-ui-/);
    expect(css).not.toMatch(/max-height:\s*40vh/);
    expect(css).toMatch(/\.cm-room-thread__body \{[\s\S]*?display:\s*flex;/);
    expect(css).toMatch(/\.cm-room-thread__main \{[\s\S]*?flex-direction:\s*column;/);
    expect(css).not.toMatch(/delpi-ui-room-side-panel/);
    expect(css).not.toMatch(/cm-room-thread__context/);
    expect(css).not.toMatch(/cm-room-context-drawer/);
    expect(css).toMatch(/\.cm-room-alert-host \{[\s\S]*?position:\s*absolute;/);
    expect(css).toMatch(/\.cm-room-inbox-pane \{[\s\S]*?gap:\s*var\(--cm-gap-sm\);/);
    expect(css).toMatch(/\.cm-room-inbox-pane__body \{[\s\S]*?display:\s*flex;/);
    expect(css).toMatch(/\.cm-room-workspace__grid > \.cm-room-inbox-pane/);
  });

  it("o host do Portal honra dashboard-page--fill (não height auto)", () => {
    const portalCss = readFileSync(
      join(dir, "../../../../../portal/src/index.css"),
      "utf8",
    );
    expect(portalCss).toMatch(/:not\(\.dashboard-page--fill\)/);
    expect(portalCss).toMatch(
      /\.app-host-federated__mount:has\(\.dashboard-page--fill\)/,
    );
    expect(portalCss).toMatch(/\.content:has\(\.dashboard-page--fill\)/);
  });
});
