import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  ConfigurableTableClassesProvider,
  configurableTableTvClasses,
} from "../configurableTableClasses";
import { TableContainer } from "./TableContainer";

afterEach(() => cleanup());

const transparentParts = {
  frame: { style: { fill: "transparent", stroke: "#06a6dd", strokeWidth: 1 } },
};

describe("TableContainer sem fundo (GLPI #1606)", () => {
  it("só habilita transparência completa quando a moldura é explicitamente transparente", () => {
    const { container, rerender } = render(
      <TableContainer options={{ headerBg: "#dbeafe", cellBg: "#fff8ee", zebraStripe: true }}>
        <span>Valor</span>
      </TableContainer>,
    );
    expect(container.firstElementChild?.classList.contains(
      "delpi-ui-config-table--transparent-background",
    )).toBe(false);

    rerender(
      <TableContainer
        options={{ headerBg: "#dbeafe", cellBg: "#fff8ee", zebraStripe: true }}
        tableParts={transparentParts}
      >
        <span>Valor</span>
      </TableContainer>,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.classList.contains("delpi-ui-config-table--transparent-background")).toBe(true);
    expect(root.style.getPropertyValue("--delpi-ui-config-table-bg")).toBe("transparent");
    expect(root.classList.contains("delpi-ui-config-table--frameless")).toBe(true);
    // Não apaga a configuração de cores que volta quando o usuário reativa o fundo.
    expect(root.style.getPropertyValue("--delpi-ui-config-table-header-bg")).toBe("#dbeafe");
    expect(root.style.getPropertyValue("--delpi-ui-config-table-cell-bg")).toBe("#fff8ee");
  });

  it("aplica a mesma classe no renderer de TV publicado (tdp-*)", () => {
    const { container } = render(
      <ConfigurableTableClassesProvider classNames={configurableTableTvClasses()}>
        <TableContainer options={{}} tableParts={transparentParts}>
          <span>TV</span>
        </TableContainer>
      </ConfigurableTableClassesProvider>,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.classList.contains("tdp-configurable-table")).toBe(true);
    expect(root.classList.contains("delpi-ui-config-table--transparent-background")).toBe(true);
    expect(root.style.getPropertyValue("--tdp-table-bg")).toBe("transparent");
  });
});
