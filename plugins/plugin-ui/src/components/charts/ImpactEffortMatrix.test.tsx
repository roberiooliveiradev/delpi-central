import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ImpactEffortMatrix } from "./ImpactEffortMatrix";
import { resolveImpactEffortQuadrant, type ImpactEffortPoint } from "./impactEffortTypes";

const SAMPLE: ImpactEffortPoint[] = [
  { id: "r1", label: "v1.1.0", impacto: 72, esforco: 41, quadrante: "quick_win" },
  { id: "r2", label: "v1.0.0", impacto: 30, esforco: 80, quadrante: "rethink", muted: true },
];

describe("resolveImpactEffortQuadrant", () => {
  it("classifica quick win acima do limiar de impacto e abaixo de esforço", () => {
    expect(resolveImpactEffortQuadrant(72, 41)).toBe("quick_win");
  });

  it("classifica rethink com baixo impacto e alto esforço", () => {
    expect(resolveImpactEffortQuadrant(30, 80)).toBe("rethink");
  });
});

describe("ImpactEffortMatrix", () => {
  it("renderiza svg com pontos visíveis", () => {
    const { container } = render(<ImpactEffortMatrix points={SAMPLE} activePointId="r1" />);
    expect(container.querySelector("svg")).toBeTruthy();
    expect(container.querySelectorAll("circle").length).toBeGreaterThan(0);
  });

  it("dispara onPointSelect ao clicar ponto interativo", () => {
    const onSelect = vi.fn();
    render(<ImpactEffortMatrix points={SAMPLE} activePointId="r1" onPointSelect={onSelect} />);
    const button = screen.getByRole("button", { name: /v1\.1\.0/i });
    fireEvent.click(button);
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "r1" }));
  });

  it("mostra mensagem vazia sem pontos", () => {
    render(<ImpactEffortMatrix points={[]} emptyMessage="Sem revisões" />);
    expect(screen.getByText("Sem revisões")).toBeTruthy();
  });
});
