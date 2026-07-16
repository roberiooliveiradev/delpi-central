import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { DataPrepareContextMenu } from "./DataPrepareContextMenu";

describe("DataPrepareContextMenu", () => {
  it("mostra ações de coluna e dispara ordenar", () => {
    const onSortColumn = vi.fn();
    render(
      <DataPrepareContextMenu
        open
        position={{ x: 10, y: 10 }}
        target={{ kind: "column", name: "oee" }}
        onClose={() => undefined}
        onRefresh={() => undefined}
        onClearSteps={() => undefined}
        onCopyText={() => undefined}
        onEditStepFx={() => undefined}
        onMoveStep={() => undefined}
        onDeleteStep={() => undefined}
        onRenameColumn={() => undefined}
        onFilterColumn={() => undefined}
        onSortColumn={onSortColumn}
        onRemoveColumn={() => undefined}
        onKeepOnlyColumn={() => undefined}
      />,
    );

    fireEvent.click(screen.getByRole("menuitem", { name: /Ordenar A→Z/i }));
    expect(onSortColumn).toHaveBeenCalledWith("oee", "asc");
  });

  it("mostra ações de etapa", () => {
    const onDeleteStep = vi.fn();
    render(
      <DataPrepareContextMenu
        open
        position={{ x: 10, y: 10 }}
        target={{ kind: "step", index: 1 }}
        canMoveStepUp
        canMoveStepDown
        onClose={() => undefined}
        onRefresh={() => undefined}
        onClearSteps={() => undefined}
        onCopyText={() => undefined}
        onEditStepFx={() => undefined}
        onMoveStep={() => undefined}
        onDeleteStep={onDeleteStep}
        onRenameColumn={() => undefined}
        onFilterColumn={() => undefined}
        onSortColumn={() => undefined}
        onRemoveColumn={() => undefined}
        onKeepOnlyColumn={() => undefined}
      />,
    );

    fireEvent.click(screen.getByRole("menuitem", { name: /Excluir etapa/i }));
    expect(onDeleteStep).toHaveBeenCalledWith(1);
  });
});
