import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  ComunicadoInputBlockView,
  resolveInputControlKind,
} from "./ComunicadoInputBlockView";
import type { ComunicadoInputBlock } from "./comunicadoTypes";

function makeBlock(
  input: ComunicadoInputBlock["input"],
): ComunicadoInputBlock {
  return {
    id: "input-1",
    type: "input",
    frame: { x: 0, y: 0, w: 30, h: 12 },
    input,
  };
}

describe("resolveInputControlKind", () => {
  it("usa enum/boolean/number/date do paramSchema", () => {
    expect(resolveInputControlKind("branch", { type: "string", enum: ["01", "02"] })).toBe(
      "select",
    );
    expect(resolveInputControlKind("flag", { type: "boolean" })).toBe("boolean");
    expect(resolveInputControlKind("limit", { type: "integer" })).toBe("number");
    expect(resolveInputControlKind("fromDate", { type: "string", format: "date" })).toBe("date");
    expect(resolveInputControlKind("q", { type: "string" })).toBe("text");
  });
});

describe("ComunicadoInputBlockView", () => {
  it("renderiza ícone, badge de escopo e select do enum", () => {
    const { container } = render(
      <ComunicadoInputBlockView
        block={makeBlock({
          paramKey: "branch",
          label: "Filial",
          iconName: "Building2",
          targetScope: "sources",
          targetSourceIds: ["a", "b"],
          defaultValue: "01",
        })}
        field={{ type: "string", enum: ["01", "02"], label: "Filial" }}
        interactive
        linkedSourceCount={2}
      />,
    );

    expect(screen.getByText("Filial")).toBeTruthy();
    expect(screen.getByText("2 fontes")).toBeTruthy();
    expect(container.querySelector('[data-input-part="icon"]')).toBeTruthy();
    expect(container.querySelector('[data-input-part="label"]')).toBeTruthy();
    expect(container.querySelector('[data-input-part="badge"]')).toBeTruthy();
    expect(container.querySelector('[data-input-part="control"]')).toBeTruthy();
    expect(container.querySelector("select.delpi-ui-native-control")).toBeTruthy();
    expect(container.querySelector("select.tdp-comunicado__input-block-control--select")).toBeTruthy();
    expect(container.querySelector('[data-scope="sources"]')).toBeTruthy();
  });

  it("badge «Filtro do slide» e input date", () => {
    const { container } = render(
      <ComunicadoInputBlockView
        block={makeBlock({
          paramKey: "fromDate",
          targetScope: "slide",
          defaultValue: "2026-01-01",
        })}
        field={{ type: "string", format: "date" }}
        interactive
      />,
    );

    expect(screen.getByText("Filtro do slide")).toBeTruthy();
    expect(
      container.querySelector("input.delpi-ui-native-control.tdp-comunicado__input-block-control--date[type='date']"),
    ).toBeTruthy();
  });

  it("sem paramKey pede seleção no inspetor; com paramKey e schema ausente ainda edita", () => {
    const { rerender, container } = render(
      <ComunicadoInputBlockView
        block={makeBlock({ paramKey: "", targetScope: "slide" })}
        interactive
        paramAvailable={false}
      />,
    );
    expect(screen.getByText("Selecione o parâmetro no inspetor")).toBeTruthy();

    rerender(
      <ComunicadoInputBlockView
        block={makeBlock({
          paramKey: "branch",
          label: "Filial",
          targetScope: "slide",
        })}
        interactive
        paramAvailable={false}
      />,
    );
    expect(screen.queryByText("Selecione o parâmetro no inspetor")).toBeNull();
    expect(screen.getAllByText("Filial").length).toBeGreaterThan(0);
    expect(container.querySelector("input.delpi-ui-native-control.tdp-comunicado__input-block-control")).toBeTruthy();
    expect(screen.getByText("Valor livre")).toBeTruthy();
  });

  it("com interaction e parte control não selecionada, nativo fica hit-through", () => {
    const onPartPointerDown = vi.fn();
    const { container } = render(
      <ComunicadoInputBlockView
        block={makeBlock({
          paramKey: "branch",
          label: "Filial",
          targetScope: "slide",
          defaultValue: "01",
        })}
        field={{ type: "string", label: "Filial" }}
        interactive
        interaction={{
          selectedPart: null,
          onPartPointerDown,
        }}
      />,
    );
    const input = container.querySelector("input.delpi-ui-native-control.tdp-comunicado__input-block-control");
    expect(input?.classList.contains("tdp-comunicado__input-block-control--hit-through")).toBe(
      true,
    );
  });
});

