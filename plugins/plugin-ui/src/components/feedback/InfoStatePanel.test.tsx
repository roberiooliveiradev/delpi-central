import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InfoStatePanel, infoStateBemClasses } from "./InfoStatePanel";

describe("InfoStatePanel", () => {
  it("renderiza título, descrição e ação", () => {
    const onAction = vi.fn();

    render(
      <InfoStatePanel
        title="Sem dados"
        description="Cadastre indicadores."
        actionLabel="Abrir configurações"
        onAction={onAction}
        icon={<span>i</span>}
        classNames={infoStateBemClasses("si")}
      />,
    );

    expect(screen.getByText("Sem dados")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Abrir configurações" })).toBeTruthy();
  });
});
