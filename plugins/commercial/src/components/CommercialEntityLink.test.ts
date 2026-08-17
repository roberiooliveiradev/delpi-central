import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const css = readFileSync(resolve(root, "src/index.css"), "utf8");

describe("CommercialEntityLink visual parity CSS", () => {
  it("estende cm-link-button para anchors com visited reset", () => {
    expect(css).toMatch(/a\.cm-link-button/);
    expect(css).toMatch(/a\.cm-link-button:visited/);
  });

  it("estende nome de cliente para anchors com visited reset", () => {
    expect(css).toMatch(/a\.cm-open-orders-client__name:hover/);
    expect(css).toMatch(/a\.cm-open-orders-client__name:visited/);
  });
});
