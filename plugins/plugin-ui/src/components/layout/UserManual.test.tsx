import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { UserManual, createDashboardUserManual, userManualBemClasses } from "./UserManual";

afterEach(() => {
  cleanup();
});

describe("UserManual", () => {
  it("emite dual-class no frame", () => {
    const { container } = render(
      <UserManual classNames={userManualBemClasses("cm")}>Manual</UserManual>,
    );
    expect(container.querySelector(".delpi-ui-user-manual")).toBeTruthy();
    expect(container.querySelector(".cm-user-manual")).toBeTruthy();
  });

  it("factory monta TOC, conceitos e tabela", () => {
    const onSelect = vi.fn();
    const kit = createDashboardUserManual({ prefix: "sp" });
    const { container } = render(
      <kit.Frame>
        <kit.Eyebrow>Ajuda</kit.Eyebrow>
        <kit.Scope>Escopo do portal.</kit.Scope>
        <kit.Layout
          title="Neste manual"
          aria-label="Índice"
          items={[{ id: "concepts", label: "Conceitos", onSelect }]}
        >
          <kit.Concepts items={[{ term: "Portal", meaning: "Área do produto." }]} />
          <kit.GuideTable
            rows={[{ want: "Abrir início", where: "Início", how: "Clique no menu." }]}
          />
        </kit.Layout>
      </kit.Frame>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Conceitos" }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Portal")).toBeTruthy();
    expect(screen.getByText("Quero…")).toBeTruthy();
    expect(container.querySelector(".sp-user-manual")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-user-manual__layout")).toBeTruthy();
  });
});
