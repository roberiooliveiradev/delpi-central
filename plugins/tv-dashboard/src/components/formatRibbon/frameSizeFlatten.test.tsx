import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { Move } from "lucide-react";

import {
  RibbonGroupSurfaceProvider,
  useRibbonSectionPopoverSurface,
} from "../../../../plugin-ui/src/components/ribbon/RibbonGroupSurfaceContext";

afterEach(() => cleanup());

/** Espelho mínimo da regra FrameSizeBandOrInline — sem montar editor completo. */
function FrameSizeProbe({ hint = "hint" }: { hint?: string }) {
  const flattenNested = useRibbonSectionPopoverSurface();
  if (flattenNested) {
    return <div data-testid="frame-inline">grade</div>;
  }
  return (
    <div data-testid="frame-entry">
      <button type="button" aria-label="Tamanho e posição">
        <Move size={18} />
        Posição
      </button>
      <span>{hint}</span>
    </div>
  );
}

describe("ribbon section popover flatten", () => {
  it("banda: mantém gatilho Posição", () => {
    render(<FrameSizeProbe />);
    expect(screen.getByTestId("frame-entry")).toBeTruthy();
    expect(screen.queryByTestId("frame-inline")).toBeNull();
  });

  it("section-popover: grade direta sem gatilho Posição", () => {
    render(
      <RibbonGroupSurfaceProvider value="section-popover">
        <FrameSizeProbe />
      </RibbonGroupSurfaceProvider>,
    );
    expect(screen.getByTestId("frame-inline")).toBeTruthy();
    expect(screen.queryByTestId("frame-entry")).toBeNull();
  });
});
