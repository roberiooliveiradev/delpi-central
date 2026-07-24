import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StateBox } from "./StateBox";

afterEach(() => {
  cleanup();
});

describe("StateBox", () => {
  it("emite dual-class inline + tom de sucesso", () => {
    const { container } = render(
      <StateBox variant="success" prefix="ds">
        Exportação concluída
      </StateBox>,
    );
    const root = container.firstElementChild;
    expect(root?.className).toContain("ds-state-box");
    expect(root?.className).toContain("delpi-ui-state-box");
    expect(root?.className).toContain("delpi-ui-state-box--inline");
    expect(root?.className).toContain("delpi-ui-state-box--success");
    expect(screen.getByRole("status")).toBeTruthy();
  });

  it("erro usa role=alert", () => {
    render(
      <StateBox variant="error" prefix="ds">
        Falha
      </StateBox>,
    );
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("onDismiss fecha o aviso", () => {
    const onDismiss = vi.fn();
    render(
      <StateBox variant="success" prefix="ds" onDismiss={onDismiss}>
        Ok
      </StateBox>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Fechar aviso" }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("dismissible=false omite o botão fechar", () => {
    render(
      <StateBox variant="error" prefix="ds" dismissible={false}>
        Falha
      </StateBox>,
    );
    expect(screen.queryByRole("button", { name: "Fechar aviso" })).toBeNull();
  });
});
