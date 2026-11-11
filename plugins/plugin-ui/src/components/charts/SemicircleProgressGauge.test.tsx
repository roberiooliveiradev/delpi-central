import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  SemicircleProgressGauge,
  semicircleProgressGaugeBemClasses,
} from "./SemicircleProgressGauge";

afterEach(() => {
  cleanup();
});

describe("SemicircleProgressGauge", () => {
  it("emite dual-class e valor central", () => {
    const classNames = semicircleProgressGaugeBemClasses("itp");
    expect(classNames.root).toContain("delpi-ui-semicircle-gauge");
    render(<SemicircleProgressGauge prefix="itp" value={100} centerLabel="tudo certo" />);
    expect(screen.getByText("100")).toBeTruthy();
    expect(screen.getByText("tudo certo")).toBeTruthy();
    expect(document.querySelector(".itp-semicircle-gauge__fill")).toBeTruthy();
  });

  it("legenda de contagens entra no nome acessível", () => {
    render(
      <SemicircleProgressGauge
        prefix="itp"
        value={75}
        centerLabel="resumo"
        legend={[
          { id: "a", label: "Alta ou crítica", count: 1, tone: "danger" },
          { id: "b", label: "Baixa ou média", count: 3, tone: "success" },
        ]}
      />,
    );
    const gauge = screen.getByRole("img");
    expect(gauge.getAttribute("aria-label")).toContain("Alta ou crítica: 1");
    expect(screen.getByText("Alta ou crítica")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
  });

  it("valor zero não desenha preenchimento e acima do máximo é limitado", () => {
    const { rerender } = render(<SemicircleProgressGauge prefix="itp" value={0} />);
    expect(document.querySelector(".delpi-ui-semicircle-gauge__fill")).toBeNull();
    rerender(<SemicircleProgressGauge prefix="itp" value={250} />);
    const gauge = screen.getByRole("img");
    expect(gauge.getAttribute("data-ratio")).toBe("1.0000");
  });

  it("valor nulo mostra traço sem percentual inventado", () => {
    render(<SemicircleProgressGauge prefix="itp" value={null} centerLabel="sem dados" />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
