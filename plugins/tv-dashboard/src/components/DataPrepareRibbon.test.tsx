import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { DataPrepareRibbon } from "./DataPrepareRibbon";

describe("DataPrepareRibbon", () => {
  it("mostra formulário só após escolher ação em Transformar", () => {
    const onAddStep = vi.fn();
    render(
      <DataPrepareRibbon
        tab="transform"
        onTabChange={() => undefined}
        columnOptions={[{ value: "oee", label: "oee" }]}
        activeColumn="oee"
        onActiveColumnChange={() => undefined}
        siblingOptions={[]}
        previewLoading={false}
        hasPreset={false}
        onRefresh={() => undefined}
        onAddStep={onAddStep}
        onStartFxColumn={() => undefined}
        onApplyPreset={() => undefined}
      />,
    );

    expect(screen.queryByText("Renomear coluna")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Renomear" }));
    expect(screen.getByText("Renomear coluna")).toBeTruthy();
    fireEvent.change(screen.getByPlaceholderText("Novo nome"), {
      target: { value: "oee_pct" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onAddStep).toHaveBeenCalledWith({
      op: "rename",
      from: "oee",
      to: "oee_pct",
    });
  });
});
