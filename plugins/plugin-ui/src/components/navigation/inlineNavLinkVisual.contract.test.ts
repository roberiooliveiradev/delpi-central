import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

describe("inline-nav-link CSS contract", () => {
  const stylesEntry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");

  it("está importado no styles.css do kit", () => {
    expect(stylesEntry).toMatch(/@import\s+[\"'].*inline-nav-link\.css[\"']/);
  });
});
