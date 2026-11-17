import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { QuestionTextAnswer } from "./QuestionTextAnswer";

afterEach(cleanup);

describe("QuestionTextAnswer", () => {
  it("renderiza rótulo visível ligado ao textarea (classes do escopo)", () => {
    const { container, getByLabelText } = render(
      <QuestionTextAnswer label="Sua resposta" value="" onChange={() => {}} />,
    );
    const textarea = getByLabelText("Sua resposta");
    expect(textarea.tagName).toBe("TEXTAREA");
    expect(textarea.className).toContain(
      "delpi-ui-form-textanswer__control--textarea",
    );
    expect(
      container.querySelector(".delpi-ui-form-textanswer"),
    ).toBeTruthy();
  });

  it("repassa value, onChange, placeholder e maxLength", () => {
    const onChange = vi.fn();
    const { getByPlaceholderText } = render(
      <QuestionTextAnswer
        label="Campo"
        value="abc"
        onChange={onChange}
        placeholder="Escreva aqui"
        maxLength={200}
      />,
    );
    const textarea = getByPlaceholderText(
      "Escreva aqui",
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe("abc");
    expect(textarea.maxLength).toBe(200);

    fireEvent.change(textarea, { target: { value: "novo" } });
    expect(onChange).toHaveBeenCalledWith("novo");
  });

  it("describedBy vai para o envoltório role=group (TextAreaField intacto)", () => {
    const { container } = render(
      <QuestionTextAnswer
        label="Campo"
        value=""
        onChange={() => {}}
        describedBy="erro-campo"
      />,
    );
    const group = container.querySelector('[role="group"]')!;
    expect(group.getAttribute("aria-describedby")).toBe("erro-campo");
  });

  it("sem describedBy não emite aria-describedby", () => {
    const { container } = render(
      <QuestionTextAnswer label="Campo" value="" onChange={() => {}} />,
    );
    expect(
      container
        .querySelector('[role="group"]')!
        .getAttribute("aria-describedby"),
    ).toBeNull();
  });
});
