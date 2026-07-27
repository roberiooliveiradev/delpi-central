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

  it("emite tipografia global (família, peso, estilo, tamanho)", () => {
    const options = mergeConfigurableTableOptions({
      fontSize: 14,
      fontFamily: "Inter, sans-serif",
      fontWeight: "bold",
      fontStyle: "italic",
    });
    const vars = configurableTableOptionsCssVars(options);
    expect(vars["--delpi-ui-config-table-font-size"]).toBe("14px");
    expect(vars["--delpi-ui-config-table-font-family"]).toBe("Inter, sans-serif");
    expect(vars["--delpi-ui-config-table-font-weight"]).toBe("bold");
    expect(vars["--delpi-ui-config-table-font-style"]).toBe("italic");
  });
});
