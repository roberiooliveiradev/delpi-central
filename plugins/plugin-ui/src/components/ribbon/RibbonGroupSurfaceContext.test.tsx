import { describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach } from "vitest";

import { RibbonGroup } from "./RibbonGroup";
import { RibbonGroupsRow } from "./RibbonGroupsRow";
import {
  RibbonGroupSurfaceProvider,
  useRibbonGroupSurface,
  useRibbonSectionPopoverSurface,
} from "./RibbonGroupSurfaceContext";

afterEach(() => cleanup());

function SurfaceProbe() {
  const surface = useRibbonGroupSurface();
  const section = useRibbonSectionPopoverSurface();
  return (
    <span data-testid="probe" data-surface={surface} data-section={String(section)}>
      {surface}
    </span>
  );
}

describe("RibbonGroupSurfaceContext", () => {
  it("default band na faixa expandida", () => {
    render(
      <RibbonGroupsRow overflowEnabled={false}>
        <RibbonGroup groupId="g1" label="Zoom">
          <SurfaceProbe />
        </RibbonGroup>
      </RibbonGroupsRow>,
    );
    expect(screen.getByTestId("probe").getAttribute("data-surface")).toBe("band");
    expect(screen.getByTestId("probe").getAttribute("data-section")).toBe("false");
  });

  it("section-popover via Provider (corpo do popover colapsado)", () => {
    render(
      <RibbonGroupSurfaceProvider value="section-popover">
        <SurfaceProbe />
      </RibbonGroupSurfaceProvider>,
    );
    expect(screen.getByTestId("probe").getAttribute("data-surface")).toBe("section-popover");
    expect(screen.getByTestId("probe").getAttribute("data-section")).toBe("true");
  });
});
