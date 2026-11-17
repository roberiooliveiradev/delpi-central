import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FormStepFooter } from "./FormStepFooter";

afterEach(cleanup);

const NEXT = { label: "Avançar", onClick: vi.fn() };

describe("FormStepFooter", () => {
  it("sem back não renderiza o botão Voltar", () => {
    const { queryByRole, getByRole } = render(
      <FormStepFooter next={NEXT} />,
    );
    expect(queryByRole("button", { name: "Voltar" })).toBeNull();
    expect(getByRole("button", { name: "Avançar" })).toBeTruthy();
  });

  it("back renderiza botão secundário que chama onClick", () => {
    const back = { label: "Voltar", onClick: vi.fn() };
    const { getByRole } = render(
      <FormStepFooter back={back} next={NEXT} />,
    );
    const button = getByRole("button", { name: "Voltar" });
    expect(button.className).toContain("delpi-ui-form-button--secondary");
    fireEvent.click(button);
    expect(back.onClick).toHaveBeenCalledTimes(1);
  });

  it("message renderiza com role=status e estilo de pendência", () => {
    const { getByRole } = render(
      <FormStepFooter message="Responda a questão 2" next={NEXT} />,
    );
    const status = getByRole("status");
    expect(status.textContent).toBe("Responda a questão 2");
    expect(status.className).toContain("__message");
  });

  it("next.busy mostra busyLabel e não dispara onClick", () => {
    const next = { ...NEXT, onClick: vi.fn(), busy: true, busyLabel: "Enviando…" };
    const { getByRole } = render(<FormStepFooter next={next} />);
    const button = getByRole("button", { name: "Enviando…" });
    fireEvent.click(button);
    expect(next.onClick).not.toHaveBeenCalled();
  });
});
