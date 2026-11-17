import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FormReviewSection } from "./FormReviewSection";

afterEach(cleanup);

const EDIT = { label: "Editar", ariaLabel: "Editar respostas da etapa", onClick: vi.fn() };

const ROWS = [
  { label: "Pergunta 1", value: "Muito bom" },
  { label: "Pergunta 2", value: "Sem resposta", muted: true },
  { label: "Comentário", value: "Linha 1\nLinha 2", block: true },
];

describe("FormReviewSection", () => {
  it("usa dl/dt/dd semânticos com uma linha por par", () => {
    const { container } = render(
      <FormReviewSection title="Suas respostas" edit={EDIT} rows={ROWS} />,
    );
    expect(container.querySelectorAll("dl")).toHaveLength(1);
    expect(container.querySelectorAll("dt")).toHaveLength(3);
    expect(container.querySelectorAll("dd")).toHaveLength(3);
    expect(container.querySelectorAll("dt")[0].textContent).toBe("Pergunta 1");
  });

  it("Editar tem nome acessível via ariaLabel e dispara onClick", () => {
    const edit = { ...EDIT, onClick: vi.fn() };
    const { getByRole } = render(
      <FormReviewSection title="Seção" edit={edit} rows={ROWS} />,
    );
    const button = getByRole("button", { name: edit.ariaLabel });
    fireEvent.click(button);
    expect(edit.onClick).toHaveBeenCalledTimes(1);
  });

  it("muted aplica __row--muted; block aplica __row--block", () => {
    const { container } = render(
      <FormReviewSection title="Seção" edit={EDIT} rows={ROWS} />,
    );
    const rows = container.querySelectorAll(".delpi-ui-form-review__row");
    expect(rows[0].className).not.toContain("--muted");
    expect(rows[1].className).toContain("__row--muted");
    expect(rows[2].className).toContain("__row--block");
  });
});
