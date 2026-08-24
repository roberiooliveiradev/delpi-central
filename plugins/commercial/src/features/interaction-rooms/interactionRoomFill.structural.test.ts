import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(dir, "../../index.css"), "utf8");

describe("interaction room fill CSS", () => {
  it("preenche viewport só com --fill; chrome da thread no kit", () => {
    expect(css).toMatch(/\.dashboard-commercial\.dashboard-page--fill \{/);
    const fillPage =
      css.match(
        /\.dashboard-commercial\.dashboard-page--fill \{[^}]+\}/,
      )?.[0] ?? "";
    expect(fillPage).toMatch(/padding:\s*0/);
    expect(fillPage).toMatch(/gap:\s*0/);
    expect(fillPage).not.toMatch(/--cm-page-padding:\s*16px/);
    expect(css).toMatch(/\.dashboard-page--fill \.cm-view-transition--page/);
    expect(css).toMatch(/--delpi-ui-room-thread-header-padding/);
    expect(css).toMatch(/--delpi-ui-room-thread-msgs-padding-inline/);
    expect(css).toMatch(/--delpi-ui-room-thread-dock-padding/);
    expect(css).not.toMatch(/\.cm-room-thread__stage \{/);
    expect(css).not.toMatch(/\.cm-room-thread__body \{/);
    expect(css).not.toMatch(/\.cm-room-panel \{/);
    expect(css).toMatch(/\.cm-interaction-room-embed \{/);
    const fillChunk = css.split("Sala: fill viewport")[1]?.slice(0, 2500) ?? "";
    expect(fillChunk).not.toMatch(/\.delpi-ui-/);
    expect(css).not.toMatch(/max-height:\s*40vh/);
    expect(css).not.toMatch(/delpi-ui-room-side-panel/);
    expect(css).not.toMatch(/cm-room-thread__context/);
    expect(css).not.toMatch(/cm-room-context-drawer/);
    expect(css).toMatch(/\.cm-room-alert-host \{[\s\S]*?position:\s*absolute;/);
    expect(css).toMatch(/\.cm-room-inbox-pane \{[\s\S]*?gap:\s*var\(--cm-gap-sm\);/);
    expect(css).toMatch(/\.cm-room-inbox-pane__body \{[\s\S]*?display:\s*flex;/);
    expect(css).toMatch(/\.cm-room-workspace \{[\s\S]*?flex-direction:\s*column;/);
    expect(css).toMatch(/\.cm-room-workspace__grid \{[\s\S]*?flex:\s*1 1 auto;/);
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
    expect(portalCss).toMatch(
      /\.content:has\(\.dashboard-page--fill\) \{[\s\S]*?scrollbar-gutter:\s*auto;/,
    );
    expect(portalCss).toMatch(/scrollbar-gutter:\s*stable/);
  });

  it("fill #root não usa 100vh (evita corte no mount do Portal)", () => {
    const fillRoot =
      css.match(
        /#root:has\(> \.dashboard-commercial\.dashboard-page--fill\) \{[^}]+\}/,
      )?.[0] ?? "";
    expect(fillRoot).toMatch(/height:\s*100%/);
    expect(fillRoot).toMatch(/min-height:\s*0/);
    expect(fillRoot).not.toMatch(/100vh/);
    expect(css).toMatch(
      /\.cm-resizable-columns__left > \.cm-room-inbox-pane \{[\s\S]*?min-height:\s*0;/,
    );
    expect(css).toMatch(
      /\.cm-resizable-columns__right > \.cm-room-thread \{[\s\S]*?min-height:\s*0;/,
    );
    expect(css).toMatch(
      /\.cm-room-inbox-pane__body > \.cm-room-inbox-panel \{[\s\S]*?min-height:\s*0;/,
    );
    expect(css).toMatch(
      /\.cm-room-inbox-pane \{[\s\S]*?padding-inline:\s*var\(--cm-gap\);/,
    );
    expect(css).toMatch(
      /\.cm-room-inbox-pane \.cm-room-inbox__list \{[\s\S]*?padding-inline:\s*0;/,
    );
  });
});
