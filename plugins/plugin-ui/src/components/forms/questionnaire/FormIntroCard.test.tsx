import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormIntroCard } from "./FormIntroCard";

const base = {
  logo: <span data-testid="logo" />,
  title: "Título",
  action: <button type="button">Começar</button>,
};

afterEach(cleanup);

describe("FormIntroCard", () => {
  it("renderiza todos os blocos quando presentes", () => {
    const { container } = render(
      <FormIntroCard
        {...base}
        prefix="puc"
        headerAction={<button type="button">tema</button>}
        eyebrow="Avaliação"
        context={{ label: "Respondendo por", value: "Empresa X" }}
        description="Descrição."
        items={[
          { icon: <svg data-testid="ico1" />, content: "Item um" },
          { icon: <svg data-testid="ico2" />, content: "Item dois" },
        ]}
        footnote="Nota de rodapé."
      />,
    );
    const card = container.firstElementChild!;
    expect(card.className).toContain("delpi-ui-form-card");
    expect(card.className).toContain("delpi-ui-form-card--intro");

    expect(card.querySelector(".delpi-ui-form-intro__row")).toBeTruthy();
    expect(
      card.querySelector(".delpi-ui-form-eyebrow")!.textContent,
    ).toBe("Avaliação");
    expect(
      card.querySelector(".delpi-ui-form-intro__title")!.textContent,
    ).toBe("Título");
    expect(
      card.querySelector(".delpi-ui-form-intro__context-label")!.textContent,
    ).toBe("Respondendo por");
    expect(
      card.querySelector(".delpi-ui-form-intro__context-value")!.textContent,
    ).toBe("Empresa X");
    expect(
      card.querySelector(".delpi-ui-form-intro__description")!.textContent,
    ).toBe("Descrição.");
    expect(card.querySelectorAll(".delpi-ui-form-intro__item").length).toBe(2);
    expect(
      card.querySelectorAll(".delpi-ui-form-intro__item-icon")[0].getAttribute(
        "aria-hidden",
      ),
    ).toBe("true");
    expect(
      card.querySelector(".delpi-ui-form-intro__footnote")!.textContent,
    ).toBe("Nota de rodapé.");
  });

  it("omite blocos opcionais ausentes", () => {
    const { container } = render(<FormIntroCard {...base} />);
    const card = container.firstElementChild!;
    expect(card.querySelector(".delpi-ui-form-eyebrow")).toBeNull();
    expect(card.querySelector(".delpi-ui-form-intro__context")).toBeNull();
    expect(
      card.querySelector(".delpi-ui-form-intro__description"),
    ).toBeNull();
    expect(card.querySelector(".delpi-ui-form-intro__items")).toBeNull();
    expect(card.querySelector(".delpi-ui-form-intro__footnote")).toBeNull();
    // ação e título permanecem
    expect(card.querySelector("button")).toBeTruthy();
  });
});
