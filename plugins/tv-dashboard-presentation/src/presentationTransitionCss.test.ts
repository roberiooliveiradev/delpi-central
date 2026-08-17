import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { PRESENTATION_TRANSITION_STYLES } from "./presentationTransition";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "native-screens.css"),
  "utf8",
);

describe("CSS do catálogo de transições", () => {
  it.each(PRESENTATION_TRANSITION_STYLES)("implementa .tdp-slide--%s", (style) => {
    expect(css).toContain(`.tdp-slide--${style}`);
  });

  it("remove movimento quando o sistema pede redução", () => {
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\)/);
    expect(css).toMatch(/transition-duration:\s*0\.01ms\s*!important/);
  });

  it("desativa a entrada no primeiro paint da prévia", () => {
    expect(css).toMatch(/\.tdp-stage--boot \.tdp-slide\.tdp-slide--active/);
  });
});
