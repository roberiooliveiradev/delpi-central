import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RibbonGroup, ribbonGroupBemClasses } from "./RibbonGroup";
import { RibbonGroupsRow } from "./RibbonGroupsRow";

describe("RibbonGroup", () => {
  it("renderiza expandido com dual-class e caption", () => {
    const cn = ribbonGroupBemClasses("td");
    render(
      <RibbonGroupsRow overflowEnabled={false}>
        <RibbonGroup groupId="demo" label="Zoom" classNames={cn}>
          <button type="button">Ajustar</button>
        </RibbonGroup>
      </RibbonGroupsRow>,
    );
    expect(screen.getAllByText("Zoom").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Ajustar" })).toBeTruthy();
    const root = document.querySelector('[data-ribbon-group-mode="expanded"]');
    expect(root?.className).toContain("td-ribbon-group");
    expect(root?.className).toContain("delpi-ui-ribbon-group");
  });
});
