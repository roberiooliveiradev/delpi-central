import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("ExternalSlideView contract", () => {
  it("pacote exporta ExternalSlideView canônico com referrerPolicy", () => {
    const src = readFileSync(join(here, "ExternalSlideView.tsx"), "utf8");
    const index = readFileSync(join(here, "index.ts"), "utf8");
    expect(index).toContain('from "./ExternalSlideView"');
    expect(src).toContain('referrerPolicy="no-referrer-when-downgrade"');
    expect(src).toContain("tdp-external-wrap");
  });

  it("prévia e public-hub consomem o pacote (sem iframe local)", () => {
    const preview = readFileSync(
      join(here, "../../tv-dashboard/src/presentation/PresentationPreview.tsx"),
      "utf8",
    );
    const publicView = readFileSync(
      join(here, "../../public-hub/src/apps/tv-dashboard/PresentationView.tsx"),
      "utf8",
    );
    expect(preview).toContain("ExternalSlideView");
    expect(preview).not.toContain("ExternalSlidePreview");
    expect(publicView).toContain("ExternalSlideView");
    expect(publicView).toContain("@delpi/tv-dashboard-presentation");
    expect(publicView).not.toContain('from "./ExternalSlideView"');
  });
});
