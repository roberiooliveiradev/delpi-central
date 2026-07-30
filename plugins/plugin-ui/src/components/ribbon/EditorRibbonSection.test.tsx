import { Circle } from "lucide-react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EditorRibbonSection, EditorRibbonSections } from "./EditorRibbonSection";
import { RibbonTile } from "./RibbonTile";

describe("EditorRibbonSection", () => {
  it("renderiza seção expandida com caption e tiles", () => {
    render(
      <EditorRibbonSections overflowEnabled={false}>
        <EditorRibbonSection groupId="bpmn-events" label="Eventos" collapseIcon={Circle} order={10}>
          <RibbonTile icon={Circle} label="Início" />
        </EditorRibbonSection>
      </EditorRibbonSections>,
    );
    expect(screen.getAllByText("Eventos").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Início" })).toBeTruthy();
    const root = document.querySelector('[data-ribbon-group-mode="expanded"]');
    expect(root?.className).toContain("delpi-ui-ribbon-group");
  });
});
