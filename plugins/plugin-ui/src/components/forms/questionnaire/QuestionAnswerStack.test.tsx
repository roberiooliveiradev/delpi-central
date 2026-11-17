import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { QuestionAnswerStack } from "./QuestionAnswerStack";

afterEach(cleanup);

describe("QuestionAnswerStack", () => {
  it("renderiza pilha com dual-class e filhos em ordem", () => {
    const { container } = render(
      <QuestionAnswerStack prefix="puc">
        <div data-testid="a" />
        <div data-testid="b" />
      </QuestionAnswerStack>,
    );
    const stack = container.firstElementChild!;
    expect(stack.className).toContain("delpi-ui-form-answer-stack");
    expect(stack.className).toContain("puc-form-answer-stack");
    expect(stack.children).toHaveLength(2);
    expect(stack.firstElementChild!.getAttribute("data-testid")).toBe("a");
  });

  it("aceita className extra", () => {
    const { container } = render(
      <QuestionAnswerStack className="extra" />,
    );
    expect(container.firstElementChild!.className).toContain("extra");
  });
});
