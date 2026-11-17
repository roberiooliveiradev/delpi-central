import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormResultPanel } from "./FormResultPanel";

afterEach(cleanup);

describe("FormResultPanel", () => {
  it("success usa role=status e mostra o círculo", () => {
    const { container, getByRole } = render(
      <FormResultPanel tone="success" title="Obrigado" message="Enviado." />,
    );
    expect(getByRole("status")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-form-result__circle")).toBeTruthy();
  });

  it("info também usa role=status, sem círculo", () => {
    const { container, getByRole } = render(
      <FormResultPanel tone="info" title="Aviso" message="Msg." />,
    );
    expect(getByRole("status")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-form-result__circle")).toBeNull();
  });

  it("error usa role=alert e não mostra círculo", () => {
    const { container, getByRole } = render(
      <FormResultPanel tone="error" title="Erro" message="Falhou." />,
    );
    expect(getByRole("alert")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-form-result__circle")).toBeNull();
  });

  it("hint e action opcionais renderizam quando presentes", () => {
    const { getByRole, getByText } = render(
      <FormResultPanel
        tone="success"
        title="T"
        message="M"
        hint="Dica"
        action={<button type="button">Fechar</button>}
      />,
    );
    expect(getByText("Dica").className).toContain("__hint");
    expect(getByRole("button", { name: "Fechar" })).toBeTruthy();
  });
});
