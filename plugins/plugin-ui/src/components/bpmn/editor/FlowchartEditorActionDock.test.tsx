import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Trash2 } from "lucide-react";

import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import { FlowchartEditorActionDock } from "./FlowchartEditorActionDock";

const labels = {
  selectionDockAriaLabel: "Ações de seleção",
} as FlowchartEditorLabels;

describe("FlowchartEditorActionDock", () => {
  it("usa layout horizontal na statusbar (sem dock flutuante)", () => {
    const { container } = render(
      <FlowchartEditorActionDock
        labels={labels}
        selectionActions={[
          {
            id: "delete",
            label: "Excluir",
            hint: "Remove a seleção",
            icon: Trash2,
          },
        ]}
        clipboardReady={false}
        onSelectionAction={vi.fn()}
        isSelectionActionDisabled={() => false}
        variant="statusbar"
      />,
    );

    const dock = container.querySelector(".delpi-ui-bpmn-editor__action-dock--statusbar");
    expect(dock).toBeTruthy();
    expect(container.querySelector(".delpi-ui-bpmn-editor__action-dock--floating")).toBeNull();
    expect(screen.getByRole("toolbar", { name: "Ações de seleção" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Excluir" })).toBeTruthy();
  });
});
