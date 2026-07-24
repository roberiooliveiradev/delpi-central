import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SegmentToggle, segmentToggleBemClasses } from "./SegmentToggle";

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
});
