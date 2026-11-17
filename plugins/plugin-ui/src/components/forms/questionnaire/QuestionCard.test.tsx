import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { QuestionCard } from "./QuestionCard";

afterEach(cleanup);

describe("QuestionCard", () => {
  it("renderiza fieldset com legend visível (primeiro filho) contendo eyebrow + número + enunciado", () => {
    const { container } = render(
      <QuestionCard
        prefix="puc"
        eyebrow="Qualidade"
        number={1}
        prompt="Como você avalia?"
      >
        <div>resposta</div>
      </QuestionCard>,
    );
    const fieldset = container.firstElementChild!;
    expect(fieldset.tagName).toBe("FIELDSET");
    expect(fieldset.className).toContain("delpi-ui-form-question");
    expect(fieldset.className).toContain("puc-form-question");

    const legend = fieldset.firstElementChild!;
    expect(legend.tagName).toBe("LEGEND");
    expect(legend.className).toContain("delpi-ui-form-question__legend");
    expect(legend.textContent).toContain("Qualidade");
    expect(legend.textContent).toContain("1. Como você avalia?");
    expect(
      legend.querySelector(".delpi-ui-form-eyebrow")!.textContent,
    ).toBe("Qualidade");
    expect(
      legend.querySelector(".delpi-ui-form-question__prompt")!.textContent,
    ).toContain("1. Como você avalia?");
  });

  it("obrigatória: asterisco aria-hidden + texto acessível via requiredLabel", () => {
    const { container } = render(
      <QuestionCard prompt="Pergunta" required requiredLabel="obrigatória" />,
    );
    const legend = container.querySelector("legend")!;
    const asterisk = legend.querySelector(
      ".delpi-ui-form-question__required",
    )!;
    expect(asterisk.textContent).toBe(" *");
    expect(asterisk.getAttribute("aria-hidden")).toBe("true");

    const srOnly = legend.querySelector(
      ".delpi-ui-form-question__sr-only",
    )!;
    expect(srOnly.textContent).toBe(" obrigatória");
  });

  it("opcional: optionalLabel com peso neutro (classe própria)", () => {
    const { container } = render(
      <QuestionCard prompt="Pergunta" optionalLabel="(opcional)" />,
    );
    const label = container.querySelector(
      ".delpi-ui-form-question__optional",
    )!;
    expect(label.textContent).toBe(" (opcional)");
    // sem asterisco nem sr-only em pergunta não obrigatória
    expect(
      container.querySelector(".delpi-ui-form-question__required"),
    ).toBeNull();
  });

  it("erro: cartão fica inválido e fieldset é descrito pela mensagem", () => {
    const { container } = render(
      <QuestionCard prompt="Pergunta" error="Selecione uma opção." />,
    );
    const fieldset = container.firstElementChild!;
    expect(fieldset.className).toContain(
      "delpi-ui-form-card--tone-invalid",
    );

    const error = container.querySelector(
      ".delpi-ui-form-question__error",
    )!;
    expect(error.textContent).toBe("Selecione uma opção.");
    expect(fieldset.getAttribute("aria-describedby")).toBe(error.id);
    expect(error.id).toBeTruthy();
  });

  it("sem erro não emite aria-describedby", () => {
    const { container } = render(<QuestionCard prompt="Pergunta" />);
    expect(
      container.firstElementChild!.getAttribute("aria-describedby"),
    ).toBeNull();
  });
});
