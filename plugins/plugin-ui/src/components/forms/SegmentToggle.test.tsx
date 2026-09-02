import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SegmentToggle, createDashboardSegmentToggle, segmentToggleBemClasses } from "./SegmentToggle";

afterEach(() => {
  cleanup();
});

describe("segmentToggleBemClasses", () => {
  it("emite dual-class prefix + delpi-ui", () => {
    const seg = segmentToggleBemClasses("ds");
    expect(seg.root).toBe("ds-segment-toggle delpi-ui-segment-toggle");
    expect(seg.button).toContain("delpi-ui-segment-toggle__btn");
    expect(seg.buttonActive).toContain("delpi-ui-segment-toggle__btn--active");
  });
});

describe("SegmentToggle", () => {
  it("marca a opção ativa e dispara onChange", () => {
    const onChange = vi.fn();
    render(
      <SegmentToggle
        ariaLabel="Visualizar por"
        idPrefix="tm-proc-browse"
        options={[
          { value: "processo", label: "Processos" },
          { value: "departamento", label: "Departamentos" },
        ]}
        value="processo"
        onChange={onChange}
      />,
    );

    const processos = screen.getByRole("button", { name: "Processos" });
    const departamentos = screen.getByRole("button", { name: "Departamentos" });
    expect(processos.getAttribute("aria-pressed")).toBe("true");
    expect(departamentos.getAttribute("aria-pressed")).toBe("false");

    fireEvent.click(departamentos);
    expect(onChange).toHaveBeenCalledWith("departamento");
  });

  it("aplica width-content fora do fill em FiltersRow", () => {
    const { container } = render(
      <SegmentToggle
        ariaLabel="Modo"
        widthMode="content"
        options={[
          { value: "list", label: "Lista" },
          { value: "grouped", label: "Agrupado" },
        ]}
        value="list"
        onChange={() => undefined}
      />,
    );
    const root = container.querySelector(".delpi-ui-segment-toggle");
    expect(root?.className.includes("delpi-ui-segment-toggle--width-content")).toBe(true);
  });

  it("aplica column para pilha vertical", () => {
    const { container } = render(
      <SegmentToggle
        ariaLabel="Tipo"
        direction="column"
        options={[
          { value: "a", label: "A" },
          { value: "b", label: "B" },
        ]}
        value="a"
        onChange={() => undefined}
      />,
    );
    const root = container.querySelector(".delpi-ui-segment-toggle");
    expect(root?.className.includes("delpi-ui-segment-toggle--column")).toBe(true);
  });

  it("aplica modificador sm no root", () => {
    const { container } = render(
      <SegmentToggle
        ariaLabel="Tamanho"
        size="sm"
        options={[
          { value: "a", label: "A" },
          { value: "b", label: "B" },
        ]}
        value="a"
        onChange={() => undefined}
      />,
    );
    const root = container.querySelector(".delpi-ui-segment-toggle");
    expect(root?.className.includes("delpi-ui-segment-toggle--sm")).toBe(true);
  });

  it("renderiza três ou mais opções sem perder botões", () => {
    render(
      <SegmentToggle
        ariaLabel="Visão"
        options={[
          { value: "consolidated", label: "Consolidado" },
          { value: "filial", label: "Unidade" },
          { value: "department", label: "Departamento" },
        ]}
        value="consolidated"
        onChange={() => undefined}
      />,
    );
    expect(screen.getAllByRole("button")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Departamento" })).toBeTruthy();
  });

  it("usa ariaLabel quando o label é ícone", () => {
    render(
      <SegmentToggle
        ariaLabel="Vista"
        idPrefix="room-tab"
        size="sm"
        options={[
          { value: "chat", label: <span data-testid="chat-icon" />, ariaLabel: "Chat" },
          {
            value: "shared",
            label: <span data-testid="shared-icon" />,
            ariaLabel: "Compartilhados",
          },
        ]}
        value="chat"
        onChange={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "Chat" }).getAttribute("aria-pressed")).toBe(
      "true",
    );
    expect(screen.getByRole("button", { name: "Compartilhados" })).toBeTruthy();
  });
});

describe("createDashboardSegmentToggle", () => {
  it("aplica prefixo do MFE no dual-class", () => {
    const Toggle = createDashboardSegmentToggle("cm");
    const { container } = render(
      <Toggle
        ariaLabel="Modo"
        options={[
          { value: "list", label: "Lista" },
          { value: "org", label: "Diagrama" },
        ]}
        value="list"
        onChange={() => undefined}
      />,
    );
    const root = container.querySelector(".cm-segment-toggle");
    expect(root?.className).toContain("delpi-ui-segment-toggle");
  });
});
