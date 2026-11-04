import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

function source(relativePath: string): string {
  return readFileSync(join(here, relativePath), "utf8");
}

function sliceBetween(text: string, start: string, end: string): string {
  const from = text.indexOf(start);
  const to = text.indexOf(end, from + start.length);
  return from >= 0 && to > from ? text.slice(from, to) : text;
}

describe("Line feeder E4 wiring", () => {
  it("usa materials/preview e published-queue no fluxo principal", () => {
    const page = source("./LineFeederPage.tsx");
    const api = source("../api/ppcApi.ts");
    expect(page).toMatch(/LineFeederCollectModal/);
    expect(page).toMatch(/LineFeederIdleCard/);
    expect(page).toMatch(/useLineFeederMaterialsPreview/);
    expect(page).toMatch(/LineFeederUrgentRequestsPanel/);
    expect(page).not.toMatch(/fetchLineFeederRequirements/);
    expect(page).not.toMatch(/createLineFeederPickPlan/);
    expect(page).not.toMatch(/patchLineFeederPickItem/);
    expect(page).not.toMatch(/closeLineFeederPickPlan/);
    expect(api).toMatch(/\/line-feeder\/materials\/preview/);
    expect(api).toMatch(/\/line-feeder\/published-queue/);
  });

  it("idle state usa cartão Liquid Glass com CTA Coletar", () => {
    const idle = source("../components/LineFeederIdleCard.tsx");
    const css = source("../index.css");
    const copy = sliceBetween(source("../content/copy.ts"), "lineFeeder:", "materials:");
    expect(idle).toMatch(/ppc-feeder-idle__cta/);
    expect(idle).toMatch(/emptyTitle/);
    expect(copy).toMatch(/emptyTitle:\s*"Pronto para abastecer"/);
    expect(css).toMatch(/backdrop-filter:\s*saturate\(190%\) blur\(36px\)/);
    expect(css).toMatch(/ppc-feeder-idle__card/);
  });

  it("não vaza códigos técnicos de estoque na copy nem na ajuda", () => {
    const copy = sliceBetween(source("../content/copy.ts"), "lineFeeder:", "materials:");
    const help = sliceBetween(
      source("../content/helpTooltips.ts"),
      "lineFeeder:",
      "lineFeederPickPlan:",
    );
    for (const leak of ["SD3", "D3_CF", "SB2", "DE0", "RE0", "PR0", "SD4"]) {
      expect(copy).not.toContain(leak);
      expect(help).not.toContain(leak);
    }
    expect(help.toLowerCase()).toContain("coletar");
  });
});
