import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("native checkbox containing block", () => {
  const css = readFileSync(resolve(here, "../../styles/native-controls.css"), "utf8");

  it("define position:relative no label (input absoluto não ancora no side panel)", () => {
    const block = css.slice(
      css.indexOf(".delpi-ui-native-checkbox {"),
      css.indexOf(".delpi-ui-native-checkbox[data-disabled"),
    );
    expect(block).toContain("position: relative");
    expect(css).toContain(".delpi-ui-native-checkbox__input");
    expect(css).toMatch(/\.delpi-ui-native-checkbox__input\s*\{[^}]*position:\s*absolute/s);
  });
});
