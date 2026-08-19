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
    expect(css).toMatch(/\.cm-room-thread__msgs \{[\s\S]*?overflow-y:\s*auto;/);
    const fillChunk = css.split("Sala: fill viewport")[1]?.slice(0, 2500) ?? "";
    expect(fillChunk).not.toMatch(/\.delpi-ui-/);
  });
});
