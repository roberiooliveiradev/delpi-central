import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { InlineMeter, inlineMeterBemClasses } from "./InlineMeter";

describe("InlineMeter", () => {
  it("emite dual-class BEM", () => {
    const cn = inlineMeterBemClasses("cm");
    expect(cn.root).toContain("cm-inline-meter");
    expect(cn.root).toContain("delpi-ui-inline-meter");
  });

  it("expõe role meter com percentual", () => {
    const cn = inlineMeterBemClasses("cm");
    render(
      <InlineMeter
        classNames={cn}
        value={62}
        max={100}
        tone="success"
        label="62%"
        aria-label="Cobertura"
      />,
    );
    const meter = screen.getByRole("meter", { name: "Cobertura" });
    expect(meter.getAttribute("aria-valuenow")).toBe("62");
    expect(screen.getByText("62%")).toBeTruthy();
  });
});
