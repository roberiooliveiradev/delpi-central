import { describe, expect, it } from "vitest";

import {
  configurableTableOptionsCssVars,
  mergeConfigurableTableOptions,
} from "./configurableTableOptions";

describe("configurableTableOptionsCssVars", () => {
  it("emite peso e estilo da caneta de borda", () => {
    const options = mergeConfigurableTableOptions({
      borderWidth: 2,
      borderStyle: "dashed",
      borderColor: "#aabbcc",
    });
    const vars = configurableTableOptionsCssVars(options);
    expect(vars["--delpi-ui-config-table-border-width"]).toBe("2px");
    expect(vars["--delpi-ui-config-table-border-style"]).toBe("dashed");
    expect(vars["--delpi-ui-config-table-border-color"]).toBe("#aabbcc");
  });
});
