import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { AlertQueue, alertQueueBemClasses } from "./AlertQueue";
import { ScopeChipBar, scopeChipBarBemClasses } from "./ScopeChipBar";
import { WorklistItem, worklistItemBemClasses } from "./WorklistItem";

describe("Wave G worklist surface", () => {
  it("alertQueueBemClasses emite dual-class", () => {
    const cn = alertQueueBemClasses("cm");
    expect(cn.root).toContain("cm-alert-queue");
    expect(cn.root).toContain("delpi-ui-alert-queue");
  });

  it("AlertQueue renderiza item e empty", () => {
    const cn = alertQueueBemClasses("cm");
    const { rerender } = render(
      <AlertQueue
        classNames={cn}
        items={[{ id: "1", title: "Atraso", actionLabel: "Ver", onAction: () => undefined }]}
      />,
    );
    expect(screen.getByText("Atraso")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ver" })).toBeTruthy();

    rerender(<AlertQueue classNames={cn} items={[]} emptyMessage="Vazio" />);
    expect(screen.getByText("Vazio")).toBeTruthy();
  });

  it("ScopeChipBar e WorklistItem dual-class + active", () => {
    const chipCn = scopeChipBarBemClasses("cm");
    const wlCn = worklistItemBemClasses("cm");
    expect(chipCn.chip).toContain("delpi-ui-scope-chip-bar__chip");
    expect(wlCn.root).toContain("delpi-ui-worklist-item");

    render(
      <ScopeChipBar
        classNames={chipCn}
        chips={[{ id: "me", label: "Minha carteira", active: true }]}
      />,
    );
    expect(screen.getByRole("button", { name: "Minha carteira" }).getAttribute("aria-pressed")).toBe(
      "true",
    );

    render(
      <WorklistItem
        classNames={wlCn}
        title="Follow-up"
        primaryActionLabel="Concluir"
        onPrimaryAction={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "Concluir" })).toBeTruthy();
  });
});
